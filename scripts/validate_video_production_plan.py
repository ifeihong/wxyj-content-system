"""Check handoff integrity; visual/semantic approval still requires human review."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

try:
    from scripts.media_contract import read_png_dimensions, nonempty_text, INPUT_MODES, VIDEO_RATIOS
except ModuleNotFoundError:
    from media_contract import read_png_dimensions, nonempty_text, INPUT_MODES, VIDEO_RATIOS


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_plan(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)


def validate_package(run_dir: Path, stage: str | None = None) -> list[str]:
    root = Path(run_dir).resolve()
    errors = []
    try:
        plan = load_plan(root / "video-master/production-plan.json")
    except (OSError, ValueError) as exc:
        return [f"production-plan: {exc}"]
    if not isinstance(plan, dict):
        return ["production-plan must be an object"]
    selected = stage or plan.get("stage")
    if not isinstance(selected, str) or selected not in {"draft", "ready"}:
        return ["stage must be draft or ready"]
    strict = selected == "ready"
    revision = plan.get("revision")
    if type(revision) is not int or revision < 1:
        errors.append("revision must be a positive integer")
    if type(plan.get("schema_version")) is not int or plan.get("schema_version") != 1:
        errors.append("unsupported production-plan schema")

    def local_file(value, label):
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{label}: missing path")
            return None
        try:
            path = (root / value).resolve()
        except (OSError, ValueError):
            errors.append(f"{label}: invalid path")
            return None
        if not path.is_relative_to(root) or not path.is_file():
            errors.append(f"{label}: missing file or path outside run: {value}")
            return None
        return path

    def evidence(item, label):
        if not isinstance(item, dict):
            errors.append(f"{label}: missing evidence object")
            return None
        path = local_file(item.get("path"), label)
        if item.get("revision") != revision:
            errors.append(f"{label}: stale revision")
        if path:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if item.get("sha256") != digest:
                errors.append(f"{label}: stale or missing sha256")
        return path

    canvas = plan.get("canvas", {})
    if not isinstance(canvas, dict):
        canvas = {}
    width, height = canvas.get("width"), canvas.get("height")
    ratio = VIDEO_RATIOS.get(canvas.get("aspect_ratio")) if isinstance(canvas.get("aspect_ratio"), str) else None
    if (type(width) is not int or type(height) is not int
            or width <= 0 or height <= 0 or ratio is None):
        errors.append("invalid canvas")
    elif width * ratio[1] != height * ratio[0]:
        errors.append("canvas ratio mismatch")
    if strict and not all(nonempty_text(plan.get(key)) for key in ("story", "style")):
        errors.append("ready package requires story and shared style")

    shots = plan.get("shots")
    if not isinstance(shots, list):
        return errors + ["shots must be a list"]
    if strict and not shots:
        errors.append("ready package has no shots")
    ids, fingerprints, hashes = set(), set(), set()
    previous = None
    for shot in shots:
        if not isinstance(shot, dict):
            errors.append("shot must be an object")
            continue
        sid = shot.get("id")
        if not isinstance(sid, str) or not re.fullmatch(r"S\d{2}", sid):
            errors.append("invalid shot id")
            continue
        if sid in ids:
            errors.append(f"{sid}: duplicate shot id")
        ids.add(sid)
        fields = ("subject_region", "view", "framing", "visual_role")
        fingerprint = tuple(shot[key].strip().casefold() if nonempty_text(shot.get(key)) else "" for key in fields)
        if strict and not all(fingerprint):
            errors.append(f"{sid}: incomplete visual fingerprint")
        if all(fingerprint) and fingerprint[:3] in fingerprints:
            errors.append(f"{sid}: repeated visual fingerprint across sequence")
        fingerprints.add(fingerprint[:3])
        if not strict:
            continue
        for key in ("state_in", "state_out", "narration", "visual_support"):
            if not nonempty_text(shot.get(key)):
                errors.append(f"{sid}: missing {key}")
        if previous and not nonempty_text(shot.get("bridge_from_previous")):
            errors.append(f"{sid}: missing continuity bridge")
        if previous and previous.get("state_out") != shot.get("state_in") and not nonempty_text(shot.get("state_change_reason")):
            errors.append(f"{sid}: unexplained product state change")
        previous = shot
        duration = shot.get("edit_duration_seconds")
        if type(duration) not in (int, float) or not 0 < duration < 600:
            errors.append(f"{sid}: invalid edit duration")
        source = shot.get("source_type")
        if not isinstance(source, str) or source not in {"static", "seedance"}:
            errors.append(f"{sid}: unsupported source_type")
        asset = evidence(shot.get("image"), f"{sid} image")
        if asset:
            digest = hashlib.sha256(asset.read_bytes()).hexdigest()
            if digest in hashes:
                errors.append(f"{sid}: reused image bytes")
            hashes.add(digest)
            try:
                if read_png_dimensions(asset) != (width, height):
                    errors.append(f"{sid}: image dimensions differ from canvas")
            except (OSError, ValueError) as exc:
                errors.append(f"{sid}: {exc}")
        review = shot.get("review", {})
        evidence(review, f"{sid} visual review")
        if not isinstance(review, dict) or review.get("status") != "pass":
            errors.append(f"{sid}: visual review pending")
        references = shot.get("references", [])
        if not isinstance(references, list) or not references:
            errors.append(f"{sid}: missing references")
            references = []
        roles = set()
        for ref in references:
            if not isinstance(ref, dict) or not isinstance(ref.get("role"), str):
                errors.append(f"{sid}: invalid reference")
                continue
            roles.add(ref["role"])
            evidence(ref, f"{sid} reference")
        if type(shot.get("full_bottle")) is not bool:
            errors.append(f"{sid}: full_bottle must be a boolean")
        if shot.get("full_bottle") is True and not {"geometry_master", "dimension_check"} <= roles:
            errors.append(f"{sid}: full bottle lacks geometry/dimension references")
        if source == "seedance":
            ext = shot.get("external", {})
            if not isinstance(ext, dict):
                ext = {}
            mode = ext.get("input_mode")
            if not isinstance(mode, str) or mode not in INPUT_MODES:
                errors.append(f"{sid}: unsupported input_mode")
            image = shot.get("image")
            if mode in ("first-frame", "first-last-frame") and (not isinstance(image, dict) or ext.get("first_frame") != image.get("path")):
                errors.append(f"{sid}: first_frame differs from generated image")
            if mode == "first-last-frame":
                last = evidence(ext.get("last_frame"), f"{sid} last_frame")
                if last:
                    try:
                        if read_png_dimensions(last) != (width, height):
                            errors.append(f"{sid}: last_frame canvas mismatch")
                    except (OSError, ValueError) as exc:
                        errors.append(f"{sid}: {exc}")
            if mode in ("reference-guided", "text-to-video"):
                if not nonempty_text(ext.get("mode_reason")):
                    errors.append(f"{sid}: non-first-frame mode requires mode_reason")
                if ext.get("first_frame") or ext.get("last_frame"):
                    errors.append(f"{sid}: input_mode conflicts with frame slots")
                if mode == "text-to-video" and shot.get("full_bottle") is True:
                    errors.append(f"{sid}: text-to-video cannot lock full product geometry")
            seconds = ext.get("generation_duration_seconds")
            speed = ext.get("playback_speed", 1)
            if (type(seconds) not in (int, float) or type(duration) not in (int, float)
                    or type(speed) not in (int, float) or not 0 < speed <= 4
                    or not 0 < seconds < 600 or not 0 < duration <= seconds / speed):
                errors.append(f"{sid}: insufficient generation duration")
            for key in ("positive", "negative", "combined", "task_card"):
                evidence(ext.get(key), f"{sid} {key}")
            name = ext.get("output_name", "")
            if not isinstance(name, str) or not name.endswith(".mp4") or sid.lower() not in name.lower():
                errors.append(f"{sid}: invalid return name")

    if strict:
        review = plan.get("sequence_review", {})
        evidence(review, "sequence contact-sheet review")
        if not isinstance(review, dict) or review.get("status") != "pass":
            errors.append("sequence review pending")
        documents = plan.get("documents", [])
        required = {"video-master/storyboard.md", "video-master/edit-plan.md", "video-master/motion-plan.json"}
        if not isinstance(documents, list):
            documents = []
        for doc in documents:
            path = evidence(doc, "derived document")
            if path:
                required.discard(path.relative_to(root).as_posix())
        if required:
            errors.append(f"missing derived documents: {', '.join(sorted(required))}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--stage", choices=("draft", "ready"), default=None)
    args = parser.parse_args()
    errors = validate_package(args.run_dir, args.stage)
    for error in errors:
        print(f"FAIL {error}")
    if not errors:
        print("PASS 交付登记检查；不替代实际图像、连续性和视听验收")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
