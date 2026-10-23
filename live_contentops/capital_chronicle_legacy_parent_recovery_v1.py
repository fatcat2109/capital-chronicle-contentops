"""Owner-pinned ancestry recovery for two immutable legacy Unicode wires only.

The original bytes/failure stay evidence. An in-memory ASCII validation view exercises
the normal schema, rights, authority, clock and evidence gates. No normalized wire is
exported, and no recovered claim or horizon can enter editorial selection.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

POLICY_ID = "GOAL29_TWO_PARENT_UNICODE_V1"
POLICY_SHA256 = "1b219c06f70f9bdf769c93e57ed2171cb22c653de778ecdb4333df876f72fcc4"


def _policy():
    raw = (Path(__file__).resolve().parents[1] / "config/main_legacy_public_parent_recovery_v1.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != POLICY_SHA256:
        raise ValueError("LEGACY_PARENT_RECOVERY_POLICY_CHANGED")
    return json.loads(raw)


def recovery_binding(pointer, manifest, spec, manifest_raw):
    """Only an explicit consumer pointer and the exact committed manifest opt in."""
    if pointer.get("legacy_parent_recovery") != POLICY_ID:
        return None
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    policy = _policy()
    if (any(pointer.get(k) != policy[k] for k in ("producer_repository", "producer_commit"))
            or manifest["manifest_sha256"] != policy["manifest_sha256"]
            or hashlib.sha256(manifest_raw).hexdigest() != policy["manifest_raw_sha256"]):
        raise ValueError("LEGACY_PARENT_RECOVERY_SOURCE_UNPINNED")
    pin = next((p for p in policy["parents"] if p["entry_sha256"] == sha256_of(spec)), None)
    if pin is None:
        return None
    child = manifest["latest_by_asset"][pin["asset_id"]]
    if (sha256_of(child) != pin["child_entry_sha256"]
            or child["parent_report_sha256"] != pin["report_sha256"]):
        raise ValueError("LEGACY_PARENT_RECOVERY_CHILD_UNPINNED")
    return {"policy_id": POLICY_ID, "policy_sha256": POLICY_SHA256, "pin": pin,
            "manifest_raw_sha256": policy["manifest_raw_sha256"]}


def recover_pinned_parent(bundle, failed, *, cutoff_utc):
    """Return ancestry-only normal-gate validation, or None for an ineligible wire."""
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
        canonical_bytes, sha256_of, validate_latest_report_bytes,
    )
    binding = bundle["binding"]
    grant = binding.get("legacy_parent_recovery")
    if not grant or failed["status"] != "BLOCKED":
        return None
    policy = _policy()
    pin = grant.get("pin")
    if (grant.get("policy_id") != POLICY_ID or grant.get("policy_sha256") != POLICY_SHA256
            or pin not in policy["parents"] or grant.get("manifest_raw_sha256") != policy["manifest_raw_sha256"]
            or any(binding.get(k) != policy[k] for k in ("producer_repository", "producer_commit", "manifest_sha256"))
            or binding.get("public_export_manifest_verified") is not True
            or hashlib.sha256(bundle["envelope"]).hexdigest() != pin["envelope_raw_sha256"]
            or hashlib.sha256(bundle["public_export"]).hexdigest() != pin["public_raw_sha256"]
            or hashlib.sha256(bundle["envelope_schema"]).hexdigest() != pin["schema_raw_sha256"]):
        return None
    envelope, public = json.loads(bundle["envelope"]), json.loads(bundle["public_export"])
    if (envelope["report_sha256"] != pin["report_sha256"]
            or envelope["parent_report_sha256"] != pin["parent_report_sha256"]
            or envelope["report_version"] != pin["report_version"]
            or envelope["asset_ids"] != [pin["asset_id"]]):
        return None

    def legacy_hash(value, field):
        return hashlib.sha256(json.dumps({k: v for k, v in value.items() if k != field},
            sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

    # Establish the documented defect positively, including every original claim seal.
    if (envelope["envelope_sha256"] != legacy_hash(envelope, "envelope_sha256")
            or public["projection_sha256"] != legacy_hash(public, "projection_sha256")
            or any(c["claim_hash"] != legacy_hash(c, "claim_hash") for c in envelope["public_safe_claims"])
            or envelope["envelope_sha256"] == sha256_of({k: v for k, v in envelope.items() if k != "envelope_sha256"})):
        return None
    view, public_view = deepcopy(envelope), deepcopy(public)
    for claim in view["public_safe_claims"]:
        claim["claim_hash"] = sha256_of({k: v for k, v in claim.items() if k != "claim_hash"})
    public_view["latest_reports"][0]["public_safe_claims"] = view["public_safe_claims"]
    public_view["projection_sha256"] = sha256_of({k: v for k, v in public_view.items() if k != "projection_sha256"})
    view["envelope_sha256"] = sha256_of({k: v for k, v in view.items() if k != "envelope_sha256"})
    public_raw = canonical_bytes(public_view)
    checked = validate_latest_report_bytes(canonical_bytes(view), expected_cutoff_utc=cutoff_utc,
        envelope_schema_bytes=bundle["envelope_schema"], public_export_bytes=public_raw,
        producer_binding={**binding, "public_report_raw_sha256": hashlib.sha256(public_raw).hexdigest()},
        allow_lineage_only=True)
    if checked["status"] != "ADMITTED":
        return None
    proof = {"policy_id": POLICY_ID, "policy_sha256": POLICY_SHA256,
        "original_failure_blockers": failed["blockers"], "original_envelope_sha256": envelope["envelope_sha256"],
        "original_envelope_raw_sha256": pin["envelope_raw_sha256"],
        "original_public_raw_sha256": pin["public_raw_sha256"], "pin": pin,
        "legacy_canonicalization": policy["intended_legacy_canonicalization"],
        "normal_validation_gates_passed": True, "editorial_claim_credit": 0,
        "independent_observation_credit": 0, "publication_authority": False}
    return {**checked, "producer_binding": deepcopy(binding),
        "raw_sha256": failed["raw_sha256"], "report_raw_sha256": [pin["public_raw_sha256"]],
        "envelope_sha256": envelope["envelope_sha256"], "claims": [], "horizon_blocks": [],
        "claim_set_hash": sha256_of([]), "hold_and_invalidation_conditions": [],
        "withdrawal_only": False, "lineage_only": True, "lineage_recovery": proof}
