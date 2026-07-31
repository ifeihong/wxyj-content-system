from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path


RETURN_NAME = re.compile(
    r"^(?P<date>\d{8})-wxyj-(?P<topic>[a-z0-9-]+)-"
    r"(?P<shot>s\d{2})-(?P<role>[a-z0-9-]+)-seedance-"
    r"v(?P<version>\d{2})(?:-candidate-[ab])?\.(?:mp4|mov)$",
    re.IGNORECASE,
)
SHOT_DIR_PATTERN = re.compile(
    r"^(?P<shot>S\d{2})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$"
)
RUN_DIR_PATTERN = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})-"
    r"(?P<topic>[a-z0-9]+(?:-[a-z0-9]+)*)$"
)
SCREEN_CAPTURE_MARKERS = (
    "screenshot",
    "screen-record",
    "screen_record",
    "录屏",
    "截屏",
    "截图",
)


def _parse_scalar(value: str) -> object:
    stripped = value.strip()
    if not stripped:
        return ""
    if stripped in {"true", "false"}:
        return stripped == "true"
    if stripped.startswith('"') and stripped.endswith('"'):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return stripped[1:-1]
    try:
        return int(stripped)
    except ValueError:
        pass
    try:
        return float(stripped)
    except ValueError:
        return stripped


def parse_shot_contract(path: Path) -> dict[str, object]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"shot contract not found: {path}")
    contract: dict[str, object] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line or raw_line.startswith((" ", "#", "-")):
            continue
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        if key == "references":
            break
        contract[key.strip()] = _parse_scalar(value)
    return contract


def validate_probe(
    metadata: dict[str, object],
    contract: dict[str, object],
) -> list[str]:
    errors: list[str] = []
    if metadata.get("codec_type") != "video":
        errors.append("文件不包含可解码的视频流")

    try:
        width = int(metadata["width"])
        height = int(metadata["height"])
    except (KeyError, TypeError, ValueError):
        errors.append("无法读取视频宽高")
        return errors

    if width <= 0 or height <= 0:
        errors.append("视频宽高必须大于0")
    else:
        divisor = math.gcd(width, height)
        reduced = (width // divisor, height // divisor)
        if reduced != (9, 16):
            errors.append(
                f"画幅必须为精确9:16，当前为{width}×{height}"
            )

    resolution = contract.get("final_resolution")
    if resolution == "1080p" and height < 1920:
        errors.append("成片分辨率不足：1080p任务高度至少1920")
    elif resolution == "720p" and height < 1280:
        errors.append("成片分辨率不足：720p任务高度至少1280")

    try:
        actual_duration = float(metadata["duration"])
        expected_duration = float(contract["duration_seconds"])
        tolerance = float(
            contract.get("duration_tolerance_seconds", 0.75)
        )
    except (KeyError, TypeError, ValueError):
        errors.append("无法核对视频时长")
    else:
        if abs(actual_duration - expected_duration) > tolerance:
            errors.append(
                "视频时长不符："
                f"目标{expected_duration:g}秒±{tolerance:g}秒，"
                f"当前{actual_duration:.2f}秒"
            )
    return errors


def validate_filename(
    path: Path,
    run_date: str,
    topic_slug: str,
    shot_id: str,
) -> list[str]:
    path = Path(path)
    errors: list[str] = []
    lower_name = path.name.lower()
    if any(marker in lower_name for marker in SCREEN_CAPTURE_MARKERS):
        errors.append("禁止回传录屏或截图文件")
    match = RETURN_NAME.fullmatch(path.name)
    if match is None:
        errors.append("回传文件名不符合外部Seedance命名规范")
        return errors

    expected_date = run_date.replace("-", "")
    if match.group("date") != expected_date:
        errors.append("回传文件日期与内容运行包不一致")
    if match.group("topic").lower() != topic_slug.lower():
        errors.append("回传文件主题与内容运行包不一致")
    if match.group("shot").lower() != shot_id.lower():
        errors.append("回传文件镜头号与任务目录不一致")
    return errors


def probe_video(
    video_path: Path,
    probe_command: str = "ffprobe",
) -> tuple[dict[str, object] | None, str | None]:
    executable = shutil.which(probe_command)
    if executable is None:
        return None, f"找不到{probe_command}，无法验证视频"
    command = [
        executable,
        "-v",
        "error",
        "-show_entries",
        "stream=codec_type,width,height,r_frame_rate",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(video_path),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as error:
        return None, f"无法运行{probe_command}: {error}"
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "未知解码错误"
        return None, f"视频无法解码: {detail}"
    try:
        payload = json.loads(completed.stdout)
        stream = next(
            item
            for item in payload.get("streams", [])
            if item.get("codec_type") == "video"
        )
        return {
            "codec_type": stream.get("codec_type"),
            "width": stream.get("width"),
            "height": stream.get("height"),
            "duration": payload.get("format", {}).get("duration"),
        }, None
    except (json.JSONDecodeError, StopIteration, TypeError) as error:
        return None, f"无法解析视频元数据: {error}"


def detect_persistent_black_bars(
    video_path: Path,
    width: int,
    height: int,
    ffmpeg_command: str = "ffmpeg",
) -> list[str]:
    executable = shutil.which(ffmpeg_command)
    if executable is None:
        return [f"WARNING: 找不到{ffmpeg_command}，未执行黑边诊断"]
    command = [
        executable,
        "-v",
        "info",
        "-i",
        str(video_path),
        "-vf",
        "fps=2,cropdetect=24:16:0",
        "-frames:v",
        "120",
        "-f",
        "null",
        os.devnull,
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    crops = re.findall(
        r"crop=(?P<w>\d+):(?P<h>\d+):(?P<x>\d+):(?P<y>\d+)",
        completed.stderr,
    )
    if not crops:
        return []
    recent = crops[-min(8, len(crops)) :]
    vertical_bars = [
        int(y) > 0 and int(y) + int(crop_height) < height
        for _, crop_height, _, y in recent
    ]
    if len(vertical_bars) >= 3 and all(vertical_bars):
        return ["WARNING: 检测到持续上下黑边，必须人工复核"]
    return []


def validate_return(
    video_path: Path,
    shot_dir: Path,
    *,
    probe_command: str = "ffprobe",
) -> list[str]:
    video_path = Path(video_path)
    shot_dir = Path(shot_dir)
    errors: list[str] = []
    if not video_path.is_file():
        return [f"回传文件不存在: {video_path}"]

    shot_match = SHOT_DIR_PATTERN.fullmatch(shot_dir.name)
    if shot_match is None:
        errors.append("镜头目录命名不合法")
        shot_id = "S00"
    else:
        shot_id = shot_match.group("shot")

    try:
        run_dir = shot_dir.parents[2]
    except IndexError:
        return errors + ["无法从镜头目录定位内容运行包"]
    run_match = RUN_DIR_PATTERN.fullmatch(run_dir.name)
    if run_match is None:
        errors.append("内容运行目录命名不合法")
        run_date = "0000-00-00"
        topic_slug = "unknown"
    else:
        run_date = run_match.group("date")
        topic_slug = run_match.group("topic")
    errors.extend(
        validate_filename(video_path, run_date, topic_slug, shot_id)
    )

    try:
        contract = parse_shot_contract(shot_dir / "shot.yaml")
    except (FileNotFoundError, ValueError) as error:
        return errors + [str(error)]
    expected_name = contract.get("output_name")
    if expected_name and video_path.name != expected_name:
        errors.append("回传文件名与shot.yaml的output_name不一致")

    metadata, probe_error = probe_video(video_path, probe_command)
    if probe_error:
        return errors + [probe_error]
    assert metadata is not None
    errors.extend(validate_probe(metadata, contract))
    if not errors:
        errors.extend(
            detect_persistent_black_bars(
                video_path,
                int(metadata["width"]),
                int(metadata["height"]),
            )
        )
    return errors


def _print_report(messages: list[str]) -> None:
    warnings = [
        message.removeprefix("WARNING:").strip()
        for message in messages
        if message.startswith("WARNING:")
    ]
    errors = [
        message
        for message in messages
        if not message.startswith("WARNING:")
    ]
    print("ERROR")
    if errors:
        for message in errors:
            print(f"- {message}")
    else:
        print("- none")
    print("WARNING")
    if warnings:
        for message in warnings:
            print(f"- {message}")
    else:
        print("- none")
    print("PASS")
    print("- yes" if not errors else "- no")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a returned external Seedance video."
    )
    parser.add_argument("video", type=Path)
    parser.add_argument("--shot-dir", type=Path, required=True)
    parser.add_argument("--probe-command", default="ffprobe")
    parser.add_argument(
        "--accept",
        action="store_true",
        help="Copy a clean return to video-master/accepted/.",
    )
    args = parser.parse_args()

    messages = validate_return(
        args.video,
        args.shot_dir,
        probe_command=args.probe_command,
    )
    _print_report(messages)
    errors = [
        message
        for message in messages
        if not message.startswith("WARNING:")
    ]
    if args.accept and not errors:
        accepted = args.shot_dir.parents[1] / "accepted" / args.video.name
        accepted.parent.mkdir(parents=True, exist_ok=True)
        if accepted.exists() and accepted.read_bytes() != args.video.read_bytes():
            print(f"ERROR\n- accepted目标已存在且内容不同: {accepted}")
            return 1
        if not accepted.exists():
            shutil.copy2(args.video, accepted)
        print(f"accepted: {accepted}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
