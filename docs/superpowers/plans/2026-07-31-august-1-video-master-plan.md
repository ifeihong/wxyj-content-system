# 8月1日共享视频母版 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 制作一个38秒、1080×1920、可编辑且可同时投放抖音和视频号的威熏邑境V1混合高奢视频母版。

**Architecture:** 在内容运行包之外的本地 `outputs/` 创建独立 Remotion 工程，公共资产目录只复制本次所需的两段 Seedance 回传和4张产品参考图。时间线、事实文字与场景参数由JSON契约驱动，React/TypeScript只负责渲染；Python脚本生成原创音乐床，Edge TTS生成7段普通话旁白，最终用Remotion渲染并由ffprobe与代表帧总览验收。

**Tech Stack:** Remotion、React、TypeScript、Node.js内置测试、Python/NumPy/WAV、Edge TTS、FFmpeg/FFprobe。

## Global Constraints

- 成片固定 `1080×1920`、30fps、38秒、H.264、AAC。
- S01使用4秒完整草稿；S02只使用最稳定的前6秒。
- Seedance输入顶部锚定等比裁切去除底部水印，不拉伸、不补边。
- S03、S04、S07事实文字必须可编辑且逐字匹配事实库。
- S06不得重新生成礼盒结构，只能受控运动现有开盒参考图。
- 所有生成二进制和 `node_modules/` 保存在被忽略的 `outputs/`，不进入GitHub。
- 不调用ChatCut付费视频生成。

---

### Task 1: 隔离工作区与工程契约

**Files:**
- Modify: `.gitignore`
- Modify: `tests/test_repository_contract.py`
- Create: `docs/superpowers/specs/2026-07-31-august-1-video-master-design.md`
- Create: `docs/superpowers/plans/2026-07-31-august-1-video-master-plan.md`

**Interfaces:**
- Consumes: 当前仓库测试与Git工作树规则。
- Produces: 被忽略的 `.worktrees/` 和隔离分支 `codex/august-1-video-master`。

- [ ] **Step 1: 为 `.worktrees/` 写失败的忽略规则测试**

在 `test_local_build_artifacts_are_ignored` 增加：

```python
self.assertRegex(gitignore, r"(?m)^\.worktrees/$")
```

- [ ] **Step 2: 运行红灯测试**

Run: `python -m unittest tests.test_repository_contract.RepositoryContractTests.test_local_build_artifacts_are_ignored -v`
Expected: FAIL，指出 `.worktrees/` 不在 `.gitignore`。

- [ ] **Step 3: 最小修改 `.gitignore` 并重跑测试**

加入一行 `.worktrees/`，重跑同一测试，Expected: PASS。

- [ ] **Step 4: 提交规格与工作树规则并创建隔离工作树**

```powershell
git add .gitignore tests/test_repository_contract.py docs/superpowers/specs/2026-07-31-august-1-video-master-design.md docs/superpowers/plans/2026-07-31-august-1-video-master-plan.md
git commit -m "docs: plan august 1 video master"
git worktree add .worktrees/august-1-video-master -b codex/august-1-video-master
```

### Task 2: 时间线契约与Remotion工程

**Files:**
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/package.json`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/tsconfig.json`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/src/index.ts`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/src/timeline.json`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/tests/timeline.test.mjs`

**Interfaces:**
- Consumes: 设计规格中的7镜时间、事实文字和分辨率。
- Produces: `timeline.json`，字段为 `fps`、`width`、`height`、`durationSeconds`、`shots[]`。

- [ ] **Step 1: 写时间线失败测试**

测试读取 `src/timeline.json`，断言7镜连续、总时长38、1080×1920、30fps，并断言事实字符串 `1996`、`2026`、`PX Sherry Hogshead`、`51.0% Vol.`、`261311` 全部存在。

- [ ] **Step 2: 运行红灯测试**

Run: `node --test tests/timeline.test.mjs`
Expected: FAIL，指出 `timeline.json` 不存在。

- [ ] **Step 3: 创建最小工程与时间线JSON**

场景区间固定为 `[0,4]`、`[4,10]`、`[10,16]`、`[16,22]`、`[22,27]`、`[27,33]`、`[33,38]`。

- [ ] **Step 4: 安装依赖并运行绿灯测试**

Run: `npm install`
Run: `npm test`
Expected: PASS。

### Task 3: 素材接入与原创音频

**Files:**
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/scripts/prepare-assets.ps1`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/scripts/generate_music.py`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/scripts/generate_voice.py`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/public/media/*`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/public/audio/*`

**Interfaces:**
- Consumes: Downloads中的S01/S02原件、4张产品参考图和7句旁白。
- Produces: 哈希匹配的媒体副本、38秒原创音乐WAV和7段独立旁白MP3。

- [ ] **Step 1: 编写素材与音频清单失败测试**

在时间线测试中断言所列媒体与音频文件均存在且非空，首次运行应因文件缺失失败。

- [ ] **Step 2: 无转码复制输入资产并验证SHA-256**

S01必须匹配 `C162C4A6F8466CE1ADA2D40F49401380736AA68F09E00EB4ADB1170ABA071134`；S02必须匹配 `E68043432D77D7AF7EA18E691739B2620F43DE26E6B5AFF4789C854D63880993`。

- [ ] **Step 3: 生成原创音乐和7段旁白**

音乐为48kHz立体声38秒WAV；旁白文本逐句取自 `storyboard.md`，使用沉稳普通话男声并独立输出。

- [ ] **Step 4: 重跑素材测试**

Run: `npm test`
Expected: PASS。

### Task 4: 七镜可编辑画面实现

**Files:**
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/src/Root.tsx`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/src/MasterVideo.tsx`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/src/components/BrandFrame.tsx`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/src/components/Typography.tsx`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/src/scenes/SeedanceScene.tsx`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/src/scenes/TimelineScene.tsx`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/src/scenes/CaskScene.tsx`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/src/scenes/FlavourScene.tsx`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/src/scenes/BoxScene.tsx`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/src/scenes/ClosingScene.tsx`

**Interfaces:**
- Consumes: `timeline.json`、`public/media`、`public/audio`。
- Produces: Composition ID `WxyjAugust1Master`，1140帧、1080×1920、30fps。

- [ ] **Step 1: 编写静态源代码契约测试**

断言Composition ID、1140帧、AIGC披露、7个场景组件和四个事实字段出现在源代码中；首次运行因文件不存在失败。

- [ ] **Step 2: 实现Root、品牌框架与七镜场景**

所有动画仅使用 `useCurrentFrame()`、`interpolate()` 和Remotion `Sequence`；禁止CSS动画。Seedance场景顶部锚定等比裁切，其他场景保持80px横向与100px纵向安全区。

- [ ] **Step 3: 实现音频层和镜头衔接**

音乐全程播放；7段旁白按镜头起点后0.25秒进入；转场只使用8–12帧光扫、遮挡或淡化，不改变38秒总时长。

- [ ] **Step 4: 运行测试与TypeScript检查**

Run: `npm test`
Run: `npm run typecheck`
Expected: 全部PASS。

### Task 5: 代表帧、正式渲染与QA

**Files:**
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/scripts/verify_render.py`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/out/representative/*.png`
- Create: `outputs/2026/08/2026-08-01-label-reading-video/remotion/out/20260801-wxyj-label-reading-master-v01.mp4`
- Modify: `examples/content-runs/2026-08-01-label-reading/video-master/qa.md`

**Interfaces:**
- Consumes: Composition `WxyjAugust1Master`。
- Produces: 经媒体参数和视觉QA的共享母版、7镜代表帧与QA记录。

- [ ] **Step 1: 渲染7张代表帧并逐张审查**

帧号固定为60、210、390、570、735、900、1065。检查焦点、文字、产品边缘、礼盒内页、水印残留与安全区；不合格先修场景再继续。

- [ ] **Step 2: 渲染正式母版**

Run: `npm run render`
Expected: 生成H.264/AAC MP4。

- [ ] **Step 3: 运行媒体QA**

`verify_render.py` 断言宽1080、高1920、30fps、37.85–38.15秒、包含音轨、无持续纯黑上下边。

- [ ] **Step 4: 更新运行包QA并执行仓库验证**

Run: `python -m unittest discover -s tests -v`
Run: `python scripts/validate_content_run.py examples/content-runs/2026-08-01-label-reading`
Run: `git diff --check`
Expected: 全部退出0。

- [ ] **Step 5: 提交、推送并交付**

只提交规格、计划与运行包文字记录；`outputs/`工程和MP4保持本地，不推送GitHub。最终回复提供母版、Remotion工程、代表帧目录及双平台发布文案的绝对路径。
