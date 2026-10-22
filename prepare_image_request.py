"""Prepare real imagegen request parameters offline; never call an API or generate an image."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from base_constraints import checked_scope, check_skin, skin_contract

ROOT = Path(__file__).resolve().parent
TEXT_OPENING = "只生成一张完整原创成片，不做拼图或联系表。本次没有任何参考图输入。"
REFERENCE_OPENING = "只生成一张新的完整原创成片，不做拼图或联系表。提供的图像仅为我方原创风格参考，不是编辑目标，也不是人物身份参考；没有竞品图输入。"
RELEASE = "不得继承参考图的人物身份、脸型、五官、发型、身体比例、服装款式、场景布局、镜头构图、具体道具或动作；它们全部服从本次文字输入。风格参考不锁定人物身份，也不保证风格或身份稳定。"


def nonempty_text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(name + " must be non-empty text")


def checked_reference(item, root):
    if not isinstance(item, dict):
        raise ValueError("each reference must be an object")
    for key in ("id", "file", "sha256", "role", "source_kind", "shot_scale", "provenance", "limits"):
        nonempty_text(item.get(key), "reference." + key)
    if item["role"] != "style_reference":
        raise ValueError("only style_reference is allowed; demo and identity_reference are different roles")
    if item["source_kind"] != "our_generated_original":
        raise ValueError("only declared own-original images may be used")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", item["sha256"]):
        raise ValueError("reference.sha256 must be a full SHA256 digest")
    relative = Path(item["file"])
    if relative.is_absolute() or ".." in relative.parts or ":" in item["file"] or "\\" in item["file"]:
        raise ValueError("reference.file must be a package-relative local path")
    path = (root / relative).resolve()
    if root not in path.parents:
        raise ValueError("reference path escapes the package")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != item["sha256"].lower():
        raise ValueError("reference SHA256 mismatch")
    if path.suffix.lower() != ".png" or not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("reference must be a PNG image")
    return path


def request_skin_scope(prompt, assembly, skin_scope):
    """Require reviewed scope; current assemblies carry a byte-bound base contract.

    Legacy text replay remains unchanged. Preparing a new request from legacy or
    handwritten text requires explicit scope and the same final-prompt checks.
    This does not prove the declaration or recognize all possible prose conflicts.
    """
    if assembly is not None:
        if not isinstance(assembly, dict):
            raise ValueError("assembly must be an object")
        if assembly.get("prompt_sha256") != hashlib.sha256(prompt.encode("utf-8")).hexdigest():
            raise ValueError("assembly prompt SHA256 mismatch")
    bound = assembly.get("skin_constraint") if assembly else None
    if bound is not None:
        if not isinstance(bound, dict):
            raise ValueError("assembly skin constraint must be an object")
        expected = skin_contract(bound.get("scope"))
        if json.dumps(bound, sort_keys=True) != json.dumps(expected, sort_keys=True):
            raise ValueError("assembly mandatory skin constraint is stale or overridden")
        if skin_scope is not None and checked_scope(skin_scope) != bound["scope"]:
            raise ValueError("explicit skin scope conflicts with assembly")
        skin_scope = bound["scope"]
    scope = checked_scope(skin_scope)
    check_skin(prompt, scope)
    return scope


def prepare_request(prompt, mode="text", manifest=None, package_root=ROOT, reference_ids=None, assembly=None, skin_scope=None):
    """Return only actual imagegen kwargs. SHA checks byte identity, not ownership or beauty."""
    nonempty_text(prompt, "prompt")
    if not (prompt == TEXT_OPENING or prompt.startswith(TEXT_OPENING + "\n")):
        raise ValueError("use a generate-mode prompt from compose_prompt.py, not edit or identity_reference")
    if mode not in {"text", "style-reference"}:
        raise ValueError("mode must be text or style-reference")
    scope = request_skin_scope(prompt, assembly, skin_scope)
    request = {"prompt": prompt, "transparent_background": False}
    if mode == "text":
        if manifest is not None or reference_ids:
            raise ValueError("text mode must not receive a manifest or reference IDs")
        return request
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "style-reference-1":
        raise ValueError("style-reference mode requires a supported manifest")
    style = manifest.get("style")
    if not isinstance(style, dict):
        raise ValueError("manifest.style is required")
    for key in ("id", "version", "base_version"):
        nonempty_text(style.get(key), "style." + key)
    if not isinstance(assembly, dict) or assembly.get("mode") != "generate" or assembly.get("input_images") != []:
        raise ValueError("style-reference mode requires a generate-mode assembly manifest with no image inputs")
    actual_style = assembly.get("style")
    actual_base = assembly.get("base")
    if not isinstance(actual_style, dict) or not isinstance(actual_base, dict):
        raise ValueError("assembly must identify its base and style")
    if (style["id"], style["version"], style["base_version"]) != (actual_style.get("id"), actual_style.get("version"), actual_base.get("version")):
        raise ValueError("reference manifest style/base versions do not match this assembly")
    if assembly.get("prompt_sha256") != hashlib.sha256(prompt.encode("utf-8")).hexdigest():
        raise ValueError("assembly prompt SHA256 mismatch")
    style_scope = manifest.get("inherit_style_only")
    if not isinstance(style_scope, list) or not style_scope:
        raise ValueError("manifest must declare a non-empty style-only scope")
    for entry in style_scope:
        nonempty_text(entry, "inherit_style_only entry")
    references = manifest.get("references")
    if not isinstance(references, list) or not 1 <= len(references) <= 5:
        raise ValueError("manifest must contain one to five references")
    root = Path(package_root).resolve()
    checked = {}
    for entry in references:
        path = checked_reference(entry, root)
        if entry["id"] in checked:
            raise ValueError("reference IDs must be unique")
        checked[entry["id"]] = path
    selected = list(checked) if reference_ids is None else list(reference_ids)
    if not selected or len(set(selected)) != len(selected) or set(selected) - set(checked):
        raise ValueError("select known, unique reference IDs")
    body = prompt[len(TEXT_OPENING):].lstrip("\n")
    request["prompt"] = "\n".join([
        REFERENCE_OPENING,
        "仅继承的风格关系：" + "；".join(style_scope) + "。",
        RELEASE,
        body,
    ])
    request["referenced_image_paths"] = [str(checked[key]) for key in selected]
    check_skin(request["prompt"], scope)  # Re-check added reference instructions, not just the original body.
    return request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", required=True, help="A generate-mode assembled-prompt.txt")
    parser.add_argument("--mode", choices=("text", "style-reference"), default="text")
    parser.add_argument("--manifest", help="Curated own-original style-reference manifest")
    parser.add_argument("--assembly-manifest", help="Required in style-reference mode; binds prompt and declared style/base versions")
    parser.add_argument("--reference-id", action="append", dest="reference_ids", help="Optional subset; repeat for multiple IDs")
    parser.add_argument("--rendering-medium", choices=("photoreal", "non_photoreal"), help="Explicit reviewed scope for legacy/handwritten prompts")
    parser.add_argument("--visible-humans", choices=("yes", "no"), help="Whether people are visible; not inferred from keywords")
    parser.add_argument("--out", required=True, help="Write request JSON under an ignored build directory")
    args = parser.parse_args()
    try:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8")) if args.manifest else None
        assembly = json.loads(Path(args.assembly_manifest).read_text(encoding="utf-8")) if args.assembly_manifest else None
        scope = None
        if args.rendering_medium is not None or args.visible_humans is not None:
            if args.rendering_medium is None or args.visible_humans is None:
                raise ValueError("supply both --rendering-medium and --visible-humans")
            scope = {"rendering_medium": args.rendering_medium, "visible_humans": args.visible_humans == "yes"}
        request = prepare_request(Path(args.prompt).read_text(encoding="utf-8"), args.mode, manifest, ROOT, args.reference_ids, assembly, scope)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(request, ensure_ascii=False, indent=2) + "\n")
    except (ValueError, OSError) as exc:
        parser.exit(2, "Request not prepared: " + str(exc) + "\n")
    print("Prepared request only. No image generation performed. Review the prompt and inspect every selected image before using it.")


if __name__ == "__main__":
    main()
