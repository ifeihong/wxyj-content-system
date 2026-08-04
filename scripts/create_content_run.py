from __future__ import annotations

import argparse
import json
import re
from datetime import date as date_type
from pathlib import Path


ALLOWED_PLATFORMS = ("xiaohongshu", "douyin", "weixin-channels")
VIDEO_PLATFORMS = {"douyin", "weixin-channels"}
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION = "2.5.0"
DEFAULT_PRODUCT = "马克瑞普之选亚伯乐1996年单桶"


PUBLISH_TEMPLATES = {
    "xiaohongshu": """# 小红书发布包

## 主标题

## 备选标题

## 一句话钩子

## 发布正文

## 话题标签

## 首评

## CTA
""",
    "douyin": """# 抖音发布包

## 主标题

## 备选标题

## 3秒钩子

## 视频简介

## 话题标签

## 置顶评论

## CTA
""",
    "weixin-channels": """# 视频号发布包

## 主标题

## 备选标题

## 5秒观看理由

## 视频描述

## 话题标签

## 首评

## 朋友圈转发文案

## CTA
""",
}


def _write_once(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def _validate_inputs(
    date: str, slug: str, platforms: list[str], product: str
) -> None:
    try:
        date_type.fromisoformat(date)
    except ValueError as exc:
        raise ValueError("date must use YYYY-MM-DD and be a real date") from exc
    if not SLUG_PATTERN.fullmatch(slug):
        raise ValueError("slug must contain lowercase letters, digits, and hyphens")
    invalid = sorted(set(platforms) - set(ALLOWED_PLATFORMS))
    if invalid:
        raise ValueError(f"unsupported platforms: {', '.join(invalid)}")
    if not platforms:
        raise ValueError("at least one platform is required")
    if not product.strip():
        raise ValueError("product must not be empty")
    if any(character in product for character in "\r\n"):
        raise ValueError("product must use a single line")


def _manifest_scalar(text: str, field: str) -> str | None:
    match = re.search(
        rf"^{re.escape(field)}:\s*(.*?)\s*$",
        text,
        re.MULTILINE,
    )
    if not match:
        return None
    value = match.group(1).strip()
    if not value:
        return None
    if value.startswith('"') and value.endswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, str) and parsed else None
    return value


def _manifest_platforms(text: str) -> list[str]:
    platforms: list[str] = []
    in_platforms = False
    for line in text.splitlines():
        if line.strip() == "platforms:":
            in_platforms = True
            continue
        if in_platforms and line.startswith("  - "):
            platforms.append(line[4:].strip())
            continue
        if in_platforms and line.strip():
            break
    return platforms


def _check_existing_manifest(
    manifest_path: Path, product: str, platforms: list[str]
) -> None:
    if not manifest_path.exists():
        return
    manifest = manifest_path.read_text(encoding="utf-8")
    existing_product = _manifest_scalar(manifest, "product")
    if existing_product is None:
        raise ValueError("existing manifest is missing product")
    if existing_product != product:
        raise ValueError("existing manifest belongs to another product")
    existing_platforms = _manifest_platforms(manifest)
    if not existing_platforms:
        raise ValueError("existing manifest does not declare platforms")
    missing = sorted(set(platforms) - set(existing_platforms))
    if missing:
        raise ValueError(
            "existing manifest does not declare requested platforms: "
            + ", ".join(missing)
        )


def needs_video_master(platforms: list[str]) -> bool:
    return bool(VIDEO_PLATFORMS.intersection(platforms))


def create_run(
    root: Path,
    date: str,
    slug: str,
    platforms: list[str],
    *,
    product: str = DEFAULT_PRODUCT,
) -> Path:
    normalized_platforms = list(dict.fromkeys(platforms))
    normalized_product = product.strip()
    _validate_inputs(date, slug, normalized_platforms, normalized_product)

    year, month, _ = date.split("-")
    run_id = f"{date}-{slug}"
    run_dir = Path(root) / year / month / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    _check_existing_manifest(
        run_dir / "manifest.yaml",
        normalized_product,
        normalized_platforms,
    )

    manifest = "\n".join(
        [
            f"run_id: {run_id}",
            f"version: {VERSION}",
            f"date: {date}",
            f"topic_slug: {slug}",
            f"product: {json.dumps(normalized_product, ensure_ascii=False)}",
            "status: draft",
            "platforms:",
            *[f"  - {platform}" for platform in normalized_platforms],
            "",
        ]
    )
    _write_once(run_dir / "manifest.yaml", manifest)
    release_manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "release_status": "working",
        "native_targets": {
            **(
                {
                    "xiaohongshu": {
                        "aspect_ratio": "3:4",
                        "target": "1086x1448 or 1536x2048",
                    }
                }
                if "xiaohongshu" in normalized_platforms
                else {}
            ),
            **(
                {
                    "video_master": {
                        "aspect_ratio": "9:16",
                        "target": "1080x1920",
                    }
                }
                if needs_video_master(normalized_platforms)
                else {}
            ),
        },
        "quality_gates": {
            "facts": "pending",
            "product_geometry": "pending",
            "public_copy": "pending",
            "media": "pending",
            "audio": "pending" if needs_video_master(normalized_platforms) else "not-applicable",
            "deliverables": "pending",
        },
        "assets": [],
    }
    _write_once(
        run_dir / "release-manifest.json",
        json.dumps(release_manifest, ensure_ascii=False, indent=2) + "\n",
    )
    _write_once(
        run_dir / "brief.md",
        "# 内容简报\n\n## 母题\n\n## 目标受众\n\n## 核心事实\n\n## 增长目标\n",
    )
    _write_once(
        run_dir / "sources.md",
        "# 素材与事实来源\n\n## 真实产品\n\n## 文件证据\n\n## AIGC参考\n\n## 待核验项\n",
    )
    _write_once(
        run_dir / "product-visual-qa.md",
        """# 产品视觉人工验收卡

## 结论

`pending` / `pass` / `fail`

## 每张发布资产

| 文件 | 产品形态 | 几何参考 | 瓶盖与瓶肩 | 酒标与液面 | 边缘融合 | 礼盒结构与内页 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- |

完整酒瓶必须核对瓶盖、瓶肩、瓶身宽高、酒标位置、液面和瓶底。开盒画面必须保持175°–180°，保留左侧白色内皮、故事文字、中央合页和右侧瓶槽。脚本只核对登记状态，不能替代人工视觉判断。
""",
    )
    _write_once(
        run_dir / "deliverables.md",
        """# 最终交付索引

## 发布状态

`working` / `publish`

## 小红书

## 抖音

## 视频号

## 共享视频母版

只列出 `release-manifest.json` 中状态为 `publish` 的资产及对应平台发布文案。
""",
    )

    for platform in normalized_platforms:
        platform_dir = run_dir / platform
        (platform_dir / "media").mkdir(parents=True, exist_ok=True)
        _write_once(platform_dir / "publish.md", PUBLISH_TEMPLATES[platform])
        _write_once(platform_dir / "qa.md", "# 发布前QA\n\n## 结论\n\n## 问题与修正\n")
        if platform == "xiaohongshu":
            _write_once(
                platform_dir / "prompts.md",
                "# 小红书逐页生产提示词\n\n## 套图视觉母版\n\n## 第1页\n",
            )

    if needs_video_master(normalized_platforms):
        video_master = run_dir / "video-master"
        for directory in (
            "external-generation",
            "incoming",
            "accepted",
            "media",
        ):
            (video_master / directory).mkdir(parents=True, exist_ok=True)
        _write_once(
            video_master / "treatment.md",
            "# 视频创意方案\n\n## 核心命题\n\n## 视觉方向\n\n## 制作模式\n",
        )
        _write_once(
            video_master / "shotlist.yaml",
            "version: 1\naspect_ratio: 9:16\nshots: []\n",
        )
        _write_once(
            video_master / "storyboard.md",
            "# 视频逐镜分镜\n\n## 镜头1\n",
        )
        _write_once(
            video_master / "edit-plan.md",
            "# 剪辑方案\n\n## 时间线\n\n## 声音\n\n## 字幕与图形\n",
        )
        _write_once(
            video_master / "motion-plan.json",
            json.dumps(
                {
                    "version": 1,
                    "mode": "unset",
                    "shots": [],
                    "audio_mix": {
                        "voice": "pending",
                        "music": "pending",
                        "effects": "pending",
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        )
        _write_once(
            video_master / "qa.md",
            "# 视频母版QA\n\n## 结论\n\n## 镜头状态\n\n## 问题与修正\n",
        )

    return run_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a non-destructive wxyj content run directory."
    )
    parser.add_argument("--root", type=Path, default=Path("outputs"))
    parser.add_argument("--date", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--product", default=DEFAULT_PRODUCT)
    parser.add_argument(
        "--platforms",
        nargs="+",
        choices=ALLOWED_PLATFORMS,
        default=list(ALLOWED_PLATFORMS),
    )
    args = parser.parse_args()
    run_dir = create_run(
        args.root,
        args.date,
        args.slug,
        args.platforms,
        product=args.product,
    )
    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
