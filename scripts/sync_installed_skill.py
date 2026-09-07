"""Preview or back up and sync explicitly managed Skill files; never sync outputs."""
import argparse
import hashlib
import json
import shutil
import uuid
from pathlib import Path

ROOT_FILES = ("SKILL.md", "VERSION", "README.md", "CHANGELOG.md", "CITATION.cff",
              "llms.txt", "metadata/project.json", "agents/openai.yaml")
MANAGED_DIRS = ("references", "scripts", "assets/templates", "docs")
PRODUCT = "assets/products/mackillops-choice-aberlour-1996"
RETIRED = ("README.en.md",)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"managed path escapes root: {relative}")
    return path


def sync(source, target, backup_root, apply=False):
    source, target, backup_root = (Path(p).resolve() for p in (source, target, backup_root))
    if source.is_relative_to(target) or target.is_relative_to(source):
        raise ValueError("source and installed roots must not overlap")
    if backup_root.is_relative_to(target):
        raise ValueError("backup must be outside installed root")
    for name in ("SKILL.md", "VERSION"):
        if not (source / name).is_file():
            raise ValueError(f"missing source {name}")
    files = {name for name in ROOT_FILES if (source / name).is_file()}
    for folder in MANAGED_DIRS:
        files.update(path.relative_to(source).as_posix() for path in (source / folder).glob("*") if path.is_file())
    manifest = f"{PRODUCT}/asset-manifest.json"
    if (source / manifest).is_file():
        files.add(manifest)
    files.update(path.relative_to(source).as_posix() for path in (source / PRODUCT / "reference-images").glob("*.png"))
    changed, hashes = [], {}
    for name in sorted(files):
        src, dst = inside(source, name), inside(target, name)
        hashes[name] = digest(src)
        if not dst.is_file() or digest(dst) != hashes[name]:
            changed.append(name)
    retired = [name for name in RETIRED if not (source / name).exists() and inside(target, name).is_file()]
    report = {"applied": apply, "managed_count": len(files), "changed": changed, "retired": retired, "backup": None}
    if not apply:
        return report
    backup = backup_root / ("installed-" + uuid.uuid4().hex)
    backup.mkdir(parents=True)
    report["backup"] = str(backup)
    state = inside(target, ".managed-files.json")
    # Preserve every old managed byte before overwriting or retiring anything.
    for name in (*changed, *retired, ".managed-files.json"):
        dst = inside(target, name)
        if dst.is_file():
            saved = inside(backup, name)
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, saved)
    for name in changed:
        src, dst = inside(source, name), inside(target, name)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    for name in retired:
        # Move only the explicit retired document; unmanaged files are untouched.
        dst = inside(target, name)
        saved = inside(backup, "retired/" + name)
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(dst), str(saved))
    for name, expected in hashes.items():
        if digest(inside(target, name)) != expected:
            raise ValueError(f"post-sync hash mismatch: {name}; backup: {backup}")
    state.write_text(json.dumps({"version": (source / "VERSION").read_text().strip(),
                                 "files": hashes}, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--backup-root", required=True, type=Path)
    parser.add_argument("--apply", action="store_true", help="Without this flag, only preview changes.")
    args = parser.parse_args()
    print(json.dumps(sync(args.source, args.target, args.backup_root, args.apply), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
