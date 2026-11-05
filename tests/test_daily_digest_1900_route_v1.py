"""CC-143 19:00 route helper. No browser, store, provider or production access."""
import importlib.util
import socket
import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_daily_digest_1900.py"
spec = importlib.util.spec_from_file_location("run_daily_digest_1900", SCRIPT)
route = importlib.util.module_from_spec(spec)
spec.loader.exec_module(route)


def at(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def test_early_wake_is_not_due_and_names_todays_digest():
    # The 4 Nov Codex window entered at 18:59:59.78 GMT+7 and saw only the 3 Nov digest.
    early = route.due_state(at("2026-11-04T11:59:59.783221Z"))
    assert early["state"] == "NOT_YET_DUE"
    assert early["digest_id"] == "cc143-digest-2026-11-04"
    assert early["due_at_utc"] == "2026-11-04T12:00:00+00:00"
    assert route.due_state(at("2026-11-04T12:00:00Z"))["state"] == "DUE"
    late = route.due_state(at("2026-11-04T16:59:00Z"))  # 23:59 GMT+7, same digest day
    assert (late["state"], late["digest_id"]) == ("DUE", "cc143-digest-2026-11-04")


def test_naive_clock_is_refused():
    with pytest.raises(ValueError, match="EXPLICIT_DIGEST_CLOCK_REQUIRED"):
        route.due_state(datetime(2026, 11, 5, 12))


def test_invocation_label_and_commands_carry_the_claude_surface():
    label = route.default_invocation_id(at("2026-11-05T12:05:07Z"))
    assert label == "claude-code-session:cc143-digest-1900:20261105T120507Z"
    commands = route._commands("config/native_desktop_rollout_v1.json", label)
    assert "run_daily_digest_1900.py resume" in commands["resume"] and label in commands["resume"]
    assert "digest-tool-begin" in commands["begin"] and "--request-sha256" in commands["begin"]
    assert "digest-tool-submit" in commands["submit"] and "--response" in commands["submit"]
    assert commands["observation"]["surface"] == "CLAUDE_CODE_SESSION"
    assert commands["observation"]["tool_name"] == "mcp__browseros-neo__run"


def test_early_resume_stops_before_any_store_or_rollout_read(tmp_path):
    result = route.resume(tmp_path / "absent-rollout.json", "label", now=at("2026-11-05T11:59:59Z"))
    assert result["route_state"] == "NOT_YET_DUE" and result["public_write_performed"] is False


def test_summary_flattens_the_next_request():
    summary = route.summarize_continuation({"state": "NATIVE_NEO_TOOL_PENDING", "digest_id": "d",
        "publication": {"recovery_preflight": {"per_destination": {"substack": {"native_tool_request": {
            "tool_request_sha256": "t", "public_write_authorized": True,
            "request": {"action": "PUBLISH", "destination": "substack", "request_sha256": "r"}}}}}}})
    assert summary["next_request"] == {"action": "PUBLISH", "destination": "substack", "request_sha256": "r",
                                       "tool_request_sha256": "t", "public_write_authorized": True}


def test_first_pending_reads_every_owner_shape():
    raised = {"native_tool_request": {"request": {"action": "VERIFY_IDENTITY"}}}
    assert route._first_pending(raised)["request"]["action"] == "VERIFY_IDENTITY"
    listed = {"pending_requests": [{"request": {"action": "A"}, "action_claimed": True},
                                   {"request": {"action": "B"}, "action_claimed": False}]}
    assert route._first_pending(listed)["request"]["action"] == "B"
    nested = {"publication": {"recovery_preflight": {"per_destination": {"substack": {
        "native_tool_request": {"request": {"action": "PUBLISH"}}}}}}}
    assert route._first_pending(nested)["request"]["action"] == "PUBLISH"
    assert route._first_pending({"state": "CONFIRMED"}) == {}


def test_guard_confines_writes_and_refuses_network(tmp_path):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    outside = tmp_path / "shared.txt"
    guard = route._Guard(scratch, [outside])
    with guard.active():
        (scratch / "ok.txt").write_text("ok", encoding="utf-8")
        (scratch / "sub").mkdir()
        with pytest.raises(PermissionError):
            outside.write_text("no", encoding="utf-8")
        with pytest.raises(PermissionError):
            sqlite3.connect(tmp_path / "shared.sqlite3")
        with pytest.raises(ConnectionRefusedError):
            socket.create_connection(("127.0.0.1", 9))
        assert outside.read_text(encoding="utf-8") if outside.exists() else True
    assert not outside.exists() and not (tmp_path / "shared.sqlite3").exists()
    assert len(guard.refused_writes) == 2 and len(guard.refused_connections) == 1
    # Restored after the block.
    outside.write_text("after", encoding="utf-8")
    assert outside.read_text(encoding="utf-8") == "after"
