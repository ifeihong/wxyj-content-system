"""Shared file-integrity and canvas checks, not visual acceptance."""
from pathlib import Path

VIDEO_RATIOS = {"9:16": (9, 16), "3:4": (3, 4)}
INPUT_MODES = {"text-to-video", "first-frame", "first-last-frame", "reference-guided"}


def read_png_dimensions(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValueError("PNG完整校验需要Pillow；缺少依赖时不能判定通过") from exc
    try:
        with Image.open(path) as image:
            if image.format != "PNG":
                raise ValueError("文件不是PNG")
            image.verify()
        # verify checks the container; load also decodes the compressed pixels.
        with Image.open(path) as image:
            image.load()
            return image.size
    except (OSError, SyntaxError, ValueError) as exc:
        raise ValueError(f"PNG无法完整解码: {path.name}: {exc}") from exc


def nonempty_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())
