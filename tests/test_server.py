import json

from live_contentops import server


def test_run_id_from_stdout_reads_final_status_line():
    stdout = 'noise\n[FinalStatus] {"run_id": "v6_pipeline_abc", "pipeline_status": "DISPATCH_BLOCKED"}\ntail\n'
    assert server._run_id_from_stdout(stdout) == "v6_pipeline_abc"


def test_run_id_from_stdout_missing_returns_none():
    assert server._run_id_from_stdout("no final status here") is None


def test_read_dispatch_audit_rejects_stale_run(tmp_path, monkeypatch):
    audit = tmp_path / "latest_dispatch_audit.json"
    audit.write_text(json.dumps({"run_id": "other", "pipeline_status": "DISPATCH_COMPLETE"}), encoding="utf-8")
    monkeypatch.setattr(server, "DISPATCH_AUDIT_PATH", str(audit))
    assert server._read_dispatch_audit("v6_pipeline_abc") is None


def test_read_dispatch_audit_returns_blocked_outcome(tmp_path, monkeypatch):
    audit = tmp_path / "latest_dispatch_audit.json"
    audit.write_text(
        json.dumps({
            "run_id": "v6_pipeline_abc",
            "pipeline_status": "DISPATCH_BLOCKED",
            "dispatch_live": False,
            "dispatch_blockers": ["article_too_short_words:127<2000"],
            "dispatch_summary": {"blocked_platforms": ["pipeline"]},
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(server, "DISPATCH_AUDIT_PATH", str(audit))
    outcome = server._read_dispatch_audit("v6_pipeline_abc")
    assert outcome["pipeline_status"] == "DISPATCH_BLOCKED"
    assert outcome["dispatch_blockers"] == ["article_too_short_words:127<2000"]
    assert "DISPATCH_COMPLETE" in server.LIVE_SUCCESS_STATUSES


def test_trim_tasks_keeps_latest_started_tasks(monkeypatch):
    monkeypatch.setattr(server, "MAX_RETAINED_TASKS", 2)
    server.TASKS.clear()
    server.TASKS.update({
        "old": {"started_at": "2026-01-01T00:00:00Z"},
        "mid": {"started_at": "2026-01-02T00:00:00Z"},
        "new": {"started_at": "2026-01-03T00:00:00Z"},
    })
    server._trim_tasks()
    assert set(server.TASKS) == {"mid", "new"}
    server.TASKS.clear()
