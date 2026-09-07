from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from scripts.media_contract import read_png_dimensions
except ModuleNotFoundError:
    from media_contract import read_png_dimensions


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
TARGET_SIZE = (1080, 1920)
REQUIRED_DIRECTORIES = (
    "video-master/agent-images/seedance-references",
    "video-master/agent-images/static-shots",
)


def validate_agent_images(run_dir: Path) -> list[str]:
    errors: list[str] = []
    plan_path = run_dir / "video-master/production-plan.json"
    if plan_path.exists():
        try:
            plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
            canvas = plan["canvas"]
            target = (canvas["width"], canvas["height"])
            ratio = {"9:16": (9, 16), "3:4": (3, 4)}[canvas["aspect_ratio"]]
            if not all(type(n) is int and n > 0 for n in target) or target[0] * ratio[1] != target[1] * ratio[0]:
                return ["production-plan画幅无效"]
            shots = plan["shots"]
            if not isinstance(shots, list) or not shots:
                return ["production-plan尚未登记实际镜头图片"]
            for shot in shots:
                image = (run_dir / shot["image"]["path"]).resolve()
                if not image.is_relative_to(run_dir.resolve()):
                    errors.append("production-plan图片路径越界")
                elif read_png_dimensions(image) != target:
                    errors.append(f"{image.name}: 图片尺寸与production-plan画幅不一致")
            return errors
        except (OSError, ValueError, TypeError, KeyError) as exc:
            return [f"production-plan图片登记无效: {exc}"]
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
    print("PASS Agent图片尺寸符合登记画幅；不证明原生生成来源或产品视觉一致性")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
