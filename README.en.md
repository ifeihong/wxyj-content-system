# WXYJ Content System

**WXYJ Content System is a Codex Skill for product-led whisky content operations across Xiaohongshu, Douyin, and WeChat Channels.** It produces platform-native titles, captions, tags, comments, AIGC prompts, storyboards, QA reports, and traceable content-run directories.

Version: `2.1.0`<br>
Skill ID: `wxyj-content-system`<br>
GitHub Repository ID: `wxyj-content-system`

## What it produces

- Xiaohongshu carousel plans, in-image copy, page prompts, captions, hashtags, first comments, and QA;
- Douyin hooks, shot lists, voiceover, subtitles, descriptions, tags, and pinned comments;
- WeChat Channels narratives, descriptions, tags, share copy, and comments;
- product-fact and compliance checks for whisky marketing;
- non-destructive content folders and deterministic media naming;
- AIGC disclosure, reference-image roles, negative prompts, and local redraw rules.

## Quick start

Copy `skill/wxyj-content-system` into your Codex skills directory, then invoke:

```text
Use $wxyj-content-system to create a Xiaohongshu content run with
title options, caption, tags, first comment, page prompts and QA.
```

Create a content run:

```powershell
python skill\wxyj-content-system\scripts\create_content_run.py `
  --root outputs `
  --date 2026-08-01 `
  --slug label-reading `
  --product "马克瑞普之选亚伯乐1996年单桶" `
  --platforms xiaohongshu
```

Validate it:

```powershell
python skill\wxyj-content-system\scripts\validate_content_run.py `
  outputs\2026\08\2026-08-01-label-reading
```

## Design principles

- product facts before generic education;
- one parent topic, three native platform adaptations;
- growth before aggressive conversion;
- real labels and documents establish trust; AIGC supports expression;
- generated images are not complete until matching publish copy exists;
- every run keeps a manifest, sources, media versions, and QA.

See the [Chinese README](README.md), [content contract](docs/content-contract.md), [output structure](docs/output-structure.md), and [compliance guide](docs/compliance.md).

## License

Code, templates, and public documentation are licensed under Apache-2.0. Brand names, trademarks, product images, packaging, authorization files, and third-party platform marks are excluded. See [OPEN_SOURCE.md](OPEN_SOURCE.md).
