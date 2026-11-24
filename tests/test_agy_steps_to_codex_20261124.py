"""Ops Product, 24 Nov 2026: every ContentOps step that used Antigravity runs on Codex gpt-6.2-sol.

Google disabled the Antigravity account for a Terms of Service violation; Jim ordered agy replaced by Codex,
with the effort chosen per task. Fake runners only: no Codex call, no agy process, no public write.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path
import subprocess

import pytest

from live_contentops import agy_editorial_assist_v1 as assist
from live_contentops import daily_note_first_draft_v1 as note
from live_contentops import light_model_caller_v1 as light
from live_contentops import public_draft_claims_v1 as claims
from live_contentops import x_reply_pack_v1 as packs
from live_contentops import x_reply_tabs_v1 as tabs


@pytest.fixture(autouse=True)
def no_process(monkeypatch):
    """No test here may start any process; an agy start is named in the failure."""
    started = []

    def popen(args, *a, **k):
        started.append(list(args))
        if any("agy" in Path(str(part)).name.lower() for part in args[:1]):
            pytest.fail("agy was started: " + str(args[0]))
        raise OSError("controlled: no process in this test")

    monkeypatch.setattr(subprocess, "Popen", popen)
    monkeypatch.setattr(light, "codex_executable", lambda: "codex.exe")
    return started


def codex_fake(answer, seen, *, returncode=0):
    """Stands in for `codex exec`: writes the final message where the CLI would."""
    def run(args, *, cwd, timeout, input):
        seen.append({"args": list(args), "timeout": timeout, "input": input})
        assert Path(args[0]).name == "codex.exe" and args[1] == "exec"
        if answer is not None:
            out = Path(args[args.index("--output-last-message") + 1])
            out.write_bytes(answer if isinstance(answer, bytes) else json.dumps(answer).encode())
        return subprocess.CompletedProcess(args, returncode, b"", b"")
    return run


def configured(call):
    args = call["args"]
    return args[args.index("--model") + 1], next(
        a for a in args if a.startswith("model_reasoning_effort=")).split("=", 1)[1].strip('"')


# The light caller -----------------------------------------------------------------------------

def test_the_light_caller_defaults_to_codex_only():
    assert inspect.signature(light.call_light).parameters["callers"].default == ("codex",)
    assert light.CODEX_MODEL == "gpt-6.2-sol"


def test_a_caller_still_naming_antigravity_falls_through_to_codex_without_a_process(tmp_path, no_process):
    seen = []
    answer, record = light.call_light("Do not call any tool. Say ok.", root=tmp_path, runner=None,
        callers=("antigravity", "codex"), timeout_cause="T", empty_cause="E")
    # The Codex attempt reached its (blocked-in-test) process start; agy never did.
    assert [a["caller"] for a in record["attempts"]] == ["antigravity", "codex"]
    assert record["attempts"][0]["status"] == "NOT_STARTED"
    assert record["attempts"][0]["cause"] == assist.AGY_TERMS_BLOCK
    assert no_process == [] or Path(no_process[0][0]).name == "codex.exe"
    answer, record = light.call_light("Do not call any tool. Say ok.", root=tmp_path / "2",
        runner=codex_fake(b"ok", seen), callers=("antigravity", "codex"), timeout_cause="T", empty_cause="E")
    assert answer == b"ok" and record["answered_by"] == "codex" and len(seen) == 1


# 1. X reply drafts (x_reply_tabs_v1) ---------------------------------------------------------

@pytest.fixture
def reply_setup(tmp_path):
    from test_x_reply_pack_cc455 import setup as pack_setup
    return pack_setup.__wrapped__(tmp_path)


def test_x_reply_draft_runs_on_codex_low_and_passes_the_pack_checks(reply_setup):
    from test_x_reply_pack_cc455 import NOW, response_for
    store, feed, root = reply_setup
    ready, response, _ = response_for(reply_setup)
    response.pop("request_sha256")
    seen = []
    path = tabs.draft_with_agy(ready["request_path"], output_dir=root / "agy", runner=codex_fake(response, seen))
    assert len(seen) == 1 and configured(seen[0]) == ("gpt-6.2-sol", "low")
    assert seen[0]["timeout"] == tabs.DRAFT_TIMEOUT_SECONDS
    record = packs.read_json(root / "agy" / "call.json")
    assert (record["caller"], record["model"], record["effort"]) == ("codex", "gpt-6.2-sol", "low")
    assert record["configuration_status"] == "CONFIGURED_NOT_OBSERVED"
    assert "antigravity" not in json.dumps(record).lower()
    built = packs.build(store, request_path=ready["request_path"], response_path=path,
                        feed_path=feed, output_root=root, now=NOW)
    assert built["item_count"] == 1


@pytest.mark.parametrize("bad", ["not json", "changed target", "empty"])
def test_a_bad_x_reply_answer_fails_the_draft_and_keeps_the_waiting_group(reply_setup, bad):
    from test_x_reply_pack_cc455 import response_for
    store, feed, root = reply_setup
    ready, response, _ = response_for(reply_setup)
    if bad == "changed target":
        response["items"][0]["post_id"] = "someone-else"
    answer = b"" if bad == "empty" else b"{not json" if bad == "not json" else response
    with pytest.raises(ValueError):
        tabs.draft_with_agy(ready["request_path"], output_dir=root / "agy", runner=codex_fake(answer, []))
    # The refresh owner turns the raise into REFRESH_FAILED and leaves the waiting tabs unchanged.
    calls = list((root / "agy").glob("*/call.json"))
    assert calls and packs.read_json(calls[0])["status"] == "DRAFT_FAILED"


def test_x_reply_draft_with_no_runner_never_starts_agy(reply_setup, no_process):
    store, feed, root = reply_setup
    ready = packs.prepare(store, feed_path=feed, output_root=root, now=__import__("test_x_reply_pack_cc455").NOW)
    with pytest.raises(ValueError):
        tabs.draft_with_agy(ready["request_path"], output_dir=root / "agy")
    assert no_process and all(Path(args[0]).name == "codex.exe" for args in no_process)


# 2. The daily Note's first draft (daily_note_first_draft_v1) ---------------------------------

def test_daily_note_draft_runs_on_codex_medium_and_passes_the_article_checks(tmp_path):
    from test_daily_note_first_draft_cc403 import governed, output
    from live_contentops.reader_article_contract_v1 import GUIDANCE
    seen = []
    record = note.prepare_first_draft(governed(), GUIDANCE, output_dir=tmp_path, runner=codex_fake(output(), seen))
    assert len(seen) == 1 and configured(seen[0]) == ("gpt-6.2-sol", "medium")
    assert seen[0]["timeout"] == note.DRAFT_TIMEOUT_SECONDS
    assert record["status"] == "DRAFT_CHECKS_PASS", record.get("checks") or record.get("cause")
    assert (record["caller"], record["model"], record["effort"]) == ("codex", "gpt-6.2-sol", "medium")
    assert record["configuration_status"] == "CONFIGURED_NOT_OBSERVED" and record["provider_call_attempted"]
    # The exact prompt resumes its saved result: one Codex call per prompt.
    assert note.prepare_first_draft(governed(), GUIDANCE, output_dir=tmp_path,
        runner=lambda *a, **k: pytest.fail("repeated call")) == record


@pytest.mark.parametrize("bad", ["empty", "exit", "schema", "bad_number"])
def test_a_bad_daily_note_answer_returns_to_the_editors_own_pass(tmp_path, bad):
    from test_daily_note_first_draft_cc403 import governed, output
    from live_contentops.reader_article_contract_v1 import GUIDANCE
    value = output()
    if bad == "bad_number":
        value["article"]["substack_body_markdown"] += "\n\nThe yield was 99.9%. [[SOURCE:SOURCE_1]]"
    answer = b"" if bad == "empty" else {"article": {}} if bad == "schema" else value
    record = note.prepare_first_draft(governed(), GUIDANCE, output_dir=tmp_path,
        runner=codex_fake(answer, [], returncode=7 if bad == "exit" else 0))
    if bad == "bad_number":
        assert record["status"] == "NEEDS_EDITOR_FIX" and any("99.9%" in c for c in record["checks"])
    else:
        # The native editor writes the note itself in its one pass (the fixed fallback).
        assert record["status"] == "AGY_UNAVAILABLE" and record["cause"] and record["output"] is None


def test_daily_note_draft_with_no_runner_never_starts_agy(tmp_path, no_process):
    from test_daily_note_first_draft_cc403 import governed
    from live_contentops.reader_article_contract_v1 import GUIDANCE
    record = note.prepare_first_draft(governed(), GUIDANCE, output_dir=tmp_path)
    assert record["status"] == "AGY_UNAVAILABLE" and record["caller"] == "codex"
    assert no_process and all(Path(args[0]).name == "codex.exe" for args in no_process)


# 3. The editorial light text (agy_editorial_assist_v1, CC-378) ------------------------------

def test_editorial_light_text_runs_on_codex_medium_and_passes_its_checks(tmp_path):
    from test_agy_editorial_assist_cc378 import approve, packet, recorded_output
    draft, sources, assets = packet()
    seen = []
    record = assist.prepare_assist(draft, sources, assets, output_dir=tmp_path,
                                   runner=codex_fake(recorded_output(), seen))
    assert len(seen) == 1 and configured(seen[0]) == ("gpt-6.2-sol", "medium")
    assert seen[0]["timeout"] == assist.ASSIST_TIMEOUT_SECONDS
    assert seen[0]["input"].decode().startswith("Do not call any tool")
    assert record["status"] == "AGY_AVAILABLE"
    assert (record["caller"], record["model"], record["effort"]) == ("codex", "gpt-6.2-sol", "medium")
    assert "agy" not in record and record["configuration_status"] == "CONFIGURED_NOT_OBSERVED"
    approve(tmp_path, record)
    article, media = assist.consume_assist(draft, assets, output_dir=tmp_path)
    assert media[0]["alt_text"] == recorded_output()["alt_text"][0]["text"]
    assert article["agy_light_assist"]["variant_destinations"] == sorted(assist.LIMITS)


def test_an_unsupported_number_in_codex_light_text_is_rejected_and_the_original_copy_stays(tmp_path):
    from test_agy_editorial_assist_cc378 import approve, packet, recorded_output
    draft, sources, assets = packet()
    bad = recorded_output()
    bad["alt_text"][0]["text"] = "A chart of 7 observations."
    bad["variants"]["telegram"] = "The source line reports 9 observations."
    record = assist.prepare_assist(draft, sources, assets, output_dir=tmp_path, runner=codex_fake(bad, []))
    approve(tmp_path, record)
    article, media = assist.consume_assist(draft, assets, output_dir=tmp_path)
    assert media[0]["alt_text"] == assets[0]["alt_text"]
    assert "telegram" not in article.get("publisher_light_variants", {})
    assert any("UNSUPPORTED_NUMBER" in cause for cause in article["agy_light_assist"]["rejected_suggestions"])


@pytest.mark.parametrize("bad", [b"", b"{\"variants\": {}}", b"not json"])
def test_a_bad_editorial_answer_keeps_the_original_copy(tmp_path, bad):
    from test_agy_editorial_assist_cc378 import packet
    draft, sources, assets = packet()
    record = assist.prepare_assist(draft, sources, assets, output_dir=tmp_path, runner=codex_fake(bad, []))
    assert record["status"] == "AGY_UNAVAILABLE" and record["cause"]
    article, media = assist.consume_assist(draft, assets, output_dir=tmp_path)
    assert article["substack_body_markdown"] == draft["substack_body_markdown"]
    assert "publisher_light_variants" not in article and media == assets


def test_editorial_light_text_with_no_runner_never_starts_agy(tmp_path, no_process):
    from test_agy_editorial_assist_cc378 import packet
    draft, sources, assets = packet()
    record = assist.prepare_assist(draft, sources, assets, output_dir=tmp_path)
    assert record["status"] == "AGY_UNAVAILABLE" and record["caller"] == "codex"
    assert no_process and all(Path(args[0]).name == "codex.exe" for args in no_process)


# The steps that named Antigravity explicitly --------------------------------------------------

def test_the_claim_check_asks_codex_low_and_drops_light_draft_sentences_it_cannot_source(tmp_path):
    seen = []

    def call(prompt, **kwargs):
        seen.append(kwargs)
        return b'{"claims": []}', {"status": "RETURNED", "answered_by": "codex"}

    review = claims.check_draft("d1", "x_reply", [{"text": "Wages rose 9.9% in May.", "origin": "codex_light"}],
                                {"fact": {"excerpt": "Wages rose 0.7% in May."}}, output_dir=tmp_path, call=call)
    assert seen[0]["callers"] == ("codex",) and seen[0]["codex_effort"] == "low"
    assert review["corrected"] == [""] and review["flags"][0]["action"] == "SENTENCE_DROPPED"


def test_no_light_step_names_antigravity_as_its_caller():
    root = Path(light.__file__).parent
    for name in ("public_draft_claims_v1.py", "plan_reader_editorial_v1.py", "market_wrap_editorial_v1.py",
                 "image_quality_v1.py", "x_reply_bot_v1.py", "x_reply_tabs_v1.py", "daily_note_first_draft_v1.py",
                 "agy_editorial_assist_v1.py"):
        text = (root / name).read_text(encoding="utf-8")
        assert '"antigravity",' not in text.replace('{"antigravity", "codex_light"}', ""), name
        assert "[AGY," not in text, name
