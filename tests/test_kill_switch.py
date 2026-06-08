from live_contentops import kill_switch

def test_kill_switch_default():
    assert kill_switch.is_halted() is True
    assert kill_switch.status() == "all live actions blocked"
