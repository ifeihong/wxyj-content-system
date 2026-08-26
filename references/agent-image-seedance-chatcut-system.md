# Agent 生图、Seedance 与 ChatCut 三层交接系统

## 目标

把视频生产拆成清晰的三层，避免用户反复在多个工具之间补图、补提示词或猜剪辑规则。

| 层 | 责任方 | 交付物 | 不负责 |
| --- | --- | --- | --- |
| Agent 生图层 | Codex + 多模态生图 | 静态镜头成图、每个 Seedance 镜头的原生9:16首帧/主参考图、产品视觉QA | 不生成外部 Seedance 视频 |
| Seedance 动态层 | 用户的第三方平台 | 按任务卡生成的纯动态原片 | 不生成字幕、日期、数字、线条、图形或剪辑效果 |
| ChatCut 剪辑层 | ChatCut | 可编辑时间线、镜头排序、转场、旁白、BGM、音效、字幕、导出 | 不额外调用付费视频生成，除非用户当次授权 |

## Agent 生图层：必须直接产出文件

每条含视频的平台内容，在创建运行包后由 Agent 直接调用多模态生图能力：

1. 在 `video-master/agent-images/seedance-references/` 生成每个 Seedance 镜头一张原生9:16 `SNN-...-seedance-ref-v01.png`；它是该镜头经过QA的首帧/主参考图。
2. 在 `video-master/agent-images/static-shots/` 生成每个静态镜头一张原生9:16 `SNN-...-static-v01.png`；它直接进入 ChatCut，且一图只对应一镜。
3. 每张图均保存对应 `SNN-...-image-qa.md`，记录参考图角色、瓶型/礼盒验收、边缘融合、文字洁净度、状态与版本。
4. 生成失败先做一次针对性局部修订；若连续两次仍无法保持完整瓶身几何，改为酒标近景、礼盒、内页或无完整瓶身的构图，不接受失真的完整酒瓶。

### 生图硬规则

- 静态镜头图与 Seedance 首帧均为精确1080×1920原生9:16；用 `python scripts/validate_agent_images.py <run-dir>` 验证，不得由3:4补边或拉伸而来。
- 每张图明确使用 `geometry_master`、`structure_master`、`dimension_check`、`label_detail` 和 `style_anchor` 的职责；产品几何优先。
- Agent 在深色新场景中重建透明玻璃反射、环境色和接触阴影，去除白边、灰边、抠图光晕；不得把白底产品图直接抠贴进场景。
- 这些图是视频原始素材，不预生成字幕、日期、年份、参数、时间线、扫描线、金色轨迹、UI、数据卡或转场图形。

## 用户 Seedance 交付包

每个外部镜头都必须把 Agent 已生成的 `seedance-ref` 复制到：

```text
video-master/external-generation/SNN-shot/references/
```

并在 `shot.yaml` 与 `任务卡.md` 中登记：

- `source: agent`、角色 `first_frame` 或 `shot_keyframe`；
- 紧随其后的产品几何、礼盒结构、尺寸和酒标参考；
- 上传顺序、时长、原生9:16分辨率、完整正负提示词、回传文件名；
- 参考图具体职责、必须保留与不得继承。

外部提示词只描述真实产品、礼盒、场景、自然光、材料和自然相机运动。所有设计文字、旁白、音乐、音效、转场和事实呈现留给 ChatCut。

## ChatCut 交接包

ChatCut 只读取并执行下列文件：

| 文件 | 用途 |
| --- | --- |
| `video-master/storyboard.md` | 时间线、画面职责、旁白句子、字幕内容与安全区 |
| `video-master/edit-plan.md` | 可编辑剪辑步骤、转场、字幕、音频和导出设置 |
| `video-master/motion-plan.json` | 静态图唯一素材、连续关键帧、转场时长与音频电平 |
| `video-master/agent-images/static-shots/` | 静态镜头原图 |
| `video-master/accepted/` | 通过验收的 Seedance 原片 |

ChatCut 不应读取外部 Seedance 的生成提示词来创建画面；它只负责把既有素材编辑成可审核、可修改的时间线。

## 验收顺序

1. Agent 生图QA：产品比例、礼盒结构、原生9:16、边缘融合。
2. Seedance 原片QA：画幅、时长、瓶型/酒标稳定、无额外文字标志。
3. ChatCut 时间线QA：静态镜头运动连续、转场自然、字幕不挡主体、旁白与画面同步、BGM全程可听且不压旁白、末尾延展不重置。

只有三层均通过，才可将 `release-manifest.json` 标记为 `publish`。
