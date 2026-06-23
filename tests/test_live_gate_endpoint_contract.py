from live_contentops import live_gate_endpoint_contract as endpoints
from live_contentops.platform_universe_registry_v2 import build_platform_universe_registry_v2


def test_endpoint_contracts_cover_all_platforms():
    grouped = endpoints.endpoint_contracts_by_platform_id()
    registry_platforms = {row.platform_id for row in build_platform_universe_registry_v2()}
    assert set(grouped) == registry_platforms


def test_endpoint_contracts_enforce_budget_retry_probe_live_hydration_invariants():
    for row in endpoints.build_live_gate_endpoint_contracts():
        endpoints.validate_endpoint_contract(row)
        data = row.as_dict()
        assert data["request_budget_max"] == 1
        assert data["auto_retry_allowed"] is False
        assert data["read_only_probe_allowed_in_this_task"] is False
        assert data["live_write_allowed_in_this_task"] is False
        assert data["credential_hydration_allowed_in_this_task"] is False
        assert data["manual_fallback_required"] is True


def test_endpoint_contracts_never_persist_raw_request_response_headers_or_tokens():
    for row in endpoints.build_live_gate_endpoint_contracts():
        assert row.raw_request_persisted is False
        assert row.raw_response_persisted is False
        assert row.token_logged is False
        assert row.headers_logged is False


def test_endpoint_contracts_are_symbolic_not_executable_urls():
    for row in endpoints.build_live_gate_endpoint_contracts():
        assert "://" not in row.host_family_symbolic
        assert "://" not in row.endpoint_path_family_symbolic
        assert "http" not in row.host_family_symbolic.lower()
        assert "http" not in row.endpoint_path_family_symbolic.lower()
        assert row.method_symbolic.endswith("SYMBOLIC")


def test_substack_is_manual_export_no_api():
    grouped = endpoints.endpoint_contracts_by_platform_id()
    substack_rows = grouped["substack_newsletter"]
    assert len(substack_rows) == 1
    row = substack_rows[0]
    assert row.endpoint_family == "substack_manual_export_no_api"
    assert row.host_family_symbolic == "no_api_manual_export_symbolic"
    assert row.method_symbolic == "MANUAL_EXPORT_SYMBOLIC"


def test_packet_summarizes_non_live_contract():
    packet = endpoints.live_gate_endpoint_contract_packet()
    assert packet["request_budget_max_all_1"] is True
    assert packet["auto_retry_allowed_any"] is False
    assert packet["read_only_probe_allowed_in_this_task_any"] is False
    assert packet["live_write_allowed_in_this_task_any"] is False
    assert packet["credential_hydration_allowed_in_this_task_any"] is False
    assert packet["raw_response_persisted_any"] is False
    assert packet["token_logged_any"] is False
    assert packet["headers_logged_any"] is False
    assert packet["substack_manual_export_no_api"] is True
