import json
from pathlib import Path
from live_contentops.telegram_supervised_post_queue import process_queue, generate_content_hash

def load_fixture(name):
    path = Path(f"fixtures/telegram_supervised_post_queue/{name}.json")
    return json.loads(path.read_text())

def test_valid_single_queue_item():
    q = load_fixture("valid_single_queue_item")
    res = process_queue(q)
    assert res["queue_status"] == "VALID"

def test_valid_queue_with_duplicate_marked_blocked():
    q = load_fixture("valid_queue_with_duplicate_marked_blocked")
    res = process_queue(q)
    assert res["queue_status"] == "VALID"

def test_invalid_live_execution_allowed_now():
    q = load_fixture("invalid_live_execution_allowed_now")
    res = process_queue(q)
    assert res["queue_status"] == "BLOCKED"
    assert any("Live/network capability flags must be false" in r for r in res["reasons"])

def test_invalid_public_channel_target():
    q = load_fixture("invalid_public_channel_target")
    res = process_queue(q)
    assert res["queue_status"] == "BLOCKED"
    assert any("Public targets and public postable content are forbidden" in r for r in res["reasons"])

def test_invalid_real_channel_id_present():
    q = load_fixture("invalid_real_channel_id_present")
    res = process_queue(q)
    assert res["queue_status"] == "BLOCKED"
    assert any("Real channel IDs cannot be committed" in r for r in res["reasons"])

def test_invalid_forbidden_signal_language():
    q = load_fixture("invalid_forbidden_signal_language")
    # Update hash to avoid hash mismatch error hiding the actual failure
    q["items"][0]["content_hash"] = generate_content_hash(q["items"][0]["post_text"])
    res = process_queue(q)
    assert res["queue_status"] == "BLOCKED"
    assert any("Forbidden financial/signal language found: buy" in r for r in res["reasons"])

def test_invalid_publish_ready_true():
    q = load_fixture("invalid_publish_ready_true")
    res = process_queue(q)
    assert res["queue_status"] == "BLOCKED"
    assert any("publish_ready must be false" in r for r in res["reasons"])
