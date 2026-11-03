"""CC-172/decision 53 contracts. Synthetic transports are not live timing proof."""
import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from PIL import Image

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.contentops_editorial_desk_v1 import record_native_article_review, read_reviews
from live_contentops.native_desktop_editorial_v1 import bind_editorial_media, native_review_revision, require_current_final_visual_review
from live_contentops.native_publication_latency_v1 import (
    POLICY, SPEED_POLICY, automated_media_check, publication_timing, speed_policy, attach_photo_credits,
    text_approval,
    text_revision,
)
from native_final_visual_fixture_v1 import visual_request_fixture
from test_native_desktop_publication_v1 import seeded, composed, finish, observed
from test_native_text_first_v1 import brief_packet


def current(store, run):
    return json.loads(store.get_outbox_message("cc-editorial-final-" + sha256_of(run))["payload"])


def failed_review(store, binding, result, tag):
    turn, request, response = visual_request_fixture(store, binding, result, revision_tag=tag)
    response["output"]["decision"] = "REPAIR_REQUIRED"
    photo = next(f for f in response["output"]["asset_findings"] if "caption_credit_alt" in f["checks"])
    photo["checks"]["caption_credit_alt"] = "FAIL"
    photo["findings"] = ["Controlled unresolved photo credit defect."]
    turn.submit(request["stage"], response)
    return {"stage": request["stage"], "request_sha256": request["request_sha256"],
        "output_dir": binding["output_dir"], "invocation_id": response["invocation_observation"]["invocation_id"],
        "findings_addressed": ["Controlled photo caption repair"]}


def test_one_visual_repair_then_drop_only_failed_visual_keep_facts_and_passed_chart(tmp_path, monkeypatch):
    store, binding, _, result, _ = seeded(tmp_path, monkeypatch, final_visual=False)
    run = binding["run_id"]
    repair = failed_review(store, binding, result, "initial")
    assets = copy.deepcopy(result["media_assets"])
    photo = next(a for a in assets if a["modality"] == "documentary_photo")
    photo["alt_text"] += " Controlled attempted correction."
    bind_editorial_media(store, run_id=run, article_identity=result["article_identity"], assets=assets,
        expected_package_revision=native_review_revision(result), final_visual_repair=repair)
    repaired = current(store, run)
    assert repaired["visual_repair_disposition"]["repair_rounds"] == 1
    second = failed_review(store, binding, repaired, "after-one-repair")
    with pytest.raises(ValueError, match="VISUAL_REPAIR_CAP_DROP_FAILED_ASSETS_REQUIRED"):
        bind_editorial_media(store, run_id=run, article_identity=repaired["article_identity"], assets=assets,
            expected_package_revision=native_review_revision(repaired), final_visual_repair=second)
    bind_editorial_media(store, run_id=run, article_identity=repaired["article_identity"], assets=[],
        expected_package_revision=native_review_revision(repaired), final_visual_repair=second, drop_failed_visuals=True)
    dropped = current(store, run)
    assert [a["modality"] for a in dropped["media_assets"]] == ["source_backed_chart"]
    assert dropped["evidence"] == result["evidence"] and dropped["article_identity"] == result["article_identity"]
    assert dropped["visual_repair_disposition"]["dropped_assets"][0]["asset_id"] == photo["asset_id"]
    with pytest.raises(ValueError, match="VISUAL_REPAIR_CAP"):
        bind_editorial_media(store, run_id=run, article_identity=dropped["article_identity"], assets=assets,
            expected_package_revision=native_review_revision(dropped))


def test_editor_keep_preserves_original_text_clock_across_media_review(tmp_path, monkeypatch):
    store, binding, _, result, review = seeded(tmp_path, monkeypatch, final_visual=False)
    first = review["text_approved_at_utc"]
    next_review = record_native_article_review(store, run_id=binding["run_id"], article_identity=result["article_identity"],
        decision="KEEP", rationale="Controlled later media check cannot restart the original text approval clock.",
        expected_review_id=review["review_id"])
    assert next_review["text_approved_at_utc"] == first


@pytest.mark.parametrize("short_preview", [False, True, "revised_preview", "analysis", "long"])
def test_current_policy_adopts_unchanged_legacy_text_without_rewriting_native_history(tmp_path, monkeypatch, short_preview):
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn
    from live_contentops.native_publication_latency_v1 import adopt_approved_text_speed_policy, uses_short_path
    store, binding, _, result, review = seeded(tmp_path, monkeypatch, final_visual=False)
    run = binding["run_id"]
    if short_preview:
        result["article"]["news_item_kind"] = "NEWS"
        result["article"]["substack_body_markdown"] = "Controlled short upcoming-event preview."
        if short_preview == "long":
            result["article"]["substack_body_markdown"] = " ".join(["Controlled"] * 501)
        if short_preview == "revised_preview":
            result["simple_result"]["revision_performed"] = True
        with store.get_connection() as conn:
            conn.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?",
                (canonical_bytes(result).decode(), "cc-editorial-final-" + sha256_of(run)))
        review = record_native_article_review(store, run_id=run, article_identity=result["article_identity"],
            decision="KEEP", expected_review_id=review["review_id"], rationale="Controlled short upcoming-event news preview.")
    turn = NativeDesktopTurn(store, run_id=run, output_dir=binding["output_dir"], owner_manual_validation=True)
    request = {"request_sha256": "controlled-legacy-request", "governed_input": {
        "article_mode": "WEEK_AHEAD_OR_WATCH" if short_preview else "STANDARD_NEWS_ANALYSIS",
        "visual_editorial_decision": {"story_kind": "ANALYSIS" if short_preview == "analysis" else "NEWS"} if short_preview else {},
        "source_pack": result["evidence"]}}
    response = {"request_sha256": request["request_sha256"], "output": {"article": result["article"]},
        "invocation_observation": {"surface": "CODEX_NATIVE_SUBAGENT", "model": "gpt-6.1-sol",
            "reasoning_effort": "max", "invocation_id": "controlled-original-writer",
            "observation_source": "CONTROLLED_FIXTURE_NOT_RUNTIME_PROOF"}}
    turn._put("write", "request", request)
    turn._put("write", "response", response)
    if short_preview == "revised_preview":
        revised_request = {**request, "request_sha256": "controlled-revision-request"}
        revised_response = {**response, "request_sha256": revised_request["request_sha256"]}
        turn._put("revise", "request", revised_request)
        turn._put("revise", "response", revised_response)
    if short_preview in {"analysis", "long"}:
        with pytest.raises(ValueError, match="APPROVED_TEXT_SOURCE_OR_COPY_CHANGED"):
            adopt_approved_text_speed_policy(store, run_id=run)
        assert turn._get("write", "request") == request and turn._get("write", "response") == response
        return
    basis = adopt_approved_text_speed_policy(store, run_id=run)
    assert uses_short_path(store, run_id=run, result=result)
    kept = record_native_article_review(store, run_id=run, article_identity=result["article_identity"],
        decision="KEEP", expected_review_id=review["review_id"],
        rationale="Current policy applies to the exact unchanged source-bound native article.")
    assert kept["text_approved_at_utc"] == basis["original_approval_clock_utc"]
    assert require_current_final_visual_review(store, run_id=run)["pixels_inspected"] is False
    assert turn._get("write", "request") == request and turn._get("write", "response") == response
    changed = copy.deepcopy(result)
    changed["article"]["substack_body_markdown"] += " Unreviewed copy."
    with pytest.raises(ValueError, match="APPROVED_TEXT_SOURCE_OR_COPY_CHANGED"):
        uses_short_path(store, run_id=run, result=changed)
    changed = copy.deepcopy(result)
    changed["evidence"].append({"unreviewed": True})
    with pytest.raises(ValueError, match="APPROVED_TEXT_SOURCE_OR_COPY_CHANGED"):
        uses_short_path(store, run_id=run, result=changed)


def test_text_clock_excludes_visual_metadata_but_binds_every_copy_change():
    original = {"article_identity": "article", "article": {"title": "Approved text", "substack_body_markdown": "Body",
        "social_policy_summary": "Bound social passage", "visual_editorial_decision": {"charts": []}}}
    changed = copy.deepcopy(original)
    changed["article"].update(source_date_notice="Media-only regeneration", native_destination_media={"x": ["chart"]},
        visual_repair_disposition={"dropped_asset_ids": ["photo"]})
    assert text_revision(changed) == text_revision(original)
    for field in ("title", "substack_body_markdown", "social_policy_summary"):
        changed = copy.deepcopy(original)
        changed["article"][field] += " changed"
        assert text_revision(changed) != text_revision(original)


def test_time_sensitive_writer_one_editor_publishes_without_screenshot_review(tmp_path, monkeypatch):
    store, binding, rollout, result, _, _ = brief_packet(tmp_path, monkeypatch)
    accepted = require_current_final_visual_review(store, run_id=binding["run_id"])
    assert accepted["policy_id"] == SPEED_POLICY and accepted["pixels_inspected"] is False
    assert accepted["automated_media_check"]["blocks_publication"] is False
    from live_contentops.native_desktop_publication_v1 import prepare_native_publication
    prepare_native_publication(store, binding)
    operation, executor, _ = composed(store, binding, rollout, monkeypatch)
    value, _ = finish(operation, executor)
    timing = value["publication"]["timing"]
    assert timing["state"] == "WITHIN_15_MINUTES"
    assert timing["all_channels_dispatched_within_target"]
    assert all(c["dispatched_at_utc"] for c in timing["channels"] if not c["skipped"])
    assert not any("final-visual" in json.loads(r["payload"]).get("stage", "") for r in store.list_outbox_messages())


def test_load_and_size_failure_is_logged_once_without_claiming_pixel_review(tmp_path):
    path = tmp_path / "image.png"
    Image.new("RGB", (40, 20)).save(path)
    result = {"media_assets": [{"asset_id": "test", "sha256": "metadata", "path": str(path), "width": 80, "height": 20}]}
    value = automated_media_check(result)
    assert value["findings"][0]["status"] == "DIMENSIONS_MISMATCH"
    assert value["failures_logged_no_repair_loop"] == 1 and value["blocks_publication"] is False
    assert value["findings"][0]["pixels_inspected"] is False


def test_missing_dimensions_and_unreadable_images_are_logged_without_a_loop(tmp_path):
    path = tmp_path / "image.png"
    Image.new("RGB", (40, 20)).save(path)
    result = {"media_assets": [{"asset_id": "test", "sha256": "metadata", "path": str(path)}]}
    assert automated_media_check(result)["findings"][0]["status"] == "EXPECTED_DIMENSIONS_NOT_BOUND"
    path.write_bytes(b"invalid image")
    value = automated_media_check(result)
    assert value["findings"][0]["status"] == "IMAGE_LOAD_FAILED"
    assert value["blocks_publication"] is False


def test_legacy_or_different_text_cannot_backdate_approval_and_hold_revokes_timing():
    note = {"run_id": "run", "article_identity": "article"}
    row = {"reviewer_ref": "NATIVE_DESKTOP_ARTICLE_REVIEW", "decision": "KEEP",
        "created_at": "2026-11-03T08:00:00Z", "notes": json.dumps(note)}
    assert text_approval([row], run_id="run", article_identity="article", revision="new-copy") is None
    note.update(text_revision_sha256="old-copy", text_approved_at_utc=row["created_at"])
    row["notes"] = json.dumps(note)
    assert text_approval([row], run_id="run", article_identity="article", revision="new-copy") is None
    assert text_approval([row], run_id="run", article_identity="article", revision="old-copy") == row["created_at"]
    held = {**row, "decision": "HOLD"}
    timing = publication_timing([], [row, held], run_id="run", destinations=[])
    assert timing["text_approved_at_utc"] is None and timing["state"] == "TEXT_APPROVAL_NOT_OBSERVED"


def test_review_clock_fallback_uses_the_existing_stores_reviewed_at_field():
    row = {"reviewer_ref": "NATIVE_DESKTOP_ARTICLE_REVIEW", "decision": "KEEP",
        "reviewed_at": "2026-11-03T08:00:00Z", "notes": json.dumps({"run_id": "run", "article_identity": "article",
            "text_revision_sha256": "copy"})}
    assert text_approval([row], run_id="run", article_identity="article", revision="copy") == row["reviewed_at"]
    row.pop("reviewed_at")
    assert text_approval([row], run_id="run", article_identity="article", revision="copy") is None


def test_photo_credit_attached_at_selection_from_bound_media_record(tmp_path):
    from test_native_editorial_media_standard_v1 import controlled_release_packet
    _, photo, chart = controlled_release_packet(tmp_path)
    selected = attach_photo_credits([photo, chart])
    credit = selected[0]["canonical_photo_credit"]
    assert photo["creator_publisher"] in credit and photo["license_url"] in credit and photo["source_page_url"] in credit
    assert attach_photo_credits(selected) == selected


def test_pending_neo_request_is_not_dispatched_and_overdue_does_not_block(tmp_path, monkeypatch):
    store, binding, rollout, _, _ = seeded(tmp_path, monkeypatch)
    operation, executor, _ = composed(store, binding, rollout, monkeypatch)
    operation.resume()
    projection = operation.projection()
    assert not projection["timing"]["all_channels_dispatched_within_target"]
    assert all(c["dispatched_at_utc"] is None for c in projection["timing"]["channels"])
    later = datetime.now(timezone.utc) + timedelta(hours=1)
    timing = publication_timing(store.list_outbox_messages(), read_reviews(store), run_id=binding["run_id"],
        destinations=projection["destinations"], now=later)
    assert timing["state"] == "OVERDUE_CONTINUE_PUBLICATION"


def test_substack_action_keeps_jims_code_tab_and_upload_rules_and_bounds_dispatch_clock(tmp_path, monkeypatch):
    store, binding, rollout, _, _ = seeded(tmp_path, monkeypatch)
    operation, executor, _ = composed(store, binding, rollout, monkeypatch)
    operation.resume()
    pending = next(p for p in executor.pending() if p["request"]["action"] == "PUBLISH")
    request_hash = pending["request"]["request_sha256"]
    packet = operation.tool("begin", request_hash=request_hash)
    assert packet["upload_policy"]["source_scope"] == "ARTICLE_OWN_MEDIA_FOLDER"
    assert "NATIVE_FILE_DIALOG_OPEN" in packet["upload_policy"]["native_file_dialog"]
    routine = packet["substack_publish_routine"]
    assert routine["policy"] == "JIM_DECISION_54" and routine["pending_is_dispatch"] is False
    assert "Gmail" in routine["before_publish"] and "never read" in routine["before_publish"]
    assert "PENDING_JIM_EMAIL_CODE" in routine["email_code_dialog"]
    assert "share-center" in routine["continue_only_after"]
    response = observed(pending)
    claim = executor._get(request_hash, "started")
    too_early = datetime.fromisoformat(claim["begun_at_utc"]) - timedelta(seconds=1)
    response["tool_observation"]["dispatched_at_utc"] = too_early.isoformat()
    with pytest.raises(ValueError, match="NATIVE_NEO_DISPATCH_TIME_INVALID"):
        operation.tool("submit", request_hash=request_hash, response=response)
    response["tool_observation"]["dispatched_at_utc"] = claim["begun_at_utc"]
    operation.tool("submit", request_hash=request_hash, response=response)
    timing = operation.projection()["timing"]
    canonical = next(c for c in timing["channels"] if c["destination"] == "substack")
    assert canonical["dispatched_at_utc"] == claim["begun_at_utc"]
    assert canonical["timing_basis"] == "NATIVE_ACTION_OBSERVED"


def test_long_explainer_keeps_full_visual_path():
    assert speed_policy({"article_mode": "EVERGREEN_EXPLAINER"}) is None
    assert speed_policy({"article_mode": "EVERGREEN_EXPLAINER", "selected_candidate": {"event_id": "event"}}) is None
    assert speed_policy({"article_mode": "STANDARD_NEWS_ANALYSIS"})["dispatch_target_minutes"] == 15


def test_short_analysis_prepares_source_bound_media_then_replays_exact_writer_without_visual_role(tmp_path):
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, DesktopInputRequired, bind_editorial_media_plan
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.v1_simple_gemini_newsroom_v1 import _worker_prompt
    from test_native_editorial_media_standard_v1 import controlled_release_packet
    doc, photo, chart = controlled_release_packet(tmp_path / "assets")
    for asset in (photo, chart):
        asset.pop("visual_review", None)
    store = ContentOpsDurableStore(tmp_path / "controlled.sqlite3")
    run = "controlled-fast-analysis"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)
    governed = {"source_pack": [doc], "article_mode": "STANDARD_NEWS_ANALYSIS"}
    args = dict(logical_invocation_id=run + ":write", prompt=_worker_prompt(governed),
        governed_input=governed, validator=lambda raw: (True, None, json.loads(raw), None))
    with pytest.raises(DesktopInputRequired) as media:
        turn(**args)
    assert media.value.request["stage"] == "media-plan"
    assert media.value.request["visual_editorial_decision_required"] is False
    plan_args = dict(logical_invocation_id=run + ":media-plan", prompt="Controlled source-bound plan",
        governed_input=governed, validator=args["validator"])
    with pytest.raises(DesktopInputRequired) as planner:
        turn(**plan_args)
    story = {"thesis": "Controlled analysis", "chart_plan": "Exact reported comparison"}
    turn.submit("media-plan", {"request_sha256": planner.value.request["request_sha256"], "output": {"story_plan": story},
        "invocation_observation": {"surface": "CODEX_NATIVE_SUBAGENT", "invocation_id": "CONTROLLED_NOT_MODEL_PROOF",
            "model": "gpt-6.1-sol", "reasoning_effort": "low", "observation_source": "CONTROLLED_UNIT_TEST"}})
    plan = {"native_plan_run_id": run, "native_plan_stage": "media-plan",
        "native_plan_request_sha256": planner.value.request["request_sha256"], "story_plan": story}
    bind_editorial_media_plan(store, run_id=run, output_dir=tmp_path, plan=plan, assets=[photo, chart])
    with pytest.raises(DesktopInputRequired) as writer:
        turn(**args)
    request = writer.value.request
    assert request["stage"] == "write" and "JIM DECISION 53" in request["prompt"]
    assert request["governed_input"]["publication_speed_policy"]["dispatch_target_minutes"] == 15
    assert turn.frozen_request("visual-edit") is None
    with pytest.raises(DesktopInputRequired) as resumed:
        turn(**args)
    assert resumed.value.request["request_sha256"] == request["request_sha256"]
