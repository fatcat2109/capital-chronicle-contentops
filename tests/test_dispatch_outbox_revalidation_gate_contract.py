from dataclasses import replace
from pathlib import Path

import pytest

from live_contentops import approval_ledger_revocation_expiration_contract as ua
from live_contentops import dispatch_outbox_revalidation_gate_contract as gate
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit


def _hash(label="payload"):
    return gate._digest({"fixture": label})


def _approval(*, revoked=False, expired=False):
    payload_hash = _hash()
    fact = {
        "approval_ledger_entry_id": "approval_entry_test",
        "payload_hash": payload_hash,
        "platform_id": "telegram_channel_destination",
        "payload_class_id": "telegram_channel_update",
        "destination_binding_id": "destination:telegram_channel:redacted",
        "credential_handle_id": "credential_handle:telegram:redacted",
        "approved_by_operator_ref": "operator:jim:redacted",
        "evidence_refs": ("fixture:approval",),
    }
    window = ua.build_validity_window(fact, approved_at_epoch=100, max_valid_duration_seconds=100)
    expiration = ua.build_expiration_fact(window, evaluated_at_epoch=250 if expired else 150)
    revocations = ()
    if revoked:
        revocations = (ua.build_revocation_fact(
            approval_ledger_entry_id=window.approval_ledger_entry_id,
            revoked_payload_hash=window.approval_payload_hash,
            revoked_by_operator_ref="operator:jim:redacted",
            revoked_at_epoch=125,
            revocation_reason_class="manual_hold",
        ),)
    assessment = ua.assess_approval_validity(
        validity_window=window,
        candidate_payload_hash=window.approval_payload_hash,
        candidate_platform_id=window.platform_id,
        candidate_payload_class_id=window.payload_class_id,
        candidate_destination_binding_id=window.destination_binding_id,
        candidate_credential_handle_id=window.credential_handle_id,
        evaluated_at_epoch=150,
        revocation_facts=revocations,
        expiration_fact=expiration,
    )
    return window, assessment


def _candidate(**overrides):
    window, _ = _approval()
    data = {
        "outbox_entry_id": "outbox_entry_test",
        "outbox_idempotency_key": "idempotency:test:redacted",
        "payload_hash": window.approval_payload_hash,
        "platform_id": window.platform_id,
        "payload_class_id": window.payload_class_id,
        "destination_binding_id": window.destination_binding_id,
        "credential_handle_id": window.credential_handle_id,
        "approval_ledger_entry_id": window.approval_ledger_entry_id,
        "approval_payload_hash": window.approval_payload_hash,
        "policy_version": "policy:test",
        "requested_dispatch_epoch": 150,
        "evidence_refs": ("fixture:outbox",),
    }
    data.update(overrides)
    return gate.build_revalidation_candidate(data)


def _kill(**overrides):
    params = {"evaluated_at_epoch": 150}
    params.update(overrides)
    return gate.build_kill_switch_state(**params)


def _policy(**overrides):
    params = {
        "policy_version": "policy:test",
        "platform_id": "telegram_channel_destination",
        "payload_class_id": "telegram_channel_update",
    }
    params.update(overrides)
    return gate.build_policy_gate_state(**params)


def _chain(candidate=None, *, broken=False, unredacted=False):
    candidate = candidate or _candidate()
    payload = gate._asdict(candidate)
    if unredacted:
        payload["raw_token"] = "token=secret-value"
    entry = audit.build_redacted_ledger_entry(
        entry_sequence=1,
        previous_entry_hash=audit.GENESIS_HASH,
        entry_family="dispatch_outbox_fact",
        source_model="0174UB",
        source_model_version=gate.MODEL_VERSION,
        payload=payload,
        created_at_epoch=150,
    )
    if broken:
        entry = replace(entry, previous_entry_hash="1" * 64)
    return audit.build_ledger_chain((entry,))


def _result(candidate=None, assessment=None, kill=None, policy=None, chain=None, **kwargs):
    candidate = candidate or _candidate()
    if assessment is None:
        _, assessment = _approval()
    return gate.revalidate_dispatch_candidate(
        candidate=candidate,
        approval_assessment=assessment,
        kill_switch_state=kill or _kill(),
        policy_gate_state=policy or _policy(),
        audit_chain=chain if chain is not None else _chain(candidate),
        **kwargs,
    )


def test_revalidation_candidate_builds_deterministically():
    assert _candidate() == _candidate()
    assert _candidate().candidate_id.startswith("dispatch_revalidation_candidate_")


def test_exact_payload_hash_match_required_and_happy_still_future_gate():
    result = _result()
    assert result.payload_hash_match is True
    assert result.revalidation_status == gate.STATUS_LOCAL_REVALIDATED_FUTURE_GATE
    assert result.can_dispatch is False
    assert result.dispatch_ready is False
    assert result.public_postable is False
    assert gate.BLOCK_FUTURE_SEND_GATE_REQUIRED in result.blocked_reasons


def test_payload_hash_mismatch_blocks():
    candidate = _candidate(payload_hash=_hash("different"))
    result = _result(candidate=candidate, chain=_chain(candidate))
    assert result.revalidation_status == gate.STATUS_BLOCKED
    assert gate.BLOCK_PAYLOAD_HASH_MISMATCH in result.blocked_reasons


def test_unknown_platform_blocks():
    candidate = _candidate(platform_id="unknown_platform")
    result = _result(candidate=candidate, chain=_chain(candidate))
    assert gate.BLOCK_UNKNOWN_PLATFORM in result.blocked_reasons


def test_unknown_payload_class_blocks():
    candidate = _candidate(payload_class_id="unknown_payload")
    result = _result(candidate=candidate, chain=_chain(candidate))
    assert gate.BLOCK_UNKNOWN_PAYLOAD_CLASS in result.blocked_reasons


def test_incompatible_platform_payload_class_blocks():
    candidate = _candidate(platform_id="x", payload_class_id="telegram_channel_update")
    result = _result(candidate=candidate, chain=_chain(candidate))
    assert gate.BLOCK_INCOMPATIBLE_PAYLOAD_CLASS in result.blocked_reasons


def test_destination_binding_mismatch_blocks():
    candidate = _candidate(destination_binding_id="destination:other:redacted")
    result = _result(candidate=candidate, chain=_chain(candidate))
    assert gate.BLOCK_DESTINATION_MISMATCH in result.blocked_reasons


def test_credential_handle_mismatch_blocks():
    candidate = _candidate(credential_handle_id="credential_handle:other:redacted")
    result = _result(candidate=candidate, chain=_chain(candidate))
    assert gate.BLOCK_CREDENTIAL_MISMATCH in result.blocked_reasons


def test_valid_0174ua_assessment_required():
    result = _result(assessment=None)
    assert gate.BLOCK_APPROVAL_ASSESSMENT_REQUIRED not in result.blocked_reasons
    result = gate.revalidate_dispatch_candidate(candidate=_candidate(), approval_assessment=None, kill_switch_state=_kill(), policy_gate_state=_policy(), audit_chain=_chain())
    assert gate.BLOCK_APPROVAL_ASSESSMENT_REQUIRED in result.blocked_reasons


def test_revoked_approval_blocks():
    _, assessment = _approval(revoked=True)
    result = _result(assessment=assessment)
    assert gate.BLOCK_APPROVAL_REVOKED in result.blocked_reasons


def test_expired_approval_blocks():
    _, assessment = _approval(expired=True)
    result = _result(assessment=assessment)
    assert gate.BLOCK_APPROVAL_EXPIRED in result.blocked_reasons


def test_missing_idempotency_key_blocks():
    candidate = _candidate(outbox_idempotency_key="")
    result = _result(candidate=candidate, chain=_chain(candidate))
    assert gate.BLOCK_IDEMPOTENCY_KEY_MISSING in result.blocked_reasons


def test_idempotency_replay_unsafe_blocks():
    result = _result(idempotency_replay_safe=False)
    assert gate.BLOCK_IDEMPOTENCY_REPLAY_UNSAFE in result.blocked_reasons


@pytest.mark.parametrize("field", [
    "global_dispatch_disabled",
    "platform_dispatch_disabled",
    "destination_dispatch_disabled",
    "credential_handle_disabled",
])
def test_kill_switch_scopes_block(field):
    result = _result(kill=_kill(**{field: True, "reason_class": "operator_hold"}))
    assert gate.BLOCK_KILL_SWITCH_ACTIVE in result.blocked_reasons


def test_unknown_kill_switch_reason_fails_closed():
    result = _result(kill=_kill(reason_class="mystery"))
    assert gate.BLOCK_KILL_SWITCH_UNKNOWN in result.blocked_reasons


def test_over_limit_policy_blocks():
    result = _result(policy=_policy(rate_limit_state="blocked_over_limit"))
    assert gate.BLOCK_POLICY_RATE in result.blocked_reasons


def test_over_budget_policy_blocks():
    result = _result(policy=_policy(budget_state="blocked_over_budget"))
    assert gate.BLOCK_POLICY_BUDGET in result.blocked_reasons


def test_retry_limit_policy_blocks():
    result = _result(policy=_policy(retry_state="blocked_retry_limit"))
    assert gate.BLOCK_POLICY_RETRY in result.blocked_reasons


@pytest.mark.parametrize("kwargs", [
    {"rate_limit_state": "mystery"},
    {"budget_state": "mystery"},
    {"retry_state": "mystery"},
])
def test_unknown_policy_rate_budget_retry_states_fail_closed(kwargs):
    result = _result(policy=_policy(**kwargs))
    assert gate.BLOCK_POLICY_UNKNOWN in result.blocked_reasons


def test_u9_audit_chain_valid_redacted_requirement_enforced():
    result = _result(chain=_chain())
    assert result.audit_chain_valid is True
    assert result.audit_entries_redacted is True


def test_broken_audit_chain_blocks():
    result = _result(chain=_chain(broken=True))
    assert gate.BLOCK_AUDIT_CHAIN_INVALID in result.blocked_reasons


def test_unredacted_audit_chain_blocks():
    chain = replace(_chain(), all_entries_redacted=False)
    result = _result(chain=chain)
    assert gate.BLOCK_AUDIT_ENTRIES_NOT_REDACTED in result.blocked_reasons


def test_no_live_behavior_flags_exist_and_false():
    result = _result()
    flags = result.safety_flags
    for key in (
        "platform_api_called", "telegram_api_called", "provider_api_called",
        "llm_provider_called", "credential_hydrated", "env_read",
        "network_performed", "scheduler_enabled", "scraping_performed",
        "dm_or_reply_automation_allowed", "ingestion_repo_mutated",
    ):
        assert flags[key] is False
    assert flags["local_revalidation_only"] is True
    assert flags["future_send_gate_required"] is True


def test_artifact_writer_touches_only_docs_automation_0174ub(tmp_path):
    root = tmp_path
    result = gate.write_artifacts(root)
    assert str(Path(result["packet_path"]).parent).endswith(str(Path("docs") / "automation" / "0174UB"))
    with pytest.raises(ValueError):
        gate.write_artifacts(root, root / "docs" / "automation" / "0174UA")


def test_no_ingestion_repo_mutation_flag():
    packet = gate.build_revalidation_gate_packet()
    assert packet.safety_flags["ingestion_repo_mutated"] is False
    assert all(c.safety_flags["ingestion_repo_mutated"] is False for c in packet.candidates)
    assert all(r.safety_flags["ingestion_repo_mutated"] is False for r in packet.revalidation_results)


def test_packet_builds_with_next_gate_and_no_dispatch():
    packet = gate.build_revalidation_gate_packet()
    assert packet.next_required_gate == "TASK_CONTENTOPS_0174UC_MANUAL_PUBLISH_RECORD_AND_METRICS_LEDGER_CONTRACT_V0"
    assert packet.all_results_no_dispatch is True
    assert packet.all_results_require_future_send_gate is True
