"""Base invariants cannot be removed or replaced by style/input configuration.

The source remains editable code, not a security boundary. Explicit scope is a
reviewed declaration, not automatic recognition of humans or photographic media.
"""
import hashlib
import json
from pathlib import Path

import skin_guard

ROOT = Path(__file__).resolve().parent
POLICY_PATH = ROOT / "base-image-production" / "mandatory-constraints.json"
EXPECTED_POLICY = {
    "schema_version": "base-constraints-1",
    "rules": [{"id": "PHOTO-SKIN-001", "sentence": "保留自然纹理，不过度磨皮",
               "when": {"rendering_medium": "photoreal", "visible_humans": True},
               "overridable": False}],
}


def validate_policy_data(value):
    if json.dumps(value, sort_keys=True) != json.dumps(EXPECTED_POLICY, sort_keys=True):
        raise ValueError("mandatory base skin policy cannot be removed, weakened or overridden")


def load_policy():
    raw = POLICY_PATH.read_bytes()
    value = json.loads(raw)
    validate_policy_data(value)
    if (skin_guard.RULE_ID, skin_guard.REQUIRED_SENTENCE) != (
            "PHOTO-SKIN-001", "保留自然纹理，不过度磨皮"):
        raise ValueError("mandatory skin validator contract mismatch")
    return value, hashlib.sha256(raw).hexdigest()


def checked_scope(scope):
    if not isinstance(scope, dict) or set(scope) != {"rendering_medium", "visible_humans"}:
        raise ValueError("explicit skin scope requires rendering_medium and visible_humans")
    if not isinstance(scope["rendering_medium"], str) or scope["rendering_medium"] not in {"photoreal", "non_photoreal"}:
        raise ValueError("rendering_medium must be photoreal or non_photoreal")
    if type(scope["visible_humans"]) is not bool:
        raise ValueError("visible_humans must be a boolean")
    return dict(scope)


def skin_contract(scope):
    scope = checked_scope(scope)
    _, policy_hash = load_policy()
    return {"id": skin_guard.RULE_ID, "scope": scope,
            "required_sentence": skin_guard.REQUIRED_SENTENCE,
            "applicable": scope["rendering_medium"] == "photoreal" and scope["visible_humans"],
            "overridable": False, "policy_sha256": policy_hash,
            "validator_sha256": hashlib.sha256(Path(skin_guard.__file__).read_bytes()).hexdigest(),
            "source_file": "base-image-production/mandatory-constraints.json"}


def check_skin(prompt, scope, require_sentence=True):
    contract = skin_contract(scope)
    result = skin_guard.evaluate_skin_constraint(prompt, **contract["scope"],
                                                 require_sentence=require_sentence)
    return {**result, "contract": contract}
