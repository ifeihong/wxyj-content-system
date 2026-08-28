from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = PROJECT_ROOT / "scripts" / "validate_video_motion_plan.py"
    spec = importlib.util.spec_from_file_location("video_motion_plan", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VideoMotionPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load_validator()

    @staticmethod
    def valid_plan() -> dict[str, object]:
        return {
            "version": 2,
            "mode": "V4",
            "shots": [
                {
                    "shot_id": "S01",
                    "source_type": "static",
                    "asset_paths": ["agent-images/static-shots/S01.png"],
                    "motion_pattern": "push-in",
                    "motion_duration_scope": "full_shot",
                    "start_scale": 1.0,
                    "end_scale": 1.06,
                    "transition_out": {
                        "type": "cross_dissolve",
                        "duration_frames": 18,
                    },
                    "rendered_checkpoints": {
                        "start": True,
                        "mid": True,
                        "end": True,
                    },
                }
            ],
            "audio_mix": {
                "voice": "pass",
                "music": "pass",
                "effects": "pass",
                "tail_extension_seconds": 1.5,
                "tail_music_continuity": "pass",
                "segment_listening": {
                    "opening": "pass",
                    "voice": "pass",
                    "tail": "pass",
                },
            },
        }

    def test_accepts_one_asset_continuous_push_and_audio_continuity(self):
        self.assertEqual(self.validator.validate(self.valid_plan()), [])

    def test_rejects_motion_that_stops_before_shot_end(self):
        plan = self.valid_plan()
        shot = plan["shots"][0]
        assert isinstance(shot, dict)
        shot["motion_duration_scope"] = "partial"
        errors = self.validator.validate(plan)
        self.assertTrue(any("full shot" in error for error in errors))

    def test_rejects_static_hold_without_a_safety_rationale(self):
        plan = self.valid_plan()
        shot = plan["shots"][0]
        assert isinstance(shot, dict)
        shot["motion_pattern"] = "hold"
        shot["end_scale"] = 1.0
        errors = self.validator.validate(plan)
        self.assertTrue(any("hold requires" in error for error in errors))

    def test_rejects_tail_music_level_discontinuity(self):
        plan = self.valid_plan()
        audio = plan["audio_mix"]
        assert isinstance(audio, dict)
        audio["tail_music_continuity"] = "fail"
        errors = self.validator.validate(plan)
        self.assertTrue(any("tail extension" in error for error in errors))

