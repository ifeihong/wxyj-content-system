# 生产内容运行目录

实际内容按以下结构生成：

```text
YYYY/MM/YYYY-MM-DD-topic-slug/
```

生产媒体默认不提交到公开仓库。可公开的文本示例放入 `examples/`。

创建目录：

```powershell
python ..\skill\wxyj-content-system\scripts\create_content_run.py `
  --root . `
  --date 2026-08-01 `
  --slug label-reading `
  --product "马克瑞普之选亚伯乐1996年单桶" `
  --platforms xiaohongshu
```
