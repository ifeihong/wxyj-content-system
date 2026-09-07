#!/usr/bin/env python3
"""Validate the editable-motion and audio-continuity contract for a video master."""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path


VALID_TRANSITIONS = {"cross_dissolve", "material_match", "cut", "none"}


def positive_number(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def validate(plan: dict[str, object], expected_shots: list | None = None) -> list[str]:
    """Return contract errors without attempting to judge the rendered picture."""
    errors: list[str] = []
    if not isinstance(plan, dict):
        return ["motion-plan must be an object"]
    if type(plan.get("version")) is not int or plan.get("version") != 2:
        errors.append("motion-plan version must be 2")

    mode = plan.get("mode")
    if not isinstance(mode, str) or mode not in {"V1", "V2", "V3", "V4"}:
        errors.append("mode cannot be unset; select V1, V2, V3, or V4")

    shots = plan.get("shots")
    if not isinstance(shots, list):
        return errors + ["shots must be a list"]
    if not shots:
        errors.append("shots must not be empty")
    if expected_shots is not None:
        actual_ids = [s.get("shot_id") for s in shots if isinstance(s, dict)]
        expected_ids = [s.get("id") for s in expected_shots if isinstance(s, dict)]
        if actual_ids != expected_ids:
            errors.append("motion shot order differs from production-plan")
    seen = set()

    for index, shot in enumerate(shots, start=1):
        if not isinstance(shot, dict):
            errors.append(f"shot {index} must be an object")
            continue
        shot_id = shot.get("shot_id", f"shot {index}")
        if not isinstance(shot_id, str) or not re.fullmatch(r"S\d{2}", shot_id):
            errors.append(f"shot {index}: invalid shot_id")
            continue
        if shot_id in seen:
            errors.append(f"{shot_id}: duplicate shot_id")
        seen.add(shot_id)
        if shot.get("source_type") not in ("static", "seedance", "video"):
            errors.append(f"{shot_id}: invalid source_type")
        if expected_shots is not None:
            expected = next((s for s in expected_shots if isinstance(s, dict) and s.get("id") == shot_id), {})
            if shot.get("source_type") != expected.get("source_type"):
                errors.append(f"{shot_id}: source differs from production-plan")
            if shot.get("source_type") == "static":
                requested = expected.get("requested_motion")
                if not isinstance(requested, dict) or not all(k in requested for k in ("motion_pattern", "start_scale", "end_scale")):
                    errors.append(f"{shot_id}: missing requested_motion in production-plan")
                else:
                    for key in ("motion_pattern", "start_scale", "end_scale", "start_position", "end_position"):
                        if key in requested and requested[key] != shot.get(key):
                            errors.append(f"{shot_id}: {key} differs from requested_motion")
        transition = shot.get("transition_out", {})
        if not isinstance(transition, dict):
            errors.append(f"{shot_id}: transition_out must be an object")
        else:
            transition_type = transition.get("type")
            if not isinstance(transition_type, str) or transition_type not in VALID_TRANSITIONS:
                errors.append(f"{shot_id}: unsupported transition type")
            frames = transition.get("duration_frames", 0)
            if type(frames) is not int or frames < 0:
                errors.append(f"{shot_id}: duration_frames must be a non-negative integer")
            elif transition_type == "cross_dissolve" and not 8 <= frames <= 24:
                errors.append(f"{shot_id}: cross_dissolve must be 8–24 frames")

        if shot.get("source_type") != "static":
            continue
        assets = shot.get("asset_paths")
        if not isinstance(assets, list) or len(assets) != 1:
            errors.append(f"{shot_id}: a static shot must use exactly one asset")
        if shot.get("motion_duration_scope") != "full_shot":
            errors.append(f"{shot_id}: motion must run for the full shot")

        start_scale = shot.get("start_scale")
        end_scale = shot.get("end_scale")
        pattern = shot.get("motion_pattern")
        if not isinstance(pattern, str) or pattern not in {"push-in", "pull-out", "pan", "hold"}:
            errors.append(f"{shot_id}: unsupported motion pattern")
        if not positive_number(start_scale) or not positive_number(end_scale):
            errors.append(f"{shot_id}: scales must be finite positive numbers")
        elif pattern == "hold":
            if not isinstance(shot.get("motion_rationale"), str) or not shot["motion_rationale"].strip():
                errors.append(f"{shot_id}: hold requires motion_rationale")
            if start_scale != end_scale:
                errors.append(f"{shot_id}: hold cannot change scale")
        elif pattern == "push-in" and end_scale <= start_scale:
            errors.append(f"{shot_id}: push-in must increase scale")
        elif pattern == "pull-out" and end_scale >= start_scale:
            errors.append(f"{shot_id}: pull-out must decrease scale")
        elif pattern == "pan":
            positions = [shot.get("start_position"), shot.get("end_position")]
            valid = all(isinstance(p, list) and len(p) == 2 and all(
                type(v) in (int, float) and math.isfinite(v) for v in p) for p in positions)
            if not valid or positions[0] == positions[1] or start_scale != end_scale:
                errors.append(f"{shot_id}: pan requires distinct positions and equal scales")

        checkpoints = shot.get("rendered_checkpoints")
        if not isinstance(checkpoints, dict) or not all(
            checkpoints.get(key) is True for key in ("start", "mid", "end")
        ):
            errors.append(f"{shot_id}: start/mid/end rendered checkpoints must pass")

    audio = plan.get("audio_mix", {})
    if not isinstance(audio, dict):
        return errors + ["audio_mix must be an object"]
    checks = audio.get("segment_listening", {})
    if not isinstance(checks, dict) or not all(
        checks.get(key) == "pass" for key in ("opening", "voice", "tail")
    ):
        errors.append("audio_mix: opening, voice, and tail listening checks must pass")
    tail = audio.get("tail_extension_seconds", 0)
    if type(tail) not in (int, float) or not math.isfinite(tail) or tail < 0:
        errors.append("audio_mix: invalid tail_extension_seconds")
    if tail and audio.get("tail_music_continuity") != "pass":
        errors.append("audio_mix: tail extension requires tail_music_continuity=pass")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("用法: validate_video_motion_plan.py <motion-plan.json>")
        return 2
    path = Path(argv[1])
    if not path.is_file():
        print(f"文件不存在: {path}")
        return 2
    try:
        plan = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"无法读取 motion plan: {exc}")
        return 2
    errors = validate(plan)
    if errors:
        print("视频运动计划未通过:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("视频运动计划验证通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
