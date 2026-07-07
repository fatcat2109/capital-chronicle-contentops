from live_contentops.linkedin_browser_adapter_v6 import (
    _linkedin_media_attachment_passed,
    _linkedin_media_blocked_result,
)


def test_linkedin_image_required_failure_cannot_pass_text_only():
    evidence = {
        "media_upload_requested": True,
        "media_upload_status": "preview_not_detected",
        "media_preview_detected": False,
        "selector_used": "input[type=file]#0",
    }

    result = _linkedin_media_blocked_result("LinkedIn text", "downloads/chart.png", evidence)

    assert result["status"] == "FAILED"
    assert result["error_class"] == "LINKEDIN_MEDIA_ATTACHMENT_BLOCKED"
    assert result["media_upload_requested"] is True
    assert result["media_preview_detected"] is False
    assert _linkedin_media_attachment_passed(result["media_attachment_evidence"]) is False


def test_linkedin_media_attachment_requires_preview_and_uploaded_status():
    assert _linkedin_media_attachment_passed({
        "media_upload_status": "uploaded",
        "media_preview_detected": True,
    })
    assert not _linkedin_media_attachment_passed({
        "media_upload_status": "uploaded",
        "media_preview_detected": False,
    })
    assert not _linkedin_media_attachment_passed({
        "media_upload_status": "preview_not_detected",
        "media_preview_detected": True,
    })
