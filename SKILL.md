---
name: wxyj-content-system
description: Use when creating, repurposing, reviewing, scheduling, storing, or analyzing 威熏邑境 brand content for “马克瑞普之选”单一单桶系列威士忌 - 亚伯乐1996 across 小红书, 抖音, 视频号, private messages, WeCom, platform stores, and tasting events.
---

# 威熏邑境自媒体内容生成系统

## 专属范围

这是威熏邑境品牌专属 Skill，不是通用威士忌内容模板。它服务威熏邑境在中国市场的威士忌销售、运营与宣传；当前默认且主要服务的商品是““马克瑞普之选”单一单桶系列威士忌 - 亚伯乐1996”，目标是在小红书、抖音和视频号持续生产以该商品为核心的增长型内容。

- 用户没有指定产品时，默认使用““马克瑞普之选”单一单桶系列威士忌 - 亚伯乐1996”。
- 每次产品内容创作都读取 `references/product-facts.md`；涉及包装品鉴词、品牌故事或人物信息时，同时读取 `references/product-packaging-copy.md`。
- 每次图片或视频生产都先读取 `references/visual-asset-library.md` 和 `assets/products/mackillops-choice-aberlour-1996/asset-manifest.json`，从内置22张参考图中按职责选图。
- 新产品只有在用户明确提供并核验产品卡后才能接入；不得因此稀释当前核心产品定位。

## 核心原则

从真实产品事实出发，一题三做，先增长后转化。每次可发布内容都同时交付视觉/分镜与匹配的标题、正文、标签、评论和 CTA，并保存为可追踪的内容运行包。

## 任务路由

| 任务 | 必读文件 | 交付 |
| --- | --- | --- |
| 定位、栏目、品牌口径 | `references/brand-positioning.md` | 定位、受众、风格、内容比例 |
| 产品文案、事实核验 | `references/product-facts.md`、`references/compliance-and-evidence.md` | 事实白名单、证据缺口、合规口径 |
| 包装、品鉴词、品牌故事 | `references/product-packaging-copy.md` | 包装口径、传播转述、出处 |
| 选题、标题、爆款方向 | `references/content-formulas.md` | 评分后的母题卡 |
| 近期去重与长期日更 | `references/content-diversity-system.md` | 创意记录、30天台账比对、重复修正 |
| 当前热点、节日、节气 | `references/trend-and-calendar-system.md` | 实时检索、适配评分、采用理由 |
| 三平台创作 | `references/platform-playbooks.md` | 平台原生发布包 |
| 小红书套图 | `references/xiaohongshu-carousel-system.md`、`references/editorial-art-direction.md`、`references/text-in-image-system.md`、`references/visual-asset-library.md` | 动态页数、艺术方向、逐页提示词、成图文字、QA |
| 抖音/视频号短视频 | `references/video-production-system.md`、`references/external-seedance-handoff.md`、`references/visual-asset-library.md` | 共享母版、逐镜任务包、回传验收、双平台发布包 |
| 图片/视频 AIGC | `references/visual-asset-library.md`、`references/text-in-image-system.md`、`assets/products/mackillops-choice-aberlour-1996/asset-manifest.json` | 内置参考图编排、提示词、产品锁定、负面词 |
| 内容目录与命名 | `references/content-run-system.md` | 运行目录、文件名、保存与校验 |
| 发布预检与最终交付 | `references/content-run-system.md`、`references/review-rubric.md` | 发布清单、产品视觉验收卡、最终交付索引 |
| 评论、私信、企微、店铺、品鉴会 | `references/conversion-playbook.md` | 分阶段转化话术 |
| 发布审核与复盘 | `references/review-rubric.md` | 评分、退回项、复盘结论 |
| 数据驱动提示与实验 | `references/performance-adaptive-system.md` | 成熟数据简报、主题冷却、单变量实验、平台提示要求 |
| 新品接入 | `assets/templates/product-card.md` | 新产品事实卡 |

只读取与当前任务相关的 references。需要三平台完整成品时，读取全部 references。

## 标准工作流

1. **识别任务**：确定是定位、选题、创作、排期、审核、互动、复盘或新品接入。
2. **锁定事实**：默认商品从 `references/product-facts.md` 取值；先分清“马克瑞普之选＝品牌、亚伯乐＝酒厂、30年＝酒龄”，商品名称固定为““马克瑞普之选”单一单桶系列威士忌 - 亚伯乐1996”，规格为700毫升/瓶，蒸馏日期为1996年2月14日，桶型为PX Sherry Hogshead，桶号261311，酒精度51%；缺失字段标为“待核验”，不推断。
3. **验证并盘点素材**：先执行 `python scripts/validate_product_assets.py`；通过后从内置22张产品参考图选择当前页面或镜头需要的2–3张，再标记真实产品、真实文件、真实活动、主观品鉴、AIGC 或待补。
4. **查询近期创意**：读取最近30天 `creative-ledger.csv`，先排除完整创意指纹、14天视觉配方和连续版式路线重复。
5. **读取成熟效果**：读取近期 `performance-log.csv`；用 `python scripts/analyze_performance.py <台账> --date YYYY-MM-DD --theme-family <主题族> --output <运行目录>/performance-brief.json` 生成简报。发布不足48小时的数据只记录为观察，少于10条可比成熟内容只生成假设。
6. **建立母题与实验**：只回答一个具体用户问题，直接关联当前产品；在 `creative-record.json` 登记主题族、事实、首图机位、钩子结构、CTA、`typography_mode` 和唯一实验变量。主题冷却提示出现时默认换主主题；如继续使用，填写 `campaign_override` 并改变用户问题、首屏形式和主事实中的至少两项。
7. **判断时效**：涉及当前热点、热梗、节日或假期时实时检索；不相关则采用常青主题。
7. **创建运行包**：需要交付可发布内容时，先执行：

```powershell
python scripts/create_content_run.py --root <输出根目录> --date YYYY-MM-DD --slug <topic-slug> --product "“马克瑞普之选”单一单桶系列威士忌 - 亚伯乐1996" --platforms xiaohongshu douyin weixin-channels
```

8. **生成平台版本**：按平台原生结构生成，不机械复制。抖音或视频号视频采用一个共享 `video-master/`；默认路径为“生成共享video-master→选择制作模式→为external-seedance镜头创建逐镜任务包→等待用户回传→验收incoming→把accepted素材进入可编辑剪辑”。
9. **锁定小红书艺术方向、事实、机位与几何**：整套先选一个 `typography_mode`，各页轮换 `layout_pattern`；再建立逐页 `primary_fact_id` 表和机位分配表。完整正面酒瓶统一以 `酒瓶-正面.png` 为 `geometry_master`，不得让风格参考覆盖瓶型。
10. **锁定首轮画幅**：每页首轮原生成文件必须是宽:高 = 3:4，并立即执行 `python scripts/validate_xhs_image.py <image.png>`；不通过就按原提示词重新生成，不允许通过裁切、拉伸或补边把错误比例伪装成合格成图。
11. **保存发布文案**：把采用标题、正文/描述、标签、评论、CTA和最终素材顺序写入各平台 `publish.md`；备选标题只作策划记录。素材来源与事实核验状态只写入内部 `sources.md` 和 `qa.md`。
12. **保存生产资产**：小红书写入 `prompts.md`；视频分镜写入共享 `video-master/storyboard.md`，外部 Seedance 任务写入 `video-master/external-generation/`，用户原始回传写入 `video-master/incoming/`，通过验收的副本写入 `video-master/accepted/`。每个媒体版本在 `qa.md` 标记状态。
13. **执行 QA**：把事实、文字、视觉、AIGC、合规、媒体状态与修改记录写入 `qa.md`；逐项完成人工 `product-visual-qa.md`，发布总览只能引用 `publish` 文件。
14. **登记发布清单**：把每个候选资产的路径、原生画幅、来源类型、页面/镜头角色、产品参考与状态写入 `release-manifest.json`；只有全部质量门槛为 `pass` 或 `not-applicable` 时才把 `release_status` 标为 `publish`。
15. **运行验证**：

```powershell
python scripts/validate_content_run.py <运行目录>
python scripts/validate_release_preflight.py <运行目录>
python scripts/validate_content_diversity.py <运行目录>/creative-record.json --ledger <运营内容库>/creative-ledger.csv
```

16. **生成交付索引**：在 `deliverables.md` 只列出通过发布预检和多样性校验的素材、最终平台文案和共享视频母版。
17. **发布后登记**：把已发布 `creative-record.json` 追加到创意台账，再把平台效果写入 `performance-log.csv`。
18. **交付缺口**：列出仍需补拍、文件核验、库存核验或平台实时确认的项目。

## 发布文案输出契约

生成图片不等于完成内容。每个平台都必须同步生成与画面匹配的发布文案：

| 平台 | `publish.md` 必填 |
| --- | --- |
| 小红书 | 采用标题、备选标题、一句话钩子、发布正文、话题标签、首评、CTA、最终素材顺序 |
| 抖音 | 采用标题、备选标题、3秒钩子、视频简介、话题标签、置顶评论、CTA、最终素材顺序 |
| 视频号 | 采用标题、备选标题、5秒观看理由、视频描述、话题标签、首评、朋友圈转发文案、CTA、最终素材顺序 |

标题、正文和标签必须共享同一母题与事实锚点。标签采用“品类词 + 细分词 + 内容意图词 + 品牌词”，不要堆砌无关热词。

## 小红书成品契约

默认按信息量使用 3–6 页，只有深度主题使用 7–8 页。只有第1页承担封面职责，后续页使用证据、解释、判断、情绪、总结或互动模块。

读取 `performance-brief.json` 后执行：封面点击高但内页价值弱时保留封面钩子，重写第2页；第2页必须直接给出具体产品判断或可保存信息，且不得重复封面标题。冷启动互动采用感官、礼赠或场景选择，不用技术考试式问题要求评论。

每套小红书内容交付：

- 采用标题、备选标题策划记录与一句话钩子；
- 页数及选择依据；
- 套图视觉母版卡；
- 整套 `typography_mode` 与逐页 `layout_pattern`；
- 逐页机位分配表：`view_id`、主体、参考图、透视验收特征；
- 逐页角色、文字密度、精确文案和参考图；
- 逐页完整提示词、负面提示词、局部重绘规则和 QA；
- 已含设计文字的最终图片；
- 发布正文、5–10个聚焦标签、首评和 CTA；
- 整套缩略图总览；
- 内部 `qa.md` 中的素材来源与实物核验缺口；不把内部说明放进公开成图或发布文案。

使用不同产品角度和页面功能，保持同一视觉 DNA，不把所有页面做成封面，不固定生成8页。相邻页面不得使用相同 `view_id`；左右 45°页必须在成图中看到足够的侧面可见宽度、标签平面呈梯形透视和不对称瓶肩，不以文件名或提示词声明代替视觉验收。

套图先分配 `primary_fact_id`；同一 `primary_fact_id` 只能出现一次。桶号只能有一个主视觉事实页，其他页面可以让包装微小字段自然存在，但不得再用传播标题、巨型数字或高对比信息卡强调桶号。五页套图默认完整酒瓶不超过 2 页，其余页面优先使用酒标近景、礼盒、证据或风味静物。

## AIGC 生产契约

公开成品采用以下硬规则：

- 成片画面与图文成图禁止出现账号名“威熏邑境”、缩写“WXYJ”；账号身份由平台头像、昵称和主页承接。
- 禁止出现“下一条”“下期”等续集预告；结尾只保留与本条内容直接相关的自然互动问题。
- 禁止把AIGC或事实核验说明写入成片、成图、标题、正文、评论或 CTA；来源边界继续完整记录在内部 `sources.md` 与 `qa.md`。
- 平台后台要求AI标签时，只使用平台原生开关，不把“创意演绎”“AIGC制作”或“产品信息以实物与文件为准”等说明设计进画面或文案。

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

小红书成品规格固定写入：`3:4 portrait, width:height = 3:4, target 1086x1448 or 1536x2048, full bleed; do not output 2:3, 4:5 or square.` 每次图像生成调用结束后，先对首轮原生成文件执行 `python scripts/validate_xhs_image.py <image.png>`，比例不合格直接重生成；不允许通过裁切、拉伸、扩图或程序改尺寸作为首轮比例修复。

视频全屏画面、运动首帧、尾帧和封面必须原生9:16，成片目标 `1080×1920`。3:4图片不能作为全屏主画面，禁止黑边、上下补边和拉伸。

当 `performance-brief.json` 提示视频前段跳出偏高，逐镜提示词必须锁定：0.0–0.8秒先出现准确的产品主体、酒标或礼盒，并发生可见动作；2.0–5.0秒兑现标题承诺。禁止纯文字、黑底或静态片头。每条视频只测试一个变量，不同时改动标题、时长、首屏、旁白与 CTA。

V4静帧视频必须把一张图片作为一个镜头的唯一素材，在同一时间线项目中以一条连续关键帧曲线完成左到右、右到左或克制推拉。不得把同一图片拆成多张不同裁切的静态片段来假装移动；每镜在 `video-master/motion-plan.json` 登记唯一素材、方向、起止位置和转场。

让多模态生图模型直接生成产品、场景与设计文字的最终图片。不下载字体文件，不用程序贴字，不把无字底图当成静态图文成品。

锁定瓶型、瓶盖、瓶肩、酒标位置和事实字段；软化最外缘像素。白底参考进入深色场景时，重新生成玻璃折射、环境色和接触阴影，禁止白边、灰边、抠图光晕和均匀描边。

所有参考图必须声明角色；冲突时固定采用 `geometry_master > structure_master > label_detail > style_anchor`。完整正面酒瓶只认 `酒瓶-正面.png` 的几何比例；连续3次仍无法保持瓶型时，减少完整酒瓶露出，不接受明显变形的产品。

内置22张图片均为 AIGC 高清产品参考图，只负责身份、角度、结构、材质与构图一致性。它们不是真实拍摄，也不能替代酒标实拍、报关、溯源或授权文件。酒瓶正面与酒标近景是当前最高优先级身份参考；其他图中可见的细小瓶号、铭牌或物流文字不得直接作为发布事实。新增两张半开礼盒图只用于45度或半开状态的结构与透视参考，不能替代正面175°–180°开盒母版。

## 外部视频生成授权边界

抖音与视频号默认采用平台无关的外部 Seedance 交接：Codex 提供当前镜头实际参考图、上传顺序、`prompt-all-in-one.txt`、`prompt-positive.txt`、`prompt-negative.txt`、通用参数和回传命名，用户在任意支持相应输入模式的平台生成。

只有用户在当前任务中当次明确授权使用 ChatCut 生成积分，才允许调用 ChatCut 内置 Seedance、Kling 或其他付费视频生成。未授权时，ChatCut只用于素材管理、可编辑剪辑、字幕、动态图形、声音和导出；镜头失败也不得静默消耗积分补生成。

## 外部视频交付可见性契约

最终回复必须逐镜显示：镜头号、任务卡路径、参考图目录、每张参考图文件名与角色、上传顺序、生成模式、时长、分辨率、输出文件名、完整正向提示词、完整负向提示词和完整一体化提示词。不得只提供目录、只说“提示词已生成”或要求用户自行查找文件。

每个 `任务卡.md` 同样内嵌上述可执行信息，尤其必须直接展开完整一体化提示词；独立的 `prompt-all-in-one.txt`、`prompt-positive.txt`、`prompt-negative.txt` 继续保留，供复制使用。最终回复与任务卡中的文字必须与独立文件一致。

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
- 缺少标题、正文/描述、标签、评论或 CTA；
- 把账号名、续集预告、内部 AIGC 或事实核验说明写进成片、成图或公开发布文案；
- 文件名、运行目录或媒体版本不符合规范。

## 数据复盘

优先读取真实平台数据。效果台账必须记录数据导出时间、发布后小时数、内容形式、真实时长/页数、首屏动作和实验字段，并保留封面点击、2秒跳出、5秒完播、平均观看、收藏、评论、分享、主页访问、关注、私信、企微、店铺、品鉴报名和成交。

- 发布不足48小时或缺少发布后小时数：只作观察；
- 少于10条可比成熟内容：只形成假设，不淘汰栏目或固化公式；
- 同一主题族7天内已有两条成熟内容：触发主题冷却提示，默认改主主题；
- 每条发布候选必须在 `creative-record.json` 填一个实验变量、假设和成功指标，成熟后再写结果。

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
| 多页重复强调同一事实 | 先分配唯一 `primary_fact_id`，桶号只设一个主视觉事实页 |
| 候选稿混入最终总览 | 在 `qa.md` 标记状态，发布总览只引用 `publish` |
| 用 AIGC 提高真实性 | 用真实酒标与文件建立信任，AIGC只做表达 |
| 把184瓶写成当前库存 | 只称该桶总装瓶数，库存另行核验 |

## 可复用资产

- 运行与命名规范：`references/content-run-system.md`
- 发布预检脚本：`scripts/validate_release_preflight.py`
- 内容多样性校验：`scripts/validate_content_diversity.py`
- 效果分析与提示简报：`scripts/analyze_performance.py`
- 高奢编辑艺术方向：`references/editorial-art-direction.md`
- 内容多样性系统：`references/content-diversity-system.md`
- 创意记录模板：`assets/templates/creative-record.json`
- 创意台账模板：`assets/templates/creative-ledger.csv`
- 发布清单模板：`assets/templates/release-manifest.json`
- 产品视觉人工验收卡：`assets/templates/product-visual-qa.md`
- 产品事实：`references/product-facts.md`
- 包装品鉴与故事：`references/product-packaging-copy.md`
- 内置产品资产清单：`assets/products/mackillops-choice-aberlour-1996/asset-manifest.json`
- 内置产品参考图：`assets/products/mackillops-choice-aberlour-1996/reference-images/`
- 平台手册：`references/platform-playbooks.md`
- 产品卡：`assets/templates/product-card.md`
- 选题卡：`assets/templates/topic-card.md`
- 内容简报：`assets/templates/content-brief.md`
- 发布日历：`assets/templates/publishing-calendar.csv`
- 数据台账：`assets/templates/performance-log.csv`
- 数据驱动提示：`references/performance-adaptive-system.md`
- 周复盘：`assets/templates/weekly-review.md`
- 三平台示例：`examples/strategy/three-platform-content-pack.md`
