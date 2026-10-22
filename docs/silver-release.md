# 银息柔映 · 银灰风格 0.2.0

基础版本仍为 0.3.3，银灰参数为 0.2.0。基础 JSON、原编译器与奶杏参数未改。用户已接受银灰 Skill 整体效果；本次发布遵循用户最新确认，保持公开仓库但移除根目录展示 README；这不追认每张图片的严格参数偏差，也不代表所有讨论中的自动机制都已实现。

## 内容入口
- [银灰 Skill](../styles/silver-window-v0.2/SKILL.md) 与 [唯一风格参数](../styles/silver-window-v0.2.json)。
- [六场景、逐图 QA 与已保留偏差](../runs/silver-six-scenes-20261022/README.md)。6 张为近景、中景、全身各两张，全部纯文本原创生成，无图像参考、无身份锁。
- [Demo01–04 历史精选](../runs/SILVER-HISTORY.md)：保留输入、实际提示词与当时观察，不覆盖失败。
- [原创风格参考与请求接线](style-references.md)：新增可选参考模式，尚未完成 reference-conditioned 图像实测。
- [来源及许可证边界](silver-sources.md) 与 [发布测试](silver-test-report.md)。

![银灰近景示例](../runs/silver-six-scenes-20261022/outputs/scene-01/original.png)
![银灰中景示例](../runs/silver-six-scenes-20261022/outputs/scene-04/original.png)

## 可运行的纯文本流程
```sh
python3 -B -m unittest discover -v
python3 -B compose_prompt.py --base base-image-production/base.json --style styles/silver-window-v0.2.json --input runs/silver-six-scenes-20261022/inputs/scene-01.json --review runs/silver-six-scenes-20261022/reviews/scene-01-before.json --out build/silver-preview
python3 -B prepare_image_request.py --prompt build/silver-preview/assembled-prompt.txt --out build/silver-text-request.json
```
Python 3.10+，仅标准库，无网络或付费 API 调用。最后一步只准备真实工具参数 JSON，不执行图像生成。prompt 与公开的历史纯文本调用可逐字节回放。

## 实际实现与待办
已实现：共享基础规则、独立银灰参数及选角表演进入最终文字；已有九项记录结构与摘要检查；本轮人工意图卡、规则到 prompt 行的映射和绑定原图摘要的视觉证据；新增可选风格参考请求参数适配器。

未实现：景别自动路由、视觉证据语义真实性门禁、input/base/style/compiler/actual prompt/image/review 全链组合版本的生成时自动门禁、历史审美误判的完整失败回归。这些不是做了几项 hash/标准库测试就已经落地。

图像返回、机械测试、实际视觉判断和用户接受是不同层次。六张中微小 RGB 通道余差，以及开书/合书、人物占比、杯高、步态阶段或嘴唇状态等偏差已保留。参考资产是风格关系示例，不是每项规格都完美的金标准；不以此自动批准新图。
