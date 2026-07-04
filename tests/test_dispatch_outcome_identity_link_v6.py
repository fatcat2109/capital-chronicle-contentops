import pytest

from live_contentops.dispatch_outcome_identity_link_v6 import make_dispatch_outcome_identity_link
from live_contentops.platform_publication_identity_registry_v6 import make_registry_record


def _x_record(**overrides):
    record = make_registry_record(
        platform="x",
        payload_hash="sha256:abc123",
        public_url="https://x.com/CapitalChron/status/1800000000000000000",
        approval_id="approval_1",
        outbox_entry_id="outbox_1",
        dispatch_attempt_id="dispatch_1",
        account_binding_ref="acct_x_capital_chronicle",
        destination_binding_ref="dest_x_main",
        created_at_utc="2026-07-03T00:00:00+00:00",
    )
    record.update(overrides)
    return record


def test_valid_x_identity_record_produces_audit_ready_link():
    link = make_dispatch_outcome_identity_link(_x_record())

    assert link["link_status"] == "READY_FOR_PUBLICATION_AUDIT_RECORD"
    assert link["ready_for_publication_audit_record"] is True
    assert link["platform_publication_id"] == "1800000000000000000"
    assert link["no_paid_api_used"] is True
    assert link["live_write_attempted"] is False
    assert link["api_request_performed"] is False
    assert link["webhook_request_performed"] is False
    assert link["browser_session_started"] is False
    assert link["blockers"] == []


def test_missing_dispatch_context_returns_review_blockers():
    record = _x_record(approval_id=None, outbox_entry_id=None, dispatch_attempt_id=None)
    link = make_dispatch_outcome_identity_link(record)

    assert link["link_status"] == "REVIEW_MISSING_DISPATCH_CONTEXT"
    assert link["ready_for_publication_audit_record"] is False
    assert set(link["blockers"]) >= {
        "approval_id_missing",
        "outbox_entry_id_missing",
        "dispatch_attempt_id_missing",
    }


def test_manual_non_x_platform_can_link_when_safe():
    record = make_registry_record(
        platform="substack",
        payload_hash="sha256:def456",
        public_url="https://capitalchronicle.substack.com/p/example",
        approval_id="approval_1",
        outbox_entry_id="outbox_1",
        dispatch_attempt_id="dispatch_1",
        account_binding_ref="acct_substack_capital_chronicle",
        destination_binding_ref="dest_substack_main",
        created_at_utc="2026-07-03T00:00:00+00:00",
    )
    record.update({
        "platform_publication_id": "substack_post_1",
        "capture_method": "operator_supplied_public_url",
        "confirmation_class": "operator_supplied_url",
    })
    link = make_dispatch_outcome_identity_link(record)

    assert link["platform"] == "substack"
    assert link["link_status"] == "READY_FOR_PUBLICATION_AUDIT_RECORD"


def test_paid_api_flag_on_x_blocks():
    record = _x_record(no_paid_api_used=False)
    link = make_dispatch_outcome_identity_link(record)

    assert link["link_status"] == "BLOCKED_UNSAFE_CAPTURE_CLAIM"
    assert "x_paid_api_flag_blocked" in link["blockers"]


@pytest.mark.parametrize(
    "flag",
    [
        "cookie_read_performed",
        "local_storage_read_performed",
        "session_storage_read_performed",
        "token_or_header_read_performed",
        "raw_secret_output",
    ],
)
def test_secret_and_session_read_flags_block(flag):
    record = _x_record(**{flag: True})
    link = make_dispatch_outcome_identity_link(record)

    assert link["link_status"] == "BLOCKED_UNSAFE_CAPTURE_CLAIM"
    assert f"{flag}_must_be_false" in link["blockers"]


def test_secret_like_keys_in_record_block_without_outputting_values():
    record = _x_record()
    record["raw_secret_value"] = "do-not-print"

    link = make_dispatch_outcome_identity_link(record)

    assert link["link_status"] == "BLOCKED_UNSAFE_CAPTURE_CLAIM"
    assert "secret_like_registry_field_blocked" in link["blockers"]
    assert "raw_secret_value" not in link
    assert "do-not-print" not in str(link)


def test_output_contains_no_raw_credential_or_session_fields():
    link = make_dispatch_outcome_identity_link(_x_record())
    serialized = " ".join(link.keys()).lower()

    assert "password" not in serialized
    assert "authorization" not in serialized
    assert "localstorage" not in serialized
    assert "sessionstorage" not in serialized
