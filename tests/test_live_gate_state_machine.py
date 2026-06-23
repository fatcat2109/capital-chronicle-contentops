from live_contentops import live_gate_state_machine as gate

PLATFORMS = {
    "x_profile",
    "telegram_remote_operator_inbox",
    "telegram_channel_destination",
    "substack_newsletter",
    "linkedin_member_profile",
    "linkedin_organization_page",
    "threads_profile",
    "instagram_professional_account",
    "facebook_page",
    "tiktok_account",
    "youtube_channel",
}


def _ready_context(platform_id="telegram_channel_destination", **overrides):
    ctx = gate.build_live_gate_context(
        platform_id,
        destination_binding_id=f"{platform_id}_default",
        credential_handle_id=f"{platform_id}_credential",
        docs_packet={"docs_status": "official_docs_checked_current"},
        binding_packet={
            "destination_binding_id": f"{platform_id}_default",
            "credential_handle_id": f"{platform_id}_credential",
            "account_binding_status": "symbolically_ready_but_live_write_forbidden",
            "permission_status": "permission_verified_symbolic",
            "scope_status": "scope_verified_symbolic",
            "wrong_account_detection_status": "wrong_account_not_detected_symbolic",
        },
        approval_packet={"approval_status": "approved_current"},
        outbox_packet={"status": "ready_for_supervised_live_future", "outbox_id": "outbox_symbolic"},
        idempotency_packet={"status": "new_key_allowed_for_local_outbox_only", "duplicate": False},
        kill_switch_packet={"status": "kill_switch_clear"},
        audit_packet={"ready": True},
        request_budget_used=1,
        media_requirement_satisfied=True,
        app_review_satisfied=True,
        paid_or_quota_gate_satisfied=True,
        read_only_probe_required_before_live=False,
        future_live_candidate_requested=True,
    )
    data = ctx.as_dict()
    data.update(overrides)
    return gate.LiveGateContext(**data)


def test_all_11_platforms_are_never_live_dispatch_ready_now():
    packet = gate.live_gate_state_machine_packet()
    assert set(packet["platform_ids"]) == PLATFORMS
    assert packet["all_valid_for_live_dispatch_now_false"] is True
    assert packet["all_gate_passed_now_false"] is True
    assert packet["request_budget_all_1"] is True
    assert packet["auto_retry_allowed_any"] is False
    assert packet["credential_hydration_performed_any"] is False


def test_future_candidate_still_live_now_false():
    evaluation = gate.evaluate_live_gate_state(_ready_context())
    assert evaluation.gate_state == "future_supervised_live_candidate"
    assert evaluation.future_live_candidate_allowed_after_gates is True
    assert evaluation.valid_for_live_dispatch_now is False
    assert evaluation.gate_passed_now is False
    assert evaluation.auto_retry_allowed is False


def test_missing_platform_registry_blocks():
    evaluation = gate.evaluate_live_gate_state(_ready_context(platform_registry_present=False))
    assert evaluation.gate_state == "blocked_by_platform_registry"
    assert "platform_registry_missing" in evaluation.blocked_reasons


def test_missing_docs_blocks():
    evaluation = gate.evaluate_live_gate_state(_ready_context(docs_status="docs_missing"))
    assert evaluation.gate_state == "blocked_by_docs"
    assert "official_docs_not_current" in evaluation.blocked_reasons


def test_missing_binding_scope_permission_and_credential_block():
    binding = gate.evaluate_live_gate_state(_ready_context(destination_binding_id="", destination_binding_status="destination_binding_missing"))
    assert binding.gate_state == "blocked_by_destination_binding"
    scope = gate.evaluate_live_gate_state(_ready_context(permission_status="permission_unverified_blocked"))
    assert scope.gate_state == "blocked_by_scope_permission"
    credential = gate.evaluate_live_gate_state(_ready_context(credential_handle_id=""))
    assert credential.gate_state == "blocked_by_credential_handle"


def test_missing_approval_outbox_idempotency_kill_audit_blocks():
    assert gate.evaluate_live_gate_state(_ready_context(approval_status="not_requested")).gate_state == "blocked_by_approval"
    assert gate.evaluate_live_gate_state(_ready_context(outbox_status="missing")).gate_state == "blocked_by_outbox"
    duplicate = gate.evaluate_live_gate_state(_ready_context(idempotency_status="duplicate_blocked", idempotency_duplicate=True))
    assert duplicate.gate_state == "blocked_by_idempotency"
    assert gate.evaluate_live_gate_state(_ready_context(kill_switch_status="kill_switch_engaged")).gate_state == "blocked_by_kill_switch"
    assert gate.evaluate_live_gate_state(_ready_context(audit_sink_ready=False)).gate_state == "blocked_by_audit_sink"


def test_request_budget_media_app_review_and_quota_blocks():
    assert gate.evaluate_live_gate_state(_ready_context(request_budget_used=2)).gate_state == "blocked_by_request_budget"
    assert gate.evaluate_live_gate_state(_ready_context("instagram_professional_account", media_requirement_satisfied=False)).gate_state == "blocked_by_media_requirement"
    assert gate.evaluate_live_gate_state(_ready_context("tiktok_account", app_review_satisfied=False)).gate_state == "blocked_by_app_review"
    assert gate.evaluate_live_gate_state(_ready_context("youtube_channel", paid_or_quota_gate_satisfied=False)).gate_state == "blocked_by_paid_or_quota_gate"


def test_media_requirement_missing_blocks_instagram_tiktok_youtube():
    for platform_id in ("instagram_professional_account", "tiktok_account", "youtube_channel"):
        evaluation = gate.evaluate_live_gate_state(_ready_context(platform_id, media_requirement_satisfied=False))
        assert evaluation.gate_state == "blocked_by_media_requirement"
        assert "complete_media_container_or_upload_requirement" in evaluation.required_repairs


def test_app_review_blocks_meta_linkedin_tiktok_youtube():
    for platform_id in gate.APP_REVIEW_PLATFORMS:
        evaluation = gate.evaluate_live_gate_state(_ready_context(platform_id, app_review_satisfied=False))
        assert evaluation.gate_state == "blocked_by_app_review"


def test_paid_quota_blocks_x_tiktok_youtube():
    for platform_id in ("x_profile", "tiktok_account", "youtube_channel"):
        evaluation = gate.evaluate_live_gate_state(_ready_context(platform_id, paid_or_quota_gate_satisfied=False))
        assert evaluation.gate_state == "blocked_by_paid_or_quota_gate"


def test_telegram_operator_inbox_never_public_publish_destination():
    evaluation = gate.evaluate_live_gate_state(_ready_context("telegram_remote_operator_inbox", public_destination_allowed_future=True))
    assert "operator_inbox_not_public_publish_destination" in evaluation.blocked_reasons
    assert evaluation.valid_for_live_dispatch_now is False


def test_substack_remains_manual_export_first_no_api_assumption():
    evaluation = gate.evaluate_live_gate_state(_ready_context("substack_newsletter"))
    assert "substack_manual_export_no_official_api" in evaluation.blocked_reasons
    assert "use_manual_export_fallback" in evaluation.required_repairs
    assert evaluation.manual_fallback_required is True


def test_assert_no_live_dispatch_ready_now_rejects_live_claim():
    good = gate.evaluate_live_gate_state(_ready_context())
    gate.assert_no_live_dispatch_ready_now([good])
    bad = good.as_dict()
    bad["valid_for_live_dispatch_now"] = True
    try:
        gate.assert_no_live_dispatch_ready_now([bad])
    except AssertionError as exc:
        assert "valid_for_live_dispatch_now" in str(exc)
    else:
        raise AssertionError("live readiness claim was not rejected")
