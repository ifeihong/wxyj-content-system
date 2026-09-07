# v3.4.1 可靠性修复与迁移

本次只修交付、校验与安装一致性，不增加新的创意配额，不改产品事实和23张原始参考图。

## 修复范围

| 已复现问题 | 修复方式 | 仍需人工判断 |
| --- | --- | --- |
| PNG只有24字节文件头也通过 | Pillow先verify再load完整解码，缺依赖报错 | 瓶型、标签、光线与文字是否正确 |
| 修改时长/提示词后仍输出旧卡 | 同源渲染；更新前检查所有文件冲突；保存旧版 | 人工文案合并与新图验收 |
| 改视觉职责即可掩盖同机位 | 去重比较主体区域、机位、景别，不依赖职责名称 | 改名或近似机位仍需全片接触表核对 |
| null台词、字符串true绕过检查 | 必填文字和布尔类型严格检查 | 旁白是否自然且匹配画面 |
| 3:4任务被9:16规则否决 | 计划、任务卡、TXT、回传统一当次画幅 | 首轮原生比例与裁切历史 |
| 发布清单只有working资产也通过 | 必须有publish资产，视频必须有实际导出文件 | 成片播放、运动连续性和声音表现 |
| 倍率设置与用户要求不一致 | publish对照production-plan中的requested_motion | 实际渲染关键帧是否达到登记值 |
| 安装副本残留旧说明 | 受管理文件列表、备份、逐文件hash复核 | 不管理的用户扩展文件 |

## 外部任务包更新

沿用 `python scripts/create_external_video_handoff.py --run-dir <运行目录> --spec <镜头规格JSON> --source-root <产品原图目录>`。

- 初建状态为pending-qa，不代表图片已通过视觉验收。Agent完成逐图与全片QA后再登记ready。
- 任务卡内三段可复制内容分别与三个TXT保持一致；正向/一体化包含参考职责、生成模式、素材秒数和画幅；负向只放禁止变形、新增印字等约束，不含正向生成参数。
- `.generated-state.json`保存生成来源hash。规格更新而目标文件未人工改动时会更新，旧内容备份至`external-generation/.history/<版本号>/`。
- 同一规格重跑时保留人工修改并发出警告，不表示修改后的卡片已重新验收；规格已变且目标含人工修改则停止，要求合并或新建版本运行包。
- 参考图字节变更、镜头编号/slug/文件集合变化：使用新的版本运行包，不覆盖原任务包。没有生成记录的老包如与新内容不同，也报告冲突。
- 更新前会检查全部规格与参考文件，避免已知冲突出现后部分文案已改。磁盘故障仍可能中断写入；报错后从备份恢复或检查差异，不能宣称更新成功。
- 生成器不会替你改写production-plan的revision、人工QA或发布状态。更新后重新登记新hash、检查适配性，不把旧验收沿用为新版本验收。

首帧模式使用一张生成图；首尾帧模式使用两个对应槽位；reference-guided使用辅助参考，不混写首尾帧。text-to-video只用于不可识别产品的氛围镜头，不承担整瓶还原。平台不支持所需模式时停止，不擅自降级。

## 发布登记新增要求

静态镜头在production-plan中登记当次确认值，例如：

```json
"requested_motion": {"motion_pattern":"push-in","start_scale":1.0,"end_scale":1.06}
```

motion-plan保持同镜头顺序、source_type、起止倍率与运动类型。平移还要登记start_position/end_position；用户要求静止则用hold并写理由。不额外强制所有任务100%→106%。这些字段只能约束计划，不能证明实际动画已执行。

release-manifest的schema 5视频发布还需：

```json
"video_acceptance": {
  "status": "pass",
  "render_path": "video-master/final.mp4",
  "render_sha256": "实际成片SHA-256",
  "editable_project": {"path":"video-master/project-evidence.json","sha256":"实际文件SHA-256"},
  "av_review": {"path":"video-master/av-review.md","sha256":"实际文件SHA-256"}
}
```

render_path必须已登记为publish视频。project-evidence保存实际ChatCut项目ID、链接、时间线版本及最近读取结果（或实际工程导出），不是只写计划名称；av-review记录同一成片hash、逐镜首中尾帧、每个转场、旁白最后一句、片尾延长段和音乐分段听检的结果。未实际查看/听取不得写pass。机器检查证据文件/hash存在，不判断其中内容真实与否。

所有publish资产必须登记native_ratio（1:1、3:4、9:16）；电商详情长图用`native_ratio: long`加`pixel_size: [实际宽, 实际高]`。视频元数据需ffprobe可用；ffprobe读取成功不是完整播放验收。

## 安装与迁移

Python图片校验新增Pillow依赖：`python -m pip install Pillow`。需联网安装时遵循环境授权，不自动下载。

运行 `python scripts/sync_installed_skill.py --source <仓库根> --target <安装根> --backup-root <备份目录>`先预览，确认后加`--apply`。安装位置在可写范围之外时必须申请授权。备份目录不得位于安装目录内。

同步仅覆盖明确的Skill文档、脚本、模板和产品参考图库；逐文件hash复核。退役清单仅含README.en.md，移出前备份；不递归清理用户文件、不推送outputs。仓库修改、安装同步、本地git提交和GitHub推送是四个不同状态，分别报告。

历史内容包原样保留。再次使用schema 5发布时补齐上面的证据；工作中草稿仍允许unset，不应因草稿未完成就伪填pass。已确认的图片与视频不自动重生成。

## 验证与下一阶段边界

```powershell
python -X utf8 -m unittest discover -s tests
python scripts/validate_product_assets.py
python scripts/validate_video_production_plan.py <运行目录> --stage ready
python scripts/validate_release_preflight.py <运行目录>
```

回归测试覆盖文件完整性、错误输入、安全更新、画幅、发布漏检和安装备份，不是实际短视频视觉或音频质量认证。v3.5.0才考虑更深入的瓶型对照输出、渲染首中尾证据自动采集与统一生成编排，本版本不宣称已具备这些能力。
