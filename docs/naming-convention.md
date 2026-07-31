# 文件命名规范

## Topic Slug

Topic slug 表达一次内容的核心问题：

```text
label-reading
px-sherry-hogshead
thirty-year-dates
single-cask-184-bottles
```

要求：

- 小写英文字母、数字和连字符；
- 不使用空格、中文或下划线；
- 不使用 `final`、`new`、`latest`；
- 保持2–5个短词。

## 运行目录

```text
YYYY-MM-DD-topic-slug
```

示例：

```text
2026-08-01-label-reading
```

## 平台代码

| 平台 | 代码 | 目录 |
| --- | --- | --- |
| 小红书 | `xhs` | `xiaohongshu` |
| 抖音 | `dy` | `douyin` |
| 视频号 | `wxv` | `weixin-channels` |

## 小红书媒体

```text
YYYYMMDD-xhs-topic-slug-pNN-role-vNN.ext
```

常用 role：

- `cover`
- `dates`
- `label`
- `cask-data`
- `tasting-notes`
- `summary`
- `interaction`
- `qa-overview`

QA 总览使用 `p00`。

## 视频媒体

```text
YYYYMMDD-dy-topic-slug-sNN-role-vNN.ext
YYYYMMDD-wxv-topic-slug-sNN-role-vNN.ext
```

常用 role：

- `hook`
- `bottle`
- `label-closeup`
- `timeline`
- `flavor`
- `summary`
- `cta`

## 版本

- 首次生成：`v01`
- 第一次视觉修改：`v02`
- 第二次视觉修改：`v03`

仅修改发布文案时不复制媒体，在 `qa.md` 中记录正文版本。媒体像素或视频内容变化时增加媒体版本。
