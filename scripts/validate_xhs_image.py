from __future__ import annotations

import struct
import sys
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def read_png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) < 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise ValueError("仅支持带有效IHDR头的PNG文件")
    return struct.unpack(">II", header[16:24])


def validate_xhs_image(path: Path) -> list[str]:
    if not path.is_file():
        return [f"文件不存在: {path}"]
    try:
        width, height = read_png_dimensions(path)
    except (OSError, ValueError) as exc:
        return [f"{path.name}: {exc}"]
    if width * 4 != height * 3:
        return [
            f"{path.name}: {width}x{height}，小红书首轮原生成文件必须为精确3:4，"
            "不得靠裁切或拉伸补救"
        ]
    return []


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args == ["--help"]:
        print("用法: python scripts/validate_xhs_image.py <image.png> [image.png ...]")
        return 0 if args else 2

    errors: list[str] = []
    for value in args:
        path = Path(value)
        current = validate_xhs_image(path)
        errors.extend(current)
        if not current:
            width, height = read_png_dimensions(path)
            print(f"PASS {path}: {width}x{height} (3:4)")
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
