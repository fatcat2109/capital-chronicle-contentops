from live_contentops import kill_switch_policy as policy


def test_global_kill_switch_blocks_every_platform():
    state = policy.build_global_kill_switch_state(True, "incident", "ops", "2026-06-23T00:00:00Z")
    assert policy.is_kill_switch_blocking_platform(state, "x_profile") is True
    assert policy.is_kill_switch_blocking_platform(state, "linkedin_org") is True
    explanation = policy.explain_kill_switch_blocker(state, "x_profile")
    assert explanation["scope"] == "global_active"
    assert explanation["blocking"] is True


def test_platform_kill_switch_blocks_only_selected_platform():
    state = policy.build_platform_kill_switch_state("x_profile", True, "platform incident", "ops", "2026-06-23T00:00:00Z")
    assert policy.is_kill_switch_blocking_platform(state, "x_profile") is True
    assert policy.is_kill_switch_blocking_platform(state, "linkedin_org") is False


def test_inactive_kill_switch_does_not_block_preview_or_approval():
    state = policy.build_global_kill_switch_state(False, "clear", "ops", "2026-06-23T00:00:00Z")
    assert state["scope"] == "inactive"
    assert state["does_not_block_preview"] is True
    assert policy.is_kill_switch_blocking_platform(state, "x_profile") is False
    decision = policy.evaluate_kill_switch(state, "x_profile").as_dict()
    assert decision["local_outbox_allowed"] is True


def test_active_kill_switch_does_not_delete_outbox():
    state = policy.build_global_kill_switch_state(True, "incident", "ops", "2026-06-23T00:00:00Z")
    explanation = policy.explain_kill_switch_blocker(state, "x_profile")
    assert explanation["does_not_delete_outbox"] is True
    assert explanation["does_not_block_preview"] is True


def test_active_kill_switch_blocks_live_readiness():
    state = policy.build_platform_kill_switch_state("x_profile", True, "incident", "ops", "2026-06-23T00:00:00Z", expires_at=None)
    decision = policy.evaluate_kill_switch(state, "x_profile").as_dict()
    assert decision["local_outbox_allowed"] is False
    assert decision["live_readiness_blocked"] is True
    assert decision["auto_retry_allowed"] is False


def test_state_contains_required_metadata_and_packet_helpers():
    state = policy.build_platform_kill_switch_state("x_profile", True, "incident", "ops", "2026-06-23T00:00:00Z", "2026-06-24T00:00:00Z")
    for key in ("reason", "operator_id", "activated_at", "expires_at", "does_not_block_preview", "does_not_delete_outbox"):
        assert key in state
    packet = policy.kill_switch_policy_packet()
    assert "build_global_kill_switch_state" in packet["helper_api_completed"]
