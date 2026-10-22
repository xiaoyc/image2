import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).parents[1] / 'scripts/validate_demo.py'
spec = importlib.util.spec_from_file_location('demo', SCRIPT)
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class DemoTests(unittest.TestCase):
    """Synthetic records only. No real image inspection or user approval."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        template = Path(__file__).parents[1] / 'assets/plan.template.json'
        self.plan = json.loads(template.read_text())
        self.plan.update(id='offline-synthetic-six', style_id='test-style', authorization='Synthetic test fixture, no generation authorization')
        self.plan['bindings'] = {
            'base_skill':self.write('base.md', 'Synthetic base guide'),
            'style_skill':self.write('style.md', 'Synthetic style guide'),
            'skin_policy':self.write('policy.json', {'rules':[{'id':'PHOTO-SKIN-001','sentence':d.SKIN,'overridable':False,'when':{'rendering_medium':'photoreal','visible_humans':True}}]})}
        self.plan['protagonist']['style_fit'] = '年轻成年女子，表演与衣装按情境，不默认甜笑。'
        for i,s in enumerate(self.plan['scenes']):
            s.update(showcase='Text-only structural fixture', situation=f'Synthetic distinct situation {i}',
                     space='A connected floor and opening, hypothetical design only',
                     action_phase='A single paused action', wardrobe_identity_relation='Adult subject and clean maintained clothing appropriate to the declared role', reviewer='Synthetic test record, not actual review')
            s['design_checks'] = {k:{'status':'ready','evidence':'Synthetic field completeness fixture: '+k} for k in d.CHECKS}
            prompt=f'Synthetic scene {i}: light relates to face and fabric. {d.SKIN}'
            s['prompt'] = self.write(f'{i}.txt',prompt)
            s['request'] = self.write(f'{i}.json', {'prompt':prompt,'transparent_background':False})

    def write(self, name, value):
        p=self.root/name
        p.write_text(json.dumps(value,ensure_ascii=False) if not isinstance(value,str) else value)
        return {'path':name,'sha256':d.digest(p)}

    def check(self): return d.check_plan(self.plan,self.root)

    def row(self):
        s=self.plan['scenes'][0]
        image=self.write('synthetic-image.bin','Not an image; hash-binding test fixture only')
        return {'scene_id':s['id'],'status':'generated','calls':[{'started_at':'test-start','finished_at':'test-end','tool_result_receipt':'synthetic-receipt','actual_request_sha256':s['request']['sha256']}],
                'image':image,'qa':{'inspected':True,'image_sha256':image['sha256'],'reviewer':'Synthetic QA fixture, no visual result', 'actual_shot':'near','axes':{k:{'status':'uncertain','evidence':'Synthetic evidence field, not a real image judgment'} for k in d.AXES}},'user_acceptance':{'status':'pending'},'delivery':{'status':'pending'}}

    def run_check(self,row, delivered=False, seal=None):
        seal=seal or d.freeze(self.plan,self.root)
        return d.check_run(self.plan,seal,{'schema_version':'demo-run-1','plan_sha256':d.canonical(self.plan),'images':[row]},self.root,delivered)

    def test_valid_six_plan_and_freeze(self):
        self.assertEqual(self.check()['scenes'],6)
        self.assertFalse(d.freeze(self.plan,self.root)['structural_result']['visual_quality_proven'])

    def test_configurable_coverage_not_always_six(self):
        self.plan.update(total=1,max_calls=1,coverage={'near':1},scenes=self.plan['scenes'][:1])
        self.check()

    def test_wrong_coverage(self):
        self.plan['scenes'][5]['shot']='near'
        with self.assertRaises(d.Invalid): self.check()

    def test_duplicate_scene(self):
        self.plan['scenes'][1]['situation']=self.plan['scenes'][0]['situation']
        with self.assertRaises(d.Invalid): self.check()

    def test_pending_design(self):
        self.plan['scenes'][0]['design_checks']['space']['status']='pending'
        with self.assertRaises(d.Invalid): self.check()

    def test_empty_evidence(self):
        self.plan['scenes'][0]['design_checks']['space']['evidence']=''
        with self.assertRaises(d.Invalid): self.check()

    def test_no_prop_is_valid_but_incomplete_prop_is_not(self):
        self.check()
        self.plan['scenes'][0]['props']=[{'name':'vase','compositional_role':'left counterweight'}]
        with self.assertRaises(d.Invalid): self.check()

    def test_unrequested_change(self):
        self.plan['scenes'][0]['change_budget']['changed']=['wardrobe']
        with self.assertRaises(d.Invalid): self.check()

    def test_missing_exact_skin_in_final_request(self):
        s=self.plan['scenes'][0]
        s['prompt']=self.write('no-skin.txt','A portrait without required instruction')
        s['request']=self.write('no-skin.json',{'prompt':'A portrait without required instruction'})
        with self.assertRaises(d.Invalid): self.check()

    def test_no_human_supporting_scene_does_not_require_skin(self):
        s=self.plan['scenes'][0]
        s.update(role='supporting',protagonist_visible=False,scope={'rendering_medium':'photoreal','visible_humans':False})
        s['prompt']=self.write('architecture.txt','Architecture only')
        s['request']=self.write('architecture.json',{'prompt':'Architecture only'})
        self.check()

    def test_prompt_and_request_must_match(self):
        self.plan['scenes'][0]['request']=self.write('other-request.json',{'prompt':'changed'})
        with self.assertRaises(d.Invalid): self.check()

    def test_stale_file_hash(self):
        (self.root/'style.md').write_text('changed style')
        with self.assertRaises(d.Invalid): self.check()

    def test_young_adult_woman_not_child_or_male(self):
        for field,value in [('adult',False),('gender','man'),('life_stage','child')]:
            original=copy.deepcopy(self.plan['protagonist'])
            self.plan['protagonist'][field]=value
            with self.assertRaises(d.Invalid): self.check()
            self.plan['protagonist']=original

    def test_identity_not_guaranteed(self):
        self.plan['identity']['guaranteed']=True
        with self.assertRaises(d.Invalid): self.check()

    def test_competitor_input_rejected(self):
        self.plan['references']=[{'id':'r','role':'style_reference','source':'public reference','input':True,'origin':'competitor'}]
        with self.assertRaises(d.Invalid): self.check()

    def test_unbound_image_reference_rejected(self):
        s=self.plan['scenes'][0]; prompt=(self.root/s['prompt']['path']).read_text()
        s['request']=self.write('badref.json',{'prompt':prompt,'referenced_image_paths':['not-in-manifest.png']})
        with self.assertRaises(d.Invalid): self.check()

    def test_style_brief_maps_actual_prompt_and_scope(self):
        brief={'schema_version':'style-brief-1','style_id':'test-style','sources':[{'id':'u','kind':'user','locator':'synthetic user fixture'}],
               'claims':[{'id':'c','basis':'user','source_ids':['u'],'scope':['near'],'statement':'synthetic requirement','evidence':'synthetic user fixture','relationship':'light and face','retain':'relation','vary':'scene','avoid':'equal gloss'}]}
        self.plan['bindings']['style_brief']=self.write('brief.json',brief)
        self.plan['scenes'][0]['brief_mapping']={'c':'light relates to face and fabric'}
        self.check()
        self.plan['scenes'][0]['brief_mapping']={}
        with self.assertRaises(d.Invalid): self.check()

    def test_unseen_visual_claim_rejected(self):
        brief={'schema_version':'style-brief-1','sources':[{'id':'i','kind':'image','locator':'synthetic image fixture','inspected':False}],
               'claims':[{'id':'c','basis':'visual_observation','source_ids':['i'],'scope':['near'],'statement':'x','evidence':'x','relationship':'x','retain':'x','vary':'x','avoid':'x'}]}
        with self.assertRaises(d.Invalid): d.check_brief(brief)

    def test_compiled_claim_requires_manifest(self):
        self.plan['scenes'][0]['prompt_pipeline']='compiled'
        with self.assertRaises((d.Invalid,KeyError)): self.check()

    def test_partial_run_not_fake_completion(self):
        r=self.run_check(self.row())
        self.assertEqual(r['recorded_calls'],1)
        self.assertFalse(r['visual_quality_proven'])

    def test_extra_retry_rejected(self):
        r=self.row();r['calls']*=2
        with self.assertRaises(d.Invalid): self.run_check(r)

    def test_qa_requires_matching_original(self):
        r=self.row();r['qa']['image_sha256']='wrong'
        with self.assertRaises(d.Invalid): self.run_check(r)

    def test_shot_mismatch_cannot_pass_brief(self):
        r=self.row();r['qa']['actual_shot']='medium';r['qa']['axes']['brief']['status']='pass'
        with self.assertRaises(d.Invalid): self.run_check(r)

    def test_comparison_must_match_actual_shot(self):
        r=self.row();r['qa']['comparisons']=[{'reference':'test source','shot':'wide','comparable':True}]
        with self.assertRaises(d.Invalid): self.run_check(r)

    def test_acceptance_needs_user_evidence(self):
        r=self.row();r['user_acceptance']['status']='accepted'
        with self.assertRaises(d.Invalid): self.run_check(r)

    def test_upload_is_not_delivery(self):
        r=self.row();r['delivery']={'status':'sent','library_file_id':'test-file'}
        with self.assertRaises(d.Invalid): self.run_check(r,True)

    def test_pending_delivery_does_not_pass_final_delivery_check(self):
        with self.assertRaises(d.Invalid): self.run_check(self.row(),True)

    def test_plan_mutation_after_freeze(self):
        seal=d.freeze(self.plan,self.root)
        self.plan['scenes'][0]['showcase']='changed description'
        with self.assertRaises(d.Invalid): self.run_check(self.row(),seal=seal)

    def test_final_empty_or_unstarted_run_rejected(self):
        seal=d.freeze(self.plan,self.root)
        for rows in [[],[{'scene_id':s['id'],'status':'not_started','calls':[]} for s in self.plan['scenes']]]:
            with self.assertRaises(d.Invalid):
                d.check_run(self.plan,seal,{'schema_version':'demo-run-1','plan_sha256':d.canonical(self.plan),'images':rows},self.root,True)

    def test_source_without_locator_rejected(self):
        brief={'schema_version':'style-brief-1','sources':[{'id':'i','kind':'image','inspected':True}],
               'claims':[{'id':'c','basis':'visual_observation','source_ids':['i'],'scope':['near'],'statement':'x','evidence':'x','relationship':'x','retain':'x','vary':'x','avoid':'x'}]}
        with self.assertRaises(d.Invalid):d.check_brief(brief)

    def test_actual_skin_conflict_rejected_despite_required_sentence(self):
        for bad in ['要求人物皮肤无毛孔','airbrushed skin','remove all skin texture']:
            s=self.plan['scenes'][0]
            prompt=d.SKIN+'。'+bad
            s['prompt']=self.write('conflict.txt',prompt)
            s['request']=self.write('conflict.json',{'prompt':prompt})
            with self.assertRaises(d.Invalid):self.check()

    def test_avoid_plastic_and_natural_young_skin_allowed(self):
        s=self.plan['scenes'][0]
        prompt=d.SKIN+'。避免塑料皮肤。自然年轻肤面，不夸张毛孔。'
        s['prompt']=self.write('allowed.txt',prompt)
        s['request']=self.write('allowed.json',{'prompt':prompt})
        self.check()

    def test_skin_policy_scope_cannot_be_weakened(self):
        self.plan['bindings']['skin_policy']=self.write('bad-policy.json',{'rules':[{'id':'PHOTO-SKIN-001','sentence':d.SKIN,'overridable':False,'when':{'visible_humans':False}}]})
        with self.assertRaises(d.Invalid):self.check()

    def test_guard_hash_bound_to_freeze(self):
        seal=d.freeze(self.plan,self.root);seal['skin_guard_sha256']='bad'
        with self.assertRaises(d.Invalid):self.run_check(self.row(),seal=seal)

    def test_final_complete_generated_and_failure_disclosure(self):
        self.plan.update(total=1,max_calls=1,coverage={'near':1},scenes=self.plan['scenes'][:1])
        r=self.row();r['delivery']={'status':'sent','receipt':'synthetic-delivery','library_file_id':'synthetic-file'}
        self.run_check(r,True)
        r.update(status='generation_failed',failure='Synthetic execution failure');r.pop('image');r.pop('qa')
        r['delivery']={'status':'pending'}
        with self.assertRaises(d.Invalid):self.run_check(r,True)
        r['delivery']={'status':'sent','receipt':'synthetic-failure-disclosure'}
        self.run_check(r,True)


if __name__ == '__main__': unittest.main()
