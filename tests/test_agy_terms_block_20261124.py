"""Ops Product, 24 Nov 2026: Google disabled the Antigravity account for a Terms of Service violation; no ContentOps
code may start agy. Every caller gets a refusal without a process being started, and uses its fallback."""
from __future__ import annotations

import subprocess

import pytest

from live_contentops import agy_editorial_assist_v1 as assist
from live_contentops import agy_neo_answerer_v1 as answerer


def _no_process(*args, **kwargs):
    pytest.fail("agy was started")


def test_the_shared_runner_refuses_agy_without_starting_a_process(monkeypatch, tmp_path):
    monkeypatch.setattr(subprocess, "Popen", _no_process)
    done = assist._run([assist.AGY, "--print", "x"], cwd=tmp_path, timeout=5)
    assert done.returncode == 3 and done.stderr == assist.AGY_TERMS_BLOCK.encode() and done.stdout == b""


def test_the_block_names_agy_by_path_and_spares_other_programs():
    assert assist.agy_blocked(r"C:\Users\bullw\.gemini\bin\agy.exe") and assist.agy_blocked("agy")
    assert not assist.agy_blocked("codex.exe") and not assist.agy_blocked("python")


def test_the_posting_answerer_refuses_agy_without_starting_a_process(monkeypatch, tmp_path):
    monkeypatch.setattr(subprocess, "Popen", _no_process)
    runner = answerer.AgyRunner(scratch_root=tmp_path) if hasattr(answerer, "AgyRunner") else None
    if runner is None:
        runner = next(v for v in vars(answerer).values() if isinstance(v, type) and hasattr(v, "available"))(scratch_root=tmp_path)
    result = runner("post this")
    assert result == {"runner_status": "NOT_STARTED", "cause": assist.AGY_TERMS_BLOCK}
