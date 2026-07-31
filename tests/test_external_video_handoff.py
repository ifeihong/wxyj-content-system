from __future__ import annotations

import importlib.util
import shutil
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


@contextmanager
def workspace_tempdir():
    test_root = (PROJECT_ROOT / ".test-work").resolve()
    path = (test_root / uuid.uuid4().hex).resolve()
    path.mkdir(parents=True)
    try:
        yield path
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


class ExternalVideoHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module(
            "create_external_video_handoff",
            "create_external_video_handoff.py",
        )
        cls.return_validator = load_module(
            "validate_external_video_return",
            "validate_external_video_return.py",
        )

    @staticmethod
    def valid_spec() -> dict[str, object]:
        return {
            "shot_id": "S01",
            "slug": "date-reveal",
            "title": "情人节日期揭晓",
            "input_mode": "first-frame",
            "aspect_ratio": "9:16",
            "duration_seconds": 5,
            "draft_resolution": "720p",
            "final_resolution": "1080p",
            "candidate_target": 1,
            "max_attempts": 2,
            "references": [
                {
                    "order": 1,
                    "file": "S01-first-frame-9x16.png",
                    "role": "first_frame",
                    "required": True,
                }
            ],
            "prompt_positive": "暖金色光线缓慢扫过酒标。",
            "prompt_negative": "瓶型变形，白边，灰边，黑边。",
        }

    def test_create_handoff_writes_complete_platform_neutral_shot_package(self):
        with workspace_tempdir() as workspace:
            run_dir = workspace / "2026-08-01-label-reading"
            source_root = workspace / "source"
            source_root.mkdir()
            (source_root / "S01-first-frame-9x16.png").write_bytes(
                b"reference-image"
            )

            handoff = self.module.create_handoff(
                run_dir,
                [self.valid_spec()],
                source_root,
            )

            shot = handoff / "S01-date-reveal"
            for relative in (
                "任务卡.md",
                "shot.yaml",
                "prompt-all-in-one.txt",
                "prompt-positive.txt",
                "prompt-negative.txt",
                "references/S01-first-frame-9x16.png",
            ):
                self.assertTrue((shot / relative).exists(), relative)

            task = (shot / "任务卡.md").read_text(encoding="utf-8")
            self.assertNotIn("第三方平台名称", task)
            self.assertIn("9:16", task)
            self.assertIn("最大尝试次数：2", task)
            self.assertIn("参考图文件位置", task)
            self.assertIn(
                "references/S01-first-frame-9x16.png",
                task,
            )
            self.assertIn("## 可直接复制：一体化提示词", task)
            self.assertIn("## 可直接复制：正向提示词", task)
            self.assertIn("## 可直接复制：负向提示词", task)
            self.assertIn("暖金色光线缓慢扫过酒标。", task)
            self.assertIn("瓶型变形，白边，灰边，黑边。", task)

    def test_create_handoff_never_overwrites_user_edits(self):
        with workspace_tempdir() as workspace:
            run_dir = workspace / "2026-08-01-label-reading"
            source_root = workspace / "source"
            source_root.mkdir()
            (source_root / "S01-first-frame-9x16.png").write_bytes(
                b"reference-image"
            )
            handoff = self.module.create_handoff(
                run_dir,
                [self.valid_spec()],
                source_root,
            )
            prompt = (
                handoff
                / "S01-date-reveal"
                / "prompt-positive.txt"
            )
            prompt.write_text("用户已调整的提示词", encoding="utf-8")

            self.module.create_handoff(
                run_dir,
                [self.valid_spec()],
                source_root,
            )

            self.assertEqual(
                prompt.read_text(encoding="utf-8"),
                "用户已调整的提示词",
            )

    def test_create_handoff_rejects_conflicting_reference_overwrite(self):
        with workspace_tempdir() as workspace:
            run_dir = workspace / "2026-08-01-label-reading"
            source_root = workspace / "source"
            source_root.mkdir()
            reference = source_root / "S01-first-frame-9x16.png"
            reference.write_bytes(b"reference-image-v1")
            self.module.create_handoff(
                run_dir,
                [self.valid_spec()],
                source_root,
            )
            reference.write_bytes(b"reference-image-v2")

            with self.assertRaisesRegex(ValueError, "reference conflict"):
                self.module.create_handoff(
                    run_dir,
                    [self.valid_spec()],
                    source_root,
                )

    def test_validate_shot_spec_rejects_missing_mode_and_reference_order(self):
        invalid = self.valid_spec()
        invalid.pop("input_mode")
        references = invalid["references"]
        assert isinstance(references, list)
        references[0].pop("order")

        errors = self.module.validate_shot_spec(invalid)

        joined = "\n".join(errors)
        self.assertIn("input_mode", joined)
        self.assertIn("references.order", joined)

    def test_return_validator_accepts_exact_nine_sixteen_metadata(self):
        metadata = {
            "width": 1080,
            "height": 1920,
            "duration": 5.1,
            "codec_type": "video",
        }
        contract = {
            "aspect_ratio": "9:16",
            "duration_seconds": 5,
            "duration_tolerance_seconds": 0.75,
            "final_resolution": "1080p",
        }

        self.assertEqual(
            self.return_validator.validate_probe(metadata, contract),
            [],
        )

    def test_return_validator_rejects_three_four_and_wrong_duration(self):
        metadata = {
            "width": 1080,
            "height": 1440,
            "duration": 8.0,
            "codec_type": "video",
        }
        contract = {
            "aspect_ratio": "9:16",
            "duration_seconds": 5,
            "duration_tolerance_seconds": 0.75,
            "final_resolution": "1080p",
        }

        errors = self.return_validator.validate_probe(metadata, contract)

        self.assertTrue(any("9:16" in error for error in errors))
        self.assertTrue(any("时长" in error for error in errors))

    def test_return_validator_rejects_random_download_name(self):
        errors = self.return_validator.validate_filename(
            Path("seedance_download_123.mp4"),
            "2026-08-01",
            "label-reading",
            "S01",
        )

        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
