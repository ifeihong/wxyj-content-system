# 外部 Seedance 视频交接系统设计

## 目标

为威熏邑境建立平台无关的外部 Seedance 生产闭环。Codex 负责逐镜策划、参考图准备、提示词、生成参数、命名、回传验收和最终剪辑；用户在任意支持 Seedance 2.0 的第三方平台生成视频并控制积分与费用。

默认不调用 ChatCut 内置付费视频生成。只有用户在当前任务中明确授权使用 ChatCut 积分时，才允许调用 ChatCut 的 Seedance 生成功能。ChatCut 默认只承担素材管理、可编辑剪辑、字幕、动态图形、声音和最终导出。

## 已确认约束

1. 不绑定具体第三方平台，不要求用户提供平台名称或界面截图。
2. 使用 Seedance 2.0 的通用生成字段与模式，不编写平台按钮级教程。
3. 每个需要用户生成的镜头必须交付独立任务包。
4. 用户不负责从17张产品参考图中自行选图，不负责判断参考图职责和上传顺序。
5. 视频主画面、首帧、尾帧与封面必须原生9:16。
6. 生成费用由用户在第三方平台自行控制；系统必须提供逐镜尝试预算和停止条件。
7. 用户回传第三方平台下载的原始无水印文件，不使用录屏或社交软件二次压缩文件。
8. 抖音与视频号共用一个视频母版，平台目录只保存各自发布文案和必要的发布差异。

## 当前缺口

现有系统只有平台级 `storyboard.md`、`qa.md` 和 `media/`，无法表达：

- 哪些镜头需要外部 Seedance 生成；
- 每镜应该上传哪些参考图以及上传顺序；
- 首帧、尾帧、产品身份、结构、标签和风格参考的职责；
- 单提示词框与正负提示词双框的复制方式；
- 草稿与最终生成的分辨率、时长和尝试预算；
- 用户应如何命名并回传候选视频；
- 回传视频的机器验收、视觉验收和修改闭环；
- 同一个视频母版如何同时服务抖音与视频号。

## 方案选择

### 方案A：单一总文档

把所有镜头、参考图和提示词写进一个 `storyboard.md`。

优点是文件少；缺点是用户需要反复定位段落、寻找图片和判断文件名，容易上传错参考图或覆盖候选文件。不采用。

### 方案B：逐镜任务包

每个镜头拥有独立目录、任务卡、提示词文件、已准备好的参考图和回传目录。

优点是操作路径明确、可逐镜审核、适合不同平台、方便控制费用和版本。采用此方案。

### 方案C：一次性批量ZIP

把所有镜头打包后要求用户一次生成并回传。

优点是启动快；缺点是首镜风格不合格时会浪费后续全部积分。ZIP只作为传输方式，不作为生产顺序。

## 总体架构

一次同时包含抖音与视频号的视频内容运行包采用：

```text
YYYY-MM-DD-topic-slug/
├── manifest.yaml
├── brief.md
├── sources.md
├── video-master/
│   ├── treatment.md
│   ├── shotlist.yaml
│   ├── storyboard.md
│   ├── edit-plan.md
│   ├── qa.md
│   ├── external-generation/
│   │   ├── 00-开始前必读.md
│   │   ├── 00-镜头状态表.csv
│   │   ├── handoff-manifest.yaml
│   │   ├── S01-shot-slug/
│   │   │   ├── 任务卡.md
│   │   │   ├── shot.yaml
│   │   │   ├── prompt-all-in-one.txt
│   │   │   ├── prompt-positive.txt
│   │   │   ├── prompt-negative.txt
│   │   │   └── references/
│   │   └── S02-shot-slug/
│   │       └── ...
│   ├── incoming/
│   ├── accepted/
│   └── media/
├── douyin/
│   ├── publish.md
│   └── qa.md
└── weixin-channels/
    ├── publish.md
    └── qa.md
```

`video-master/`是成片唯一事实源。抖音和视频号不复制同一份分镜和媒体，只保存平台发布文案、封面选择、标题、标签、评论和披露。

## 视频制作方式路由

每个镜头在 `shotlist.yaml` 中指定一种生产方式：

| `production_method` | 用途 |
| --- | --- |
| `external-seedance` | 用户在第三方平台生成的Seedance视频 |
| `hyperframes` | 精确文字、日期、数据和高端动态图形 |
| `remotion` | 复杂参数化、3D或长期品牌模板 |
| `chatcut-edit` | 剪辑、转场、字幕、声音和可编辑合成 |
| `controlled-still-motion` | 经过QA的9:16静帧进行有限视差或镜头运动 |
| `real-footage` | 用户提供的真实产品视频 |

默认一条20–40秒视频只安排2–3个 `external-seedance` 镜头，其余镜头使用可控的动态图形、静帧运动或真实素材完成。

## 逐镜任务包契约

### `shot.yaml`

每镜必须包含以下字段：

```yaml
schema_version: 1
shot_id: S01
slug: date-reveal
title: 情人节日期揭晓
production_method: external-seedance
model: seedance-2.0
input_mode: first-frame
aspect_ratio: 9:16
duration_seconds: 5
draft_resolution: 720p
final_resolution: 1080p
candidate_target: 1
max_attempts: 2
audio_policy: ignore-for-final-mix
output_basename: 20260801-wxyj-date-reveal-s01-seedance
```

`input_mode`只允许：

- `text-to-video`
- `first-frame`
- `first-last-frame`
- `reference-guided`

如果任务要求严格首帧或严格首尾帧，用户不得改用普通多参考图模式。第三方平台不支持指定模式时，将该镜头标记为 `blocked`，不自行降级。

### 参考图清单

`shot.yaml`为每张参考图记录：

```yaml
references:
  - order: 1
    file: references/S01-first-frame-9x16.png
    role: first_frame
    required: true
```

允许的 `role`：

- `first_frame`
- `last_frame`
- `geometry_master`
- `structure_master`
- `label_detail`
- `style_anchor`
- `motion_reference`

任务包必须复制实际需要的文件，不能只写17张产品图库中的原路径。用户只处理当前镜头 `references/` 里的文件。

### 提示词文件

每镜同时交付：

- `prompt-all-in-one.txt`：用于只有一个提示词输入框的平台，包含正向描述和负面约束；
- `prompt-positive.txt`：用于正向提示词输入框；
- `prompt-negative.txt`：用于负面提示词输入框。

三个文件必须表达同一意图。不得要求用户自行把正负提示词重新组合。

Seedance提示词按以下顺序书写：

1. 主体与身份；
2. 动作或环境运动；
3. 场景；
4. 灯光与色彩；
5. 单一镜头运动；
6. 视觉风格；
7. 画质与稳定性；
8. 产品和结构负面约束。

重要年份、日期、桶号、瓶数、酒精度、容量和长文字不交给Seedance重新生成；这些信息由通过QA的首帧保留，或在后续动态图形与时间轴文字中精确呈现。

### `任务卡.md`

任务卡使用固定顺序：

1. 镜头目的；
2. 选择的生成模式；
3. 应上传文件及顺序；
4. 画幅、时长、草稿和最终分辨率；
5. 应复制哪个提示词文件；
6. 建议候选数和最大尝试次数；
7. 六项快速自检；
8. 下载格式和命名；
9. 回传位置；
10. 失败时停止条件。

任务卡不包含任何特定第三方平台的按钮名称。

## 9:16运动首帧规则

产品身份要求高的镜头先制作运动就绪静帧，再交给用户生成视频。

运动首帧必须：

- 原生生成或设计为精确9:16；
- 通过瓶型、瓶盖、瓶颈、瓶肩、瓶身宽高、酒标位置和玻璃底检查；
- 重建产品外缘反射、环境色和接触阴影，不保留白底参考图的白灰轮廓；
- 避开平台顶部、底部和右侧交互安全区；
- 为指定镜头运动保留空间；
- 不把AIGC参考图中的细小瓶号、木盒铭牌或物流文字当作事实证据；
- 开盒画面保持175°–180°且不超过180°，保留左侧故事内页的文字密度和签名版式。

原始产品参考图不直接承担视频画面职责；它们用于制作首帧、锁定身份、结构和角度。

## 用户操作合同

用户每次只需要：

1. 打开一个 `SNN-shot-slug` 目录；
2. 按任务卡顺序上传 `references/` 中的文件；
3. 选择任务卡指定的Seedance模式、9:16、时长和分辨率；
4. 复制单框提示词，或分别复制正负提示词；
5. 下载第三方平台输出的原始无水印MP4；
6. 按任务卡命名并放入 `video-master/incoming/`。

用户只需淘汰明显的黑边、严重变形、多余物体、融化、跳变和明显白灰轮廓。专业产品、逐帧和剪辑可用性QA由Codex完成。

## 回传命名与候选规则

标准文件名：

```text
YYYYMMDD-wxyj-topic-slug-sNN-role-seedance-vNN.mp4
```

候选文件：

```text
YYYYMMDD-wxyj-topic-slug-sNN-role-seedance-v01-candidate-a.mp4
YYYYMMDD-wxyj-topic-slug-sNN-role-seedance-v01-candidate-b.mp4
```

默认每镜回传一个候选。用户无法判断时最多回传两个候选。禁止使用 `final`、`new`、`最新版` 或第三方平台的随机下载文件名。

## 状态与费用控制

`00-镜头状态表.csv`使用：

- `planned`
- `ready-for-user`
- `generating-external`
- `returned`
- `accepted`
- `revision-required`
- `blocked`
- `rejected`
- `placed`

费用规则：

1. 先完成一个代表性镜头，验收风格后再生成后续镜头；
2. 平台支持时，草稿使用720P，确认后再输出1080P；
3. 默认每镜生成一个候选；
4. `max_attempts`默认2；
5. 同一问题连续失败两次后停止抽卡；
6. 停止后优先修改首帧、降低产品运动、改用受控静帧运动或动态图形；
7. 不因一个镜头失败而自动调用ChatCut付费生成。

## 回传验收

### 机器验收

新增验证脚本检查：

- 文件名与当前运行日期、主题、镜头编号一致；
- 文件容器为可支持的视频格式；
- 画幅为精确9:16；
- 分辨率达到任务卡要求；
- 时长位于任务卡目标允许范围；
- 文件可解码且包含视频流；
- 顶部和底部不存在持续性黑边；
- 同一镜头版本号不覆盖历史文件。

### 视觉验收

生成接触表并检查：

- 酒瓶几何是否漂移；
- 产品外缘是否出现白边、灰边、抠图光晕或异常环境色；
- 酒标、液面、瓶口、瓶肩和瓶底是否跳变；
- 木盒结构和开合角度是否真实；
- 是否出现额外瓶盖、酒瓶、标签、门板、合页、手或漂浮物体；
- 镜头运动是否与任务卡一致；
- 是否存在平台水印、烧录字幕或不可用文字；
- 可用区间能否支持最终剪辑。

验收结果写入 `video-master/qa.md`。通过的素材复制到 `accepted/`；`incoming/`始终保留用户回传原件和状态记录。

## 修改闭环

不合格时生成一张“修改卡”，包含：

- 问题时间码；
- 问题类型；
- 应保留部分；
- 修改后的首帧或参考图；
- 修改后的提示词；
- 是否需要重新生成；
- 剩余尝试次数；
- 新版本文件名。

如果只有局部可用，先记录可用时间段，再判断是否能通过剪辑规避。不得为了小问题直接要求用户重新生成完整镜头。

## ChatCut边界

默认允许：

- 导入用户回传的视频；
- 在可编辑时间线中裁切、排序和分层；
- 添加字幕、动态图形、音乐、音效和转场；
- 检查合成画面；
- 在用户要求最终交付时导出。

默认禁止：

- 未经当次明确授权调用ChatCut付费Seedance、Kling或其他视频生成；
- 用ChatCut积分静默补生成缺失镜头；
- 把所有源素材预先压平成单个MP4再放入时间线；
- 用本地程序合成成片代替可编辑ChatCut项目。

## 脚本与模板变更

实施阶段新增：

- `references/video-production-system.md`
- `references/external-seedance-handoff.md`
- `assets/templates/seedance-shot-card.md`
- `assets/templates/seedance-shot.yaml`
- `assets/templates/seedance-return-checklist.md`
- `scripts/create_external_video_handoff.py`
- `scripts/validate_external_video_return.py`

实施阶段更新：

- `SKILL.md`
- `references/platform-playbooks.md`
- `references/visual-asset-library.md`
- `references/content-run-system.md`
- `references/review-rubric.md`
- `README.md`
- `README.en.md`
- `docs/content-contract.md`
- `docs/output-structure.md`
- `docs/naming-convention.md`
- `CHANGELOG.md`
- `VERSION`
- 相关测试和8月1日示例运行包。

详细Seedance流程放在一级引用文件中，`SKILL.md`只保留默认路由、授权边界和必读引用，避免入口文件继续膨胀。

## 测试设计

### 基线失败

当前Skill会把视频生成提示词与分镜写入平台目录，但没有可直接交给用户执行的逐镜任务包，也没有禁止在未明确授权时调用ChatCut积分生成。这一失败已经由实际使用反馈确认。

### 自动化测试

1. 创建同时包含抖音和视频号的运行包时，只创建一个 `video-master/`；
2. 外部任务包创建器按镜头生成完整必填文件；
3. 重复运行不覆盖用户已填写的任务卡、提示词或回传视频；
4. `shot.yaml`缺少模式、9:16、参考图顺序、尝试预算或输出命名时验证失败；
5. 错误文件名、错误镜头号、非9:16、时长不符或无法解码时验证失败；
6. 同一个回传文件不能同时标记为 `accepted` 和 `rejected`；
7. 现有小红书内容运行测试继续通过；
8. 公开8月1日示例运行包通过完整验证。

### Skill行为测试

使用真实任务检查Skill是否：

- 默认生成外部Seedance任务包，而不是直接调用付费生成；
- 不再询问用户使用哪家第三方Seedance平台；
- 自动从17张参考图中选择并复制当前镜头所需文件；
- 同时输出单框与双框提示词；
- 明确用户操作、回传文件名和停止条件；
- 收到回传视频后先验收再进入剪辑；
- 只有用户当次明确授权时才允许使用ChatCut生成积分。

## 完成标准

升级完成后，用户面对每个外部Seedance镜头，只需要“上传指定文件—复制提示词—设置参数—生成—按名称回传”。用户不需要理解参考图角色、产品几何规则、提示词结构、素材目录或剪辑技术。

Codex可以从同一运行包继续完成视频验收、版本管理、ChatCut可编辑剪辑，以及抖音和视频号发布包交付。
