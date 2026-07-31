#!/usr/bin/env python3
"""Validate required sections and explicit high-risk wording in a content pack."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_HEADINGS = [
    "选题标题",
    "一句话开头钩子",
    "爆款公式",
    "受众需求",
    "预估热度",
    "核心产品事实锚点",
    "推荐平台与内容形态",
    "所需真实素材",
    "转化动作",
    "合规风险提示",
]

RISK_PATTERNS = {
    "投资或升值承诺": r"稳赚|保值|升值|投资回报",
    "无法证明的绝对化": r"全球唯一|永远|最顶级|百分之百",
    "虚假紧迫": r"只剩最后一瓶|错过不再",
    "AIGC冒充真实": r"AIGC.{0,12}(真实酒厂|历史现场|真实人物|真实顾客)",
}


def _section_value(text: str, heading: str) -> str | None:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not match:
        return None
    value = match.group(1).strip()
    return value or None


def validate(path: Path) -> tuple[list[str], list[str]]:
    """Return missing required headings and categorized risky matches."""
    text = path.read_text(encoding="utf-8-sig")
    missing = [
        heading
        for heading in REQUIRED_HEADINGS
        if _section_value(text, heading) is None
    ]

    claim_text = re.sub(
        r"^##\s+合规风险提示\s*$.*?(?=^##\s+|\Z)",
        "",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    risks = []
    for category, pattern in RISK_PATTERNS.items():
        if re.search(pattern, claim_text, flags=re.IGNORECASE):
            sample = re.search(pattern, claim_text, flags=re.IGNORECASE).group(0)
            risks.append(f"{category}: {sample}")
    return missing, risks


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] in {"-h", "--help"}:
        print("用法: validate_content_pack.py <内容包.md>")
        return 0
    if len(argv) != 2:
        print("用法: validate_content_pack.py <内容包.md>")
        return 2

    path = Path(argv[1])
    if not path.is_file():
        print(f"文件不存在: {path}")
        return 2

    missing, risks = validate(path)
    if missing:
        print("缺少必填字段:")
        for heading in missing:
            print(f"- {heading}")
    if risks:
        print("高风险表述:")
        for risk in risks:
            print(f"- {risk}")
    if missing or risks:
        return 1

    print("验证通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
