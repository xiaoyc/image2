说明：本文件的“原图观察”栏是事前约定的核查目标，不代表已达到；实际结论见 OBSERVATIONS.md。

# 本张人工适用规则 → 字段 → 最终prompt → 原图观察

这是本张实际使用的人工映射，不是新增的自动门禁。基础与风格源码未改。生成后同ID追加观察，代码不判断语义或审美。

## silver.value
- 来源：公开description＋我方检查细化
- 字段：fixed.palette / light_signature
- 实际编译输出：assembled-prompt.txt 第11行，行摘要 b199778bf32bf52f0f4aa0d0868ed1e9c8f03281cb0592827c4be61725d043ee。
- 后检观察：脸/深发/墙暗部/浅衣的灰阶细节

## silver.reflectance
- 来源：公开description
- 字段：fixed.material_signature
- 实际编译输出：assembled-prompt.txt 第14行，行摘要 4d31bfbf010c26e0a1533e6c27b070571228f19c20730a6ed9328c1e767efafe。
- 后检观察：眼唇发亮带与肤/衣消光差异

## silver.casting
- 来源：用户反馈＋我方造型设计
- 字段：fixed.style_features＋input.subject/expression
- 实际编译输出：assembled-prompt.txt 第15行，行摘要 704cb13d1ec157775ff09769deee0a15b4901489ae29c25ea59f23ab97aab8a3。
- 后检观察：眼睑嘴角头颈肩共同表达克制，不代替用户判断

## frame.moment
- 来源：本次用户要求与意图卡
- 字段：input.action/expression
- 实际编译输出：assembled-prompt.txt 第8行，行摘要 8ea09b8dd8aa6b976e2c9c0d14eedc5135cde65f3b65940e7fee3e15bf69f750。
- 后检观察：身体侧向、头轻转、目光明确，不依照叙述冒称像素成立

## frame.crop
- 来源：本次事前构图决定
- 字段：input.composition
- 实际编译输出：assembled-prompt.txt 第10行，行摘要 5594097dd9b415b0062de0d760e97f01032f96a45ce89f56f58662eab731ffe0。
- 后检观察：允许少量发顶出画；五官下颌颈肩仍可读

## base.balance
- 来源：Photo Composition Critic独立转述＋项目规则
- 字段：base.quality_rules.composition＋input.composition
- 实际编译输出：assembled-prompt.txt 第16行，行摘要 85fc6c441c6371bce6ee7adfc161437bbd12723ba0a0d0dc853e25560938be4f。
- 后检观察：一组近景与目光留白，无强制配重

## base.visible_physics
- 来源：Photoreal相关维度＋项目可见性校准
- 字段：base.quality_rules.anatomy/physics/eyes
- 实际编译输出：assembled-prompt.txt 第21行，行摘要 a5e604884242e3ffef89f93f20e4ef18758da6650011d534b29fa2d8325d14d3。
- 后检观察：只检查可见颈肩眼睛，不伪称验证画外手脚

