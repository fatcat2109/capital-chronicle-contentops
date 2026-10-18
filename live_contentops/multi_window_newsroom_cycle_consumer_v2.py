"""Merged Main multi-window bundle consumer and ContentOps shadow receipt v2."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any, Callable, Mapping, Sequence

from live_contentops.scheduled_shadow_production_day_v1 import (
    SHADOW_CONFIRMED,
    UNKNOWN_WRITE,
    run_scheduled_shadow_production_day,
)


SCHEMA_VERSION = "CapitalChronicleMultiWindowIntelligenceCycleBundleV1"
RECEIPT_SCHEMA_VERSION = "contentops.multi_window_newsroom_cycle_receipt.v2"
CANONICALIZATION = "JSON_SORT_KEYS_COMPACT_ASCII_UTF8_NO_FLOAT_NAN"
WINDOW_IDS = ("CURRENT_REAL", "RECENT_REPLAY", "PROXY_CONTEXT")
MAIN_REPOSITORY = "fatcat2109/Headline-Raw-data-json"
MAIN_REF = "main"
MAIN_HEAD = "11323a08706cfb90a9f62233598b8ba3e5e6b307"
CONTENTOPS_HEAD = "8571cca13cff70fed69da113f96c243e62962170"
MAIN_ARTIFACT_PATH = "tests/fixtures/multi_window_intelligence_cycle_bundle_current_v1.json"
MAIN_ARTIFACT_BYTES = 53548
MAIN_ARTIFACT_SHA256 = "5d76952bc3c9709f9cc910ab9333144bd5c8ec508e53bc3ed3221e95c3ad2129"
MAIN_BUNDLE_SHA256 = "9e113fd45caf623458f7bb2adfe9b43fe204cb10d96abe62b718f6a13affaed9"
MAIN_CYCLE_ID = "multi-window-cycle-ed95e189282d21a03a9f26f9"
PARENT_RECONCILIATION_SHA256 = "313631f2c3c16ce8fa0de5de7d08aefe961caecbfa4d1e95842c7e43a3cddc29"
PARENT_MAIN_HEAD = "8f66238d320062e9258c893d59d2293253655f94"
PARENT_CONTENTOPS_INPUT_HEAD = "aa5dbda6c73a4f53683365ce26c6323ec57298a9"
PARENT_CONTENTOPS_CONSUMER_HEAD = "f3fb9fb273261d94850007db19aedf4171014c19"
ZERO_EFFECT_KEYS = (
    "scheduler_started",
    "durable_store_write_count",
    "database_mutation",
    "model_call_count",
    "provider_call_count",
    "browser_action_count",
    "public_write_performed",
    "publication_authority",
)
AUTHORITY_KEYS = (
    "decision_authority",
    "forecast_authority",
    "numeric_truth_authority",
    "paper_authority",
    "broker_authority",
    "publication_authority",
    "runtime_authority",
    "database_authority",
    "account_authority",
    "provider_call_performed",
    "model_call_performed",
    "network_call_performed",
    "runtime_mutation_performed",
    "mutable_status_owner",
    "external_effect",
)
CLASSIFICATIONS = frozenset(
    {
        "SHADOW_CONFIRMED",
        "NOT_VERIFIED",
        "BLOCKED",
        "STALE",
        "AMBIGUOUS",
        "UNKNOWN_WRITE",
        "AUTHORITY_FLAG",
        "PACKET_HASH_MISMATCH",
        "PROOF_LAYER_MISMATCH",
        "SOURCE_HEAD_MISMATCH",
    }
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SECRET_VALUE_RE = re.compile(
    r"(?i)(?:bearer\s+[A-Za-z0-9._~+/=-]{8,}|(?:sk|pk|rk)-[A-Za-z0-9_-]{12,}|"
    r"(?:access[_-]?token|refresh[_-]?token|api[_-]?key|password|secret|cookie)\s*[:=]\s*[^\s,;]{8,})"
)
SENSITIVE_RE = re.compile(
    r"(?i)(?:^|_)(?:access[_-]?token|refresh[_-]?token|cookie|password|secret|authorization|"
    r"api[_-]?key|private[_-]?key|session[_-]?token|webhook[_-]?url)(?:$|_)"
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256_without(value: Mapping[str, Any], field: str) -> str:
    return sha256(canonical_bytes({k: v for k, v in value.items() if k != field})).hexdigest()


def receipt_sha256(value: Mapping[str, Any]) -> str:
    return sha256_without(value, "receipt_sha256")


def _parse_utc(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field}_invalid") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field}_timezone_missing")
    return parsed.astimezone(timezone.utc)


def _walk_secret(value: Any, *, path: str = "root") -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if SENSITIVE_RE.search(key_text):
                found.append(f"secret_material:{path}.{key_text}")
            found.extend(_walk_secret(item, path=f"{path}.{key_text}"))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            found.extend(_walk_secret(item, path=f"{path}[{index}]"))
    elif isinstance(value, str) and SECRET_VALUE_RE.search(value):
        found.append(f"secret_material:{path}")
    return found


def _unknown_write(value: Any) -> bool:
    if isinstance(value, Mapping):
        if value.get("unknown_write") is True or str(value.get("status") or "") == UNKNOWN_WRITE:
            return True
        return any(_unknown_write(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_unknown_write(item) for item in value)
    return False


def _zero_effect(core: Mapping[str, Any]) -> dict[str, Any]:
    source = core.get("zero_effect") if isinstance(core.get("zero_effect"), Mapping) else {}
    return {key: source.get(key) for key in ZERO_EFFECT_KEYS}


def _host_facts(bundle: Mapping[str, Any]) -> dict[str, Any]:
    current = next((row for row in bundle.get("windows", []) if row.get("window_id") == "CURRENT_REAL"), {})
    record = (current.get("records") or [{}])[0] if isinstance(current, Mapping) else {}
    lineage = record.get("raw_lineage") if isinstance(record.get("raw_lineage"), Mapping) else {}
    current_facts = lineage.get("current_facts") if isinstance(lineage.get("current_facts"), Mapping) else {}
    return {
        "browseros": lineage.get("browseros"),
        "x_ingestion_cdp": lineage.get("x_ingestion_cdp"),
        "publication_cdp": lineage.get("publication_cdp"),
        "scheduler_tasks": lineage.get("scheduler_tasks") or lineage.get("tasks") or current_facts.get("tasks"),
        "identity": {"status": current_facts.get("identity_status", "MISSING")},
        "destination": {"status": current_facts.get("destination_status", "MISSING")},
        "store": {"integrity_check": current_facts.get("sqlite_integrity", "ok")},
        "runtime_proven": False,
        "publicly_proven": False,
    }


def _validate_bundle(bundle: Mapping[str, Any], *, now_utc: str | None = None) -> list[str]:
    blockers: list[str] = []
    required = {
        "as_of_utc",
        "authority_flags",
        "bundle_sha256",
        "core_projection",
        "cycle_id",
        "drift_summary",
        "editorial_projection",
        "generated_at_utc",
        "limitations",
        "lineage",
        "parent_reconciliation",
        "schema",
        "version",
        "windows",
    }
    if set(bundle) != required:
        blockers.append("bundle_top_level_shape_invalid")
    if bundle.get("schema") != SCHEMA_VERSION or bundle.get("version") != "1.0.0":
        blockers.append("bundle_schema_or_version_invalid")
    supplied = str(bundle.get("bundle_sha256") or "")
    if not SHA256_RE.fullmatch(supplied) or supplied != sha256_without(bundle, "bundle_sha256"):
        blockers.append("bundle_hash_invalid")
    if bundle.get("cycle_id") != MAIN_CYCLE_ID:
        blockers.append("cycle_id_mismatch")
    source = bundle.get("lineage") if isinstance(bundle.get("lineage"), Mapping) else {}
    if source and source.get("contentops_consumer", {}).get("head") not in {None, CONTENTOPS_HEAD}:
        blockers.append("contentops_source_head_mismatch")
    parent = bundle.get("parent_reconciliation") if isinstance(bundle.get("parent_reconciliation"), Mapping) else {}
    if parent.get("receipt_sha256") != PARENT_RECONCILIATION_SHA256:
        blockers.append("parent_reconciliation_hash_mismatch")
    psource = parent.get("source") if isinstance(parent.get("source"), Mapping) else {}
    if psource.get("main_input_head") != PARENT_MAIN_HEAD or psource.get("contentops_input_head") != PARENT_CONTENTOPS_INPUT_HEAD:
        blockers.append("parent_source_head_mismatch")
    authority = bundle.get("authority_flags") if isinstance(bundle.get("authority_flags"), Mapping) else {}
    if any(value not in (False, 0, None) for value in authority.values()):
        blockers.append("authority_flag")
    core = bundle.get("core_projection") if isinstance(bundle.get("core_projection"), Mapping) else {}
    if core.get("authority") is True or core.get("core_authority") is True:
        blockers.append("core_authority_flag")
    if core.get("projection_sha256") != sha256_without(core, "projection_sha256"):
        blockers.append("core_projection_hash_invalid")
    editorial = bundle.get("editorial_projection") if isinstance(bundle.get("editorial_projection"), Mapping) else {}
    if editorial.get("authority") is True or editorial.get("editorial_authority") is True:
        blockers.append("editorial_authority_flag")
    if editorial.get("projection_sha256") != sha256_without(editorial, "projection_sha256"):
        blockers.append("editorial_projection_hash_invalid")
    zero = _zero_effect(core)
    if any(value not in (False, 0, None) for value in zero.values()):
        blockers.append("zero_effect_not_zero")
    windows = bundle.get("windows")
    if not isinstance(windows, Sequence) or [row.get("window_id") for row in windows] != list(WINDOW_IDS):
        blockers.append("windows_exact_order_required")
    for window in windows or []:
        if not isinstance(window, Mapping):
            blockers.append("window_not_mapping")
            continue
        if not SHA256_RE.fullmatch(str(window.get("window_sha256") or "")):
            blockers.append(f"window_hash_invalid:{window.get('window_id')}")
        elif sha256_without(window, "window_sha256") != window.get("window_sha256"):
            blockers.append(f"window_hash_mismatch:{window.get('window_id')}")
        for record in window.get("records") or []:
            if not isinstance(record, Mapping):
                blockers.append("record_not_mapping")
                continue
            eligibility = record.get("eligibility") if isinstance(record.get("eligibility"), Mapping) else {}
            rights = record.get("rights") if isinstance(record.get("rights"), Mapping) else {}
            if rights.get("internal_analysis_allowed") is not True:
                blockers.append(f"rights_invalid:{record.get('claim_id')}")
            if _unknown_write(record):
                blockers.append(f"unknown_write:{record.get('claim_id')}")
            if record.get("freshness", {}).get("state") in {"STALE", "FUTURE"}:
                blockers.append(f"stale_or_future:{record.get('claim_id')}")
            if str(record.get("pit_state") or "").startswith("PIT_INVALID_FUTURE"):
                blockers.append(f"future:{record.get('claim_id')}")
            if eligibility.get("status") == "ADMITTED" and record.get("exact_proxy_context", {}).get("state") == "PROXY":
                blockers.append(f"proxy_core_admission:{record.get('claim_id')}")
    if now_utc:
        try:
            if _parse_utc(bundle.get("as_of_utc"), "bundle.as_of_utc") > _parse_utc(now_utc, "now_utc"):
                blockers.append("bundle_future_as_of")
        except ValueError as exc:
            blockers.append(str(exc))
    blockers.extend(_walk_secret(bundle))
    return list(dict.fromkeys(blockers))


def _policy_matrix() -> dict[str, Any]:
    return {
        "CURRENT_REAL": {"core": "EXCLUDE_WHEN_NOT_VERIFIED", "editorial": "ABSTAIN_UNTIL_FRESH_EXACT", "context": "RETAIN_FACTS"},
        "RECENT_REPLAY": {"core": "ADMIT_EXACT_PIT_RIGHTS_ALLOWED", "editorial": "ADMIT_EXACT_ONLY", "context": "QUALITATIVE_CONTEXT"},
        "PROXY_CONTEXT": {"core": "NEVER", "editorial": "QUALITATIVE_CONTEXT_ONLY", "context": "RETAIN_WITH_PROXY_LABEL"},
        "CONTRADICTION": {"core": "QUARANTINE", "editorial": "QUARANTINE", "context": "RETAIN_REASONS"},
        "STALE_FUTURE_RIGHTS_UNKNOWN": {"core": "ABSTAIN", "editorial": "ABSTAIN", "context": "RETAIN_BLOCKER"},
    }


def _receipt_base(bundle: Mapping[str, Any], *, artifact: Mapping[str, Any], classification: str, blockers: Sequence[str], production_day: Mapping[str, Any] | None, selected: Sequence[str], abstained: Sequence[str], quarantined: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    windows = [dict(row) for row in bundle.get("windows") or [] if isinstance(row, Mapping)]
    core = bundle.get("core_projection") if isinstance(bundle.get("core_projection"), Mapping) else {}
    editorial = bundle.get("editorial_projection") if isinstance(bundle.get("editorial_projection"), Mapping) else {}
    result = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "version": "2.0.0",
        "canonicalization": CANONICALIZATION,
        "cycle_id": bundle.get("cycle_id"),
        "status": "SHADOW_CONFIRMED" if classification == "SHADOW_CONFIRMED" else "BLOCKED",
        "immutable_receipt": True,
        "shadow_only": True,
        "artifact": dict(artifact),
        "bundle_sha256": bundle.get("bundle_sha256"),
        "parent_reconciliation": dict(bundle.get("parent_reconciliation") or {}),
        "source": {
            "main_repository": MAIN_REPOSITORY,
            "main_ref": MAIN_REF,
            "main_head": MAIN_HEAD,
            "contentops_head": CONTENTOPS_HEAD,
        },
        "artifact_provenance": {
            "repository": MAIN_REPOSITORY,
            "ref": MAIN_REF,
            "commit": MAIN_HEAD,
            "path": MAIN_ARTIFACT_PATH,
            "bytes": MAIN_ARTIFACT_BYTES,
            "sha256": MAIN_ARTIFACT_SHA256,
            "bundle_sha256": MAIN_BUNDLE_SHA256,
            "cycle_id": MAIN_CYCLE_ID,
            "parent_reconciliation_sha256": PARENT_RECONCILIATION_SHA256,
            "parent_source_heads": {
                "main_input": PARENT_MAIN_HEAD,
                "contentops_input": PARENT_CONTENTOPS_INPUT_HEAD,
                "contentops_consumer": PARENT_CONTENTOPS_CONSUMER_HEAD,
            },
        },
        "projection_provenance": {
            "lineage_owner_paths": sorted(
                str(value) for value in (bundle.get("lineage") or {}).values()
            ),
            "core_owner_paths": list(core.get("owner_paths") or []),
            "editorial_owner_paths": list(editorial.get("owner_paths") or []),
            "core_owner_packet_id": core.get("owner_packet_id"),
            "core_owner_packet_hash": core.get("owner_packet_hash"),
            "core_owner_packet_verified": core.get("owner_packet_verified"),
        },
        "clocks": {"generated_at_utc": bundle.get("generated_at_utc"), "as_of_utc": bundle.get("as_of_utc")},
        "windows": windows,
        "policy_matrix": _policy_matrix(),
        "core_admission": {"authority": False, "record_count": len(core.get("records") or []), "admitted_claim_ids": [str(row.get("claim_id")) for row in core.get("records") or []], "reasons": list(core.get("blockers") or [])},
        "editorial_admission": {"authority": False, "consumer_contract": editorial.get("consumer_contract"), "record_count": len(editorial.get("records") or [])},
        "selected_claim_ids": list(selected),
        "abstained_claim_ids": list(abstained),
        "contradiction_quarantine": [dict(row) for row in quarantined],
        "unsupported_dimensions": list(bundle.get("limitations") or []) + list(core.get("unsupported_dimensions") or []),
        "article_decision": {"status": "SHADOW_QUALIFIED" if production_day else "ABSTAINED", "article_id": (production_day or {}).get("canonical_article_id"), "reason": "EXACT_PIT_RIGHTS_ALLOWED" if production_day else "CURRENT_REAL_OR_CONTRADICTION_BOUNDARY"},
        "derivative_shadow": {"count": len((production_day or {}).get("derivative_destinations") or []), "destinations": list((production_day or {}).get("derivative_destinations") or []), "receipt_sha256": (production_day or {}).get("production_day_receipt_sha256")},
        "destination_readback_shadow_sha256": (production_day or {}).get("destination_readback_sha256"),
        "interruption_resume": (production_day or {}).get("interruption_recovery", "NOT_ATTEMPTED"),
        "host_facts": {"current_real": _host_facts(bundle), "runtime_proven": False, "publicly_proven": False},
        "zero_effect": _zero_effect(core),
        "proof_axes": {"artifact_hash": artifact.get("status") == "SEALED_MATCH", "bundle_hash": not any("bundle_hash" in b for b in blockers), "parent_hash": not any("parent" in b for b in blockers), "core_authority": False, "runtime_proven": False, "publicly_proven": False},
        "classification": classification,
        "blockers": list(dict.fromkeys(str(item) for item in blockers)),
        "next": "RETAIN_SHADOW_RECEIPT_AND_HAND_TO_MAIN_FOR_GOAL_12_RECONCILIATION",
        "receipt_sha256": None,
    }
    result["receipt_sha256"] = receipt_sha256(result)
    return result


def consume_multi_window_bundle_v2(payload: Mapping[str, Any], *, artifact_bytes: bytes | None = None, shadow_runner: Callable[..., Mapping[str, Any]] | None = None, now_utc: str | None = None) -> dict[str, Any]:
    """Consume the merged Main bundle while reusing the v1 shadow owner seam."""
    bundle = dict(payload) if isinstance(payload, Mapping) else {}
    raw = artifact_bytes if artifact_bytes is not None else canonical_bytes(bundle)
    artifact_hash = sha256(raw).hexdigest()
    artifact = {"repository": MAIN_REPOSITORY, "ref": MAIN_REF, "commit": MAIN_HEAD, "path": MAIN_ARTIFACT_PATH, "bytes": len(raw), "sha256": artifact_hash, "expected_sha256": MAIN_ARTIFACT_SHA256, "status": "SYNTHETIC" if artifact_bytes is None else ("SEALED_MATCH" if len(raw) == MAIN_ARTIFACT_BYTES and artifact_hash == MAIN_ARTIFACT_SHA256 else "HASH_MISMATCH")}
    blockers = _validate_bundle(bundle, now_utc=now_utc)
    if artifact_bytes is not None:
        try:
            sealed_payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            blockers.append("main_artifact_json_invalid")
        else:
            if sealed_payload != bundle:
                blockers.append("main_artifact_payload_mismatch")
    if artifact["status"] == "HASH_MISMATCH":
        blockers.append("main_artifact_hash_mismatch")
    selected = [str(row.get("claim_id")) for row in (bundle.get("core_projection", {}).get("records") or []) if isinstance(row, Mapping) and row.get("eligibility", {}).get("status") == "ADMITTED"]
    abstained = [str(row.get("claim_id")) for window in bundle.get("windows") or [] if isinstance(window, Mapping) for row in window.get("records") or [] if isinstance(row, Mapping) and row.get("eligibility", {}).get("status") != "ADMITTED"]
    quarantined = [row for window in bundle.get("windows") or [] if isinstance(window, Mapping) for row in window.get("contradiction_quarantine") or [] if isinstance(row, Mapping)]
    if blockers:
        classification = "NOT_VERIFIED" if any("secret_material" in b for b in blockers) else "UNKNOWN_WRITE" if any("unknown_write" in b or "zero_effect" in b for b in blockers) else "AUTHORITY_FLAG" if any("authority" in b for b in blockers) else "STALE" if any("stale" in b or "future" in b for b in blockers) else "PACKET_HASH_MISMATCH" if any("hash" in b or "payload_mismatch" in b or "json_invalid" in b for b in blockers) else "SOURCE_HEAD_MISMATCH" if any("head" in b or "source" in b for b in blockers) else "NOT_VERIFIED"
        return _receipt_base(bundle, artifact=artifact, classification=classification, blockers=blockers, production_day=None, selected=selected, abstained=abstained, quarantined=quarantined)
    editorial = bundle.get("editorial_projection") if isinstance(bundle.get("editorial_projection"), Mapping) else {}
    if bundle.get("drift_summary", {}).get("classification") == "NOT_VERIFIED":
        blockers.append("current_real_or_parent_not_verified")
        return _receipt_base(bundle, artifact=artifact, classification="NOT_VERIFIED", blockers=blockers, production_day=None, selected=selected, abstained=abstained, quarantined=quarantined)
    components = editorial.get("shadow_components")
    if not isinstance(components, Mapping):
        return _receipt_base(bundle, artifact=artifact, classification="NOT_VERIFIED", blockers=["shadow_components_missing"], production_day=None, selected=selected, abstained=abstained, quarantined=quarantined)
    runner = shadow_runner or run_scheduled_shadow_production_day
    production_day = runner(enabled=True, **dict(components))
    classification = "SHADOW_CONFIRMED" if production_day.get("status") == SHADOW_CONFIRMED else "UNKNOWN_WRITE" if production_day.get("status") == UNKNOWN_WRITE else "BLOCKED"
    return _receipt_base(bundle, artifact=artifact, classification=classification, blockers=[] if classification == "SHADOW_CONFIRMED" else [f"scheduled_shadow:{production_day.get('status')}"], production_day=production_day, selected=selected, abstained=abstained, quarantined=quarantined)


__all__ = ["RECEIPT_SCHEMA_VERSION", "consume_multi_window_bundle_v2", "receipt_sha256"]
