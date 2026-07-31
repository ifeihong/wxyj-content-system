from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path


SHOT_ID_PATTERN = re.compile(r"^S\d{2}$")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RUN_PATTERN = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})-"
    r"(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$"
)
ALLOWED_INPUT_MODES = {
    "text-to-video",
    "first-frame",
    "first-last-frame",
    "reference-guided",
}
ALLOWED_REFERENCE_ROLES = {
    "first_frame",
    "last_frame",
    "geometry_master",
    "structure_master",
    "label_detail",
    "style_anchor",
    "motion_reference",
}
REQUIRED_FIELDS = (
    "shot_id",
    "slug",
    "title",
    "input_mode",
    "duration_seconds",
    "draft_resolution",
    "final_resolution",
    "candidate_target",
    "max_attempts",
    "references",
    "prompt_positive",
    "prompt_negative",
)


def _write_once(path: Path, content: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_reference_path(source_root: Path, filename: object) -> Path:
    if not isinstance(filename, str) or not filename:
        raise ValueError("reference file must be a non-empty string")
    relative = Path(filename)
    if relative.is_absolute() or relative.name != filename:
        raise ValueError(f"reference file must be a basename: {filename}")
    source = (source_root / relative).resolve()
    root = source_root.resolve()
    if not source.is_relative_to(root):
        raise ValueError(f"reference escapes source root: {filename}")
    if not source.is_file():
        raise FileNotFoundError(f"reference file not found: {source}")
    return source


def validate_shot_spec(spec: dict[str, object]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in spec:
            errors.append(f"missing field: {field}")

    shot_id = spec.get("shot_id")
    if not isinstance(shot_id, str) or not SHOT_ID_PATTERN.fullmatch(shot_id):
        errors.append("shot_id must match SNN")

    slug = spec.get("slug")
    if not isinstance(slug, str) or not SLUG_PATTERN.fullmatch(slug):
        errors.append("slug must use lowercase kebab-case")

    input_mode = spec.get("input_mode")
    if input_mode not in ALLOWED_INPUT_MODES:
        errors.append(
            "input_mode must be one of: "
            + ", ".join(sorted(ALLOWED_INPUT_MODES))
        )

    if spec.get("aspect_ratio", "9:16") != "9:16":
        errors.append("aspect_ratio must be 9:16")

    duration = spec.get("duration_seconds")
    if not isinstance(duration, (int, float)) or not 4 <= duration <= 15:
        errors.append("duration_seconds must be between 4 and 15")

    candidate_target = spec.get("candidate_target")
    if not isinstance(candidate_target, int) or not 1 <= candidate_target <= 2:
        errors.append("candidate_target must be 1 or 2")

    max_attempts = spec.get("max_attempts")
    if not isinstance(max_attempts, int) or not 1 <= max_attempts <= 2:
        errors.append("max_attempts must be 1 or 2")

    references = spec.get("references")
    if not isinstance(references, list):
        errors.append("references must be a list")
        references = []

    orders: list[int] = []
    roles: list[str] = []
    for index, reference in enumerate(references, start=1):
        if not isinstance(reference, dict):
            errors.append(f"references[{index}] must be an object")
            continue
        order = reference.get("order")
        if not isinstance(order, int):
            errors.append(f"references.order missing at item {index}")
        else:
            orders.append(order)
        role = reference.get("role")
        if role not in ALLOWED_REFERENCE_ROLES:
            errors.append(f"references.role invalid at item {index}")
        else:
            roles.append(role)
        filename = reference.get("file")
        if (
            not isinstance(filename, str)
            or not filename
            or Path(filename).name != filename
        ):
            errors.append(f"references.file invalid at item {index}")

    if orders and (
        len(orders) != len(set(orders))
        or sorted(orders) != list(range(1, len(orders) + 1))
    ):
        errors.append("references.order must be unique and consecutive from 1")

    if input_mode == "first-frame" and "first_frame" not in roles:
        errors.append("first-frame mode requires a first_frame reference")
    if input_mode == "first-last-frame":
        if "first_frame" not in roles or "last_frame" not in roles:
            errors.append(
                "first-last-frame mode requires first_frame and last_frame"
            )
    if input_mode == "reference-guided" and {
        "first_frame",
        "last_frame",
    }.intersection(roles):
        errors.append(
            "reference-guided mode cannot mix first_frame or last_frame roles"
        )

    return errors


def _shot_yaml(spec: dict[str, object], output_name: str) -> str:
    lines = [
        f"shot_id: {spec['shot_id']}",
        f"slug: {spec['slug']}",
        f"title: {json.dumps(spec['title'], ensure_ascii=False)}",
        f"input_mode: {spec['input_mode']}",
        "aspect_ratio: 9:16",
        f"duration_seconds: {spec['duration_seconds']}",
        "duration_tolerance_seconds: 0.75",
        f"draft_resolution: {spec['draft_resolution']}",
        f"final_resolution: {spec['final_resolution']}",
        f"candidate_target: {spec['candidate_target']}",
        f"max_attempts: {spec['max_attempts']}",
        f"output_name: {output_name}",
        "references:",
    ]
    references = spec["references"]
    assert isinstance(references, list)
    for reference in sorted(references, key=lambda item: item["order"]):
        lines.extend(
            [
                f"  - order: {reference['order']}",
                f"    file: references/{reference['file']}",
                f"    role: {reference['role']}",
                "    required: "
                + ("true" if reference.get("required", True) else "false"),
            ]
        )
    return "\n".join(lines) + "\n"


def _task_card(spec: dict[str, object], output_name: str) -> str:
    references = spec["references"]
    assert isinstance(references, list)
    reference_lines = "\n".join(
        f"{reference['order']}. `references/{reference['file']}`"
        f" — {reference['role']}"
        for reference in sorted(references, key=lambda item: item["order"])
    )
    shot_path = (
        "video-master/external-generation/"
        f"{spec['shot_id']}-{spec['slug']}"
    )
    positive = str(spec["prompt_positive"]).strip()
    negative = str(spec["prompt_negative"]).strip()
    all_in_one = positive + "\n\n【负面约束】\n" + negative
    return f"""# {spec['shot_id']} {spec['title']}

## 生成设置

- 模式：`{spec['input_mode']}`
- 画幅：`9:16`
- 时长：`{spec['duration_seconds']}秒`
- 草稿分辨率：`{spec['draft_resolution']}`
- 成片分辨率：`{spec['final_resolution']}`
- 候选目标：{spec['candidate_target']}个
- 最大尝试次数：{spec['max_attempts']}

## 上传参考图

严格按以下顺序上传，只使用本目录内的文件：

{reference_lines}

## 参考图文件位置

- 当前镜头目录：`{shot_path}/`
- 参考图目录：`{shot_path}/references/`
- 独立提示词文件：`prompt-all-in-one.txt`、`prompt-positive.txt`、`prompt-negative.txt`

## 可直接复制：一体化提示词

```text
{all_in_one}
```

## 可直接复制：正向提示词

```text
{positive}
```

## 可直接复制：负向提示词

```text
{negative}
```

## 操作

1. 使用平台中与“模式”对应的通用 Seedance 生成方式。
2. 可直接复制本任务卡中的完整提示词，也可复制同目录的独立提示词文件。
3. 首次只生成一个候选；同一问题最多尝试两次。
4. 下载原始视频，不录屏、不二次压缩。
5. 文件命名为 `{output_name}`，放入 `video-master/incoming/`。
"""


def _start_readme() -> str:
    return """# 外部 Seedance 生成开始前必读

本任务包平台无关，适用于支持相应 Seedance 输入模式的第三方平台。

1. 从 S01 开始，先生成并回传一个镜头。
2. 打开镜头目录的 `任务卡.md`，按顺序上传 `references/` 中的文件。
3. 复制对应提示词，保持任务卡规定的9:16、时长和模式。
4. 下载原始视频并按任务卡命名，放入 `video-master/incoming/`。
5. 未通过验收前不要批量生成后续镜头，避免浪费积分。
"""


def create_handoff(
    run_dir: Path,
    shot_specs: list[dict[str, object]],
    source_root: Path,
) -> Path:
    run_dir = Path(run_dir)
    source_root = Path(source_root)
    handoff = run_dir / "video-master" / "external-generation"
    handoff.mkdir(parents=True, exist_ok=True)
    for directory in ("incoming", "accepted"):
        (run_dir / "video-master" / directory).mkdir(
            parents=True,
            exist_ok=True,
        )

    all_errors: list[str] = []
    seen_shots: set[str] = set()
    for spec in shot_specs:
        errors = validate_shot_spec(spec)
        shot_id = str(spec.get("shot_id", "<missing>"))
        if shot_id in seen_shots:
            errors.append("shot_id must be unique")
        seen_shots.add(shot_id)
        all_errors.extend(f"{shot_id}: {error}" for error in errors)
    if all_errors:
        raise ValueError("invalid shot specs:\n" + "\n".join(all_errors))

    run_match = RUN_PATTERN.fullmatch(run_dir.name)
    date_token = (
        run_match.group("date").replace("-", "")
        if run_match
        else "yyyymmdd"
    )
    topic_slug = run_match.group("slug") if run_match else "topic"

    _write_once(handoff / "00-开始前必读.md", _start_readme())
    _write_once(
        handoff / "00-镜头状态表.csv",
        "shot_id,title,status,attempts,returned_file,qa_result\n"
        + "".join(
            f"{spec['shot_id']},{spec['title']},ready,0,,\n"
            for spec in shot_specs
        ),
    )
    _write_once(
        handoff / "handoff-manifest.yaml",
        "version: 1\n"
        "workflow: external-seedance\n"
        "platform_specific: false\n"
        "aspect_ratio: 9:16\n"
        f"shot_count: {len(shot_specs)}\n",
    )

    for spec in shot_specs:
        shot_id = str(spec["shot_id"])
        slug = str(spec["slug"])
        shot_dir = handoff / f"{shot_id}-{slug}"
        references_dir = shot_dir / "references"
        references_dir.mkdir(parents=True, exist_ok=True)
        output_name = (
            f"{date_token}-wxyj-{topic_slug}-{shot_id.lower()}-"
            f"{slug}-seedance-v01.mp4"
        )

        _write_once(shot_dir / "任务卡.md", _task_card(spec, output_name))
        _write_once(shot_dir / "shot.yaml", _shot_yaml(spec, output_name))
        positive = str(spec["prompt_positive"]).strip() + "\n"
        negative = str(spec["prompt_negative"]).strip() + "\n"
        _write_once(shot_dir / "prompt-positive.txt", positive)
        _write_once(shot_dir / "prompt-negative.txt", negative)
        _write_once(
            shot_dir / "prompt-all-in-one.txt",
            positive.rstrip()
            + "\n\n【负面约束】\n"
            + negative,
        )

        references = spec["references"]
        assert isinstance(references, list)
        for reference in references:
            source = _safe_reference_path(source_root, reference["file"])
            destination = references_dir / source.name
            if destination.exists():
                if _sha256(source) != _sha256(destination):
                    raise ValueError(
                        f"reference conflict: {destination}"
                    )
                continue
            shutil.copy2(source, destination)

    return handoff


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create platform-neutral external Seedance shot packages."
    )
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.spec.read_text(encoding="utf-8"))
    shot_specs = payload["shots"] if isinstance(payload, dict) else payload
    if not isinstance(shot_specs, list):
        parser.error("spec JSON must be a list or contain a shots list")
    handoff = create_handoff(args.run_dir, shot_specs, args.source_root)
    print(handoff)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
