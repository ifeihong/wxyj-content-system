from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import shutil
import uuid
import warnings
from pathlib import Path

try:
    from scripts.media_contract import INPUT_MODES, VIDEO_RATIOS, nonempty_text
except ModuleNotFoundError:
    from media_contract import INPUT_MODES, VIDEO_RATIOS, nonempty_text


SHOT_ID_PATTERN = re.compile(r"^S\d{2}$")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RUN_PATTERN = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})-"
    r"(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$"
)
ALLOWED_INPUT_MODES = INPUT_MODES
ALLOWED_REFERENCE_ROLES = {
    "first_frame",
    "last_frame",
    "geometry_master",
    "structure_master",
    "dimension_check",
    "label_detail",
    "style_anchor",
    "shot_keyframe",
    "motion_reference",
}
ALLOWED_REFERENCE_SOURCES = {"product", "agent"}
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
    if not isinstance(spec, dict):
        return ["shot spec must be an object"]
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
    if not isinstance(input_mode, str) or input_mode not in ALLOWED_INPUT_MODES:
        errors.append(
            "input_mode must be one of: "
            + ", ".join(sorted(ALLOWED_INPUT_MODES))
        )

    ratio = spec.get("aspect_ratio", "9:16")
    if not isinstance(ratio, str) or ratio not in VIDEO_RATIOS:
        errors.append("aspect_ratio must be 9:16 or 3:4")
    for field in ("title", "prompt_positive", "prompt_negative"):
        if not nonempty_text(spec.get(field)):
            errors.append(f"{field} must be non-empty text")

    duration = spec.get("duration_seconds")
    if type(duration) not in (int, float) or not 4 <= duration <= 15:
        errors.append("duration_seconds must be between 4 and 15")

    candidate_target = spec.get("candidate_target")
    if type(candidate_target) is not int or not 1 <= candidate_target <= 2:
        errors.append("candidate_target must be 1 or 2")

    max_attempts = spec.get("max_attempts")
    if type(max_attempts) is not int or not 1 <= max_attempts <= 2:
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
        if type(order) is not int:
            errors.append(f"references.order missing at item {index}")
        else:
            orders.append(order)
        role = reference.get("role")
        if not isinstance(role, str) or role not in ALLOWED_REFERENCE_ROLES:
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
        reference_source = reference.get("source", "product")
        if not isinstance(reference_source, str) or reference_source not in ALLOWED_REFERENCE_SOURCES:
            errors.append(f"references.source invalid at item {index}")

    if orders and (
        len(orders) != len(set(orders))
        or sorted(orders) != list(range(1, len(orders) + 1))
    ):
        errors.append("references.order must be unique and consecutive from 1")

    if input_mode == "first-frame" and not {
        "first_frame",
        "shot_keyframe",
    }.intersection(roles):
        errors.append("first-frame mode requires a first_frame or shot_keyframe reference")
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
    if input_mode == "reference-guided" and not roles:
        errors.append("reference-guided mode requires references")
    if input_mode == "text-to-video" and references:
        errors.append("text-to-video cannot contain image input references")
    if input_mode in ("first-frame", "first-last-frame"):
        if sum(role in ("first_frame", "shot_keyframe") for role in roles) != 1:
            errors.append("frame mode requires exactly one first-frame slot")
    if input_mode == "first-last-frame" and roles.count("last_frame") != 1:
        errors.append("first-last-frame requires exactly one last-frame slot")
    if input_mode == "first-frame" and "last_frame" in roles:
        errors.append("first-frame cannot contain last_frame")
    for field in ("draft_resolution", "final_resolution"):
        if spec.get(field) not in ("720p", "1080p"):
            errors.append(f"unsupported {field}")

    return errors


def _shot_yaml(spec: dict[str, object], output_name: str) -> str:
    lines = [
        f"shot_id: {spec['shot_id']}",
        f"slug: {spec['slug']}",
        f"title: {json.dumps(spec['title'], ensure_ascii=False)}",
        f"input_mode: {spec['input_mode']}",
        f"aspect_ratio: {spec.get('aspect_ratio', '9:16')}",
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
                f"    source: {reference.get('source', 'product')}",
                "    required: "
                + ("true" if reference.get("required", True) else "false"),
            ]
        )
    return "\n".join(lines) + "\n"


def _reference_manifest(references):
    return "\n".join(
        f"{reference['order']}. `references/{reference['file']}`"
        f" — {reference['role']}，来源：{reference.get('source', 'product')}"
        for reference in sorted(references, key=lambda item: item["order"])
    )


def _reference_details(references: list[dict[str, object]]) -> str:
    reference_detail_lines = []
    for reference in sorted(references, key=lambda item: item["order"]):
        description = str(reference.get("description", "")).strip()
        must_keep = str(reference.get("must_keep", "")).strip()
        do_not_inherit = str(reference.get("do_not_inherit", "")).strip()
        reference_detail_lines.append(
            "\n".join(
                line
                for line in (
                    f"### `references/{reference['file']}`（{reference['role']}，"
                    f"{reference.get('source', 'product')}）",
                    f"- 参考图具体职责：{description or '按提示词中的产品/结构职责使用，不作为泛风格图。'}",
                    f"- 必须保留：{must_keep or '参考图中与本镜头主体身份直接相关的比例、材质和结构。'}",
                    f"- 不得继承：{do_not_inherit or '参考图背景中的白底、边缘残影及与本镜头无关的小字细节。'}",
                )
                if line
            )
        )
    return "\n\n".join(reference_detail_lines)


def _prompt_bundle(
    spec: dict[str, object],
    reference_details: str,
    reference_manifest: str,
) -> tuple[str, str]:
    positive = str(spec["prompt_positive"]).strip()
    negative = _negative_prompt(spec)
    prompt_context = (
        "【本镜头生成参数】\n"
        f"- 生成模式：{spec['input_mode']}\n"
        f"- 画幅：原生{spec.get('aspect_ratio', '9:16')}\n"
        f"- 素材视频时长：{spec['duration_seconds']}秒\n"
        f"- 本镜头调用的参考图（按顺序上传）：\n{reference_manifest}\n\n"
        "【参考图职责与锁定细节】\n"
        + reference_details
        + "\n\n【生成提示词】\n"
    )
    return (
        prompt_context + positive,
        prompt_context + positive + "\n\n【负面约束】\n" + negative,
    )


def _negative_prompt(spec):
    return (str(spec["prompt_negative"]).strip()
            + "\n不得在产品上新增文字、数字、标志、浮雕或标签；保留参考图既有标识，不擦除、不改写、不重复。")


def _task_card(spec: dict[str, object], output_name: str) -> str:
    references = spec["references"]
    assert isinstance(references, list)
    reference_lines = _reference_manifest(references)
    reference_details = _reference_details(references)
    reference_manifest = reference_lines
    shot_path = (
        "video-master/external-generation/"
        f"{spec['shot_id']}-{spec['slug']}"
    )
    positive_with_context, all_in_one = _prompt_bundle(
        spec, reference_details, reference_manifest
    )
    negative = _negative_prompt(spec)
    return f"""# {spec['shot_id']} {spec['title']}

## 生成设置

- 模式：`{spec['input_mode']}`
- 画幅：`{spec.get('aspect_ratio', '9:16')}`
- 时长：`{spec['duration_seconds']}秒`
- 草稿分辨率：`{spec['draft_resolution']}`
- 成片分辨率：`{spec['final_resolution']}`
- 候选目标：{spec['candidate_target']}个
- 最大尝试次数：{spec['max_attempts']}

## 上传参考图

按以下编号核对文件。first-frame仅将first_frame或shot_keyframe上传首帧槽；first-last-frame分别使用首帧与尾帧槽。其余产品/尺寸参考仅在平台支持辅助参考时上传，否则用于校准，不混入首帧槽：

{reference_lines}

## 参考图职责与锁定细节

{reference_details}

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
{positive_with_context}
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


def _start_readme(first_shot: str) -> str:
    return f"""# 外部 Seedance 生成开始前必读

本任务包平台无关，适用于支持相应 Seedance 输入模式的第三方平台。

1. 从 {first_shot} 开始，先生成并回传一个镜头。
2. Agent负责先生成并验收参考起始图；用户不需要另行生图。状态pending-qa表示仍待验收，不应消耗视频积分。
3. 打开镜头目录的 `任务卡.md`，按顺序上传 `references/` 中的文件；`shot_keyframe` 优先作为首帧或主参考，几何/结构/尺寸参考负责产品一致性。
4. 复制对应提示词，保持任务卡规定的画幅、时长和模式；Seedance只生成产品、环境、光线和自然镜头运动。保留原产品文字，不添加新文字、标志或图形。
5. 下载原始视频并按任务卡命名，放入 `video-master/incoming/`。
6. 未通过 {first_shot} 的产品与风格验收前不要批量生成后续镜头，避免浪费积分。
"""


def create_handoff(
    run_dir: Path,
    shot_specs: list[dict[str, object]],
    source_root: Path,
) -> Path:
    run_dir = Path(run_dir)
    source_root = Path(source_root)
    handoff = run_dir / "video-master" / "external-generation"
    if not isinstance(shot_specs, list) or not shot_specs:
        raise ValueError("shot specs must be a non-empty list")
    all_errors: list[str] = []
    seen_shots: set[str] = set()
    for spec in shot_specs:
        errors = validate_shot_spec(spec)
        shot_id = str(spec.get("shot_id", "<missing>")) if isinstance(spec, dict) else "<invalid>"
        if shot_id in seen_shots:
            errors.append("shot_id must be unique")
        seen_shots.add(shot_id)
        all_errors.extend(f"{shot_id}: {error}" for error in errors)
    if all_errors:
        raise ValueError("invalid shot specs:\n" + "\n".join(all_errors))

    ratios = {spec.get("aspect_ratio", "9:16") for spec in shot_specs}
    if len(ratios) != 1:
        raise ValueError("all shots must share one canvas")
    plan_path = run_dir / "video-master/production-plan.json"
    if plan_path.exists():
        plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
        if plan.get("canvas", {}).get("aspect_ratio") not in ratios:
            raise ValueError("handoff canvas conflicts with production-plan")

    run_match = RUN_PATTERN.fullmatch(run_dir.name)
    date_token = (
        run_match.group("date").replace("-", "")
        if run_match
        else "yyyymmdd"
    )
    topic_slug = run_match.group("slug") if run_match else "topic"

    # Prepare every byte and resolve all sources before changing any existing file.
    payload = {}
    def document(relative, content):
        payload[relative] = content.encode("utf-8")
    document("00-开始前必读.md", _start_readme(str(shot_specs[0]["shot_id"])))
    status_csv = io.StringIO(newline="")
    writer = csv.writer(status_csv, lineterminator="\n")
    writer.writerow(("shot_id", "title", "status", "attempts", "returned_file", "qa_result"))
    writer.writerows((spec["shot_id"], spec["title"], "pending-qa", 0, "", "") for spec in shot_specs)
    document("00-镜头状态表.csv", status_csv.getvalue())
    document("handoff-manifest.yaml",
        "version: 1\n"
        "workflow: external-seedance\n"
        "platform_specific: false\n"
        f"aspect_ratio: {next(iter(ratios))}\n"
        f"shot_count: {len(shot_specs)}\n",
    )

    for spec in shot_specs:
        shot_id = str(spec["shot_id"])
        slug = str(spec["slug"])
        relative_dir = f"{shot_id}-{slug}"
        output_name = (
            f"{date_token}-wxyj-{topic_slug}-{shot_id.lower()}-"
            f"{slug}-seedance-v01.mp4"
        )

        document(f"{relative_dir}/任务卡.md", _task_card(spec, output_name))
        document(f"{relative_dir}/shot.yaml", _shot_yaml(spec, output_name))
        references = spec["references"]
        assert isinstance(references, list)
        reference_details = _reference_details(references)
        reference_manifest = _reference_manifest(references)
        positive_with_context, all_in_one = _prompt_bundle(
            spec, reference_details, reference_manifest
        )
        negative = _negative_prompt(spec) + "\n"
        document(
            f"{relative_dir}/prompt-positive.txt",
            positive_with_context + "\n",
        )
        document(f"{relative_dir}/prompt-negative.txt", negative)
        document(
            f"{relative_dir}/prompt-all-in-one.txt",
            all_in_one + "\n",
        )

        for reference in references:
            reference_source = reference.get("source", "product")
            reference_root = (
                run_dir / "video-master" / "agent-images" / "seedance-references"
                if reference_source == "agent"
                else source_root
            )
            source = _safe_reference_path(reference_root, reference["file"])
            relative = f"{relative_dir}/references/{source.name}"
            content = source.read_bytes()
            if relative in payload and payload[relative] != content:
                raise ValueError(f"reference conflict: {relative}")
            payload[relative] = content

    state_path = handoff / ".generated-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    digest = hashlib.sha256(json.dumps(shot_specs, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    previous = state.get("files", {})
    if previous and set(previous) != set(payload):
        raise ValueError("shot/reference set changed: create a new versioned run; existing package preserved")
    same_spec = state.get("spec_sha256") == digest
    changes = {}
    for relative, content in payload.items():
        target = (handoff / relative).resolve()
        if not target.is_relative_to(handoff.resolve()):
            raise ValueError(f"path outside handoff: {relative}")
        if target.exists():
            old = target.read_bytes()
            if old == content:
                continue
            if "/references/" in relative:
                raise ValueError(f"reference conflict: {target}; use a versioned reference/run")
            current_hash = hashlib.sha256(old).hexdigest()
            if current_hash != previous.get(relative):
                if same_spec:
                    warnings.warn(f"manual file preserved, not revalidated: {relative}")
                    continue
                raise ValueError(f"manual file conflict: {target}; merge edits or use a new run")
        changes[relative] = content
    backup = handoff / ".history" / uuid.uuid4().hex
    for relative, content in changes.items():
        target = handoff / relative
        if target.exists():
            saved = backup / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    handoff.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"spec_sha256": digest, "files": {
        key: hashlib.sha256(value).hexdigest() for key, value in payload.items()
    }}, ensure_ascii=False, indent=2), encoding="utf-8")
    for directory in ("incoming", "accepted"):
        (run_dir / "video-master" / directory).mkdir(parents=True, exist_ok=True)
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
