from dataclasses import replace
from pathlib import Path

import pytest

from live_contentops import redacted_immutable_audit_ledger_v2_contract as ledger


def _entry(seq=1, prev=ledger.GENESIS_HASH, family="content_idea", payload=None):
    return ledger.build_redacted_ledger_entry(
        entry_sequence=seq,
        previous_entry_hash=prev,
        entry_family=family,
        source_model="test_model",
        source_model_version="v1",
        payload=payload or {"idea_id": f"idea_{seq}", "topic_hint": "safe", "evidence_refs": [f"e:{seq}"]},
    )


def _chain(n=3):
    entries = []
    prev = ledger.GENESIS_HASH
    for seq in range(1, n + 1):
        e = _entry(seq=seq, prev=prev)
        entries.append(e)
        prev = e.entry_hash
    return ledger.build_ledger_chain(tuple(entries))


def test_redaction_policy_removes_email_token_secret_env_material_from_summary():
    e = _entry(payload={
        "raw_input_id": "raw1",
        "raw_text": "Email editor@example.com bearer abcdefghijklmnop SECRET_KEY=C:\\tmp\\.env phone +1 202 555 0199",
        "context_summary": "callback https://example.test/cb?token=abcdef1234567890",
        "evidence_refs": ["fixture:redaction"],
    })
    summary_text = str(e.redacted_summary)
    assert "editor@example.com" not in summary_text
    assert "abcdefghijklmnop" not in summary_text
    assert "C:\\tmp\\.env" not in summary_text
    assert "+1 202 555 0199" not in summary_text
    assert "[REDACTED" in summary_text


def test_redaction_preserves_source_hashes_and_evidence_refs():
    e = _entry(payload={"idea_id": "idea_hash", "payload_hash": "abc123", "evidence_refs": ["fixture:hash"]})
    assert e.source_payload_hash == "abc123"
    assert e.retained_evidence_refs == ("fixture:hash",)
    assert e.evidence_refs == ("fixture:hash",)


def test_entry_hash_deterministic():
    payload = {"idea_id": "same", "topic_hint": "same", "evidence_refs": ["e"]}
    assert _entry(payload=payload).entry_hash == _entry(payload=payload).entry_hash


def test_entry_hash_changes_when_retained_content_changes():
    one = _entry(payload={"idea_id": "same", "topic_hint": "one", "evidence_refs": ["e"]})
    two = _entry(payload={"idea_id": "same", "topic_hint": "two", "evidence_refs": ["e"]})
    assert one.entry_hash != two.entry_hash


def test_entry_hash_changes_when_previous_hash_changes():
    payload = {"idea_id": "same", "topic_hint": "same", "evidence_refs": ["e"]}
    one = _entry(prev=ledger.GENESIS_HASH, payload=payload)
    two = _entry(prev="f" * 64, payload=payload)
    assert one.entry_hash != two.entry_hash


def test_chain_validates_previous_hash_linkage():
    chain = _chain(3)
    result = ledger.validate_ledger_chain(chain)
    assert chain.all_previous_hashes_match is True
    assert result.hash_chain_valid is True
    assert result.validation_status == "pass"


def test_chain_rejects_broken_previous_hash():
    chain = _chain(3)
    broken = replace(chain.entries[1], previous_entry_hash="b" * 64)
    bad_chain = ledger.build_ledger_chain((chain.entries[0], broken, chain.entries[2]))
    result = ledger.validate_ledger_chain(bad_chain)
    assert result.hash_chain_valid is False
    assert "hash_chain_valid_failed" in result.blocked_reasons


def test_sequence_monotonic_validation_works():
    chain = _chain(2)
    bad_second = replace(chain.entries[1], entry_sequence=4)
    bad_chain = ledger.build_ledger_chain((chain.entries[0], bad_second))
    result = ledger.validate_ledger_chain(bad_chain)
    assert result.monotonic_sequence_valid is False
    assert "monotonic_sequence_valid_failed" in result.blocked_reasons


def test_unknown_source_family_fails_closed():
    e = _entry(family="alien_family")
    assert e.entry_family == "unknown_or_blocked"
    assert "unknown_source_family_fail_closed" in e.blocked_reasons


def test_ledger_entry_from_u4_idea_intent_remains_review_only():
    idea = _entry(family="content_idea", payload={"idea_id": "u4", "evidence_refs": ["u4"]})
    intent = _entry(seq=2, prev=idea.entry_hash, family="local_intent", payload={"intent_id": "intent", "evidence_refs": ["u4i"]})
    for e in (idea, intent):
        assert e.human_review_required is True
        assert e.public_postable is False
        assert e.approval_granted is False
        assert e.dispatch_ready is False


def test_ledger_entry_from_u5_writer_output_remains_review_only():
    e = _entry(family="ai_writer_output", payload={"writer_output_id": "u5", "review_status": "review_only", "public_postable": True, "evidence_refs": ["u5"]})
    assert e.public_postable is False
    assert e.approval_granted is False
    assert e.dispatch_ready is False


def test_ledger_entry_from_u6_dry_run_remains_review_only():
    e = _entry(family="multi_platform_dry_run", payload={"dry_run_id": "u6", "dispatch_ready": True, "dry_run_hash": "h", "evidence_refs": ["u6"]})
    assert e.dispatch_ready is False
    assert e.public_postable is False
    assert e.safety_state_snapshot["dispatch_ready"] is False


def test_ledger_entry_from_u7_ingestion_context_remains_context_only():
    e = _entry(family="ingestion_context_candidate", payload={"candidate_id": "u7", "may_create_current_truth": True, "evidence_refs": ["u7"]})
    assert e.current_truth_promoted is False
    assert e.dqr_cleared is False
    assert e.readiness_cleared is False
    assert e.safety_state_snapshot["ingestion_repo_mutated"] is False


def test_ledger_entry_from_u8_artifact_eligibility_never_clears_gates():
    e = _entry(family="content_eligibility_assessment", payload={"assessment_id": "u8", "dqr_cleared": True, "readiness_cleared": True, "current_truth_promoted": True, "evidence_refs": ["u8"]})
    assert e.dqr_cleared is False
    assert e.readiness_cleared is False
    assert e.current_truth_promoted is False


def test_no_entry_can_become_public_approval_or_dispatch_ready():
    e = _entry(payload={"idea_id": "forge", "public_postable": True, "approval_granted": True, "dispatch_ready": True, "evidence_refs": ["f"]})
    assert (e.public_postable, e.approval_granted, e.dispatch_ready) == (False, False, False)


def test_validation_blocks_forged_forbidden_state():
    e = _entry()
    forged = replace(e, public_postable=True)
    chain = ledger.build_ledger_chain((forged,))
    result = ledger.validate_ledger_chain(chain)
    assert result.no_public_postable is False
    assert "no_public_postable_failed" in result.blocked_reasons


def test_artifact_writer_touches_only_docs_automation_0174u9(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    packet = ledger.write_artifacts(repo)
    out = repo / "docs" / "automation" / "0174U9"
    assert (out / ledger.PACKET_FILENAME).exists()
    assert (out / ledger.RUNBOOK_FILENAME).exists()
    assert packet["ledger_scope"] == "docs/automation/0174U9_only"
    with pytest.raises(ValueError):
        ledger.write_artifacts(repo, repo / "docs" / "automation" / "0174U8")


def test_no_provider_api_network_env_credential_scheduler_scraping_dm_behavior_exists():
    packet = ledger.build_contract_packet()
    flags = packet["ledger_chain"]["safety_flags"]
    for flag in ("provider_api_called", "platform_api_called", "telegram_api_called", "credential_hydrated", "env_read", "network_performed", "scheduler_enabled", "scraping_performed", "dm_or_reply_automation_allowed"):
        assert flags[flag] is False
    assert packet["validation_result"]["no_provider_or_platform_behavior"] is True


def test_no_ingestion_repo_mutation_occurs():
    e = _entry(family="ingestion_context_candidate", payload={"candidate_id": "u7", "safety_flags": {"ingestion_repo_mutated": True}, "evidence_refs": ["u7"]})
    assert e.safety_state_snapshot["ingestion_repo_mutated"] is False


def test_contract_packet_is_valid_and_has_expected_families():
    packet = ledger.build_contract_packet()
    assert packet["validation_result"]["validation_status"] == "pass"
    families = {entry["entry_family"] for entry in packet["ledger_chain"]["entries"]}
    assert "raw_operator_input" in families
    assert "artifact_idea_seed" in families
    assert "approval_ledger_fact" in families
    assert "dispatch_outbox_fact" in families
    assert "unknown_or_blocked" in families
    assert packet["next_heavy_batch_recommendation"] == "TASK_CONTENTOPS_0174UA_APPROVAL_LEDGER_REVOCATION_EXPIRATION_CONTRACT_V0"
