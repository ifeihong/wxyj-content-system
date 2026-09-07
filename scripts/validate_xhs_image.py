from __future__ import annotations

import sys
from pathlib import Path

try:
    from scripts.media_contract import read_png_dimensions
except ModuleNotFoundError:
    from media_contract import read_png_dimensions


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
