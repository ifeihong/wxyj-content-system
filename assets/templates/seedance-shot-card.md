# {{shot_id}} {{title}}

## 生成设置

- 模式：`{{input_mode}}`
- 画幅：`9:16`
- 时长：`{{duration_seconds}}秒`
- 草稿分辨率：`{{draft_resolution}}`
- 成片分辨率：`{{final_resolution}}`
- 候选目标：{{candidate_target}}个
- 最大尝试次数：{{max_attempts}}

## 上传参考图

严格按 `shot.yaml` 的 `references.order` 顺序上传本镜头 `references/` 中的文件。

## 回传

下载原始视频，不录屏、不二次压缩；按 `shot.yaml` 的 `output_name` 命名并放入 `video-master/incoming/`。
