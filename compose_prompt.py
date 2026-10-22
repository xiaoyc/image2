"""Offline prompt assembly and local image verification. Python stdlib only; no API calls."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from validate_review import validate_review, verify_review_target

FIXED = ("palette", "light_signature", "camera_signature", "material_signature", "style_features")
INPUTS = ("subject", "wardrobe", "action", "expression", "environment", "composition")
STYLE_KEYS = {"id", "name", "version", "base_version", "source", "fixed", "overrides", "override_reasons"}
ALLOWED_OVERRIDES = {"medium", "text"}
QUALITY_KEYS = {"composition", "lighting", "background", "materials", "physics", "anatomy", "eyes"}
REFERENCE_KEYS = {"source_kind", "source_file", "source_sha256", "provenance"}
IDENTITY_USE = "仅继承同一明确成年人物的身份、脸型与五官比例、肤色、头发及身体比例；不继承旧图的姿势或取景。"
IDENTITY_RELEASE = "彻底释放参考图的构图、景别、机位、身体截幅、场景、衣服、道具、动作与光线布置；全部按本次输入和当前风格重新设计，不把旧图当作编辑目标。"


def require_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}: non-empty text required")


def require_object(value, field):
    if not isinstance(value, dict):
        raise ValueError(f"{field}: JSON object required")
    return value


def validate_image_metadata(image, mode):
    require_object(image, mode)
    if image.get("source_kind") != "our_generated_original":
        raise ValueError(f"{mode} only accepts our own generated original")
    required = REFERENCE_KEYS if mode == "identity_reference" else REFERENCE_KEYS - {"provenance"} | {"preserve", "change"}
    allowed = required if mode == "identity_reference" else required | {"provenance"}
    if set(image) - allowed:
        raise ValueError(f"{mode}: unsupported fields; exactly one original image is allowed")
    for key in required:
        require_text(image.get(key), mode + "." + key)
    if not re.fullmatch(r"[a-fA-F0-9]{64}", image["source_sha256"]):
        raise ValueError(f"{mode}.source_sha256 must be a full SHA256 digest")
    if "provenance" in image:
        require_text(image["provenance"], mode + ".provenance")
    source = Path(image["source_file"])
    if source.is_absolute() or ".." in source.parts or "://" in image["source_file"]:
        raise ValueError("source_file must be a package-relative local path")


def verify_source(image, package_root):
    """Verify the single declared file, not authorship or an actual image-tool invocation."""
    root = Path(package_root).resolve()
    source = (root / image["source_file"]).resolve()
    if root not in source.parents:
        raise ValueError("source_file must remain inside the package")
    actual = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual.lower() != image["source_sha256"].lower():
        raise ValueError("source image SHA256 mismatch")
    return source


def compose(base, style, inputs, edit=None, reference=None, design_review=None):
    """Return prompt and an assembly-only manifest; this function does not read image bytes."""
    for value, field in ((base, "base"), (style, "style"), (inputs, "input")):
        require_object(value, field)
    if design_review is None:
        raise ValueError("a complete before design_review is required")
    review_summary = validate_review(design_review, expected_stage="before")
    if review_summary["generation_gate"] == "blocked":
        raise ValueError("before-review failed: do not generate; correct the design and review it again")
    if edit is not None and reference is not None:
        raise ValueError("edit and identity_reference modes are mutually exclusive")
    for key in ("name", "version"):
        require_text(base.get(key), "base." + key)
    quality = require_object(base.get("quality_rules"), "base.quality_rules")
    if set(quality) != QUALITY_KEYS:
        raise ValueError("all seven base quality rule categories are required")
    for key, value in quality.items():
        require_text(value, "base.quality_rules." + key)
    defaults = require_object(base.get("defaults"), "base.defaults")
    for key in ("medium", "ratio", "text"):
        require_text(defaults.get(key), "base.defaults." + key)
    review = require_object(base.get("review_methods", {}), "base.review_methods")
    for key, value in review.items():
        require_text(value, "base.review_methods." + key)
    if set(style) - STYLE_KEYS:
        raise ValueError("unsupported style fields; do not copy base quality rules or image inputs")
    for field in ("id", "name", "version", "base_version"):
        require_text(style.get(field), "style." + field)
    source = require_object(style.get("source"), "style.source")
    for field in ("page_url", "use"):
        require_text(source.get(field), "source." + field)
    if not source["page_url"].startswith("https://"):
        raise ValueError("source.page_url must be an HTTPS provenance link")
    if style["base_version"] != base["version"]:
        raise ValueError("base version mismatch")
    fixed = require_object(style.get("fixed"), "style.fixed")
    if set(fixed) != set(FIXED):
        raise ValueError("fixed fields must match the style template")
    for key in FIXED:
        require_text(fixed[key], key)
    if set(inputs) - set(INPUTS) - {"ratio"}:
        raise ValueError("unsupported input field or attempt to override fixed style")
    for key in INPUTS:
        if key != "environment":
            require_text(inputs.get(key), key)
    env = require_object(inputs.get("environment"), "environment")
    if set(env) != {"foreground", "midground", "background"}:
        raise ValueError("three environment layer descriptions are required; a layer may explicitly be empty")
    for key, value in env.items():
        require_text(value, "environment." + key)
    defaults = dict(defaults)
    overrides = require_object(style.get("overrides", {}), "overrides")
    reasons = require_object(style.get("override_reasons", {}), "override_reasons")
    if set(overrides) - ALLOWED_OVERRIDES or set(reasons) != set(overrides):
        raise ValueError("override must be an allowed aesthetic default with a matching reason")
    for key, value in overrides.items():
        require_text(value, key)
        require_text(reasons[key], "reason." + key)
    defaults.update(overrides)
    ratio = inputs.get("ratio", defaults["ratio"])
    if ratio not in {"16:9", "4:5", "3:4", "1:1", "9:16", "3:2", "2:3"}:
        raise ValueError("unsupported ratio")

    mode = "identity_reference" if reference is not None else "edit" if edit is not None else "generate"
    image = reference if reference is not None else edit
    if image is not None:
        validate_image_metadata(image, mode)
    opening = {
        "generate": "只生成一张完整原创成片，不做拼图或联系表。本次没有任何参考图输入。",
        "edit": "只编辑提供的这一张我方原创图，输出一张完整修订成片，不做拼图或联系表。不含竞品图。",
        "identity_reference": "只生成一张新的完整原创成片，不做拼图或联系表。唯一图像输入为我方已生成原创人物，仅作身份参考，不是旧画面编辑；没有竞品图输入。",
    }
    lines = [opening[mode]]
    if mode == "identity_reference":
        lines += ["身份继承范围：" + IDENTITY_USE, "明确释放旧图：" + IDENTITY_RELEASE]
    elif mode == "edit":
        lines += ["编辑不变量：" + edit["preserve"], "本次仅修改：" + edit["change"]]
    lines += [
        "媒介：" + defaults["medium"],
        "场景前景：" + env["foreground"],
        "场景中景：" + env["midground"],
        "场景远景：" + env["background"],
        "主体：" + inputs["subject"], "服装：" + inputs["wardrobe"],
        "动态与接触：" + inputs["action"], "神情与视线：" + inputs["expression"],
        "本次构图与景别：" + inputs["composition"],
        "风格配色：" + fixed["palette"], "风格光线：" + fixed["light_signature"],
        "镜头语言：" + fixed["camera_signature"], "材质特征：" + fixed["material_signature"],
        "本套特色：" + fixed["style_features"],
    ]
    lines += ["基础质量 / " + key + "：" + value for key, value in quality.items()]
    lines += ["输出画幅：" + ratio + "。" + defaults["text"]]
    prompt = "\n".join(lines)
    image_records = []
    if image is not None:
        image_records.append({
            "source_file": image["source_file"], "sha256": image["source_sha256"].lower(),
            "source_kind": image["source_kind"],
            "provenance": image.get("provenance", "Caller-declared own original edit target; legacy metadata has no provenance narrative."),
            "role": "our_generated_original_identity_reference" if reference is not None else "our_generated_original_edit_target",
            "use_scope": IDENTITY_USE if reference is not None else edit["preserve"],
            "release_or_change": IDENTITY_RELEASE if reference is not None else edit["change"],
        })
    manifest = {
        "base": {"name": base["name"], "version": base["version"]},
        "style": {"id": style["id"], "name": style["name"], "version": style["version"]},
        "style_research_provenance": dict(source),
        "input_images": image_records, "image_count_requested": 1,
        "mode": mode, "execution_status": "assembled_only",
        "network_calls": 0, "generation_performed_by_script": False,
        "reference_bytes_verified": False,
        "input_image_record_scope": "declared inputs for a future image-tool call, not evidence that such a call occurred; SHA256 checks byte identity, not authorship",
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "review_methods": dict(review),
        "design_review": {"target": dict(design_review["target"]), "summary": review_summary},
        "validation_scope": "schema, local byte verification when run via CLI, and deterministic assembly only; not visual quality, identity consistency, or complete semantic validation",
    }
    return prompt, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "style", "input", "out"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--review", required=True, help="Complete before-review JSON for this exact input; any declared fail blocks assembly")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--edit", help="JSON for one own-original edit target; preserve/change its existing image")
    modes.add_argument("--reference", help="JSON for one own-original identity reference; release old scene, clothing and framing")
    args = parser.parse_args()
    load = lambda path: json.loads(Path(path).read_text(encoding="utf-8"))
    edit = load(args.edit) if args.edit else None
    reference = load(args.reference) if args.reference else None
    design_review = load(args.review)
    prompt, manifest = compose(load(args.base), load(args.style), load(args.input), edit=edit, reference=reference, design_review=design_review)
    verify_review_target(design_review, Path(__file__).resolve().parent, expected_file=args.input)
    manifest["design_review"]["summary"]["target_bytes_verified"] = True
    manifest["design_review"]["record_sha256"] = hashlib.sha256(Path(args.review).read_bytes()).hexdigest()
    image = reference if reference is not None else edit
    if image is not None:
        verify_source(image, Path(__file__).resolve().parent)
        manifest["reference_bytes_verified"] = True
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "assembled-prompt.txt").write_text(prompt, encoding="utf-8")
    (out / "assembly-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
