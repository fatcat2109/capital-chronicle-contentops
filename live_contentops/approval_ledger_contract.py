"""Approval ledger contract (LOCAL APPEND-ONLY FIXTURE OUTPUT)."""

import copy
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import approval_ledger_policy as policy
from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174XN_XO_XP_APPROVAL_LEDGER_CONTRACT_V0"
MODEL = "APPROVAL_LEDGER_CONTRACT_0174XN_XO_XP"
MODEL_VERSION = "0174XN_XO_XP_APPROVAL_LEDGER_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "a763e3aaa1cf079a472b9fe0f8748c36dae60a50"
DOC_REL_DIR = os.path.join("docs", "automation", "0174XN_XO_XP")
SOURCE_DIR = os.path.join("docs", "automation", "0174XK_XL_XM")
VARIANT_PACKET = os.path.join("docs", "automation", "0174XH_XI_XJ", "primary_platform_variant_dry_run_packet.json")
DISPATCH_REGISTRY = os.path.join("docs", "automation", "0174WY_WZ_XA", "telegram_supervised_dispatch_capability_registry_packet.json")
CANDIDATES = os.path.join(SOURCE_DIR, "approval_challenge_candidate_fixture_outputs.json")
CANDIDATE_CONTRACT = os.path.join(SOURCE_DIR, "approval_challenge_candidate_contract_packet.json")
CANDIDATE_POLICY = os.path.join(SOURCE_DIR, "approval_challenge_policy_packet.json")
NEXT_LEDGER = os.path.join(SOURCE_DIR, "next_approval_ledger_contract_packet.json")
RESPONSE_FIXTURES = "approval_response_fixture_inputs.json"
LEDGER_OUTPUTS = "approval_ledger_fixture_outputs.json"
CONTRACT_PACKET = "approval_ledger_contract_packet.json"
CONTRACT_DOC = "approval_ledger_contract.md"
NEXT_PACKET = "next_dispatch_outbox_candidate_contract_packet.json"
NEXT_DOC = "next_dispatch_outbox_candidate_contract.md"
NEXT_BATCH_PROMPT = "TASK_CONTENTOPS_0174XQ_XR_XS_DISPATCH_OUTBOX_CANDIDATE_CONTRACT_V0"


def _read_json(repo_root, rel_path):
    return json.loads((pathlib.Path(repo_root) / rel_path).read_text(encoding="utf-8"))


def load_inputs(repo_root="."):
    return {
        "candidates": _read_json(repo_root, CANDIDATES),
        "candidate_contract": _read_json(repo_root, CANDIDATE_CONTRACT),
        "candidate_policy": _read_json(repo_root, CANDIDATE_POLICY),
        "next_ledger": _read_json(repo_root, NEXT_LEDGER),
        "variant_packet": _read_json(repo_root, VARIANT_PACKET),
        "dispatch_registry": _read_json(repo_root, DISPATCH_REGISTRY),
    }


def _response(response_id, candidate, response_class, order, hash_short=None, replay="not_replay"):
    return {
        "response_id": response_id,
        "source_challenge_candidate_id": candidate["challenge_candidate_id"],
        "operator_id": "jim_operator_fixture",
        "response_channel": "telegram_future_fixture" if candidate["challenge_channel"] == "telegram_future" else "local_ui_fixture",
        "response_text_redacted": response_class.replace("explicit_", "").replace("_", " "),
        "response_class": response_class,
        "response_payload_hash_short": hash_short or candidate["payload_hash_short"],
        "received_at_order": order,
        "replay_status": replay,
        "redaction_status": "redacted",
        "trust_status": "untrusted_input_until_validated",
    }


def build_response_fixtures(candidates):
    by_class = {c["payload_class"]: c for c in candidates}
    fixtures = [
        _response("resp_001_approve", by_class["substack_newsletter_issue"], "explicit_approve", 1),
        _response("resp_002_reject", by_class["substack_longform_post"], "explicit_reject", 2),
        _response("resp_003_edit", by_class["x_short_post"], "explicit_edit_request", 3),
        _response("resp_004_hold", by_class["x_thread"], "explicit_hold", 4),
        _response("resp_005_ambiguous", by_class["telegram_channel_update"], "ambiguous", 5),
        _response("resp_006_hash_mismatch", by_class["telegram_operator_review_message"], "explicit_approve", 6, "000000000000"),
        {
            "response_id": "resp_007_unknown_challenge",
            "source_challenge_candidate_id": "unknown_challenge_candidate_fixture",
            "operator_id": "jim_operator_fixture",
            "response_channel": "local_ui_fixture",
            "response_text_redacted": "approve unknown",
            "response_class": "explicit_approve",
            "response_payload_hash_short": "111111111111",
            "received_at_order": 7,
            "replay_status": "not_replay",
            "redaction_status": "redacted",
            "trust_status": "untrusted_input_until_validated",
        },
        _response("resp_008_replay", by_class["substack_newsletter_issue"], "explicit_approve", 8, replay="replay"),
    ]
    return fixtures


def _blank_candidate(response):
    return {
        "challenge_candidate_id": response["source_challenge_candidate_id"],
        "source_payload_id": None,
        "source_brief_id": None,
        "source_intent_id": None,
        "platform": None,
        "payload_class": None,
        "payload_hash": None,
        "payload_hash_short": response.get("response_payload_hash_short"),
        "destination_binding_id": None,
        "credential_handle_id": None,
        "expires_policy": "future_required_not_active",
        "human_review_required": True,
        "no_financial_advice": True,
        "no_signal_language": True,
    }


def audit_hash_material(response, candidate, event_class, blocked_reasons, policy_packet):
    material = {
        "response_id": response["response_id"],
        "response_text_redacted": response["response_text_redacted"],
        "response_class": response["response_class"],
        "payload_hash": candidate.get("payload_hash"),
        "payload_hash_short": candidate.get("payload_hash_short"),
        "platform": candidate.get("platform"),
        "destination_binding_id": candidate.get("destination_binding_id"),
        "event_class": event_class,
        "blocked_reasons": blocked_reasons,
        "policy_checksum": policy_packet["approval_ledger_policy_checksum"],
    }
    return material


def compute_audit_hash(response, candidate, event_class, blocked_reasons, policy_packet):
    return adapter.compute_checksum(audit_hash_material(response, candidate, event_class, blocked_reasons, policy_packet))


def build_ledger_event(response, candidate, contract_packet, policy_packet):
    event_class, blocked_reasons = policy.classify_response(response, candidate, contract_packet)
    candidate = candidate or _blank_candidate(response)
    entry = {
        "ledger_entry_id": f"ledger_{response['response_id']}_{event_class}",
        "ledger_event_class": event_class,
        "approved_at_order": response["received_at_order"] if event_class == "approval_candidate" else None,
        "operator_id": response["operator_id"],
        "approval_channel": response["response_channel"],
        "source_challenge_candidate_id": response["source_challenge_candidate_id"],
        "source_payload_id": candidate.get("source_payload_id"),
        "source_brief_id": candidate.get("source_brief_id"),
        "source_intent_id": candidate.get("source_intent_id"),
        "platform": candidate.get("platform"),
        "payload_class": candidate.get("payload_class"),
        "payload_hash": candidate.get("payload_hash"),
        "payload_hash_short": candidate.get("payload_hash_short"),
        "destination_binding_id": candidate.get("destination_binding_id"),
        "credential_handle_id": candidate.get("credential_handle_id"),
        "media_manifest_hash": None,
        "approval_text_redacted": response["response_text_redacted"],
        "approval_method": "challenge_response_fixture",
        "prior_payload_hash": None,
        "revoked": False,
        "expiration_policy": "future_required_not_active",
        "valid_for_dispatch": False,
        "eligible_for_outbox_candidate": policy.eligible_for_outbox_candidate(event_class, blocked_reasons),
        "blocked_reasons": blocked_reasons,
        "human_review_required": True,
        "no_financial_advice": True,
        "no_signal_language": True,
        "public_postable": False,
        "can_dispatch": False,
        "can_create_outbox": False,
        "platform_api_called": False,
        "response_payload_hash_short": response["response_payload_hash_short"],
        **policy.safety_flags(),
    }
    entry["audit_hash"] = compute_audit_hash(response, candidate, event_class, blocked_reasons, policy_packet)
    policy.validate_no_forbidden_material(entry)
    return entry


def build_ledger_events(responses, candidates, candidate_contract, policy_packet):
    by_id = {c["challenge_candidate_id"]: c for c in candidates}
    events = []
    for response in responses:
        events.append(build_ledger_event(response, by_id.get(response["source_challenge_candidate_id"]), candidate_contract, policy_packet))
    return events


def build_blocked_proof_events(candidates, candidate_contract, policy_packet):
    blocked_ids = policy.blocked_proof_brief_ids(candidate_contract)
    events = []
    for order, brief_id in enumerate(sorted(blocked_ids), start=100):
        pseudo = {
            "challenge_candidate_id": f"blocked_proof_{brief_id}",
            "source_payload_id": None,
            "source_brief_id": brief_id,
            "source_intent_id": None,
            "platform": "blocked_fixture",
            "payload_class": "blocked_source_brief_proof",
            "payload_hash": "blocked_proof_no_payload_hash",
            "payload_hash_short": "blockedproof",
            "destination_binding_id": "symbolic_fixture_only",
            "credential_handle_id": "symbolic_fixture_only",
            "expires_policy": "future_required_not_active",
        }
        response = {
            "response_id": f"resp_blocked_{brief_id}",
            "source_challenge_candidate_id": pseudo["challenge_candidate_id"],
            "operator_id": "jim_operator_fixture",
            "response_channel": "local_ui_fixture",
            "response_text_redacted": "approve blocked proof",
            "response_class": "explicit_approve",
            "response_payload_hash_short": pseudo["payload_hash_short"],
            "received_at_order": order,
            "replay_status": "not_replay",
            "redaction_status": "redacted",
            "trust_status": "untrusted_input_until_validated",
        }
        events.append(build_ledger_event(response, pseudo, candidate_contract, policy_packet))
    return events


def event_counts(events):
    counts = {"approval_candidate": 0, "rejected_event": 0, "edit_request_event": 0, "hold_event": 0, "blocked_event": 0}
    for event in events:
        counts[event["ledger_event_class"]] += 1
    return counts


def build_contract_packet(inputs, responses, events, policy_packet):
    counts = event_counts(events)
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "approval_challenge_candidate_contract_checksum": inputs["candidate_contract"]["approval_challenge_candidate_contract_checksum"],
        "approval_challenge_policy_checksum": inputs["candidate_policy"]["approval_challenge_policy_checksum"],
        "next_approval_ledger_contract_checksum": inputs["next_ledger"]["next_approval_ledger_contract_checksum"],
        "primary_variant_dry_run_checksum": inputs["variant_packet"]["primary_variant_dry_run_checksum"],
        "telegram_dispatch_registry_checksum": inputs["dispatch_registry"]["registry_checksum"],
        "response_fixture_count": len(responses),
        "ledger_event_count": len(events),
        "approved_entry_count": counts["approval_candidate"],
        "rejected_event_count": counts["rejected_event"],
        "edit_event_count": counts["edit_request_event"],
        "hold_event_count": counts["hold_event"],
        "blocked_event_count": counts["blocked_event"],
        "hash_mismatch_blocked_proof": any("payload_hash_short_mismatch" in e["blocked_reasons"] for e in events),
        "unknown_challenge_blocked_proof": any("unknown_challenge_candidate" in e["blocked_reasons"] for e in events),
        "replay_blocked_proof": any("replayed_response" in e["blocked_reasons"] for e in events),
        "blocked_source_brief_proof": sorted(policy.blocked_proof_brief_ids(inputs["candidate_contract"])),
        "all_can_dispatch_false": all(e["can_dispatch"] is False for e in events),
        "all_can_create_outbox_false": all(e["can_create_outbox"] is False for e in events),
        "all_public_postable_false": all(e["public_postable"] is False for e in events),
        "all_valid_for_dispatch_false": all(e["valid_for_dispatch"] is False for e in events),
        "approval_eligible_entries_bind_exact_hash": all(e["payload_hash_short"] == e["response_payload_hash_short"] for e in events if e["eligible_for_outbox_candidate"]),
        "status": "pass",
    }
    packet["approval_response_fixture_checksum"] = adapter.compute_checksum(responses)
    packet["approval_ledger_fixture_outputs_checksum"] = adapter.compute_checksum(events)
    packet["approval_ledger_contract_checksum"] = adapter.compute_checksum(packet)
    return packet


def build_next_packet(contract_packet, policy_packet):
    packet = {
        "task_label": NEXT_BATCH_PROMPT,
        "model": "NEXT_DISPATCH_OUTBOX_CANDIDATE_CONTRACT_0174XN_XO_XP",
        "model_version": "0174XN_XO_XP_NEXT_DISPATCH_OUTBOX_CANDIDATE_CONTRACT_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "next_batch_prompt": NEXT_BATCH_PROMPT,
        "next_scope": "dispatch_outbox_candidate_contract_local_only",
        "allowed_inputs": ["approval_ledger_candidate_entry", "payload_hash", "symbolic_destination_binding", "symbolic_credential_handle"],
        "forbidden_outputs": ["live_dispatch", "platform_api_call", "credential_access", "public_postable_content"],
        "approval_ledger_contract_checksum": contract_packet["approval_ledger_contract_checksum"],
        "approval_ledger_policy_checksum": policy_packet["approval_ledger_policy_checksum"],
        "approval_ledger_fixture_outputs_checksum": contract_packet["approval_ledger_fixture_outputs_checksum"],
    }
    packet["next_dispatch_outbox_candidate_contract_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(title, packet):
    lines = [f"# {title}", "", "> [!IMPORTANT]", "> Local append-only approval ledger fixtures only. No dispatch, no outbox creation, no platform/provider call, no network, no credential/env read.", ""]
    for key in sorted(packet):
        value = packet[key]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, sort_keys=True)
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def _assert_safe_output(repo_root, output_dir):
    root = pathlib.Path(repo_root).resolve()
    out = pathlib.Path(output_dir).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    if out != allowed:
        raise ValueError("unsafe_output_path_refused")
    return out


def write_artifacts(repo_root=".", output_dir=None):
    output_dir = output_dir or (pathlib.Path(repo_root) / DOC_REL_DIR)
    out = _assert_safe_output(repo_root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    policy_packet = policy.write_artifacts(repo_root)
    inputs = load_inputs(repo_root)
    responses = build_response_fixtures(inputs["candidates"])
    events = build_ledger_events(responses, inputs["candidates"], inputs["candidate_contract"], policy_packet)
    events.extend(build_blocked_proof_events(inputs["candidates"], inputs["candidate_contract"], policy_packet))
    contract_packet = build_contract_packet(inputs, responses, events, policy_packet)
    next_packet = build_next_packet(contract_packet, policy_packet)
    (out / RESPONSE_FIXTURES).write_text(adapter.serialize(responses), encoding="utf-8", newline="\n")
    (out / LEDGER_OUTPUTS).write_text(adapter.serialize(events), encoding="utf-8", newline="\n")
    (out / CONTRACT_PACKET).write_text(adapter.serialize(contract_packet), encoding="utf-8", newline="\n")
    (out / CONTRACT_DOC).write_text(render_doc("Approval Ledger Contract", contract_packet), encoding="utf-8", newline="\n")
    (out / NEXT_PACKET).write_text(adapter.serialize(next_packet), encoding="utf-8", newline="\n")
    (out / NEXT_DOC).write_text(render_doc("Next Dispatch Outbox Candidate Contract", next_packet), encoding="utf-8", newline="\n")
    return copy.deepcopy({"responses": responses, "events": events, "contract_packet": contract_packet, "policy_packet": policy_packet, "next_packet": next_packet})


if __name__ == "__main__":
    result = write_artifacts(".")
    print("APPROVAL_LEDGER_CONTRACT_CHECKSUM", result["contract_packet"]["approval_ledger_contract_checksum"])
    print("APPROVAL_LEDGER_POLICY_CHECKSUM", result["policy_packet"]["approval_ledger_policy_checksum"])
    print("APPROVAL_RESPONSE_FIXTURE_CHECKSUM", result["contract_packet"]["approval_response_fixture_checksum"])
    print("APPROVAL_LEDGER_FIXTURE_OUTPUTS_CHECKSUM", result["contract_packet"]["approval_ledger_fixture_outputs_checksum"])
    print("NEXT_DISPATCH_OUTBOX_CANDIDATE_CONTRACT_CHECKSUM", result["next_packet"]["next_dispatch_outbox_candidate_contract_checksum"])
