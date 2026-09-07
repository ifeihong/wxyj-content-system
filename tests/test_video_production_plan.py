from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("production_validator", ROOT / "scripts/validate_video_production_plan.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def png(width, height, color):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress((b"\0" + bytes(color) * width) * height)) + chunk(b"IEND", b""))


class ProductionPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "video-master").mkdir()
        self.plan = {"schema_version": 1, "revision": 1, "stage": "ready",
                     "canvas": {"width": 1080, "height": 1920, "aspect_ratio": "9:16"},
                     "story": "先看到盒内故事，再看瓶身", "style": "深木色柔光", "shots": []}
        for i, source in enumerate(("static", "seedance"), 1):
            sid = f"S{i:02}"
            shot = {"id": sid, "source_type": source, "subject_region": f"region-{i}",
                    "view": "front", "framing": "medium", "visual_role": f"role-{i}",
                    "state_in": "open", "state_out": "open", "narration": "与画面关联的旁白",
                    "visual_support": "可见的产品部位", "bridge_from_previous": "同一礼盒空间",
                    "edit_duration_seconds": 5, "full_bottle": True,
                    "image": self.evidence(f"video-master/{sid}.png", png(1080, 1920, [i, 2, 3])),
                    "review": dict(self.evidence(f"video-master/{sid}-review.md"), status="pass"),
                    "references": [dict(self.evidence(f"video-master/{sid}-{role}.png", png(10, 10, [2, 3, 4])), role=role)
                                   for role in ("geometry_master", "dimension_check")]}
            if source == "seedance":
                shot["external"] = {"input_mode": "first-frame", "first_frame": shot["image"]["path"],
                                    "generation_duration_seconds": 6, "output_name": f"test-{sid.lower()}.mp4",
                                    **{key: self.evidence(f"video-master/{sid}-{key}.txt")
                                       for key in ("positive", "negative", "combined", "task_card")}}
            self.plan["shots"].append(shot)
        self.plan["sequence_review"] = dict(self.evidence("video-master/sequence-review.md"), status="pass")
        self.plan["documents"] = [self.evidence(f"video-master/{name}")
                                  for name in ("storyboard.md", "edit-plan.md", "motion-plan.json")]

    def evidence(self, path, data=b"review fixture, not production approval"):
        (self.root / path).write_bytes(data)
        return {"path": path, "sha256": hashlib.sha256(data).hexdigest(), "revision": 1}

    def check(self, stage=None):
        (self.root / "video-master/production-plan.json").write_text(json.dumps(self.plan), encoding="utf-8")
        return validator.validate_package(self.root, stage)

    def test_accepts_complete_registry(self):
        self.assertEqual(self.check(), [])

    def test_rejects_truncated_image_with_matching_hash(self):
        shot = self.plan["shots"][0]
        shot["image"] = self.evidence(shot["image"]["path"], png(1080, 1920, [1, 2, 3])[:24])
        self.assertTrue(self.check())

    def test_rejects_null_text_and_non_boolean_full_bottle(self):
        for field, value in (("narration", None), ("visual_support", None),
                             ("full_bottle", "true"), ("full_bottle", None)):
            with self.subTest(field=field, value=value):
                shot = self.plan["shots"][0]
                old = shot[field]
                shot[field] = value
                self.assertTrue(self.check())
                shot[field] = old

    def test_role_change_does_not_disguise_duplicate_view(self):
        a, b = self.plan["shots"]
        for key in ("subject_region", "view", "framing"):
            b[key] = a[key]
        self.assertTrue(self.check())

    def test_first_last_frame_checks_last_frame_evidence(self):
        ext = self.plan["shots"][1]["external"]
        ext.update(input_mode="first-last-frame", last_frame=self.evidence("video-master/last.png", png(1080, 1920, [7, 8, 9])))
        self.assertEqual(self.check(), [])
        (self.root / "video-master/last.png").write_bytes(b"broken")
        self.assertTrue(self.check())

    def test_draft_is_not_ready(self):
        self.plan.update(stage="draft", shots=[])
        self.assertEqual(self.check(), [])
        self.assertTrue(self.check("ready"))

    def test_all_pairs_duplicate_fingerprint(self):
        duplicate = dict(self.plan["shots"][0], id="S03")
        self.plan["shots"].append(duplicate)
        self.assertTrue(any("repeated visual fingerprint" in e for e in self.check()))

    def test_rejects_reused_image_even_with_new_names(self):
        self.plan["shots"][1]["image"] = self.evidence("video-master/renamed.png", (self.root / "video-master/S01.png").read_bytes())
        self.assertTrue(any("reused image bytes" in e for e in self.check()))

    def test_rejects_stale_file_hash(self):
        (self.root / "video-master/S02-positive.txt").write_text("updated prompt", encoding="utf-8")
        self.assertTrue(any("sha256" in e for e in self.check()))

    def test_rejects_stale_review_revision(self):
        self.plan["shots"][0]["review"]["revision"] = 0
        self.assertTrue(any("stale revision" in e for e in self.check()))

    def test_rejects_missing_firstframe(self):
        (self.root / "video-master/S02.png").unlink()
        self.assertTrue(self.check())

    def test_rejects_label_only_geometry(self):
        self.plan["shots"][0]["references"] = [dict(self.plan["shots"][0]["references"][0], role="label_detail")]
        self.assertTrue(any("geometry/dimension" in e for e in self.check()))

    def test_rejects_unexplained_state_jump(self):
        self.plan["shots"][1]["state_in"] = "closed"
        self.assertTrue(any("state change" in e for e in self.check()))

    def test_rejects_near_ratio(self):
        self.plan["canvas"].update(width=941, height=1672)
        self.assertTrue(any("ratio mismatch" in e for e in self.check()))

    def test_accepts_requested_three_four(self):
        self.plan["canvas"].update(width=1080, height=1440, aspect_ratio="3:4")
        for i, shot in enumerate(self.plan["shots"]):
            shot["image"] = self.evidence(shot["image"]["path"], png(1080, 1440, [i, 4, 5]))
        self.assertEqual(self.check(), [])

    def test_rejects_outside_path(self):
        self.plan["shots"][0]["review"]["path"] = "../../outside.md"
        self.assertTrue(any("outside run" in e for e in self.check()))

    def test_duplicate_json_key_is_not_silently_overwritten(self):
        path = self.root / "video-master/production-plan.json"
        path.write_text('{"revision":1,"revision":2}', encoding="utf-8")
        self.assertTrue(any("duplicate JSON key" in e for e in validator.validate_package(self.root)))

    def test_invalid_image_object_returns_error_not_crash(self):
        self.plan["shots"][1]["image"] = None
        self.assertTrue(self.check())

    def test_accepts_explicit_slow_motion_duration(self):
        self.plan["shots"][1]["edit_duration_seconds"] = 10
        self.plan["shots"][1]["external"].update(generation_duration_seconds=5, playback_speed=0.5)
        self.assertEqual(self.check(), [])

    def test_rejects_insufficient_duration(self):
        self.plan["shots"][1]["external"]["generation_duration_seconds"] = 2
        self.assertTrue(any("duration" in e for e in self.check()))


if __name__ == "__main__":
    unittest.main()
