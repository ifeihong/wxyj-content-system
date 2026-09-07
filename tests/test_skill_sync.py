import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SkillSyncTests(unittest.TestCase):
    def test_dry_run_then_backup_managed_files_only(self):
        spec = importlib.util.spec_from_file_location("skill_sync", ROOT / "scripts/sync_installed_skill.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, target = root / "repo", root / "installed"
            source.mkdir()
            target.mkdir()
            for name in ("SKILL.md", "VERSION"):
                (source / name).write_text("new", encoding="utf-8")
                (target / name).write_text("old", encoding="utf-8")
            (target / "README.en.md").write_text("obsolete", encoding="utf-8")
            (target / "user-note.md").write_text("keep", encoding="utf-8")
            preview = module.sync(source, target, root / "backups")
            self.assertFalse(preview["applied"])
            self.assertEqual((target / "VERSION").read_text(), "old")
            report = module.sync(source, target, root / "backups", apply=True)
            self.assertEqual((target / "VERSION").read_text(), "new")
            self.assertFalse((target / "README.en.md").exists())
            self.assertEqual((Path(report["backup"]) / "README.en.md").read_text(), "obsolete")
            self.assertEqual((target / "user-note.md").read_text(), "keep")
            self.assertEqual(module.sync(source, target, root / "backups")["changed"], [])

    def test_rejects_overlapping_roots(self):
        spec = importlib.util.spec_from_file_location("skill_sync", ROOT / "scripts/sync_installed_skill.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.assertRaises(ValueError):
            module.sync(ROOT, ROOT / "nested", ROOT / ".test-work")
