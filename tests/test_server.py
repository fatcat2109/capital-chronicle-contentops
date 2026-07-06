from live_contentops import server


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
