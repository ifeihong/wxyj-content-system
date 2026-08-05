# v2.7.0 Performance-Adaptive Prompting Design

## Goal

Turn mature platform performance data into a bounded planning input for the next 威熏邑境 content run. Preserve v2.6.0 creative diversity and avoid treating three cold-start posts as permanent truth.

## Scope

v2.7.0 adds four connected units:

1. A wider `performance-log.csv` that preserves platform-native metrics, publication age, creative execution and one declared experiment.
2. A `performance-brief.json` in each new run. It records the historical-data state, the single variable under test, the success metric and the content restrictions that follow from mature data.
3. A deterministic `analyze_performance.py` script that reads the log and writes/prints the brief. Rows younger than 48 hours remain observations and cannot create a hard instruction.
4. A soft seven-day theme cooldown. A recent dominant theme produces a planning warning, not an automatic release rejection; a declared campaign override remains possible.

## Data Model

`creative-record.json` gains `experiment`:

```json
{
  "variable": "first-second-product-reveal",
  "hypothesis": "完整产品和可见动作会降低前2秒跳出",
  "success_metric": "two_second_bounce_rate",
  "baseline": "recent mature douyin median",
  "result": "pending"
}
```

The record stays valid for working runs with blank experiment values. A publish candidate must provide a non-empty variable, hypothesis and success metric. This turns the rule into an auditable planning discipline without falsely requiring a result before posting.

The performance log keeps common fields and adds platform-native fields such as `data_exported_at`, `hours_since_publish`, `content_format`, `duration_seconds`, `page_count`, `hook_execution`, `two_second_bounce_rate`, `five_second_completion_rate`, `average_watch_seconds`, `cover_click_rate`, `profile_visit`, `mature_data`, `experiment_variable`, `experiment_hypothesis`, and `experiment_result`.

## Decision Rules

- Mature data means `hours_since_publish >= 48`; unknown age is an observation.
- Fewer than ten mature comparable rows create hypotheses only, never a permanent performance rule.
- A theme published twice in the previous seven days is in cooldown. The next candidate receives a warning asking for a different primary theme. A `campaign_override` field may document a deliberate exception.
- A next-run brief must contain exactly one experimental variable. It can use one of `first-second-product-reveal`, `hook-copy`, `duration`, `cover-utility`, `comment-prompt`, or a specific custom value.
- For video, a retention brief requires a visible product or product-detail event in 0.0–0.8 seconds and title payoff by 5.0 seconds; it does not mandate a fixed duration. The next test can set a 15–22 second target when the data supports a short-form test.
- For Xiaohongshu carousels, the cover creates curiosity and page 2 must deliver a specific product judgment. The same title may not be repeated as the page-2 headline.
- Cold-start interaction prompts must be low-cognitive-load sensory, gifting or scenario choices. Technical-field questions remain suitable only for an education-focused run.

## Interfaces

`analyze_performance.py <performance-log.csv> --date YYYY-MM-DD --theme-family <value> [--output <brief.json>]` returns JSON or writes JSON. It reports:

- `mature_rows`, `observation_rows`, `baseline_status`;
- `theme_cooldown` and recent content IDs;
- platform recommendations derived only from mature rows;
- a `required_planning_fields` checklist.

`create_content_run.py` creates `performance-brief.json` and seeds `creative-record.json` with `experiment` and `campaign_override` fields. It does not silently analyze an external operating ledger because a new run may be created offline.

## Verification

- Tests prove a sub-48-hour row cannot trigger a performance rule.
- Tests prove two same-theme published rows within seven days trigger cooldown warning, while an override documents the exception.
- Tests prove a publish candidate requires a complete experiment declaration and working runs remain creatable.
- Tests prove generated briefs include product-first video and Xiaohongshu page-2 requirements.
- Existing 65 tests and all repository-link checks continue to pass.
