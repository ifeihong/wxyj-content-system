# 外部 Seedance 逐镜交接规范

## 目录

1. 核心原则与目录契约
2. 镜头字段、输入模式与参考图
3. 提示词与交付可见性
4. 用户执行、回传与状态
5. 成本控制、验收与修订

## 核心原则

这是平台无关的外部 Seedance 工作流。无需询问用户使用哪家第三方平台，也不编写按钮级教程。Codex 负责把每个镜头整理成可直接执行的任务包；用户只需上传指定参考图、复制提示词、设置通用参数、生成并回传原始视频。

默认外部生成。只有用户在当前任务中当次明确授权使用 ChatCut 生成积分，才允许改用 ChatCut 内置 Seedance、Kling 或其他付费视频生成。

## 目录契约

```text
video-master/
├── external-generation/
│   ├── 00-开始前必读.md
│   ├── 00-镜头状态表.csv
│   ├── handoff-manifest.yaml
│   └── SNN-shot-slug/
│       ├── 任务卡.md
│       ├── shot.yaml
│       ├── prompt-all-in-one.txt
│       ├── prompt-positive.txt
│       ├── prompt-negative.txt
│       └── references/
├── incoming/
└── accepted/
```

`incoming` 永久保留用户下载的原始回传文件。只有经过机器检查与人工 QA 的版本才复制到 `accepted`，不能移动或覆盖原件。

## shot.yaml 必填字段

```yaml
shot_id: S01
slug: date-reveal
title: "情人节日期揭晓"
input_mode: first-frame
aspect_ratio: 9:16
duration_seconds: 5
duration_tolerance_seconds: 0.75
draft_resolution: 720p
final_resolution: 1080p
candidate_target: 1
max_attempts: 2
output_name: 20260801-wxyj-label-reading-s01-date-reveal-seedance-v01.mp4
```

镜头号使用 `SNN`，slug 使用小写英文与连字符。`max_attempts` 默认且最多为2，`candidate_target` 默认为1。

## 通用输入模式

| 模式 | 使用条件 | 必须参考 |
| --- | --- | --- |
| `text-to-video` | 不包含可识别产品的纯氛围镜头 | 无 |
| `first-frame` | 首帧已严格锁定产品与构图 | `first_frame` |
| `first-last-frame` | 需要确定起止构图与转场 | `first_frame` + `last_frame` |
| `reference-guided` | 多参考身份、结构或风格控制 | 不混用首尾帧角色 |

第三方平台不支持任务卡指定模式时，把镜头标记为 `blocked`，不要自行降级到其他模式。

## 参考图角色与顺序

- `first_frame`：原生9:16、已完成产品与文字 QA 的运动首帧。
- `last_frame`：原生9:16、与首帧身份和光线一致的尾帧。
- `geometry_master`：锁定瓶型比例和关键结构。
- `structure_master`：锁定木盒、包装开合与相对位置。
- `label_detail`：只用于酒标信息和材质细节。
- `style_anchor`：只提供色彩、光线、材质和设计语法。
- `motion_reference`：只提供运动方式，不覆盖产品身份。

任务包必须复制当前镜头实际需要的参考文件，并在 `references.order` 中给出上传顺序。不得只写22张图库的原始路径，不能要求用户自行找图。半开礼盒镜头应优先复制新增的 `木质礼盒-45度°半打开内置酒瓶.png` 或 `木质礼盒-半打开内置酒瓶.png`，正面175°–180°开盒镜头使用 `木质礼盒-内置酒瓶.png`。

## 提示词交付

每个镜头同时提供：

- `prompt-all-in-one.txt`：适用于只有一个提示词框的平台；
- `prompt-positive.txt`：动作、场景、构图、镜头、光线、产品硬锁；
- `prompt-negative.txt`：变形、跳变、白灰边、黑边、伪文字和禁止运动。

正向提示词顺序为：主体身份→构图→动作→镜头→光线与材质→产品锁定→结束状态。负向提示词必须明确：瓶型变形、标签漂移、液面跳变、额外瓶盖、白边、灰边、抠图光晕、黑边、伪文字、重复标识、礼盒超过180°。

年份、日期、30 YEARS、261311、51.0%、70cl、184瓶等事实不要让视频模型重新生成。使用经过 QA 的首帧保留，或在可编辑时间线上精确制作。

## 交付可见性

最终回复必须逐镜显示任务卡路径、参考图目录、参考图文件名与角色、上传顺序、模式、时长、分辨率、输出命名、完整正向提示词、完整负向提示词和完整一体化提示词。不得只提供目录，不得只说“详见任务包”，也不得让用户自行在多层文件夹中寻找。

每个 `任务卡.md` 必须把三种提示词全文展开，并同时保留三个独立提示词文件。任务卡、独立文件与最终回复必须内容一致；一体化提示词等于正向提示词加清晰标记的负面约束。

## 用户执行步骤

1. 只打开当前镜头目录；
2. 阅读 `任务卡.md`；
3. 按顺序上传 `references/` 中的文件；
4. 选择任务卡指定的通用输入模式；
5. 设置9:16、时长和分辨率；
6. 复制单字段或双字段提示词；
7. 首次只生成一个候选；
8. 下载原始 MP4/MOV，不录屏、不二次压缩；
9. 按 `output_name` 命名并放入 `video-master/incoming/`。

## 回传命名

```text
YYYYMMDD-wxyj-topic-slug-sNN-role-seedance-vNN.mp4
```

可选候选后缀为 `-candidate-a` 或 `-candidate-b`。随机下载名、录屏名、错误日期、错误主题或错误镜头号不进入 QA。

## 状态

| 状态 | 含义 |
| --- | --- |
| `ready` | 任务包完整，可生成 |
| `generated` | 用户已生成但尚未回传 |
| `returned` | 原件已进入 `incoming` |
| `accepted` | 机器与人工 QA 通过，已复制到 `accepted` |
| `revision-needed` | 存在明确可修问题 |
| `rejected` | 不可用于成片 |
| `blocked` | 平台能力或素材条件不足 |

## 成本控制

- 默认一个候选；
- 第一次失败先定位单一主因；
- 第二次只修改对应参考图或提示词；
- 同一问题连续失败两次后停止抽卡；
- 不因镜头失败自动调用 ChatCut 付费生成；
- S01 通过后再批量启动后续镜头。

## 验收与修订卡

先运行：

```powershell
python scripts/validate_external_video_return.py `
  <video-master/incoming/文件.mp4> `
  --shot-dir <video-master/external-generation/SNN-shot-slug>
```

机器检查精确9:16、分辨率、时长、命名、可解码性与持续上下黑边。人工继续检查瓶型、酒标、液面、白灰轮廓、礼盒结构、运动自然度、文字和品牌气质。

退回时只写一张修订卡：

```text
镜头：
失败主因：
保留不变：
本次只修改：
替换参考图：
提示词增量：
剩余尝试次数：
```

不得用“再高级一点”“更像参考图”等不可验证描述。通过后使用 `--accept` 复制到 `accepted`；原始 `incoming` 文件继续保留。
