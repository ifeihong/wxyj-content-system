# 内容多样性与创意台账

## 目录

1. 使用时机
2. 创意记录字段
3. 重复门槛
4. 验证与发布后登记

## 使用时机

每次确定母题前先读取最近30天创意台账与近期 `performance-log.csv`；生成完页面角色、机位和版式后填写运行包根目录的 `creative-record.json`。同一主题可以继续做，但必须改变事实组合、首图机位、钩子或艺术执行，不能只换标题。

## 创意记录字段

| 字段 | 含义 |
| --- | --- |
| `theme_family` | 稳定主题族，如日期故事、风味旅程、礼盒仪式、酒标解读 |
| `primary_fact_ids` | 本条内容承担主视觉的事实ID集合 |
| `hero_view_id` | 首图或第一镜主要产品机位 |
| `view_ids` | 按页面/镜头顺序记录的机位 |
| `typography_mode` | 整套高奢编辑艺术方向 |
| `hook_pattern` | 钩子结构，如时间反差、问题、感官隐喻、数字证据 |
| `cta_type` | 评论、收藏、分享、关注、私信等主要动作 |
| `audience_question` | 本条实际回答的用户问题，不能只写泛泛主题 |
| `emotion_axis` | 收藏、礼赠、时间、风味、包装或判断等情绪主轴 |
| `hero_visual_motif` | 首屏视觉母题，如开盒仪式、酒标微距、时间数字或风味静物 |
| `product_form` | 首屏主要产品形态，如完整酒瓶、半开礼盒、酒标、背标或外箱 |
| `interaction_type` | 评论区的低门槛动作，如感官选择、礼赠选择或保存判断 |
| `experiment` | 本条唯一实验变量、假设、成功指标、基线和结果 |
| `campaign_override` | 主题冷却期间继续使用该主题时的活动理由 |

运行包中的记录状态依次为 `working`、`publish-candidate`、`published` 或 `archived`。只有准备发布时才改为 `publish-candidate` 并执行历史比对。

## 重复门槛

- 30天硬门槛：`theme_family + primary_fact_ids + hero_view_id + hook_pattern` 完全相同，退回重新策划。
- 14天视觉门槛：`theme_family + hero_view_id + typography_mode` 相同，退回更换首图或艺术方向。
- 连续轮换门槛：同一 `typography_mode` 不得连续发布三次。
- 14天叙事门槛：`audience_question + emotion_axis + hero_visual_motif + product_form` 相同，退回重新选择受众切入或首屏形态。
- 效果冷却提示：最近7天同一主题族已有两条成熟内容时，默认更换主主题；这是提示，不替代上面三条创意硬门槛。详见 `performance-adaptive-system.md`。
- 同一主题族本身不是错误；只要事实、视角、钩子和版式执行形成新的用户价值即可继续使用。
- 热点或节日也执行同样门槛，不能以“当前正热”为由复制旧内容结构。

## 验证与发布后登记

从 `assets/templates/creative-ledger.csv` 建立运营台账。发布候选执行：

```powershell
python scripts/validate_content_diversity.py `
  <运行目录>/creative-record.json `
  --ledger <运营内容库>/creative-ledger.csv
```

通过后才能把内容放入 `deliverables.md`。发布后把 `creative-record.json` 对应字段追加到台账，并把状态改为 `published`；效果指标继续写入 `performance-log.csv`。创意台账回答“近期做过什么”，效果台账回答“做得怎么样”，两者不能互相替代。
