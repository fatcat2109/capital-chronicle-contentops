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


@pytest.mark.parametrize("mismatch", [None, "return", "source"])
def test_completed_native_revision_reaches_existing_assembly_without_another_writer(tmp_path, monkeypatch, mismatch):
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, resume_completed_native_revision
    store, binding, _, result, _ = seeded(tmp_path, monkeypatch, final_visual=False)
    turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=binding["output_dir"], owner_manual_validation=True)
    original = json.loads((Path(__file__).resolve().parents[1] /
        "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal31/goal31-company-machine-reading-write-output.json").read_bytes())
    turn._put("write", "response", {"output": original,
        "invocation_observation": {"invocation_id": "CONTROLLED_TEST_SAME_WRITER"}})
    worker = copy.deepcopy(original)
    worker["article"]["substack_body_markdown"] = worker["article"]["substack_body_markdown"].replace("\n\n", "\n\n\n", 1)
    request = {"request_sha256": "a" * 64, "governed_input": {"source_pack": result["evidence"]}}
    if mismatch == "source":
        request["governed_input"]["source_pack"] = []
    response = {"request_sha256": ("b" * 64 if mismatch == "return" else request["request_sha256"]),
                "output": worker, "invocation_observation": turn._get("write", "response")["invocation_observation"]}
    turn._put("revise", "request", request)
    turn._put("revise", "response", response)
    before = copy.deepcopy(current(store, binding["run_id"]))
    call = lambda: resume_completed_native_revision(store, turn, result, run_id=binding["run_id"])
    if mismatch:
        with pytest.raises(ValueError, match="EXACT_COMPLETED_NATIVE_REVISION_REQUIRED"):
            call()
        assert current(store, binding["run_id"]) == before
        return
    call()
    actual = current(store, binding["run_id"])
    assert actual["article"]["substack_body_markdown"] == worker["article"]["substack_body_markdown"]
    assert actual["simple_result"]["revision_performed"] is True
    assert len(actual["previews"]) == 8
    assert actual["evidence"] == before["evidence"]
    assert turn._get("write", "response")["output"] != worker
    assert turn._get("revise", "response") == response
    assert not store.list_platform_dispatches()


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


def test_pre_writer_repair_counts_and_failed_asset_drops_with_source_bound_copy_alignment(tmp_path, monkeypatch):
    store, binding, _, result, review = seeded(tmp_path, monkeypatch, final_visual=False)
    for asset in result["media_assets"]:
        asset["visual_review"] = {**asset.get("visual_review", {}), "repair_round": 1,
            "pixels_inspected": True, "asset_sha256": asset["sha256"]}
    store.finalize_outbox_payload_before_dispatch(
        message_id="cc-editorial-final-" + sha256_of(binding["run_id"]),
        payload=canonical_bytes(result).decode(), status="EDITORIAL_INTERNAL")
    repair = failed_review(store, binding, result, "prewriter-one-repair")
    passing_chart = next(a["asset_id"] for a in result["media_assets"] if a["modality"] == "source_backed_chart")
    repair["channel_media_after_drop"] = {p["destination"]: [passing_chart] for p in result["previews"]}
    worker = json.loads((Path(__file__).resolve().parents[1] /
        "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal31/goal31-company-machine-reading-write-output.json").read_bytes())
    original_dek = worker["article"]["dek"]
    worker["article"]["dek"] += " A focused reading."
    for claim in worker["material_claim_bindings"]:
        if claim["claim_text"] == original_dek:
            claim["claim_text"] = worker["article"]["dek"]
    bind_editorial_media(store, run_id=binding["run_id"], article_identity=result["article_identity"], assets=[],
        expected_package_revision=native_review_revision(result), final_visual_repair=repair,
        drop_failed_visuals=True, corrected_worker_output=worker)
    updated = current(store, binding["run_id"])
    assert updated["article"]["dek"].endswith(" A focused reading.")
    assert updated["evidence"] == result["evidence"]
    assert updated["visual_repair_disposition"]["repair_rounds"] == 1
    assert [a["modality"] for a in updated["media_assets"]] == ["source_backed_chart"]
    assert len(updated["previews"]) == 8
    assert updated["article"]["post_visual_destination_media"] == repair["channel_media_after_drop"]
    assert all(not {a["asset_id"] for a in updated["visual_repair_disposition"]["dropped_assets"]}
        & set(p["payload"].get("media_asset_ids", [])) for p in updated["previews"])
    assert Path(updated["visual_repair_revision"]["qualified_record_path"]).is_file()


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
            "reasoning_effort": "high", "invocation_id": "controlled-original-writer",
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
    media_only = copy.deepcopy(result)
    media_only["article"]["native_destination_media"] = {"x": ["replacement-reviewed-card"]}
    assert uses_short_path(store, run_id=run, result=media_only)
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


@pytest.mark.parametrize("saved_configuration", [None,
    {"model": "controlled-observed-model", "reasoning_effort": "high"},
    {"model": None, "reasoning_effort": None, "configuration_status": "CONFIGURED_NOT_OBSERVED"}])
def test_time_sensitive_writer_one_editor_publishes_without_screenshot_review(tmp_path, monkeypatch, saved_configuration):
    store, binding, rollout, result, _, _ = brief_packet(tmp_path, monkeypatch)
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, ROLE_ASSIGNMENTS
    turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=binding["output_dir"], owner_manual_validation=True)
    stage = "revise" if result.get("simple_result", {}).get("revision_performed") else "write"
    response = turn._get(stage, "response")
    if saved_configuration is not None:
        # Simulate actual telemetry on an already saved, approved return. Role
        # dispatch still requests Jim's settings; labels never park publication.
        response["invocation_observation"].update(saved_configuration)
        with store.get_connection() as conn:
            conn.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?",
                (canonical_bytes(response).decode(), turn._key(stage, "response")))
    assert ROLE_ASSIGNMENTS["write"] == {"model": "gpt-6.1-sol", "reasoning_effort": "max"}
    accepted = require_current_final_visual_review(store, run_id=binding["run_id"])
    assert accepted["policy_id"] == SPEED_POLICY and accepted["pixels_inspected"] is False
    assert accepted["automated_media_check"]["blocks_publication"] is False
    from live_contentops.native_desktop_publication_v1 import prepare_native_publication
    prepare_native_publication(store, binding)
    operation, executor, transport = composed(store, binding, rollout, monkeypatch)
    # The legacy general fixture simulates every non-core destination as an
    # API. Exercise the actual company-page Neo route in this timing test.
    from live_contentops.publication_coordinator_v1 import CanonicalDestinationTransportRuntimeV1
    publish, readback = transport.publish, transport.readback
    monkeypatch.setattr(transport, "publish", lambda **kw:
        CanonicalDestinationTransportRuntimeV1.publish(transport, **kw)
        if kw["destination"] == "linkedin_company" else publish(**kw))
    monkeypatch.setattr(transport, "readback", lambda **kw:
        CanonicalDestinationTransportRuntimeV1.readback(transport, **kw)
        if kw["destination"] == "linkedin_company" else readback(**kw))
    value, _ = finish(operation, executor)
    timing = value["publication"]["timing"]
    # Decision 83: no site link, so the plan takes its Substack route: Substack first, then
    # the social copies linking the confirmed Substack post, all inside the target.
    assert timing["state"] == "WITHIN_15_MINUTES"
    assert timing["all_channels_dispatched_within_target"]
    assert next(c for c in timing["channels"] if c["destination"] == "substack")["dispatched_at_utc"]
    assert all(c["within_target"] is True for c in timing["channels"]
               if not c["skipped"] and c["destination"] != "substack"), timing["channels"]
    assert not any("final-visual" in json.loads(r["payload"]).get("stage", "") for r in store.list_outbox_messages())
    assert turn._get(stage, "response") == response


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
    assert routine["policy"] == "JIM_DECISIONS_48_52_63" and routine["pending_is_dispatch"] is False
    assert "task's tab group" in routine["before_publish"]
    assert "Never read a mailbox" in routine["before_publish"]
    assert "PENDING_JIM_EMAIL_CODE" in routine["email_code_dialog"]
    # CC-242 (decision 74): Gmail opens only on the "Check your email" dialog, never read or snapshotted.
    assert "Do not open Gmail unless Substack shows" in routine["before_publish"]
    assert "Only now open Gmail" in routine["email_code_dialog"]
    assert "never tabs action=new" in routine["email_code_dialog"]
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


@pytest.mark.skip(reason="Jim's decision 83 (5 Nov): no social or Substack post links the preview site until Capital Chronicle owns its domain; site-first linking is off (SITE_LINKS_ALLOWED=False). Re-enable against the owned domain.")
@pytest.mark.parametrize("change", [
    {"plan_hash": "another-plan"}, {"article_content_sha256": "0" * 64},
    {"public_object_url": "https://example.com/wrong-article"}])
def test_site_readback_before_first_dispatch_requires_exact_reviewed_plan(tmp_path, monkeypatch, change):
    from live_contentops.native_desktop_publication_v1 import prepare_native_publication
    from live_contentops.site_first_publication_v1 import request_for_site
    from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired
    store, binding, rollout, _, _, _ = brief_packet(tmp_path, monkeypatch)
    prepare_native_publication(store, binding)
    operation, executor, _ = composed(store, binding, rollout, monkeypatch)
    operation.resume()
    plan, _ = operation.validate()
    request = {**request_for_site(binding["run_id"], plan, executor.native_invocation_id), **change}
    request["request_sha256"] = sha256_of({k: v for k, v in request.items() if k != "request_sha256"})
    with pytest.raises(NativeNeoInputRequired):
        executor(request)
    with pytest.raises(ValueError, match="NATIVE_NEO_EXACT_SITE_READBACK_REQUIRED"):
        operation.tool("begin", request_hash=request["request_sha256"])
    assert not store.list_platform_dispatches()


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


def test_agents_md_opens_gmail_only_on_the_check_your_email_dialog():
    import re
    from pathlib import Path
    text = re.sub(r"\s+", " ", (Path(__file__).resolve().parents[1] / "AGENTS.md").read_text(encoding="utf-8"))
    assert "with the draft only" in text
    assert "untouched Gmail inbox" not in text
    assert "Open Gmail only when Substack shows \"Check your email\"" in text
    assert "Agents never read Gmail: no snapshot, read, grep, evaluate or screenshot" in text
