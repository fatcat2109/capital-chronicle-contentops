"""Jim's decisions 157 and 158 for newly written public analysis."""
from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
import re

CONTRACT = "CC755_V1"
GUIDANCE = (
    "Write scenario analysis. Lead with the Base case and its stated chance, then the source's Bull or "
    "Bear case and what would prove each wrong. Use only the scenarios and odds the evidence actually holds. "
    "Connect the event to its transmission channel and the impact on the asset. Weigh macro, fundamentals, "
    "sentiment and positioning, and what is priced in. Use technicals to explain the zone and invalidation. "
    "Give the conditional direction and zone in plain language. Keep profit targets out. Use long, short, "
    "buy and sell sparingly. "
)

_LINK = re.compile(r"https?://[^\s<>]+", re.I)
_TARGET = re.compile(
    r"\b(?:profit[- ]target|take[- ]profit|price target|model target level)s?\b"
    r"|\btarget (?:level|price|zone)\s*(?:[:=]|(?:is|at|of)\s+[-+$€£]?\d)"
    r"|(?m:^\s*(?:[-*•>]\s*)?(?:#{1,6}\s*)?(?:model\s+)?target(?:\s+(?:level|price|zone))?\s*[:=])"
    r"|\b(?:our|the plan(?:'s|’s)|exit) (?:price )?target\b",
    re.I,
)
_NUMERIC_TARGET = re.compile(r"\btarget\s+(?:(?:of|at|is|near|around)\s+)?[$€£]?\d[\d,.]*(?![\d.,%])", re.I)
_POLICY_TARGET = re.compile(r"\b(?:inflation|rates?|yield|federal funds|employment|deficit)\s+$", re.I)
_POSITION = re.compile(r"\b(?:longs?|shorts?|buy|sell)\b(?![- ]term\b)", re.I)
_FORCES = (
    re.compile(r"\bmacro(?:economic)?\b", re.I),
    re.compile(r"\bfundamentals?\b", re.I),
    re.compile(r"\b(?:sentiment|positioning)\b", re.I),
    re.compile(r"\bpriced[- ]in\b", re.I),
)
_DIRECTIONS = {
    "BULL": "Bull case", "BULLISH": "Bull case", "UPSIDE": "Bull case", "LONG": "Bull case",
    "BEAR": "Bear case", "BEARISH": "Bear case", "DOWNSIDE": "Bear case", "SHORT": "Bear case",
}


def case_records(plan):
    """Name only held branches. The legacy main alternative is the other side of the base case."""
    scenario = plan.get("scenario_analysis")
    if not isinstance(scenario, Mapping):
        return []

    def has_case(branch):
        return isinstance(branch, Mapping) and (
            bool(str(branch.get("market_move") or "").strip()) or _probability(branch.get("probability_pct"))
        )

    cases = []
    for key, label in (("base_case", "Base case"), ("bull_case", "Bull case"), ("bear_case", "Bear case")):
        branch = scenario.get(key)
        if has_case(branch):
            cases.append((key, label, branch))
    alternative = scenario.get("main_alternative")
    if has_case(alternative) and not any(key != "base_case" for key, _, _ in cases):
        explicit = str(alternative.get("direction") or "").upper()
        base_branch = scenario.get("base_case")
        base_direction = base_branch.get("direction") if isinstance(base_branch, Mapping) else None
        base = str(base_direction or plan.get("direction") or "").upper()
        opposite = {"Bull case": "Bear case", "Bear case": "Bull case"}.get(_DIRECTIONS.get(base))
        label = _DIRECTIONS.get(explicit) if explicit else opposite
        cases.append(("main_alternative", label or "Alternative case", alternative))
    return cases


def _probability(value):
    return type(value) in (int, float) and 0 <= value <= 100


def format_case(label, probability, text=""):
    if _probability(probability):
        odds = format(Decimal(str(probability)).normalize(), "f")
        label += f" ({odds}%)"
    return f"{label}: {text}" if text else label + "."


def validate_copy(text, *, plan=False):
    """Reject profit targets. Return editorial findings for decision 158's preferences."""
    plain = _LINK.sub("", re.sub(r"[*_\x60]", "", text))
    if _TARGET.search(plain) or any(not _POLICY_TARGET.search(plain[:match.start()])
                                    for match in _NUMERIC_TARGET.finditer(plain)):
        raise ValueError("SCENARIO_VOICE_TARGET_FORBIDDEN")
    findings = []
    if len(_POSITION.findall(plain)) > 1:
        findings.append("SCENARIO_VOICE_POSITION_WORDS")
    if plan:
        if not (re.search(r"\bbase case\b", plain, re.I) and re.search(r"\b(?:bull|bear) case\b", plain, re.I)):
            findings.append("SCENARIO_VOICE_CASES")
        if sum(bool(pattern.search(plain)) for pattern in _FORCES) < 2:
            findings.append("SCENARIO_VOICE_FORCE_WEIGHT")
    return findings
