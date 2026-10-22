# 我方原创风格参考

## 三种角色不可混用
- demo：历史输出示例，默认不成为后续图像输入。
- style_reference：经选取的我方原创风格图，只有显式启用时才作为图像输入。仅借鉴光、色、明暗、材质和气质关系。
- identity_reference：继承人物身份的另一模式。风格参考不继承脸型、五官或身份，不能冒充身份锁。

新增 [prepare_image_request.py](../prepare_image_request.py) 只准备 imagegen 的真实参数，不调用 API，不生图。默认 text 模式只输出 prompt 与 transparent_background:false。显式 style-reference 才读取受控 manifest，检查角色、原创声明、PNG、包内路径和 SHA256，并将清单的风格id/版本/基础版本与本次assembly manifest及prompt摘要绑定，并输出 referenced_image_paths。SHA 只证明字节一致，不能独立证明作者或许可。

## 两套独立清单
- [银灰清单](../styles/silver-window-v0.2/references.json)：scene-01 原生上胸近景、scene-04 原生侧坐中景；直接复用本仓库原图，不重复二进制。只借鉴银灰体积、柔侧前窗光、局部亮泽/消光差异与克制气质。
- [奶杏清单](../styles/apricot-colonnade/references.json)：已接受六场景试验的书店膝上中景与温室完整坐姿环境景；不使用已否决的001/002。只借鉴奶杏灰绿关系、暖侧逆发缘、软脸光和针织材质。没有原生特写参考，不裁切冒充特写。

两套都不锁人物、旧衣服、场景布局、道具或动作。参考图中的书店、温室、茶杯不是以后必选的场景或物件。具体局限保留于 manifest，用户整体接受不代表每张完全满足全部输入。

## 新请求迁移

旧编译器和历史实际请求不改。新的请求须按[自然肤质约束](natural-skin.md)制作包含原句的本次输入及对应 before 记录，再编译到 build/current；适配器现在要求显式范围。下列参考命令针对这个新的 assembly，不是旧图历史请求的重放。

## 显式银灰参考请求
先按上述迁移说明编译新的银灰输入，再运行：
```sh
python3 -B prepare_image_request.py --prompt build/current/assembled-prompt.txt --rendering-medium photoreal --visible-humans yes --mode style-reference --assembly-manifest build/current/assembly-manifest.json --manifest styles/silver-window-v0.2/references.json --reference-id close-museum --reference-id medium-tea --out build/silver-style-reference-request.json
```
可省略 reference-id 使用清单全部图，或只选需要的图。输出的是适配器运行机器上的已验证本地路径；不得把旧机器上的请求 JSON 直接搬到另一执行环境。应在真正消费图片的环境重新准备，并实际查看所选图片。

适配器仅在新的准备请求中替换“没有参考图”开头，加上风格继承范围和身份/构图释放要求。它不修改任何历史 actual-tool-request.json 或实际 prompt。既有 edit 与 identity_reference 提示词不能被它悄悄改解释成风格参考。

## 实测边界
参考清单与请求结构测试已实现；两套 reference-conditioned 图像效果均尚未实测。本次银灰六张仍是纯文本结果，不能改写成有参考图的验证。风格参考可能有助于传达视觉关系，但不保证更准确，也可能把人物或布局带入，需要另行获准后做同输入对照并看图判断。

## 奶杏请求准备示例
下面只复用已接受六场景实验的书店文字输入，before 的目标路径已为本仓库重新定位，输入字节保持不变；不是新生图记录。命令从仓库根目录运行：
```sh
python3 -B compose_prompt.py --base base-image-production/base.json --style styles/apricot-colonnade.json --input examples/request-preparation/apricot-input.json --review examples/request-preparation/apricot-before.json --out build/apricot-reference-preview
# 上一条仅历史重放；另按迁移说明准备本次含原句的新输入并编译到 build/current 后：
python3 -B prepare_image_request.py --prompt build/current/assembled-prompt.txt --rendering-medium photoreal --visible-humans yes --mode style-reference --assembly-manifest build/current/assembly-manifest.json --manifest styles/apricot-colonnade/references.json --out build/apricot-style-reference-request.json
```
两套都必须显式提供对应assembly manifest，不从prompt猜风格。银灰prompt不能误接奶杏清单。适配器还拒绝覆盖任何已有输出文件，以免误写历史实际请求；再次准备请使用新的输出文件名。

此绑定仅覆盖请求准备的结构和字节，仍不是完整的视觉证据语义或生成全链门禁。历史纯文本请求不变，真正调用前仍须实际看所选原图并确认新请求符合本次任务。
