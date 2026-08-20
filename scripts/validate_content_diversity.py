from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path


REQUIRED_FIELDS = (
    "content_id",
    "date",
    "status",
    "theme_family",
    "primary_fact_ids",
    "hero_view_id",
    "view_ids",
    "typography_mode",
    "hook_pattern",
    "cta_type",
)
ALLOWED_STATUSES = {"working", "publish-candidate", "published", "archived"}
EXPERIMENT_FIELDS = (
    "variable",
    "hypothesis",
    "success_metric",
    "baseline",
    "result",
)
NARRATIVE_FIELDS = (
    "audience_question",
    "emotion_axis",
    "hero_visual_motif",
    "product_form",
    "interaction_type",
)


def _load_candidate(path: Path, errors: list[str]) -> dict | None:
    if not path.is_file():
        errors.append(f"创意记录不存在: {path}")
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"创意记录不是有效JSON: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append("创意记录顶层必须是对象")
        return None
    return value


def validate_record(
    record: dict,
    *,
    require_complete: bool = True,
    require_experiment: bool = False,
) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"创意记录缺少字段: {field}")
    if errors:
        return errors
    if record["status"] not in ALLOWED_STATUSES:
        errors.append("创意记录status不合法")
    try:
        date.fromisoformat(str(record["date"]))
    except ValueError:
        errors.append("创意记录date必须是有效YYYY-MM-DD")
    for field in ("primary_fact_ids", "view_ids"):
        value = record[field]
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item.strip() for item in value
        ):
            errors.append(f"创意记录{field}必须是非空字符串数组")
    if require_complete:
        for field in (
            "theme_family",
            "hero_view_id",
            "typography_mode",
            "hook_pattern",
            "cta_type",
        ):
            if not isinstance(record[field], str) or not record[field].strip():
                errors.append(f"发布候选缺少创意字段: {field}")
        if not record["primary_fact_ids"]:
            errors.append("发布候选至少需要一个primary_fact_id")
        if not record["view_ids"]:
            errors.append("发布候选至少需要一个view_id")
        experiment = record.get("experiment")
        if require_experiment and experiment is None:
            errors.append("发布候选缺少experiment")
        if experiment is not None:
            if not isinstance(experiment, dict):
                errors.append("创意记录experiment必须是对象")
            else:
                for field in EXPERIMENT_FIELDS:
                    if field not in experiment:
                        errors.append(f"创意记录experiment缺少字段: {field}")
                for field in ("variable", "hypothesis", "success_metric"):
                    if not isinstance(experiment.get(field), str) or not experiment[
                        field
                    ].strip():
                        errors.append(f"发布候选缺少实验字段: {field}")
                for field in ("baseline", "result"):
                    if not isinstance(experiment.get(field), str):
                        errors.append(f"创意记录experiment字段必须是字符串: {field}")
        if "campaign_override" in record and not isinstance(
            record["campaign_override"], str
        ):
            errors.append("创意记录campaign_override必须是字符串")
        if record.get("schema_version", 1) >= 2:
            for field in NARRATIVE_FIELDS:
                if not isinstance(record.get(field), str) or not record[field].strip():
                    errors.append(f"发布候选缺少创意字段: {field}")
    return errors


def _split_list(value: str) -> tuple[str, ...]:
    return tuple(sorted(item.strip() for item in value.split(";") if item.strip()))


def _fingerprint(record: dict) -> tuple[str, tuple[str, ...], str, str]:
    return (
        str(record["theme_family"]).strip(),
        tuple(sorted(str(item).strip() for item in record["primary_fact_ids"])),
        str(record["hero_view_id"]).strip(),
        str(record["hook_pattern"]).strip(),
    )


def _row_fingerprint(row: dict[str, str]) -> tuple[str, tuple[str, ...], str, str]:
    return (
        row.get("theme_family", "").strip(),
        _split_list(row.get("primary_fact_ids", "")),
        row.get("hero_view_id", "").strip(),
        row.get("hook_pattern", "").strip(),
    )


def validate_diversity(candidate_path: Path, ledger_path: Path) -> list[str]:
    candidate_path = Path(candidate_path)
    ledger_path = Path(ledger_path)
    errors: list[str] = []
    record = _load_candidate(candidate_path, errors)
    if record is None:
        return errors
    require_complete = record.get("status") in {"publish-candidate", "published"}
    errors.extend(validate_record(record, require_complete=require_complete))
    if errors or not require_complete:
        return errors
    if not ledger_path.is_file():
        errors.append(f"创意台账不存在: {ledger_path}")
        return errors

    with ledger_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    candidate_date = date.fromisoformat(str(record["date"]))
    candidate_fingerprint = _fingerprint(record)
    recent_rows: list[tuple[int, dict[str, str]]] = []
    for row in rows:
        try:
            row_date = date.fromisoformat(row.get("date", ""))
        except ValueError:
            continue
        days = (candidate_date - row_date).days
        if 0 <= days <= 30:
            recent_rows.append((days, row))
            if _row_fingerprint(row) == candidate_fingerprint:
                errors.append(
                    "30天内创意指纹重复: "
                    + row.get("content_id", "unknown-content")
                )

    for days, row in recent_rows:
        if days <= 14 and (
            row.get("theme_family", "").strip()
            == str(record["theme_family"]).strip()
            and row.get("hero_view_id", "").strip()
            == str(record["hero_view_id"]).strip()
            and row.get("typography_mode", "").strip()
            == str(record["typography_mode"]).strip()
        ):
            errors.append(
                "14天内主题、首图机位与版式路线重复: "
                + row.get("content_id", "unknown-content")
            )
            break

    if record.get("schema_version", 1) >= 2:
        candidate_narrative = tuple(
            str(record[field]).strip() for field in NARRATIVE_FIELDS[:-1]
        )
        for days, row in recent_rows:
            if days > 14 or not all(row.get(field, "").strip() for field in NARRATIVE_FIELDS[:-1]):
                continue
            row_narrative = tuple(row.get(field, "").strip() for field in NARRATIVE_FIELDS[:-1])
            if row_narrative == candidate_narrative:
                errors.append(
                    "14天内受众问题、情绪、首屏母题与产品形态重复: "
                    + row.get("content_id", "unknown-content")
                )
                break

    last_two_modes = [
        row.get("typography_mode", "").strip()
        for _, row in sorted(recent_rows, key=lambda item: item[0])[:2]
    ]
    if len(last_two_modes) == 2 and all(
        mode == str(record["typography_mode"]).strip() for mode in last_two_modes
    ):
        errors.append("同一typography_mode不得连续使用三次")

    return list(dict.fromkeys(errors))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a wxyj creative record against recent content history."
        )
    )
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()
    errors = validate_diversity(args.candidate, args.ledger)
    if errors:
        for error in errors:
            print(f"- {error}")
        return 1
    print("内容多样性验证通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
