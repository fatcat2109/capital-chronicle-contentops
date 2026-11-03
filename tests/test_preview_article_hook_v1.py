"""Synthetic publication completion and detached hook; no live feed or child."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from live_contentops import preview_article_hook_v1 as hook
from live_contentops.published_content_v1 import append_record, read_records
from test_published_content_v1 import sealed


@pytest.fixture
def binding(tmp_path, monkeypatch):
    feed = tmp_path / "published.jsonl"
    root = tmp_path / "web"
    module = root / "tools/product/republish_preview_articles_v1.py"
    module.parent.mkdir(parents=True)
    module.write_bytes(b"synthetic consumer")
    config = tmp_path / "binding.json"
    config.write_text(json.dumps({"schema": "contentops.preview_mirror_binding.v1",
        "consumer_root": str(root), "consumer_module_sha256": sha256(module.read_bytes()).hexdigest()}))
    python = tmp_path / "python.exe"
    python.with_name("pythonw.exe").write_bytes(b"synthetic executable, never run")
    monkeypatch.setattr(hook, "FEED", feed)
    monkeypatch.setattr(hook, "CONFIG", config)
    monkeypatch.setattr(hook.sys, "executable", str(python))
    calls = []

    def start(command, **kwargs):
        calls.append((command, kwargs))
        assert read_records(feed)[0]["content_id"] == sealed()["content_id"]
        return SimpleNamespace(pid=456)

    monkeypatch.setattr(hook.subprocess, "Popen", start)
    return feed, root, module, config, calls


def test_new_confirmed_append_detaches_hidden_pythonw_after_feed_unlock(binding):
    feed, root, _, _, calls = binding
    result = append_record(feed, sealed())
    assert result["status"] == "APPENDED" and result["preview_mirror"] == {"status": "STARTED", "pid": 456}
    command, kwargs = calls[0]
    assert Path(command[0]).name == "pythonw.exe" and command[1:4] == ["-E", "-m", "tools.product.republish_preview_articles_v1"]
    assert command[4:] == ["--execute", "--record", str(feed)]
    assert kwargs["cwd"] == root and kwargs["shell"] is False
    assert kwargs["stdout"] == kwargs["stderr"] == kwargs["stdin"] == subprocess.DEVNULL
    assert kwargs["creationflags"] & subprocess.CREATE_NO_WINDOW
    assert kwargs["creationflags"] & subprocess.DETACHED_PROCESS
    assert "wait" not in kwargs


def test_duplicate_append_never_starts_another_job(binding):
    feed, _, _, _, calls = binding
    append_record(feed, sealed())
    before = feed.read_bytes()
    assert append_record(feed, sealed())["status"] == "ALREADY_RECORDED"
    assert len(calls) == 1 and feed.read_bytes() == before


def test_hook_failure_never_blocks_the_confirmed_feed_or_retries_publication(binding, monkeypatch):
    feed, _, _, _, _ = binding

    def fail(*args, **kwargs):
        raise RuntimeError("private diagnostic, never echoed")
    monkeypatch.setattr(hook, "launch_preview_mirror", fail)
    result = append_record(feed, sealed())
    assert result["status"] == "APPENDED"
    assert result["preview_mirror"] == {"status": "NOT_STARTED", "cause": "PREVIEW_HOOK_UNAVAILABLE"}
    assert len(read_records(feed)) == 1
    assert append_record(feed, sealed())["status"] == "ALREADY_RECORDED"


@pytest.mark.parametrize("bad", ["changed_module", "missing_config", "invalid_binding", "missing_pythonw"])
def test_unavailable_binding_is_destination_local_and_never_starts(binding, bad):
    feed, _, module, config, calls = binding
    if bad == "changed_module":
        module.write_bytes(b"unreviewed")
    elif bad == "missing_config":
        config.unlink()
    elif bad == "invalid_binding":
        config.write_text("{}")
    else:
        Path(hook.sys.executable).with_name("pythonw.exe").unlink()
    assert append_record(feed, sealed())["preview_mirror"]["status"] == "NOT_STARTED"
    assert not calls and len(read_records(feed)) == 1


def test_nonproduction_feed_cannot_launch_from_tests_or_backfill(binding):
    feed, root, _, _, calls = binding
    result = append_record(root / "test-feed.jsonl", sealed())
    assert result["preview_mirror"] == {"status": "SKIPPED", "cause": "NONPRODUCTION_FEED"}
    assert not calls and not feed.exists()
