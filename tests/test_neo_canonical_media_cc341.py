"""Editor-selected media must reach the actual canonical browser handoff."""
import pytest

from live_contentops.neo_destination_handoff_v1 import _payload_binding


@pytest.mark.parametrize("destination", ["linkedin", "linkedin_company"])
@pytest.mark.parametrize("object_id,valid", [
    ("urn:li:activity:7525534845696122880", True),
    ("7525534845696122880", True),
    ("7525534845696122881", False),
    ("urn:li:share:7525534845696122880", False),
])
def test_linkedin_exact_url_accepts_urn_or_its_numeric_id(destination, object_id, valid):
    from live_contentops.neo_destination_handoff_v1 import _public_url
    assert bool(_public_url(destination,
        "https://www.linkedin.com/feed/update/urn:li:activity:7525534845696122880/",
        object_id)) is valid


@pytest.mark.parametrize("excluded", ["article_inclusion", "canonical_article_media"])
def test_canonical_browser_binding_excludes_retained_unused_asset(excluded):
    selected = {"asset_id": "selected-chart", "path": "chart.png", "sha256": "a" * 64,
                "article_inclusion": True, "canonical_article_media": True, "delivery_only": True}
    unused = {"asset_id": "unused-card", "path": "card.png", "sha256": "b" * 64, excluded: False}
    payload = {"title": "Controlled article", "body_markdown": "Controlled source-bound text."}
    actual, binding = _payload_binding({"native_payload": payload, "media_assets": [selected, unused]}, "substack")
    assert actual == payload
    assert [a["asset_id"] for a in binding["media_manifest"]] == [selected["asset_id"]]
    assert binding["media_manifest"][0]["sha256"] == selected["sha256"]


def test_derivative_keeps_its_independent_reviewed_asset_selection():
    payload = {"text": "Controlled derivative", "media_asset_ids": ["social-card"]}
    assets = [{"asset_id": "social-card", "path": "card.png", "sha256": "b" * 64,
               "canonical_article_media": False}]
    _, binding = _payload_binding({"native_payload": payload, "media_assets": assets}, "x")
    assert [a["asset_id"] for a in binding["media_manifest"]] == ["social-card"]
