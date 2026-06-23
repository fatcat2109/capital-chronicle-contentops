from live_contentops import platform_error_classifier as classifier

BASE = {
    "platform_id": "x_profile",
    "endpoint_family": "x_create_post_supervised_future",
    "method": "POST_SYMBOLIC",
}


def _class(**kwargs):
    data = {**BASE, **kwargs}
    return classifier.classify_platform_error(data)


def test_credential_missing_and_invalid_classified_correctly():
    missing = _class(symbolic_status="credential_missing")
    invalid = _class(http_status_class="401", symbolic_status="unauthorized")
    assert missing.error_class == "credential_missing"
    assert missing.credential_repair_required is True
    assert invalid.error_class == "credential_invalid"
    assert invalid.credential_repair_required is True


def test_permission_and_scope_missing_classified_correctly():
    permission = _class(permission_context="permission_missing")
    scope = _class(scope_context="scope_missing")
    assert permission.error_class == "permission_missing"
    assert permission.scope_permission_repair_required is True
    assert scope.error_class == "scope_missing"
    assert scope.scope_permission_repair_required is True


def test_wrong_account_and_destination_not_found_classified_correctly():
    wrong = _class(account_binding_context="wrong_account")
    missing = _class(account_binding_context="destination_not_found")
    assert wrong.error_class == "wrong_account"
    assert wrong.destination_rebind_required is True
    assert missing.error_class == "destination_not_found"
    assert missing.destination_rebind_required is True


def test_app_review_and_quota_paid_gate_classified_correctly():
    review = _class(symbolic_status="app_review_required")
    quota = _class(quota_context="paid_quota_gate_required")
    assert review.error_class == "app_review_required"
    assert review.app_review_required is True
    assert quota.error_class == "paid_or_quota_gate_required"
    assert quota.quota_or_paid_gate_required is True


def test_rate_limited_does_not_auto_retry():
    rate = _class(http_status_class="429", symbolic_status="rate_limited")
    assert rate.error_class == "rate_limited"
    assert rate.retry_allowed is False
    assert rate.auto_retry_allowed is False
    assert rate.quota_or_paid_gate_required is True


def test_unknown_provider_error_does_not_auto_retry():
    unknown = _class(http_status_class="unknown", symbolic_status="unknown_provider_error")
    assert unknown.error_class == "unknown_provider_error"
    assert unknown.retry_allowed is False
    assert unknown.auto_retry_allowed is False
    assert unknown.re_ground_docs_required is True


def test_media_payload_policy_endpoint_and_docs_classes():
    assert _class(media_context="media_requirement_missing").error_class == "media_requirement_missing"
    assert _class(symbolic_status="payload_invalid").error_class == "payload_invalid"
    assert _class(symbolic_status="policy_violation").error_class == "policy_violation"
    assert _class(symbolic_status="unsupported_endpoint").error_class == "unsupported_endpoint"
    assert _class(symbolic_status="stale_official_docs").error_class == "stale_official_docs"


def test_request_budget_exceeded_classified():
    result = _class(request_budget_used=2)
    assert result.error_class == "request_budget_exceeded"
    assert result.quota_or_paid_gate_required is True


def test_blocked_before_request_and_none():
    blocked = _class(symbolic_status="blocked_before_request")
    ok = _class(http_status_class="2xx", symbolic_status="ok")
    assert blocked.error_class == "blocked_before_request"
    assert ok.error_class == "none"
    assert ok.manual_fallback_required is False


def test_secret_shaped_raw_metadata_safety_stops():
    result = classifier.classify_platform_error({**BASE, "provider_error_code_redacted": "123456789:ABCdefGHijkLMNopqRSTuvwXYZ123456789"})
    assert result.error_class == "safety_stop_secret_risk"
    assert result.severity == "safety_stop"
    raw_key = classifier.classify_platform_error({**BASE, "raw_response": "redacted"})
    assert raw_key.error_class == "safety_stop_secret_risk"


def test_raw_response_header_token_flags_are_false_for_all_classes():
    packet = classifier.platform_error_classifier_packet()
    assert set(classifier.ERROR_CLASSES) == set(packet["error_classes"])
    for error_class in classifier.ERROR_CLASSES:
        result = classifier._classification(error_class)
        assert result.raw_response_safe_to_persist is False
        assert result.raw_headers_safe_to_persist is False
        assert result.token_safe_to_log is False
        assert result.retry_allowed is False
        assert result.auto_retry_allowed is False
