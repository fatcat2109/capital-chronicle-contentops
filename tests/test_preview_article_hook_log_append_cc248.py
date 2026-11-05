"""CC-248, 5 Nov: a queued preview worker never overwrites another worker's log output.

On 5 Nov the worker started by the PPI append (00:34Z) waited in its load window and published
at 02:32Z. The worker started by the Southwest append (02:28Z) queued on the mutex, then wrote
its UNCHANGED result from byte 0 over the PUBLISHED result. The hook now opens the log so that
every write a child makes lands at the end of the file.
"""
import os
from pathlib import Path
import subprocess
import sys

import pytest

from live_contentops import preview_article_hook_v1 as hook
from live_contentops.published_content_v1 import append_record
from test_preview_article_hook_v1 import binding  # noqa: F401  (fixture)
from test_published_content_v1 import sealed

pytestmark = pytest.mark.skipif(os.name != "nt", reason="the hook launches its worker only on Windows (pythonw)")


def _child(log, text, delay):
    code = f"import sys, time; time.sleep({delay}); sys.stdout.write({text!r}); sys.stdout.flush()"
    with hook._open_worker_log(log) as handle:
        return subprocess.Popen([sys.executable, "-E", "-c", code], stdin=subprocess.DEVNULL,
                                stdout=handle, stderr=handle, close_fds=True,
                                creationflags=subprocess.CREATE_NO_WINDOW)


def test_two_queued_workers_both_keep_their_output(tmp_path):
    log = tmp_path / "preview_article_worker.log"
    log.write_bytes(b"earlier run\n")
    # Both handles are opened before either child writes, as on 5 Nov.
    first = _child(log, "PUBLISHED e57b0f1c\n", 1.0)
    second = _child(log, "UNCHANGED e57b0f1c\n", 2.5)
    assert first.wait(timeout=60) == 0 and second.wait(timeout=60) == 0
    lines = log.read_bytes().decode().splitlines()
    # Before the fix both children wrote from byte 12, and the second line replaced the first.
    assert lines[0] == "earlier run"
    assert sorted(lines[1:]) == ["PUBLISHED e57b0f1c", "UNCHANGED e57b0f1c"]


def test_a_write_at_offset_zero_still_lands_at_the_end(tmp_path):
    import _winapi
    import msvcrt
    log = tmp_path / "preview_article_worker.log"
    log.write_bytes(b"PUBLISHED\n")
    with hook._open_worker_log(log) as handle:
        fd = handle.fileno()
        os.lseek(fd, 0, os.SEEK_SET)  # the offset a handle opened before the last write keeps
        written, error = _winapi.WriteFile(msvcrt.get_osfhandle(fd), b"UNCHANGED\n")
        assert (written, error) == (10, 0)
    assert log.read_bytes() == b"PUBLISHED\nUNCHANGED\n"


def test_the_hook_starts_the_worker_on_the_append_only_log(binding, monkeypatch):  # noqa: F811
    feed, _, _, _, calls = binding
    opened = []
    real = hook._open_worker_log

    def record(path):
        handle = real(path)
        opened.append((Path(path), handle))
        return handle

    monkeypatch.setattr(hook, "_open_worker_log", record)
    result = append_record(feed, sealed())
    assert result["preview_mirror"]["status"] == "STARTED"
    assert [path for path, _ in opened] == [feed.with_name("preview_article_worker.log")]
    _, kwargs = calls[0]
    assert kwargs["stdout"] is opened[0][1] and kwargs["stderr"] is opened[0][1]
    assert Path(kwargs["stdout"].name).name == "preview_article_worker.log"
