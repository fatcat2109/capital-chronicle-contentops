"""Public meaning/provenance carrier, not an estimator or numeric admission owner.

The optional extension is a consumer contract; no current Main wire is claimed to
implement it. Missing descriptors remain unknown and do not veto useful journalism.
"""
from __future__ import annotations

from copy import deepcopy
import re

FIELDS = ("target_event", "instrument_proxy", "horizon", "knowledge_cutoff_utc",
          "outcome_resolution", "probability_measure", "method", "evaluation_scope",
          "selection", "dependence")
MEASURES = {None, "PHYSICAL_STATISTICAL", "SUBJECTIVE_CHALLENGER", "RISK_NEUTRAL", "UNKNOWN"}


def reader_notices(descriptor):
    """Keep every supplied limitation, including ones outside the short disclosure."""
    notices = [descriptor["reader_disclosure"]]
    for limitation in descriptor["limitations"]:
        if not any(" ".join(limitation.casefold().split()) in " ".join(n.casefold().split()) for n in notices):
            notices.append(limitation)
    return notices


def public_descriptors(row, envelope):
    """Bind an optional exact public extension after ordinary wire/seal validation."""
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of, _private
    values = row.get("public_research_descriptors", [])
    if not isinstance(values, list) or len(values) > 256 or _private(values):
        raise ValueError("PUBLIC_RESEARCH_DESCRIPTOR_INVALID")
    claims = {c["claim_id"]: c for c in envelope.get("public_safe_claims", [])}
    found = {}
    for value in values:
        if not isinstance(value, dict):
            raise ValueError("PUBLIC_RESEARCH_DESCRIPTOR_INVALID")
        cid = value.get("claim_id")
        claim = claims.get(cid) if isinstance(cid, str) else None
        if (claim is None or cid in found
                or value.get("schema_version") != "contentops.public_research_descriptor.v1"
                or value.get("descriptor_sha256") != sha256_of({k: v for k, v in value.items() if k != "descriptor_sha256"})
                or any(value.get(k) != envelope.get(k) for k in ("report_id", "report_version", "report_sha256"))
                or value.get("claim_hash") != claim["claim_hash"]
                or not (value.get("probability_measure") is None or isinstance(value.get("probability_measure"), str))
                or value.get("probability_measure") not in MEASURES
                or any(value.get(k) is not None and not isinstance(value[k], dict)
                    for k in ("target_event", "instrument_proxy", "horizon", "method", "evaluation_scope", "selection", "dependence"))
                or not isinstance(value.get("limitations"), list)
                or len(value["limitations"]) > 16
                or not all(isinstance(v, str) and 8 <= len(v) <= 500 for v in value["limitations"])
                or not isinstance(value.get("reader_disclosure"), str)
                or not 8 <= len(value["reader_disclosure"]) <= 500):
            raise ValueError("PUBLIC_RESEARCH_DESCRIPTOR_INVALID")
        # Preserve the exact original object, including unknown fields. This grants
        # neither model accuracy, numerical authority nor independence.
        found[cid] = deepcopy(value)
    return found


def claim_semantics(admission, claim):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    descriptor = (admission.get("public_research_descriptors") or {}).get(claim["claim_id"])
    context = {"report_id": admission["report_id"], "report_version": admission["report_version"],
        "report_sha256": admission["source_report_sha256"], "claim_id": claim["claim_id"],
        "claim_hash": claim["claim_hash"], "producer_layer": claim["producer_layer"],
        "exact_or_proxy": claim.get("exact_or_proxy"), "basis_risk": claim.get("basis_risk"),
        "review_horizons": deepcopy(admission.get("horizon_blocks", [])),
        "probability_descriptor": deepcopy(descriptor),
        "probability_metadata_state": "EXACT_PERMITTED_PUBLIC_DESCRIPTOR" if descriptor else "UNKNOWN_NOT_SUPPLIED",
        "selection": {"channel": "MAIN_PERMITTED_PUBLIC_REPORT", "population": None, "filter_identity": None},
        "dependence": {"source_hashes": sorted({e["source_hash"] for e in claim.get("evidence", []) if e.get("source_hash")}),
            "component_claim_hash": claim["claim_hash"], "independence": "NOT_ESTABLISHED",
            "main_recirculation_is_independent_confirmation": False},
        "numeric_authority_granted": False}
    context["semantics_sha256"] = sha256_of(context)
    return context


def reference_blockers(reference, context, *, claim_text=""):
    """Check an explicit semantic reference; unknown is never a generated estimate."""
    if reference is None:
        return []
    descriptor = context.get("probability_descriptor")
    if not isinstance(reference, dict) or descriptor is None:
        return ["public_probability_reference_unknown"]
    blockers = []
    if reference.get("descriptor_sha256") != descriptor["descriptor_sha256"]:
        blockers.append("public_probability_descriptor_changed")
    for key in FIELDS:
        if reference.get(key) != descriptor.get(key):
            blockers.append("public_probability_semantic_mismatch:" + key)
    if reference.get("independent_confirmation") is True:
        blockers.append("public_report_recirculation_not_independent_confirmation")
    # Narrow semantic anti-conversion checks complement exact typed joins. They
    # are not a claim that arbitrary natural-language meaning is machine-proven.
    patterns = []
    if descriptor.get("probability_measure") == "RISK_NEUTRAL":
        patterns += [r"win rate", r"probability of profit", r"tỷ lệ thắng", r"xác suất (?:có )?lãi"]
    if (descriptor.get("target_event") or {}).get("kind") == "TERMINAL_DIRECTION":
        patterns += [r"stop.before.target", r"barrier.first.passage", r"chạm (?:dừng lỗ|mục tiêu) trước"]
    for pattern in patterns:
        for match in re.finditer(pattern, claim_text, re.IGNORECASE):
            prefix = claim_text[max(0, match.start() - 55):match.start()]
            if not re.search(r"(?:not|never|không|chưa)\b[^.!?\n]{0,45}$", prefix, re.IGNORECASE):
                blockers.append("public_probability_target_or_measure_reworded")
    return sorted(set(blockers))


def dependence_copy_blockers(claim_text, contexts):
    if not contexts:
        return []
    for match in re.finditer(r"(?:independent (?:sources|confirmations)|xác nhận độc lập|nguồn độc lập)", claim_text, re.IGNORECASE):
        prefix = claim_text[max(0, match.start() - 70):match.start()]
        if not re.search(r"(?:not|never|không|chưa)\b[^.!?\n]{0,60}$", prefix, re.IGNORECASE):
            return ["public_report_recirculation_not_independent_confirmation"]
    return []


def descriptor_changes(before_claims, after_admission):
    """Descriptor changes matter even when permitted claim IDs/prose stay equal."""
    current = after_admission.get("public_research_descriptors") or {}
    changed = []
    for claim in before_claims:
        previous = (claim.get("research_semantics") or {}).get("probability_descriptor")
        if previous != current.get(claim["claim_id"]):
            changed.append(claim["claim_id"])
    return sorted(set(changed))
