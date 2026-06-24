from __future__ import annotations

import json
from pathlib import Path

from live_contentops.final_environment_format_inventory import (
    DEFERRED_EMPTY_KEYS,
    REQUIRED_KEYS,
    build_inventory,
    build_inventory_from_text,
)


def final_fixture() -> str:
    lines = []
    deferred = set(DEFERRED_EMPTY_KEYS)
    for key in REQUIRED_KEYS:
        if key in deferred:
            lines.append(f"{key}=")
        elif key == "SUBSTACK_DASHBOARD_URL":
            lines.append("SUBSTACK_DASHBOARD_URL=https://capitalnicle.substack.com/publish/home")
        elif key == "SUBSTACK_PUBLICATION_URL":
            lines.append("SUBSTACK_PUBLICATION_URL=https://capitalnicle.substack.com")
        elif key == "SUBSTACK_COMPOSE_URL":
            lines.append("SUBSTACK_COMPOSE_URL=https://capitalnicle.substack.com/publish/post/new")
        elif key == "SUBSTACK_POSTS_LIST_URL":
            lines.append("SUBSTACK_POSTS_LIST_URL=https://capitalnicle.substack.com/publish/posts/published")
        elif key == "GOOGLE_APPLICATION_CREDENTIALS":
            lines.append(r"GOOGLE_APPLICATION_CREDENTIALS=A:\Capital Chronicle\local-secrets\vertex_service_account.json")
        else:
            lines.append(f"{key}=present_redacted")
    return "\n".join(lines) + "\n"


def test_duplicate_key_detection_works() -> None:
    report = build_inventory_from_text("X_CLIENT_ID=\nX_CLIENT_ID=\n")
    assert report["duplicate_keys"] == ["X_CLIENT_ID"]


def test_raw_json_and_private_key_block_detection_works() -> None:
    text = '{\n  "type": "service_account",\n  "private_key": "-----BEGIN PRIVATE KEY----- redacted"\n}\n'
    report = build_inventory_from_text(text)
    assert report["raw_json_block_present"] is True
    assert report["private_key_block_present"] is True


def test_no_raw_values_are_returned() -> None:
    secret_like = "X_CLIENT_ID=SHOULD_NOT_APPEAR_IN_REPORT\n"
    report = build_inventory_from_text(secret_like)
    serialized = json.dumps(report, sort_keys=True)
    assert "SHOULD_NOT_APPEAR_IN_REPORT" not in serialized
    assert report["raw_values_returned"] is False
    assert report["token_length_prefix_suffix_digest_hash_returned"] is False
    assert report["known_secret_values_redacted"] is True


def test_required_final_keys_present_in_fixture() -> None:
    report = build_inventory_from_text(final_fixture())
    assert report["required_key_missing"] == []
    assert report["duplicate_keys"] == []


def test_x_linkedin_tiktok_may_remain_empty_as_deferred() -> None:
    report = build_inventory_from_text(final_fixture())
    assert set(DEFERRED_EMPTY_KEYS).issubset(set(report["deferred_empty_keys"]))


def test_substack_capitalnicle_dashboard_fixture_passes() -> None:
    report = build_inventory_from_text(final_fixture())
    assert report["required_key_missing"] == []
    assert report["platform_families_present"]["substack"] is True


def test_vertex_raw_json_fixture_blocks() -> None:
    text = final_fixture() + '{\n  "private_key": "-----BEGIN PRIVATE KEY----- redacted"\n}\n'
    report = build_inventory_from_text(text)
    assert report["raw_json_block_present"] is True
    assert report["private_key_block_present"] is True


def test_actual_local_env_validates_without_printing_values() -> None:
    report = build_inventory(Path(__file__).resolve().parents[1])
    serialized = json.dumps(report, sort_keys=True)
    assert report["required_key_missing"] == []
    assert report["duplicate_keys"] == []
    assert report["known_secret_values_redacted"] is True
    assert "BEGIN PRIVATE KEY" not in serialized
    assert "access_token=" not in serialized.lower()
