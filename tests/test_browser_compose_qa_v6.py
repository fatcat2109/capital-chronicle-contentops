from live_contentops import browser_compose_qa_v6 as compose_qa

def test_compose_qa_checklist():
    html = "<html><body><h1>Review-Only</h1><button disabled>Publish</button></body></html>"
    preview = {"payload_hash": "unhashed"}
    checklist = compose_qa.generate_qa_checklist(html, preview)
    assert checklist["local_mock_file_only"] is True
    assert checklist["no_real_substack_domain"] is True
    assert checklist["no_live_publish_controls_enabled"] is True
    
def test_screenshot_evidence_manifest():
    manifest1 = compose_qa.get_screenshot_evidence(screenshot_captured=False)
    assert manifest1["screenshot_created"] is False
    assert manifest1["screenshot_required_later"] is True
    
    manifest2 = compose_qa.get_screenshot_evidence(screenshot_captured=True, screenshot_path="docs/preview.png")
    assert manifest2["screenshot_created"] is True
    assert manifest2["screenshot_path"] == "docs/preview.png"
    assert manifest2["real_substack_opened"] is False
