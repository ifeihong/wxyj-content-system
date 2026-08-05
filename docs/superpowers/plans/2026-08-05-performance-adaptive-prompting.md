# v2.7.0 Performance-Adaptive Prompting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded performance-feedback loop that improves the next content prompt without overfitting early platform data.

**Architecture:** Keep source performance data in a portable CSV; use a new pure-Python analyzer to produce a per-run performance brief. Extend the existing creative record validator and run creator with experiment fields, then route the resulting brief through Skill and reference instructions.

**Tech Stack:** Python 3 standard library, Markdown, JSON, CSV, unittest.

## Global Constraints

- Treat rows younger than 48 hours or with unknown age as observations, not hard rules.
- Keep the current product facts, compliance, visual QA and v2.6.0 diversity gates unchanged.
- Use one declared experimental variable per publish candidate.
- Keep dominant-theme cooldown as a documented planning warning, not a release block.
- Preserve public-copy restrictions: no account watermark, AIGC disclosure or sequel language.

---

### Task 1: Add performance model regression tests

**Files:**
- Modify: `tests/test_content_run.py`
- Modify: `tests/test_repository_contract.py`

**Interfaces:**
- Consumes: `scripts/analyze_performance.py::analyze_performance`
- Produces: assertions for maturity, cooldown, brief fields and experiment validation.

- [ ] **Step 1: Write failing analyzer tests**

```python
brief = analyzer.analyze_performance(log, candidate_date="2026-08-05", theme_family="date-story")
self.assertEqual(brief["mature_rows"], 2)
self.assertTrue(brief["theme_cooldown"]["active"])
self.assertNotIn("unknown-age-row", brief["theme_cooldown"]["recent_content_ids"])
```

- [ ] **Step 2: Run focused test to verify it fails**

Run: `python -m unittest tests.test_content_run.ContentRunContractTests.test_performance_analyzer_ignores_immature_rows -v`

- [ ] **Step 3: Write failing creative-record experiment test**

```python
candidate["status"] = "publish-candidate"
candidate["experiment"] = {"variable": "", "hypothesis": "", "success_metric": "", "baseline": "", "result": "pending"}
self.assertIn("发布候选缺少实验字段: variable", validator.validate_record(candidate))
```

- [ ] **Step 4: Run focused test to verify it fails**

Run: `python -m unittest tests.test_content_run.ContentRunContractTests.test_diversity_validator_requires_experiment_for_publish_candidate -v`

### Task 2: Implement performance brief and experiment validation

**Files:**
- Create: `scripts/analyze_performance.py`
- Modify: `scripts/validate_content_diversity.py`
- Modify: `scripts/create_content_run.py`
- Modify: `assets/templates/performance-log.csv`
- Modify: `assets/templates/creative-record.json`

**Interfaces:**
- Produces: `analyze_performance(log_path, candidate_date, theme_family) -> dict`
- Produces: per-run `performance-brief.json`

- [ ] **Step 1: Implement analyzer with standard-library CSV parsing**

```python
def analyze_performance(log_path: Path, *, candidate_date: str, theme_family: str) -> dict:
    # Parse rows, separate mature rows, detect cooldown and emit planning requirements.
```

- [ ] **Step 2: Extend record schema with experiment and campaign override**

```python
EXPERIMENT_FIELDS = ("variable", "hypothesis", "success_metric", "baseline", "result")
```

- [ ] **Step 3: Seed new run files without overwriting user work**

```python
_write_once(run_dir / "performance-brief.json", json.dumps(default_brief, ensure_ascii=False, indent=2) + "\n")
```

- [ ] **Step 4: Run focused tests**

Run: `python -m unittest tests.test_content_run -v`

### Task 3: Route performance feedback into prompts and docs

**Files:**
- Create: `references/performance-adaptive-system.md`
- Modify: `SKILL.md`
- Modify: `references/review-rubric.md`
- Modify: `references/content-diversity-system.md`
- Modify: `references/video-production-system.md`
- Modify: `references/xiaohongshu-carousel-system.md`
- Modify: `README.md`
- Modify: `README.en.md`

**Interfaces:**
- Consumes: `performance-brief.json`
- Produces: pre-creation data brief, platform-specific retention prompt blocks and cold-start interaction rules.

- [ ] **Step 1: Document maturity and cooldown policy**
- [ ] **Step 2: Add explicit video and Xiaohongshu prompt contracts**
- [ ] **Step 3: Add Skill route and standard workflow steps**
- [ ] **Step 4: Run repository contract tests**

Run: `python -m unittest tests.test_repository_contract -v`

### Task 4: Release and verify v2.7.0

**Files:**
- Modify: `VERSION`
- Modify: `CHANGELOG.md`
- Modify: `CITATION.cff`
- Modify: `metadata/project.json`
- Modify: `docs/versioning.md`
- Modify: `docs/output-structure.md`
- Modify: `docs/getting-started.md`
- Modify: `llms.txt`

- [ ] **Step 1: Update version metadata to 2.7.0**
- [ ] **Step 2: Run full test suite and Skill validator**

Run: `python -m unittest discover -s tests -v`

Run: `python C:\Users\cme\.codex\skills\.system\skill-creator\scripts\quick_validate.py .`

- [ ] **Step 3: Check whitespace and repository status**

Run: `git diff --check && git status --short`

- [ ] **Step 4: Commit the verified release**

```bash
git add .
git commit -m "feat: release wxyj content system v2.7.0"
```
