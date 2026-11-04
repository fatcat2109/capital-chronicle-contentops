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
    (root / "ui/node_modules").mkdir(parents=True)
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
    monkeypatch.setattr(hook.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0))
    return feed, root, module, config, calls


def test_new_confirmed_append_detaches_hidden_pythonw_after_feed_unlock(binding):
    feed, root, _, _, calls = binding
    result = append_record(feed, sealed())
    assert result["status"] == "APPENDED" and result["preview_mirror"]["status"] == "STARTED"
    assert result["preview_mirror"]["pid"] == 456
    assert result["preview_mirror"]["consumer_module_sha256"] == sha256(b"synthetic consumer").hexdigest()
    command, kwargs = calls[0]
    assert Path(command[0]).name == "pythonw.exe" and command[1:4] == ["-E", "-m", "tools.product.republish_preview_articles_v1"]
    assert command[4:] == ["--execute", "--record", str(feed)]
    assert kwargs["cwd"] == root and kwargs["shell"] is False
    assert kwargs["stdin"] == subprocess.DEVNULL
    assert kwargs["stdout"] == kwargs["stderr"]
    assert Path(kwargs["stdout"].name).name == "preview_article_worker.log"
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


@pytest.mark.parametrize("bad", ["missing_module", "missing_config", "invalid_binding", "missing_pythonw"])
def test_unavailable_binding_is_destination_local_and_never_starts(binding, bad):
    feed, _, module, config, calls = binding
    if bad == "missing_module":
        module.unlink()
    elif bad == "missing_config":
        config.unlink()
    elif bad == "invalid_binding":
        config.write_text("{}")
    else:
        Path(hook.sys.executable).with_name("pythonw.exe").unlink()
    assert append_record(feed, sealed())["preview_mirror"]["status"] == "NOT_STARTED"
    assert not calls and len(read_records(feed)) == 1


def test_changed_public_write_worker_needs_review_before_launch(binding):
    feed, _, module, _, calls = binding
    module.write_bytes(b"repaired consumer with exact-folder guard")
    result = append_record(feed, sealed())["preview_mirror"]
    assert result["status"] == "NOT_STARTED" and not calls
    assert result["cause"] == "CONSUMER_SOURCE_CHANGED"
    assert result["consumer_module_sha256"] == sha256(module.read_bytes()).hexdigest()



def test_nonproduction_feed_cannot_launch_from_tests_or_backfill(binding):
    feed, root, _, _, calls = binding
    result = append_record(root / "test-feed.jsonl", sealed())
    assert result["preview_mirror"] == {"status": "SKIPPED", "cause": "NONPRODUCTION_FEED"}
    assert not calls and not feed.exists()


def test_missing_jsonschema_is_named_before_detach(binding, monkeypatch):
    feed, _, _, _, calls = binding
    monkeypatch.setattr(hook.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=1))
    result = append_record(feed, sealed())["preview_mirror"]
    assert result == {"status": "NOT_STARTED", "cause": "CONSUMER_PYTHON_DEPENDENCY_MISSING:jsonschema"}
    assert not calls


def test_shared_node_dependencies_never_run_a_public_write_worker(binding, monkeypatch):
    feed, root, _, _, calls = binding
    original = Path.resolve
    dependencies = root / "ui/node_modules"
    def resolve(path, *args, **kwargs):
        return root / "other-lane/node_modules" if path == dependencies else original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "resolve", resolve)
    result = append_record(feed, sealed())["preview_mirror"]
    assert result == {"status": "NOT_STARTED", "cause": "CONSUMER_NODE_DEPENDENCIES_SHARED"}
    assert not calls


def _fake_python(folder, *, pythonw=True):
    folder.mkdir(parents=True, exist_ok=True)
    python = folder / "python.exe"
    python.write_bytes(b"synthetic executable, never run")
    if pythonw:
        python.with_name("pythonw.exe").write_bytes(b"synthetic executable, never run")
    return python


def _probe(ok):
    """subprocess.run stand-in: jsonschema imports only for interpreters named in ok."""
    seen = []

    def run(command, **kwargs):
        seen.append(command[0])
        return SimpleNamespace(returncode=0 if command[0] in ok else 1)
    return run, seen


def test_venv_without_jsonschema_falls_back_to_checked_system_python(binding, monkeypatch, tmp_path):
    # CC-248 (Ops Product, 5 Nov): the ContentOps runtime venv has no jsonschema; nothing is
    # installed there. The worker runs with the runbook's system Python found on PATH instead.
    feed, _, _, _, calls = binding
    system = _fake_python(tmp_path / "Python313")
    monkeypatch.setattr(hook.shutil, "which", lambda name: str(system) if name == "python" else None)
    run, seen = _probe({str(system)})
    monkeypatch.setattr(hook.subprocess, "run", run)
    result = append_record(feed, sealed())["preview_mirror"]
    assert result["status"] == "STARTED" and result["worker_python_fallback"] == str(system)
    assert seen == [hook.sys.executable, str(system)]
    assert calls[0][0][0] == str(system.with_name("pythonw.exe"))


def test_configured_worker_python_is_checked_before_it_is_used(binding, monkeypatch, tmp_path):
    feed, _, _, config, calls = binding
    no_pythonw = _fake_python(tmp_path / "configured", pythonw=False)
    on_path = _fake_python(tmp_path / "onpath")
    value = json.loads(config.read_text())
    config.write_text(json.dumps({**value, "worker_python": str(no_pythonw)}))
    monkeypatch.setattr(hook.shutil, "which", lambda name: str(on_path))
    run, seen = _probe({str(no_pythonw), str(on_path)})
    monkeypatch.setattr(hook.subprocess, "run", run)
    result = append_record(feed, sealed())["preview_mirror"]
    # The configured interpreter has no pythonw beside it, so it is never probed or run.
    assert result["worker_python_fallback"] == str(on_path) and str(no_pythonw) not in seen
    assert calls[0][0][0] == str(on_path.with_name("pythonw.exe"))


def test_no_interpreter_with_jsonschema_keeps_the_named_cause(binding, monkeypatch, tmp_path):
    feed, _, _, _, calls = binding
    store_alias = tmp_path / "WindowsApps" / "python.exe"
    _fake_python(store_alias.parent)
    system = _fake_python(tmp_path / "Python313")
    for found in (None, str(store_alias), str(system)):
        monkeypatch.setattr(hook.shutil, "which", lambda name, found=found: found)
        run, seen = _probe(set())
        monkeypatch.setattr(hook.subprocess, "run", run)
        result = hook.launch_preview_mirror(feed)
        assert result == {"status": "NOT_STARTED", "cause": "CONSUMER_PYTHON_DEPENDENCY_MISSING:jsonschema"}
        assert str(store_alias) not in seen  # a Store alias never runs
    assert not calls
