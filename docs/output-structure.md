# 输出目录规范

## 为什么按“内容运行包”保存

每次内容生产都有日期、主题、平台、参考素材、多个媒体版本和发布文案。把它们放在同一运行目录，可以回答：

- 这张图片属于哪篇内容；
- 发布时使用了哪个标题和Tag；
- 哪些内容是AIGC；
- 当前媒体是第几个版本；
- 发布前检查了什么；
- 后续复盘对应哪一条内容。

## 目录

```text
outputs/YYYY/MM/YYYY-MM-DD-topic-slug/
├── manifest.yaml
├── release-manifest.json
├── creative-record.json
├── performance-brief.json
├── brief.md
├── sources.md
├── product-visual-qa.md
├── ecommerce-asset-qa.md       # 仅电商运行包
├── deliverables.md
├── xiaohongshu/
│   ├── publish.md
│   ├── prompts.md
│   ├── qa.md
│   └── media/
├── ecommerce/                  # 仅电商运行包
│   ├── publish.md
│   ├── prompts.md
│   ├── qa.md
│   └── media/
├── video-master/
│   ├── treatment.md
│   ├── shotlist.yaml
│   ├── storyboard.md
│   ├── edit-plan.md
│   ├── motion-plan.json
│   ├── qa.md
│   ├── external-generation/
│   ├── incoming/
│   ├── accepted/
│   └── media/
├── douyin/
│   ├── publish.md
│   ├── qa.md
│   └── media/
└── weixin-channels/
    ├── publish.md
    ├── qa.md
    └── media/
```

`video-master/external-generation/` 是平台无关的外部 Seedance 交接区；`video-master/incoming/` 永久保留回传原件；`accepted/` 只保存通过验收的副本。平台目录只保存发布文案、平台 QA 和必要导出，不复制共同分镜。

`release-manifest.json` 管理候选、退回与发布资产及事实、证据、产品几何、文字洁净度等质量门槛；`creative-record.json` 管理本条内容的主题、事实、首图机位、版式、钩子、CTA、受众问题、情绪主轴、首屏母题和单变量实验；`performance-brief.json` 记录成熟数据、主题冷却和平台提示。前者回答“能否发布”，创意记录回答“是否与近期内容重复”，效果简报回答“下一条该测试什么”。

## Manifest 字段

```yaml
run_id: 2026-08-01-label-reading
version: 2.9.0
date: 2026-08-01
topic_slug: label-reading
product: "马克瑞普之选 单桶苏格兰威士忌"
status: draft
platforms:
  - xiaohongshu
  - ecommerce
```

状态建议：

- `draft`：生产中；
- `qa`：等待审核；
- `approved`：审核通过；
- `published`：已发布；
- `archived`：归档。

## 输出根目录

脚本默认使用当前工作目录下的 `outputs`。团队可通过 `--root` 指定外部内容库，例如：

```powershell
--root D:\content\wxyj-runs
```

公开 Git 仓库默认忽略 `outputs` 中的生产资产，避免上传大图、客户信息或敏感文件。需要公开的文本示例放入 `examples`。

## 非覆盖原则

- 脚手架只创建缺失文件；
- 已存在的 `publish.md` 不被覆盖；
- 同一运行目录不得在重跑时静默更换产品或增加 manifest 未声明的平台；
- 媒体修改增加 `vNN`；
- 发布后冻结对应版本；
- 旧内容只复制迁移，不移动或删除。
