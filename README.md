# 威熏邑境自媒体内容生成系统

**威熏邑境自媒体内容生成系统（WXYJ Content System）是一套面向小红书、抖音和视频号的产品型威士忌内容运营 Codex Skill。** 它把产品事实、选题、标题、正文、Tag、AIGC 图片/视频提示词、发布审核和内容归档组织成一个可重复执行的工作流。

当前版本：`2.1.0`<br>
Skill ID：`wxyj-content-system`<br>
GitHub Repository ID：`wxyj-content-system`

项目名称、版本、平台与 GitHub Topics 同时保存在
[`metadata/project.json`](metadata/project.json)，供脚本和代理读取。

## 适合谁

- 运营中高端威士忌品牌、酒类产品或进口酒业务的团队；
- 需要持续生成小红书图文、抖音脚本和视频号内容的创作者；
- 主要使用 AIGC 视觉，但必须保持真实产品、酒标和溯源边界的运营者；
- 希望把标题、正文、标签、首评、提示词和媒体文件规范归档的内容团队。

## 系统能生成什么

| 模块 | 输出 |
| --- | --- |
| 选题 | 母题、钩子、爆款公式、受众需求、事实锚点、热度与风险 |
| 小红书 | 标题 A/B、动态页数、逐页提示词、图片内文字、正文、Tag、首评、QA |
| 抖音 | 标题、3秒钩子、逐镜分镜、旁白、字幕、简介、Tag、置顶评论 |
| 视频号 | 标题、5秒观看理由、逐镜分镜、描述、Tag、首评、朋友圈转发文案 |
| AIGC | 参考图职责、完整提示词、负面提示词、产品锁定、局部重绘与QA |
| 内容管理 | 标准运行目录、媒体命名、版本保留、发布前自动校验 |
| 运营闭环 | 评论、私信、企微、店铺、品鉴会与数据复盘 |

生成图片只是一个环节。系统要求每套内容同时具备可直接发布的标题、正文/描述、平台标签、首评或置顶评论、CTA 与 AIGC 披露。

## 核心场景

### 小红书图文生成

根据内容信息量选择3–8页，而不是固定生成8页。第1页承担封面职责，后续页按证据、解释、判断、总结和互动分工，并使用不同产品角度保持变化。

### 抖音短视频脚本

生成25–60秒竖屏脚本，包含3秒钩子、逐镜画面、旁白、字幕、封面字、简介、话题标签和置顶评论。

### 视频号内容策划

生成30–90秒完整叙事，强调年份、纪念日、礼赠或品鉴判断，并提供适合朋友圈转发的文案。

### 威士忌 AIGC 内容

使用真实酒瓶、酒标、桶号、包装和文件作为身份或事实参考；AIGC 负责氛围、解释与视觉表达，不冒充真实酒厂、历史现场或顾客反馈。

## 项目结构

```text
wxyj-content-system/
├── README.md
├── README.en.md
├── CHANGELOG.md
├── VERSION
├── OPEN_SOURCE.md
├── docs/
├── skill/
│   └── wxyj-content-system/
│       ├── SKILL.md
│       ├── agents/
│       ├── references/
│       ├── assets/
│       ├── examples/
│       └── scripts/
├── tests/
├── examples/
└── outputs/
```

仓库层面向使用者、贡献者和搜索系统；`skill/wxyj-content-system` 是可以单独安装的 Codex Skill。

## 快速开始

### 1. 安装 Skill

将以下目录复制到 Codex Skills 目录：

```text
skill/wxyj-content-system
```

Windows 默认安装目标：

```text
C:\Users\<用户名>\.codex\skills\wxyj-content-system
```

### 2. 调用

```text
使用 $wxyj-content-system，为8月1日生成一套小红书图文，
同时生成标题A/B、发布正文、Tag、首评、逐页提示词和QA。
```

### 3. 创建标准内容运行包

```powershell
python skill\wxyj-content-system\scripts\create_content_run.py `
  --root outputs `
  --date 2026-08-01 `
  --slug label-reading `
  --product "马克瑞普之选亚伯乐1996年单桶" `
  --platforms xiaohongshu
```

系统创建：

```text
outputs/2026/08/2026-08-01-label-reading/
├── manifest.yaml
├── brief.md
├── sources.md
└── xiaohongshu/
    ├── publish.md
    ├── prompts.md
    ├── qa.md
    └── media/
```

### 4. 验证

```powershell
python skill\wxyj-content-system\scripts\validate_content_run.py `
  outputs\2026\08\2026-08-01-label-reading
```

校验器会检查目录、文件名、标题、正文、Tag、首评、CTA、AIGC披露和高风险表达。

## 小红书发布包标准

每个 `xiaohongshu/publish.md` 必须包含：

1. 主标题；
2. 备选标题；
3. 一句话钩子；
4. 完整发布正文；
5. 5–10个聚焦话题标签；
6. 首评；
7. CTA；
8. AIGC与事实披露。

详细规范参见：

- [内容交付契约](docs/content-contract.md)
- [输出目录](docs/output-structure.md)
- [文件命名](docs/naming-convention.md)
- [合规边界](docs/compliance.md)

## 文件命名示例

```text
20260801-xhs-label-reading-p01-cover-v01.png
20260801-xhs-label-reading-p02-dates-v01.png
20260801-xhs-label-reading-p03-cask-data-v02.png
20260801-xhs-label-reading-p00-qa-overview-v01.png
```

不使用“最终版”“最新版”“新图2”等无法追踪的文件名。视觉发生变化时增加 `vNN`，不覆盖已发布版本。

## SEO 与 GEO 说明

本 README 采用以下可验证原则：

- 首屏直接回答项目是什么、适合谁、能做什么；
- 用清晰标题、自然语言和内部链接组织文本；
- 同时提供中文实体名、英文名、Skill ID、平台和领域关键词；
- 保留独特的产品运营方法、输出契约和可运行示例；
- 不批量堆砌同义关键词，不承诺搜索或生成式回答排名。

Google Search 官方说明，AI搜索仍沿用基础SEO与“有帮助、可靠、以人为本”的内容原则，并不要求特殊的GEO标记或AI专用文件。[官方说明](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)

仓库保留 `llms.txt` 作为代理快速阅读入口，但不把它视为Google排名信号。

## GitHub 元数据建议

Repository description：

```text
Codex Skill for product-led whisky content operations across Xiaohongshu, Douyin and WeChat Channels, including AIGC prompts, captions, tags and QA.
```

Topics：

```text
codex-skill
content-marketing
content-operations
whisky
xiaohongshu
douyin
wechat-channels
aigc
social-media
chinese-content
prompt-engineering
```

GitHub Topics 应使用小写字母、数字和连字符，并保持与项目主题直接相关。[GitHub Topics 文档](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics)

## 常见问题

### 这只是图片生成 Skill 吗？

不是。图片只是媒体资产。系统同时生成选题、标题、正文、Tag、首评、CTA、提示词、分镜、QA和内容目录。

### 是否固定每次生成8张小红书图片？

不固定。轻内容通常3–4页，标准内容5–6页，只有信息量足够的深度主题使用7–8页。

### 是否可以使用同一张酒瓶参考图完成全部页面？

不建议。系统根据页面功能选择正面、45度、酒标、礼盒或文件参考，同时使用统一视觉母版保持连续性。

### 是否会把AIGC图片当成产品证据？

不会。产品事实应由实物酒标、真实产品、进口与溯源材料支撑；AIGC只承担创意表达，并需要披露。

### 能否用于其他威士忌产品？

可以。先使用产品卡接入事实、证据、素材与传播边界，再纳入同一内容系统。

## 文档与维护

- [开始使用](docs/getting-started.md)
- [标准内容示例](examples/README.md)
- [版本策略](docs/versioning.md)
- [更新记录](CHANGELOG.md)
- [开放范围](OPEN_SOURCE.md)
- [参与贡献](CONTRIBUTING.md)

## 许可

代码、模板与公开文档使用 Apache-2.0。威熏邑境名称、商标、产品图片、包装设计、授权文件及第三方平台标识不因本许可而授权。详见 [OPEN_SOURCE.md](OPEN_SOURCE.md)。
