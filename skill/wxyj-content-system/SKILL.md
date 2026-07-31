---
name: wxyj-content-system
description: Use when creating, repurposing, reviewing, scheduling, storing, or analyzing product-led social content for 威熏邑境, 马克瑞普之选亚伯乐1996年单桶, or future whisky products across 小红书, 抖音, 视频号, private messages, WeCom, platform stores, and tasting events.
---

# 威熏邑境自媒体内容生成系统

## 核心原则

从真实产品事实出发，一题三做，先增长后转化。每次可发布内容都同时交付视觉/分镜与匹配的标题、正文、标签、评论和 CTA，并保存为可追踪的内容运行包。

## 任务路由

| 任务 | 必读文件 | 交付 |
| --- | --- | --- |
| 定位、栏目、品牌口径 | `references/brand-positioning.md` | 定位、受众、风格、内容比例 |
| 产品文案、事实核验 | `references/product-facts.md`、`references/compliance-and-evidence.md` | 事实白名单、证据缺口、合规口径 |
| 包装、品鉴词、品牌故事 | `references/product-packaging-copy.md` | 包装口径、传播转述、出处 |
| 选题、标题、爆款方向 | `references/content-formulas.md` | 评分后的母题卡 |
| 当前热点、节日、节气 | `references/trend-and-calendar-system.md` | 实时检索、适配评分、采用理由 |
| 三平台创作 | `references/platform-playbooks.md` | 平台原生发布包 |
| 小红书套图 | `references/xiaohongshu-carousel-system.md`、`references/text-in-image-system.md`、`references/visual-asset-library.md` | 动态页数、逐页提示词、成图文字、QA |
| 图片/视频 AIGC | `references/visual-asset-library.md`、`references/text-in-image-system.md` | 参考图编排、提示词、产品锁定、负面词 |
| 内容目录与命名 | `references/content-run-system.md` | 运行目录、文件名、保存与校验 |
| 评论、私信、企微、店铺、品鉴会 | `references/conversion-playbook.md` | 分阶段转化话术 |
| 发布审核与复盘 | `references/review-rubric.md` | 评分、退回项、复盘结论 |
| 新品接入 | `assets/templates/product-card.md` | 新产品事实卡 |

只读取与当前任务相关的 references。需要三平台完整成品时，读取全部 references。

## 标准工作流

1. **识别任务**：确定是定位、选题、创作、排期、审核、互动、复盘或新品接入。
2. **锁定事实**：从 `references/product-facts.md` 取值；缺失字段标为“待核验”，不推断。
3. **盘点素材**：标记真实产品、真实文件、真实活动、主观品鉴、AIGC 或待补。
4. **建立母题**：只回答一个具体用户问题，直接关联当前产品。
5. **判断时效**：涉及当前热点、热梗、节日或假期时实时检索；不相关则采用常青主题。
6. **创建运行包**：需要交付可发布内容时，先执行：

```powershell
python scripts/create_content_run.py --root <输出根目录> --date YYYY-MM-DD --slug <topic-slug> --product "<正式产品名>" --platforms xiaohongshu douyin weixin-channels
```

7. **生成平台版本**：按平台原生结构生成，不机械复制。
8. **保存发布文案**：把标题、正文/描述、标签、评论、CTA 和披露写入各平台 `publish.md`。
9. **保存生产资产**：小红书写入 `prompts.md`，视频写入 `storyboard.md`，媒体写入 `media/`。
10. **执行 QA**：把事实、文字、视觉、AIGC、合规与修改记录写入 `qa.md`。
11. **运行验证**：

```powershell
python scripts/validate_content_run.py <运行目录>
```

12. **交付缺口**：列出仍需补拍、文件核验、库存核验或平台实时确认的项目。

## 发布文案输出契约

生成图片不等于完成内容。每个平台都必须同步生成与画面匹配的发布文案：

| 平台 | `publish.md` 必填 |
| --- | --- |
| 小红书 | 主标题、备选标题、一句话钩子、发布正文、话题标签、首评、CTA、AIGC与事实披露 |
| 抖音 | 主标题、备选标题、3秒钩子、视频简介、话题标签、置顶评论、CTA、AIGC与事实披露 |
| 视频号 | 主标题、备选标题、5秒观看理由、视频描述、话题标签、首评、朋友圈转发文案、CTA、AIGC与事实披露 |

标题、正文和标签必须共享同一母题与事实锚点。标签采用“品类词 + 细分词 + 内容意图词 + 品牌词”，不要堆砌无关热词。

## 小红书成品契约

默认按信息量使用 3–6 页，只有深度主题使用 7–8 页。只有第1页承担封面职责，后续页使用证据、解释、判断、情绪、总结或互动模块。

每套小红书内容交付：

- 标题 A/B 与一句话钩子；
- 页数及选择依据；
- 套图视觉母版卡；
- 逐页角色、文字密度、精确文案和参考图；
- 逐页完整提示词、负面提示词、局部重绘规则和 QA；
- 已含设计文字的最终图片；
- 发布正文、5–10个聚焦标签、首评和 CTA；
- 整套缩略图总览；
- AIGC 披露与实物核验缺口。

使用不同产品角度和页面功能，保持同一视觉 DNA，不把所有页面做成封面，不固定生成8页。

## AIGC 生产契约

为每页、封面或镜头依次输出：

1. 成品规格；
2. 画面目标；
3. 完整生成提示词；
4. 负面提示词；
5. 参考图及职责；
6. 产品硬锁字段；
7. `Text (verbatim)` 与产品保护区；
8. 制作方式；
9. 局部重绘策略；
10. 生成后 QA。

让多模态生图模型直接生成产品、场景与设计文字的最终图片。不下载字体文件，不用程序贴字，不把无字底图当成静态图文成品。

锁定瓶型、瓶盖、瓶肩、酒标位置和事实字段；软化最外缘像素。白底参考进入深色场景时，重新生成玻璃折射、环境色和接触阴影，禁止白边、灰边、抠图光晕和均匀描边。

## 产品与内容比例

- 70% 产品原生：年份、日期、桶号、总装瓶数、酒精度、酒标、风味与购买判断；
- 20% 产品延展：从该酒解释亚伯乐、斯佩塞、单桶、高年份与桶强；
- 10% 品牌与场景：进口、包装、礼赠、品鉴会和新品。

核心传播词为“亚伯乐30年”“30年”“2月14日”“情人节”。按事实边界使用，不把传播词替代法定商品名。

## 审核门槛

使用 `references/review-rubric.md` 评分。低于80分不标记为可发布。以下情况直接退回：

- 产品事实错误或来源冲突；
- AIGC 冒充真实酒厂、人物、历史现场、品鉴或顾客反馈；
- 金融收益、绝对品质或虚假紧迫承诺；
- 未成年人导向、豪饮或酒驾暗示；
- 把总装瓶数写成当前库存；
- 缺少标题、正文/描述、标签、评论、CTA 或 AIGC 披露；
- 文件名、运行目录或媒体版本不符合规范。

## 数据复盘

优先读取真实平台数据。记录曝光/播放、留存/完成、收藏、评论、分享、主页访问、关注、私信、企微、店铺、品鉴报名和成交。

- 高播放低关注：强化账号承诺与关注理由；
- 高收藏低播放：保留内容价值，重做标题和封面；
- 高私信低成交：补足价格解释、信任证据和承接；
- 同类内容少于10条：不淘汰整个栏目；
- 单条爆款：只形成假设，不立即改变定位。

## 常见错误

| 错误 | 修正 |
| --- | --- |
| 只生成图片，不生成发布文案 | 同步完成 `publish.md` 全部字段 |
| 文件散落在日期根目录 | 先创建运行包，再保存平台资产 |
| 用“最终版”“新图”命名 | 使用日期、平台、主题、页/镜、角色和版本号 |
| 三平台复制同一稿 | 共享母题，重写开头、结构和 CTA |
| 每篇固定8页 | 按信息量选择动态页数 |
| 每页都使用同一角度 | 为页面角色选择不同产品参考 |
| 用 AIGC 提高真实性 | 用真实酒标与文件建立信任，AIGC只做表达 |
| 把184瓶写成当前库存 | 只称该桶总装瓶数，库存另行核验 |

## 可复用资产

- 运行与命名规范：`references/content-run-system.md`
- 产品事实：`references/product-facts.md`
- 平台手册：`references/platform-playbooks.md`
- 产品卡：`assets/templates/product-card.md`
- 选题卡：`assets/templates/topic-card.md`
- 内容简报：`assets/templates/content-brief.md`
- 发布日历：`assets/templates/publishing-calendar.csv`
- 数据台账：`assets/templates/performance-log.csv`
- 周复盘：`assets/templates/weekly-review.md`
- 三平台示例：`examples/three-platform-content-pack.md`
