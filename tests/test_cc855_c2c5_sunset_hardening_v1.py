"""CC-855 ContentOps C2-C5 sunset hardening hermetic regression tests.

Strictly offline and isolated under tmp_path: zero live browser, zero network,
zero writes outside tmp_path, zero Claude/AGY process spawns.

Operator: T3 Code, Gemini 4 Neon xhigh, antigravity_14
"""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

import pytest

from live_contentops import agy_editorial_assist_v1 as assist
from live_contentops import agy_neo_answerer_v1 as agy_neo
from live_contentops import ai_research_canonical_article_engine_v6 as v6_engine
from live_contentops import native_desktop_editorial_v1 as editorial
from live_contentops import substack_first_north_star_pipeline_loop_v1 as substack_loop
from live_contentops import tier1_editorial_quality_v1 as tier1_quality
from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from test_native_editorial_claude_cc300 import claude as claude_obs
from test_native_neo_composed_run_cc283 import composed_setup, pending_publish

REPO_ROOT = Path(__file__).resolve().parents[1]
EDITORIAL_CLI = REPO_ROOT / "scripts" / "run_native_desktop_editorial.py"
MOCK_CHECK_CLI = REPO_ROOT / "scripts" / "agy_neo_mock_check_cc798.py"


def _load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _isolated_profile(tmp_path: Path) -> dict[str, str]:
    store_path = tmp_path / "state.sqlite3"
    ContentOpsDurableStore(store_path)
    out_root = tmp_path / "editorial"
    pub_root = tmp_path / "published"
    out_root.mkdir(parents=True, exist_ok=True)
    pub_root.mkdir(parents=True, exist_ok=True)
    pointer = tmp_path / "feed_pointer.json"
    pointer.write_text(json.dumps({"research_root": str(tmp_path / "research")}), encoding="utf-8")
    return {
        "schema_version": "contentops.native_desktop_operator_profile.v1",
        "store_path": str(store_path),
        "editorial_output_root": str(out_root),
        "feed_pointer_path": str(pointer),
        "published_memory_store": str(store_path),
        "published_memory_output_root": str(pub_root),
    }


# ---------------------------------------------------------------------------
# C2: Post-2026-12-03T17:00:00Z refusal gate for new --editorial-agent claude
# ---------------------------------------------------------------------------


def test_c2_claude_sunset_boundary_clock_and_env():
    before = datetime(2026, 12, 3, 16, 59, 59, tzinfo=timezone.utc)
    at_cutoff = datetime(2026, 12, 3, 17, 0, 0, tzinfo=timezone.utc)
    after = datetime(2026, 12, 4, 0, 0, 0, tzinfo=timezone.utc)

    assert editorial.CLAUDE_SUNSET_UTC == at_cutoff
    assert editorial.claude_sunset_active(before, env={}) is False
    assert editorial.claude_sunset_active("2026-12-03T16:59:59Z", env={}) is False
    assert editorial.claude_sunset_active(at_cutoff, env={}) is True
    assert editorial.claude_sunset_active("2026-12-03T17:00:00Z", env={}) is True
    assert editorial.claude_sunset_active(after, env={}) is True
    assert editorial.claude_sunset_active(before, env={"CC_CLAUDE_SUNSET_ACTIVE": "1"}) is True
    assert editorial.claude_sunset_active(before, force=True) is True

    assert editorial.assert_new_editorial_agent_allowed("claude", now=before, wall_now=before, env={}) == "claude"
    assert editorial.assert_new_editorial_agent_allowed("codex", now=after, env={"CC_CLAUDE_SUNSET_ACTIVE": "1"}) == "codex"
    assert editorial.assert_new_editorial_agent_allowed(None, now=after, env={"CC_CLAUDE_SUNSET_ACTIVE": "1"}) == "codex"
    with pytest.raises(ValueError, match=editorial.CLAUDE_EDITORIAL_AGENT_RETIRED):
        editorial.assert_new_editorial_agent_allowed("claude", now=at_cutoff, env={})
    with pytest.raises(ValueError, match=editorial.CLAUDE_EDITORIAL_AGENT_RETIRED):
        editorial.assert_new_editorial_agent_allowed("claude", now=before, env={"CC_CLAUDE_SUNSET_ACTIVE": "true"})


def test_c2_new_claude_binding_refused_post_sunset_and_on_env_flag(tmp_path, monkeypatch):
    cli = _load_script("run_native_desktop_editorial_c2", EDITORIAL_CLI)
    profile = _isolated_profile(tmp_path)
    req = "Prepare one clean analysis note covering US Treasury auction demand."
    monkeypatch.delenv(editorial.CLAUDE_SUNSET_ENV, raising=False)

    # Exact post-sunset UTC boundary fails closed with zero filesystem write.
    with pytest.raises(ValueError, match=editorial.CLAUDE_EDITORIAL_AGENT_RETIRED):
        cli.resolve_owner_operation(
            profile,
            operation_id="claude-at-sunset",
            request=req,
            now=datetime(2026, 12, 3, 17, 0, 0, tzinfo=timezone.utc),
            editorial_agent="claude",
        )
    assert not (Path(profile["editorial_output_root"]) / "claude-at-sunset").exists()

    # Env override forces immediate refusal even before the UTC cutoff.
    monkeypatch.setenv(editorial.CLAUDE_SUNSET_ENV, "1")
    with pytest.raises(ValueError, match=editorial.CLAUDE_EDITORIAL_AGENT_RETIRED):
        cli.resolve_owner_operation(
            profile,
            operation_id="claude-env-override",
            request=req,
            now=datetime(2026, 11, 26, 12, 0, 0, tzinfo=timezone.utc),
            editorial_agent="claude",
        )
    assert not (Path(profile["editorial_output_root"]) / "claude-env-override").exists()

    # Codex bindings remain unaffected post-sunset and with CC_CLAUDE_SUNSET_ACTIVE=1.
    codex_path, codex_binding = cli.resolve_owner_operation(
        profile,
        operation_id="codex-post-sunset",
        request=req,
        now=datetime(2026, 12, 5, 10, 0, 0, tzinfo=timezone.utc),
        editorial_agent="codex",
    )
    assert codex_path.is_file()
    assert "editorial_agent" not in codex_binding

    # Pre-sunset without env flag still permits pre-cutoff binding creation.
    monkeypatch.delenv(editorial.CLAUDE_SUNSET_ENV, raising=False)
    pre_before = datetime(2026, 12, 3, 16, 59, 59, tzinfo=timezone.utc)
    pre_path, pre_binding = cli.resolve_owner_operation(
        profile,
        operation_id="claude-before-sunset",
        request=req,
        now=pre_before,
        wall_now=pre_before,
        editorial_agent="claude",
    )
    assert pre_path.is_file()
    assert pre_binding["editorial_agent"] == "claude"


def test_c2_cli_newsroom_refuses_new_claude_binding_when_sunset_active(tmp_path, monkeypatch, capsys):
    cli = _load_script("run_native_desktop_editorial_c2_cli", EDITORIAL_CLI)
    profile = _isolated_profile(tmp_path)
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    monkeypatch.setenv(editorial.CLAUDE_SUNSET_ENV, "1")

    rc = cli.main([
        "newsroom",
        "--profile", str(profile_path),
        "--operation-id", "claude-cli-blocked",
        "--request", "Prepare one clean analysis note covering US Treasury auction demand.",
        "--editorial-agent", "claude",
    ])
    captured = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert rc == 2
    assert captured["classification"] == "NATIVE_DESKTOP_BLOCKED"
    assert captured["blocker"] == editorial.CLAUDE_EDITORIAL_AGENT_RETIRED
    assert not (Path(profile["editorial_output_root"]) / "claude-cli-blocked").exists()


def test_c2_historical_claude_session_replay_preserved_after_sunset(tmp_path, monkeypatch):
    cli = _load_script("run_native_desktop_editorial_c2_replay", EDITORIAL_CLI)
    profile = _isolated_profile(tmp_path)
    req = "Historical pre-sunset Claude editorial operation for readback proof."
    monkeypatch.delenv(editorial.CLAUDE_SUNSET_ENV, raising=False)

    # Create a pre-sunset Claude binding and seal a completed CLAUDE_CODE_SESSION turn.
    hist_now = datetime(2026, 11, 5, 10, 0, 0, tzinfo=timezone.utc)
    hist_path, hist_binding = cli.resolve_owner_operation(
        profile,
        operation_id="historical-claude-op",
        request=req,
        now=hist_now,
        wall_now=hist_now,
        editorial_agent="claude",
    )
    store = ContentOpsDurableStore(profile["store_path"])
    work = "cc-opportunity-" + sha256_of("historical-claude-op")
    store.create_work_item(story_id=work, work_item_id=work, title="hist", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    store.register_outbox_message(
        message_id="native-operation-binding-" + sha256_of("historical-claude-op"),
        work_item_id=work,
        destination="internal:native-desktop-editorial",
        payload=canonical_bytes(hist_binding).decode("utf-8"),
        status="EDITORIAL_INTERNAL",
    )
    turn = editorial.NativeDesktopTurn(
        store,
        run_id="historical-claude-op",
        output_dir=hist_binding["output_dir"],
        owner_manual_validation=True,
    )
    call_args = {
        "logical_invocation_id": "historical-claude-op:select",
        "prompt": "historical select prompt",
        "governed_input": {},
        "validator": lambda raw: (True, None, json.loads(raw), None),
    }
    with pytest.raises(editorial.DesktopInputRequired) as raised:
        turn(**call_args)
    turn.submit(
        "select",
        {
            "request_sha256": raised.value.request["request_sha256"],
            "output": {"selected": "historical"},
            "invocation_observation": claude_obs(),
        },
    )

    # Activate CC-855 sunset: historical binding & CLAUDE_CODE_SESSION replay MUST still succeed.
    monkeypatch.setenv(editorial.CLAUDE_SUNSET_ENV, "1")
    resumed_path, resumed_binding = cli.resolve_owner_operation(
        profile,
        operation_id="historical-claude-op",
        now=datetime(2026, 12, 10, 0, 0, 0, tzinfo=timezone.utc),
    )
    assert resumed_path == hist_path
    assert resumed_binding == hist_binding
    assert cli.validate_binding(hist_binding)["editorial_agent"] == "claude"

    replayed_turn = editorial.NativeDesktopTurn(
        store,
        run_id="historical-claude-op",
        output_dir=hist_binding["output_dir"],
        owner_manual_validation=True,
    )
    out, receipt = replayed_turn(**call_args)
    assert out == {"selected": "historical"}
    assert receipt["provider"] == "NATIVE_CLAUDE_CODE"
    assert receipt["selected_model"] == editorial.CLAUDE_MODEL

    # By contrast, a forged post-sunset Claude binding in SQLite fails closed in NativeDesktopTurn.
    post_run = "forged-post-sunset-claude"
    post_work = "cc-opportunity-" + sha256_of(post_run)
    store.create_work_item(story_id=post_work, work_item_id=post_work, title="forged", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    forged_binding = {**hist_binding, "run_id": post_run, "cutoff_utc": "2026-12-03T17:00:00Z"}
    store.register_outbox_message(
        message_id="native-operation-binding-" + sha256_of(post_run),
        work_item_id=post_work,
        destination="internal:native-desktop-editorial",
        payload=canonical_bytes(forged_binding).decode("utf-8"),
        status="EDITORIAL_INTERNAL",
    )
    with pytest.raises(ValueError, match=editorial.CLAUDE_EDITORIAL_AGENT_RETIRED):
        editorial.NativeDesktopTurn(
            store,
            run_id=post_run,
            output_dir=tmp_path / post_run,
            owner_manual_validation=True,
        )


# ---------------------------------------------------------------------------
# C3: agy_neo_answerer_v1 pre-claim AGY_TERMS_BLOCK guard
# ---------------------------------------------------------------------------


def test_c3_agy_runner_available_false_when_terms_blocked_even_if_exe_exists(tmp_path, monkeypatch):
    fake_exe = tmp_path / "agy.exe"
    fake_exe.write_bytes(b"stub")
    runner = agy_neo.AgyRunner(fake_exe)

    assert assist.agy_blocked(fake_exe) is True
    assert runner.blocked_cause() == assist.AGY_TERMS_BLOCK
    assert runner.available() is False
    assert runner("PROMPT") == {"runner_status": "NOT_STARTED", "cause": assist.AGY_TERMS_BLOCK}

    # Lifting the terms block in-test restores file-existence semantics cleanly.
    monkeypatch.setattr(assist, "AGY_TERMS_BLOCK", "")
    assert runner.blocked_cause() is None
    assert runner.available() is True


def test_c3_answer_request_and_dry_run_short_circuit_before_begin_when_blocked(tmp_path, monkeypatch):
    store, executor, coordinator, ids, value = composed_setup(tmp_path, monkeypatch)
    packet = pending_publish(coordinator, store, ids, value, executor)

    fake_exe = tmp_path / "agy.exe"
    fake_exe.write_bytes(b"stub")
    runner = agy_neo.AgyRunner(fake_exe)
    begin_calls: list[str] = []

    def tracking_begin(req_hash: str):
        begin_calls.append(req_hash)
        return executor.begin(req_hash)

    # Even with an accidental routes map pointing X -> AGY, answer_request leaves the row unclaimed for Codex.
    outcome = agy_neo.answer_request(
        packet,
        begin=tracking_begin,
        submit=executor.submit,
        native_invocation_id=executor.native_invocation_id,
        runner=runner,
        routes={"x": agy_neo.ROUTE_AGY},
        report_dir=tmp_path / "reports",
        clock=executor.clock,
    )
    assert outcome["outcome"] == "LEFT_FOR_CODEX"
    assert outcome["reason_code"] == assist.AGY_TERMS_BLOCK
    assert begin_calls == []
    req_hash = packet["request"]["request_sha256"]
    assert executor._get(req_hash, "started") is None
    assert executor._get(req_hash, "response") is None

    # answer_pending also leaves the outbox row unclaimed.
    pending_results = agy_neo.answer_pending(
        executor,
        begin=tracking_begin,
        runner=runner,
        routes={"x": agy_neo.ROUTE_AGY},
        report_dir=tmp_path / "reports-pending",
    )
    assert len(pending_results) == 1
    assert pending_results[0]["outcome"] == "LEFT_FOR_CODEX"
    assert pending_results[0]["reason_code"] == assist.AGY_TERMS_BLOCK
    assert begin_calls == []
    assert executor._get(req_hash, "started") is None

    # dry_run fails closed with AGY_TERMS_BLOCK and zero spawn.
    dry = agy_neo.dry_run(packet, runner=runner, report_dir=tmp_path / "reports-dry")
    assert dry["passed"] is False
    assert dry["reason_code"] == assist.AGY_TERMS_BLOCK
    assert dry["claimed"] is False and dry["submitted"] is False


def test_c3_mock_check_script_fails_closed_under_terms_block(tmp_path, capsys):
    mock_mod = _load_script("agy_neo_mock_check_c3", MOCK_CHECK_CLI)
    rc = mock_mod.main(str(tmp_path / "mock-scratch"))
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert rc == 2
    assert out == {"ok": False, "skipped": assist.AGY_TERMS_BLOCK}


# ---------------------------------------------------------------------------
# C4: Dormant V6 ANTHROPIC_API_KEY auto-selection removal + fail-closed guard
# ---------------------------------------------------------------------------


def test_c4_v6_auto_selection_skips_anthropic_and_explicit_anthropic_fails_closed(monkeypatch):
    from live_contentops import ai_provider_gate_v6

    # Only ANTHROPIC_API_KEY present -> auto-selection MUST NOT pick anthropic.
    only_anthropic = {"NINE_ROUTER_API_KEY": False, "ANTHROPIC_API_KEY": True, "OPENAI_API_KEY": False}
    monkeypatch.setattr(ai_provider_gate_v6, "inspect_provider_credentials", lambda: dict(only_anthropic))

    with pytest.raises(RuntimeError, match="no_live_llm_provider_credentials_present"):
        substack_loop._choose_live_llm_provider("auto")
    with pytest.raises(RuntimeError, match="no_live_llm_editorial_reviewer_credentials_present"):
        tier1_quality._choose_llm_provider("auto")

    # Both ANTHROPIC_API_KEY and OPENAI_API_KEY present -> picks openai, never anthropic.
    with_openai = {"NINE_ROUTER_API_KEY": False, "ANTHROPIC_API_KEY": True, "OPENAI_API_KEY": True}
    monkeypatch.setattr(ai_provider_gate_v6, "inspect_provider_credentials", lambda: dict(with_openai))

    assert substack_loop._choose_live_llm_provider("auto") == "openai"
    assert tier1_quality._choose_llm_provider("auto") == "openai"

    # Explicit anthropic fails closed everywhere with zero network call.
    with pytest.raises(ValueError, match=v6_engine.ANTHROPIC_PROVIDER_RETIRED):
        substack_loop._choose_live_llm_provider("anthropic")
    with pytest.raises(ValueError, match=v6_engine.ANTHROPIC_PROVIDER_RETIRED):
        tier1_quality._choose_llm_provider("ANTHROPIC")
    with pytest.raises(ValueError, match=v6_engine.ANTHROPIC_PROVIDER_RETIRED):
        v6_engine.call_live_provider("test prompt", provider="anthropic")

    # Engine live_provider_call with anthropic records blocker before any search or HTTP call.
    packet = v6_engine.run_article_engine(
        v6_engine.sample_inputs(),
        provider_mode="live_provider_call",
        provider_request_budget=1,
        live_provider="anthropic",
    )
    assert v6_engine.ANTHROPIC_PROVIDER_RETIRED in packet["blockers"]
    assert packet["provider_call_made"] is False


# ---------------------------------------------------------------------------
# C5: Supersession docs updated & leak/profile defenses preserved
# ---------------------------------------------------------------------------


def test_c5_docs_record_decision_168_184_and_preserve_defenses():
    agents_md = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    readme_md = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    skill_md = (REPO_ROOT / ".agents" / "skills" / "contentops-newsroom" / "SKILL.md").read_text(encoding="utf-8")
    runbook_md = (REPO_ROOT / "docs" / "publisher" / "CONTENTOPS_V1_RUNBOOK.md").read_text(encoding="utf-8")

    for text in (agents_md, readme_md, skill_md, runbook_md):
        assert "2026-12-03T17:00:00Z" in text
        assert "AGY_TERMS_BLOCK" in text

    assert "CLAUDE_EDITORIAL_AGENT_RETIRED_CC855" in agents_md
    assert "ANTHROPIC_PROVIDER_RETIRED_CC855" in agents_md
    assert "Antigravity is the default implementation and Browser QA agent." not in readme_md
    assert "Claude remains Jim-triggered." not in skill_md

    # Preserve leak scrubbers and Antigravity Chrome profile guard intact.
    from live_contentops import publishing_profile_registry_v1 as profile_guard
    from live_contentops import reader_article_contract_v1 as article_contract

    for forbidden_name in ("Claude", "Antigravity", "Anthropic"):
        assert forbidden_name in article_contract.INTERNAL_MODEL_AND_CLOCK_PHRASES
    assert any("antigravity" in p.lower() for p in profile_guard._ANTIGRAVITY_MARKERS)
    assert profile_guard._profile_class(r"C:\Users\bullw\.gemini\antigravity-browser-profile") == "antigravity_profile_blocked"
