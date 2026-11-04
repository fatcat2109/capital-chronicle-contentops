"""A typographic apostrophe is not an unknown publication; numbers stay exact."""
from live_contentops.neo_destination_handoff_v1 import _text, NeoDestinationHandoff


def test_reader_smart_quotes_only_normalizes_glyphs():
    assert _text("BLS’ September release: ‘0.6%’ and “3.7%”.") == _text("BLS' September release: '0.6%' and \"3.7%\".")
    assert _text("0.6%") != _text("0.7%")
    assert _text("-0.6%") != _text("0.6%")
    assert _text("not confirmed") != _text("confirmed")


def test_typography_fix_creates_only_a_new_readback_identity():
    intent = {"work_item_id": "CONTROLLED", "native_payload": {"title": "BLS' CPI"},
        "destination_plan": {"surface": "SUBSTACK_ARTICLE"}}
    value = NeoDestinationHandoff().request(destination="substack", action="READBACK", intent=intent,
        public_object_id="123", public_object_url="https://capitalchronicle.substack.com/p/controlled")
    assert value["reader_text_normalization"] == "MARKDOWN_WHITESPACE_SMART_QUOTES_V1"
    assert value["action"] == "READBACK" and value["dispatch_attempt_identity"] is None


def test_exact_reviewed_caption_between_paragraphs_does_not_break_canonical_readback():
    body = "Original report.\n\n## Details\n\nThe value was 0.6%."
    caption = "Official source, September 2026."
    intent = {"work_item_id": "CONTROLLED", "native_payload": {"title": "CPI", "body_markdown": body},
        "reader_presentation_review": {"stage": "CONTROLLED"}, "removed_reader_text": [],
        "media_assets": [{"asset_id": "chart", "sha256": "a" * 64, "caption": caption}],
        "destination_plan": {"surface": "SUBSTACK_ARTICLE"}}
    observed = {"observed_identity": "capitalchronicle.substack.com", "public_object_id": "123",
        "public_object_url": "https://capitalchronicle.substack.com/p/controlled", "content_verified": True,
        "observed_text": "CPI\nOriginal report.\nDetails\n" + caption + "\nThe value was 0.6%.",
        "observed_media_sha256": ["a" * 64]}
    adapter = NeoDestinationHandoff(native_executor=lambda q: {**observed, "request_sha256": q["request_sha256"]})
    kwargs = dict(destination="substack", intent=intent, public_object_id="123", public_object_url=observed["public_object_url"])
    assert adapter.readback(**kwargs)["verified"]
    observed["observed_text"] = observed["observed_text"].replace("0.6%", "0.7%")
    assert not adapter.readback(**kwargs)["verified"]
    observed["observed_text"] = observed["observed_text"].replace("0.7%", "0.6%").replace(caption, "Unreviewed assertion.")
    assert not adapter.readback(**kwargs)["verified"]
