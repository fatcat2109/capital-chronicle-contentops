"""Read-only Capital Chronicle evidence bridge for generic ContentOps stories."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "capital_chronicle_content_evidence_packet.v2"
REQUIRED_STATE_FILES = (
    "MarketSnapshot.json",
    "MarketHistory.json",
    "DataQualityReport.json",
    "InputStateManifest.json",
    "SourceHealth.json",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path.name}")
    return value


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_evidence_packet(packet: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    required = (
        "schema_version", "packet_id", "generated_at_utc", "as_of_utc", "story_window",
        "events", "official_source_documents", "numeric_claims", "market_snapshots",
        "source_state", "candidate_visual_inputs", "citation_map", "provenance",
        "public_claim_permissions", "blockers",
    )
    blockers.extend(f"missing:{key}" for key in required if key not in packet)
    for claim in packet.get("numeric_claims") or []:
        for key in ("claim_id", "metric", "value", "unit", "observation_time_utc", "source_id", "source_artifact_ref"):
            if claim.get(key) in (None, ""):
                blockers.append(f"numeric_claim:{claim.get('claim_id') or 'unknown'}:missing:{key}")
        if claim.get("llm_numeric_authority") is not False:
            blockers.append(f"numeric_claim:{claim.get('claim_id')}:llm_authority_must_be_false")
    return blockers


def build_evidence_packet_from_cc_root(
    capital_chronicle_root: str | Path,
    *,
    as_of_utc: str | None = None,
    story_window_hours: int = 24,
) -> dict[str, Any]:
    root = Path(capital_chronicle_root).resolve()
    state_root = root / "data" / "state" / "current"
    missing = [name for name in REQUIRED_STATE_FILES if not (state_root / name).is_file()]
    if missing:
        raise FileNotFoundError("missing_cc_state_files:" + ",".join(missing))
    artifacts = {name: _read_json(state_root / name) for name in REQUIRED_STATE_FILES}
    snapshot = artifacts["MarketSnapshot.json"]
    dqr = artifacts["DataQualityReport.json"]
    source_health = artifacts["SourceHealth.json"]
    market_history = artifacts["MarketHistory.json"]
    as_of = as_of_utc or _iso_now()
    numeric_claims: list[dict[str, Any]] = []
    visual_inputs: list[dict[str, Any]] = []
    citation_map: dict[str, list[str]] = {}
    for symbol, row in sorted((snapshot.get("metrics") or {}).items()):
        if not isinstance(row, Mapping) or row.get("value") is None or not row.get("timestamp_utc"):
            continue
        claim_id = f"market:{symbol}:{str(row['timestamp_utc']).replace(':', '').replace('-', '')}"
        source_id = str(row.get("source_id") or "unknown")
        source_ref = f"data/state/current/MarketSnapshot.json#metrics.{symbol}"
        history_rows = [item for item in (market_history.get(symbol) or []) if isinstance(item, Mapping) and item.get("value") is not None]
        prior_rows = [item for item in history_rows if str(item.get("timestamp_utc") or "") < str(row.get("timestamp_utc") or "")]
        prior_close = prior_rows[-1].get("value") if prior_rows else None
        move_since_prior = (float(row["value"]) - float(prior_close)) if prior_close is not None else None
        move_percent = (move_since_prior / float(prior_close) * 100.0) if prior_close not in (None, 0) else None
        numeric_claims.append({
            "claim_id": claim_id,
            "metric": symbol,
            "canonical_symbol": symbol,
            "provider_symbol": source_id,
            "value": row.get("value"),
            "bid": row.get("bid"),
            "ask": row.get("ask"),
            "mid": row.get("mid"),
            "last": row.get("last") or row.get("value"),
            "prior_close": prior_close,
            "move_since_prior_close": round(move_since_prior, 6) if move_since_prior is not None else None,
            "move_since_prior_close_percent": round(move_percent, 6) if move_percent is not None else None,
            "interval": "latest_committed_observation",
            "unit": row.get("unit"),
            "observation_time_utc": row.get("timestamp_utc"),
            "release_time_utc": None,
            "ingestion_time_utc": snapshot.get("generated_at_utc"),
            "revision_time_utc": None,
            "source_id": source_id,
            "source_method": row.get("source_method"),
            "source_authority": (row.get("metadata") or {}).get("status", "unverified"),
            "freshness_class": row.get("freshness_status", "unknown"),
            "session_state": snapshot.get("market_session_state", "unknown"),
            "source_health": row.get("freshness_status", "unknown"),
            "source_artifact_ref": source_ref,
            "public_claim_allowed": bool(dqr.get("reporting_allowed")) and row.get("freshness_status") == "fresh",
            "llm_numeric_authority": False,
        })
        citation_map[claim_id] = [source_ref]
        visual_inputs.append({
            "visual_input_id": f"series:{symbol}",
            "role_candidates": ["primary_quantitative_chart", "cross_asset_chart"],
            "evidence_dimension": f"market_series:{symbol}",
            "modality": "time_series",
            "underlying_series_ids": [symbol],
            "source_artifact_ref": source_ref,
            "rights_status": "capital_chronicle_internal_data_visualization_allowed",
            "public_claim_allowed": bool(dqr.get("reporting_allowed")),
        })
    provenance = {
        name: {
            "relative_path": f"data/state/current/{name}",
            "sha256": _sha256_file(state_root / name),
            "last_write_time_utc": datetime.fromtimestamp((state_root / name).stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        for name in REQUIRED_STATE_FILES
    }
    hard_blockers = []
    if not dqr.get("reporting_allowed"):
        hard_blockers.append("capital_chronicle_dqr_reporting_not_allowed")
    if str(dqr.get("overall_status")) != "ready":
        hard_blockers.append(f"capital_chronicle_dqr_{dqr.get('overall_status', 'unknown')}")
    packet_core = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _iso_now(),
        "as_of_utc": as_of,
        "story_window": {"hours": story_window_hours, "start_utc": None, "end_utc": as_of},
        "events": [],
        "headlines": [],
        "official_source_documents": [],
        "numeric_claims": numeric_claims,
        "market_snapshots": [{
            "snapshot_id": snapshot.get("snapshot_id"),
            "generated_at_utc": snapshot.get("generated_at_utc"),
            "market_session_state": snapshot.get("market_session_state"),
            "snapshot_quality": snapshot.get("snapshot_quality"),
            "ttl_policy_seconds": snapshot.get("ttl_policy_seconds"),
            "claim_ids": [row["claim_id"] for row in numeric_claims],
        }],
        "time_series_references": [row["source_artifact_ref"] for row in numeric_claims],
        "cross_asset_context": [row["claim_id"] for row in numeric_claims],
        "source_state": {
            "dqr_report_id": dqr.get("report_id"),
            "dqr_generated_at_utc": dqr.get("generated_at_utc"),
            "dqr_status": dqr.get("overall_status"),
            "reporting_allowed": bool(dqr.get("reporting_allowed")),
            "source_health_status": source_health.get("overall_status"),
            "source_health_generated_at_utc": source_health.get("generated_at_utc"),
            "input_state_manifest_authority": artifacts["InputStateManifest.json"].get("manifest_authority"),
        },
        "candidate_visual_inputs": visual_inputs,
        "citation_map": citation_map,
        "provenance": provenance,
        "public_claim_permissions": {
            "numeric_claims_allowed": bool(dqr.get("reporting_allowed")),
            "narrative_synthesis_allowed": bool(dqr.get("reporting_allowed")),
            "llm_numeric_authority": False,
            "decision": "ALLOW" if dqr.get("reporting_allowed") else "BLOCK",
        },
        "blockers": hard_blockers,
        "bridge_safety": {"source_repo_modified": False, "secret_files_read": False, "network_call_made": False},
    }
    packet_id = "cc-evidence-" + hashlib.sha256(json.dumps(packet_core, sort_keys=True).encode()).hexdigest()[:16]
    packet = {"packet_id": packet_id, **packet_core}
    packet["validation_blockers"] = validate_evidence_packet(packet)
    packet["status"] = "PASS_CONTRACT_BLOCKED_PUBLICATION" if hard_blockers and not packet["validation_blockers"] else ("PASS" if not packet["validation_blockers"] else "FAIL_SCHEMA")
    return packet


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capital-chronicle-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--as-of-utc")
    args = parser.parse_args(argv)
    packet = build_evidence_packet_from_cc_root(args.capital_chronicle_root, as_of_utc=args.as_of_utc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": packet["status"], "packet_id": packet["packet_id"]}, sort_keys=True))
    return 0 if packet["status"] != "FAIL_SCHEMA" else 2


if __name__ == "__main__":
    raise SystemExit(main())
