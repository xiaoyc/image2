# 新请求的自然肤质约束

PHOTO-SKIN-001 仅适用于 rendering_medium=photoreal 且 visible_humans=true。必须逐字包含：保留自然纹理，不过度磨皮。不得把年龄自然的细腻皮肤误写成过度纹理或衰老。空镜和非写实媒介无需加入这句话，也不应为通过检查虚报范围。

## 实际实现和限制

skin_guard.py 检查原句及有限中英文冲突短语、近距离否定；base_constraints.py 校验不可被输入/风格替换的策略及其摘要；prepare_image_request.py 在新请求准备阶段及风格参考文字拼接后检查。它们都不调用模型、不看图片，也不能发现所有双重否定、隐喻、引语或远距离矛盾。实际图片仍须人工看图。

base.json、compose_prompt.py、旧实际 prompt 和旧 request 保持原字节。旧编译器不自动加本句；历史重放成功不等于符合新请求约束。旧请求缺少本句时会被新的准备器拒绝，不能为让测试通过而改写历史记录。

## 手写提示词

桃霞云岫样片是手写 prompt 直接生成，不是当前程序的历史执行结果。可用 base_constraints.check_skin(prompt, {"rendering_medium": "photoreal", "visible_humans": True}) 对完整新 prompt 做离线检查；检查不会更改文字。

## 为新的编译式请求准备输入

1. 在 build/current-input.json 创建本次新输入，不覆盖历史 input。在 subject 描述中包含上述原句，完成本次 before 审查并绑定新输入摘要。
2. 使用未改动的 compose_prompt.py 编译本次新输入。读完整输出，检查是否有相反肤质要求。
3. 使用显式范围准备请求：

```sh
python3 -B prepare_image_request.py --prompt build/current/assembled-prompt.txt --assembly-manifest build/current/assembly-manifest.json --rendering-medium photoreal --visible-humans yes --out build/current-text-request.json
```

如使用银灰或奶杏的原创风格参考，在同一条命令加 --mode style-reference 与对应 --manifest；风格/基础版本和 prompt SHA 必须与本次 assembly 一致。参考文字加完后仍会再次检查皮肤冲突。桃霞云岫本次未提供或验证风格参考适配器 manifest，不能声称七图为参考条件生成。

只准备 JSON，不执行生成。输出文件已存在会拒绝覆盖。实际调用前仍须读新请求并看选定原图；实际调用授权、返回图片与用户验收是不同阶段。
