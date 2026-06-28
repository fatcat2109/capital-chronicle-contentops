from live_contentops import browser_safety_policy_v6 as safety

def test_browser_safety_policy_flags():
    policy = safety.get_safety_policy()
    assert policy["real_substack_navigation_allowed"] is False
    assert policy["cookie_read_allowed"] is False
    assert policy["network_allowed"] is False
    assert policy["live_publish_click_allowed"] is False
    
def test_safety_compliance_checks():
    # If Substack was actually navigated or clicked
    state = {"real_substack_opened": True}
    report = safety.validate_safety_compliance(state)
    assert report["compliance_passed"] is False
    assert "real_platform_navigation_detected" in report["blockers"]
    
    # Executable publish trigger check
    state2 = {"live_publish_control_enabled": True}
    report2 = safety.validate_safety_compliance(state2)
    assert "executable_publish_control_detected" in report2["blockers"]
