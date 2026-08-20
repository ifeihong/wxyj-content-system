# 电商资产生产系统

## 适用范围

用于商品缩略图、商品详情长图、店铺主图与活动落地页视觉；不直接复用小红书图文页或9:16视频封面。

## 运行包

创建电商资产时使用：

```powershell
python scripts/create_content_run.py --root outputs --date YYYY-MM-DD --slug <topic-slug> --product "“马克瑞普之选”单一单桶系列威士忌 - 亚伯乐1996" --platforms ecommerce
```

电商运行包必须填写 `ecommerce/publish.md`、`ecommerce/prompts.md` 与 `ecommerce-asset-qa.md`。

## 1:1 商品缩略图

- 原生正方形，建议 2000×2000 或更高；
- 商品是第一识别对象，主体建议占画面高度 55%–72%；
- 可使用一条不超过12字的主题文案，文字不得遮挡瓶盖、酒标、礼盒合页或瓶底；
- 先锁定酒瓶与礼盒比例，再设计背景与文字；
- 不使用低价促销海报、堆叠卖点、夸张爆炸贴或虚假紧迫感。

## 商品详情长图

建议以独立模块组织，而非把所有信息塞进一张海报：

1. 品牌与商品名；
2. 产品主视觉与30年时间锚点；
3. 核心规格：700毫升、51%、PX Sherry Hogshead、桶号261311；
4. 木质礼盒与内页故事；
5. 香气、口感、余味；
6. 适合的礼赠或品鉴判断。

每一模块仅承担一个信息任务。数值必须来自 `product-facts.md`，没有文件或库存核验时不得扩写为库存、稀缺性或投资承诺。

## 发布前验收

`release-manifest.json` 中的电商缩略图标记 `native_ratio: "1:1"`。通过产品几何、文字洁净度、事实、证据和媒体门槛后，才能设置 `release_status: "publish"`。
