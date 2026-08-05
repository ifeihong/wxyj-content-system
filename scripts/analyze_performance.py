from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from statistics import median


MATURITY_HOURS = 48.0
ESTABLISHED_SAMPLE_SIZE = 10
THEME_COOLDOWN_DAYS = 7

FIELD_ALIASES = {
    "content_id": ("content_id", "内容ID"),
    "platform": ("platform", "平台"),
    "published_at": ("published_at", "发布日期"),
    "hours_since_publish": ("hours_since_publish", "发布后小时数"),
    "theme_family": ("theme_family", "主题族", "母题"),
    "two_second_bounce_rate": ("two_second_bounce_rate", "2秒跳出率"),
}


def _value(row: dict[str, str], name: str) -> str:
    for alias in FIELD_ALIASES[name]:
        value = row.get(alias, "")
        if value is not None and value.strip():
            return value.strip()
    return ""


def _number(row: dict[str, str], name: str) -> float | None:
    value = _value(row, name).rstrip("%")
    if not value:
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    if name.endswith("_rate") and number > 1:
        return number / 100
    return number


def _published_date(row: dict[str, str]) -> date | None:
    value = _value(row, "published_at")
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _platform_rules(mature_rows: list[dict[str, str]]) -> dict[str, list[str]]:
    by_platform: dict[str, list[dict[str, str]]] = {}
    for row in mature_rows:
        platform = _value(row, "platform")
        if platform:
            by_platform.setdefault(platform, []).append(row)

    rules: dict[str, list[str]] = {}
    douyin_rows = by_platform.get("douyin", [])
    if douyin_rows:
        bounce_rates = [
            value
            for row in douyin_rows
            if (value := _number(row, "two_second_bounce_rate")) is not None
        ]
        rule = "0.0–0.8秒内呈现产品或酒标可见动作；2.0–5.0秒完成标题承诺。"
        if bounce_rates and median(bounce_rates) >= 0.4:
            rule += "近期成熟数据前段跳出偏高，本次禁止纯文字或静态片头。"
        rules["douyin"] = [rule]
    if by_platform.get("xiaohongshu"):
        rules["xiaohongshu"] = [
            "封面只承担一个好奇钩子；第2页必须给出具体产品判断，且不得重复封面标题。"
        ]
    if by_platform.get("weixin-channels"):
        rules["weixin-channels"] = [
            "首秒先给产品主体或酒标动作，再给日期、桶型或风味解释；不要先铺陈背景。"
        ]
    return rules


def analyze_performance(
    log_path: Path,
    *,
    candidate_date: str,
    theme_family: str,
) -> dict:
    candidate_day = date.fromisoformat(candidate_date)
    with Path(log_path).open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    mature_rows: list[dict[str, str]] = []
    observation_rows = 0
    for row in rows:
        hours = _number(row, "hours_since_publish")
        if hours is not None and hours >= MATURITY_HOURS:
            mature_rows.append(row)
        else:
            observation_rows += 1

    recent_theme_rows: list[dict[str, str]] = []
    for row in mature_rows:
        row_date = _published_date(row)
        if row_date is None or _value(row, "theme_family") != theme_family:
            continue
        days = (candidate_day - row_date).days
        if 0 <= days <= THEME_COOLDOWN_DAYS:
            recent_theme_rows.append(row)
    recent_theme_rows.sort(key=lambda row: _published_date(row) or candidate_day)
    cooldown_active = len(recent_theme_rows) >= 2

    return {
        "schema_version": 1,
        "candidate_date": candidate_date,
        "theme_family": theme_family,
        "maturity_hours": int(MATURITY_HOURS),
        "mature_rows": len(mature_rows),
        "observation_rows": observation_rows,
        "baseline_status": (
            "established"
            if len(mature_rows) >= ESTABLISHED_SAMPLE_SIZE
            else "hypothesis" if mature_rows else "not-analyzed"
        ),
        "theme_cooldown": {
            "active": cooldown_active,
            "window_days": THEME_COOLDOWN_DAYS,
            "recent_content_ids": [
                _value(row, "content_id") for row in recent_theme_rows
            ],
            "message": (
                "近期成熟内容已两次使用该主题；默认更换主主题，如继续使用必须填写campaign_override并改变用户问题、首屏形式和主事实中的至少两项。"
                if cooldown_active
                else "未触发主题冷却。"
            ),
        },
        "platform_prompt_rules": _platform_rules(mature_rows),
        "required_planning_fields": [
            "experiment.variable",
            "experiment.hypothesis",
            "experiment.success_metric",
            "experiment.baseline",
            "campaign_override",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze mature wxyj platform data for the next content run."
    )
    parser.add_argument("log", type=Path)
    parser.add_argument("--date", required=True, dest="candidate_date")
    parser.add_argument("--theme-family", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    brief = analyze_performance(
        args.log,
        candidate_date=args.candidate_date,
        theme_family=args.theme_family,
    )
    output = json.dumps(brief, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
