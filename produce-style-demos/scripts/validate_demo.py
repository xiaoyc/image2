#!/usr/bin/env python3
"""Offline record checks, not image aesthetics or permission verification.

No image tool, network call, external executable, or imported project code.
"""
import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path

SHOTS = {'detail', 'near', 'medium', 'wide'}
SKIN = '保留自然纹理，不过度磨皮'
CHECKS = {'style', 'framing', 'space', 'casting_wardrobe', 'props_coherence',
          'action_support', 'light_material', 'change_budget'}
AXES = {'composition', 'style', 'brief', 'natural_physics'}
GUARD_PATH = Path(__file__).with_name('skin_guard.py')
_spec = importlib.util.spec_from_file_location('demo_bundled_skin_guard', GUARD_PATH)
_guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_guard)


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def words(value, name):
    require(isinstance(value, str) and bool(value.strip()), name + ' must contain specific text')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def bound(record, root):
    require(isinstance(record, dict), 'file binding must be an object')
    words(record.get('path'), 'file path')
    path = (root / record['path']).resolve()
    require(path.is_relative_to(root.resolve()), 'binding must remain inside --root')
    require(path.is_file(), 'missing bound file: ' + record['path'])
    require(record.get('sha256') == digest(path), 'stale or missing SHA256: ' + record['path'])
    return path


def check_brief(brief):
    require(brief.get('schema_version') == 'style-brief-1', 'unknown style brief schema')
    sources = brief.get('sources', [])
    require(isinstance(sources, list), 'brief sources must be a list')
    for source in sources:
        words(source.get('id'), 'brief source ID')
        words(source.get('locator'), 'traceable brief source locator')
        require(source.get('kind') in {'image', 'public_description', 'user', 'document'}, 'source kind required')
    by_id = {s['id']: s for s in sources}
    require(len(by_id) == len(sources), 'duplicate brief source IDs')
    claims = brief.get('claims', [])
    require(isinstance(claims, list) and claims, 'brief needs claims, not just an object inventory')
    ids = set()
    for c in claims:
        words(c.get('id'), 'claim ID')
        require(c['id'] not in ids, 'duplicate claim ID')
        ids.add(c['id'])
        require(c.get('basis') in {'description', 'visual_observation', 'inference', 'user'}, 'claim basis required')
        require(c.get('scope') and set(c['scope']) <= SHOTS, 'claim shot scope required')
        require(c.get('source_ids') and set(c['source_ids']) <= set(by_id), 'claim needs valid sources')
        for key in ('statement', 'evidence', 'relationship', 'retain', 'vary', 'avoid'):
            words(c.get(key), 'claim ' + key)
        if c['basis'] == 'visual_observation':
            require(any(by_id[s].get('kind') == 'image' and by_id[s].get('inspected') is True
                        for s in c['source_ids']), 'visual claim needs an inspected image declaration')
        if c['basis'] == 'description':
            require(any(by_id[s].get('kind') == 'public_description' and by_id[s].get('inspected') is True
                        for s in c['source_ids']), 'description claim needs a read description declaration')
        if c['basis'] == 'inference':
            words(c.get('uncertainty'), 'inference uncertainty')
    return claims


def check_plan(plan, root):
    require(plan.get('schema_version') == 'demo-plan-1', 'unknown plan schema')
    words(plan.get('id'), 'plan ID')
    words(plan.get('style_id'), 'style ID')
    words(plan.get('authorization'), 'bounded request reference')
    n = plan.get('total')
    require(type(n) is int and n > 0, 'positive integer total required')
    require(type(plan.get('max_calls')) is int and plan['max_calls'] == n,
            'this entry allows one call per planned image; retries require a new authorized plan')
    coverage = plan.get('coverage', {})
    require(isinstance(coverage, dict) and set(coverage) <= SHOTS and coverage,
            'coverage uses detail/near/medium/wide')
    require(all(type(v) is int and v >= 0 for v in coverage.values()) and sum(coverage.values()) == n,
            'coverage counts must total the requested number')
    bindings = plan.get('bindings', {})
    require({'base_skill', 'style_skill', 'skin_policy'} <= set(bindings), 'base, style and skin policy bindings required')
    for binding in bindings.values():
        bound(binding, root)
    policy = json.loads(bound(bindings['skin_policy'], root).read_text())
    rule = next((r for r in policy.get('rules', []) if r.get('id') == 'PHOTO-SKIN-001'), {})
    require(rule.get('sentence') == SKIN and rule.get('overridable') is False,
            'base natural-skin policy must not be weakened')
    require(rule.get('when') == {'rendering_medium':'photoreal','visible_humans':True},
            'base natural-skin policy applicability must not be weakened')
    identity = plan.get('identity', {})
    require(identity.get('mode') in {'not_locked', 'identity_reference'}, 'explicit identity mode required')
    words(identity.get('description'), 'identity description and limits')
    require(identity.get('guaranteed') is False, 'identity continuity cannot be guaranteed by this validator')
    protagonist = plan.get('protagonist', {})
    require(protagonist.get('gender') == 'woman' and protagonist.get('adult') is True
            and protagonist.get('life_stage') == 'young_adult',
            'current user Demo rule: protagonist must be a young adult woman')
    words(protagonist.get('style_fit'), 'style-appropriate protagonist temperament, wardrobe and action')
    refs = plan.get('references', [])
    require(isinstance(refs, list), 'references must be a list')
    ref_ids = set()
    for r in refs:
        words(r.get('id'), 'reference ID')
        require(r['id'] not in ref_ids, 'duplicate reference ID')
        ref_ids.add(r['id'])
        require(r.get('role') in {'style_reference', 'identity_reference', 'research_only'}, 'reference role required')
        words(r.get('source'), 'reference provenance')
        require(type(r.get('input')) is bool, 'reference input flag required')
        if r['input']:
            require(r.get('origin') != 'competitor' and r['role'] != 'research_only',
                    'competitor/research-only images cannot be generation inputs')
            require(r.get('permission') == 'approved', 'input reference needs an explicit approved-use record')
            words(r.get('approval_evidence'), 'reference permission evidence')
            require(r.get('inspected') is True, 'inspect actual input reference before preparing a request')
            bound(r['file'], root)
    require(identity['mode'] != 'identity_reference' or any(r['input'] and r['role'] == 'identity_reference' for r in refs),
            'identity-reference mode requires an actual identity input')
    if identity['mode'] == 'not_locked':
        require(not any(r['input'] and r['role'] == 'identity_reference' for r in refs),
                'identity input and declared identity mode disagree')
    claims = []
    if 'style_brief' in bindings:
        brief = json.loads(bound(bindings['style_brief'], root).read_text())
        require(brief.get('style_id') == plan['style_id'], 'style brief belongs to a different style')
        claims = check_brief(brief)
    scenes = plan.get('scenes', [])
    require(isinstance(scenes, list) and len(scenes) == n, 'scene count mismatch')
    require(len({s['id'] for s in scenes}) == n, 'duplicate scene ID')
    require(collections.Counter(s['shot'] for s in scenes) == collections.Counter({k:v for k,v in coverage.items() if v}),
            'planned shot coverage mismatch')
    require(len({s['situation'].strip() for s in scenes}) == n, 'scenes need distinct situations, not duplicate labels')
    for scene in scenes:
        for key in ('situation', 'space', 'action_phase', 'wardrobe_identity_relation'):
            words(scene.get(key), key)
        require(scene.get('role') in {'hero', 'supporting'}, 'demo role required')
        words(scene.get('showcase'), 'intended showcase traits')
        scope = scene.get('scope', {})
        require(scope.get('rendering_medium') in {'photoreal', 'non_photoreal'} and type(scope.get('visible_humans')) is bool,
                'explicit rendering medium and visible-human scope required')
        require(type(scene.get('protagonist_visible')) is bool, 'declare whether the protagonist is visible')
        if scene['protagonist_visible']:
            require(scope['visible_humans'], 'visible protagonist conflicts with no-human scope')
        else:
            require(scene['role'] == 'supporting', 'a protagonist-free scene is supporting in this Demo profile')
        require(scene.get('prompt_pipeline') in {'manual', 'compiled'}, 'declare actual prompt pipeline')
        if scene['prompt_pipeline'] == 'compiled':
            bound(scene['compiler_manifest'], root)
        checks = scene.get('design_checks', {})
        require(set(checks) == CHECKS, 'eight design domains must be reviewed')
        for key, check in checks.items():
            require(check.get('status') in {'ready', 'not_applicable'}, 'unresolved design review: ' + key)
            words(check.get('evidence'), key + ' specific design evidence or NA reason')
        props = scene.get('props', [])
        require(isinstance(props, list), 'props must be a list; empty is valid')
        for prop in props:
            for key in ('name', 'function', 'necessity_or_existing_equivalent', 'material_period_status',
                        'scale_placement_conditions', 'compositional_role'):
                words(prop.get(key), 'prop ' + key)
        change = scene.get('change_budget', {})
        require(change.get('mode') in {'new', 'revision'}, 'change mode required')
        require(isinstance(change.get('preserve'), list), 'preserved variables required')
        require(set(change.get('changed', [])) <= set(change.get('requested', [])), 'unrequested variable change')
        require(not set(change.get('preserve', [])) & set(change.get('changed', [])), 'same variable changed and preserved')
        if change['mode'] == 'revision':
            bound(change['baseline'], root)
        prompt_path = bound(scene['prompt'], root)
        prompt = prompt_path.read_text()
        request = json.loads(bound(scene['request'], root).read_text())
        require(request.get('prompt') == prompt, 'final request prompt differs from frozen prompt file')
        require(not request.get('num_last_images_to_include'), 'offline manifest requires explicit reference files, not unbound recent images')
        require(not {'referenced_image_paths', 'num_last_images_to_include'} <= set(request), 'two reference mechanisms conflict')
        expected = {(root / r['file']['path']).resolve() for r in refs if r['input']}
        actual = {(root / p).resolve() for p in request.get('referenced_image_paths', [])}
        require(actual == expected, 'actual reference inputs differ from the manifest')
        try:
            _guard.evaluate_skin_constraint(prompt, scope['rendering_medium'], scope['visible_humans'])
        except _guard.SkinConstraintError as exc:
            raise Invalid(str(exc)) from exc
        active = {c['id'] for c in claims if scene['shot'] in c['scope']}
        mapping = scene.get('brief_mapping', {})
        require(set(mapping) == active, 'style-brief applicable claim mapping is incomplete or extraneous')
        for cid, excerpt in mapping.items():
            words(excerpt, 'mapped prompt excerpt')
            require(excerpt in prompt, 'claim mapping is not in actual prompt: ' + cid)
        words(scene.get('reviewer'), 'actual design reviewer')
    return {'kind': 'structural_plan_validation', 'plan_sha256': canonical(plan),
            'scenes': n, 'coverage': coverage, 'visual_quality_proven': False,
            'limitations': ['declarations are not proof of authorization or inspection',
                           'distinct text does not prove distinct plausible scenes',
                           'prompt excerpts do not prove semantic completeness',
                           _guard.LIMITATION]}


def freeze(plan, root):
    result = check_plan(plan, root)
    return {'schema_version': 'demo-freeze-1', 'plan_sha256': result['plan_sha256'],
            'validator_sha256': digest(Path(__file__)), 'skin_guard_sha256': digest(GUARD_PATH),
            'structural_result': result}


def check_run(plan, sealed, run, root, require_delivered=False):
    check_plan(plan, root)
    require(sealed.get('plan_sha256') == canonical(plan), 'plan changed after freeze')
    require(sealed.get('validator_sha256') == digest(Path(__file__)), 'validator changed after freeze')
    require(sealed.get('skin_guard_sha256') == digest(GUARD_PATH), 'skin guard changed after freeze')
    require(run.get('schema_version') == 'demo-run-1' and run.get('plan_sha256') == canonical(plan), 'run does not match frozen plan')
    by_id = {s['id']:s for s in plan['scenes']}
    rows = run.get('images', [])
    require(len({r['scene_id'] for r in rows}) == len(rows), 'duplicate image record')
    require({r['scene_id'] for r in rows} <= set(by_id), 'unplanned image record')
    if require_delivered:
        require({r['scene_id'] for r in rows} == set(by_id), 'final delivery check needs every planned image record')
        require(all(r.get('status') != 'not_started' for r in rows), 'final delivery check has unstarted scenes')
    calls = 0
    for row in rows:
        status = row.get('status')
        require(status in {'not_started', 'generated', 'generation_failed'}, 'invalid execution status')
        events = row.get('calls', [])
        require(isinstance(events, list) and len(events) <= 1, 'extra call/retry is outside this plan')
        calls += len(events)
        if status == 'not_started':
            require(not events and not row.get('image') and not row.get('qa'), 'not-started record cannot claim output or review')
            continue
        require(len(events) == 1, 'executed image requires one actual call record')
        event = events[0]
        for key in ('started_at', 'finished_at', 'tool_result_receipt'):
            words(event.get(key), 'actual call ' + key)
        require(event.get('actual_request_sha256') == by_id[row['scene_id']]['request']['sha256'], 'actual request changed from frozen request')
        if status == 'generation_failed':
            words(row.get('failure'), 'visible failure reason')
            require(not row.get('image') and not row.get('qa'), 'failed generation cannot claim visual QA')
            if require_delivered:
                require(row.get('delivery', {}).get('status') == 'sent', 'failed attempt still needs truthful user notification')
                words(row['delivery'].get('receipt'), 'actual failure notification receipt')
            continue
        image = bound(row['image'], root)
        qa = row.get('qa', {})
        require(qa.get('inspected') is True and qa.get('image_sha256') == digest(image), 'QA must bind to the actually inspected original')
        words(qa.get('reviewer'), 'actual image reviewer')
        require(qa.get('actual_shot') in SHOTS, 'actual shot classification required')
        require(set(qa.get('axes', {})) == AXES, 'four independent visual axes required')
        for axis, item in qa['axes'].items():
            require(item.get('status') in {'pass', 'fail', 'uncertain', 'not_applicable'}, 'invalid visual conclusion')
            words(item.get('evidence'), axis + ' actual-pixel evidence or NA explanation')
        if qa['actual_shot'] != by_id[row['scene_id']]['shot']:
            require(qa['axes']['brief']['status'] != 'pass', 'shot mismatch cannot be marked brief passed')
        for comparison in qa.get('comparisons', []):
            words(comparison.get('reference'), 'comparison reference')
            if comparison.get('comparable') is True:
                require(comparison.get('shot') == qa['actual_shot'], 'cannot claim same-shot comparison across different shot scales')
            else:
                words(comparison.get('limitation'), 'comparison limitation')
        approval = row.get('user_acceptance', {})
        require(approval.get('status') in {'pending', 'accepted', 'rejected'}, 'user acceptance is a separate state')
        if approval['status'] != 'pending':
            words(approval.get('evidence'), 'actual user acceptance/rejection evidence')
        delivery = row.get('delivery', {})
        require(delivery.get('status') in {'pending', 'sent', 'failed'}, 'delivery state required')
        if delivery['status'] == 'sent':
            words(delivery.get('receipt'), 'actual message delivery receipt, not just an upload ID')
            words(delivery.get('library_file_id'), 'delivered original asset ID')
        if require_delivered:
            require(delivery['status'] == 'sent', 'completed output still awaits individual delivery')
    require(calls <= plan['max_calls'], 'call budget exceeded')
    return {'kind': 'structural_run_validation', 'recorded_calls': calls,
            'records': len(rows), 'visual_quality_proven': False,
            'unrecorded_calls_detectable': False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['plan', 'freeze', 'run'])
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--plan', type=Path, required=True)
    ap.add_argument('--freeze', type=Path)
    ap.add_argument('--run', type=Path)
    ap.add_argument('--out', type=Path)
    ap.add_argument('--require-delivered', action='store_true')
    args = ap.parse_args()
    try:
        plan = json.loads(args.plan.read_text())
        if args.command == 'plan': result = check_plan(plan, args.root)
        elif args.command == 'freeze': result = freeze(plan, args.root)
        else:
            require(args.freeze and args.run, 'run needs --freeze and --run')
            result = check_run(plan, json.loads(args.freeze.read_text()), json.loads(args.run.read_text()), args.root, args.require_delivered)
        payload = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.out: args.out.write_text(payload)
        else: print(payload, end='')
    except (Invalid, KeyError, TypeError, ValueError, OSError) as exc:
        ap.exit(2, 'INVALID: ' + str(exc) + '\n')


if __name__ == '__main__': main()
