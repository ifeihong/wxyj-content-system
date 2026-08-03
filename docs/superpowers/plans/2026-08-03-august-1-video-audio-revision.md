# August 1 Video Audio Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a new editable ChatCut timeline and final 38.10-second export using the approved seven-part narration, audible first-11-second music mix, and four restrained luxury sound accents without changing the visuals.

**Architecture:** Duplicate the current timeline before editing. Generate seven independent Doubao voice assets, validate their real durations against the locked visual windows, replace the old narration items, separate the first 11 seconds of music onto an anchor track with manual levels, retain follower ducking after 11 seconds, then add library sound effects and verify both timeline state and exported audio.

**Tech Stack:** ChatCut MCP project/timeline tools, Doubao TTS (`ruyayichen`), ChatCut sound-effects library, ChatCut cloud export, local read-only `ffprobe`/`ffmpeg` diagnostics.

## Global Constraints

- Project: `66a36d8c-6dd0-4468-b027-3d459ae07ce2`.
- Source timeline: `137ce63f-be5b-45a6-b95c-4840741ae0f5`, 1080 × 1920, 30 fps.
- Preserve existing visuals, shot order, framing, and 38.10-second duration.
- Voice provider is `doubao`; voice preset is `ruyayichen`.
- Narration text must match `docs/superpowers/specs/2026-08-03-august-1-video-audio-revision-design.md` exactly.
- Do not add “威熏邑境”, “WXYJ”, next-post prompts, AIGC notices, or product-disclaimer text.
- Do not generate paid video or image assets.

---

### Task 1: Create a Reversible Editing Timeline

**Files:**
- Reference: `docs/superpowers/specs/2026-08-03-august-1-video-audio-revision-design.md`
- Modify: ChatCut project timeline state only

**Interfaces:**
- Consumes: source timeline `137ce63f-be5b-45a6-b95c-4840741ae0f5`
- Produces: an activated duplicate timeline named `2026-08-01 推荐旁白音频修订 v04` and its returned timeline id

- [ ] **Step 1: Refresh the source timeline**

Call `read_project` with `view:"timeline"`, `timelineId:"137ce63f-be5b-45a6-b95c-4840741ae0f5"`, and `limit:100`. Confirm 1080 × 1920 at 30 fps, existing BGM on A1, and seven narration items on A2.

- [ ] **Step 2: Duplicate and activate the timeline**

Call `manage_timelines` with:

```json
{
  "action": "duplicate",
  "projectId": "66a36d8c-6dd0-4468-b027-3d459ae07ce2",
  "timelineId": "137ce63f-be5b-45a6-b95c-4840741ae0f5",
  "name": "2026-08-01 推荐旁白音频修订 v04",
  "activate": true
}
```

- [ ] **Step 3: Verify duplicate state**

Read the returned timeline with `view:"timeline"`. Confirm all video/audio items and the 1140-frame BGM clone exist before editing.

### Task 2: Generate Seven Approved Narration Assets

**Files:**
- Reference: `docs/superpowers/specs/2026-08-03-august-1-video-audio-revision-design.md`
- Modify: ChatCut project media pool only

**Interfaces:**
- Consumes: approved script rows S01–S07
- Produces: seven ready audio asset ids with measured durations

- [ ] **Step 1: Submit one TTS job per visual beat**

Call `submit_voice` seven times with `provider:"doubao"`, `voiceId:"ruyayichen"`, `speedRatio:1`, `pitch:0`, and a restrained performance prompt. Use these exact names and texts:

```text
20260801-aberlour30-recommended-s01-v04
一张酒标，写下了两个相同的日子。

20260801-aberlour30-recommended-s02-v04
1996年2月14日，入桶；2026年2月14日，罐瓶。

20260801-aberlour30-recommended-s03-v04
两个情人节之间，沉睡着三十年的时光。

20260801-aberlour30-recommended-s04-v04
桶型、强度与桶号，为这三十年，留下了无法复制的坐标。

20260801-aberlour30-recommended-s05-v04
黑樱桃、无花果与黑可可，在杯中，一层层醒来。

20260801-aberlour30-recommended-s06-v04
打开木盒——守护者永不沉睡。选桶人的名字，也留在这一页。

20260801-aberlour30-recommended-s07-v04
读懂这样的酒标，你最先寻找的，是年份、桶型，还是桶号？
```

Shared performance prompt:

```text
儒雅、近距离、克制、有温度，像在安静的藏酒室里对一位朋友讲述。自然呼吸，不用广告腔、播音腔或资料朗读腔。标点处真实停顿，句尾自然收住，不拖长。
```

- [ ] **Step 2: Track generation once**

Call `track_progress` for all returned job ids. If still running, wait at least the returned interval and perform only one additional status check in this turn.

- [ ] **Step 3: Inspect real durations**

For each completed asset, call `inspect_asset`. Compare real duration to these target windows: S01 `0–120`, S02 `120–300`, S03 `300–480`, S04 `480–660`, S05 `660–810`, S06 `810–990`, S07 `990–1140` frames.

- [ ] **Step 4: Resolve fit before placement**

If an asset is too long, resubmit only that segment with a minimally increased `speedRatio` and the same text. Do not truncate or rewrite. If it fits, record the asset id and measured duration for Task 3.

### Task 3: Replace and Sync Narration

**Files:**
- Modify: duplicated ChatCut timeline A2

**Interfaces:**
- Consumes: seven fitted TTS asset ids from Task 2
- Produces: seven A2 narration items aligned to frames `0,120,300,480,660,810,990`

- [ ] **Step 1: Validate the narration replacement**

Call `edit_item` with `validateOnly:true`, deleting the seven cloned old narration items and adding the seven new audio assets to A2. Each add uses its locked start frame, real duration, `audioFadeIn:0.08`, `audioFadeOut:0.12`, and `decibelAdjustment:0`.

- [ ] **Step 2: Commit the narration replacement**

Repeat the validated `edit_item` payload without `validateOnly`.

- [ ] **Step 3: Verify item placement**

Read A2 on the duplicated timeline and confirm seven non-overlapping items, correct start frames, and no speech extending beyond its visual window.

### Task 4: Rebuild the Background-Music Routing

**Files:**
- Modify: duplicated ChatCut timeline A1 and new audio track

**Interfaces:**
- Consumes: BGM asset `67f5e6134c` and cloned full-length BGM item
- Produces: manually mixed intro from frames 0–330 and follower-routed BGM from frames 330–1140

- [ ] **Step 1: Create an anchor intro-music track**

Call `edit_track` with `action:"create"` and `json:{"trackType":"audio","role":"anchor"}`. Record the returned track id.

- [ ] **Step 2: Validate the BGM split**

Update the cloned A1 BGM item to `from:330`, `durationInFrames:810`, `sourceStartFromInSeconds:11`, `decibelAdjustment:-10`, `audioFadeIn:0.12`, and `audioFadeOut:2.5`. Add four contiguous instances of asset `67f5e6134c` to the new anchor track:

```text
frames 0–120: source 0.0s, -16 dB, 0.4s fade-in
frames 120–289: source 4.0s, -16 dB
frames 289–300: source 9.633s, -11.5 dB
frames 300–330: source 10.0s, -16 dB, 0.12s fade-out
```

Use `edit_item` with `validateOnly:true` before committing.

- [ ] **Step 3: Commit and verify the BGM split**

Apply the validated update/add payload. Read both music tracks and confirm continuous source-time coverage from frame 0 through 1140 with no overlap or gap.

### Task 5: Add Four Restrained Sound Accents

**Files:**
- Modify: duplicated ChatCut timeline and one new anchor audio track

**Interfaces:**
- Consumes: ChatCut sound-effects library items
- Produces: four placed SFX anchored at frames `36`, `123`, `195`, and `306`

- [ ] **Step 1: Search the free sound-effects library**

Use `browse_library` with `category:"sound-effects"` for these queries: `delicate glass chime`, `soft air wood resonance`, `subtle metallic glass shimmer`, and `soft low cinematic impact`. Inspect the best result from each query before placement.

- [ ] **Step 2: Create an SFX anchor track**

Call `edit_track` with `action:"create"` and `json:{"trackType":"audio","role":"anchor"}`.

- [ ] **Step 3: Validate and place SFX**

Use `edit_item` with `validateOnly:true`, then commit four library audio adds with editorial anchor frames 36, 123, 195, and 306. Start at conservative levels between `-18` and `-14 dB`, with short fades where supported.

- [ ] **Step 4: Verify placement**

Read the SFX track and confirm four items exist at the intended visual moments and do not extend into unrelated scenes.

### Task 6: Verify, Export, and Diagnose the Result

**Files:**
- Create after export: `outputs/2026/08/2026-08-01-label-reading-video/final-project/out/20260801-wxyj-label-reading-publish-v04.mp4`
- Create after diagnostics: `outputs/2026/08/2026-08-01-label-reading-video/final-project/qa/20260801-audio-v04-loudness.txt`

**Interfaces:**
- Consumes: completed duplicated ChatCut timeline
- Produces: editable timeline verification, exported MP4, local audio diagnostic report

- [ ] **Step 1: Read back final timeline state**

Use `read_project` with `view:"timeline"`. Confirm video structure is unchanged, seven narration items are present, intro and post-11-second BGM routing are correct, and all four SFX are present.

- [ ] **Step 2: Inspect representative composed frames**

Use `view_timeline_frames` at frames `36,123,195,306,600,1050`. Inspect the returned pixels and confirm no visual edit, crop, overlay, or prohibited text was introduced.

- [ ] **Step 3: Submit the final ChatCut export**

Call `submit_export` with `format:"video"`, `codec:"h264"`, `resolution:"1080p"`, `fps:30`, the duplicated timeline id, and name `20260801-wxyj-label-reading-publish-v04.mp4`.

- [ ] **Step 4: Track and download the export**

Call `track_export` with the returned render id. If incomplete, wait at least ten seconds and check once more. Download the completed `downloadUrl` to the exact output path above.

- [ ] **Step 5: Run read-only technical diagnostics**

Use `ffprobe` to confirm 1080 × 1920, 30 fps, approximately 38.1 seconds, H.264 video, and AAC audio. Use `ffmpeg -filter_complex ebur128=peak=true` to record integrated loudness and true peak in the QA text file. Target approximately `-16 LUFS` and true peak no higher than `-1.5 dBTP`.

- [ ] **Step 6: Perform final sync check**

Report each narration segment’s placement and fit status, the first-11-second music treatment, the four SFX anchors, any mismatch fixes, and whether all expected visual beats have matching narration.
