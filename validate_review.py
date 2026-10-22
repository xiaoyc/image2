"""Validate review records and declared decisions, never visual quality. Standard library only."""
import argparse
import hashlib
import json
import re
from pathlib import Path

CHECKS = (
    "subject_weight_groups", "balance_mechanism", "viewing_connections",
    "negative_space", "pose_and_support", "proportions_and_position",
    "shot_scale", "light_and_color", "style_identity",
)
STATUSES = {"pass", "fail", "not_applicable"}


def validate_review(record, expected_stage=None):
    """Check complete written evidence and derive the declared outcome; no image inference."""
    if not isinstance(record, dict) or set(record) != {"schema_version", "stage", "target", "checks"}:
        raise ValueError("review requires exactly schema_version, stage, target and checks")
    if record["schema_version"] != "1.0":
        raise ValueError("unsupported review schema_version")
    stage = record["stage"]
    if stage not in {"before", "after"} or expected_stage is not None and stage != expected_stage:
        raise ValueError("review stage mismatch; expected before or after as requested")
    target = record["target"]
    if not isinstance(target, dict) or set(target) != {"file", "sha256"}:
        raise ValueError("review.target requires exactly file and sha256")
    file = target["file"]
    if not isinstance(file, str) or not file.strip():
        raise ValueError("review.target.file must be non-empty")
    path = Path(file)
    if path.is_absolute() or ".." in path.parts or "://" in file:
        raise ValueError("review target must be a package-relative local file")
    if not isinstance(target["sha256"], str) or not re.fullmatch(r"[a-fA-F0-9]{64}", target["sha256"]):
        raise ValueError("review.target.sha256 must be a full SHA256 digest")
    checks = record["checks"]
    if not isinstance(checks, dict) or set(checks) != set(CHECKS):
        raise ValueError("review must contain all nine checks, with no extra check names")
    for key in CHECKS:
        item = checks[key]
        if not isinstance(item, dict) or set(item) != {"status", "evidence"}:
            raise ValueError(f"review.{key} requires exactly status and evidence")
        if not isinstance(item["status"], str) or item["status"] not in STATUSES:
            raise ValueError(f"review.{key}.status must be pass, fail or not_applicable")
        if not isinstance(item["evidence"], str) or not item["evidence"].strip():
            raise ValueError(f"review.{key}.evidence is required, including reasons for not_applicable")
    failed = [key for key in CHECKS if checks[key]["status"] == "fail"]
    applicable = [key for key in CHECKS if checks[key]["status"] != "not_applicable"]
    if not applicable:
        raise ValueError("a review cannot mark all nine checks not_applicable")
    outcome = "fail" if failed else "pass"
    return {
        "structure_valid": True,
        "stage": stage,
        "declared_outcome": outcome,
        "failed_checks": failed,
        "generation_gate": "blocked" if stage == "before" and failed else "declared_pass" if stage == "before" else "not_applicable",
        "delivery_instruction": "May deliver as failed when the user requested it; label failures explicitly, never retry automatically." if stage == "after" and failed else "This record does not authorize generation or delivery and is not user approval.",
        "automatic_retry": False,
        "visual_quality_automatically_evaluated": False,
        "target_bytes_verified": False,
        "validation_scope": "record completeness and declared statuses only; evidence truth and aesthetic decisions require actual human or visual-model review",
    }


def verify_review_target(record, package_root, expected_file=None):
    root = Path(package_root).resolve()
    target = (root / record["target"]["file"]).resolve()
    if root not in target.parents:
        raise ValueError("review target must remain inside the package")
    if expected_file is not None and target != Path(expected_file).resolve():
        raise ValueError("review target is not the requested input file")
    actual = hashlib.sha256(target.read_bytes()).hexdigest()
    if actual != record["target"]["sha256"].lower():
        raise ValueError("review target SHA256 mismatch; review is stale or refers to another file")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", required=True)
    parser.add_argument("--stage", choices=("before", "after"))
    args = parser.parse_args()
    try:
        record = json.loads(Path(args.review).read_text(encoding="utf-8"))
        summary = validate_review(record, expected_stage=args.stage)
        verify_review_target(record, Path(__file__).resolve().parent)
        summary["target_bytes_verified"] = True
    except (ValueError, OSError) as exc:
        parser.exit(2, "Review invalid: " + str(exc) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["generation_gate"] == "blocked":
        parser.exit(3, "Before-review failed: do not generate. Fix the design and review it again.\n")


if __name__ == "__main__":
    main()
