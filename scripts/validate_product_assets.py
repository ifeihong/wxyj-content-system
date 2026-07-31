from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


DEFAULT_PRODUCT_ROOT = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "products"
    / "mackillops-choice-aberlour-1996"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def validate_assets(product_root: Path) -> list[str]:
    product_root = product_root.resolve()
    manifest_path = product_root / "asset-manifest.json"
    image_root = product_root / "reference-images"
    errors: list[str] = []

    if not manifest_path.is_file():
        return [f"缺少资产清单：{manifest_path}"]
    if not image_root.is_dir():
        return [f"缺少参考图目录：{image_root}"]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"资产清单无法读取：{exc}"]

    entries = manifest.get("assets")
    if not isinstance(entries, list):
        return ["资产清单的 assets 必须是数组"]

    declared_count = manifest.get("asset_count")
    if declared_count != len(entries):
        errors.append(
            f"asset_count={declared_count}，实际清单条目={len(entries)}"
        )

    expected: dict[str, str] = {}
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            errors.append(f"第{index}条资产不是对象")
            continue
        filename = entry.get("file")
        expected_hash = entry.get("sha256")
        if not isinstance(filename, str) or not filename.endswith(".png"):
            errors.append(f"第{index}条资产文件名无效")
            continue
        if filename in expected:
            errors.append(f"资产文件名重复：{filename}")
            continue
        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            errors.append(f"资产哈希无效：{filename}")
            continue
        expected[filename] = expected_hash.upper()

    actual = {path.name for path in image_root.glob("*.png")}
    for filename in sorted(set(expected) - actual):
        errors.append(f"缺少参考图：{filename}")
    for filename in sorted(actual - set(expected)):
        errors.append(f"存在未登记参考图：{filename}")

    for filename in sorted(set(expected) & actual):
        actual_hash = sha256_file(image_root / filename)
        if actual_hash != expected[filename]:
            errors.append(f"参考图哈希不一致：{filename}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="验证威熏邑境内置产品参考图数量、登记状态和 SHA-256"
    )
    parser.add_argument(
        "product_root",
        nargs="?",
        type=Path,
        default=DEFAULT_PRODUCT_ROOT,
        help="包含 asset-manifest.json 和 reference-images 的产品资产目录",
    )
    args = parser.parse_args()

    errors = validate_assets(args.product_root)
    if errors:
        for error in errors:
            print(f"错误：{error}")
        return 1

    print("产品参考图验证通过：17张文件与资产清单一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
