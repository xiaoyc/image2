# 最小风格与输入契约

适用于发布版 0.3.3；前后审查字段契约沿用 0.3.1。

每套风格是一个 JSON 文件，仅维护差异，引用基础版本。不复制 quality_rules 或 review_methods。

## 风格

必填：id、name、version、base_version、source、fixed。source 至少包含 page_url 和 use，用于记录公开研究出处与使用边界；它不是生成图像输入。

fixed 恰好包含：

- palette：主辅色关系与饱和度倾向，不强定颜色必须属于某件衣服或道具。
- light_signature：有识别性的光质、明暗及色温关系，不固定某个具体场景。
- camera_signature：镜头气质、透视与清晰度倾向，不固定近景、中景、全身、截幅或主体大小。
- material_signature：独有材质呈现与触感倾向，不代替具体衣服和道具输入。
- style_features：可观察的特色与氛围，不写死位置、情节或动作。

可选 overrides 只覆盖基础 defaults 中的 medium 或 text，必须在 override_reasons 为每个覆盖写理由。不可覆盖基础质量规则。比例由本次输入指定，未指定使用基础默认。

现有风格名称是同一条目的标识，不意味着基础层可以携带该名称中的场景或服装限制。

## 单张创作输入

必填 subject、wardrobe、action、expression、environment、composition，可选 ratio。environment 包含 foreground、midground、background，均为非空文字；不需要某层装饰时写“无额外元素”。

composition 指定本次原生景别、机位、身体截幅、主体相对大小及视觉关系。action 指定主动作、真实接触及辅助落点。用视线、色彩、结构线或动作建立连接，不强制每张添加相同道具。

输入不接受任意 reference_image、image_paths 或风格覆盖字段。图像元数据与创作输入分开，三个模式互斥。

## identity_reference 元数据

--reference 接受且仅接受以下四个字段，引用一张图：

```json
{
  "source_kind": "our_generated_original",
  "source_file": "inputs/identity-reference-v2.png",
  "source_sha256": "完整的64位SHA256摘要",
  "provenance": "图像实际由何次我方原创生成或编辑产生，以及只用于身份参考的说明"
}
```

source_file 必须是包根目录内的相对文件路径，不接受外链、绝对路径或越界路径。CLI 检查本地文件字节；compose() 纯组装函数不读取图片，其 manifest 的 reference_bytes_verified 为 false。CLI 完成校验后才改为 true。

identity_reference 的继承与释放范围由编译器明确写入，不接受任意 preserve/change 扩成旧画面编辑。SHA256 验证的是文件一致性，不是作者归属证明；provenance 保留为来源声明。

## edit 与 generate

--edit 继续接受 source_kind、source_file、source_sha256、preserve、change，可选 provenance。编辑模式保留其 preserve/change 契约，不自动释放旧构图。旧版合法元数据仍可使用；本包执行时源图需位于本包内。

不传 --reference 或 --edit 时是 generate，input_images 为空。--reference 与 --edit 不可同时使用。

## 记录范围

assembled-prompt.txt 和 assembly-manifest.json 只证明文本组装及声明输入，不证明图像工具已运行。真正运行后独立保存实际调用提示词、参数、返回信息、输出文件及视觉检查。

结构测试不会完整识别自然语言矛盾，也不能评估图像美感、身份一致性或自动授予生成权限。

## 0.3.1 前后审查

当前 compose_prompt.py 必须收到 --review。该 JSON 按 references/review-methods.md 的九项契约，stage="before"，target 指向本次输入及 SHA256；任一 fail 阻止组装。--review 是设计声明的结构门槛，不是自动视觉评估或新生成授权。

工具返回后必须独立填写 stage="after" 的记录并绑定真实图片，逐项依据可见证据判断。后检失败仍可按用户要求标失败交付，不能自动重试。visual-review.json 的完整性与图像通过是两个不同判断。

本仓库的 0.3.2 参数快照仅用于历史 r3 回放，不应用旧参数绕过当前前检要求。

## 可复用动作设计补充（不增加JSON字段）
当本次目标为自然生活动作，填写input.action时用‘目的＋一个动作阶段＋抓握/接触与受力＋全身支撑连动’，expression写视线对象与颈肩放松，composition约束自然臂展与空间。空闲手可自然，不强行加物。证据分别进入before/after的pose_and_support、viewing_connections与proportions_and_position。后检把物理成立、阶段可读、自然程度分开写；具体书册/椅/站位只属于输入，不固化到基础或所有风格。详见[人物自然度](pose-naturalness.md)。
