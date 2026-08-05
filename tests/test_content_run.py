from __future__ import annotations

import importlib.util
import json
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
        cls.release_validator = load_module(
            "validate_release_preflight", "validate_release_preflight.py"
        )
        cls.diversity_validator = load_module(
            "validate_content_diversity", "validate_content_diversity.py"
        )
        cls.performance_analyzer = load_module(
            "analyze_performance", "analyze_performance.py"
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
                "release-manifest.json",
                "creative-record.json",
                "brief.md",
                "sources.md",
                "product-visual-qa.md",
                "deliverables.md",
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
                "video-master/motion-plan.json",
                "video-master/qa.md",
                "video-master/external-generation",
                "video-master/incoming",
                "video-master/accepted",
                "video-master/media",
            ]
            for relative in expected:
                self.assertTrue((run_dir / relative).exists(), relative)

            xhs_publish = (run_dir / "xiaohongshu" / "publish.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("## 采用标题", xhs_publish)
            self.assertIn("## 最终素材顺序", xhs_publish)

    def test_release_preflight_rejects_v4_fake_motion_and_unapproved_gates(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp),
                "2026-08-08",
                "sensory-journey",
                ["douyin", "weixin-channels"],
            )
            release_path = run_dir / "release-manifest.json"
            release_path.write_text(
                """{
  "schema_version": 1,
  "run_id": "2026-08-08-sensory-journey",
  "release_status": "publish",
  "quality_gates": {
    "facts": "pass",
    "product_geometry": "pending",
    "public_copy": "pass",
    "media": "pass",
    "deliverables": "pass"
  },
  "assets": []
}
""",
                encoding="utf-8",
            )
            motion_path = run_dir / "video-master" / "motion-plan.json"
            motion_path.write_text(
                """{
  "version": 1,
  "mode": "V4",
  "shots": [
    {
      "shot_id": "S01",
      "asset_paths": ["a.png", "b.png"],
      "continuous_motion": false,
      "direction": "left-to-right",
      "start_x": -43,
      "end_x": 0,
      "transition_out": "soft-light-wipe"
    }
  ]
}
""",
                encoding="utf-8",
            )

            errors = self.release_validator.validate_release(run_dir)

            joined = "\n".join(errors)
            self.assertIn("product_geometry必须为pass", joined)
            self.assertIn("每镜只允许一个静帧素材", joined)
            self.assertIn("必须是连续运动", joined)

    def test_release_preflight_requires_diversity_gate_for_schema_two(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp), "2026-08-08", "diversity-release", ["xiaohongshu"]
            )
            release_path = run_dir / "release-manifest.json"
            release = release_path.read_text(encoding="utf-8")
            release = release.replace(
                '"release_status": "working"',
                '"release_status": "publish"',
            )
            release_path.write_text(release, encoding="utf-8")

            errors = self.release_validator.validate_release(run_dir)

            self.assertIn(
                "发布状态为publish时diversity必须为pass",
                errors,
            )

    def test_content_run_validator_invokes_release_preflight(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp), "2026-08-08", "release-gate", ["xiaohongshu"]
            )
            (run_dir / "release-manifest.json").unlink()

            errors = self.validator.validate_run(run_dir)

            self.assertIn("缺少发布清单: release-manifest.json", errors)

    def test_diversity_validator_rejects_recent_creative_fingerprint(self):
        with workspace_tempdir() as tmp:
            root = Path(tmp)
            candidate = root / "creative-record.json"
            candidate.write_text(
                """{
  "content_id": "2026-08-08-sensory-journey",
  "date": "2026-08-08",
  "status": "publish-candidate",
  "theme_family": "sensory-journey",
  "primary_fact_ids": ["tasting-dried-fruit"],
  "hero_view_id": "bottle-front",
  "view_ids": ["bottle-front", "label-macro", "box-open-front-180"],
  "typography_mode": "sherry-depth",
  "hook_pattern": "sensory-metaphor",
  "cta_type": "comment"
}
""",
                encoding="utf-8",
            )
            ledger = root / "creative-ledger.csv"
            ledger.write_text(
                "content_id,date,theme_family,primary_fact_ids,hero_view_id,view_ids,typography_mode,hook_pattern,cta_type\n"
                "2026-08-01-label-reading,2026-08-01,sensory-journey,tasting-dried-fruit,bottle-front,bottle-front;label-macro,sherry-depth,sensory-metaphor,save\n",
                encoding="utf-8",
            )

            errors = self.diversity_validator.validate_diversity(
                candidate, ledger
            )

            self.assertIn("30天内创意指纹重复", "\n".join(errors))

    def test_diversity_validator_allows_same_theme_with_new_execution(self):
        with workspace_tempdir() as tmp:
            root = Path(tmp)
            candidate = root / "creative-record.json"
            candidate.write_text(
                """{
  "content_id": "2026-08-08-gift-ritual",
  "date": "2026-08-08",
  "status": "publish-candidate",
  "theme_family": "sensory-journey",
  "primary_fact_ids": ["gift-box-story"],
  "hero_view_id": "box-open-front-180",
  "view_ids": ["box-open-front-180", "bottle-right-45"],
  "typography_mode": "gift-ritual",
  "hook_pattern": "occasion-question",
  "cta_type": "share"
}
""",
                encoding="utf-8",
            )
            ledger = root / "creative-ledger.csv"
            ledger.write_text(
                "content_id,date,theme_family,primary_fact_ids,hero_view_id,view_ids,typography_mode,hook_pattern,cta_type\n"
                "2026-08-01-label-reading,2026-08-01,sensory-journey,tasting-dried-fruit,bottle-front,bottle-front;label-macro,sherry-depth,sensory-metaphor,save\n",
                encoding="utf-8",
            )

            self.assertEqual(
                self.diversity_validator.validate_diversity(candidate, ledger),
                [],
            )

    def test_content_run_validator_requires_v26_creative_record(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp), "2026-08-08", "creative-gate", ["xiaohongshu"]
            )
            (run_dir / "creative-record.json").unlink()

            errors = self.validator.validate_run(run_dir)

            self.assertIn("缺少创意记录: creative-record.json", errors)

    def test_content_run_validator_requires_v27_performance_brief(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp), "2026-08-08", "performance-gate", ["xiaohongshu"]
            )
            (run_dir / "performance-brief.json").unlink()

            errors = self.validator.validate_run(run_dir)

            self.assertIn("缺少性能简报: performance-brief.json", errors)

    def test_content_run_validator_requires_v27_experiment_card(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp), "2026-08-08", "experiment-gate", ["xiaohongshu"]
            )
            record_path = run_dir / "creative-record.json"
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record.update(
                {
                    "status": "publish-candidate",
                    "theme_family": "flavor-journey",
                    "primary_fact_ids": ["tasting-dried-fruit"],
                    "hero_view_id": "label-macro",
                    "view_ids": ["label-macro"],
                    "typography_mode": "sherry-depth",
                    "hook_pattern": "sensory-metaphor",
                    "cta_type": "comment",
                }
            )
            record.pop("experiment")
            record_path.write_text(
                json.dumps(record, ensure_ascii=False), encoding="utf-8"
            )

            errors = self.validator.validate_run(run_dir)

            self.assertIn("发布候选缺少experiment", errors)

    def test_diversity_validator_rejects_third_consecutive_typography_mode(self):
        with workspace_tempdir() as tmp:
            root = Path(tmp)
            candidate = root / "creative-record.json"
            candidate.write_text(
                """{
  "content_id": "2026-08-08-label-detail",
  "date": "2026-08-08",
  "status": "publish-candidate",
  "theme_family": "label-reading",
  "primary_fact_ids": ["abv-51"],
  "hero_view_id": "label-macro",
  "view_ids": ["label-macro", "bottle-left-45"],
  "typography_mode": "archive-label",
  "hook_pattern": "field-decoding",
  "cta_type": "save"
}
""",
                encoding="utf-8",
            )
            ledger = root / "creative-ledger.csv"
            ledger.write_text(
                "content_id,date,theme_family,primary_fact_ids,hero_view_id,view_ids,typography_mode,hook_pattern,cta_type\n"
                "2026-08-07-a,2026-08-07,date-story,date-1996,bottle-front,bottle-front,archive-label,time-contrast,comment\n"
                "2026-08-06-b,2026-08-06,cask-story,cask-261311,bottle-right-45,bottle-right-45,archive-label,number-proof,save\n",
                encoding="utf-8",
            )

            errors = self.diversity_validator.validate_diversity(
                candidate, ledger
            )

            self.assertIn("同一typography_mode不得连续使用三次", errors)

    def test_diversity_validator_rejects_recent_visual_recipe(self):
        with workspace_tempdir() as tmp:
            root = Path(tmp)
            candidate = root / "creative-record.json"
            candidate.write_text(
                """{
  "content_id": "2026-08-08-new-copy",
  "date": "2026-08-08",
  "status": "publish-candidate",
  "theme_family": "date-story",
  "primary_fact_ids": ["date-2026"],
  "hero_view_id": "bottle-front",
  "view_ids": ["bottle-front", "box-open-front-180"],
  "typography_mode": "valentine-time",
  "hook_pattern": "question",
  "cta_type": "share"
}
""",
                encoding="utf-8",
            )
            ledger = root / "creative-ledger.csv"
            ledger.write_text(
                "content_id,date,theme_family,primary_fact_ids,hero_view_id,view_ids,typography_mode,hook_pattern,cta_type\n"
                "2026-08-01-old,2026-08-01,date-story,date-1996,bottle-front,bottle-front,valentine-time,time-contrast,comment\n",
                encoding="utf-8",
            )

            errors = self.diversity_validator.validate_diversity(
                candidate, ledger
            )

            self.assertIn(
                "14天内主题、首图机位与版式路线重复",
                "\n".join(errors),
            )

    def test_diversity_validator_requires_ledger_for_publish_candidate(self):
        with workspace_tempdir() as tmp:
            root = Path(tmp)
            candidate = root / "creative-record.json"
            candidate.write_text(
                """{
  "content_id": "2026-08-08-new-topic",
  "date": "2026-08-08",
  "status": "publish-candidate",
  "theme_family": "gift-ritual",
  "primary_fact_ids": ["gift-box-story"],
  "hero_view_id": "box-open-front-180",
  "view_ids": ["box-open-front-180"],
  "typography_mode": "gift-ritual",
  "hook_pattern": "occasion-question",
  "cta_type": "share"
}
""",
                encoding="utf-8",
            )

            errors = self.diversity_validator.validate_diversity(
                candidate, root / "missing-ledger.csv"
            )

            self.assertIn("创意台账不存在", "\n".join(errors))

    def test_diversity_validator_requires_experiment_when_declared(self):
        candidate = {
            "content_id": "2026-08-08-retention-test",
            "date": "2026-08-08",
            "status": "publish-candidate",
            "theme_family": "flavor-journey",
            "primary_fact_ids": ["tasting-dried-fruit"],
            "hero_view_id": "label-macro",
            "view_ids": ["label-macro"],
            "typography_mode": "sherry-depth",
            "hook_pattern": "sensory-metaphor",
            "cta_type": "comment",
            "experiment": {
                "variable": "",
                "hypothesis": "",
                "success_metric": "",
                "baseline": "",
                "result": "pending",
            },
        }

        errors = self.diversity_validator.validate_record(candidate)

        self.assertIn("发布候选缺少实验字段: variable", errors)
        self.assertIn("发布候选缺少实验字段: hypothesis", errors)
        self.assertIn("发布候选缺少实验字段: success_metric", errors)

    def test_performance_analyzer_ignores_immature_rows_and_warns_theme_cooldown(self):
        with workspace_tempdir() as tmp:
            log = Path(tmp) / "performance-log.csv"
            log.write_text(
                "content_id,platform,published_at,hours_since_publish,theme_family,content_format,play_or_impressions,average_watch_seconds,two_second_bounce_rate,cover_click_rate\n"
                "2026-08-01-date-a,douyin,2026-08-01T12:00:00,72,date-story,video,100,4.0,0.60,\n"
                "2026-08-03-date-b,douyin,2026-08-03T12:00:00,48,date-story,video,120,6.0,0.50,\n"
                "unknown-age-row,douyin,2026-08-05T09:00:00,,date-story,video,10,20.0,0.01,\n",
                encoding="utf-8",
            )

            brief = self.performance_analyzer.analyze_performance(
                log,
                candidate_date="2026-08-05",
                theme_family="date-story",
            )

            self.assertEqual(brief["mature_rows"], 2)
            self.assertEqual(brief["observation_rows"], 1)
            self.assertTrue(brief["theme_cooldown"]["active"])
            self.assertEqual(
                brief["theme_cooldown"]["recent_content_ids"],
                ["2026-08-01-date-a", "2026-08-03-date-b"],
            )
            self.assertTrue(
                any(
                    "0.0–0.8秒内呈现产品或酒标可见动作" in rule
                    for rule in brief["platform_prompt_rules"]["douyin"]
                )
            )

    def test_create_run_seeds_performance_brief_and_experiment(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp), "2026-08-08", "performance-brief", ["xiaohongshu"]
            )

            brief = json.loads(
                (run_dir / "performance-brief.json").read_text(encoding="utf-8")
            )
            record = json.loads(
                (run_dir / "creative-record.json").read_text(encoding="utf-8")
            )

            self.assertEqual(brief["baseline_status"], "not-analyzed")
            self.assertEqual(record["experiment"]["result"], "pending")
            self.assertEqual(record["campaign_override"], "")

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

    def test_validator_reports_invalid_version_without_crashing(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp), "2026-08-08", "bad-version", ["xiaohongshu"]
            )
            manifest = run_dir / "manifest.yaml"
            manifest.write_text(
                manifest.read_text(encoding="utf-8").replace(
                    "version: 2.7.0", "version: not-semver"
                ),
                encoding="utf-8",
            )

            errors = self.validator.validate_run(run_dir)

            self.assertIn("manifest版本号不合法: not-semver", errors)

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

    def test_validator_rejects_internal_disclosure_in_public_copy(self):
        with workspace_tempdir() as tmp:
            run_dir = self.creator.create_run(
                Path(tmp), "2026-08-01", "public-copy", ["xiaohongshu"]
            )
            publish = run_dir / "xiaohongshu" / "publish.md"
            publish.write_text(
                publish.read_text(encoding="utf-8").replace(
                    "## 发布正文\n",
                    "## 发布正文\n画面含AIGC创意演绎，产品信息以实物与文件为准。\n",
                ),
                encoding="utf-8",
            )

            errors = self.validator.validate_run(run_dir)

            self.assertIn("xiaohongshu公开文案包含内部说明: AIGC或事实核验", errors)

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
