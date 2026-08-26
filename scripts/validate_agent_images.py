from __future__ import annotations

import struct
import sys
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
TARGET_SIZE = (1080, 1920)
REQUIRED_DIRECTORIES = (
    "video-master/agent-images/seedance-references",
    "video-master/agent-images/static-shots",
)


def read_png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) < 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise ValueError("仅支持带有效IHDR头的PNG文件")
    return struct.unpack(">II", header[16:24])


def validate_agent_images(run_dir: Path) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_DIRECTORIES:
        directory = run_dir / relative
        if not directory.is_dir():
            errors.append(f"缺少Agent生图目录: {relative}")
            continue
        images = sorted(directory.glob("*.png"))
        if not images:
            errors.append(f"没有可验收的Agent图片: {relative}")
            continue
        for image in images:
            try:
                dimensions = read_png_dimensions(image)
            except (OSError, ValueError) as exc:
                errors.append(f"{image.name}: {exc}")
                continue
            if dimensions != TARGET_SIZE:
                errors.append(
                    f"{image.name}: {dimensions[0]}x{dimensions[1]}，"
                    "Agent视频素材必须为精确1080×1920原生9:16"
                )
    return errors


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("用法: python scripts/validate_agent_images.py <content-run-dir>")
        return 2

    run_dir = Path(args[0])
    errors = validate_agent_images(run_dir)
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1
    print("PASS Agent静态镜头与Seedance首帧均为精确1080×1920原生9:16")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
