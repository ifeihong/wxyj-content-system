from __future__ import annotations

import argparse
import json
import struct
import subprocess
from pathlib import Path


ALLOWED_RELEASE_STATUSES = {"working", "publish", "archived"}
ALLOWED_ASSET_STATUSES = {"working", "rejected", "publish"}
REQUIRED_GATES = (
    "facts",
    "product_geometry",
    "public_copy",
    "media",
    "audio",
    "deliverables",
)


def _load_json(path: Path, label: str, errors: list[str]) -> dict | None:
    if not path.exists():
        errors.append(f"缺少{label}: {path.name}")
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label}不是有效JSON: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label}顶层必须是对象")
        return None
    return value


def _png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        data = path.read_bytes()[:24]
    except OSError:
        return None
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    return None


def _video_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "json",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        stream = json.loads(result.stdout)["streams"][0]
        return int(stream["width"]), int(stream["height"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _dimensions(path: Path) -> tuple[int, int] | None:
    if path.suffix.lower() == ".png":
        return _png_dimensions(path)
    if path.suffix.lower() in {".mp4", ".mov"}:
        return _video_dimensions(path)
    return None


def _validate_motion_plan(run_dir: Path, errors: list[str]) -> None:
    motion_path = run_dir / "video-master" / "motion-plan.json"
    motion = _load_json(motion_path, "视频运动计划", errors)
    if motion is None or motion.get("mode") != "V4":
        return
    shots = motion.get("shots")
    if not isinstance(shots, list) or not shots:
        errors.append("V4视频运动计划必须至少包含一个镜头")
        return
    for index, shot in enumerate(shots, start=1):
        shot_id = shot.get("shot_id", f"S{index:02d}") if isinstance(shot, dict) else f"S{index:02d}"
        if not isinstance(shot, dict):
            errors.append(f"{shot_id}镜头必须是对象")
            continue
        asset_paths = shot.get("asset_paths")
        if not isinstance(asset_paths, list) or len(asset_paths) != 1:
            errors.append(f"{shot_id}每镜只允许一个静帧素材")
        if shot.get("continuous_motion") is not True:
            errors.append(f"{shot_id}必须是连续运动")
        if shot.get("direction") not in {"left-to-right", "right-to-left", "push-in", "pull-out", "locked"}:
            errors.append(f"{shot_id}缺少受控运动方向")
        start_x = shot.get("start_x")
        end_x = shot.get("end_x")
        if shot.get("direction") in {"left-to-right", "right-to-left"} and (
            not isinstance(start_x, (int, float))
            or not isinstance(end_x, (int, float))
            or start_x == end_x
        ):
            errors.append(f"{shot_id}横向运动必须填写不同的start_x与end_x")
        if not str(shot.get("transition_out", "")).strip():
            errors.append(f"{shot_id}缺少匹配的转场")


def validate_release(run_dir: Path) -> list[str]:
    run_dir = Path(run_dir)
    errors: list[str] = []
    release = _load_json(run_dir / "release-manifest.json", "发布清单", errors)
    if release is None:
        return errors

    if release.get("run_id") != run_dir.name:
        errors.append("发布清单run_id与运行目录不一致")
    release_status = release.get("release_status")
    if release_status not in ALLOWED_RELEASE_STATUSES:
        errors.append("发布清单release_status不合法")

    gates = release.get("quality_gates")
    if not isinstance(gates, dict):
        errors.append("发布清单缺少quality_gates")
        gates = {}
    required_gates = list(REQUIRED_GATES)
    if release.get("schema_version") == 2:
        required_gates.append("diversity")
    for gate in required_gates:
        if gate not in gates:
            errors.append(f"发布清单缺少质量门槛: {gate}")
        if release_status == "publish" and gates.get(gate) not in {"pass", "not-applicable"}:
            errors.append(f"发布状态为publish时{gate}必须为pass")

    assets = release.get("assets")
    if not isinstance(assets, list):
        errors.append("发布清单assets必须是数组")
        assets = []
    if release_status == "publish" and not assets:
        errors.append("发布状态为publish时必须登记至少一个发布资产")

    for index, asset in enumerate(assets, start=1):
        if not isinstance(asset, dict):
            errors.append(f"发布资产{index}必须是对象")
            continue
        if asset.get("status") not in ALLOWED_ASSET_STATUSES:
            errors.append(f"发布资产{index}状态不合法")
            continue
        if asset.get("status") != "publish":
            continue
        relative = asset.get("path")
        if not isinstance(relative, str) or not relative.strip():
            errors.append(f"发布资产{index}缺少path")
            continue
        path = (run_dir / relative).resolve()
        if not path.is_relative_to(run_dir.resolve()):
            errors.append(f"发布资产{index}路径越界")
            continue
        if not path.is_file():
            errors.append(f"发布资产不存在: {relative}")
            continue
        expected_ratio = asset.get("native_ratio")
        dimensions = _dimensions(path)
        if expected_ratio in {"3:4", "9:16"}:
            if dimensions is None:
                errors.append(f"无法读取发布资产画幅: {relative}")
            else:
                width, height = dimensions
                left, right = (3, 4) if expected_ratio == "3:4" else (9, 16)
                if width * right != height * left:
                    errors.append(f"发布资产不是原生{expected_ratio}: {relative}")

    if (run_dir / "video-master").exists():
        _validate_motion_plan(run_dir, errors)
    if not (run_dir / "product-visual-qa.md").exists():
        errors.append("缺少产品视觉人工验收卡")
    if not (run_dir / "deliverables.md").exists():
        errors.append("缺少最终交付索引")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate release readiness for a wxyj content run.")
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    errors = validate_release(args.run_dir)
    if errors:
        for error in errors:
            print(f"- {error}")
        return 1
    print("发布预检通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
