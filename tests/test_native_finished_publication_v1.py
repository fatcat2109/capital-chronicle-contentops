"""Finished-piece release in disposable stores; no public or model calls."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore, LeaseConflictError
from live_contentops.event_article_guard_v1 import public_execution_copy_forbidden
from live_contentops.native_finished_publication_v1 import (
    check_finished_piece, confirmed_canonicals, newsroom_lease,
    publication_due, release_finished_piece, standing_binding,
)
from live_contentops.native_publication_promotion_v1 import ReadOnlyStore
from live_contentops.native_desktop_workspace_v1 import workspace_snapshot
from test_native_desktop_publication_v1 import composed, finish
from test_native_text_first_v1 import brief_packet
from scripts.run_native_desktop_editorial import resolve_owner_operation


@pytest.fixture
def ready(tmp_path, monkeypatch):
    source, binding, _, _, _, _ = brief_packet(tmp_path / "source", monkeypatch)
    binding = {k: v for k, v in binding.items() if k not in {"automation_id", "window_id", "slot_ordinal"}}
    binding["owner_manual_validation"] = True
    binding["feed_pointer_path"] = str(tmp_path / "feed.json")
    with source.get_connection() as conn:
        conn.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?",
            (canonical_bytes(binding).decode(), "native-operation-binding-" + sha256_of(binding["run_id"])))
    path = Path(binding["output_dir"]) / "binding.json"
    path.write_bytes(canonical_bytes(binding))
    target = ContentOpsDurableStore(tmp_path / "target.sqlite3")
    control = target.get_operating_control()
    target.update_operating_control(operating_mode="AUTONOMOUS_DEFAULT",
        expected_state_version=control["state_version"], control_source="CONTROLLED_TEST")
    rollout = {"schema_version": "contentops.native_desktop_rollout.v1", "public_write_authority": True,
        "store_path": str(target.db_path), "editorial_output_root": str(tmp_path / "live"),
        "published_output_root": str(tmp_path / "published"), "feed_pointer_path": binding["feed_pointer_path"],
        "live_authority": {"scope": "V1_NATIVE_PUBLICATION", "thread_id": "CONTROLLED",
            "turn_id": "CONTROLLED", "message_id": "CONTROLLED", "not_before_utc": "2026-11-01T00:00:00Z"}}
    return source, target, binding, path, rollout


def test_any_finished_store_releases_without_manifest_and_preserves_source(ready, monkeypatch):
    source, target, original, path, rollout = ready
    before = workspace_snapshot(source.db_path)
    value = release_finished_piece(path, rollout)
    assert value["classification"] == "FINISHED_PIECE_READY_FOR_COORDINATOR"
    binding = value["binding"]
    assert binding["owner_manual_live"] and binding["cutoff_utc"] == original["cutoff_utc"]
    assert binding["publication_eligibility_utc"] != binding["cutoff_utc"]
    assert before == workspace_snapshot(source.db_path)
    assert target.list_platform_dispatches() == []
    assert release_finished_piece(path, rollout)["binding"] == binding
    operation, executor, transports = composed(target, binding, rollout, monkeypatch)
    final, browser_writes = finish(operation, executor)
    assert operation.coordinator.allow_prior_confirmed_distribution is True
    assert final["publication"]["canonical_article_real_published"] is True
    assert final["publication"]["state"] == "RECONCILED"
    assert set(browser_writes + transports.calls) == {"substack", "telegram", "discord", "x", "linkedin", "threads"}
    assert len(list(confirmed_canonicals(target))) == 1
    assert before == workspace_snapshot(source.db_path)


def test_live_piece_reuses_binding_and_never_imports_or_rewrites_attempts(ready, monkeypatch):
    _, target, _, path, rollout = ready
    released = release_finished_piece(path, rollout)
    operation, executor, _ = composed(target, released["binding"], rollout, monkeypatch)
    finish(operation, executor)
    dispatches = target.list_platform_dispatches()
    again = release_finished_piece(released["binding_path"], rollout)
    assert again["prepared"] is None
    assert again["publication"]["canonical_article_real_published"]
    assert target.list_platform_dispatches() == dispatches


@pytest.mark.parametrize("failure", ["model", "clock", "private", "changed_request"])
def test_finished_source_faults_fail_without_import(ready, monkeypatch, failure):
    source, target, binding, path, rollout = ready
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn
    original = NativeDesktopTurn.frozen_request
    def request(turn, stage):
        value = deepcopy(original(turn, stage))
        if stage == "write":
            if failure == "clock":
                value["governed_input"]["source_pack"][0]["known_at_utc"] = "2030-01-01T00:00:00Z"
            elif failure == "private":
                value["governed_input"]["source_pack"][0]["public_claim_allowed"] = False
            elif failure == "changed_request":
                value["governed_input"]["cutoff_utc"] = "2030-01-01T00:00:00Z"
            if failure != "changed_request":
                value["request_sha256"] = sha256_of({k: v for k, v in value.items() if k != "request_sha256"})
        return value
    if failure == "model":
        get = NativeDesktopTurn._get
        def wrong_model(turn, stage, kind):
            value = deepcopy(get(turn, stage, kind))
            if stage == "write" and kind == "response":
                value["invocation_observation"]["model"] = "WRONG_MODEL"
            return value
        monkeypatch.setattr(NativeDesktopTurn, "_get", wrong_model)
    else:
        monkeypatch.setattr(NativeDesktopTurn, "frozen_request", request)
    before = workspace_snapshot(source.db_path)
    with pytest.raises(ValueError):
        release_finished_piece(path, rollout)
    assert before == workspace_snapshot(source.db_path)
    assert target.list_platform_dispatches() == []
    assert not Path(rollout["editorial_output_root"]).exists()


def test_newsroom_lease_is_shared_and_never_steals_a_window(ready):
    _, target, _, path, rollout = ready
    lease = target.acquire_lease("internal:native-editorial:window", "CONTROLLED_WINDOW", ttl_seconds=900)
    with pytest.raises(ValueError, match="NEWSROOM_LEASE_ACTIVE"):
        release_finished_piece(path, rollout)
    target.release_lease(lease["lease_id"], "CONTROLLED_WINDOW", lease["fencing_token"])
    with newsroom_lease(target):
        with pytest.raises(LeaseConflictError):
            with newsroom_lease(target):
                pytest.fail("second operation entered")


def test_drip_uses_first_confirmed_canonical_readback_and_does_not_delay_derivatives(ready, monkeypatch):
    _, target, _, path, rollout = ready
    released = release_finished_piece(path, rollout)
    operation, executor, _ = composed(target, released["binding"], rollout, monkeypatch)
    finish(operation, executor)
    first = list(confirmed_canonicals(target))[0]["first_readback_utc"]
    assert not publication_due(target, now=first + timedelta(hours=3))["due"]
    assert publication_due(target, now=first + timedelta(hours=3, minutes=30))["due"]
    assert publication_due(target, run_id=released["binding"]["run_id"], now=first)["due"]
    assert operation.resume()["publication"]["state"] == "RECONCILED"


def test_standing_binding_is_live_resumable_and_refuses_a_second_pending_operation(ready):
    _, target, private, _, rollout = ready
    profile = {"schema_version": "contentops.native_desktop_operator_profile.v1"}
    request = "Select one useful admitted article, then use the existing publisher and readback."
    path, binding = standing_binding(profile, rollout, operation_id="controlled-standing",
        resolver=resolve_owner_operation, request=request, report_only=True)
    assert binding["standing_operation"] and binding["owner_manual_live"]
    assert binding["owner_manual_validation"] is False
    assert Path(binding["rolling_input_path"]).name == "native_desktop_report_only_input_v1.json"
    assert binding["store_path"] == str(target.db_path)
    assert standing_binding(profile, rollout, operation_id=binding["run_id"], resolver=resolve_owner_operation)[0] == path
    target.create_work_item(story_id="controlled", work_item_id="controlled", title="controlled", target_surface="TEST")
    target.register_outbox_message(message_id="native-operation-binding-" + sha256_of(binding["run_id"]),
        work_item_id="controlled", destination="internal:native-desktop-editorial",
        payload=canonical_bytes(binding).decode(), status="EDITORIAL_INTERNAL")
    with pytest.raises(ValueError, match="STANDING_OPERATION_ALREADY_PENDING"):
        standing_binding(profile, rollout, operation_id="second", resolver=resolve_owner_operation, request=request)
    assert private["owner_manual_validation"]


@pytest.mark.parametrize("text,forbidden", [
    ("The federal funds target at 3.75 to 4 percent.", False),
    ("The Fed held its target at 3.75 to 4 percent.", False),
    ("The inflation target at 2 percent remains.", False),
    ("Target at 3.75; stop at 2.75.", True),
    ("Our position size is 2 lots.", True),
    ("Buy at 3.75.", True),
])
def test_policy_target_is_distinct_from_position_instruction(text, forbidden):
    assert public_execution_copy_forbidden(text) is forbidden


def test_missing_exact_writer_cannot_be_promoted(ready, monkeypatch):
    source, _, binding, _, _ = ready
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn
    monkeypatch.setattr(NativeDesktopTurn, "frozen_request", lambda *a: None)
    with pytest.raises(ValueError):
        check_finished_piece(ReadOnlyStore(source.db_path), binding)


def test_standing_daily_cap_counts_distinct_read_back_articles(ready, monkeypatch):
    _, _, _, _, rollout = ready
    now = datetime.now(timezone.utc)
    monkeypatch.setattr("live_contentops.native_finished_publication_v1.confirmed_canonicals",
        lambda _: iter([{"run_id": str(i), "article_identity": str(i), "first_readback_utc": now} for i in range(8)]))
    with pytest.raises(ValueError, match="STANDING_DAILY_TARGET_REACHED"):
        standing_binding({"schema_version": "contentops.native_desktop_operator_profile.v1"}, rollout,
            operation_id="ninth", resolver=resolve_owner_operation, request="Prepare the next useful admitted article.")
    assert not Path(rollout["editorial_output_root"]).exists()


def test_legacy_drip_prevents_a_new_canonical_attempt_without_a_text_clock(ready, monkeypatch):
    _, target, _, path, rollout = ready
    released = release_finished_piece(path, rollout)
    operation, _, transport = composed(target, released["binding"], rollout, monkeypatch)
    monkeypatch.setattr("live_contentops.native_finished_publication_v1.publication_due",
        lambda *a, **k: {"due": False, "next_publication_utc": "CONTROLLED_FUTURE"})
    original_projection = operation.projection
    def legacy_projection():
        value = original_projection()
        return {**value, "timing": {**value["timing"], "text_approved_at_utc": None}}
    monkeypatch.setattr(operation, "projection", legacy_projection)
    assert operation.resume()["classification"] == "NATIVE_PUBLICATION_NOT_YET_DUE"
    assert not target.list_platform_dispatches() and not transport.calls


def test_approved_text_dispatches_without_waiting_for_old_spacing(ready, monkeypatch):
    _, target, _, path, rollout = ready
    released = release_finished_piece(path, rollout)
    operation, _, _ = composed(target, released["binding"], rollout, monkeypatch)
    monkeypatch.setattr("live_contentops.native_finished_publication_v1.publication_due",
        lambda *a, **k: {"due": False, "next_publication_utc": "CONTROLLED_FUTURE"})
    value = operation.resume()
    assert value["classification"] != "NATIVE_PUBLICATION_NOT_YET_DUE"
    assert value["publication"]["timing"]["text_approved_at_utc"]
    assert any(d["platform"] == "substack" for d in target.list_platform_dispatches())


def test_old_source_cutoff_counts_on_actual_publication_day_in_existing_record(ready, monkeypatch):
    _, target, original, path, rollout = ready
    released = release_finished_piece(path, rollout)
    operation, executor, _ = composed(target, released["binding"], rollout, monkeypatch)
    finish(operation, executor)
    from live_contentops.native_newsroom_volume_v1 import persist_native_day_measurement
    from live_contentops.newsroom_production_day_v1 import newsroom_production_day_id
    record = Path(persist_native_day_measurement(target, released["binding"]))
    value = json.loads(record.read_bytes())
    assert value["newsroom_production_day_id"] == newsroom_production_day_id(datetime.now(timezone.utc))
    assert value["native_volume_measurement"]["distinct_canonical_items_published"] == 1
    assert value["native_volume_measurement"]["confirmed_copies_by_channel"]["substack"] == 1
    assert original["cutoff_utc"] == released["binding"]["cutoff_utc"]
    assert value["native_volume_measurement"]["reader_counts_availability"] == "UNAVAILABLE"


def test_zero_chart_analysis_is_refused_but_brief_keeps_exact_instagram_skip(tmp_path, monkeypatch):
    from test_reader_first_data_journalism_v1 import decision
    from live_contentops.native_desktop_editorial_v1 import validate_release_media
    from live_contentops.native_newsroom_volume_v1 import permitted_derivative_skips
    from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import build_native_derivative_payloads
    visual = decision(count=0)
    article = {"reader_first_version": "DATA_JOURNALISM_V1", "visual_editorial_decision": visual,
        "resolved_article_mode": "DATA_OR_DOCUMENT_LENS", "native_destination_media": visual["channel_media"],
        "title": "Controlled source-qualified analysis", "substack_body_markdown": "Controlled text argument.",
        "social_hook": "Controlled source-qualified analysis", "story_identity": "controlled-analysis"}
    with pytest.raises(ValueError, match="ANALYSIS_OFFICIAL_HISTORY_CHARTS_REQUIRED"):
        validate_release_media({"article": article, "media_assets": []})
    visual["story_kind"] = "NEWS"
    article.update(resolved_article_mode="BREAKING_BRIEF", news_item_kind="NEWS")
    assert validate_release_media({"article": article, "media_assets": []})["chart_count"] == 0
    payloads = build_native_derivative_payloads(article=article, selection={},
        canonical_url="https://example.org/actual", media_asset_ids=[])
    assert payloads["instagram_business"]["delivery_state"] == "SKIPPED_IMAGE_REQUIRED"
    # The compiler's exact named skip remains the coordinator's sole permitted omission.
    plan = {"image_optional_policy": "JIM_DECISION_39", "skipped_derivative_destinations": [
        {"destination": "instagram_business", "status": "SKIPPED_IMAGE_REQUIRED"}]}
    assert permitted_derivative_skips(plan) == {"instagram_business"}
    plan["skipped_derivative_destinations"][0]["destination"] = "telegram"
    assert permitted_derivative_skips(plan) == set()


def test_finished_release_can_consult_live_history_from_a_distinct_private_store(ready):
    source, target, binding, path, rollout = ready
    binding["published_memory_store"] = str(target.db_path)
    with source.get_connection() as conn:
        conn.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?",
            (canonical_bytes(binding).decode(), "native-operation-binding-" + sha256_of(binding["run_id"])))
    path.write_bytes(canonical_bytes(binding))
    before = workspace_snapshot(source.db_path)
    released = release_finished_piece(path, rollout)
    assert released["classification"] == "FINISHED_PIECE_READY_FOR_COORDINATOR"
    assert released["binding"]["store_path"] == str(target.db_path)
    assert released["binding"]["published_memory_store"] == str(target.db_path)
    assert released["binding"]["cutoff_utc"] == binding["cutoff_utc"]
    assert workspace_snapshot(source.db_path) == before
    assert target.list_platform_dispatches() == []
    assert release_finished_piece(path, rollout)["binding"] == released["binding"]


@pytest.mark.parametrize("fault", [None, "same_article", "canonical", "unbound", "legacy"])
def test_finished_import_reuses_coordinator_policy_for_prior_derivative_gap(ready, monkeypatch, fault):
    from live_contentops.native_publication_promotion_v1 import _target_guards
    source, target, _, path, rollout = ready
    released = release_finished_piece(path, rollout)
    operation, executor, _ = composed(target, released["binding"], rollout, monkeypatch)
    finish(operation, executor)
    platform = "substack" if fault == "canonical" else "linkedin"
    with target.get_connection() as conn:
        conn.execute("UPDATE platform_dispatches SET status='UNKNOWN_WRITE' WHERE platform=?", (platform,))
        if fault == "unbound":
            row = conn.execute("SELECT message_id FROM platform_dispatches WHERE platform=?", (platform,)).fetchone()
            intent = json.loads(conn.execute("SELECT payload FROM outbox_messages WHERE message_id=?", (row[0],)).fetchone()[0])
            intent["plan_hash"] = "CONTROLLED-unbound"
            conn.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?", (canonical_bytes(intent).decode(), row[0]))
    original = workspace_snapshot(target.db_path)
    article = released["check"]["article_identity"] if fault == "same_article" else "CONTROLLED-distinct-article"
    candidate = {"release_authority": "LEGACY" if fault == "legacy" else "JIM_DECISIONS_20261030_DECISION_39",
        "pin": {"article_identity": article}, "item": {"work_item_id": "CONTROLLED-next-item"},
        "rows": [], "reviews": []}
    binding = {"run_id": "CONTROLLED-next-run", "store_path": str(target.db_path)}
    promotion = {"message_id": "CONTROLLED-next-promotion"}
    with target.get_read_only_connection() as conn:
        if fault:
            with pytest.raises(ValueError, match="EXISTING_PUBLICATION_RECOVERY_REQUIRED"):
                _target_guards(conn, candidate, binding, promotion)
        else:
            assert _target_guards(conn, candidate, binding, promotion) is False
    assert workspace_snapshot(target.db_path) == original


@pytest.mark.parametrize("status", ["UNKNOWN_WRITE", "NATIVE_NEO_TOOL_PENDING"])
def test_distinct_finished_run_defers_prior_distribution_before_transport(ready, monkeypatch, status):
    _, target, _, path, rollout = ready
    released = release_finished_piece(path, rollout)
    operation, executor, transports = composed(target, released["binding"], rollout, monkeypatch)
    finish(operation, executor)
    with target.get_connection() as conn:
        conn.execute("UPDATE platform_dispatches SET status=? WHERE platform='linkedin'", (status,))
    coordinator = operation.coordinator
    coordinator.recovery_scope = {"work_item_id": "CONTROLLED-next-run",
        "plan": {"article_identity": "CONTROLLED-distinct-article"}}
    before, calls = workspace_snapshot(target.db_path), list(transports.calls)
    summary = coordinator.recover_pending()
    assert summary["publish_calls"] == 0
    assert transports.calls == calls
    assert workspace_snapshot(target.db_path) == before
    assert {"work_item_id": released["binding"]["run_id"], "destination": "linkedin"} in summary["deferred_prior_distribution"]
    assert not coordinator.recovery_blocks_new_publication(summary, "CONTROLLED-next-run",
        plan={"article_identity": "CONTROLLED-distinct-article"})
    intent = {"work_item_id": released["binding"]["run_id"]}
    assert not coordinator._defer_prior_distribution_recovery(intent, "substack")
    coordinator.recovery_scope["plan"]["article_identity"] = released["check"]["article_identity"]
    assert not coordinator._defer_prior_distribution_recovery(intent, "linkedin")
    coordinator.recovery_scope = None
    assert not coordinator._defer_prior_distribution_recovery(intent, "linkedin")
