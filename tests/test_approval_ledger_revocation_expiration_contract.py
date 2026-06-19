from pathlib import Path

from live_contentops import approval_ledger_revocation_expiration_contract as c
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit


APPROVAL = {
    "approval_ledger_entry_id": "approval_entry_test",
    "payload_hash": c._digest({"payload": "exact"}),
    "platform_id": "telegram_channel_destination",
    "payload_class_id": "telegram_channel_update",
    "destination_binding_id": "destination:telegram:redacted",
    "credential_handle_id": "credential_handle:telegram:redacted",
    "approved_by_operator_ref": "operator:jim:redacted",
    "evidence_refs": ("fixture:approval",),
}


def window():
    return c.build_validity_window(APPROVAL, approved_at_epoch=1000, max_valid_duration_seconds=600)


def assess(**overrides):
    w = overrides.pop("validity_window", window())
    args = {
        "validity_window": w,
        "candidate_payload_hash": w.approval_payload_hash if w else APPROVAL["payload_hash"],
        "candidate_platform_id": w.platform_id if w else APPROVAL["platform_id"],
        "candidate_payload_class_id": w.payload_class_id if w else APPROVAL["payload_class_id"],
        "candidate_destination_binding_id": w.destination_binding_id if w else APPROVAL["destination_binding_id"],
        "candidate_credential_handle_id": w.credential_handle_id if w else APPROVAL["credential_handle_id"],
        "evaluated_at_epoch": 1100,
    }
    args.update(overrides)
    return c.assess_approval_validity(**args)


def test_validity_window_builds_deterministically_from_approval_fixture():
    assert window() == window()
    assert window().validity_window_id.startswith("validity_window_")


def test_validity_window_includes_exact_scope():
    w = window()
    assert w.approval_payload_hash == APPROVAL["payload_hash"]
    assert w.platform_id == APPROVAL["platform_id"]
    assert w.payload_class_id == APPROVAL["payload_class_id"]
    assert w.destination_binding_id == APPROVAL["destination_binding_id"]
    assert w.credential_handle_id == APPROVAL["credential_handle_id"]
    assert w.approved_by_operator_ref == APPROVAL["approved_by_operator_ref"]
    assert w.approved_at_epoch == 1000
    assert w.expires_at_epoch == 1600


def test_revocation_fact_is_deterministic_and_append_only():
    r1 = c.build_revocation_fact(
        approval_ledger_entry_id="a", revoked_payload_hash="h",
        revoked_by_operator_ref="op", revoked_at_epoch=1,
        revocation_reason_class="operator_revoked",
        revocation_reason_detail="raw reason")
    r2 = c.build_revocation_fact(
        approval_ledger_entry_id="a", revoked_payload_hash="h",
        revoked_by_operator_ref="op", revoked_at_epoch=1,
        revocation_reason_class="operator_revoked",
        revocation_reason_detail="raw reason")
    assert r1 == r2
    assert r1.immutable_append_only is True


def test_revocation_reason_detail_is_hashed_not_raw():
    raw = "operator email jim@example.com token=SECRET123456"
    r = c.build_revocation_fact(
        approval_ledger_entry_id="a", revoked_payload_hash="h",
        revoked_by_operator_ref="op", revoked_at_epoch=1,
        revocation_reason_class="manual_hold",
        revocation_reason_detail=raw)
    encoded = c._json(r)
    assert raw not in encoded
    assert "jim@example.com" not in encoded
    assert r.revocation_reason_detail_hash == c._digest({"revocation_reason_detail": raw})


def test_expiration_fact_marks_expired_when_evaluated_after_expires():
    exp = c.build_expiration_fact(window(), evaluated_at_epoch=1601)
    assert exp.is_expired is True
    assert exp.expiration_reason_class == "time_window_expired"


def test_expiration_fact_marks_not_expired_when_evaluated_at_or_before_expires():
    exp = c.build_expiration_fact(window(), evaluated_at_epoch=1600)
    assert exp.is_expired is False
    assert exp.expiration_reason_class == "not_expired_yet"


def test_invalid_time_order_blocks():
    bad = c.build_validity_window(APPROVAL, approved_at_epoch=1000, max_valid_duration_seconds=0)
    exp = c.build_expiration_fact(bad, evaluated_at_epoch=1000)
    result = assess(validity_window=bad, expiration_fact=exp)
    assert c.BLOCK_INVALID_TIME_ORDER in exp.blocked_reasons
    assert c.BLOCK_INVALID_TIME_ORDER in result.blocked_reasons


def test_missing_validity_window_blocks_assessment():
    result = assess(validity_window=None)
    assert c.BLOCK_MISSING_VALIDITY_WINDOW in result.blocked_reasons
    assert result.approval_still_valid is False


def test_payload_hash_mismatch_blocks():
    result = assess(candidate_payload_hash="wrong")
    assert c.BLOCK_PAYLOAD_HASH_MISMATCH in result.blocked_reasons
    assert result.payload_hash_match is False


def test_platform_mismatch_blocks():
    result = assess(candidate_platform_id="x")
    assert c.BLOCK_PLATFORM_SCOPE_MISMATCH in result.blocked_reasons


def test_payload_class_mismatch_blocks():
    result = assess(candidate_payload_class_id="x_thread")
    assert c.BLOCK_PAYLOAD_CLASS_SCOPE_MISMATCH in result.blocked_reasons


def test_destination_mismatch_blocks():
    result = assess(candidate_destination_binding_id="different")
    assert c.BLOCK_DESTINATION_SCOPE_MISMATCH in result.blocked_reasons


def test_credential_scope_mismatch_blocks():
    result = assess(candidate_credential_handle_id="different")
    assert c.BLOCK_CREDENTIAL_SCOPE_MISMATCH in result.blocked_reasons


def test_revoked_approval_blocks():
    w = window()
    rev = c.build_revocation_fact(
        approval_ledger_entry_id=w.approval_ledger_entry_id,
        revoked_payload_hash=w.approval_payload_hash,
        revoked_by_operator_ref="op", revoked_at_epoch=1200,
        revocation_reason_class="operator_revoked")
    result = assess(validity_window=w, revocation_facts=(rev,))
    assert c.BLOCK_APPROVAL_REVOKED in result.blocked_reasons
    assert result.not_revoked is False


def test_expired_approval_blocks():
    exp = c.build_expiration_fact(window(), evaluated_at_epoch=2000)
    result = assess(expiration_fact=exp)
    assert c.BLOCK_APPROVAL_EXPIRED in result.blocked_reasons
    assert result.not_expired is False


def test_valid_approval_still_cannot_dispatch_and_requires_revalidation():
    result = assess()
    assert result.approval_still_valid is True
    assert result.can_dispatch is False
    assert result.dispatch_revalidation_required is True
    assert c.BLOCK_DISPATCH_REVALIDATION_REQUIRED in result.blocked_reasons


def test_unknown_revocation_reason_fails_closed():
    r = c.build_revocation_fact(
        approval_ledger_entry_id="a", revoked_payload_hash="h",
        revoked_by_operator_ref="op", revoked_at_epoch=1,
        revocation_reason_class="mystery")
    assert r.revocation_reason_class == "unknown_or_blocked"
    assert c.BLOCK_UNKNOWN_REVOCATION_REASON in r.blocked_reasons


def test_ledger_packet_is_deterministic_append_only_redacted_no_dispatch():
    p1 = c.build_ledger_packet()
    p2 = c.build_ledger_packet()
    assert p1 == p2
    assert p1.append_only is True
    assert p1.all_facts_redacted is True
    assert p1.no_dispatch is True
    assert p1.safety_flags["can_dispatch"] is False


def test_u9_redacted_audit_ledger_records_facts_without_secret_leakage():
    r = c.build_revocation_fact(
        approval_ledger_entry_id="a", revoked_payload_hash="h",
        revoked_by_operator_ref="op", revoked_at_epoch=1,
        revocation_reason_class="manual_hold",
        revocation_reason_detail="token=SECRET123456 jim@example.com")
    entries = c.build_u9_audit_entries((r, c.build_expiration_fact(window(), evaluated_at_epoch=1)))
    chain = audit.build_ledger_chain(entries)
    validation = audit.validate_ledger_chain(chain)
    assert validation.validation_status == "pass"
    assert not audit.scan_for_forbidden_material(audit._asdict(chain))


def test_no_provider_api_network_env_credential_scheduler_scraping_dm_behavior_exists():
    source = Path(c.__file__).read_text(encoding="utf-8")
    forbidden = [
        "import requests", "import httpx", "import aiohttp", "urllib.request",
        "import socket", "import dotenv", "import keyring", "import openai",
        "import anthropic", "telegram.Bot", "sendMessage(", "getUpdates(",
        "import selenium", "import playwright",
    ]
    assert all(term not in source for term in forbidden)


def test_artifact_writer_touches_only_docs_automation_0174ua(tmp_path):
    root = tmp_path
    result = c.write_artifacts(root)
    assert Path(result["packet_path"]).parent == root / c.DOC_REL_DIR
    try:
        c.write_artifacts(root, root / "docs" / "automation" / "other")
    except ValueError as exc:
        assert "0174UA" in str(exc)
    else:
        raise AssertionError("writer accepted forbidden path")


def test_no_ingestion_repo_mutation_flag_occurs():
    assert c.safety_flags()["ingestion_repo_mutated"] is False
    assert c.build_ledger_packet().safety_flags["ingestion_repo_mutated"] is False


def test_packet_hash_matches_content_basis():
    packet = c.build_ledger_packet()
    basis = c._asdict(packet)
    packet_hash = basis.pop("packet_hash")
    basis.pop("packet_id")
    basis.pop("packet_hash_algorithm")
    assert packet_hash == c._digest(basis)
