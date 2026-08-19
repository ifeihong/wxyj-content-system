from __future__ import annotations

import json
import hashlib
import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IDENTITY_PATH = PROJECT_ROOT / "metadata" / "project.json"
PRODUCT_ASSET_ROOT = (
    PROJECT_ROOT
    / "assets"
    / "products"
    / "mackillops-choice-aberlour-1996"
)
EXPECTED_PRODUCT_ASSETS = {
    "酒瓶-背面.png": "B105FAC8125A17031121CEB4DA62D26633BF0CEE4AE1BD432A0F85EAB7594D0B",
    "酒瓶-酒标.png": "7539AD71D76835D07F2406A284E66E248F03DE1A67B389F51C324E2E3234C7B7",
    "酒瓶-右侧45°.png": "EB2AB39813567434ED1B7E61C1AAA6AE3C753F0A427A2E662BD7DB86A369D197",
    "酒瓶-正面.png": "8BEEBB208F197F0A7A5E43059CC4312A223B1C7CA8E8E6B71CF8427E036DD76F",
    "酒瓶-左侧45°.png": "C0B87B9AA91B45A9B012E88428401026EB01134681E7C455B95B0C75F2725299",
    "木质礼盒-背面.png": "427163C22475DAC551280B90C3BFE81E2F182A6145CFAB3EAED2E2F0CB36AA89",
    "木质礼盒-背面右侧45°.png": "5D4AD1214CEFC93B6FAF2C3D727D2B82D3D11359460F195021DA56A6D541DA6B",
    "木质礼盒-背面左侧45°.png": "1426FC484789BA87D606D3CC4671047B3AE753E8D06A020D862A2C384BD2E156",
    "木质礼盒-背面品鉴标签.png": "47906AB8A57F42B0AAE5BE5BE81F4C205EEEE9F47E4FF647B28D46A9C018F63C",
    "木质礼盒-内置酒瓶.png": "9136C98797B435DA56719C7ABDDBD2D1211E0E51DA35CFA9B1FF3F89EBA4CF03",
    "木质礼盒-右侧45°.png": "39CD7F8A62F02781A0123C8C1A0EC5BD2C0F2EFC430676B1EFE048FCF72B0904",
    "木质礼盒-正面.png": "CA8041790526F5E0AC06402DF75486AA3A8DDE623ACC66555A58DF03238996B3",
    "木质礼盒-左侧45°.png": "139CC0093987349301619367ADB2615353FE345C85C32A2A126C7A4D0B9B8DAF",
    "外包装-右侧45°.png": "AE3D6F63377475E1A0DEDBD1F66C91E80C74959C4539B8CBE74085A651E15E96",
    "外包装-右侧45°俯视.png": "A6BCF0435E7E0015F6FCE84FC8C2DF6562D196354F8480CCC8961EFE87DBE6BB",
    "外包装-右侧面.png": "189B07ED57ECF59A795C24218CB823E45F2E1FA25A064A15254B7694A1735E38",
    "外包装-正面背面.png": "378164C6CE1BCB81FE3AE211A5BA225C9C42F796DADD60D384BFAB22275A5F97",
    "外包装-左侧45°.png": "6129E0C3AFDDF366889E6731D4999F0311C0C1FD36DC30032E73C7AD1E0B091A",
    "外包装-左侧45°俯视.png": "37CAD3462645248A28AF1979DD1E1AC2324B624002BBA2A316A361C439CB9FBA",
    "外包装-左侧面.png": "83C5A59D234E9742503E69964AFE665024513465D3A013E08F7F9414B650C540",
}
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
    "scripts/validate_product_assets.py",
    "scripts/validate_xhs_image.py",
    "scripts/validate_release_preflight.py",
    "scripts/validate_content_diversity.py",
    "scripts/analyze_performance.py",
    "assets/templates/release-manifest.json",
    "assets/templates/product-visual-qa.md",
    "assets/templates/creative-record.json",
    "assets/templates/creative-ledger.csv",
    "assets/templates/performance-log.csv",
    "references/editorial-art-direction.md",
    "references/content-diversity-system.md",
    "references/performance-adaptive-system.md",
]


class RepositoryContractTests(unittest.TestCase):
    def test_brand_specific_positioning_is_explicit(self):
        for relative in ("SKILL.md", "README.md"):
            text = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("威熏邑境品牌专属", text, relative)
            self.assertIn("马克瑞普之选", text, relative)
            for platform in ("小红书", "抖音", "视频号"):
                self.assertIn(platform, text, relative)

    def test_product_knowledge_system_is_bundled(self):
        facts = (PROJECT_ROOT / "references" / "product-facts.md").read_text(
            encoding="utf-8"
        )
        packaging = (
            PROJECT_ROOT / "references" / "product-packaging-copy.md"
        ).read_text(encoding="utf-8")
        for fact in (
            "261311",
            "51%",
            "PX Sherry Hogshead",
            "700毫升/瓶",
            "184 瓶",
            "1996-02-14",
            "2026-02-14",
            "7888 元",
            "180 of 184",
        ):
            self.assertIn(fact, facts)
        for knowledge in (
            "黑樱桃果脯",
            "圣诞水果布丁",
            "黑森林蛋糕",
            "Non Dormit Qui Custodit",
            "守护者永不沉睡",
            "洛恩·麦基洛普",
        ):
            self.assertIn(knowledge, facts + packaging)

    def test_product_identity_keeps_brand_distillery_and_age_distinct(self):
        facts = (PROJECT_ROOT / "references" / "product-facts.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("| 商品名称 | “马克瑞普之选”单一单桶系列威士忌 - 亚伯乐1996 |", facts)
        self.assertIn("| 品牌 | Mackillop's Choice（马克瑞普之选） |", facts)
        self.assertIn("| 酒厂 | ABERLOUR（亚伯乐） |", facts)
        self.assertIn("| 酒龄 | 30年 |", facts)
        self.assertIn("不得把“亚伯乐”写成品牌", facts)
        self.assertIn("不得把“30年”写成品牌或酒厂", facts)

    def test_product_reference_assets_are_complete_and_unchanged(self):
        image_root = PRODUCT_ASSET_ROOT / "reference-images"
        actual = {path.name for path in image_root.glob("*.png")}
        self.assertEqual(actual, set(EXPECTED_PRODUCT_ASSETS))

        manifest_path = PRODUCT_ASSET_ROOT / "asset-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["brand"], "威熏邑境")
        self.assertEqual(
            manifest["product_name"],
            "“马克瑞普之选”单一单桶系列威士忌 - 亚伯乐1996",
        )
        self.assertEqual(
            manifest["product_brand"], "Mackillop's Choice（马克瑞普之选）"
        )
        self.assertEqual(manifest["distillery"], "ABERLOUR（亚伯乐）")
        self.assertEqual(manifest["age_statement"], "30年")
        self.assertEqual(manifest["asset_count"], 20)
        self.assertEqual(manifest["license"], "All rights reserved")

        by_file = {entry["file"]: entry for entry in manifest["assets"]}
        self.assertEqual(set(by_file), set(EXPECTED_PRODUCT_ASSETS))
        for filename, expected_hash in EXPECTED_PRODUCT_ASSETS.items():
            path = image_root / filename
            actual_hash = hashlib.sha256(path.read_bytes()).hexdigest().upper()
            self.assertEqual(actual_hash, expected_hash, filename)
            self.assertEqual(by_file[filename]["sha256"], expected_hash)

    def test_product_images_are_excluded_from_apache_license(self):
        open_source = (PROJECT_ROOT / "OPEN_SOURCE.md").read_text(encoding="utf-8")
        self.assertIn(
            "assets/products/mackillops-choice-aberlour-1996/reference-images/",
            open_source,
        )
        self.assertIn("不适用 Apache-2.0", open_source)

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
        self.assertEqual(identity["version"], "2.7.3")
        self.assertEqual(
            identity["product_identity"]["brand"],
            "Mackillop's Choice（马克瑞普之选）",
        )
        self.assertEqual(
            identity["product_identity"]["distillery"], "ABERLOUR（亚伯乐）"
        )
        self.assertEqual(
            identity["product_identity"]["official_product_name"],
            "“马克瑞普之选”单一单桶系列威士忌 - 亚伯乐1996",
        )
        self.assertEqual(identity["product_identity"]["age_statement"], "30年")

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

    def test_performance_adaptive_prompt_contract_is_explicit(self):
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        reference = (
            PROJECT_ROOT / "references" / "performance-adaptive-system.md"
        ).read_text(encoding="utf-8")
        template = (
            PROJECT_ROOT / "assets" / "templates" / "performance-log.csv"
        ).read_text(encoding="utf-8")
        self.assertIn("performance-brief.json", skill)
        self.assertIn("已满 48 小时", reference)
        self.assertIn("campaign_override", reference)
        self.assertIn("发布后小时数", template)
        self.assertIn("实验变量", template)

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
        self.assertRegex(gitignore, r"(?m)^\.worktrees/$")
        self.assertRegex(gitignore, r"(?m)^dist/$")
        self.assertRegex(gitignore, r"(?m)^outputs/\*\*$")
        self.assertRegex(
            gitignore,
            r"(?m)^examples/content-runs/\*\*/video-master/incoming/\*\*$",
        )

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

    def test_xiaohongshu_angle_plan_is_measurable(self):
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        carousel = (
            PROJECT_ROOT / "references" / "xiaohongshu-carousel-system.md"
        ).read_text(encoding="utf-8")
        joined = skill + carousel
        for contract in (
            "机位分配表",
            "view_id",
            "相邻页面不得使用相同",
            "侧面可见宽度",
            "标签平面呈梯形透视",
        ):
            self.assertIn(contract, joined)

    def test_open_box_geometry_and_story_panel_are_hard_locked(self):
        visual_reference = (
            PROJECT_ROOT / "references" / "visual-asset-library.md"
        ).read_text(encoding="utf-8")
        for contract in (
            "175°–180°",
            "不得超过 180°",
            "左侧白色内皮",
            "RARE MASTER'S COLLECTION",
            "多段故事文字",
            "不得清空",
        ):
            self.assertIn(contract, visual_reference)

    def test_xiaohongshu_first_generation_requires_three_four_gate(self):
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        carousel = (
            PROJECT_ROOT / "references" / "xiaohongshu-carousel-system.md"
        ).read_text(encoding="utf-8")
        joined = skill + carousel
        for contract in (
            "首轮原生成文件",
            "validate_xhs_image.py",
            "不允许通过裁切",
            "宽:高 = 3:4",
        ):
            self.assertIn(contract, joined)

    def test_carousel_primary_fact_is_unique(self):
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        carousel = (
            PROJECT_ROOT / "references" / "xiaohongshu-carousel-system.md"
        ).read_text(encoding="utf-8")
        joined = skill + carousel
        for contract in (
            "primary_fact_id",
            "同一 `primary_fact_id` 只能出现一次",
            "桶号只能有一个主视觉事实页",
        ):
            self.assertIn(contract, joined)

    def test_bottle_geometry_master_has_priority_and_tolerance(self):
        visual_reference = (
            PROJECT_ROOT / "references" / "visual-asset-library.md"
        ).read_text(encoding="utf-8")
        for contract in (
            "geometry_master",
            "geometry_master > structure_master > label_detail > style_anchor",
            "0.33–0.35",
            "0.30–0.33",
            "34%–41%",
            "偏差不得超过 5%",
        ):
            self.assertIn(contract, visual_reference)

    def test_five_page_carousel_limits_complete_bottle_exposure(self):
        carousel = (
            PROJECT_ROOT / "references" / "xiaohongshu-carousel-system.md"
        ).read_text(encoding="utf-8")
        self.assertIn("完整酒瓶不超过 2 页", carousel)
        self.assertIn("酒标近景、礼盒、证据或风味静物", carousel)

    def test_generation_status_separates_rejected_from_publish(self):
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        run_system = (
            PROJECT_ROOT / "references" / "content-run-system.md"
        ).read_text(encoding="utf-8")
        joined = skill + run_system
        for contract in (
            "`working`",
            "`rejected`",
            "`publish`",
            "发布总览只能引用 `publish`",
        ):
            self.assertIn(contract, joined)

    def test_external_seedance_is_default_and_platform_neutral(self):
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        handoff = (
            PROJECT_ROOT / "references" / "external-seedance-handoff.md"
        ).read_text(encoding="utf-8")
        joined = skill + handoff
        for contract in (
            "外部 Seedance",
            "平台无关",
            "当次明确授权",
            "prompt-all-in-one.txt",
            "prompt-positive.txt",
            "prompt-negative.txt",
            "video-master/incoming",
            "max_attempts",
            "最终回复必须逐镜显示",
            "不得只提供目录",
            "完整一体化提示词",
        ):
            self.assertIn(contract, joined)
        self.assertNotIn("必须提供第三方平台名称", joined)

    def test_video_generation_requires_native_nine_sixteen(self):
        joined = (
            (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
            + (
                PROJECT_ROOT
                / "references"
                / "video-production-system.md"
            ).read_text(encoding="utf-8")
        )
        for contract in (
            "1080×1920",
            "原生9:16",
            "3:4图片不能作为全屏主画面",
            "禁止黑边",
        ):
            self.assertIn(contract, joined)

    def test_public_docs_explain_external_video_handoff(self):
        chinese_docs = "\n".join(
            (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for relative in (
                "README.md",
                "docs/content-contract.md",
                "docs/output-structure.md",
                "docs/naming-convention.md",
                "docs/getting-started.md",
                "llms.txt",
            )
        )
        for contract in (
            "video-master/external-generation",
            "video-master/incoming",
            "create_external_video_handoff.py",
            "validate_external_video_return.py",
            "平台无关",
            "原生9:16",
        ):
            self.assertIn(contract, chinese_docs)
        self.assertNotIn("ChatCut 是默认视频生成工具", chinese_docs)

        english = (PROJECT_ROOT / "README.en.md").read_text(
            encoding="utf-8"
        )
        for contract in (
            "video-master/external-generation",
            "video-master/incoming",
            "platform-neutral",
            "current-task authorization",
        ):
            self.assertIn(contract, english)

    def test_published_assets_omit_internal_labels_and_account_watermarks(self):
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        video = (
            PROJECT_ROOT / "references" / "video-production-system.md"
        ).read_text(encoding="utf-8")
        text_in_image = (
            PROJECT_ROOT / "references" / "text-in-image-system.md"
        ).read_text(encoding="utf-8")
        joined = skill + video + text_in_image
        for contract in (
            "成片画面与图文成图禁止出现账号名“威熏邑境”、缩写“WXYJ”",
            "禁止出现“下一条”“下期”等续集预告",
            "禁止把AIGC或事实核验说明写入成片、成图、标题、正文、评论或 CTA",
            "平台后台要求AI标签时，只使用平台原生开关",
        ):
            self.assertIn(contract, joined)
        self.assertNotIn("CTA、AIGC与事实披露", skill)

    def test_video_audio_defaults_to_chatcut_human_delivery(self):
        video = (
            PROJECT_ROOT / "references" / "video-production-system.md"
        ).read_text(encoding="utf-8")
        for contract in (
            "submit_voice",
            "submit_music",
            "不得使用 Edge TTS 作为默认发布配音",
            "自然口语台词",
            "真实时长",
        ):
            self.assertIn(contract, video)

    def test_video_product_framing_keeps_complete_subject_boundaries(self):
        video = (
            PROJECT_ROOT / "references" / "video-production-system.md"
        ).read_text(encoding="utf-8")
        for contract in (
            "瓶顶、瓶底和瓶身完整边界",
            "objectFit: contain",
            "源图顶部本身已截断",
            "1996年2月14日，入桶；2026年2月14日，罐瓶。",
        ):
            self.assertIn(contract, video)

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
