"""Interpret hash-bound producer attestation without reading private native workers."""
from __future__ import annotations

import hashlib
from copy import deepcopy


def interpret_public_native_lineage(row, envelope):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of, _hash, _private
    value = row.get("native_public_lineage")
    if value is None:
        return None
    def require(condition):
        if not condition:
            raise ValueError("PUBLIC_NATIVE_LINEAGE_BINDING_INVALID")
    require(isinstance(value, dict) and not _private(value))
    require(value.get("schema") == "CapitalChroniclePublicNativeAssetLineageV1"
        and value.get("state") == "VERIFIED_ACCEPTED_NATIVE_EXCERPTS"
        and value.get("lineage_sha256") == sha256_of({k: v for k, v in value.items() if k != "lineage_sha256"}))
    require(all(value.get(k) == envelope.get(k) for k in ("report_id", "report_version", "report_sha256")))
    require(envelope.get("asset_ids") == [value.get("asset_id")]
        and value.get("model") == "gpt-6.1-sol" and value.get("reasoning_effort") == "max"
        and value.get("canonical_model_source_eligible") is False
        and value.get("execution_readiness") == "BLOCKED"
        and value.get("research_eligibility") == "PERMITTED_CLAIMS_ONLY"
        and value.get("new_independent_observations") == 0)
    require(all(_hash(value.get(k)) for k in ("accepted_native_result_sha256", "individual_asset_analysis_sha256")))
    roles = value.get("role_proof_sha256")
    require(isinstance(roles, dict) and set(roles) == {"primary", "critical", "synthesis"}
        and all(_hash(v) for v in roles.values()))
    claims = {c["claim_id"]: c for c in envelope["public_safe_claims"]}
    excerpts = value.get("excerpts")
    require(isinstance(excerpts, list) and 1 <= len(excerpts) <= 128)
    seen, paths = set(), set()
    for item in excerpts:
        require(isinstance(item, dict) and isinstance(item.get("claim_id"), str))
        claim = claims.get(item.get("claim_id"))
        require(claim is not None and claim["claim_id"] not in seen)
        require(claim["public_safe"] is True and claim["epistemic_layer"] in {"CC_ANALYSIS", "CONDITIONAL_SCENARIO"})
        require(item.get("claim_hash") == claim["claim_hash"]
            and item.get("text_sha256") == hashlib.sha256(claim["text"].encode()).hexdigest()
            and item.get("evidence_refs") == claim["evidence_refs"])
        path = item.get("asset_analysis_path")
        require(isinstance(path, list) and 2 <= len(path) <= 3
            and all(isinstance(p, (str, int)) and not isinstance(p, bool) for p in path))
        require(tuple(path) not in paths)
        seen.add(claim["claim_id"])
        paths.add(tuple(path))
    critical = value.get("critical_review")
    require(isinstance(critical, dict))
    require(_hash(critical.get("individual_review_sha256")))
    if critical.get("state") == "WITHHELD_NO_COMPLETE_PUBLIC_INPUT_JOIN":
        require(set(critical) == {"state", "individual_review_sha256"})
    else:
        require(isinstance(critical.get("evidence_refs"), list)
            and all(isinstance(r, str) for r in critical["evidence_refs"]))
        require(critical.get("state") == "PUBLIC_EXCERPTS_VERIFIED"
            and critical.get("verdict") in {"ACCEPT", "ACCEPT_QUALIFIED"}
            and set(critical.get("evidence_refs") or []) <= {r for c in claims.values() for r in c["evidence_refs"]})
        require(all(isinstance(critical.get(k), list) and all(isinstance(s, str) for s in critical[k])
            for k in ("findings", "required_repairs", "retained_dissent")))
    return {"state": "PRODUCER_ATTESTED_NATIVE_PUBLIC_EXCERPTS", "producer_attestation": deepcopy(value),
        "consumer_exact_public_bindings_verified": True, "permitted_excerpt_count": len(excerpts),
        "independent_native_runtime_verified": False, "private_worker_artifacts_read": False,
        "canonical_model_source_eligible": False, "publication_authority": False}
