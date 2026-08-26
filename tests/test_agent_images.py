from __future__ import annotations

import importlib.util
import shutil
import struct
import unittest
import uuid
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
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", width, height)
    )


class AgentImageValidationTests(unittest.TestCase):
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
