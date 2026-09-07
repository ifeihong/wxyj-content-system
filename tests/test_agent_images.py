from __future__ import annotations

import importlib.util
import json
import shutil
import struct
import unittest
import uuid
import zlib
from contextlib import contextmanager
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = PROJECT_ROOT / ".test-work"
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate_agent_images.py"


@contextmanager
def workspace_tempdir():
    path = (TEST_ROOT / uuid.uuid4().hex).resolve()
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        if not path.is_relative_to(TEST_ROOT.resolve()):
            raise RuntimeError(f"unsafe test cleanup path: {path}")
        shutil.rmtree(path, ignore_errors=True)


def write_png(path: Path, width: int, height: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress((b"\0" + b"\0\0\0" * width) * height)) + chunk(b"IEND", b""))


class AgentImageValidationTests(unittest.TestCase):
    def test_truncated_png_rejected(self):
        with workspace_tempdir() as run_dir:
            path = run_dir / "broken.png"
            write_png(path, 1080, 1920)
            path.write_bytes(path.read_bytes()[:24])
            with self.assertRaises(ValueError):
                self.module.read_png_dimensions(path)

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("validate_agent_images", SCRIPT_PATH)
        assert spec and spec.loader
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_accepts_exact_native_video_assets(self):
        with workspace_tempdir() as run_dir:
            for directory in (
                "video-master/agent-images/seedance-references",
                "video-master/agent-images/static-shots",
            ):
                write_png(run_dir / directory / "S01-v01.png", 1080, 1920)
            self.assertEqual(self.module.validate_agent_images(run_dir), [])

    def test_rejects_near_but_not_exact_nine_sixteen(self):
        with workspace_tempdir() as run_dir:
            write_png(
                run_dir / "video-master/agent-images/seedance-references/S01-v01.png",
                941,
                1672,
            )
            write_png(
                run_dir / "video-master/agent-images/static-shots/S02-v01.png",
                1080,
                1920,
            )
            errors = self.module.validate_agent_images(run_dir)
            self.assertEqual(len(errors), 1)
            self.assertIn("必须为精确1080×1920", errors[0])

    def test_declared_static_only_three_four_does_not_require_seedance(self):
        with workspace_tempdir() as run_dir:
            path = "video-master/agent-images/static-shots/S01.png"
            write_png(run_dir / path, 1080, 1440)
            plan = {"canvas": {"width": 1080, "height": 1440, "aspect_ratio": "3:4"},
                    "shots": [{"image": {"path": path}}]}
            (run_dir / "video-master/production-plan.json").write_text(json.dumps(plan), encoding="utf-8")
            self.assertEqual(self.module.validate_agent_images(run_dir), [])
