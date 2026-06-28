"""V6 Payload Preview and Deterministic Hash Lane.

Processes committed delegated evidence artifacts to generate an exact review-only
payload preview and deterministic payload hash when safe non-placeholder content
can be produced.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_PAYLOAD_PREVIEW_AND_HASH_LANE_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"
BLOCKED_STATUS = "BLOCKED_EXACT_PAYLOAD_MISSING"
READY_STATUS = "READY_FOR_OPERATOR_REVIEW"
NEXT_APPROVAL_TASK = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_SIGNATURE_BINDING_LANE_HEAVY_BATCH_V0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_PAYLOAD_PREVIEW_HASH")
DEFAULT_SOURCE_MAP_REF = "docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_source_map.json"
DEFAULT_SUMMARY_REF = "docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_fixture_redacted_summary.json"
DEFAULT_REFRESH_REF = "docs/automation/V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_refresh_result.json"

FORBIDDEN_HASH_INPUT_TERMS = [
    "placeholder",
    "token",
    "secret",
    "webhook",
    "chat_id",
    "provider_response",
    "api_key",
    "auth header",
    "authorization",
    "bearer",
    "password",
    "cookie",
    "session",
    "localstorage",
    "sessionstorage",
    ".env",
    "appdata",
    "c:\\users\\",
    "a:\\",
    "http://",
    "https://",
    "fake public url",
    "fake market number",
    "fake metric",
    "buy signal",
    "sell signal",
]


def write_json(path: str | Path, data: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any] | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return "placeholder" in value.lower()
    if isinstance(value, dict):
        return any(contains_placeholder(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(contains_placeholder(v) for v in value)
    return False


def ensure_forbidden_terms_absent(data: Any) -> None:
    if isinstance(data, str):
        serialized = data.lower()
        for term in FORBIDDEN_HASH_INPUT_TERMS:
            if term in serialized:
                raise ValueError(f"forbidden_hash_input_material: term '{term}' detected")
        return
    if isinstance(data, dict):
        for value in data.values():
            ensure_forbidden_terms_absent(value)
        return
    if isinstance(data, (list, tuple, set)):
        for value in data:
            ensure_forbidden_terms_absent(value)



def compute_payload_hash(hash_inputs: dict[str, Any]) -> str:
    serialized = json.dumps(hash_inputs, sort_keys=True)
    ensure_forbidden_terms_absent(hash_inputs)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def generate_runbook(status: str) -> str:
    next_task = NEXT_APPROVAL_TASK if status == READY_STATUS else TASK_LABEL
    return f"""# V6 Payload Preview & Hash Verification Runbook

Jim, follow these steps to verify payload preview truth and deterministic hash state:

## Verification Steps
- [ ] **Step 1**: Review `payload_preview_exact_review.json` under `docs/automation/V6_PAYLOAD_PREVIEW_HASH/`.
- [ ] **Step 2**: Confirm the preview uses committed delegated evidence summary facts only.
- [ ] **Step 3**: Inspect `payload_hash_inputs_redacted.json` for deterministic safe inputs only.
- [ ] **Step 4**: If status is `{READY_STATUS}`, confirm `payload_hash_record.json` matches the preview inputs exactly.
- [ ] **Step 5**: If status is `{BLOCKED_STATUS}`, keep this lane blocked and do not advance approval binding.
- [ ] **Step 6**: Next recommended task remains `{next_task}`.
"""


def generate_blocker_report(status: str, blockers: list[str]) -> str:
    blocker_lines = "\n".join(f"- `{b}`" for b in blockers)
    return f"""# V6 Payload Preview Blocker Report

- **Payload Preview Status**: {status}
- **Remaining Active Blockers**:

{blocker_lines}
"""


def generate_implementation_report(status: str, preview_created: bool, hash_created: bool) -> str:
    return f"""# V6 Payload Preview & Hash Implementation Report

- **Task Label**: {TASK_LABEL}
- **Preview Status**: {status}
- **Exact Payload Preview Created**: `{str(preview_created).lower()}`
- **Payload Hash Created**: `{str(hash_created).lower()}`

- **Compliance Rules**:
  - No secrets or keys in hash inputs: `true`
  - No webhook URLs or tokens in hash inputs: `true`
  - No live write or destination binding: `true`
  - No env read in this task: `true`
  - No network call in this task: `true`
  - No provider call in this task: `true`
  - No placeholder content accepted as exact payload truth: `true`
"""


def generate_next_task_pointer(preview_created: bool, hash_created: bool) -> str:
    if preview_created and hash_created:
        next_task = NEXT_APPROVAL_TASK
        goal = "Bind operator signatures to validated exact payload hash."
    else:
        next_task = TASK_LABEL
        goal = "Repair or complete exact safe payload preview inputs without placeholders."

    return f"""# Next Task Pointer

Recommended next task at time of bundle generation (not permanent authority):

`{next_task}`

Goal: {goal}
"""


def build_safe_preview(
    summary_data: dict[str, Any] | None,
    source_map_data: dict[str, Any] | None,
    refresh_data: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, list[str]]:
    blockers = [
        "destination_binding_incomplete",
        "kill_switch_active",
        "live_write_authorization_missing",
        "operator_approval_incomplete",
        "outbox_creation_blocked",
        "safety_review_incomplete",
    ]
    missing_reasons: list[str] = []

    if not summary_data:
        missing_reasons.append("delegated_summary_missing")
    if not source_map_data:
        missing_reasons.append("delegated_source_map_missing")
    if not refresh_data:
        missing_reasons.append("delegated_refresh_result_missing")

    if missing_reasons:
        return None, blockers + missing_reasons

    fixture_completions = summary_data.get("fixture_completions", {})
    required_completion_keys = [
        "citation_candidates",
        "factual_claims",
        "intended_canonical_article_angle",
        "intended_content_lane",
        "no_signal_disclosure",
        "operator_idea_source_ref",
        "supporting_artifacts",
        "topic_statement",
    ]
    missing_completion_keys = [key for key in required_completion_keys if fixture_completions.get(key) is not True]
    if missing_completion_keys:
        return None, blockers + [f"missing_safe_completion:{key}" for key in missing_completion_keys]

    evidence_complete = refresh_data.get("evidence_complete") is True
    source_preflight_ready = refresh_data.get("source_preflight_ready") is True
    verification_state = summary_data.get("verification_state") == "PASS"
    safe_summary = (
        summary_data.get("contains_secrets_or_credentials") is False
        and summary_data.get("contains_webhooks_or_cookies") is False
    )
    source_map = source_map_data.get("source_map", {})
    source_map_refs = sorted(
        {
            ref
            for refs in source_map.values()
            if isinstance(refs, list)
            for ref in refs
            if isinstance(ref, str) and ref.startswith("docs/automation/") and "placeholder" not in ref.lower()
        }
    )

    if not evidence_complete:
        return None, blockers + ["evidence_incomplete"]
    if not source_preflight_ready:
        return None, blockers + ["source_preflight_not_ready"]
    if not verification_state:
        return None, blockers + ["delegated_summary_not_verified"]
    if not safe_summary:
        return None, blockers + ["delegated_summary_not_safe"]
    if not source_map_refs:
        return None, blockers + ["safe_source_map_refs_missing"]

    factual_claims_count = int(summary_data.get("factual_claims_count", 0))
    citation_candidates_count = int(summary_data.get("citation_candidates_count", 0))
    preview_blockers = [
        "live_write_scope_missing" if blocker == "live_write_authorization_missing" else blocker
        for blocker in blockers
    ]
    preview_lines = [
        "Review scope: internal operator payload approval preview only.",
        f"evidence_complete={str(evidence_complete).lower()}",
        f"source_preflight_ready={str(source_preflight_ready).lower()}",
        f"verification_state={summary_data.get('verification_state', 'UNKNOWN')}",
        f"factual_claims_count={factual_claims_count}",
        f"citation_candidates_count={citation_candidates_count}",
        f"source_map_refs={', '.join(source_map_refs)}",
        "no_signal_disclosure=verified",
        "no_financial_advice_disclosure=verified",
        f"remaining_blockers={', '.join(preview_blockers)}",
    ]
    payload_preview = {
        "payload_type": "review_only_payload_preview",
        "content_lane": "operator_internal_review",
        "title": "Review Preview: V6 delegated evidence candidate is ready for payload approval",
        "body_text": "\n".join(preview_lines),
        "adapter_class": "review_only_preview",
        "payload_schema_version": SCHEMA_VERSION,
        "visibility_class": "review_only_payload_preview",
        "approval_required": True,
        "dispatch_ready": False,
        "public_postable": False,
        "human_review_required": True,
        "no_financial_advice": True,
        "no_signal_language": True,
        "is_local_only": True,
        "source_summary_ref": DEFAULT_SUMMARY_REF,
        "source_map_ref": DEFAULT_SOURCE_MAP_REF,
        "refresh_result_ref": DEFAULT_REFRESH_REF,
    }
    if contains_placeholder(payload_preview):
        return None, blockers + ["placeholder_detected_in_preview"]
    return payload_preview, blockers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Payload Preview & Hash Lane")
    parser.add_argument("--fixture-file", default=None)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    is_default = args.output_dir == str(DEFAULT_OUTPUT_DIR)
    if is_default:
        target_dir = out_dir
        base_automation_dir = Path("docs/automation")
    else:
        target_dir = out_dir / "V6_PAYLOAD_PREVIEW_HASH"
        target_dir.mkdir(parents=True, exist_ok=True)
        base_automation_dir = out_dir

    summary_data = load_json(base_automation_dir / "V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_fixture_redacted_summary.json")
    source_map_data = load_json(base_automation_dir / "V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_source_map.json")
    refresh_data = load_json(base_automation_dir / "V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_refresh_result.json")

    payload_preview, blockers = build_safe_preview(summary_data, source_map_data, refresh_data)
    preview_created = payload_preview is not None
    hash_created = False
    payload_hash = None
    status = READY_STATUS if preview_created else BLOCKED_STATUS

    if preview_created:
        hash_inputs = {
            "adapter_class": payload_preview["adapter_class"],
            "body_text": payload_preview["body_text"],
            "content_lane": payload_preview["content_lane"],
            "payload_schema_version": payload_preview["payload_schema_version"],
            "payload_type": payload_preview["payload_type"],
            "policy_data": {
                "contains_secrets_or_credentials": summary_data.get("contains_secrets_or_credentials", False),
                "contains_webhooks_or_cookies": summary_data.get("contains_webhooks_or_cookies", False),
                "verification_state": summary_data.get("verification_state", "UNKNOWN"),
            },
            "refresh_result": {
                "approval_valid_for_dispatch": refresh_data.get("approval_valid_for_dispatch", False),
                "dispatch_allowed_now": refresh_data.get("dispatch_allowed_now", False),
                "evidence_complete": refresh_data.get("evidence_complete", False),
                "live_write_allowed_now": refresh_data.get("live_write_allowed_now", False),
                "source_preflight_ready": refresh_data.get("source_preflight_ready", False),
            },
            "source_map_refs": sorted(
                {
                    ref
                    for refs in (source_map_data or {}).get("source_map", {}).values()
                    if isinstance(refs, list)
                    for ref in refs
                    if isinstance(ref, str)
                }
            ),
            "summary_counts": {
                "citation_candidates_count": summary_data.get("citation_candidates_count", 0),
                "factual_claims_count": summary_data.get("factual_claims_count", 0),
            },
            "title": payload_preview["title"],
        }
        if contains_placeholder(hash_inputs):
            raise ValueError("forbidden_hash_input_material: placeholder detected")
        payload_hash = compute_payload_hash(hash_inputs)
        hash_created = True
    else:
        payload_preview = {
            "payload_type": "review_only_payload_preview",
            "content_lane": "operator_internal_review",
            "title": "Review Preview: exact safe payload unavailable",
            "body_text": (
                "Exact review payload could not be produced from committed delegated evidence artifacts.\n"
                f"payload_preview_status={BLOCKED_STATUS}\n"
                f"remaining_blockers={', '.join(blockers)}"
            ),
            "adapter_class": "review_only_preview",
            "payload_schema_version": SCHEMA_VERSION,
            "visibility_class": "review_only_payload_preview",
            "approval_required": True,
            "dispatch_ready": False,
            "public_postable": False,
            "human_review_required": True,
            "no_financial_advice": True,
            "no_signal_language": True,
            "is_local_only": True,
            "source_summary_ref": DEFAULT_SUMMARY_REF,
            "source_map_ref": DEFAULT_SOURCE_MAP_REF,
            "refresh_result_ref": DEFAULT_REFRESH_REF,
        }
        hash_inputs = {
            "hash_blocked": True,
            "reason": BLOCKED_STATUS,
            "safe_committed_refs": [DEFAULT_SUMMARY_REF, DEFAULT_SOURCE_MAP_REF, DEFAULT_REFRESH_REF],
            "remaining_blockers": blockers,
        }

    write_json(target_dir / "payload_preview_exact_review.json", payload_preview)
    write_json(target_dir / "payload_hash_inputs_redacted.json", hash_inputs)

    hash_record = {
        "payload_hash": payload_hash,
        "payload_hash_algorithm": "sha256" if hash_created else None,
        "schema_version": SCHEMA_VERSION,
        "timestamp": "2026-06-28T08:48:00Z",
    }
    write_json(target_dir / "payload_hash_record.json", hash_record)

    refresh_data = refresh_data or {}
    hash_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "payload_preview_status": status,
        "payload_hash_created": hash_created,
        "exact_payload_preview_created": preview_created,
        "evidence_complete": refresh_data.get("evidence_complete", False),
        "source_preflight_ready": refresh_data.get("source_preflight_ready", False),
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "outbox_entry_created": False,
        "destination_binding_complete": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True,
        "payload_hash": payload_hash,
        "next_recommended_task": NEXT_APPROVAL_TASK if hash_created else TASK_LABEL,
    }
    write_json(target_dir / "payload_preview_hash_packet.json", hash_packet)

    (target_dir / "payload_preview_blocker_report.md").write_text(generate_blocker_report(status, blockers), encoding="utf-8")
    (target_dir / "payload_preview_runbook.md").write_text(generate_runbook(status), encoding="utf-8")
    (target_dir / "implementation_report.md").write_text(
        generate_implementation_report(status, preview_created, hash_created),
        encoding="utf-8",
    )
    (target_dir / "next_task_pointer.md").write_text(
        generate_next_task_pointer(preview_created, hash_created),
        encoding="utf-8",
    )

    print(json.dumps({
        "payload_preview_status": status,
        "payload_hash_created": hash_created,
        "payload_hash": payload_hash,
    }, indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
