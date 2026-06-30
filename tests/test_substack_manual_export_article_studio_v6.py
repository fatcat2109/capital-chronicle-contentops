from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from live_contentops.substack_manual_export_article_studio_v6 import (
    SubstackExportError,
    build_substack_manual_export_packet,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "automation" / "V6_AI_RESEARCH_CANONICAL_ARTICLE_ENGINE" / "sample_ai_research_canonical_article_packet.json"
SAMPLE = ROOT / "docs" / "automation" / "V6_SUBSTACK_MANUAL_EXPORT_ARTICLE_STUDIO" / "sample_substack_manual_export_article_studio_packet.json"


def _source() -> dict:
    return json.loads(SOURCE.read_text(encoding="utf-8-sig"))


def _sample() -> dict:
    return json.loads(SAMPLE.read_text(encoding="utf-8-sig"))


def test_committed_sample_matches_builder() -> None:
    built = build_substack_manual_export_packet(_source())
    assert _sample() == built
    assert built["export_packet_id"].startswith("substack_manual_export_")
    assert built["source_article_packet_id"] == "article_engine_packet_d4a5afd3ecf03b1b"
    assert built["source_canonical_hash"] == "d4a5afd3ecf03b1b93caf5b9dbd204d93eb80237eb8d368c9eea24680fabe44e"


def test_export_hash_is_stable() -> None:
    first = build_substack_manual_export_packet(_source())
    second = build_substack_manual_export_packet(_source())
    assert first["exact_payload_hash"] == second["exact_payload_hash"]
    assert first["export_packet_id"] == second["export_packet_id"]


def test_export_safety_flags_are_closed() -> None:
    packet = build_substack_manual_export_packet(_source())
    assert packet["export_status"] == "ready_for_manual_review"
    assert packet["approval_status"] == "pending"
    assert packet["live_publish_allowed"] is False
    assert packet["live_publish_performed"] is False
    assert packet["provider_call_made"] is False
    assert packet["network_call_made"] is False
    assert packet["browser_session_used"] is False
    assert packet["raw_secret_values_serialized"] is False
    assert packet["env_lines_serialized"] is False
    assert packet["sample_scope"] == "sample_fixture_only"


def test_no_secret_env_provider_webhook_or_session_material_serialized() -> None:
    serialized = json.dumps(build_substack_manual_export_packet(_source()), sort_keys=True).lower()
    forbidden = [
        "https://discord.com/api/webhooks/",
        "discord_live_announcements_webhook=https",
        "sk-",
        "xoxb-",
        "ghp_",
        "bearer ",
        "cookie=",
        "localstorage=",
        "sessionstorage=",
    ]
    for term in forbidden:
        assert term not in serialized


@pytest.mark.parametrize(
    "field,value",
    [
        ("intro", "This is financial advice."),
        ("intro", "Buy this now."),
        ("intro", "Fake citation: Journal X."),
        ("intro", "Invented URL: https://example.com/fake"),
        ("intro", "Published on Substack already."),
    ],
)
def test_forbidden_article_content_fails_closed(field: str, value: str) -> None:
    packet = copy.deepcopy(_source())
    packet["canonical_article_draft"][field] = value
    with pytest.raises(SubstackExportError):
        build_substack_manual_export_packet(packet)


def test_missing_canonical_article_packet_fails_closed() -> None:
    packet = _source()
    packet.pop("canonical_article_draft")
    with pytest.raises(SubstackExportError):
        build_substack_manual_export_packet(packet)
