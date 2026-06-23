import pytest

from live_contentops import primary_payload_classes_contract as contract

REQUIRED_CLASSES = {
    "x_short_post",
    "x_thread",
    "telegram_operator_review_message",
    "telegram_channel_update",
    "substack_newsletter_issue",
    "substack_manual_export_package",
    "linkedin_member_post",
    "linkedin_organization_post",
    "threads_text_post",
    "instagram_caption_media_package",
    "facebook_page_text_link_post",
    "tiktok_video_metadata_packet",
    "youtube_video_metadata_packet",
}


def test_payload_classes_exist():
    assert {p.payload_class_id for p in contract.PAYLOAD_CLASSES} == REQUIRED_CLASSES


def test_no_live_allowed_defaults():
    for p in contract.PAYLOAD_CLASSES:
        assert p.live_write_allowed_now is False
        assert p.dispatchable_now is False
        assert p.public_postable_now is False
        assert p.no_financial_advice_required is True
        assert p.no_signal_language_required is True
        assert p.dispatch_transform_allowed_after_approval is False


def test_lookup_payload_class():
    entry = contract.lookup_payload_class("x_short_post")
    assert entry.payload_class_id == "x_short_post"
    assert entry.platform_id == "x_profile"


def test_unsupported_payload_class_fails_closed():
    with pytest.raises(contract.UnsupportedPayloadClassError):
        contract.lookup_payload_class("unknown_payload")


def test_payload_classes_by_platform_id():
    mapping = contract.payload_classes_by_platform_id()
    assert "x_profile" in mapping
    assert len(mapping["x_profile"]) == 2
    assert "telegram_channel_destination" in mapping
    assert len(mapping["telegram_channel_destination"]) == 1


def test_packet_generation():
    packet = contract.primary_payload_classes_packet()
    assert packet["task_label"] == contract.TASK_LABEL
    assert len(packet["payload_class_entries"]) == len(contract.PAYLOAD_CLASSES)
