from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IDENTITY_PATH = PROJECT_ROOT / "metadata" / "project.json"
REQUIRED_DOCS = [
    ".gitattributes",
    "README.md",
    "README.en.md",
    "CHANGELOG.md",
    "VERSION",
    "LICENSE",
    "NOTICE",
    "OPEN_SOURCE.md",
    "CONTRIBUTING.md",
    "CITATION.cff",
    "llms.txt",
    "docs/getting-started.md",
    "docs/content-contract.md",
    "docs/output-structure.md",
    "docs/naming-convention.md",
    "docs/versioning.md",
    "docs/compliance.md",
    "SKILL.md",
    "agents/openai.yaml",
]


class RepositoryContractTests(unittest.TestCase):
    def test_single_skill_repository_is_flat(self):
        self.assertTrue((PROJECT_ROOT / "SKILL.md").is_file())
        self.assertTrue((PROJECT_ROOT / "agents" / "openai.yaml").is_file())
        self.assertFalse((PROJECT_ROOT / "skill").exists())

    def test_readme_does_not_expose_optimization_notes(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotRegex(readme, r"(?i)\bSEO\b|\bGEO\b")

    def test_machine_readable_identity_is_consistent(self):
        self.assertTrue(IDENTITY_PATH.exists(), f"missing {IDENTITY_PATH}")
        identity = json.loads(IDENTITY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(identity["display_name"], "威熏邑境自媒体内容生成系统")
        self.assertEqual(identity["skill_id"], "wxyj-content-system")
        self.assertEqual(identity["github_repository_id"], "wxyj-content-system")
        self.assertEqual(identity["version"], "2.1.1")

        version = (PROJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(identity["version"], version)

        for relative in ("README.md", "README.en.md", "CHANGELOG.md"):
            text = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(identity["skill_id"], text, relative)
            self.assertIn(identity["version"], text, relative)

    def test_required_public_documents_exist(self):
        missing = [
            relative
            for relative in REQUIRED_DOCS
            if not (PROJECT_ROOT / relative).exists()
        ]
        self.assertEqual(missing, [])

    def test_local_readme_links_resolve(self):
        readme = PROJECT_ROOT / "README.md"
        text = readme.read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
        missing = []
        for link in links:
            if link.startswith(("http://", "https://", "#")):
                continue
            target = (readme.parent / link.split("#", 1)[0]).resolve()
            if not target.exists():
                missing.append(link)
        self.assertEqual(missing, [])

    def test_all_local_markdown_links_resolve(self):
        missing = []
        for document in PROJECT_ROOT.rglob("*.md"):
            if any(
                part in {"dist", "outputs", ".test-work"}
                for part in document.parts
            ):
                continue
            text = document.read_text(encoding="utf-8-sig")
            links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
            for link in links:
                if link.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                target_text = link.split("#", 1)[0]
                if not target_text:
                    continue
                target = (document.parent / target_text).resolve()
                if not target.exists():
                    missing.append(f"{document.relative_to(PROJECT_ROOT)} -> {link}")
        self.assertEqual(missing, [])

    def test_installable_skill_routes_only_to_existing_files(self):
        skill_root = PROJECT_ROOT
        skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        referenced = set(re.findall(r"`((?:references|assets|examples)/[^`]+)`", skill_text))
        missing = [
            relative
            for relative in sorted(referenced)
            if not (skill_root / relative).exists()
        ]
        self.assertEqual(missing, [])
        openai_yaml = (skill_root / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("$wxyj-content-system", openai_yaml)

    def test_local_build_artifacts_are_ignored(self):
        gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertRegex(gitignore, r"(?m)^dist/$")
        self.assertRegex(gitignore, r"(?m)^outputs/\*\*$")

    def test_xiaohongshu_examples_respect_dynamic_page_contract(self):
        text_files = [
            *PROJECT_ROOT.glob("references/*.md"),
            *PROJECT_ROOT.glob("examples/strategy/*.md"),
            *PROJECT_ROOT.glob("examples/strategy/*.csv"),
        ]
        joined = "\n".join(
            path.read_text(encoding="utf-8-sig") for path in text_files
        )
        self.assertNotRegex(joined, r"同一轮\s*8\s*页内容")
        self.assertNotRegex(joined, r"小红书,9页")

    def test_visual_asset_root_is_configurable(self):
        visual_reference = (
            PROJECT_ROOT
            / "references"
            / "visual-asset-library.md"
        ).read_text(encoding="utf-8")
        content_brief = (
            PROJECT_ROOT
            / "assets"
            / "templates"
            / "content-brief.md"
        ).read_text(encoding="utf-8")
        self.assertIn("asset_root", visual_reference)
        self.assertIn("asset_root", content_brief)

    def test_long_reference_files_have_a_table_of_contents(self):
        references = PROJECT_ROOT / "references"
        missing = []
        for path in references.glob("*.md"):
            text = path.read_text(encoding="utf-8")
            if len(text.splitlines()) > 100 and "## 目录" not in text:
                missing.append(path.name)
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
