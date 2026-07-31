# 参与贡献

欢迎改进平台适配、目录工具、校验规则、提示词方法和文档。

## 提交前

1. 保持 Skill ID 为 `wxyj-content-system`；
2. 不提交真实报关、授权、客户、库存或销售敏感文件；
3. 不提交无授权的产品图片、字体、音乐或视频；
4. 新增确定性行为时先添加失败测试；
5. 修改输出契约时同步更新 README、docs、CHANGELOG 和版本号；
6. 不加入保证爆款、绝对品质、金融收益或虚假紧迫表达。

## 验证

```powershell
python -m unittest discover -s tests -v
python C:\Users\<用户名>\.codex\skills\.system\skill-creator\scripts\quick_validate.py .
python scripts\validate_product_assets.py
```

## 版本

- 修正文案、事实或小型校验规则：PATCH；
- 新增兼容模块、平台或脚本：MINOR；
- 修改 Skill ID、目录或交付契约：MAJOR。

## Pull Request 内容

说明：

- 改了什么；
- 为什么需要；
- 哪个测试先失败；
- 运行了哪些验证；
- 是否影响输出目录或发布文案契约。
