from live_contentops import idempotency_policy as policy


def _candidate(**overrides):
    data = {
        "payload_hash": "a" * 64,
        "platform_id": "x_profile",
        "payload_class_id": "x_short_post",
        "destination_binding_id": "x_profile_default",
        "credential_handle_id": "x_symbolic_handle",
        "media_manifest_hash": "media_none",
        "policy_snapshot_id": "policy_v1",
        "approval_ledger_entry_id": "app_1",
        "approval_event_id": "app_1",
        "dispatch_intent_class": "manual_supervised_dispatch_candidate",
    }
    data.update(overrides)
    return data


def test_same_inputs_produce_same_key():
    assert policy.compute_idempotency_key(_candidate()) == policy.compute_idempotency_key(_candidate())


def test_payload_hash_change_changes_key():
    assert policy.compute_idempotency_key(_candidate()) != policy.compute_idempotency_key(_candidate(payload_hash="b" * 64))


def test_destination_change_changes_key():
    assert policy.compute_idempotency_key(_candidate()) != policy.compute_idempotency_key(_candidate(destination_binding_id="x_alt"))


def test_credential_handle_change_changes_key():
    assert policy.compute_idempotency_key(_candidate()) != policy.compute_idempotency_key(_candidate(credential_handle_id="x_other_symbolic"))


def test_platform_change_changes_key():
    assert policy.compute_idempotency_key(_candidate()) != policy.compute_idempotency_key(_candidate(platform_id="linkedin_org"))


def test_approval_event_change_changes_key():
    assert policy.compute_idempotency_key(_candidate()) != policy.compute_idempotency_key(_candidate(approval_event_id="app_2", approval_ledger_entry_id="app_2"))


def test_duplicate_success_suppresses_candidate():
    key = policy.compute_idempotency_key(_candidate())
    decision = policy.decide_idempotency(_candidate(), existing_keys={key}).as_dict()
    assert policy.is_duplicate_success(decision) is True
    action = policy.classify_duplicate_action(decision)
    assert action["duplicate_action"] == "suppress_candidate_duplicate_success"
    assert action["auto_retry_allowed"] is False


def test_unknown_result_does_not_auto_retry_and_routes_manual():
    action = policy.classify_duplicate_action({"status": "unknown", "duplicate": None})
    assert action["auto_retry_allowed"] is False
    assert action["manual_fallback_status"] == "manual_fallback_required"
    assert action["duplicate_action"] == "manual_reconciliation_required_unknown_result"


def test_packet_declares_helper_api():
    packet = policy.idempotency_policy_packet()
    assert packet["helper_api_completed"] == ["is_duplicate_success", "classify_duplicate_action"]
    assert packet["unknown_result_auto_retry_allowed"] is False
