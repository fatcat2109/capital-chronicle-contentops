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
