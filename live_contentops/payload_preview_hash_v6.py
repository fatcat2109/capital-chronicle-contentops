"""V6 Payload Preview and Deterministic Hash Lane.

Processes delegated evidence candidate details to generate a review-only
exact payload preview and deterministic payload hash.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_PAYLOAD_PREVIEW_AND_HASH_LANE_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_PAYLOAD_PREVIEW_HASH")
FORBIDDEN_HASH_INPUT_TERMS = [
    "token", "secret", "chat_id", "provider_response", "env",
    "api_url", "https://api", ".env", "cookie", "session",
    "auth", "bearer", "password"
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


def generate_runbook() -> str:
    return """# V6 Payload Preview & Hash Verification Runbook

Jim, please follow these steps to verify the deterministic payload hash:

## Verification Steps
- [ ] **Step 1**: Review `payload_preview_exact_review.json` under `docs/automation/V6_PAYLOAD_PREVIEW_HASH/`.
- [ ] **Step 2**: Inspect the safe, redacted hash input keys in `payload_hash_inputs_redacted.json`.
- [ ] **Step 3**: Confirm that the payload hash record is successfully captured in `payload_hash_record.json`.
- [ ] **Step 4**: Note that changing the payload body text, platform type, source mapping, or policy parameters will automatically regenerate a new payload hash.
- [ ] **Step 5**: Once satisfied, proceed to `TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_SIGNATURE_BINDING_LANE_HEAVY_BATCH_V0`.
"""


def generate_blocker_report(status: str, blockers: list[str]) -> str:
    blocker_lines = "\n".join(f"- `{b}`" for b in blockers)
    return f"""# V6 Payload Preview Blocker Report

- **Payload Preview Status**: {status}
- **Remaining Active Blockers**:

{blocker_lines}
"""


def generate_implementation_report(status: str) -> str:
    return f"""# V6 Payload Preview & Hash Implementation Report

- **Task Label**: {TASK_LABEL}
- **Preview Status**: {status}

- **Compliance Rules**:
  - No secrets or keys in hash inputs: `true`
  - No webhook URLs or tokens in hash inputs: `true`
  - No live write or destination binding: `true`
  - No env read in this task: `true`
  - No network call in this task: `true`
  - No provider call in this task: `true`
"""


def generate_next_task_pointer(evidence_complete: bool) -> str:
    if evidence_complete:
        next_task = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_SIGNATURE_BINDING_LANE_HEAVY_BATCH_V0"
        goal = "Bind operator signatures to the validated payload hash."
    else:
        next_task = TASK_LABEL
        goal = "Complete evidence console fixture."

    return f"""# Next Task Pointer

Recommended next task at time of bundle generation (not permanent authority):

`{next_task}`

Goal: {goal}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Payload Preview & Hash Lane")
    parser.add_argument("--fixture-file", default=None)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Resolve output directories
    is_default = (args.output_dir == str(DEFAULT_OUTPUT_DIR))
    if is_default:
        target_dir = out_dir
        base_automation_dir = Path("docs/automation")
    else:
        target_dir = out_dir / "V6_PAYLOAD_PREVIEW_HASH"
        target_dir.mkdir(parents=True, exist_ok=True)
        base_automation_dir = out_dir

    # 2. Determine evidence completion
    evidence_complete = False
    source_preflight_ready = False

    # Check delegated refresh result
    delegated_result_path = base_automation_dir / "V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_refresh_result.json"
    delegated_result = load_json(delegated_result_path)
    if delegated_result:
        evidence_complete = delegated_result.get("evidence_complete", False)
        source_preflight_ready = delegated_result.get("source_preflight_ready", False)

    # Check local console fixture
    fixture_path = args.fixture_file
    if not fixture_path:
        fixture_path = str(base_automation_dir / "V6_OPERATOR_EVIDENCE_CONSOLE/operator_evidence_fixture.json")
    if Path(fixture_path).exists():
        evidence_complete = True
        source_preflight_ready = True

    # 3. Load fixture content
    fixture_data = load_json(fixture_path) or {}
    content_lane = fixture_data.get("intended_content_lane", "PLACEHOLDER_LANE")
    topic_statement = fixture_data.get("topic_statement", "PLACEHOLDER_TOPIC")
    factual_claims = fixture_data.get("factual_claims", [])
    angle = fixture_data.get("intended_canonical_article_angle", "PLACEHOLDER_ANGLE")

    # Format review-only body text
    body_text_parts = [
        f"Topic Statement: {topic_statement}",
        "Factual Claims:"
    ]
    for claim in factual_claims:
        body_text_parts.append(f"- {claim}")
    body_text_parts.append(f"Editorial Angle: {angle}")
    body_text = "\n".join(body_text_parts)

    status = "READY_FOR_OPERATOR_REVIEW" if evidence_complete else "BLOCKED_AWAITING_OPERATOR_EVIDENCE"

    # 4. Load source map and policy
    source_map_path = base_automation_dir / "V6_OPERATOR_DELEGATED_EVIDENCE_AUTHORING/delegated_evidence_source_map.json"
    source_map_data = load_json(source_map_path) or {"schema_version": "6.0.0", "source_map": {}}

    policy_packet_path = base_automation_dir / "V6_NETWORK_SCOPE_POLICY/network_scope_policy_packet.json"
    policy_data = load_json(policy_packet_path) or {"policy_packet_id": "policy_default"}

    # 5. Build exact review payload preview
    payload_preview = {
        "payload_type": "review_only_payload_preview",
        "content_lane": content_lane,
        "title": f"Review Preview: {topic_statement}",
        "body_text": body_text,
        "adapter_class": "review_only_preview",
        "payload_schema_version": SCHEMA_VERSION,
        "visibility_class": "review_only_payload_preview",
        "approval_required": True,
        "dispatch_ready": False,
        "public_postable": False,
        "human_review_required": True,
        "no_financial_advice": True,
        "no_signal_language": True,
        "is_local_only": True
    }
    write_json(target_dir / "payload_preview_exact_review.json", payload_preview)

    # 6. Build redacted hash inputs
    hash_inputs = {
        "payload_type": payload_preview["payload_type"],
        "content_lane": payload_preview["content_lane"],
        "title": payload_preview["title"],
        "body_text": payload_preview["body_text"],
        "source_map_data": source_map_data.get("source_map", {}),
        "policy_data": {
            "policy_packet_id": policy_data.get("policy_packet_id", "policy_default"),
            "violations_found": policy_data.get("violations_found", 0)
        },
        "adapter_class": payload_preview["adapter_class"],
        "payload_schema_version": payload_preview["payload_schema_version"]
    }
    write_json(target_dir / "payload_hash_inputs_redacted.json", hash_inputs)

    # 7. Validation for forbidden terms
    serialized_inputs = json.dumps(hash_inputs, sort_keys=True)
    lower_inputs = serialized_inputs.lower()
    for term in FORBIDDEN_HASH_INPUT_TERMS:
        if term in lower_inputs:
            raise ValueError(f"forbidden_hash_input_material: term '{term}' detected")

    # 8. Calculate stable deterministic hash
    payload_hash = hashlib.sha256(serialized_inputs.encode("utf-8")).hexdigest()

    # 9. payload_hash_record.json
    hash_record = {
        "payload_hash": payload_hash,
        "payload_hash_algorithm": "sha256",
        "timestamp": "2026-06-28T08:48:00Z",
        "schema_version": SCHEMA_VERSION
    }
    write_json(target_dir / "payload_hash_record.json", hash_record)

    # 10. payload_preview_hash_packet.json
    hash_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "payload_preview_status": status,
        "payload_hash_created": True,
        "exact_payload_preview_created": True,
        "evidence_complete": evidence_complete,
        "source_preflight_ready": source_preflight_ready,
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
        "next_recommended_task": "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_SIGNATURE_BINDING_LANE_HEAVY_BATCH_V0"
    }
    write_json(target_dir / "payload_preview_hash_packet.json", hash_packet)

    # Generate documents
    blockers = [
        "destination_binding_incomplete",
        "kill_switch_active",
        "live_write_authorization_missing",
        "operator_approval_incomplete",
        "outbox_creation_blocked",
        "safety_review_incomplete"
    ]
    (target_dir / "payload_preview_blocker_report.md").write_text(generate_blocker_report(status, blockers), encoding="utf-8")
    (target_dir / "payload_preview_runbook.md").write_text(generate_runbook(), encoding="utf-8")
    (target_dir / "implementation_report.md").write_text(generate_implementation_report(status), encoding="utf-8")
    (target_dir / "next_task_pointer.md").write_text(generate_next_task_pointer(evidence_complete), encoding="utf-8")

    print(json.dumps({
        "payload_preview_status": status,
        "payload_hash_created": True,
        "payload_hash": payload_hash
    }, indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
