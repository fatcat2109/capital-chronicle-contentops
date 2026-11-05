"""A fresh article's approved captions must not break exact prose readback."""
import pytest

from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff


@pytest.mark.parametrize("middle,ending,verified", [
    ("Treasury’s yield, 4 November. Source: Treasury.", "Second paragraph.", True),
    ("Unapproved caption.", "Second paragraph.", False),
    ("Treasury’s yield, 4 November. Source: Treasury.", "Changed claim.", False),
])
def test_fresh_substack_readback_removes_only_exact_approved_caption(middle, ending, verified):
    url = "https://capitalchronicle.substack.com/p/caption-test"
    request = {"request_sha256": "request", "native_payload": {"title": "Yield watch"},
        "content_binding": {"expected_text_segments": ["Yield watch", "First paragraph. Second paragraph."],
            "media_manifest": [{"sha256": "image", "caption":
                "Treasury's yield, 4 November. Source: [Treasury](https://home.treasury.gov/)."}],
            "thread_post_count": 0}}
    response = {"request_sha256": "request", "observed_identity": "capitalchronicle.substack.com",
        "public_object_id": "123", "public_object_url": url,
        "observed_text": f"Yield watch First paragraph. {middle} {ending}",
        "content_verified": True, "observed_media_sha256": ["image"]}
    adapter = NeoDestinationHandoff(native_executor=lambda _: response)
    adapter.request = lambda **_: request
    result = adapter.readback(destination="substack", intent={}, public_object_id="123", public_object_url=url)
    assert result["verified"] is verified
    assert result["content_binding_checks"]["media_match"] is True
