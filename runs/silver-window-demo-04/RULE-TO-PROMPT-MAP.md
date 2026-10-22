说明：本文件的“原图观察”栏是事前约定的核查目标，不代表已达到；实际结论见 OBSERVATIONS.md。

# Demo04 人工规则→字段→实际prompt→原图观察

本张人工应用，不代表完整新程序化门禁已实现。基底0.3.3和银灰0.2参数不改；改的是本帧输入。

## silver.neutral_value
- 来源：公开description＋用户强调＋上张残色纠偏
- 字段：fixed.palette / light_signature＋input.composition
- 实际输出：assembled-prompt.txt第11行，SHA256 b199778bf32bf52f0f4aa0d0868ed1e9c8f03281cb0592827c4be61725d043ee。
- 实际输出：assembled-prompt.txt第12行，SHA256 d0f06aeaab4415f9afe0b711b2ceb88caf551ceda608f348f8b71c756a8306d5。
- 实际输出：assembled-prompt.txt第10行，SHA256 2563d760e4db8d3853fc465f79b8d87d8fa4860d2e5ae49bb4b0fee5e6bd6f2a。
- 原图观察：肤/唇无暖色，脸/发/暗墙/浅衣灰阶细节

## silver.reflectance
- 来源：公开description＋用户强调
- 字段：fixed.material_signature
- 实际输出：assembled-prompt.txt第14行，SHA256 4d31bfbf010c26e0a1533e6c27b070571228f19c20730a6ed9328c1e767efafe。
- 原图观察：眼唇发局部反射与哑衣差异

## silver.short_casting
- 来源：本次用户短发清冷方向＋我方设计
- 字段：input.subject/wardrobe
- 实际输出：assembled-prompt.txt第6行，SHA256 ef3b4db2b6781deb5b059e415702cd2e0c543b3ad26e0631d34704e282ebccd7。
- 实际输出：assembled-prompt.txt第7行，SHA256 48c3ca645cd6fdf8375b7bab9ec43c28c0ed5ccd136ac432cc7de85ed0a075ff。
- 原图观察：原创成年、侧分齐耳短发、哑浅衣，不按长相断性格

## frame.performance
- 来源：本次用户确认方向＋上一张表演偏差
- 字段：input.action/expression
- 实际输出：assembled-prompt.txt第8行，SHA256 210959101bb562d759c48bd6c4db510b2f42210149eda231876d81165c783c8d。
- 实际输出：assembled-prompt.txt第9行，SHA256 630084eff083f4afbcdfcfd4dc0d57ad5370b55546ece38ce83fdcb988fbc386。
- 原图观察：平视、不上看圆睁、嘴轻合、微收下巴、肩颈放松

## frame.crop
- 来源：本次事前裁切边界
- 字段：input.composition
- 实际输出：assembled-prompt.txt第10行，SHA256 2563d760e4db8d3853fc465f79b8d87d8fa4860d2e5ae49bb4b0fee5e6bd6f2a。
- 原图观察：允许发冠出框，不能裁额头皮肤/五官/下颌，颈肩可读

## base.balance
- 来源：Photo Composition Critic独立转述＋我方条件化
- 字段：base.quality_rules.composition
- 实际输出：assembled-prompt.txt第16行，SHA256 85fc6c441c6371bce6ee7adfc161437bbd12723ba0a0d0dc853e25560938be4f。
- 原图观察：单一近景组、头肩方向，非强制配重

## base.visible_physics
- 来源：Photoreal相关维度＋我方可见性规则
- 字段：base.quality_rules.anatomy/eyes
- 实际输出：assembled-prompt.txt第21行，SHA256 a5e604884242e3ffef89f93f20e4ef18758da6650011d534b29fa2d8325d14d3。
- 实际输出：assembled-prompt.txt第22行，SHA256 881f6a31cf140279b65331b55d1a8541f81ffc464c02423248663a139fabb555。
- 原图观察：可见头颈眼睛，不冒称验证画外手脚

