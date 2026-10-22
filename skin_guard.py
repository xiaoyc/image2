"""Finite, scope-aware checks for one photographic-skin invariant.

This is a compiler invariant relative to input/style configuration, not a
security boundary against editing the source. It is deliberately not a semantic
classifier: the documented phrase families and nearby negations are all it sees.
"""

import re

RULE_ID = "PHOTO-SKIN-001"
REQUIRED_SENTENCE = "保留自然纹理，不过度磨皮"
LIMITATION = (
    "Finite English/Chinese phrase matching with clause-local negation only; "
    "not semantic completeness or image inspection. Scope relies on the supplied "
    "rendering_medium and visible_humans values; long-range, quoted, metaphorical "
    "and unusual double-negation constructions may require human review."
)


class SkinConstraintError(ValueError):
    """A recognized invariant violation, with inspectable evaluation metadata."""

    def __init__(self, message, metadata=None):
        super().__init__(message)
        self.metadata = metadata


_BAD = r"(?:poreless|pore[- ]free|air[- ]?brushed|flawless|plastic(?:[- ]like)?)"
_SKIN = r"(?:(?:human|facial|face|natural|youthful|young|baby)\s+)?(?:skin|complexion)"
_TEXTURE = r"(?:(?:natural|human|facial)\s+)*(?:skin\s+texture|skin\s+pores|facial\s+pores|pores)"
_QUANTITY = r"(?:(?:all|any|the|every|visible|natural|remaining)\s+)*"

# Keep patterns specific: 'flawless composition' and age-appropriate smooth
# skin are not violations. 'No pores' is a requested absence, not a negated
# request for poreless skin, so its initial negator belongs to the match.
_PATTERNS = tuple(re.compile(pattern, re.IGNORECASE) for pattern in (
    rf"\b{_BAD}\s+{_SKIN}\b",
    rf"\b{_SKIN}\s+(?:(?:must|should|will)\s+be\s+|(?:is|looks?|appears?)\s+)?{_BAD}\b",
    rf"\b(?:make|render|keep)\s+(?:(?:the|her|his|their)\s+)?{_SKIN}\s+{_BAD}\b",
    rf"\b(?:remove|removing|erase|erasing|eliminate|eliminating|delete|deleting|strip|stripping)\s+{_QUANTITY}{_TEXTURE}\b",
    rf"\b(?:no|zero|without)\s+{_QUANTITY}(?:pores|skin\s+texture)\b",
    rf"\b(?:do\s+not|don['’]t|never)\s+(?:preserve|retain|keep|show)\s+{_QUANTITY}{_TEXTURE}\b",
    r"(?:无|零)毛孔|没有(?:任何|一点|可见的?)?毛孔",
    r"(?:过度|重度|强力|极度|彻底)(?:地)?磨皮",
    r"塑料(?:般的?|感的?)?(?:皮肤|肌肤|皮)",
    r"(?:无瑕|无暇)(?:的)?(?:皮肤|肌肤)",
    r"(?:去除|去掉|消除|抹掉|抹除|擦除|磨掉)(?:所有|全部|任何|自然的?)?(?:(?:皮肤|肌肤|面部)(?:的)?(?:自然)?纹理|(?:皮肤|肌肤|面部)?(?:的)?毛孔)",
    r"(?:不|不要|无需)(?:保留|呈现|显示)(?:任何|自然的?|所有)?(?:皮肤|肌肤)(?:的)?(?:自然)?纹理",
    r"(?:不|不要|无需)保留自然纹理(?=，不过度磨皮)",
))

_BOUNDARY = re.compile(
    r"[.!?;,:\n。！？；，：]|\b(?:but|however|yet|instead)\b|但是|然而|而是|但",
    re.IGNORECASE,
)
_NEGATION = re.compile(
    r"\b(?:do\s+not|does\s+not|should\s+not|must\s+not|can\s*not|"
    r"don['’]t|doesn['’]t|shouldn['’]t|mustn['’]t|can['’]t|never|not(?!\s+only\b)|no|"
    r"avoid(?:ing)?|exclude|reject|prevent|without|forbid|prohibit)\b|"
    r"不要|避免|拒绝|禁止|不应(?:该)?|不得|不能|不可|切勿|勿|不",
    re.IGNORECASE,
)


def _negated(prompt, start):
    """Recognize nearby negation, resetting at punctuation/contrast clauses.

    Odd/even counting handles simple 'do not avoid' double negation. A bounded
    12-word / 48-CJK-character window intentionally avoids distant negators.
    Comma-separated negative lists should repeat the negator for each clause.
    """
    prefix = _BOUNDARY.split(prompt[:start])[-1]
    prefix = " ".join(prefix.split()[-12:])[-96:]
    if re.search(r"[\u3400-\u9fff]", prefix):
        prefix = prefix[-48:]
    return len(_NEGATION.findall(prefix)) % 2 == 1


def evaluate_skin_constraint(prompt: str, rendering_medium: str,
                             visible_humans: bool,
                             require_sentence: bool = True) -> dict:
    """Validate scoped PHOTO-SKIN-001, or raise SkinConstraintError.

    Only photoreal + visible humans is applicable. require_sentence=False is
    for checking unrendered design prose: it never disables conflict detection.
    Metadata records exact substring presence, not inferred equivalent wording.
    Invalid argument types raise TypeError; an unknown medium raises ValueError.
    """
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a string")
    if not isinstance(rendering_medium, str):
        raise TypeError("rendering_medium must be a string")
    if rendering_medium not in ("photoreal", "non_photoreal"):
        raise ValueError("rendering_medium must be photoreal or non_photoreal")
    if type(visible_humans) is not bool:
        raise TypeError("visible_humans must be a bool")
    if type(require_sentence) is not bool:
        raise TypeError("require_sentence must be a bool")

    applicable = rendering_medium == "photoreal" and visible_humans
    conflicts = []
    if applicable:
        matches = sorted(
            (match for pattern in _PATTERNS for match in pattern.finditer(prompt)),
            key=lambda match: (match.start(), -len(match.group())),
        )
        end = -1
        for match in matches:
            if match.start() >= end and not _negated(prompt, match.start()):
                conflicts.append(match.group())
                end = match.end()

    metadata = {
        "rule_id": RULE_ID,
        "applicable": applicable,
        "exact_sentence_present": REQUIRED_SENTENCE in prompt,
        "recognized_conflicts": conflicts,
        "limitation": LIMITATION,
    }
    failures = []
    if applicable and require_sentence and not metadata["exact_sentence_present"]:
        failures.append("missing mandatory sentence: " + REQUIRED_SENTENCE)
    if conflicts:
        failures.append("recognized contradictory skin request(s): " + "; ".join(conflicts))
    if failures:
        raise SkinConstraintError(RULE_ID + ": " + "; ".join(failures), metadata)
    return metadata
