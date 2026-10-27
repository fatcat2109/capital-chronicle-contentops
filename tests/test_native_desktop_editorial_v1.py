"""Safety and replay contracts of the native seam; controls are not model proof."""
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, DesktopInputRequired
from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff, destination_setup_projection
from live_contentops.destination_transport_registry_v1 import DestinationReadinessManager, registration_for_destination
from live_contentops.daily_app_supervisor_v1 import ContentOpsDailyAppSupervisor


def test_pending_response_restart_and_mismatched_binding(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    work = "cc-opportunity-" + sha256_of("same-turn")
    store.create_work_item(story_id=work, work_item_id=work, title="test", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id="same-turn", output_dir=tmp_path, owner_manual_validation=True)
    args = dict(logical_invocation_id="same-turn:select", prompt="exact", governed_input={"candidates": ["a"]},
                validator=lambda raw: (True, None, json.loads(raw), None))
    with pytest.raises(DesktopInputRequired) as pending:
        turn(**args)
    observation = dict(surface="CODEX_NATIVE_SUBAGENT", invocation_id="controlled-test-only", model="gpt-6.1-sol",
                       reasoning_effort="low", observation_source="CONTROLLED_UNIT_TEST_NOT_MODEL_PROOF")
    response = {"request_sha256": pending.value.request["request_sha256"], "output": {"selected": "a"},
                "invocation_observation": observation}
    with pytest.raises(ValueError, match="BINDING"):
        turn.submit("select", {**response, "request_sha256": "wrong"})
    turn.submit("select", response)
    restarted = NativeDesktopTurn(store, run_id="same-turn", output_dir=tmp_path, owner_manual_validation=True)
    assert restarted(**args)[0] == {"selected": "a"}
    before = len(store.list_outbox_messages())
    assert restarted(**args)[0] == {"selected": "a"}
    assert len(store.list_outbox_messages()) == before
    with pytest.raises(ValueError, match="CONFLICT"):
        restarted(**{**args, "prompt": "changed"})
    assert restarted.telemetry()["usage_tokens"] is None
    assert restarted.telemetry()["external_provider_attempt_count"] == 0


def test_neo_is_coordinator_only_canonical_first_and_ambiguous_return():
    adapter = NeoDestinationHandoff()
    intent = {"work_item_id": "work", "package_identity": "pkg", "destination_plan": {"payload_hash": "hash"}}
    auth = {"schema_version": "contentops.canonical_machine_authorization.v1", "operating_mode": "AUTONOMOUS_DEFAULT",
            "destination": "substack", "dispatch_attempt_identity": "attempt", "work_item_id": "work", "payload_hash": "hash"}
    with pytest.raises(ValueError, match="COORDINATOR"):
        adapter.publish(destination="substack", intent=intent, authorization_context={})
    blocked = adapter.publish(destination="substack", intent=intent, authorization_context=auth)
    assert blocked["definite_no_write"] is True
    with pytest.raises(ValueError, match="RECONCILED"):
        adapter.publish(destination="x", intent=intent, authorization_context={**auth, "destination": "x"})
    ambiguous = NeoDestinationHandoff(native_executor=lambda request: {"status": "SUCCESS", "public_object_id": "id"})
    assert ambiguous.publish(destination="substack", intent=intent, authorization_context=auth)["status"] == "UNKNOWN_WRITE"


def test_presence_is_not_validity_instagram_fallback_and_linkedin_expiry(tmp_path):
    (tmp_path / "auth_metadata_v1.json").write_text(json.dumps({"access_token_expires_at_utc": "2026-10-12T14:54:01Z"}))
    (tmp_path / "linkedin_member_credentials.dpapi").write_bytes(b"not-decrypted")
    result = destination_setup_projection(env={"META_ACCESS_TOKEN": "test-never-return", "INSTAGRAM_BUSINESS_ACCOUNT_ID": "id"},
        now=datetime(2026, 10, 20, tzinfo=timezone.utc), linkedin_root=tmp_path)
    assert result["instagram_business"]["configuration_present"] is True
    assert result["instagram_business"]["validity"] == "NOT_VERIFIED"
    assert result["linkedin"]["validity"] == "EXPIRED"
    assert result["youtube"]["api_oauth_does_not_authorize_community"] is True
    assert "test-never-return" not in json.dumps(result)
    from live_contentops.daily_app_ui_read_model_v1 import _assert_nonsecret
    _assert_nonsecret(result)


def test_neo_account_proof_never_inherits_edge_readiness(tmp_path):
    manager = DestinationReadinessManager(env={})
    assert registration_for_destination("substack").transport_type == "BROWSEROS_NEO_MCP"
    assert manager.passive_surface("SUBSTACK_ARTICLE", persist=False)["write_eligible"] is False
    assert manager.probe_surface("X_THREAD")["write_eligible"] is False
    manager.neo_readiness_provider = lambda surface: {"public_handle": "@wrong", "authenticated": True, "native_executor_bound": True}
    assert manager.probe_surface("X_THREAD")["identity_match"] is False


def test_supervisor_cannot_invoke_gemini_or_sdk_as_native_owner(tmp_path):
    supervisor = ContentOpsDailyAppSupervisor(store_path=tmp_path / "state.sqlite3", output_root=tmp_path / "out",
        newsroom_cycle=lambda **_: pytest.fail("supervisor invoked a model"))
    now = datetime(2026, 10, 20, 14, tzinfo=timezone.utc)
    assert supervisor.routine_editorial_owner == "NATIVE_CODEX_DESKTOP"
    assert supervisor._due_windows(now, None) == []


def test_scheduled_pause_before_store_and_cross_midnight(tmp_path, monkeypatch):
    import live_contentops.native_desktop_schedule_binding_v1 as module
    from live_contentops.daily_app_supervisor_v1 import build_bootstrap_editorial_window_policy, owner_locked_editorial_opportunities
    from live_contentops.newsroom_production_day_v1 import newsroom_production_day_id
    monkeypatch.setattr(module, "llm_operator_pause_active", lambda: True)
    assert module.scheduled_binding({}, "v1-newsroom-new-york-0100")["classification"] == "LLM_OPERATOR_PAUSED"
    assert not list(tmp_path.iterdir())
    now = datetime(2026, 10, 20, 18, tzinfo=timezone.utc)
    rows = owner_locked_editorial_opportunities(build_bootstrap_editorial_window_policy(), reference_utc=now, through_utc=now)
    row = next(r for r in rows if r["session"] == "new_york_0100_bangkok")
    assert newsroom_production_day_id(row["start_utc"]) == newsroom_production_day_id("2026-10-20T10:00:00Z")


def test_native_model_path_requires_native_protocol():
    from live_contentops.native_desktop_editorial_v1 import run_native_desktop_newsroom
    with pytest.raises(ValueError, match="PROTOCOL"):
        run_native_desktop_newsroom(llm_invoke=lambda **_: pytest.fail("fallback"))


def test_paused_rollout_and_active_authority_match_native_target():
    from live_contentops.codex_desktop_newsroom_operator_v1 import four_task_setup_packet
    root = Path(__file__).resolve().parents[1]
    rollout = json.loads((root / "config/native_desktop_rollout_v1.json").read_bytes())
    assert rollout["tasks"] == four_task_setup_packet()["tasks"]
    assert rollout["target_status"] == "AUTHORIZED_LIVE_TRANSITION"
    assert rollout["public_write_authority"] is True
    assert rollout["live_authority"]["scope"] == "V1_NATIVE_PUBLICATION"
    assert len({r["id"] for r in rollout["tasks"]}) == 4
    assert rollout["model"] == "gpt-6.1-sol" and rollout["reasoning_effort"] == "low"
    for name in ("AGENTS.md", "docs/codegraph/V1_CONTEXT.md",
            "docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md",
            "docs/automation/CONTENTOPS_CURRENT_STALE_DOCS_MANIFEST_V1.md",
            "docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md",
            "docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md",
            "docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_CURRENT_EXECUTION_POINTER_V3.md"):
        text = (root / name).read_text(encoding="utf-8")
        assert "NATIVE_CODEX_DESKTOP" in text and "gpt-6.1-sol" in text


def test_native_request_rechecks_pause_before_next_stage(tmp_path, monkeypatch):
    import live_contentops.llm_operator_control_v1 as control
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    turn = NativeDesktopTurn(store, run_id="paused", output_dir=tmp_path)
    monkeypatch.setattr(control, "llm_operator_pause_active", lambda *_: True)
    with pytest.raises(control.LLMOperatorPausedError):
        turn(logical_invocation_id="paused:write")
    assert not list(tmp_path.glob("desktop_request*"))


def test_current_run_now_api_requires_native_conversation_without_queue(tmp_path):
    from live_contentops.daily_app_ui_read_model_v1 import request_operator_cycle
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    control = store.update_operating_control(operating_mode="SHADOW_ONLY", expected_state_version=1,
        control_source="CONTROLLED_NATIVE_TEST")
    result = request_operator_cycle(store.db_path, expected_state_version=control["state_version"])
    assert result["status"] == "NATIVE_DESKTOP_CONVERSATION_REQUIRED"
    assert result["governed_cycle_requested"] is False
    assert store.fetch_pending_operator_trigger() is None


def test_scheduled_resume_keeps_qualified_article_at_review_boundary(tmp_path, monkeypatch):
    import live_contentops.native_desktop_schedule_binding_v1 as module
    monkeypatch.setattr(module, "llm_operator_pause_active", lambda: False)
    monkeypatch.setattr(module, "load_canonical_published_memory_read_only", lambda **_: ([], {}))
    rollout = {"schema_version": module.SCHEMA, "store_path": str(tmp_path / "state.sqlite3"),
        "published_output_root": str(tmp_path / "out"), "editorial_output_root": str(tmp_path / "out"),
        "feed_pointer_path": str(tmp_path / "feed.json")}
    now = datetime(2026, 10, 20, 14, 5, tzinfo=timezone.utc)
    first = module.scheduled_binding(rollout, "v1-newsroom-new-york-2100", now=now)
    binding = json.loads(Path(first["binding_path"]).read_bytes())
    store = ContentOpsDurableStore(Path(rollout["store_path"]))
    work = "cc-opportunity-" + sha256_of(binding["run_id"])
    store.create_work_item(story_id=work, work_item_id=work, title="Qualified result", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    store.register_outbox_message(message_id="cc-editorial-final-" + sha256_of(binding["run_id"]),
        work_item_id=work, destination="internal:native-desktop-editorial",
        payload=json.dumps({"simple_result": {"qualified_article_count": 1}}), status="EDITORIAL_INTERNAL")
    resumed = module.scheduled_binding(rollout, "v1-newsroom-new-york-2100", now=now)
    assert resumed["classification"] == "NATIVE_WINDOW_REVIEW_REQUIRED"
    assert resumed["binding_path"] == first["binding_path"]
    assert resumed["slot_ordinal"] == first["slot_ordinal"]


def test_public_source_date_guidance_preserves_frozen_legacy_requests(tmp_path, monkeypatch):
    """Controlled prompt compatibility; no actual model invocation or article."""
    import live_contentops.native_desktop_editorial_v1 as module
    store = ContentOpsDurableStore(tmp_path / 'state.sqlite3')
    for run in ('new-date-policy', 'legacy-date-policy'):
        work = 'cc-opportunity-' + module.sha256_of(run)
        store.create_work_item(story_id=work, work_item_id=work, title='Controlled prompt', target_surface='CONTENTOPS_EDITORIAL_ONLY')
    new = NativeDesktopTurn(store, run_id='new-date-policy', output_dir=tmp_path/'new', owner_manual_validation=True)
    args = dict(logical_invocation_id='new-date-policy:write', prompt='Exact controlled request',
                governed_input={'CONTROLLED_TEST_ONLY':True}, validator=lambda raw: (True,None,json.loads(raw),None))
    with pytest.raises(DesktopInputRequired) as pending:
        new(**args)
    assert 'chronology in evidence metadata' in pending.value.request['prompt']
    assert 'without microseconds or internal audit vocabulary' in pending.value.request['prompt']
    legacy = NativeDesktopTurn(store, run_id='legacy-date-policy', output_dir=tmp_path/'legacy', owner_manual_validation=True)
    with monkeypatch.context() as patch:
        patch.setattr(module, 'PUBLIC_SOURCE_DATE_GUIDANCE', module.LEGACY_SOURCE_DATE_GUIDANCE)
        with pytest.raises(DesktopInputRequired) as prior:
            legacy(**{**args, 'logical_invocation_id':'legacy-date-policy:write'})
    with pytest.raises(DesktopInputRequired) as resumed:
        legacy(**{**args, 'logical_invocation_id':'legacy-date-policy:write'})
    assert resumed.value.request['request_sha256'] == prior.value.request['request_sha256']
    assert resumed.value.request['prompt'] == prior.value.request['prompt']
    with pytest.raises(ValueError, match='CONFLICT'):
        legacy(**{**args, 'logical_invocation_id':'legacy-date-policy:write', 'prompt':'Changed controlled request'})
