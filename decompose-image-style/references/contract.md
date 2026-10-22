# 与 Demo 共用的 style-brief-1 契约

必需顶层：schema_version="style-brief-1"、style_id、status、sources、claims、unresolved。intent="analysis_only"为本Skill附加的执行边界。

sources：id、kind(image/public_description/user/document)、locator、inspected。每个来源可另加completeness与dimensions；locator只能为可追溯附件名、公开URL或用户消息出处，不放凭据/签名下载URL。inspected是实际查看声明，不是自动像素验证。

claims：id、basis(description/visual_observation/inference/user)、source_ids、statement、evidence、relationship、scope(detail/near/medium/wide)、retain、vary、avoid。推断额外必须 uncertainty。可扩展domain、confidence、counterevidence、visible_check、conditions、excludes。

四种依据对应：公开描述→description，图像观察→visual_observation，推断→inference，用户要求→user。未知不伪造成claim，放unresolved/unknowns并保留null。

维度可通过domain标为scene/identity_wardrobe/space/lighting/palette/materials/visual_weight/action_mood。必须描述关系，例如暖中间调如何连接人物与木作，不是仅列灯、桌、人物。

规则接口直接使用retain/vary/avoid，分别表示必须保留的机制、可变内容、应避免的偏离。scope是适用景别；conditions/excludes进一步限制场景。不对特写强求全房空间，不对无人图强求肤质，不对单人图强求双人同尺度。

可选扩展：matrix(多图支持和例外)、preflight(草案检查)、unknowns、validation。下游当前完整性检查器不校验这些扩展的语义，不能称自动审美检测。

Demo消费者将每张图所有适用claim的ID，通过brief_mapping映射到实际prompt原文片段；拆解者不要替消费者捏造已执行映射。用户新增要求必须独立可追溯，不能静默改写原图观察。brief不授权生图或发布。
