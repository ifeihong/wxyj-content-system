# 开始使用

## 前置条件

- Codex 或兼容 Agent Skills 的运行环境；
- Python 3.10 或更高版本；
- Skill 已内置马克瑞普之选亚伯乐1996年单桶的产品知识与17张 AIGC 高清参考图；
- 发布前仍需使用真实酒标、实物照片及运营方文件核对消费者事实。

## 安装

本仓库根目录就是 Skill 根目录。把克隆后的整个
`wxyj-content-system` 目录复制到 Codex Skills 目录。

确认最终路径包含：

```text
<Codex Skills>/wxyj-content-system/SKILL.md
<Codex Skills>/wxyj-content-system/assets/products/mackillops-choice-aberlour-1996/reference-images/
```

## 第一次调用

```text
使用 $wxyj-content-system，
为马克瑞普之选亚伯乐1996年单桶生成一套小红书内容。
输出标题A/B、正文、Tag、首评、逐页提示词、参考图和QA。
```

## 标准生产步骤

1. 明确日期、平台、母题和目标；
2. 创建内容运行目录；
3. 填写 `brief.md` 和 `sources.md`；
4. 生成平台 `publish.md`；
5. 生成小红书 `prompts.md` 或视频 `storyboard.md`；
6. 保存媒体并使用规范文件名；
7. 完成 `qa.md`；
8. 运行目录校验器；
9. 发布后更新状态和数据台账。

## 创建运行目录

```powershell
python scripts\create_content_run.py `
  --root outputs `
  --date 2026-08-01 `
  --slug label-reading `
  --product "马克瑞普之选亚伯乐1996年单桶" `
  --platforms xiaohongshu douyin weixin-channels
```

只需要小红书时：

```powershell
python scripts\create_content_run.py `
  --root outputs `
  --date 2026-08-01 `
  --slug label-reading `
  --product "马克瑞普之选亚伯乐1996年单桶" `
  --platforms xiaohongshu
```

当前产品可省略 `--product`。创建新品内容运行包时，必须显式传入新品的正式产品名。

## 验证

```powershell
python scripts\validate_product_assets.py

python scripts\validate_content_run.py `
  outputs\2026\08\2026-08-01-label-reading
```

第一条命令验证17张内置参考图及其 SHA-256，第二条命令验证内容运行包。验证通过后，仍需人工查看最终图片、视频、酒标细节、平台预览和实时商品信息。

## 推荐工作频率

- 每日：一个母题、一个主平台成品、其他平台按需转译；
- 每周：复盘标题、封面、收藏、评论、关注和素材缺口；
- 每月：更新产品事实、平台规则、栏目表现和新品卡。
