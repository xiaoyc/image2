# 记录契约

计划与运行分开。所有文件绑定为 `{"path":"项目根内相对路径","sha256":"真实文件摘要"}`。`--root` 是明确的项目根，文件不能越界；移动项目后保留相对目录。脚本仅用 Python 标准库。

## demo-plan-1

- `id`、`style_id`、`authorization`：本组标识、真实用户请求的消息或描述。检查非空不代表授权已核验。
- `total`、`max_calls`：本模板每图一次；新增重试用独立授权计划。`coverage` 可配置 detail/near/medium/wide 数量，总和一致。
- `bindings`：base_skill、style_skill、skin_policy 必填；可追加 style_brief 或其他已实际读取指南。全部文件摘要参与检查。
- `protagonist`：当前用户要求 gender=woman、adult=true、life_stage=young_adult，并写 style_fit；这是声明检查，最终 prompt 仍需读卡确认，原图仍需实际看。
- `identity`：not_locked 或 identity_reference、描述与 guaranteed=false。文本重复和风格参考不保证同一张脸。
- `references`：区分 style_reference、identity_reference、research_only；来源、是否输入、权限证据、实际查看声明以及输入文件摘要。空列表表示纯文本；全组默认相同条件，若要分条件实验则另建计划。
- `scenes`：唯一ID、景别、hero/supporting、展示重点、具体情境/空间/动作阶段/身份衣着关系。八域设计审查为 style、framing、space、casting_wardrobe、props_coherence、action_support、light_material、change_budget，各写 ready/not_applicable 及具体依据。pending/revise 不得冻结。
- `props` 可为空；有物件时分别填写功能、必要性/已有替代、材料年代身份、尺度摆放及火水条件、构图作用。物件合理不意味着构图已经成立。
- `change_budget`：new/revision；requested、changed、preserve 为变量名列表。changed 不得超出 requested；revision 另绑定原始基线，不覆盖旧文件。脚本只核声明，不识别暗中改变的语义。
- `prompt` 与 `request` 分别绑定实际最终文本和要发送的工具 kwargs JSON。二者的 prompt 必须逐字相等。引用图与清单必须一致。写实可见人物精确皮肤原句不能丢；随包复用的基础检查器直接检查有限的已识别磨皮冲突。
- `prompt_pipeline`：manual/compiled 如实标；compiled 必须绑定真实 compiler_manifest。脚本仅核该文件摘要，不能自行证明它真的来自某次编译。`protagonist_visible` 与可见人物 scope 不能矛盾，不露主角的图为 supporting。
- `brief_mapping`：本张适用的每个 brief claim ID → 实际 prompt 中的片段；不得遗漏、虚构或套入不适用项。无结构化 brief 时为空，使用已有风格正文及真实读卡审查。

`freeze` 绑定计划规范化 JSON、所有被引用文件摘要，以及当前校验器和随包基础皮肤检查器源码摘要。改输入或代码必须重新检查，不能复用旧冻结记录。

## demo-run-1

记录 plan_sha256、images。允许尚未开始的图片，以便逐张交付，不需要等整组。

- 状态 not_started/generated/generation_failed；实际执行必须有一条 call：开始/结束时间、真实工具回执、actual_request_sha256。失败写原因，不造图和 QA。
- generated 绑定原图文件、实际看图人/模型、原图摘要、实际景别及 composition/style/brief/natural_physics 四轴，每轴 pass/fail/uncertain/not_applicable 加可见证据。planned wide 实际只是全身环境人像时，不能把 brief 标通过。
- comparisons 按实际景别对照；不匹配可保存，但标不可直接比较并说明差异。
- user_acceptance 仅 pending/accepted/rejected；后两者必须保留真实用户消息依据，不因主观 QA 通过而自动批准。
- delivery 仅 pending/sent/failed；sent 需原生 Library ID 和真实发送回执。上传成功不等于已给用户发送。

整组最终检查使用 `--require-delivered`：所有计划图片均须记录终态。生成失败无需伪造 Library ID，但必须有实际告知用户的发送回执。普通 run 支持部分结果，不能据此宣称整组完成。

## 已知边界

本工具不看图，不对人脸、比例或构图打分。`inspected:true` 和 evidence 字段仍是执行者声明，不能防范伪造。命中字符串不代表含义完整；不同文字不证明情境真正不同；源摘要只证明内容一致，不证明来源结论可靠。对画面与授权仍须真实判断，不新增无意义循环评审。
