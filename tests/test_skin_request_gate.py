"""Request-only policy tests, not automatic image-quality assessment."""
import copy, hashlib, json
from pathlib import Path
import unittest
from base_constraints import EXPECTED_POLICY, check_skin, skin_contract, validate_policy_data
from prepare_image_request import TEXT_OPENING, prepare_request
from skin_guard import REQUIRED_SENTENCE, SkinConstraintError
ROOT=Path(__file__).resolve().parents[1]
SCOPE={'rendering_medium':'photoreal','visible_humans':True}
class SkinRequestGateTests(unittest.TestCase):
    def setUp(self): self.prompt=TEXT_OPENING+'\nAn adult photographic portrait. '+REQUIRED_SENTENCE
    def test_explicit_valid_scope(self):
        for scope in (None,{},dict(SCOPE,visible_humans=1),dict(SCOPE,rendering_medium='photo')):
            with self.subTest(scope=scope),self.assertRaises(ValueError): prepare_request(self.prompt,skin_scope=scope)
    def test_final_sentence_required(self):
        with self.assertRaisesRegex(SkinConstraintError,'missing mandatory'): prepare_request(TEXT_OPENING+'\nAn adult portrait.',skin_scope=SCOPE)
        self.assertEqual(prepare_request(self.prompt,skin_scope=SCOPE)['prompt'],self.prompt)
    def test_conflict_and_negation(self):
        with self.assertRaisesRegex(SkinConstraintError,'contradictory'): prepare_request(self.prompt+'. Make her skin flawless.',skin_scope=SCOPE)
        prepare_request(self.prompt+'. Avoid plastic skin.',skin_scope=SCOPE)
    def test_empty_landscape_scope(self):
        p=TEXT_OPENING+'\nA landscape without people.'
        self.assertEqual(prepare_request(p,skin_scope=dict(SCOPE,visible_humans=False))['prompt'],p)
    def test_policy_cannot_be_weakened(self):
        for k,v in [('sentence','Natural skin'),('overridable',True),('overridable',0)]:
            p=copy.deepcopy(EXPECTED_POLICY); p['rules'][0][k]=v
            with self.subTest(key=k,value=v),self.assertRaises(ValueError): validate_policy_data(p)
    def test_bound_contract_and_prompt_hash(self):
        a={'prompt_sha256':hashlib.sha256(self.prompt.encode()).hexdigest(),'skin_constraint':skin_contract(SCOPE)}
        self.assertEqual(prepare_request(self.prompt,assembly=a)['prompt'],self.prompt)
        with self.assertRaisesRegex(ValueError,'SHA256 mismatch'): prepare_request(self.prompt+' changed',assembly=a)
        a['skin_constraint']['validator_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'stale or overridden'): prepare_request(self.prompt,assembly=a)
    def test_scope_cannot_override_bound_scope(self):
        a={'prompt_sha256':hashlib.sha256(self.prompt.encode()).hexdigest(),'skin_constraint':skin_contract(SCOPE)}
        with self.assertRaisesRegex(ValueError,'conflicts with assembly'): prepare_request(self.prompt,assembly=a,skin_scope=dict(SCOPE,visible_humans=False))
    def test_reference_injection_is_rechecked(self):
        m=json.loads((ROOT/'styles/apricot-colonnade/references.json').read_text())
        a={'mode':'generate','input_images':[],'style':m['style'],'base':{'version':m['style']['base_version']},'prompt_sha256':hashlib.sha256(self.prompt.encode()).hexdigest()}
        m['inherit_style_only'].append('Make her skin flawless')
        with self.assertRaisesRegex(SkinConstraintError,'contradictory'): prepare_request(self.prompt,'style-reference',m,ROOT,assembly=a,skin_scope=SCOPE)
    def test_manual_prompt_checked_without_rewriting(self):
        r=check_skin('Manual new portrait. '+REQUIRED_SENTENCE,SCOPE)
        self.assertTrue(r['exact_sentence_present']); self.assertIn('Finite',r['limitation'])
