# 内容运行目录与文件命名系统

## 目录

1. 适用范围与创建运行包
2. 标准目录与文件职责
3. 运行目录与媒体命名
4. 发布文案与标签
5. 版本规则与验证

## 适用范围

需要交付可发布的小红书、抖音或视频号内容时使用。本规范管理一次内容生产从简报、文案、提示词、媒体到 QA 的完整文件链。

## 创建运行包

```powershell
python scripts/create_content_run.py `
  --root <输出根目录> `
  --date 2026-08-01 `
  --slug label-reading `
  --product "马克瑞普之选亚伯乐1996年单桶" `
  --platforms xiaohongshu douyin weixin-channels
```

脚本重复执行不覆盖已有文件。当前产品可省略 `--product`；接入新品时必须显式传入正式产品名。同一目录重跑时，产品和平台必须已经由原 manifest 声明；需要新增平台时创建新运行目录或先人工审核并更新 manifest，脚本不会擅自改写。需要修改媒体时创建新版本号，不覆盖旧文件。

## 标准目录

```text
outputs/
└── 2026/
    └── 08/
        └── 2026-08-01-label-reading/
            ├── manifest.yaml
            ├── brief.md
            ├── sources.md
            ├── xiaohongshu/
            │   ├── publish.md
            │   ├── prompts.md
            │   ├── qa.md
            │   └── media/
            ├── douyin/
            │   ├── publish.md
            │   ├── storyboard.md
            │   ├── qa.md
            │   └── media/
            └── weixin-channels/
                ├── publish.md
                ├── storyboard.md
                ├── qa.md
                └── media/
```

只创建本次需要的平台目录。

## 基础文件职责

| 文件 | 职责 |
| --- | --- |
| `manifest.yaml` | 运行ID、系统版本、日期、主题、产品、平台和状态 |
| `brief.md` | 母题、受众、事实、目标和创意边界 |
| `sources.md` | 实物、文件、AIGC参考和待核验项 |
| `publish.md` | 可直接复制到平台的标题、正文、标签、评论与 CTA |
| `prompts.md` | 小红书逐页生成提示词与参考图 |
| `storyboard.md` | 视频逐镜分镜、旁白、字幕和生成提示词 |
| `qa.md` | 事实、文字、视觉、合规、AIGC和修改记录 |
| `media/` | 最终媒体和保留的历史版本 |

## 运行目录命名

格式：

```text
YYYY-MM-DD-topic-slug
```

要求：

- 日期使用 ISO 格式；
- slug 只使用小写英文字母、数字和连字符；
- slug 表达母题，不使用 `final`、`new`、`最新版`；
- 同一母题同一天只使用一个运行目录。

## 媒体文件命名

### 小红书

```text
YYYYMMDD-xhs-topic-slug-pNN-role-vNN.png
```

示例：

```text
20260801-xhs-label-reading-p01-cover-v01.png
20260801-xhs-label-reading-p02-dates-v01.png
20260801-xhs-label-reading-p03-cask-data-v02.png
20260801-xhs-label-reading-p00-qa-overview-v01.png
```

### 抖音

```text
YYYYMMDD-dy-topic-slug-sNN-role-vNN.mp4
```

### 视频号

```text
YYYYMMDD-wxv-topic-slug-sNN-role-vNN.mp4
```

`pNN` 表示页码，`sNN` 表示镜头号，`vNN` 表示资产版本。QA总览使用 `p00`。

## 发布文案字段

### 小红书

1. 主标题；
2. 备选标题；
3. 一句话钩子；
4. 发布正文；
5. 话题标签；
6. 首评；
7. CTA；
8. AIGC与事实披露。

### 抖音

1. 主标题；
2. 备选标题；
3. 3秒钩子；
4. 视频简介；
5. 话题标签；
6. 置顶评论；
7. CTA；
8. AIGC与事实披露。

### 视频号

1. 主标题；
2. 备选标题；
3. 5秒观看理由；
4. 视频描述；
5. 话题标签；
6. 首评；
7. 朋友圈转发文案；
8. CTA；
9. AIGC与事实披露。

## 标签组合

采用四层标签，不机械追求数量：

```text
品类词 + 细分词 + 内容意图词 + 品牌词
```

小红书通常5–10个，抖音通常5–8个，视频号通常3–6个。热点词只有在实时核验且与母题直接相关时使用。

## 版本规则

- 首次生成使用 `v01`；
- 改文案但媒体未变：更新 `publish.md`，在 `qa.md` 记录；
- 媒体视觉发生变化：创建 `v02`，保留 `v01`；
- 发布后冻结对应版本，不覆盖；
- 新日期或新母题创建新的运行目录。

## 验证

```powershell
python scripts/validate_content_run.py <运行目录>
```

退出码：

- `0`：通过；
- `1`：目录、发布文案、文件名或风险表达存在问题。
