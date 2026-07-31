from __future__ import annotations

import argparse
import json
import re
from datetime import date as date_type
from pathlib import Path


RUN_NAME_PATTERN = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})-"
    r"(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$"
)
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
ALLOWED_STATUSES = {"draft", "qa", "approved", "published", "archived"}
VIDEO_PLATFORMS = {"douyin", "weixin-channels"}
VIDEO_MASTER_REQUIRED = (
    "treatment.md",
    "shotlist.yaml",
    "storyboard.md",
    "edit-plan.md",
    "qa.md",
    "external-generation",
    "incoming",
    "accepted",
    "media",
)
PLATFORM_CODES = {
    "xiaohongshu": "xhs",
    "douyin": "dy",
    "weixin-channels": "wxv",
}
BASE_DOCUMENT_REQUIREMENTS = {
    "brief.md": ("母题", "目标受众", "核心事实", "增长目标"),
    "sources.md": ("真实产品", "文件证据", "AIGC参考", "待核验项"),
}
PLATFORM_REQUIREMENTS = {
    "xiaohongshu": {
        "files": ("publish.md", "prompts.md", "qa.md", "media"),
        "headings": (
            "主标题",
            "备选标题",
            "一句话钩子",
            "发布正文",
            "话题标签",
            "首评",
            "CTA",
        ),
        "media": re.compile(
            r"^\d{8}-xhs-[a-z0-9-]+-p\d{2}-[a-z0-9-]+-v\d{2}"
            r"\.(?:png|jpe?g|webp)$"
        ),
    },
    "douyin": {
        "files": ("publish.md", "qa.md", "media"),
        "headings": (
            "主标题",
            "备选标题",
            "3秒钩子",
            "视频简介",
            "话题标签",
            "置顶评论",
            "CTA",
        ),
        "media": re.compile(
            r"^\d{8}-dy-[a-z0-9-]+-s\d{2}-[a-z0-9-]+-v\d{2}"
            r"\.(?:png|jpe?g|webp|mp4|mov)$"
        ),
    },
    "weixin-channels": {
        "files": ("publish.md", "qa.md", "media"),
        "headings": (
            "主标题",
            "备选标题",
            "5秒观看理由",
            "视频描述",
            "话题标签",
            "首评",
            "朋友圈转发文案",
            "CTA",
        ),
        "media": re.compile(
            r"^\d{8}-wxv-[a-z0-9-]+-s\d{2}-[a-z0-9-]+-v\d{2}"
            r"\.(?:png|jpe?g|webp|mp4|mov)$"
        ),
    },
}
RISK_PATTERNS = {
    "金融或收益承诺": re.compile(r"稳赚|保值|升值|投资回报"),
    "无法证明的绝对化": re.compile(r"全球唯一|永远|最顶级|百分之百"),
    "虚假紧迫": re.compile(r"只剩最后一瓶|错过不再"),
    "AIGC冒充真实": re.compile(
        r"AIGC.{0,12}(?:真实酒厂|历史现场|真实人物|真实顾客)"
    ),
}
PUBLIC_COPY_FORBIDDEN_PATTERNS = {
    "AIGC或事实核验": re.compile(
        r"AIGC|创意演绎|产品信息.{0,12}(?:实物|文件)为准|事实核验"
    ),
    "续集预告": re.compile(r"下一条|下期"),
}
NEGATION_PATTERN = re.compile(
    r"不承诺|不保证|不作|不做|不涉及|不构成|不宣称|不建议|"
    r"不支持|不提供|不鼓励|不是|不得|禁止|避免|未承诺|未保证|"
    r"无收益承诺"
)
CLAUSE_SPLIT_PATTERN = re.compile(r"[。！？；\n]|但是|但|然而|不过|却")


def _manifest_platforms(text: str) -> list[str]:
    lines = text.splitlines()
    platforms: list[str] = []
    in_platforms = False
    for line in lines:
        if line.strip() == "platforms:":
            in_platforms = True
            continue
        if in_platforms and line.startswith("  - "):
            platforms.append(line[4:].strip())
            continue
        if in_platforms and line.strip():
            break
    return platforms


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


def _section_value(text: str, heading: str) -> str | None:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return None
    value = match.group(1).strip()
    return value or None


def _contains_risk_claim(text: str, pattern: re.Pattern[str]) -> bool:
    for clause in CLAUSE_SPLIT_PATTERN.split(text):
        for match in pattern.finditer(clause):
            context = clause[max(0, match.start() - 12) : match.end()]
            if not NEGATION_PATTERN.search(context):
                return True
    return False


def validate_run(run_dir: Path) -> list[str]:
    run_dir = Path(run_dir)
    errors: list[str] = []

    if not run_dir.is_dir():
        return [f"运行目录不存在: {run_dir}"]
    run_name_match = RUN_NAME_PATTERN.fullmatch(run_dir.name)
    if not run_name_match:
        errors.append(f"运行目录命名不合法: {run_dir.name}")
        run_date = None
        run_slug = None
    else:
        run_date = run_name_match.group("date")
        run_slug = run_name_match.group("slug")
        try:
            date_type.fromisoformat(run_date)
        except ValueError:
            errors.append(f"运行目录日期不合法: {run_date}")
        parent_month = run_dir.parent.name
        parent_year = run_dir.parent.parent.name
        if re.fullmatch(r"\d{2}", parent_month) and re.fullmatch(
            r"\d{4}", parent_year
        ):
            expected_year, expected_month, _ = run_date.split("-")
            if parent_year != expected_year or parent_month != expected_month:
                errors.append("运行目录年月层级与运行日期不一致")

    for filename in ("manifest.yaml", "brief.md", "sources.md"):
        if not (run_dir / filename).exists():
            errors.append(f"缺少基础文件: {filename}")

    for filename, headings in BASE_DOCUMENT_REQUIREMENTS.items():
        path = run_dir / filename
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        for heading in headings:
            if _section_value(text, heading) is None:
                errors.append(f"{filename}缺少内容: {heading}")

    manifest_path = run_dir / "manifest.yaml"
    manifest = (
        manifest_path.read_text(encoding="utf-8")
        if manifest_path.exists()
        else ""
    )
    manifest_values = {
        field: _manifest_scalar(manifest, field)
        for field in (
            "run_id",
            "version",
            "date",
            "topic_slug",
            "product",
            "status",
        )
    }
    for field, value in manifest_values.items():
        if value is None:
            errors.append(f"manifest缺少字段: {field}")

    if run_name_match:
        if manifest_values["run_id"] not in (None, run_dir.name):
            errors.append("manifest的run_id与运行目录不一致")
        if manifest_values["date"] not in (None, run_date):
            errors.append("manifest的date与运行目录不一致")
        if manifest_values["topic_slug"] not in (None, run_slug):
            errors.append("manifest的topic_slug与运行目录不一致")

    version = manifest_values["version"]
    if version is not None and not VERSION_PATTERN.fullmatch(version):
        errors.append(f"manifest版本号不合法: {version}")
    status = manifest_values["status"]
    if status is not None and status not in ALLOWED_STATUSES:
        errors.append(f"manifest状态不合法: {status}")

    if "platforms:" not in manifest:
        errors.append("manifest缺少字段: platforms")

    platforms = _manifest_platforms(manifest)
    if not platforms:
        errors.append("manifest未声明平台")
    if len(platforms) != len(set(platforms)):
        errors.append("manifest平台列表包含重复项")

    if VIDEO_PLATFORMS.intersection(platforms):
        video_master = run_dir / "video-master"
        for relative in VIDEO_MASTER_REQUIRED:
            if not (video_master / relative).exists():
                errors.append(f"video-master缺少文件或目录: {relative}")

    for platform in PLATFORM_REQUIREMENTS:
        if (run_dir / platform).exists() and platform not in platforms:
            errors.append(f"存在未在manifest声明的平台目录: {platform}")

    for platform in platforms:
        requirement = PLATFORM_REQUIREMENTS.get(platform)
        if requirement is None:
            errors.append(f"不支持的平台: {platform}")
            continue
        platform_dir = run_dir / platform
        for filename in requirement["files"]:
            if not (platform_dir / filename).exists():
                errors.append(f"{platform}缺少文件: {filename}")

        publish_path = platform_dir / "publish.md"
        publish = (
            publish_path.read_text(encoding="utf-8")
            if publish_path.exists()
            else ""
        )
        for heading in requirement["headings"]:
            if _section_value(publish, heading) is None:
                errors.append(f"{platform}发布文案缺少内容: {heading}")

        qa_path = platform_dir / "qa.md"
        qa = qa_path.read_text(encoding="utf-8") if qa_path.exists() else ""
        if _section_value(qa, "结论") is None:
            errors.append(f"{platform}的qa.md缺少内容: 结论")

        for risk_name, pattern in RISK_PATTERNS.items():
            if _contains_risk_claim(publish, pattern):
                errors.append(f"{platform}命中高风险表达: {risk_name}")

        for label, pattern in PUBLIC_COPY_FORBIDDEN_PATTERNS.items():
            if pattern.search(publish):
                errors.append(f"{platform}公开文案包含内部说明: {label}")

        media_dir = platform_dir / "media"
        if media_dir.is_dir():
            for media in media_dir.iterdir():
                if media.name == ".gitkeep":
                    continue
                if media.is_file() and not requirement["media"].fullmatch(media.name):
                    errors.append(f"媒体文件命名不合法: {media.name}")
                    continue
                if media.is_file() and run_date and run_slug:
                    expected_prefix = (
                        f"{run_date.replace('-', '')}-"
                        f"{PLATFORM_CODES[platform]}-{run_slug}-"
                    )
                    if not media.name.startswith(expected_prefix):
                        errors.append(
                            "媒体文件与运行日期或主题不一致: "
                            f"{media.name}"
                        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a wxyj content run directory."
    )
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    errors = validate_run(args.run_dir)
    if errors:
        for error in errors:
            print(f"- {error}")
        return 1
    print("内容运行包验证通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
