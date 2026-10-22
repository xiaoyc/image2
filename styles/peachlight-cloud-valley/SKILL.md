---
name: peachlight-cloud-valley
description: Compose original peach-blossom fantasy portraits and landscape scenes with natural human texture, coherent usable spaces, pale cyan and ivory fabric, directional soft light, and atmospheric depth.
---

# 桃霞云岫

## Purpose

Create an original, believable inhabited mountain setting using peach pink, mist white and pale cyan. This is a style layer, not a requirement to reproduce a television series, actor, or competitor composition.

## Layer contract

- Base owns subject identity, adult age, world or historical constraints, continuity, and output requirements.
- Shot owns the visible action, camera view, shot scale, body orientation and spatial relationships.
- Style owns color, lighting, material response, atmosphere and hierarchy. It must not silently replace the shot, subject or historical constraints.
- If a monochrome-only base conflicts with this color photographic style, resolve the conflict explicitly rather than merging incompatible requests.

## Mandatory human texture

For a photoreal request with visible people, the final prompt must include the exact sentence: 保留自然纹理，不过度磨皮。

Do not force skin instructions or people into an empty landscape or non-photoreal request. Declare the scope honestly and apply the shared base policy in ../../base-image-production/mandatory-constraints.json. This style file is a manual authoring guide, not a compose_prompt.py JSON preset.

Render age-appropriate subtle skin texture and color variation, normal eye proportions and natural asymmetry. Do not substitute exaggerated pores, forced wrinkles, perfect beauty, waxy skin, doll faces or excessive eye sharpening. Text compliance is not visual compliance: inspect the actual result. Match the person's illumination, sharpness and contrast to the setting.

## Composition workflow

1. Choose one meaningful visible action and a usable location before listing scenery.
2. Establish the bearing surface, plausible body support, an intelligible access route and the purpose of nearby architecture. Water should relate to terrain, banks and flow direction.
3. Assign foreground, middle ground and distance distinct roles. Large foreground flowers or rocks may frame or support the composition; the middle ground may carry people and their relationships; distance may provide atmosphere or scale. This is not a rule that large scenery is allowed only far away.
4. Decide what viewers read first. Use position, contrast, brightness, sharpness and occlusion, not a compulsory low object count or empty walls.
5. Avoid a checklist of equally prominent pavilions, lakes, waterfalls and peaks. Richness is allowed when it belongs to the same place and supports the action.
6. Match information to shot scale. Facial details do not require a complete landscape behind them. Wide scenes must actually show small figures and readable terrain; do not claim distant skin details can be verified.

## Style invariants

- Peach pink primarily belongs to blossoms, pale cyan and ivory to garments, with cooler gray-blue distance. Keep warm timber, gray rock or muted green as tonal anchors.
- Soft directional side or back light can transmit through petals, fine hair and thin fabric edges. Broad sky fill keeps important faces readable without studio-like detachment.
- Distinguish opaque lining from translucent outer fabric. Preserve weight, weave, folds and modest embroidery rather than uniform glowing clothing.
- Keep nearby contact points readable. Haze separates distance and valley levels; it must not conceal foreground geometry.
- Favor a natural engaged action over a forced camera smile. For portrait showcase shots, a readable front or three-quarter face is a useful default, not a universal ban on profiles or backs in narrative wide views.

## Variables

People, gender, adult age, clothing cuts, actions, camera distance, light direction and locations may vary. A corridor, a single pavilion, a woman, a bridge, or a specific pose is not a permanent requirement. Buildings and vegetation may be dense if scale, routes, materials and focal hierarchy remain credible.

## Prompt construction

Describe the location and action, character and shot, material and lighting relationships, then only the scenery needed by that shot. Include the exact skin sentence. State concrete geometric relationships rather than repeating adjectives such as spectacular, luxurious, plentiful or highly detailed.

## Actual-image review

Check the face for over-retouching, material-specific light response, body support and visible limb relationships, routes/access and foundations, and coherent perspective. Separate visible defects from unverified areas: an occluded route is not proof of an impossible route, and a small back-facing figure cannot prove skin fidelity. Report dimensions actually returned. Do not silently crop or stretch to claim a target ratio.

## Provenance and status

The accepted aesthetic baseline is baseline/accepted-demo02.png, generated from baseline/actual-prompt.txt. The six examples cover one facial detail, one near shot, two medium scenes and two genuine environment-wide scenes. They are test cases, not individually approved final assets.

All included images were generated with native imagegen from manually written prompts, one call per image, without competitor image conditioning or automatic aesthetic retries. They were not produced through a compiler pipeline. No claim of automatic visual enforcement is made.

Public style research source: https://www.gonghaosnail.com/skill-library . Competitor images and paid resource contents are not included in this package.
