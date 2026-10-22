# 桃霞云岫 · 使用入口

- [Skill](SKILL.md)：可复用的手工提示词风格层，规定桃粉、雾白、浅青的关系、自然肌理、可使用的空间与景别适配。
- [已接受基线](baseline/accepted-demo02.png) 与 [实际提示词](baseline/actual-prompt.txt)。
- [六张探索样片](examples/) 与 [逐图不足](QA.md)。六张并未逐张获得用户审美验收。
- [文件摘要](manifest.json) 与 [来源及许可边界](SOURCES-AND-LICENSE.md)。

先读基础 Skill，再按本次人物、动作、场所和景别手写新 prompt。复用风格关系，不机械复制基线人物、廊道、单一亭子或构图。此目录没有可直接交给 compose_prompt.py 的风格 JSON，也没有自动生图功能。

七张图均由手写 prompt 直接调用 native imagegen，一图一次。不是编译器产物；没有竞品图像输入。本次加入的离线检查是事后文本验证，不追认旧生成经过该程序。

从仓库根目录执行以下离线检查，不联网、不生成图片：

```sh
python3 -B -m unittest discover -v
python3 -B - <<'PYCODE'
from pathlib import Path
from base_constraints import check_skin
p = Path("styles/peachlight-cloud-valley/baseline/actual-prompt.txt")
print(check_skin(p.read_text(), {"rendering_medium": "photoreal", "visible_humans": True}))
PYCODE
```

新请求的约束、有限语义检测边界和适配器用法见[自然肤质说明](../../docs/natural-skin.md)。不把检查通过当作成片自然、画面稳定或用户批准。
