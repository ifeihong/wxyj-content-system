from __future__ import annotations

import argparse
import importlib.util
import json
import hashlib
import subprocess
from pathlib import Path

try:
    from scripts.media_contract import read_png_dimensions
except ModuleNotFoundError:
    from media_contract import read_png_dimensions


ALLOWED_RELEASE_STATUSES = {"working", "publish", "archived"}
ALLOWED_ASSET_STATUSES = {"working", "rejected", "publish"}
REQUIRED_GATES = (
    "facts",
    "evidence",
    "product_geometry",
    "typography",
    "public_copy",
    "media",
    "audio",
    "deliverables",
)


def _load_json(path: Path, label: str, errors: list[str]) -> dict | None:
    if not path.exists():
        errors.append(f"缺少{label}: {path.name}")
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label}不是有效JSON: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label}顶层必须是对象")
        return None
    return value


def _png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        return read_png_dimensions(path)
    except (OSError, ValueError):
        return None


def _video_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "json",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        stream = json.loads(result.stdout)["streams"][0]
        return int(stream["width"]), int(stream["height"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _dimensions(path: Path) -> tuple[int, int] | None:
    if path.suffix.lower() == ".png":
        return _png_dimensions(path)
    if path.suffix.lower() in {".mp4", ".mov"}:
        return _video_dimensions(path)
    return None


def _validate_motion_plan(run_dir: Path, errors: list[str], publish=False) -> None:
    motion_path = run_dir / "video-master" / "motion-plan.json"
    motion = _load_json(motion_path, "视频运动计划", errors)
    if motion is None:
        return
    if motion.get("mode") == "unset":
        if publish:
            errors.append("发布视频的motion-plan不能为unset")
        return
    if motion.get("version") == 2:
        script = Path(__file__).with_name("validate_video_motion_plan.py")
        spec = importlib.util.spec_from_file_location(
            "wxyj_validate_video_motion_plan", script
        )
        if spec is None or spec.loader is None:
            errors.append("无法加载视频运动计划校验脚本")
            return
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        production_path = run_dir / "video-master/production-plan.json"
        expected = None
        if publish and production_path.exists():
            production = _load_json(production_path, "生产计划", errors)
            if production and isinstance(production.get("shots"), list):
                expected = production["shots"]
        errors.extend(module.validate(motion, expected_shots=expected))
        return
    if motion.get("mode") != "V4":
        return
    shots = motion.get("shots")
    if not isinstance(shots, list) or not shots:
        errors.append("V4视频运动计划必须至少包含一个镜头")
        return
    for index, shot in enumerate(shots, start=1):
        shot_id = shot.get("shot_id", f"S{index:02d}") if isinstance(shot, dict) else f"S{index:02d}"
        if not isinstance(shot, dict):
            errors.append(f"{shot_id}镜头必须是对象")
            continue
        asset_paths = shot.get("asset_paths")
        if not isinstance(asset_paths, list) or len(asset_paths) != 1:
            errors.append(f"{shot_id}每镜只允许一个静帧素材")
        if shot.get("continuous_motion") is not True:
            errors.append(f"{shot_id}必须是连续运动")
        if shot.get("direction") not in {"left-to-right", "right-to-left", "push-in", "pull-out", "locked"}:
            errors.append(f"{shot_id}缺少受控运动方向")
        start_x = shot.get("start_x")
        end_x = shot.get("end_x")
        if shot.get("direction") in {"left-to-right", "right-to-left"} and (
            not isinstance(start_x, (int, float))
            or not isinstance(end_x, (int, float))
            or start_x == end_x
        ):
            errors.append(f"{shot_id}横向运动必须填写不同的start_x与end_x")
        if not str(shot.get("transition_out", "")).strip():
            errors.append(f"{shot_id}缺少匹配的转场")


def validate_release(run_dir: Path) -> list[str]:
    run_dir = Path(run_dir)
    errors: list[str] = []
    release = _load_json(run_dir / "release-manifest.json", "发布清单", errors)
    if release is None:
        return errors

    if release.get("run_id") != run_dir.name:
        errors.append("发布清单run_id与运行目录不一致")
    release_status = release.get("release_status")
    if not isinstance(release_status, str) or release_status not in ALLOWED_RELEASE_STATUSES:
        errors.append("发布清单release_status不合法")
    schema = release.get("schema_version")
    if type(schema) is not int or schema not in range(1, 6):
        errors.append("发布清单schema_version必须是支持的整数版本1–5")

    gates = release.get("quality_gates")
    if not isinstance(gates, dict):
        errors.append("发布清单缺少quality_gates")
        gates = {}
    required_gates = list(REQUIRED_GATES)
    if isinstance(release.get("schema_version"), int) and release.get("schema_version") >= 2:
        required_gates.append("diversity")
    if isinstance(release.get("schema_version"), int) and release.get("schema_version") >= 4:
        required_gates.append("motion")
    for gate in required_gates:
        if gate not in gates:
            errors.append(f"发布清单缺少质量门槛: {gate}")
        if release_status == "publish" and gates.get(gate) not in {"pass", "not-applicable"}:
            errors.append(f"发布状态为publish时{gate}必须为pass")

    assets = release.get("assets")
    if not isinstance(assets, list):
        errors.append("发布清单assets必须是数组")
        assets = []
    if release_status == "publish" and not any(isinstance(a, dict) and a.get("status") == "publish" for a in assets):
        errors.append("发布状态为publish时必须登记至少一个发布资产")

    for index, asset in enumerate(assets, start=1):
        if not isinstance(asset, dict):
            errors.append(f"发布资产{index}必须是对象")
            continue
        if not isinstance(asset.get("status"), str) or asset.get("status") not in ALLOWED_ASSET_STATUSES:
            errors.append(f"发布资产{index}状态不合法")
            continue
        if asset.get("status") != "publish":
            continue
        relative = asset.get("path")
        if not isinstance(relative, str) or not relative.strip():
            errors.append(f"发布资产{index}缺少path")
            continue
        try:
            path = (run_dir / relative).resolve()
        except (OSError, ValueError):
            errors.append(f"发布资产{index}路径无效")
            continue
        if not path.is_relative_to(run_dir.resolve()):
            errors.append(f"发布资产{index}路径越界")
            continue
        if not path.is_file():
            errors.append(f"发布资产不存在: {relative}")
            continue
        expected_ratio = asset.get("native_ratio")
        dimensions = _dimensions(path)
        if expected_ratio not in ("1:1", "3:4", "9:16", "long"):
            errors.append(f"发布资产缺少有效native_ratio: {relative}")
        elif expected_ratio == "long":
            expected_size = asset.get("pixel_size")
            if (not isinstance(expected_size, list) or len(expected_size) != 2
                    or not all(type(n) is int and n > 0 for n in expected_size)
                    or dimensions != tuple(expected_size) or expected_size[1] <= expected_size[0]):
                errors.append(f"长图必须登记与实际一致的竖向pixel_size: {relative}")
        else:
            if dimensions is None:
                errors.append(f"无法读取发布资产画幅: {relative}")
            else:
                width, height = dimensions
                left, right = {
                    "1:1": (1, 1),
                    "3:4": (3, 4),
                    "9:16": (9, 16),
                }[expected_ratio]
                if width * right != height * left:
                    errors.append(f"发布资产不是原生{expected_ratio}: {relative}")

    if (run_dir / "video-master").exists():
        _validate_motion_plan(run_dir, errors, publish=release_status == "publish")
        if release_status == "publish":
            videos = [a for a in assets if isinstance(a, dict) and a.get("status") == "publish"
                      and isinstance(a.get("path"), str) and Path(a["path"]).suffix.lower() in (".mp4", ".mov")]
            if not videos:
                errors.append("视频发布必须登记实际导出的成片发布资产")
            if type(schema) is int and schema >= 5:
                _validate_video_acceptance(run_dir, release.get("video_acceptance"), videos, errors)
        if isinstance(release.get("schema_version"), int) and release["schema_version"] >= 5:
            script = Path(__file__).with_name("validate_video_production_plan.py")
            spec = importlib.util.spec_from_file_location("video_production_plan", script)
            if spec is None or spec.loader is None:
                errors.append("无法加载生产包校验")
            else:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                errors.extend(module.validate_package(run_dir, "ready" if release_status == "publish" else None))
    if not (run_dir / "product-visual-qa.md").exists():
        errors.append("缺少产品视觉人工验收卡")
    if not (run_dir / "deliverables.md").exists():
        errors.append("缺少最终交付索引")
    native_targets = release.get("native_targets")
    if isinstance(native_targets, dict) and "ecommerce" in native_targets:
        if not (run_dir / "ecommerce-asset-qa.md").exists():
            errors.append("缺少电商资产人工验收卡")
    return errors


def _validate_video_acceptance(root, record, videos, errors):
    """Bind human AV review and editable-project evidence to this exact render."""
    if not isinstance(record, dict) or record.get("status") != "pass":
        errors.append("缺少成片video_acceptance验收登记")
        return
    render = record.get("render_path")
    if render not in [asset["path"] for asset in videos]:
        errors.append("成片验收render_path不在发布视频中")
        return
    path = (root / render).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        errors.append("成片验收文件不存在或越界")
        return
    if record.get("render_sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
        errors.append("成片验收render_sha256已过期或缺失")
    for key in ("editable_project", "av_review"):
        item = record.get(key)
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not item["path"].strip():
            errors.append(f"成片验收缺少{key}文件证据")
            continue
        try:
            evidence = (root / item["path"]).resolve()
            if (not evidence.is_relative_to(root.resolve()) or not evidence.is_file()
                    or item.get("sha256") != hashlib.sha256(evidence.read_bytes()).hexdigest()):
                errors.append(f"成片验收{key}文件或hash无效")
        except (OSError, ValueError):
            errors.append(f"成片验收{key}路径无效")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate release readiness for a wxyj content run.")
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    errors = validate_release(args.run_dir)
    if errors:
        for error in errors:
            print(f"- {error}")
        return 1
    release = json.loads((args.run_dir / "release-manifest.json").read_text(encoding="utf-8"))
    if release.get("release_status") == "publish":
        print("发布登记预检通过；实际图像与视听验收仍以人工证据为准")
    else:
        print("草稿结构检查通过；未证明素材齐全、产品准确或成片可发布")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
