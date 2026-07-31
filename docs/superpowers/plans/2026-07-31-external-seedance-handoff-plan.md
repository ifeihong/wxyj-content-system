# External Seedance Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `wxyj-content-system` so external, platform-neutral Seedance generation is the default video workflow, with per-shot handoff packages, controlled returns, validation, shared video masters, and no unapproved ChatCut generation spend.

**Architecture:** Add one shared `video-master/` to content runs that include Douyin or Weixin Channels, then generate external Seedance packages below `video-master/external-generation/`. Keep task-package creation, returned-video validation, content-run validation, and human-facing reference guidance as separate units. Preserve `xiaohongshu/` as a platform-native 3:4 subsystem and keep Douyin/Weixin publish copy separate from the shared video master.

**Tech Stack:** Python 3 standard library, `unittest`, Markdown, YAML-like text manifests without a new YAML dependency, FFprobe/FFmpeg subprocesses for returned-video diagnostics, existing repository validators.

## Global Constraints

- Do not bind the workflow to a named third-party Seedance platform or UI.
- Default to external Seedance generation; ChatCut paid generation requires explicit authorization in the current task.
- Generate every full-frame video asset, first frame, last frame, and cover as native exact 9:16.
- Give the user actual per-shot reference files in upload order; never make the user search the 17-image product library.
- Deliver combined, positive, and negative prompt files for every external Seedance shot.
- Default to one candidate and at most two attempts per shot.
- Preserve returned originals in `video-master/incoming/`; copy accepted versions to `video-master/accepted/`.
- Use one shared video master for Douyin and Weixin Channels; keep their publish copy separate.
- Preserve all existing product facts, the 17 bundled images, geometry locks, 3:4 Xiaohongshu rules, and non-destructive file behavior.
- Add no third-party Python packages.

---

### Task 1: Shared Video-Master Run Contract

**Files:**
- Modify: `tests/test_content_run.py`
- Modify: `scripts/create_content_run.py`
- Modify: `scripts/validate_content_run.py`

**Interfaces:**
- Produces: `needs_video_master(platforms: list[str]) -> bool`
- Produces: `create_run(...)` with a single shared `video-master/` whenever `douyin` or `weixin-channels` is requested.
- Produces: `validate_run(run_dir: Path) -> list[str]` validation of shared video-master files.

- [ ] **Step 1: Add failing shared-video-master tests**

Add tests with these assertions:

```python
def test_video_platforms_share_one_video_master(self):
    with workspace_tempdir() as tmp:
        run_dir = self.creator.create_run(
            Path(tmp),
            "2026-08-01",
            "label-reading",
            ["douyin", "weixin-channels"],
        )

        expected = [
            "video-master/treatment.md",
            "video-master/shotlist.yaml",
            "video-master/storyboard.md",
            "video-master/edit-plan.md",
            "video-master/qa.md",
            "video-master/external-generation",
            "video-master/incoming",
            "video-master/accepted",
            "video-master/media",
        ]
        for relative in expected:
            self.assertTrue((run_dir / relative).exists(), relative)

        self.assertFalse((run_dir / "douyin" / "storyboard.md").exists())
        self.assertFalse(
            (run_dir / "weixin-channels" / "storyboard.md").exists()
        )


def test_xiaohongshu_only_run_has_no_video_master(self):
    with workspace_tempdir() as tmp:
        run_dir = self.creator.create_run(
            Path(tmp),
            "2026-08-01",
            "label-reading",
            ["xiaohongshu"],
        )
        self.assertFalse((run_dir / "video-master").exists())
```

Update the existing `test_create_run_builds_platform_native_structure` expectation so video platform `storyboard.md` files move to `video-master/storyboard.md`.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```powershell
python -m unittest tests.test_content_run.ContentRunContractTests.test_video_platforms_share_one_video_master tests.test_content_run.ContentRunContractTests.test_xiaohongshu_only_run_has_no_video_master -v
```

Expected: FAIL because `video-master/` does not exist and platform storyboards still exist.

- [ ] **Step 3: Implement the minimal shared structure**

Add:

```python
VIDEO_PLATFORMS = {"douyin", "weixin-channels"}


def needs_video_master(platforms: list[str]) -> bool:
    return bool(VIDEO_PLATFORMS.intersection(platforms))
```

When true, create the shared directories and non-destructive templates once. Stop creating `storyboard.md` in the two platform directories. Keep `publish.md`, `qa.md`, and platform `media/` only if existing validation still needs platform media; otherwise remove platform media in Task 4 after the documentation contract is updated.

- [ ] **Step 4: Update content-run validation**

Change video platform required files from:

```python
("publish.md", "storyboard.md", "qa.md", "media")
```

to:

```python
("publish.md", "qa.md", "media")
```

When either video platform is declared, require:

```python
VIDEO_MASTER_REQUIRED = (
    "treatment.md",
    "shotlist.yaml",
    "storyboard.md",
    "edit-plan.md",
    "qa.md",
    "external-generation",
    "incoming",
    "accepted",
    "media",
)
```

- [ ] **Step 5: Run tests and verify GREEN**

Run:

```powershell
python -m unittest tests.test_content_run -v
```

Expected: all content-run tests PASS.

- [ ] **Step 6: Commit**

```powershell
git add tests/test_content_run.py scripts/create_content_run.py scripts/validate_content_run.py
git commit -m "feat: add shared video master runs"
```

---

### Task 2: External Seedance Task-Package Creator

**Files:**
- Create: `tests/test_external_video_handoff.py`
- Create: `scripts/create_external_video_handoff.py`
- Create: `assets/templates/seedance-shot-card.md`
- Create: `assets/templates/seedance-shot.yaml`
- Create: `assets/templates/seedance-return-checklist.md`

**Interfaces:**
- Produces: `create_handoff(run_dir: Path, shot_specs: list[dict[str, object]], source_root: Path) -> Path`
- Produces: `validate_shot_spec(spec: dict[str, object]) -> list[str]`
- Consumes: source reference paths relative to `source_root`.
- Preserves: existing task files and reference files with identical bytes; rejects conflicting overwrites.

- [ ] **Step 1: Add failing task-package contract tests**

Create tests covering:

```python
class ExternalVideoHandoffTests(unittest.TestCase):
    def test_create_handoff_writes_complete_platform_neutral_shot_package(self):
        spec = {
            "shot_id": "S01",
            "slug": "date-reveal",
            "title": "情人节日期揭晓",
            "input_mode": "first-frame",
            "duration_seconds": 5,
            "draft_resolution": "720p",
            "final_resolution": "1080p",
            "candidate_target": 1,
            "max_attempts": 2,
            "references": [
                {
                    "order": 1,
                    "file": "S01-first-frame-9x16.png",
                    "role": "first_frame",
                    "required": True,
                }
            ],
            "prompt_positive": "暖金色光线缓慢扫过酒标。",
            "prompt_negative": "瓶型变形，白边，灰边，黑边。",
        }

        handoff = self.module.create_handoff(
            run_dir, [spec], source_root
        )

        shot = handoff / "S01-date-reveal"
        for relative in (
            "任务卡.md",
            "shot.yaml",
            "prompt-all-in-one.txt",
            "prompt-positive.txt",
            "prompt-negative.txt",
            "references/S01-first-frame-9x16.png",
        ):
            self.assertTrue((shot / relative).exists(), relative)

        task = (shot / "任务卡.md").read_text(encoding="utf-8")
        self.assertNotIn("第三方平台名称", task)
        self.assertIn("9:16", task)
        self.assertIn("最大尝试次数：2", task)

    def test_create_handoff_never_overwrites_user_edits(self):
        # Create once, edit prompt-positive.txt, create again, assert preserved.

    def test_validate_shot_spec_rejects_missing_mode_and_reference_order(self):
        # Assert errors mention input_mode and references.order.
```

- [ ] **Step 2: Run the new tests and verify RED**

Run:

```powershell
python -m unittest tests.test_external_video_handoff.ExternalVideoHandoffTests -v
```

Expected: ERROR because `create_external_video_handoff.py` does not exist.

- [ ] **Step 3: Implement shot-spec validation**

Use standard-library validation only. Require:

```python
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
```

Reject:

- non-`SNN` shot IDs;
- non-slug names;
- aspect ratios other than `9:16`;
- duration outside 4–15 seconds;
- candidate targets outside 1–2;
- maximum attempts outside 1–2;
- duplicate or non-consecutive reference orders;
- missing first frame in `first-frame`;
- missing first and last frame in `first-last-frame`;
- frame roles mixed with `reference-guided`.

- [ ] **Step 4: Implement non-destructive package creation**

Create:

```text
external-generation/
├── 00-开始前必读.md
├── 00-镜头状态表.csv
├── handoff-manifest.yaml
└── SNN-slug/
```

Copy only declared references. If a destination exists:

- identical SHA-256: retain it;
- different SHA-256: raise `ValueError`;
- prompt/task file exists: never overwrite it.

Write `prompt-all-in-one.txt` as positive prompt followed by a clearly labelled negative-constraints paragraph.

- [ ] **Step 5: Add a CLI**

Support:

```powershell
python scripts/create_external_video_handoff.py `
  --run-dir <run-dir> `
  --spec <shot-specs.json> `
  --source-root <reference-root>
```

The JSON input is an authoring interchange format; each generated shot still receives `shot.yaml`.

- [ ] **Step 6: Run tests and verify GREEN**

Run:

```powershell
python -m unittest tests.test_external_video_handoff.ExternalVideoHandoffTests -v
```

Expected: all handoff creation tests PASS.

- [ ] **Step 7: Commit**

```powershell
git add tests/test_external_video_handoff.py scripts/create_external_video_handoff.py assets/templates/seedance-shot-card.md assets/templates/seedance-shot.yaml assets/templates/seedance-return-checklist.md
git commit -m "feat: create external Seedance task packages"
```

---

### Task 3: Returned-Video Validator

**Files:**
- Modify: `tests/test_external_video_handoff.py`
- Create: `scripts/validate_external_video_return.py`

**Interfaces:**
- Produces: `parse_shot_contract(path: Path) -> dict[str, object]`
- Produces: `validate_probe(metadata: dict[str, object], contract: dict[str, object]) -> list[str]`
- Produces: `validate_filename(path: Path, run_date: str, topic_slug: str, shot_id: str) -> list[str]`
- Produces: `validate_return(video_path: Path, shot_dir: Path, *, probe_command: str = "ffprobe") -> list[str]`

- [ ] **Step 1: Add failing pure validation tests**

Add tests with real metadata dictionaries:

```python
def test_return_validator_accepts_exact_nine_sixteen_metadata(self):
    metadata = {
        "width": 1080,
        "height": 1920,
        "duration": 5.1,
        "codec_type": "video",
    }
    contract = {
        "aspect_ratio": "9:16",
        "duration_seconds": 5,
        "duration_tolerance_seconds": 0.75,
        "final_resolution": "1080p",
    }
    self.assertEqual(self.return_validator.validate_probe(metadata, contract), [])


def test_return_validator_rejects_three_four_and_wrong_duration(self):
    metadata = {
        "width": 1080,
        "height": 1440,
        "duration": 8.0,
        "codec_type": "video",
    }
    errors = self.return_validator.validate_probe(metadata, contract)
    self.assertTrue(any("9:16" in error for error in errors))
    self.assertTrue(any("时长" in error for error in errors))


def test_return_validator_rejects_random_download_name(self):
    errors = self.return_validator.validate_filename(
        Path("seedance_download_123.mp4"),
        "2026-08-01",
        "label-reading",
        "S01",
    )
    self.assertTrue(errors)
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
python -m unittest tests.test_external_video_handoff.ExternalVideoHandoffTests.test_return_validator_accepts_exact_nine_sixteen_metadata tests.test_external_video_handoff.ExternalVideoHandoffTests.test_return_validator_rejects_three_four_and_wrong_duration -v
```

Expected: ERROR because the return validator does not exist.

- [ ] **Step 3: Implement metadata and filename validation**

Require exact reduced ratio `9:16` using `math.gcd(width, height)`. Require final height of at least 1920 for `1080p`, or at least 1280 for `720p`. Accept `.mp4` and `.mov`; reject screenshots and screen recordings by extension/name where detectable.

Use this filename regex:

```python
RETURN_NAME = re.compile(
    r"^(?P<date>\d{8})-wxyj-(?P<topic>[a-z0-9-]+)-"
    r"(?P<shot>s\d{2})-(?P<role>[a-z0-9-]+)-seedance-"
    r"v(?P<version>\d{2})(?:-candidate-[ab])?\.(?:mp4|mov)$",
    re.IGNORECASE,
)
```

- [ ] **Step 4: Implement FFprobe integration**

Run:

```powershell
ffprobe -v error -show_entries stream=codec_type,width,height,r_frame_rate -show_entries format=duration -of json <video>
```

Parse the first video stream and format duration. Return a clear error if FFprobe is unavailable or the file cannot be decoded; do not silently approve.

- [ ] **Step 5: Implement persistent-black-bar diagnostics**

Use FFmpeg `cropdetect` over representative frames. Treat a stable detected crop smaller than the full frame at both top and bottom as a machine warning requiring visual review, not an automatic rejection, because luxury scenes can contain legitimate dark backgrounds.

Return structured CLI output sections:

```text
ERROR
WARNING
PASS
```

- [ ] **Step 6: Run focused and full tests**

Run:

```powershell
python -m unittest tests.test_external_video_handoff -v
python -m unittest tests.test_content_run -v
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```powershell
git add tests/test_external_video_handoff.py scripts/validate_external_video_return.py
git commit -m "feat: validate external Seedance returns"
```

---

### Task 4: Skill Routing and Paid-Generation Boundary

**Files:**
- Modify: `tests/test_repository_contract.py`
- Modify: `SKILL.md`
- Create: `references/video-production-system.md`
- Create: `references/external-seedance-handoff.md`
- Modify: `references/platform-playbooks.md`
- Modify: `references/visual-asset-library.md`
- Modify: `references/content-run-system.md`
- Modify: `references/review-rubric.md`

**Interfaces:**
- Produces: discoverable Skill routing for video-native production and external Seedance handoff.
- Consumes: scripts and templates from Tasks 1–3.

- [ ] **Step 1: Add failing repository-contract tests**

Add:

```python
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
    ):
        self.assertIn(contract, joined)
    self.assertNotIn("必须提供第三方平台名称", joined)


def test_video_generation_requires_native_nine_sixteen(self):
    joined = (
        (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        + (PROJECT_ROOT / "references" / "video-production-system.md")
        .read_text(encoding="utf-8")
    )
    for contract in (
        "1080×1920",
        "原生9:16",
        "3:4图片不能作为全屏主画面",
        "禁止黑边",
    ):
        self.assertIn(contract, joined)
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
python -m unittest tests.test_repository_contract.RepositoryContractTests.test_external_seedance_is_default_and_platform_neutral tests.test_repository_contract.RepositoryContractTests.test_video_generation_requires_native_nine_sixteen -v
```

Expected: FAIL because the two references and routing contracts do not exist.

- [ ] **Step 3: Add concise Skill routing**

Keep `SKILL.md` below 500 lines. Add a video task route that requires:

- `references/video-production-system.md`
- `references/external-seedance-handoff.md`
- `references/visual-asset-library.md`
- the product asset manifest

State the positive default recipe:

```text
生成共享video-master
→ 选择视频制作模式
→ 为external-seedance镜头创建逐镜任务包
→ 等待用户回传
→ 验收incoming
→ 把accepted素材进入可编辑剪辑
```

Add an explicit conditional: only if the user authorizes ChatCut paid generation in the current request may direct generation tools be called.

- [ ] **Step 4: Write the two focused reference systems**

`video-production-system.md` covers:

- V1 hybrid luxury film;
- V2 generative cinematic;
- V3 editorial motion;
- V4 controlled montage;
- tool routing among external Seedance, HyperFrames, Remotion, and ChatCut;
- native 9:16, shot diversity, product identity, typography, and sound rules.

`external-seedance-handoff.md` covers:

- shot package schema;
- reference roles;
- single-field and dual-field prompt delivery;
- user operations;
- return naming;
- statuses;
- cost control;
- QA and revision cards.

Both files exceed 100 lines only if they include `## 目录`.

- [ ] **Step 5: Reconcile existing references**

Remove the generic `9:16 或 3:4` ambiguity from video guidance. Preserve 3:4 only inside Xiaohongshu rules. Update content-run and review references to point at the shared video master and external handoff.

- [ ] **Step 6: Run tests and verify GREEN**

Run:

```powershell
python -m unittest tests.test_repository_contract -v
```

Expected: all repository-contract tests PASS.

- [ ] **Step 7: Commit**

```powershell
git add tests/test_repository_contract.py SKILL.md references/video-production-system.md references/external-seedance-handoff.md references/platform-playbooks.md references/visual-asset-library.md references/content-run-system.md references/review-rubric.md
git commit -m "feat: route video work through external Seedance"
```

---

### Task 5: Public Documentation and Naming Contract

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `docs/content-contract.md`
- Modify: `docs/output-structure.md`
- Modify: `docs/naming-convention.md`
- Modify: `docs/getting-started.md`
- Modify: `llms.txt`
- Modify: `tests/test_repository_contract.py`

**Interfaces:**
- Produces: user-facing operating instructions matching the implemented directories and scripts.

- [ ] **Step 1: Add failing documentation assertions**

Extend repository tests to require:

- `video-master/external-generation`;
- `video-master/incoming`;
- external-generation creator command;
- returned-video validator command;
- platform-neutral wording;
- no claim that ChatCut generation is the default;
- resolved local links.

- [ ] **Step 2: Run documentation tests and verify RED**

Run:

```powershell
python -m unittest tests.test_repository_contract -v
```

Expected: FAIL on missing external handoff documentation.

- [ ] **Step 3: Update Chinese and English README**

Add a concise “外部Seedance协作” section and one directory example. Do not expose SEO/GEO implementation notes. Explain that ChatCut remains an optional editing/export surface and paid generation requires current-task authorization.

- [ ] **Step 4: Update public contracts**

Document:

- native 9:16 video;
- shared master;
- task-package and return naming;
- status meanings;
- CLI commands;
- no-overwrite behavior;
- user/Codex responsibility boundary.

- [ ] **Step 5: Run tests and verify GREEN**

Run:

```powershell
python -m unittest tests.test_repository_contract -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add README.md README.en.md docs/content-contract.md docs/output-structure.md docs/naming-convention.md docs/getting-started.md llms.txt tests/test_repository_contract.py
git commit -m "docs: explain external Seedance workflow"
```

---

### Task 6: August 1 Reference Run

**Files:**
- Modify: `examples/content-runs/2026-08-01-label-reading/manifest.yaml`
- Modify: `examples/content-runs/2026-08-01-label-reading/brief.md`
- Modify: `examples/content-runs/2026-08-01-label-reading/sources.md`
- Create: `examples/content-runs/2026-08-01-label-reading/video-master/**`
- Create: `examples/content-runs/2026-08-01-label-reading/douyin/publish.md`
- Create: `examples/content-runs/2026-08-01-label-reading/douyin/qa.md`
- Create: `examples/content-runs/2026-08-01-label-reading/douyin/media/.gitkeep`
- Create: `examples/content-runs/2026-08-01-label-reading/weixin-channels/publish.md`
- Create: `examples/content-runs/2026-08-01-label-reading/weixin-channels/qa.md`
- Create: `examples/content-runs/2026-08-01-label-reading/weixin-channels/media/.gitkeep`
- Modify: `tests/test_content_run.py`

**Interfaces:**
- Produces: one complete public example showing Xiaohongshu plus a shared Douyin/Weixin video master.

- [ ] **Step 1: Add a failing example test**

Add:

```python
def test_public_example_contains_external_seedance_handoff(self):
    example = (
        PROJECT_ROOT
        / "examples"
        / "content-runs"
        / "2026-08-01-label-reading"
    )
    handoff = example / "video-master" / "external-generation"
    self.assertTrue((handoff / "00-开始前必读.md").exists())
    self.assertTrue((handoff / "00-镜头状态表.csv").exists())
    self.assertGreaterEqual(len(list(handoff.glob("S??-*"))), 2)
```

- [ ] **Step 2: Run example tests and verify RED**

Run:

```powershell
python -m unittest tests.test_content_run.ContentRunContractTests.test_public_example_contains_external_seedance_handoff -v
```

Expected: FAIL because the example has no video master.

- [ ] **Step 3: Build the 8月1日 shared treatment**

Use the approved hybrid structure:

- S01 date-label reveal, external Seedance, strict 9:16 first frame;
- S02 right-45-degree bottle reveal, external Seedance, strict 9:16 first frame;
- S03 exact “1996 → 2026 / 30年” editorial motion;
- S04 cask and strength editorial motion;
- S05 flavour atmosphere, external Seedance or controlled still motion;
- S06 open-box story, controlled still motion with the 175°–180° structure lock;
- S07 interaction close.

Do not generate or commit video binaries. Commit the complete task package, prompts, selected reference copies, publish copy, and QA instructions.

- [ ] **Step 4: Populate platform publish packages**

Use one visual master but separate:

- Douyin 3-second hook, description, tags, pinned comment;
- Weixin Channels 5-second viewing reason, description, tags, first comment, Moments copy.

- [ ] **Step 5: Validate example**

Run:

```powershell
python scripts/validate_content_run.py examples/content-runs/2026-08-01-label-reading
python -m unittest tests.test_content_run -v
```

Expected: both PASS.

- [ ] **Step 6: Commit**

```powershell
git add examples/content-runs/2026-08-01-label-reading tests/test_content_run.py
git commit -m "examples: add external Seedance video handoff"
```

---

### Task 7: Version, Metadata, and Changelog

**Files:**
- Modify: `VERSION`
- Modify: `metadata/project.json`
- Modify: `scripts/create_content_run.py`
- Modify: `CHANGELOG.md`
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `CITATION.cff`
- Modify: `agents/openai.yaml` only if its prompt is stale
- Modify: `tests/test_repository_contract.py`

**Interfaces:**
- Produces: consistent version `2.3.0`.

- [ ] **Step 1: Change the version assertion first**

Update the repository contract expectation from `2.2.2` to `2.3.0`.

- [ ] **Step 2: Run the version test and verify RED**

Run:

```powershell
python -m unittest tests.test_repository_contract.RepositoryContractTests.test_machine_readable_identity_is_consistent -v
```

Expected: FAIL because repository version files still contain `2.2.2`.

- [ ] **Step 3: Update all version surfaces**

Set `2.3.0` in:

- `VERSION`;
- `metadata/project.json`;
- `scripts/create_content_run.py`;
- README badges/text where present;
- `README.en.md`;
- `CITATION.cff`.

Add a changelog entry covering native 9:16 video, external Seedance task packages, shared masters, validation, cost control, and the August 1 example.

- [ ] **Step 4: Verify version consistency**

Run:

```powershell
python -m unittest tests.test_repository_contract.RepositoryContractTests.test_machine_readable_identity_is_consistent -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add VERSION metadata/project.json scripts/create_content_run.py CHANGELOG.md README.md README.en.md CITATION.cff agents/openai.yaml tests/test_repository_contract.py
git commit -m "chore: release external Seedance workflow 2.3.0"
```

---

### Task 8: Full Verification and Deployment

**Files:**
- Verify only; modify files only to correct observed failures.

**Interfaces:**
- Produces: tested repository, installable Skill, pushed GitHub main branch.

- [ ] **Step 1: Run all automated tests**

```powershell
python -m unittest discover -s tests -v
```

Expected: all tests PASS with no warnings or tracebacks.

- [ ] **Step 2: Run repository and asset validators**

```powershell
python scripts/validate_product_assets.py
python scripts/validate_content_run.py examples/content-runs/2026-08-01-label-reading
```

Expected: both PASS.

- [ ] **Step 3: Run the Skill validator**

```powershell
python C:\Users\cme\.codex\skills\.system\skill-creator\scripts\quick_validate.py D:\codex\wxyj-content-system
```

Expected: valid Skill frontmatter and directory structure.

- [ ] **Step 4: Inspect repository state and diff**

```powershell
git status --short
git diff --check
git log --oneline -10
```

Expected: clean worktree, no whitespace errors, task commits present.

- [ ] **Step 5: Push GitHub**

```powershell
git push origin main
```

Expected: remote main updated successfully.

- [ ] **Step 6: Refresh the installed Skill**

Reinstall or update the personal Skill from `ifeihong/wxyj-content-system` using the approved Skill installer. Verify the installed `VERSION` is `2.3.0` and the installed `SKILL.md` routes external Seedance correctly.

- [ ] **Step 7: Report final evidence**

Report:

- version;
- commit range;
- test counts;
- validator results;
- GitHub push result;
- installed Skill path;
- August 1 handoff package path;
- the next user action: generate S01 first and place the original MP4 in `video-master/incoming/`.
