"""Pre-public candidate gate for the V6 controlled public run.

This module is deterministic and credential-free. It checks whether the current
candidate can be promoted from dry-run rehearsal to public dispatch, with an
extra semantic duplicate-family guard for the Telegram incident class where an
exact hash-only ledger is not enough.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Mapping

from live_contentops.live_production_pipeline_runner_v6 import (
    CURRENT_8_PLATFORMS,
    _packet_hash,
    _rehearsal_payload_specs,
)
from live_contentops.public_dispatch_freeze_guard_v6 import (
    build_public_dispatch_topic_hash,
    load_public_dispatch_hashes,
)

TASK_LABEL = "TASK_CONTENTOPS_V6_CONTROLLED_8_PLATFORM_PUBLIC_CANDIDATE_OPERATOR_GO_READBACK_AND_CROP_QA_V0"
SCHEMA_VERSION = "0.1.0"

DEFAULT_ARTICLE_PACKET = Path("docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json")
DEFAULT_VARIANT_PACKET = Path("docs/automation/V6_PLATFORM_NATIVE_VARIANTS/platform_variant_packet.json")
DEFAULT_LATEST_AUDIT = Path("docs/automation/V6_PLATFORM_NATIVE_VARIANTS/latest_dispatch_audit.json")
DEFAULT_DAILY_SCHEDULE = Path("docs/automation/V6_DAILY_EDITORIAL_SCHEDULE/daily_schedule_2026_07_08.json")
DEFAULT_DRY_RUN_EVIDENCE = Path(
    "docs/automation/V6_DRY_RUN_FULL_AUTOMATION_REHEARSAL/dry_run_full_automation_rehearsal_evidence_v0.json"
)
DEFAULT_INCIDENT_EVIDENCE = Path(
    "docs/automation/V6_TELEGRAM_INCIDENT_FREEZE_ROOT_CAUSE/telegram_incident_freeze_rootcause_evidence_v0.json"
)
DEFAULT_LEDGER = Path("docs/automation/V6_PUBLIC_DISPATCH_FREEZE/public_dispatch_duplicate_ledger_v6.jsonl")
DEFAULT_OUTPUT = Path(
    "docs/automation/V6_CONTROLLED_8_PLATFORM_PUBLIC_CANDIDATE_QA/pre_public_gate_evidence_v0.json"
)
DEFAULT_FRESH_REHEARSAL_EVIDENCE = Path(
    "docs/automation/V6_CONTROLLED_8_PLATFORM_PUBLIC_CANDIDATE_QA/fresh_slot6_dry_run_rehearsal_evidence_v0.json"
)

OIL_FAMILY = "crude_wti_oil_volatility"
FED_FUNDS_FAMILY = "fed_funds_policy_rates"
CALENDAR_FAMILY = "multi_event_policy_calendar"
POLITICAL_CLAIM_FAMILY = "politically_sensitive_claim"

OIL_TERMS = (
    "crude",
    "wti",
    "oil volatility",
    "oil-volatility",
    "oil price",
    "oil sales",
    "petroleum",
    "hormuz",
    "eia",
    "energy inventory",
    "energy-price",
    "iranian oil",
)
FED_FUNDS_TERMS = (
    "effective fed funds",
    "fed funds rate",
    "federal funds",
    "fed funds policy",
    "policy corridor",
    "iorb",
    "sofr",
    "overnight rate",
    "overnight rates",
    "fomc target",
    "treasury rates",
)
POLITICAL_TERMS = ("biden", "trump", "illegal immigrant", "immigration")


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def stable_hash(value: Any, length: int | None = None) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return digest[:length] if length else digest


def read_json(path: str | Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    p = Path(path)
    if not p.exists():
        return rows
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def article_text(article_packet: Mapping[str, Any]) -> str:
    draft = article_packet.get("canonical_article_draft")
    if not isinstance(draft, Mapping):
        return ""
    parts = [
        draft.get("title"),
        draft.get("subtitle"),
        draft.get("slug_candidate"),
        draft.get("dek"),
        draft.get("meta_description"),
        draft.get("intro"),
        draft.get("conclusion"),
    ]
    for section in draft.get("sections") or []:
        if isinstance(section, Mapping):
            parts.extend([section.get("title"), section.get("body")])
    for item in (draft.get("source_trail") or []) + (draft.get("citations") or []):
        parts.append(item)
    return " ".join(_flatten_text(parts))


def _flatten_text(value: Any) -> Iterable[str]:
    if value is None:
        return
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, Mapping):
        for item in value.values():
            yield from _flatten_text(item)
        return
    if isinstance(value, Iterable):
        for item in value:
            yield from _flatten_text(item)
        return
    yield str(value)


def detect_content_families(*values: Any) -> list[str]:
    blob = " ".join(_flatten_text(values)).lower()
    families: list[str] = []
    if any(term in blob for term in OIL_TERMS):
        families.append(OIL_FAMILY)
    if any(term in blob for term in FED_FUNDS_TERMS):
        families.append(FED_FUNDS_FAMILY)
    if "today's key events" in blob or "key events" in blob:
        families.append(CALENDAR_FAMILY)
    if any(term in blob for term in POLITICAL_TERMS):
        families.append(POLITICAL_CLAIM_FAMILY)
    return families


def ledger_family_index(ledger_rows: list[dict[str, Any]], incident_evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    rows_by_family: dict[str, list[dict[str, Any]]] = {}
    for row in ledger_rows:
        families = detect_content_families(
            row.get("canonical_url"),
            row.get("topic_hint"),
            row.get("media_hint"),
            row.get("reason"),
            row.get("platform"),
        )
        for family in families:
            rows_by_family.setdefault(family, []).append(
                {
                    "record_type": row.get("record_type"),
                    "platform": row.get("platform"),
                    "canonical_url": row.get("canonical_url"),
                    "topic_hint": row.get("topic_hint"),
                    "media_hint": row.get("media_hint"),
                    "reason": row.get("reason"),
                }
            )
    if isinstance(incident_evidence, Mapping):
        families = detect_content_families(incident_evidence)
        for family in families:
            rows_by_family.setdefault(family, []).append({"record_type": "incident_evidence", "source": str(DEFAULT_INCIDENT_EVIDENCE)})
    return {
        "families": sorted(rows_by_family),
        "rows_by_family": rows_by_family,
    }


def media_fingerprint(variant_packet: Mapping[str, Any]) -> dict[str, Any]:
    manifest = variant_packet.get("media_manifest")
    manifest = manifest if isinstance(manifest, Mapping) else {}
    assets = manifest.get("media_assets") if isinstance(manifest.get("media_assets"), list) else []
    selected = manifest.get("selected_media_by_platform") if isinstance(manifest.get("selected_media_by_platform"), Mapping) else {}
    source_fields = {
        "image_path": variant_packet.get("image_path"),
        "public_image_url": variant_packet.get("public_image_url"),
        "selected_media_by_platform": selected,
        "assets": [
            {
                "asset_id": asset.get("asset_id"),
                "local_path": asset.get("local_path"),
                "public_url": asset.get("public_url") or asset.get("image_url"),
                "source_label": asset.get("canonical_source_label") or asset.get("source_label"),
                "visual_metric": asset.get("visual_metric"),
                "media_subject": asset.get("media_subject"),
            }
            for asset in assets
            if isinstance(asset, Mapping)
        ],
    }
    return {
        "media_identity": source_fields,
        "media_hash": stable_hash(source_fields, length=16),
        "families": detect_content_families(source_fields),
    }


def build_current_candidate_gate(
    *,
    article_packet: dict[str, Any],
    variant_packet: dict[str, Any],
    ledger_rows: list[dict[str, Any]],
    incident_evidence: dict[str, Any],
    run_id: str = "pre_public_current_candidate",
) -> dict[str, Any]:
    draft = article_packet.get("canonical_article_draft") if isinstance(article_packet.get("canonical_article_draft"), dict) else {}
    topic = str(
        (article_packet.get("source_context_packet") or {}).get("operator_idea")
        or draft.get("title")
        or ""
    )
    angle = str((article_packet.get("source_context_packet") or {}).get("editorial_angle") or draft.get("subtitle") or "")
    topic_hash = build_public_dispatch_topic_hash(topic, angle)
    variants = variant_packet.get("variants") if isinstance(variant_packet.get("variants"), dict) else {}
    threads = variant_packet.get("variant_threads") if isinstance(variant_packet.get("variant_threads"), dict) else {}
    manifest = variant_packet.get("media_manifest") if isinstance(variant_packet.get("media_manifest"), dict) else {}
    selected_media = manifest.get("selected_media_by_platform") if isinstance(manifest.get("selected_media_by_platform"), dict) else {}
    media = media_fingerprint(variant_packet)
    payload_specs = _rehearsal_payload_specs(
        variants=variants,
        variant_threads=threads,
        selected_platforms=CURRENT_8_PLATFORMS,
        canonical_url=None,
        local_image_path=manifest.get("news_image_path") or variant_packet.get("image_path"),
        public_image_url=variant_packet.get("public_image_url"),
        selected_media=selected_media,
        article_title=str(draft.get("title") or topic),
        public_dispatch_topic_hash=topic_hash,
    )
    payload_hashes = {platform: spec.get("payload_hash") for platform, spec in payload_specs.items()}
    article_families = detect_content_families(article_text(article_packet), topic, angle, draft)
    ledger_index = ledger_family_index(ledger_rows, incident_evidence)
    blockers: list[str] = []
    if OIL_FAMILY in article_families and OIL_FAMILY in ledger_index["families"]:
        blockers.append(f"duplicate_article_family:{OIL_FAMILY}")
    if OIL_FAMILY in media["families"] and OIL_FAMILY in ledger_index["families"]:
        blockers.append(f"duplicate_media_family:{OIL_FAMILY}")
    prior_hashes = load_public_dispatch_hashes(DEFAULT_LEDGER)
    exact_hash_checks = {
        "topic_hash_seen_before": topic_hash in prior_hashes.get("topic_hashes", set()),
        "payload_hash_seen_before": sorted(
            platform for platform, payload_hash in payload_hashes.items()
            if payload_hash in prior_hashes.get("payload_hashes", set())
        ),
        "media_hash_seen_before": media["media_hash"] in prior_hashes.get("media_url_hashes", set()),
    }
    if exact_hash_checks["topic_hash_seen_before"]:
        blockers.append("duplicate_topic_hash")
    if exact_hash_checks["payload_hash_seen_before"]:
        blockers.append("duplicate_payload_hash")
    return {
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": list(dict.fromkeys(blockers)),
        "run_id": run_id,
        "topic": topic,
        "editorial_angle": angle,
        "topic_hash": topic_hash,
        "title": draft.get("title"),
        "slug": draft.get("slug_candidate"),
        "canonical_url": None,
        "canonical_packet_hash": _packet_hash(article_packet),
        "platform_variant_packet_hash": _packet_hash(variant_packet),
        "families": {
            "article": article_families,
            "media": media["families"],
            "ledger": ledger_index["families"],
        },
        "media_hash": media["media_hash"],
        "media_identity": media["media_identity"],
        "per_platform_payload_hash": payload_hashes,
        "telegram_payload_hash": payload_hashes.get("telegram"),
        "exact_hash_checks": exact_hash_checks,
        "ledger_family_matches": {
            family: ledger_index["rows_by_family"].get(family, [])
            for family in sorted(set(article_families + media["families"]))
            if family in ledger_index["rows_by_family"]
        },
    }


def triage_schedule_slots(schedule: Mapping[str, Any], ledger_rows: list[dict[str, Any]]) -> dict[str, Any]:
    del ledger_rows
    slots = [slot for slot in schedule.get("slots") or [] if isinstance(slot, Mapping)]
    evaluated: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None
    for slot in slots:
        families = detect_content_families(slot)
        blockers: list[str] = []
        review_items: list[str] = []
        if slot.get("readiness") != "READY_FOR_PIPELINE":
            blockers.append("schedule_slot_not_ready_for_pipeline")
        if OIL_FAMILY in families:
            blockers.append(f"duplicate_family_risk:{OIL_FAMILY}")
        if POLITICAL_CLAIM_FAMILY in families:
            blockers.append("politically_sensitive_unverified_claim_requires_manual_source_verification")
        if CALENDAR_FAMILY in families:
            review_items.append("multi_event_calendar_item_requires_single_topic_extraction_before_public_candidate")
        if FED_FUNDS_FAMILY in families:
            review_items.append("fresh_non_oil_central_bank_rate_update_requires_dry_run_gates")
        status = "CANDIDATE_REQUIRES_DRY_RUN" if not blockers else "BLOCKED"
        row = {
            "slot_index": slot.get("slot_index"),
            "topic": slot.get("topic"),
            "angle": slot.get("angle"),
            "readiness": slot.get("readiness"),
            "families": families,
            "status": status,
            "blockers": blockers,
            "review_items": review_items,
        }
        evaluated.append(row)
        if selected is None and status == "CANDIDATE_REQUIRES_DRY_RUN" and FED_FUNDS_FAMILY in families:
            selected = row
    if selected is None:
        selected = next((row for row in evaluated if row["status"] == "CANDIDATE_REQUIRES_DRY_RUN"), None)
    return {
        "schedule_date": schedule.get("schedule_date"),
        "slot_count": len(slots),
        "evaluated_slots": evaluated,
        "selected_fresh_slot": selected,
        "selection_status": "SELECTED_REQUIRES_DRY_RUN_GATES" if selected else "NO_SAFE_FRESH_SLOT_AVAILABLE",
    }


def repo_state() -> dict[str, Any]:
    def git(args: list[str]) -> str:
        try:
            return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            return ""

    return {
        "branch": git(["branch", "--show-current"]),
        "head": git(["rev-parse", "HEAD"]),
        "origin_master": git(["rev-parse", "origin/master"]),
        "status_short": git(["status", "--short"]),
    }


def summarize_rehearsal_evidence(path: str | Path) -> dict[str, Any]:
    data = read_json(path)
    result = data.get("pipeline_result") if isinstance(data.get("pipeline_result"), dict) else {}
    envelope = result.get("approval_marker_envelope") if isinstance(result.get("approval_marker_envelope"), dict) else {}
    return {
        "path": str(path),
        "present": bool(data),
        "evidence_packet_id": data.get("evidence_packet_id"),
        "evidence_hash": data.get("evidence_hash"),
        "task_label": data.get("task_label"),
        "run_id": result.get("run_id"),
        "pipeline_status": result.get("pipeline_status"),
        "public_write": result.get("public_write"),
        "dispatch_live": result.get("dispatch_live"),
        "dispatch_rehearsal": result.get("dispatch_rehearsal"),
        "quality_gate_result": result.get("quality_gate_result"),
        "topic_hash": envelope.get("topic_hash"),
        "canonical_packet_hash": envelope.get("canonical_packet_hash"),
        "platform_variant_packet_hash": envelope.get("platform_variant_packet_hash"),
        "telegram_payload_hash": envelope.get("telegram_payload_hash"),
        "per_platform_payload_hash": envelope.get("per_platform_payload_hash"),
    }


def inspect_python_runner_processes() -> dict[str, Any]:
    # Intentionally avoids recording command lines, which may contain paths or arguments.
    script = (
        "$pat='live_contentops\\.live_production_pipeline_runner_v6|"
        "live_production_pipeline_runner_v6\\.py|daily_editorial_scheduler_v6|"
        "active_outbox|dispatch_live';"
        "$current=$PID;"
        "$rows=Get-CimInstance Win32_Process | Where-Object { "
        "$_.ProcessId -ne $current -and $_.Name -match '^(python|python3|py)\\.exe$' "
        "-and ($_.CommandLine -match $pat) };"
        "@{matching_python_runner_count=@($rows).Count; process_ids=@($rows | "
        "Select-Object -ExpandProperty ProcessId)} | ConvertTo-Json -Compress"
    )
    try:
        raw = subprocess.check_output(["powershell", "-NoProfile", "-Command", script], text=True, stderr=subprocess.DEVNULL)
        data = json.loads(raw)
        return data if isinstance(data, dict) else {"matching_python_runner_count": None, "process_ids": []}
    except Exception:
        return {"matching_python_runner_count": None, "process_ids": [], "scan_error": "process_scan_failed"}


def build_pre_public_evidence(
    *,
    article_packet_path: str | Path = DEFAULT_ARTICLE_PACKET,
    variant_packet_path: str | Path = DEFAULT_VARIANT_PACKET,
    schedule_path: str | Path = DEFAULT_DAILY_SCHEDULE,
    ledger_path: str | Path = DEFAULT_LEDGER,
    dry_run_evidence_path: str | Path = DEFAULT_DRY_RUN_EVIDENCE,
    incident_evidence_path: str | Path = DEFAULT_INCIDENT_EVIDENCE,
    fresh_rehearsal_evidence_path: str | Path | None = DEFAULT_FRESH_REHEARSAL_EVIDENCE,
) -> dict[str, Any]:
    article_packet = read_json(article_packet_path)
    variant_packet = read_json(variant_packet_path)
    schedule = read_json(schedule_path)
    ledger_rows = read_jsonl(ledger_path)
    incident = read_json(incident_evidence_path)
    current_gate = build_current_candidate_gate(
        article_packet=article_packet,
        variant_packet=variant_packet,
        ledger_rows=ledger_rows,
        incident_evidence=incident,
    )
    schedule_triage = triage_schedule_slots(schedule, ledger_rows)
    fresh_summary = summarize_rehearsal_evidence(fresh_rehearsal_evidence_path) if fresh_rehearsal_evidence_path else {}
    fresh_rehearsal_status = str(fresh_summary.get("pipeline_status") or "")
    blockers = list(current_gate.get("blockers") or [])
    if current_gate.get("status") != "PASS":
        blockers.append("current_rehearsal_candidate_not_public_safe")
    selected_slot = schedule_triage.get("selected_fresh_slot")
    if selected_slot and not fresh_summary.get("present"):
        blockers.append("fresh_non_duplicate_slot_dry_run_gates_not_yet_run")
    elif fresh_summary.get("present") and fresh_rehearsal_status != "LIVE_READY_REQUIRES_OPERATOR_GO":
        blockers.append(f"fresh_non_duplicate_slot_dry_run_not_live_ready:{fresh_rehearsal_status or 'UNKNOWN'}")
    elif not selected_slot:
        blockers.append("fresh_non_duplicate_slot_unavailable")
    status = "PASS_PRE_PUBLIC_GATE" if not blockers else "BLOCKED_PRE_PUBLIC_GATE"
    packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "packet_kind": "v6_controlled_public_candidate_pre_public_gate_evidence",
        "created_at": utc_now(),
        "repo_state": repo_state(),
        "process_artifact_check": inspect_python_runner_processes(),
        "dry_run_rehearsal_evidence": summarize_rehearsal_evidence(dry_run_evidence_path),
        "current_candidate_duplicate_gate": current_gate,
        "schedule_fresh_slot_triage": schedule_triage,
        "fresh_slot_dry_run_rehearsal_evidence": fresh_summary,
        "pre_public_gate_status": status,
        "blockers": list(dict.fromkeys(blockers)),
        "safety": {
            "public_dispatch_performed": False,
            "public_write": False,
            "live_platform_api_called": False,
            "credential_lookup_performed": False,
            "raw_env_values_persisted": False,
            "raw_credential_values_persisted": False,
            "browser_session_values_persisted": False,
        },
        "acceptance_label": "BLOCKED_PRE_PUBLIC_GATE" if status != "PASS_PRE_PUBLIC_GATE" else "PRE_PUBLIC_GATE_PASS_REQUIRES_OPERATOR_MARKER_AND_ONE_LIVE_RUN",
    }
    packet["evidence_hash"] = stable_hash(packet)
    packet["evidence_packet_id"] = f"v6_controlled_public_preflight_{packet['evidence_hash'][:16]}"
    return packet


def write_evidence(packet: dict[str, Any], output_path: str | Path = DEFAULT_OUTPUT) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build V6 pre-public candidate gate evidence.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--fresh-rehearsal-evidence", default=str(DEFAULT_FRESH_REHEARSAL_EVIDENCE))
    args = parser.parse_args(argv)
    packet = build_pre_public_evidence(fresh_rehearsal_evidence_path=args.fresh_rehearsal_evidence)
    path = write_evidence(packet, args.output)
    print(json.dumps({
        "path": str(path),
        "pre_public_gate_status": packet["pre_public_gate_status"],
        "acceptance_label": packet["acceptance_label"],
        "blockers": packet["blockers"],
        "evidence_packet_id": packet["evidence_packet_id"],
    }, indent=2))
    return 0 if packet["pre_public_gate_status"] == "PASS_PRE_PUBLIC_GATE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
