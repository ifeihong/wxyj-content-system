from __future__ import annotations

import importlib.util
import io
import struct
import shutil
import unittest
import uuid
from contextlib import contextmanager
from contextlib import redirect_stdout
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


@contextmanager
def workspace_tempdir():
    test_root = (PROJECT_ROOT / ".test-work").resolve()
    path = (test_root / uuid.uuid4().hex).resolve()
    path.mkdir(parents=True)
    try:
        yield str(path)
    finally:
        if not path.is_relative_to(test_root):
            raise RuntimeError(f"unsafe test cleanup path: {path}")
        shutil.rmtree(path, ignore_errors=True)


def load_module(name: str, filename: str):
    path = SCRIPTS_DIR / filename
    if not path.exists():
        raise AssertionError(f"missing production script: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ContentRunContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.creator = load_module("create_content_run", "create_content_run.py")
        cls.validator = load_module("validate_content_run", "validate_content_run.py")
        cls.xhs_image_validator = load_module(
            "validate_xhs_image", "validate_xhs_image.py"
        )
        cls.pack_validator = load_module(
            "validate_content_pack", "validate_content_pack.py"
        )
        cls.asset_validator = load_module(
            "validate_product_assets", "validate_product_assets.py"
        )

    def test_bundled_product_assets_validate(self):
        product_root = (
            PROJECT_ROOT
            / "assets"
            / "products"
            / "mackillops-choice-aberlour-1996"
        )
        self.assertEqual(self.asset_validator.validate_assets(product_root), [])

    def test_xhs_image_validator_accepts_exact_three_four_png(self):
        with workspace_tempdir() as tmp:
            path = Path(tmp) / "page.png"
            path.write_bytes(
                b"\x89PNG\r\n\x1a\n"
                + b"\x00\x00\x00\rIHDR"
                + struct.pack(">II", 1086, 1448)
            )

            self.assertEqual(
                self.xhs_image_validator.validate_xhs_image(path),
                [],
            )

    def test_xhs_image_validator_rejects_two_three_png(self):
        with workspace_tempdir() as tmp:
            path = Path(tmp) / "page.png"
            path.write_bytes(
                b"\x89PNG\r\n\x1a\n"
                + b"\x00\x00\x00\rIHDR"
                + struct.pack(">II", 1024, 1536)
            )

            errors = self.xhs_image_validator.validate_xhs_image(path)

            self.assertTrue(errors)
            self.assertIn("必须为精确3:4", errors[0])

    def test_create_run_builds_platform_native_structure(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp),
                "2026-08-01",
                "label-reading",
                ["xiaohongshu", "douyin", "weixin-channels"],
            )

            self.assertEqual(
                run_dir,
                Path(tmp) / "2026" / "08" / "2026-08-01-label-reading",
            )
            expected = [
                "manifest.yaml",
                "brief.md",
                "sources.md",
                "xiaohongshu/publish.md",
                "xiaohongshu/prompts.md",
                "xiaohongshu/qa.md",
                "xiaohongshu/media",
                "douyin/publish.md",
                "douyin/qa.md",
                "douyin/media",
                "weixin-channels/publish.md",
                "weixin-channels/qa.md",
                "weixin-channels/media",
                "video-master/treatment.md",
                "video-master/shotlist.yaml",
                "video-master/storyboard.md",
                "video-master/edit-plan.md",
                "video-master/qa.md",
                "video-master/external-generation",
                "video-master/incoming",
                "video-master/accepted",
                "video-master/media",
            ]
            for relative in expected:
                self.assertTrue((run_dir / relative).exists(), relative)

    def test_video_platforms_share_one_video_master(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp),
                "2026-08-01",
                "label-reading",
                ["douyin", "weixin-channels"],
            )

            expected = [
                "video-master/treatment.md",
                "video-master/shotlist.yaml",
                "video-master/storyboard.md",
                "video-master/edit-plan.md",
                "video-master/qa.md",
                "video-master/external-generation",
                "video-master/incoming",
                "video-master/accepted",
                "video-master/media",
            ]
            for relative in expected:
                self.assertTrue((run_dir / relative).exists(), relative)

            self.assertFalse((run_dir / "douyin" / "storyboard.md").exists())
            self.assertFalse(
                (run_dir / "weixin-channels" / "storyboard.md").exists()
            )

    def test_xiaohongshu_only_run_has_no_video_master(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp),
                "2026-08-01",
                "label-reading",
                ["xiaohongshu"],
            )

            self.assertFalse((run_dir / "video-master").exists())

    def test_create_run_never_overwrites_existing_copy(self):
        with workspace_tempdir() as tmp:
            root = Path(tmp)
            run_dir = self.creator.create_run(
                root, "2026-08-01", "label-reading", ["xiaohongshu"]
            )
            publish = run_dir / "xiaohongshu" / "publish.md"
            publish.write_text("用户已经写好的正文", encoding="utf-8")

            self.creator.create_run(
                root, "2026-08-01", "label-reading", ["xiaohongshu"]
            )

            self.assertEqual(
                publish.read_text(encoding="utf-8"), "用户已经写好的正文"
            )

    def test_create_run_refuses_incompatible_existing_manifest(self):
        with workspace_tempdir() as tmp:
            root = Path(tmp)
            run_dir = self.creator.create_run(
                root, "2026-08-01", "label-reading", ["xiaohongshu"]
            )

            with self.assertRaisesRegex(
                ValueError, "existing manifest does not declare requested platforms"
            ):
                self.creator.create_run(
                    root,
                    "2026-08-01",
                    "label-reading",
                    ["xiaohongshu", "douyin"],
                )

            self.assertFalse((run_dir / "douyin").exists())

            with self.assertRaisesRegex(
                ValueError, "existing manifest belongs to another product"
            ):
                self.creator.create_run(
                    root,
                    "2026-08-01",
                    "label-reading",
                    ["xiaohongshu"],
                    product="待发布新品A",
                )

    def test_create_run_supports_future_products(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp),
                "2026-08-01",
                "new-product-story",
                ["xiaohongshu"],
                product="待发布新品A",
            )

            manifest = (run_dir / "manifest.yaml").read_text(encoding="utf-8")
            self.assertIn("待发布新品A", manifest)

    def test_validator_requires_title_caption_tags_comment_and_cta(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp), "2026-08-01", "label-reading", ["xiaohongshu"]
            )
            publish = run_dir / "xiaohongshu" / "publish.md"
            publish.write_text(
                "# 小红书发布包\n\n## 主标题\n只有标题\n",
                encoding="utf-8",
            )

            errors = self.validator.validate_run(run_dir)

            joined = "\n".join(errors)
            self.assertIn("备选标题", joined)
            self.assertIn("发布正文", joined)
            self.assertIn("话题标签", joined)
            self.assertIn("首评", joined)
            self.assertIn("CTA", joined)

    def test_validator_rejects_empty_brief_sources_and_qa(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp), "2026-08-01", "label-reading", ["xiaohongshu"]
            )

            errors = self.validator.validate_run(run_dir)

            joined = "\n".join(errors)
            self.assertIn("brief.md缺少内容: 母题", joined)
            self.assertIn("sources.md缺少内容: 真实产品", joined)
            self.assertIn("xiaohongshu的qa.md缺少内容: 结论", joined)

    def test_validator_rejects_invalid_run_and_media_names(self):
        with workspace_tempdir() as tmp:
            root = Path(tmp)
            run_dir = root / "2026" / "08" / "August 1 中文主题"
            media = run_dir / "xiaohongshu" / "media"
            media.mkdir(parents=True)
            (run_dir / "manifest.yaml").write_text(
                "version: 2.0.0\nplatforms:\n  - xiaohongshu\n",
                encoding="utf-8",
            )
            for name in ("brief.md", "sources.md"):
                (run_dir / name).write_text("# test\n", encoding="utf-8")
            for name in ("publish.md", "prompts.md", "qa.md"):
                (run_dir / "xiaohongshu" / name).write_text(
                    "# test\n", encoding="utf-8"
                )
            (media / "封面 final.png").write_bytes(b"not-a-real-image")

            errors = self.validator.validate_run(run_dir)

            joined = "\n".join(errors)
            self.assertIn("运行目录命名不合法", joined)
            self.assertIn("媒体文件命名不合法", joined)

    def test_validator_rejects_manifest_identity_mismatch(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp), "2026-08-01", "label-reading", ["xiaohongshu"]
            )
            manifest = run_dir / "manifest.yaml"
            manifest.write_text(
                manifest.read_text(encoding="utf-8")
                .replace(
                    "run_id: 2026-08-01-label-reading",
                    "run_id: 2026-08-02-other-topic",
                )
                .replace("date: 2026-08-01", "date: 2026-08-02")
                .replace("topic_slug: label-reading", "topic_slug: other-topic"),
                encoding="utf-8",
            )

            errors = self.validator.validate_run(run_dir)

            joined = "\n".join(errors)
            self.assertIn("manifest的run_id与运行目录不一致", joined)
            self.assertIn("manifest的date与运行目录不一致", joined)
            self.assertIn("manifest的topic_slug与运行目录不一致", joined)

    def test_validator_rejects_media_from_another_run(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp), "2026-08-01", "label-reading", ["xiaohongshu"]
            )
            media = (
                run_dir
                / "xiaohongshu"
                / "media"
                / "20260802-xhs-other-topic-p01-cover-v01.png"
            )
            media.write_bytes(b"not-a-real-image")

            errors = self.validator.validate_run(run_dir)

            self.assertIn(
                "媒体文件与运行日期或主题不一致: "
                "20260802-xhs-other-topic-p01-cover-v01.png",
                errors,
            )

    def test_validator_distinguishes_disclaimer_from_risk_claim(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp), "2026-08-01", "risk-language", ["xiaohongshu"]
            )
            publish = run_dir / "xiaohongshu" / "publish.md"
            publish.write_text(
                """# 小红书发布包

## 主标题
高年份威士忌如何理性判断

## 备选标题
购买前先看事实

## 一句话钩子
先核对产品，再做决定。

## 发布正文
本内容不承诺保值、升值或投资回报。

## 话题标签
#威士忌知识

## 首评
你最想核对哪个字段？

## CTA
收藏这份核对清单。

## AIGC与事实披露
图片为AIGC创意演绎，产品信息以实物与文件为准。
""",
                encoding="utf-8",
            )

            errors = self.validator.validate_run(run_dir)

            self.assertNotIn("xiaohongshu命中高风险表达: 金融或收益承诺", errors)

            publish.write_text(
                publish.read_text(encoding="utf-8").replace(
                    "本内容不承诺保值、升值或投资回报。",
                    "购买后稳赚，还会升值。",
                ),
                encoding="utf-8",
            )

            errors = self.validator.validate_run(run_dir)

            self.assertIn("xiaohongshu命中高风险表达: 金融或收益承诺", errors)

    def test_public_example_is_a_valid_content_run(self):
        example = (
            PROJECT_ROOT
            / "examples"
            / "content-runs"
            / "2026-08-01-label-reading"
        )

        errors = self.validator.validate_run(example)

        self.assertEqual(errors, [])

    def test_public_example_contains_external_seedance_handoff(self):
        example = (
            PROJECT_ROOT
            / "examples"
            / "content-runs"
            / "2026-08-01-label-reading"
        )
        handoff = example / "video-master" / "external-generation"

        self.assertTrue((handoff / "00-开始前必读.md").exists())
        self.assertTrue((handoff / "00-镜头状态表.csv").exists())
        self.assertGreaterEqual(len(list(handoff.glob("S??-*"))), 2)

    def test_legacy_pack_validator_supports_help(self):
        output = io.StringIO()
        with redirect_stdout(output):
            result = self.pack_validator.main(
                ["validate_content_pack.py", "--help"]
            )

        self.assertEqual(result, 0)
        self.assertIn("用法:", output.getvalue())

    def test_legacy_pack_validator_rejects_empty_required_sections(self):
        with workspace_tempdir() as tmp:
            path = Path(tmp) / "empty-pack.md"
            path.write_text(
                "\n\n".join(
                    f"## {heading}"
                    for heading in self.pack_validator.REQUIRED_HEADINGS
                ),
                encoding="utf-8",
            )

            missing, risks = self.pack_validator.validate(path)

            self.assertEqual(missing, self.pack_validator.REQUIRED_HEADINGS)
            self.assertEqual(risks, [])


if __name__ == "__main__":
    unittest.main()
