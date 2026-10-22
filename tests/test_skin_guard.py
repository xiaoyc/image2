import unittest

from skin_guard import (
    REQUIRED_SENTENCE, RULE_ID, SkinConstraintError, evaluate_skin_constraint,
)


class SkinGuardTests(unittest.TestCase):
    def check(self, prose, **kwargs):
        return evaluate_skin_constraint(
            REQUIRED_SENTENCE + "; " + prose, "photoreal", True, **kwargs
        )

    def test_metadata_and_exact_sentence(self):
        result = self.check("A realistic portrait with natural facial skin.")
        self.assertEqual(result["rule_id"], RULE_ID)
        self.assertTrue(result["applicable"])
        self.assertTrue(result["exact_sentence_present"])
        self.assertEqual(result["recognized_conflicts"], [])
        self.assertIn("Finite", result["limitation"])

    def test_missing_sentence(self):
        for prompt in ("", "Keep natural texture and avoid over-retouching.",
                       "保留自然纹理,不过度磨皮"):
            with self.subTest(prompt=prompt), self.assertRaises(SkinConstraintError) as cm:
                evaluate_skin_constraint(prompt, "photoreal", True)
            self.assertFalse(cm.exception.metadata["exact_sentence_present"])

    def test_pre_render_mode_only_relaxes_sentence(self):
        result = evaluate_skin_constraint("Natural skin texture.", "photoreal", True, False)
        self.assertFalse(result["exact_sentence_present"])
        with self.assertRaises(SkinConstraintError):
            evaluate_skin_constraint("Give her poreless skin.", "photoreal", True, False)

    def test_positive_english_conflicts(self):
        requests = (
            "poreless skin", "airbrushed skin", "air-brushed facial skin",
            "flawless complexion", "plastic skin", "plastic-like human skin",
            "skin should be flawless", "make her skin poreless",
            "remove all skin texture", "erase every visible skin poreS",
            "eliminate facial pores", "no visible pores", "without any pores",
            "do not preserve natural skin texture", "never retain skin texture",
            "don’t preserve natural skin texture",
            "do not avoid plastic skin", "Not only plastic skin but dramatic light",
        )
        for request in requests:
            with self.subTest(request=request), self.assertRaises(SkinConstraintError) as cm:
                self.check(request)
            self.assertTrue(cm.exception.metadata["recognized_conflicts"])

    def test_positive_chinese_conflicts(self):
        for request in (
            "无毛孔皮肤", "零毛孔肌肤", "没有任何毛孔", "过度磨皮",
            "重度磨皮", "塑料皮肤", "塑料般的肌肤", "无瑕的皮肤",
            "去除所有皮肤纹理", "消除面部毛孔", "抹掉皮肤的自然纹理",
            "不保留皮肤纹理", "不要保留自然皮肤纹理", "不要避免塑料皮肤",
            "不要保留自然纹理，不过度磨皮",
        ):
            with self.subTest(request=request), self.assertRaises(SkinConstraintError):
                self.check(request)

    def test_english_negated_conflicts(self):
        for request in (
            "avoid plastic skin", "Do not use airbrushed skin",
            "no poreless skin", "not flawless skin", "never remove skin texture",
            "don't erase the facial pores", "without plastic skin",
            "Don’t use plastic skin", "shouldn’t remove skin texture",
            "avoid removing all skin texture", "avoid no visible pores",
            "Do not make her skin poreless", "avoid plastic skin and flawless skin",
            "Natural skin, not plastic skin.",
        ):
            with self.subTest(request=request):
                self.assertEqual(self.check(request)["recognized_conflicts"], [])

    def test_chinese_negated_conflicts(self):
        for request in (
            "不要塑料皮肤", "避免过度磨皮", "不应出现无毛孔皮肤",
            "不可去除所有皮肤纹理", "不要塑料皮肤或无毛孔皮肤",
            "保留自然纹理，不过度磨皮", "避免不保留皮肤纹理",
        ):
            with self.subTest(request=request):
                self.assertEqual(self.check(request)["recognized_conflicts"], [])

    def test_negation_does_not_leak_into_positive_clause(self):
        for request in (
            "avoid plastic skin, add poreless skin",
            "avoid plastic skin but make her skin flawless",
            "do not use plastic skin; remove skin texture",
            "不要塑料皮肤，但要无毛孔皮肤", "避免过度磨皮。去除皮肤纹理",
        ):
            with self.subTest(request=request), self.assertRaises(SkinConstraintError):
                self.check(request)

    def test_unrelated_and_age_appropriate_details(self):
        for request in (
            "flawless composition and natural skin", "plastic chairs",
            "airbrushed background with a naturally textured human face",
            "Smooth, youthful skin appropriate to the young child's age",
            "细嫩、符合儿童年龄的自然肌肤，不刻意添加皱纹",
            "无瑕的构图，保留年轻人自然细腻的皮肤",
        ):
            with self.subTest(request=request):
                self.check(request)

    def test_nonapplicable_scope(self):
        for medium, humans in (("non_photoreal", True), ("non_photoreal", False),
                               ("photoreal", False)):
            for prompt in ("Architecture without people.", "A plastic skin sculpture."):
                with self.subTest(medium=medium, humans=humans, prompt=prompt):
                    result = evaluate_skin_constraint(prompt, medium, humans)
                    self.assertFalse(result["applicable"])
                    self.assertFalse(result["exact_sentence_present"])
                    self.assertEqual(result["recognized_conflicts"], [])

    def test_invalid_types(self):
        for prompt in (None, 1, True, [], {}):
            with self.subTest(prompt=prompt), self.assertRaises(TypeError):
                evaluate_skin_constraint(prompt, "photoreal", True)
        for medium in (None, 1, True, [], {}):
            with self.subTest(medium=medium), self.assertRaises(TypeError):
                evaluate_skin_constraint("", medium, True)
        for value in (None, 0, 1, "true", [], {}):
            with self.subTest(visible_humans=value), self.assertRaises(TypeError):
                evaluate_skin_constraint("", "photoreal", value)
            with self.subTest(require_sentence=value), self.assertRaises(TypeError):
                evaluate_skin_constraint("", "photoreal", True, value)
        for medium in ("photo", "Photoreal", "photoreal ", "", "illustration"):
            with self.subTest(medium=medium), self.assertRaises(ValueError):
                evaluate_skin_constraint("", medium, True)


if __name__ == "__main__":
    unittest.main()
