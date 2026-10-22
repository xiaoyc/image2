# scene-03 人工规则映射

这是一帧的实际人工应用，不是新增程序化审美门禁。

## silver.tonal_neutrality
- 来源：公开风格description＋用户重点
- 最终prompt第11行，SHA256 b199778bf32bf52f0f4aa0d0868ed1e9c8f03281cb0592827c4be61725d043ee。
- 后检要求：明暗层次、暗发/暗墙/浅衣细节和无暖残色

## silver.reflection
- 来源：公开description
- 最终prompt第14行，SHA256 4d31bfbf010c26e0a1533e6c27b070571228f19c20730a6ed9328c1e767efafe。
- 后检要求：眼唇发局部反射与哑肤/浅衣差异，依景别可见性判断

## frame.casting
- 来源：用户短发清冷方向
- 最终prompt第6行，SHA256 0688836db380986e15992bb6adc4cfa502faa35cd5b7b81389cd660ff72083d6。
- 后检要求：年轻成年原创短发，非愤怒或惊讶，不锁身份

## frame.moment_support
- 来源：本张原创行动＋Photoreal人物意图
- 最终prompt第8行，SHA256 3d33a891c672067c8d121b613c65ee5e30305c238ab907cd0c9bfaa6b9e23b97。
- 后检要求：头到脚可见，检查脚底落地、髋膝踝自然方向、重心、书底承托和书脊接触；不让书或手悬浮。

## frame.gaze
- 来源：本张动作目标
- 最终prompt第9行，SHA256 1f04cc3c988586e7c5204414c5526e7a3bd27ddce6e518dd4404d27862981a96。
- 后检要求：目光与行动相连，眼睑安定、唇自然轻合

## frame.composition
- 来源：本张景别＋构图原则
- 最终prompt第10行，SHA256 d81a58b66b7f4b451298fb725e5c7a36e6e7267000d2a97210e063cc494f5886。
- 后检要求：脸的凝视→胸前薄册/手→身体轮廓与脚，再经书架/通道线回到主组。

## base.visual_groups
- 来源：Photo Composition Critic独立转述
- 最终prompt第16行，SHA256 85fc6c441c6371bce6ee7adfc161437bbd12723ba0a0d0dc853e25560938be4f。
- 后检要求：主组、主次和实际动线，不按道具存在自动判平衡

