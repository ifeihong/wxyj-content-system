#!/usr/bin/env python3
"""Validate the editable-motion and audio-continuity contract for a video master."""

from __future__ import annotations

import json
import sys
from pathlib import Path


VALID_TRANSITIONS = {"cross_dissolve", "material_match", "cut", "none"}


def validate(plan: dict[str, object]) -> list[str]:
    """Return contract errors without attempting to judge the rendered picture."""
    errors: list[str] = []
    if plan.get("version") != 2:
        errors.append("motion-plan version must be 2")

    mode = plan.get("mode")
    if mode not in {"unset", "V1", "V2", "V3", "V4"}:
        errors.append("mode must be unset, V1, V2, V3, or V4")

    shots = plan.get("shots")
    if not isinstance(shots, list):
        return errors + ["shots must be a list"]

    for index, shot in enumerate(shots, start=1):
        if not isinstance(shot, dict):
            errors.append(f"shot {index} must be an object")
            continue
        shot_id = shot.get("shot_id", f"shot {index}")
        transition = shot.get("transition_out", {})
        if not isinstance(transition, dict):
            errors.append(f"{shot_id}: transition_out must be an object")
        else:
            transition_type = transition.get("type")
            if transition_type not in VALID_TRANSITIONS:
                errors.append(f"{shot_id}: unsupported transition type")
            frames = transition.get("duration_frames", 0)
            if transition_type == "cross_dissolve" and not 8 <= frames <= 24:
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
        if not isinstance(start_scale, (int, float)) or not 0.98 <= start_scale <= 1.02:
            errors.append(f"{shot_id}: start_scale must be near 100%")
        if not isinstance(end_scale, (int, float)):
            errors.append(f"{shot_id}: end_scale is required")
        elif shot.get("motion_pattern") == "hold":
            if not str(shot.get("motion_rationale", "")).strip():
                errors.append(f"{shot_id}: hold requires motion_rationale")
        elif isinstance(start_scale, (int, float)) and end_scale <= start_scale:
            errors.append(f"{shot_id}: end_scale must exceed start_scale for continuous motion")

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
    if audio.get("tail_extension_seconds", 0) and audio.get("tail_music_continuity") != "pass":
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
