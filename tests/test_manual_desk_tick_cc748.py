"""CC-748: the desk runs in its own task, never inside the minute posting job."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _tick():
    spec = importlib.util.spec_from_file_location("manual_desk_tick", ROOT / "scripts/manual_desk_tick.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tick_calls_the_desk_with_the_store_folders(tmp_path, monkeypatch, capsys):
    from live_contentops import manual_desk_v1 as desk
    seen = {}

    def hook(store_path, *, desk_root, binding_path, bot=None, now=None):
        seen.update(store=store_path, desk_root=desk_root, binding=binding_path)
        return {"status": "PAGE_WRITTEN", "packs": 2, "secret_like": "never printed"}

    monkeypatch.setattr(desk, "minute_hook", hook)
    store = tmp_path / "contentops.sqlite3"
    assert _tick().main(["--store", str(store)]) == 0
    assert seen == {"store": store, "desk_root": tmp_path / "manual_desk",
                    "binding": tmp_path / "control/x_reply_bot_binding.json"}
    printed = json.loads(capsys.readouterr().out)
    assert printed == {"status": "PAGE_WRITTEN", "packs": 2}


def test_a_desk_failure_is_reported_not_raised(tmp_path, monkeypatch, capsys):
    from live_contentops import manual_desk_v1 as desk

    def hook(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(desk, "minute_hook", hook)
    assert _tick().main(["--store", str(tmp_path / "s.sqlite3")]) == 0
    assert json.loads(capsys.readouterr().out) == {"status": "DESK_FAILED", "cause": "RuntimeError"}


def test_the_minute_posting_job_no_longer_runs_the_desk():
    text = (ROOT / "scripts/plan_status_posts.py").read_text(encoding="utf-8")
    assert "manual_desk_v1" not in text
