# WXYJ Content System

**WXYJ Content System is a brand-specific Codex Skill for 威熏邑境, currently centered on 马克瑞普之选亚伯乐1996年单桶 across Xiaohongshu, Douyin, and WeChat Channels.** It bundles verified product knowledge, packaging copy, brand-story boundaries, 17 high-resolution AIGC product references, platform-native copy, prompts, storyboards, QA, and traceable content-run directories.

Version: `2.6.0`<br>
Skill ID: `wxyj-content-system`<br>
GitHub Repository ID: `wxyj-content-system`

## What it produces

- Xiaohongshu carousel plans, in-image copy, page prompts, captions, hashtags, first comments, and QA;
- Douyin hooks, shot lists, voiceover, subtitles, descriptions, tags, and pinned comments;
- WeChat Channels narratives, descriptions, tags, share copy, and comments;
- product-fact and compliance checks for whisky marketing;
- non-destructive content folders and deterministic media naming;
- machine-readable release manifests, human product-geometry sign-off, and a final deliverables index;
- creative fingerprints, recent-content diversity checks, and six editorial art-direction routes;
- internal AIGC source records, reference-image roles, negative prompts, and local redraw rules; public copy uses only platform-native AI labels when required.

## Current product

The default product is 马克瑞普之选亚伯乐1996年单桶: Speyside, distilled
on 14 February 1996, bottled on 14 February 2026, 30 years old,
PX Sherry Hogshead, cask 261311, 51% ABV, 70cl, and 184 bottles in total.

The bundled asset library contains 17 original PNG references under
[`assets/products/mackillops-choice-aberlour-1996/reference-images/`](assets/products/mackillops-choice-aberlour-1996/reference-images/).
These AIGC references are restricted brand assets and are not covered by Apache-2.0.

## Quick start

The repository root is the Skill root. Copy the cloned repository directory into
your Codex skills directory, then invoke:

```text
Use $wxyj-content-system to create a Xiaohongshu content run with
title options, caption, tags, first comment, page prompts and QA.
```

Create a content run:

```powershell
python scripts\create_content_run.py `
  --root outputs `
  --date 2026-08-01 `
  --slug label-reading `
  --product "马克瑞普之选亚伯乐1996年单桶" `
  --platforms xiaohongshu
```

Validate it:

```powershell
python scripts\validate_product_assets.py

python scripts\validate_content_run.py `
  outputs\2026\08\2026-08-01-label-reading

python scripts\validate_release_preflight.py `
  outputs\2026\08\2026-08-01-label-reading

python scripts\validate_content_diversity.py `
  outputs\2026\08\2026-08-01-label-reading\creative-record.json `
  --ledger <content-library>\creative-ledger.csv
```

## Platform-neutral external Seedance handoff

Douyin and WeChat Channels share one native 9:16 `video-master`. External Seedance generation is platform-neutral: Codex prepares per-shot reference files, upload order, combined and split prompts, common settings, and return names; the user may generate on any compatible provider.

```text
video-master/
├── external-generation/
├── incoming/
├── accepted/
├── storyboard.md
└── edit-plan.md
```

`video-master/incoming` preserves every original return. Only validated copies enter `accepted`. ChatCut remains an optional editable cutting, subtitle, motion-graphics, audio, and export surface. Paid ChatCut generation requires explicit current-task authorization.

Per-shot task packages live under `video-master/external-generation`; original files are returned to `video-master/incoming`.

```powershell
python scripts\create_external_video_handoff.py --run-dir <run> --spec <shots.json> --source-root <references>
python scripts\validate_external_video_return.py <video> --shot-dir <shot-directory>
```

## Design principles

- product facts before generic education;
- one parent topic, three native platform adaptations;
- growth before aggressive conversion;
- real labels and documents establish trust; AIGC supports expression;
- generated images are not complete until matching publish copy exists;
- every run keeps a manifest, sources, media versions, and QA;
- complete front-bottle pages share one geometry master and a 5% proportion tolerance;
- each carousel assigns one primary fact per page, and publish overviews exclude rejected generations.

See the [Chinese README](README.md), [content contract](docs/content-contract.md), [output structure](docs/output-structure.md), and [compliance guide](docs/compliance.md).

## License

Code, templates, and public documentation are licensed under Apache-2.0. Brand names, trademarks, product images, packaging, authorization files, and third-party platform marks are excluded. See [OPEN_SOURCE.md](OPEN_SOURCE.md).
