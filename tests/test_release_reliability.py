import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release_validator", ROOT / "scripts/validate_release_preflight.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class ReleaseReliabilityTests(unittest.TestCase):
    def test_publish_rejects_working_only_assets_and_unset_motion(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "video-master").mkdir()
            (root / "video-master/motion-plan.json").write_text('{"version":2,"mode":"unset","shots":[]}', encoding="utf-8")
            release = {"schema_version": 5, "run_id": root.name, "release_status": "publish",
                       "quality_gates": {key: "pass" for key in (*validator.REQUIRED_GATES, "diversity", "motion")},
                       "assets": [{"status": "working"}]}
            (root / "release-manifest.json").write_text(json.dumps(release), encoding="utf-8")
            errors = validator.validate_release(root)
            self.assertTrue(any("发布资产" in e for e in errors))
            self.assertTrue(any("unset" in e for e in errors))
            self.assertTrue(any("成片" in e for e in errors))

    def test_invalid_schema_and_missing_ratio_are_errors(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "image.png").write_bytes(b"broken")
            release = {"schema_version": "5", "run_id": root.name, "release_status": "publish",
                       "quality_gates": {}, "assets": [{"status": "publish", "path": "image.png"}]}
            (root / "release-manifest.json").write_text(json.dumps(release), encoding="utf-8")
            errors = validator.validate_release(root)
            self.assertTrue(any("schema_version" in e for e in errors))
            self.assertTrue(any("native_ratio" in e for e in errors))
