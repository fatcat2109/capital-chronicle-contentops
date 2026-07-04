import json

import pytest

from live_contentops import discord_dispatch_adapter as adapter


class MockResponse:
    def __init__(self, status):
        self.status = status


def payload(target_name="announcements", **overrides):
    config = adapter.TARGET_CONFIGS[target_name]
    item = {
        "payload_id": f"payload_{target_name}",
        "target_name": target_name,
        "destination_binding_id": config.destination_binding_id,
        "credential_handle_id": config.credential_handle_id,
        "redacted_webhook_json_preview": {"content": "Capital Chronicle dispatch adapter dry-run payload."},
    }
    item.update(overrides)
    return item


def env_for(target_name="announcements"):
    config = adapter.TARGET_CONFIGS[target_name]
    return {config.env_key_name: "https://discord.com/api/webhooks/111/mock_token"}


def test_target_config_exists_for_all_three_verified_targets():
    assert set(adapter.TARGET_CONFIGS) == {"announcements", "substack_drops", "product_updates"}


def test_target_routing_maps_each_target_to_correct_values():
    expected = {
        "announcements": (
            "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL",
            "discord_announcements_capital_chronicle_01",
            "discord_announcements_webhook_01",
        ),
        "substack_drops": (
            "DISCORD_SUBSTACK_DROPS_WEBHOOK_URL",
            "discord_substack_drops_capital_chronicle_01",
            "discord_substack_drops_webhook_01",
        ),
        "product_updates": (
            "DISCORD_PRODUCT_UPDATES_WEBHOOK_URL",
            "discord_product_updates_capital_chronicle_01",
            "discord_product_updates_webhook_01",
        ),
    }
    for target_name, values in expected.items():
        config = adapter.TARGET_CONFIGS[target_name]
        assert (config.env_key_name, config.destination_binding_id, config.credential_handle_id) == values


def test_wrong_destination_binding_blocks():
    dispatch = adapter.DiscordDispatchAdapter()
    item = payload()
    with pytest.raises(adapter.DiscordDispatchBlocked, match="destination_binding_mismatch"):
        dispatch.dispatch(
            item,
            target_name="announcements",
            destination_binding_id="wrong",
            credential_handle_id=item["credential_handle_id"],
        )


def test_wrong_credential_handle_blocks():
    dispatch = adapter.DiscordDispatchAdapter()
    item = payload()
    with pytest.raises(adapter.DiscordDispatchBlocked, match="credential_handle_mismatch"):
        dispatch.dispatch(
            item,
            target_name="announcements",
            destination_binding_id=item["destination_binding_id"],
            credential_handle_id="wrong",
        )


def test_unknown_target_blocks():
    dispatch = adapter.DiscordDispatchAdapter()
    item = payload()
    with pytest.raises(adapter.DiscordDispatchBlocked, match="unknown_target_nope"):
        dispatch.dispatch(
            item,
            target_name="nope",
            destination_binding_id=item["destination_binding_id"],
            credential_handle_id=item["credential_handle_id"],
        )


def test_payload_normalization_forces_allowed_mentions_parse_empty():
    body = adapter.normalize_payload_body({"content": "hello", "allowed_mentions": {"parse": ["everyone"]}})
    assert body["allowed_mentions"] == {"parse": []}


@pytest.mark.parametrize("field", ["attachments", "files", "components", "poll", "thread_id", "thread_name", "applied_tags"])
def test_payload_normalization_rejects_forbidden_request_fields(field):
    with pytest.raises(adapter.DiscordDispatchBlocked, match="payload_forbidden_fields"):
        adapter.normalize_payload_body({"content": "hello", field: []})


def test_payload_normalization_rejects_empty_body():
    with pytest.raises(adapter.DiscordDispatchBlocked, match="payload_body_empty"):
        adapter.normalize_payload_body({"allowed_mentions": {"parse": []}})


def test_content_only_body_accepted():
    assert adapter.normalize_payload_body({"content": "hello"}) == {"content": "hello", "allowed_mentions": {"parse": []}}


def test_embed_body_accepted():
    embeds = [{"title": "hello"}]
    assert adapter.normalize_payload_body({"embeds": embeds}) == {"embeds": embeds, "allowed_mentions": {"parse": []}}


def test_redacted_preview_body_accepted_and_preserves_embed():
    embeds = [{"title": "hello"}]
    body = adapter.normalize_payload_body({"redacted_webhook_json_preview": {"embeds": embeds, "username": "Capital Chronicle"}})
    assert body["embeds"] == embeds
    assert body["username"] == "Capital Chronicle"
    assert body["allowed_mentions"] == {"parse": []}


def test_minimal_content_fallback_from_body_field():
    body = adapter.normalize_payload_body({"body": "fallback content"})
    assert body == {"content": "fallback content", "allowed_mentions": {"parse": []}}


def test_dry_run_does_not_call_network():
    def forbidden(*args, **kwargs):
        raise AssertionError("network should not be called")

    item = payload()
    dispatch = adapter.DiscordDispatchAdapter(opener=forbidden)
    result = dispatch.dispatch(
        item,
        target_name="announcements",
        destination_binding_id=item["destination_binding_id"],
        credential_handle_id=item["credential_handle_id"],
        execute=False,
    )
    assert result["result_status"] == "DRY_RUN"
    assert result["request_count_attempted"] == 0


def test_execute_with_mocked_opener_attempts_exactly_one_request():
    calls = []

    def opener(req, timeout):
        calls.append(req)
        return MockResponse(204)

    item = payload()
    dispatch = adapter.DiscordDispatchAdapter(environ=env_for(), opener=opener)
    result = dispatch.dispatch(
        item,
        target_name="announcements",
        destination_binding_id=item["destination_binding_id"],
        credential_handle_id=item["credential_handle_id"],
        execute=True,
    )
    assert len(calls) == 1
    assert result["request_count_attempted"] == 1


def test_second_request_blocked_by_budget_guard():
    guard = adapter.DispatchBudgetGuard()
    guard.spend_before_post()
    with pytest.raises(adapter.DiscordDispatchBlocked, match="request_budget_exhausted"):
        guard.spend_before_post()


def test_user_agent_header_is_set():
    seen = []

    def opener(req, timeout):
        seen.append(req)
        return MockResponse(204)

    item = payload()
    dispatch = adapter.DiscordDispatchAdapter(environ=env_for(), opener=opener)
    dispatch.dispatch(
        item,
        target_name="announcements",
        destination_binding_id=item["destination_binding_id"],
        credential_handle_id=item["credential_handle_id"],
        execute=True,
    )
    assert seen[0].headers["User-agent"] == adapter.USER_AGENT


@pytest.mark.parametrize(
    ("status", "result_status", "diagnostic"),
    [
        (204, "PASS", "success_2xx"),
        (403, "FAIL", "credential_unauthorized"),
        (404, "FAIL", "webhook_not_found_or_deleted"),
    ],
)
def test_status_mapping(status, result_status, diagnostic):
    def opener(req, timeout):
        return MockResponse(status)

    item = payload()
    dispatch = adapter.DiscordDispatchAdapter(environ=env_for(), opener=opener)
    result = dispatch.dispatch(
        item,
        target_name="announcements",
        destination_binding_id=item["destination_binding_id"],
        credential_handle_id=item["credential_handle_id"],
        execute=True,
    )
    assert result["result_status"] == result_status
    assert result["status_code_class"] == ("2xx" if status == 204 else "4xx")
    assert result["diagnostic_interpretation"] == diagnostic


def test_execute_missing_env_blocks_without_network():
    def forbidden(*args, **kwargs):
        raise AssertionError("network should not be called")

    item = payload()
    dispatch = adapter.DiscordDispatchAdapter(environ={}, opener=forbidden)
    result = dispatch.dispatch(
        item,
        target_name="announcements",
        destination_binding_id=item["destination_binding_id"],
        credential_handle_id=item["credential_handle_id"],
        execute=True,
    )
    assert result["result_status"] == "BLOCKED"
    assert result["request_count_attempted"] == 0


def test_generated_packet_includes_three_dry_run_target_results(tmp_path):
    packet = {
        "payloads": [payload("announcements"), payload("substack_drops"), payload("product_updates")]
    }
    path = tmp_path / "payloads.json"
    out = tmp_path / "out.json"
    path.write_text(json.dumps(packet), encoding="utf-8")
    generated = adapter.generate_dry_run_packet(path, out)
    assert [item["target_name"] for item in generated["dispatch_results"]] == [
        "announcements",
        "substack_drops",
        "product_updates",
    ]
    assert all(item["result_status"] == "DRY_RUN" for item in generated["dispatch_results"])
    assert generated["request_count_attempted"] == 0


def test_generated_packet_contains_no_webhook_url(tmp_path):
    packet = {
        "payloads": [payload("announcements"), payload("substack_drops"), payload("product_updates")]
    }
    path = tmp_path / "payloads.json"
    out = tmp_path / "out.json"
    path.write_text(json.dumps(packet), encoding="utf-8")
    generated = adapter.generate_dry_run_packet(path, out)
    text = json.dumps(generated, sort_keys=True)
    assert "discord.com/api/webhooks" not in text
    assert "mock_token" not in text
    assert generated["webhook_url_printed"] is False
    assert generated["raw_secret_output"] is False
