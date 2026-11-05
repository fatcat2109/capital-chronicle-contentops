"""Copied source/turn fixtures only; no network, native model or publication proof."""
import json
import shutil
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker, sha256_of
from live_contentops.capital_chronicle_report_editorial_workspace_v1 import run_report_editorial_cycle
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.native_desktop_editorial_v1 import DesktopInputRequired, admit_pre_writer_source_recovery
from tests.test_contentops_source_research_v1 import REPORT_ROOT
from tests.test_native_newsroom_owner_operation_v1 import entry
from tests.test_native_volume_window_v1 import CUTOFF, make_turn
from tests.test_v1_simple_gemini_newsroom_v1 import _headlines, _selection, _evidence_result
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore


def source_fixture(root, *, published="2026-10-30T09:00:00Z", publisher="Reuters"):
    root.mkdir(parents=True)
    def write(name, value):
        p = root / name
        p.write_text(json.dumps(value), encoding="utf-8")
        return sha256(p.read_bytes()).hexdigest()
    policy = json.loads((REPORT_ROOT / "index.json").read_bytes())["records"][0]
    shutil.copyfile(REPORT_ROOT / policy["policy_capture_path"], root / "policy.json")
    title = "Controlled report describes a conditional policy pace"
    text = title + "\nA controlled interview report distinguishes a pace preference from a committee decision."
    url = ("https://www.bloomberg.com/news/articles/2026-10-30/controlled-policy-report"
        if publisher == "Bloomberg" else "https://www.reuters.com/markets/us/controlled-policy-report-2026-10-30/")
    known = "2026-10-31T00:00:00Z"
    raw_hash = write("capture.json", {"status": "PASS", "url": url, "reporting_publisher": publisher,
        "attribution_text": "Controlled fixture, " + publisher, "observed_at_utc": known,
        "retrieval_method": "READ_ONLY_BROWSEROS_NEO_BOUNDED_EXTRACTS", "public_write_performed": False,
        "credential_or_session_material_read": False, "full_text_sha256": sha256(text.encode()).hexdigest(),
        "full_text_characters": len(text), "excerpts": [{"start": 0, "end": len(text), "text": text}]})
    doc = {"document_id": "controlled-original", "title": title, "source_url": url,
        "publisher": publisher, "source_identity": publisher.lower() + ".com", "raw_sha256": raw_hash,
        "canonical_content_text": text, "canonical_content_sha256": sha256(text.encode()).hexdigest(),
        "source_adapter_family": "reputable_secondary_report", "source_authority_class": "reputable_secondary_source",
        "report_truth_only": True, "published_at_utc": published, "published_at_source": published,
        "content_truncated": False}
    write("admission.json", {"status": "PASS", "official_source_documents": [doc],
        "provenance": {"retrieved_at_utc": known}})
    write("index.json", {"schema_version": "contentops.retained_source_research.v1", "records": [{
        "authorship_class": "REPUTABLE_REPORT_FACTS_ONLY", "headline_id": "controlled-original",
        "headline_text": title, "capture_path": "capture.json", "source_capture_sha256": raw_hash,
        "loader_result_path": "admission.json", "policy_url": policy["policy_url"],
        "policy_capture_path": "policy.json", "policy_capture_sha256": policy["policy_capture_sha256"],
        "policy_retrieved_at_utc": policy["policy_retrieved_at_utc"], "revision_at_utc": known,
        "proposition_span": [0, len(title)], "public_expression_reuse_allowed": False}]})
    assert not RetainedSourceResearch(root).gaps
    return url


def seeded(tmp_path, monkeypatch, *, used=2, published="2026-10-30T09:00:00Z", scheduled=False, needs_sources=False,
        source_missing=False):
    monkeypatch.setattr("live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled", lambda: None)
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    root = tmp_path / "output"
    if scheduled:
        from live_contentops.newsroom_production_day_v1 import newsroom_production_day_id
        root = tmp_path / newsroom_production_day_id(CUTOFF) / "controlled-window" / "live-recovery"
        root.parent.mkdir(parents=True)
    turn, binding = make_turn(store, root, "live-recovery", owner_manual_live=True)
    binding.update(schema_version=entry().BINDING_SCHEMA, store_path=str(store.db_path),
        owner_manual_validation=True, feed_pointer_path=str(tmp_path / "feed.json"),
        published_memory_store=str(tmp_path / "memory.sqlite3"), published_memory_output_root=str(tmp_path / "memory"))
    if scheduled:
        from live_contentops.native_newsroom_volume_v1 import configure_volume_turn
        binding.update(owner_manual_validation=False, window_id="controlled-window", automation_id="v1-newsroom-new-york-2100")
        binding.pop("owner_manual_live")
        configure_volume_turn(turn, binding)
        store.register_outbox_message(message_id="native-operation-binding-" + sha256_of(turn.run_id),
            work_item_id=turn.work, destination="internal:native-desktop-editorial", payload=json.dumps(binding))
    tracker = LatestReportDeliveryTracker(store)
    calls = []
    class Resolver:
        def resume_request_count(self, count):
            pass
        def __call__(self, request):
            calls.append(request["cluster_id"])
            return deepcopy(_evidence_result(request_count=used, status="BLOCKED" if source_missing else "PASS"))
    monkeypatch.setattr("live_contentops.v1_simple_gemini_newsroom_v1._default_evidence_loader",
        lambda *a, **k: Resolver())
    rolling = _headlines(1)
    rolling["headlines"][0].update(source_timestamp_utc="2026-10-30T09:00:00Z",
        headline_text="Controlled report describes a conditional policy pace",
        source_url="https://www.reuters.com/markets/us/controlled-policy-report-2026-10-30/")
    def run():
        return run_report_editorial_cycle(tracker, receipt_id="controlled", admission=None,
            output_dir=turn.root, cutoff_utc=CUTOFF, rolling_input=rolling, llm_invoke=turn,
            run_id=turn.run_id, opportunity_id=turn.run_id)
    with pytest.raises(DesktopInputRequired) as pending:
        run()
    request = pending.value.request
    candidate = request["governed_input"]["candidates"][0]["candidate_id"]
    selected = _selection(candidate)
    # Time-sensitive modes now skip the MAX visual edit (decision 53, native_publication_latency_v1.speed_policy);
    # this recovery path is asserted through visual-edit, which long-form modes still take.
    selected["ordered_candidate_plan"][0].update(article_mode="CAPITAL_CHRONICLE_VIEW", angle="Controlled policy question",
        primary_reader_question="What does the report establish?", evidence_plan="Use exact attributed facts.")
    if source_missing:
        selected["ordered_candidate_plan"][0]["source_requests"] = [{"url": rolling["headlines"][0]["source_url"],
            "reason": "Read the full original report before interpreting its policy language."}]
    observation = {"surface": "CODEX_NATIVE_SUBAGENT", "model": "gpt-6.1-sol", "reasoning_effort": "low",
        "invocation_id": "/root/CONTROLLED_TEST", "observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF"}
    turn.submit("select", {"request_sha256": request["request_sha256"], "output": selected,
        "invocation_observation": observation})
    if source_missing:
        from live_contentops.native_desktop_editorial_v1 import request_source_preparation
        blocked = run()
        assert blocked["classification"] == "DRAFT_BLOCKED" and not blocked["writer_invoked"]
        with pytest.raises(DesktopInputRequired) as media:
            request_source_preparation(turn, selected["ordered_candidate_plan"][0]["source_requests"],
                                       candidate_id=candidate)
        assert media.value.request["stage"] == "sources"
    else:
        with pytest.raises(DesktopInputRequired) as media:
            run()
        assert media.value.request["stage"] == "media-plan"
    if not source_missing:
        pending = entry().operation(binding, command="media-plan")
        turn.submit("media-plan", {"request_sha256": pending["request_sha256"],
            "output": {"story_plan": {"thesis": "Conditional plan pending original source context",
                **({"source_requests": [{"url": rolling["headlines"][0]["source_url"],
                    "reason": "Read the full original report before interpreting its policy language."}]} if needs_sources else {})}},
            "invocation_observation": observation})
    source = turn.root / "acquired"
    url = source_fixture(source, published=published)
    capture = source / "capture.json"
    response = {"within_bound_live_budget": True, "expected_selection_request_sha256": request["request_sha256"],
        "candidate_id": candidate, "research_root": str(source), "supporting_headline_ids": ["controlled-original"],
        "expected_evidence_sha256": sha256((turn.root / "simple_gemini_evidence_v1.json").read_bytes()).hexdigest(),
        "additional_source_requests": [{"url": url, "non_chargeable": True, "observed_at_utc": "2026-10-31T00:00:00Z",
            "capture_path": str(capture), "capture_sha256": sha256(capture.read_bytes()).hexdigest()}]}
    return turn, binding, response, run, calls


def test_live_recovery_preserves_roles_and_clocks_and_reaches_max_without_gets(tmp_path, monkeypatch):
    turn, binding, response, run, calls = seeded(tmp_path, monkeypatch)
    preserved = {p: p.read_bytes() for p in turn.root.glob("desktop_*select.json")}
    preserved.update({p: p.read_bytes() for p in turn.root.glob("desktop_*media-plan.json")})
    prior_walk = (turn.root / "simple_gemini_evidence_v1.json").read_bytes()
    result = entry().operation(binding, command="recover-sources", response=response)
    before = len(turn.store.list_outbox_messages())
    assert entry().operation(binding, command="recover-sources", response=response) == result
    assert len(turn.store.list_outbox_messages()) == before
    assert result["source_request_count"] == 3 and result["source_request_limit"] == 10
    with pytest.raises(DesktopInputRequired) as pending:
        run()
    assert pending.value.request["stage"] == "media-plan" and len(calls) == 1
    walk = json.loads((turn.root / "simple_gemini_evidence_v1.json").read_bytes())
    assert walk["request_count"] == 3 and walk["selected_source_pack"][0]["report_truth_only"]
    assert walk["selected_source_pack"][0]["source_reuse_constraints"]["public_expression_reuse_allowed"] is False
    pending = entry().operation(binding, command="media-plan")
    assert pending["stage"] == "visual-edit"
    request = turn.frozen_request("visual-edit")
    assert request["governed_input"]["source_packet"]["source_pack"] == walk["selected_source_pack"]
    assert request["governed_input"]["actual_light_preparation"]["story_plan"]["thesis"].startswith("Conditional plan")
    snapshot = turn.source_recovery()["research_snapshot"]["records"]["controlled-original"]
    assert snapshot["known_at_utc"] == "2026-10-31T00:00:00Z" > binding["cutoff_utc"]
    assert snapshot["document"]["published_at_utc"] == "2026-10-30T09:00:00Z"
    history = turn.root / "source-recovery-history" / result["request_sha256"]
    assert (history / "simple_gemini_evidence_v1.json").read_bytes() == prior_walk
    assert all(p.read_bytes() == raw for p, raw in preserved.items())
    assert turn.store.list_platform_dispatches() == []


def test_held_source_span_repair_feeds_consumer_without_reacquisition(tmp_path, monkeypatch):
    turn, binding, response, run, calls = seeded(tmp_path, monkeypatch)
    original = admit_pre_writer_source_recovery(turn, binding, response)
    prior = turn.source_recovery()
    with pytest.raises(DesktopInputRequired):
        run()
    source = turn.root / "reprojected"
    shutil.copytree(response["research_root"], source)
    index_path = source / "index.json"
    index = json.loads(index_path.read_bytes())
    text = prior["research_snapshot"]["records"]["controlled-original"]["document"]["canonical_content_text"]
    begin = text.index("A controlled interview")
    index["records"][0]["context_spans"] = [[begin, len(text)]]
    index_path.write_text(json.dumps(index), encoding="utf-8")
    repair = {**response, "research_root": str(source), "source_projection_repair_of": prior["request_sha256"],
        "expected_evidence_sha256": sha256((turn.root / "simple_gemini_evidence_v1.json").read_bytes()).hexdigest()}
    admitted = admit_pre_writer_source_recovery(turn, binding, repair)
    assert admitted["source_request_count"] == original["source_request_count"]
    with pytest.raises(DesktopInputRequired):
        run()
    current = json.loads((turn.root / "simple_gemini_evidence_v1.json").read_bytes())
    assert "pace preference from a committee decision" in current["selected_source_pack"][0]["canonical_content_text"]
    assert current["request_count"] == original["source_request_count"] and len(calls) == 1
    assert turn.source_recovery()["source_projection_repair_of"] == prior["request_sha256"]
    assert turn.source_recovery()["research_snapshot"]["records"]["controlled-original"]["document"] == prior["research_snapshot"]["records"]["controlled-original"]["document"]


@pytest.mark.parametrize("fault", ["acquisition", "source_bytes"])
def test_held_source_span_repair_retains_acquisition_and_source_identity(tmp_path, monkeypatch, fault):
    turn, binding, response, _, _ = seeded(tmp_path, monkeypatch)
    admit_pre_writer_source_recovery(turn, binding, response)
    repair = deepcopy(response)
    repair["source_projection_repair_of"] = turn.source_recovery()["request_sha256"]
    if fault == "acquisition":
        repair["additional_source_requests"][0]["observed_at_utc"] = "2026-10-31T00:00:01Z"
    else:
        path = Path(response["research_root"]) / "admission.json"
        value = json.loads(path.read_bytes())
        value["official_source_documents"][0]["published_at_source"] = "changed"
        path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="SOURCE_PROJECTION_REPAIR_"):
        admit_pre_writer_source_recovery(turn, binding, repair)


def test_pending_recovery_charges_appended_context_and_feeds_writer(tmp_path, monkeypatch):
    from live_contentops.native_desktop_editorial_v1 import request_source_preparation
    turn, binding, response, run, calls = seeded(tmp_path, monkeypatch)
    with pytest.raises(DesktopInputRequired):
        request_source_preparation(turn, [{"url": response["additional_source_requests"][0]["url"],
            "reason": "Acquire the original report before writer freeze."}], candidate_id=response["candidate_id"])
    pending_path = turn.root / "source_preparation_required.json"
    original = pending_path.read_bytes()
    pending = json.loads(original)
    response["expected_source_request_sha256"] = pending["request_sha256"]
    capture = turn.root / "release-context.txt"
    capture.write_text("Controlled original publication-date context.", encoding="utf-8")
    response["additional_source_requests"].append({
        "url": "https://www.reuters.com/markets/us/controlled-date-context-2026-10-30/",
        "non_chargeable": True, "observed_at_utc": "2026-10-31T00:00:00Z",
        "capture_path": str(capture), "capture_sha256": sha256(capture.read_bytes()).hexdigest(),
    })
    admitted = admit_pre_writer_source_recovery(turn, binding, response)
    assert admitted["source_request_count"] == 4  # Two earlier and two captured reads.
    assert pending_path.read_bytes() == original
    with pytest.raises(DesktopInputRequired) as ready:
        run()
    assert ready.value.request["stage"] == "media-plan" and len(calls) == 1
    walk = json.loads((turn.root / "simple_gemini_evidence_v1.json").read_bytes())
    assert walk["request_count"] == 4
    assert walk["selected_source_pack"][0]["document_id"] == "controlled-original"
    assert len(turn.source_recovery()["additional_source_requests"]) == 2


def test_pending_recovery_cannot_replace_issued_source_with_context(tmp_path, monkeypatch):
    from live_contentops.native_desktop_editorial_v1 import request_source_preparation
    turn, binding, response, _, _ = seeded(tmp_path, monkeypatch)
    with pytest.raises(DesktopInputRequired):
        request_source_preparation(turn, [{"url": response["additional_source_requests"][0]["url"],
            "reason": "Acquire the original report before writer freeze."}], candidate_id=response["candidate_id"])
    pending = json.loads((turn.root / "source_preparation_required.json").read_bytes())
    response["expected_source_request_sha256"] = pending["request_sha256"]
    response["additional_source_requests"][0]["url"] = "https://www.reuters.com/another-source/"
    with pytest.raises(ValueError, match="EXACT_PENDING_SOURCE_PREPARATION_REQUIRED"):
        admit_pre_writer_source_recovery(turn, binding, response)


def test_standing_light_sources_reach_acquisition_before_max(tmp_path, monkeypatch):
    turn, binding, response, _, _ = seeded(tmp_path, monkeypatch, needs_sources=True)
    pending = entry().operation(binding, command="media-plan")
    assert pending["stage"] == "sources"
    assert turn.frozen_request("visual-edit") is None
    request = json.loads((turn.root / "source_preparation_required.json").read_bytes())
    assert request["source_requests"][0]["url"] == response["additional_source_requests"][0]["url"]


def test_verified_new_context_supplements_qualified_policy_without_reproving_it(tmp_path):
    from live_contentops.v1_simple_epistemic_state_v1 import candidate_report_provenance
    source_fixture(tmp_path / "new-context")
    research = RetainedSourceResearch(tmp_path / "new-context")
    statement = "The Federal Reserve maintains the target range for the federal funds rate at 3.75 to 4 percent."
    url = "https://www.federalreserve.gov/newsevents/pressreleases/monetary20261028a.htm"
    profile = candidate_report_provenance({"headline_text": statement, "source_url": url})
    request = {"headline_ids": ["controlled-original"], "story_context": {
        "leaf_summaries": [statement], "report_provenance": profile}}
    assert research.evidence(request, cutoff_utc="2026-10-31T01:00:00Z")["status"] == "BLOCKED"
    primary = {"document_id": "retained-fed", "url": url, "publisher": "Federal Reserve",
        "source_identity": "federalreserve.gov", "source_adapter_family": "official_policy",
        "source_authority_class": "official_public_primary_source", "canonical_content_text": statement,
        "canonical_content_sha256": sha256(statement.encode()).hexdigest(), "published_at_utc": "2026-10-28T18:00:00Z"}
    result = research.evidence(request, cutoff_utc="2026-10-31T01:00:00Z", qualified_source_pack=[primary])
    assert result["status"] == "PASS"
    documents = {d["document_id"]: d for d in result["evidence_documents"]}
    assert documents["retained-fed"]["canonical_content_sha256"] == primary["canonical_content_sha256"]
    assert documents["controlled-original"]["context_only"] is True


def test_unanswered_old_visual_is_preserved_and_replaced_with_acquired_sources(tmp_path, monkeypatch):
    from live_contentops.native_desktop_editorial_v1 import request_source_preparation
    turn, binding, response, run, calls = seeded(tmp_path, monkeypatch)
    pending = entry().operation(binding, command="media-plan")
    assert pending["stage"] == "visual-edit"
    original = turn.frozen_request("visual-edit")
    original_key = turn._key("visual-edit", "request")
    original_bytes = (turn.root / "desktop_request_visual-edit.json").read_bytes()
    with pytest.raises(DesktopInputRequired):
        request_source_preparation(turn, [{"url": response["additional_source_requests"][0]["url"],
            "reason": "Acquire the missing original before the unanswered visual brief is used."}])
    issued = json.loads((turn.root / "source_preparation_required.json").read_bytes())
    response["expected_source_request_sha256"] = issued["request_sha256"]
    admitted = admit_pre_writer_source_recovery(turn, binding, response)
    history = turn.root / "source-recovery-history" / admitted["request_sha256"]
    assert (history / "desktop_request_visual-edit.json").read_bytes() == original_bytes
    assert json.loads(turn.store.get_outbox_message(original_key)["payload"]) == original
    assert turn.frozen_request("visual-edit") is None
    with pytest.raises(DesktopInputRequired) as ready:
        run()
    assert ready.value.request["stage"] == "media-plan" and len(calls) == 1
    pending = entry().operation(binding, command="media-plan")
    assert pending["stage"] == "visual-edit"
    revised = turn.frozen_request("visual-edit")
    assert revised["request_sha256"] != original["request_sha256"]
    assert revised["governed_input"]["source_packet"]["source_pack"][0]["document_id"] == "controlled-original"
    assert turn.frozen_request("write") is None


def test_cached_zero_writer_source_failure_recovers_without_replacing_its_result(tmp_path, monkeypatch):
    from live_contentops.native_manual_candidate_v1 import native_artifact_key
    turn, binding, response, run, calls = seeded(tmp_path, monkeypatch, source_missing=True)
    original_key = native_artifact_key(turn.store, turn.run_id, "cc-editorial-final-")
    original = turn.store.get_outbox_message(original_key)
    pending = json.loads((turn.root / "source_preparation_required.json").read_bytes())
    response["expected_source_request_sha256"] = pending["request_sha256"]
    admitted = admit_pre_writer_source_recovery(turn, binding, response)
    assert admitted["source_request_count"] == 3
    assert native_artifact_key(turn.store, turn.run_id, "cc-editorial-final-") != original_key
    assert turn.store.get_outbox_message(original_key) == original
    with pytest.raises(DesktopInputRequired) as ready:
        run()
    assert ready.value.request["stage"] == "media-plan" and len(calls) == 1
    walk = json.loads((turn.root / "simple_gemini_evidence_v1.json").read_bytes())
    assert walk["selected_source_pack"][0]["document_id"] == "controlled-original"
    assert turn.store.get_outbox_message(original_key) == original


def test_four_verified_documents_feed_the_same_writer_with_one_shared_budget(tmp_path, monkeypatch):
    turn, binding, response, run, _ = seeded(tmp_path, monkeypatch)
    root = turn.root / "acquired"
    index = json.loads((root / "index.json").read_bytes())
    for n in range(1, 4):
        relative = "context-" + str(n)
        extra = root / relative
        source_fixture(extra)
        suffix = "controlled-original-" + str(n)
        url = "https://www.reuters.com/markets/us/controlled-policy-context-" + str(n) + "-2026-10-30/"
        capture = json.loads((extra / "capture.json").read_bytes())
        capture["url"] = url
        (extra / "capture.json").write_text(json.dumps(capture), encoding="utf-8")
        digest = sha256((extra / "capture.json").read_bytes()).hexdigest()
        admission = json.loads((extra / "admission.json").read_bytes())
        admission["official_source_documents"][0].update(document_id=suffix, source_url=url, raw_sha256=digest)
        (extra / "admission.json").write_text(json.dumps(admission), encoding="utf-8")
        spec = json.loads((extra / "index.json").read_bytes())["records"][0]
        spec.update(headline_id=suffix, source_capture_sha256=digest)
        for key in ("capture_path", "policy_capture_path", "loader_result_path"):
            spec[key] = relative + "/" + spec[key]
        index["records"].append(spec)
        response["supporting_headline_ids"].append(suffix)
        response["additional_source_requests"].append({"url": url, "non_chargeable": True,
            "observed_at_utc": "2026-10-31T00:00:00Z", "capture_path": str(extra / "capture.json"),
            "capture_sha256": digest})
    (root / "index.json").write_text(json.dumps(index), encoding="utf-8")
    result = admit_pre_writer_source_recovery(turn, binding, response)
    assert result["source_request_count"] == 6  # Two earlier and four acquired documents.
    with pytest.raises(DesktopInputRequired) as ready:
        run()
    assert ready.value.request["stage"] == "media-plan"
    walk = json.loads((turn.root / "simple_gemini_evidence_v1.json").read_bytes())
    assert len(walk["selected_source_pack"]) == 4 and walk["request_count"] == 6


@pytest.mark.parametrize("failure", ["budget", "changed_walk", "changed_selection", "different_candidate",
    "capture_hash", "unrelated_capture", "paid", "future_capture", "outside_root", "source_rights",
    "uncertain_source", "max_frozen", "terminal", "not_live"])
def test_invalid_live_recovery_changes_no_outbox_rows(tmp_path, monkeypatch, failure):
    turn, binding, response, _, _ = seeded(tmp_path, monkeypatch, used=10 if failure == "budget" else 2)
    if failure == "changed_walk": response["expected_evidence_sha256"] = "0" * 64
    elif failure == "changed_selection": response["expected_selection_request_sha256"] = "0" * 64
    elif failure == "different_candidate": response["candidate_id"] = "another"
    elif failure == "capture_hash": response["additional_source_requests"][0]["capture_sha256"] = "0" * 64
    elif failure == "unrelated_capture":
        p = turn.root / "unrelated.txt"; p.write_text("Unrelated locator-only bytes")
        response["additional_source_requests"][0].update(capture_path=str(p), capture_sha256=sha256(p.read_bytes()).hexdigest())
    elif failure == "paid": response["additional_source_requests"][0]["non_chargeable"] = False
    elif failure == "future_capture": response["additional_source_requests"][0]["observed_at_utc"] = "2099-01-01T00:00:00Z"
    elif failure == "outside_root": response["research_root"] = str(tmp_path)
    elif failure == "source_rights":
        p = turn.root / "acquired/index.json"; v = json.loads(p.read_bytes())
        v["records"][0]["public_expression_reuse_allowed"] = True; p.write_text(json.dumps(v))
    elif failure == "max_frozen":
        turn._put("visual-edit", "request", {"request_sha256": "existing"})
        turn._put("visual-edit", "response", {"request_sha256": "existing", "output": {}})
    elif failure == "uncertain_source":
        turn.store.register_outbox_message(message_id="cc-controlled-source-started", work_item_id=turn.work,
            destination="internal:cc-report-editorial-stage", payload=json.dumps({
                "stage": "source:controlled-unfinished", "request_sha256": "unfinished"}))
    elif failure == "terminal":
        turn.store.register_outbox_message(message_id="cc-editorial-final-" + sha256_of(turn.run_id),
            work_item_id=turn.work, destination="internal:controlled", payload="{}")
    elif failure == "not_live": binding["owner_manual_live"] = False
    before = turn.store.list_outbox_messages()
    with pytest.raises(ValueError):
        admit_pre_writer_source_recovery(turn, binding, response)
    assert turn.store.list_outbox_messages() == before and turn.source_recovery() is None


def test_later_publication_cannot_enter_earlier_cutoff(tmp_path, monkeypatch):
    turn, binding, response, _, _ = seeded(tmp_path, monkeypatch, published="2026-10-30T11:00:00Z")
    with pytest.raises(ValueError, match="PUBLICATION_OR_ADMISSION_CLOCK"):
        admit_pre_writer_source_recovery(turn, binding, response)
    assert turn.source_recovery() is None


def test_early_input_cutoff_and_durable_spending_remain_binding(tmp_path, monkeypatch):
    turn, binding, response, _, _ = seeded(tmp_path, monkeypatch, published="2026-10-30T09:59:30Z")
    binding["input_known_at_cutoff_utc"] = "2026-10-30T09:59:00Z"
    with pytest.raises(ValueError, match="PUBLICATION_OR_ADMISSION_CLOCK"):
        admit_pre_writer_source_recovery(turn, binding, response)
    binding.pop("input_known_at_cutoff_utc")
    p = turn.root / "simple_gemini_evidence_v1.json"
    walk = json.loads(p.read_bytes()); walk["request_count"] = 0
    p.write_text(json.dumps(walk))
    response["expected_evidence_sha256"] = sha256(p.read_bytes()).hexdigest()
    result = admit_pre_writer_source_recovery(turn, binding, response)
    assert result["source_request_count"] == 3  # Two durable source requests plus the acquired original.


def test_manual_volume_hold_does_not_claim_whole_edition_or_scheduled_continuation(tmp_path):
    from tests.test_native_pre_writer_outcomes_v1 import fixture_turn, refusal
    from live_contentops.native_newsroom_volume_v1 import configure_volume_turn, volume_policy
    turn, request, observation, _ = fixture_turn(tmp_path, candidates=("a", "b"))
    configure_volume_turn(turn, {"cutoff_utc": CUTOFF, "volume_policy": volume_policy(CUTOFF), "owner_manual_live": True})
    turn.submit("visual-edit", {"request_sha256": request["request_sha256"],
        "output": {**refusal(used=5), "source_request_limit": 10}, "invocation_observation": observation})
    result = turn.advance_story_outcomes()
    assert result["classification"] == "NATIVE_NEXT_CANDIDATE_REQUIRED" and result["candidate_id"] == "b"
    assert result["source_request_count"] == 5 and "next_operation" in result
    assert not (tmp_path / "native_desktop_result.json").exists()


def test_bloomberg_facts_keep_exact_publisher_attribution_and_no_expression_rights(tmp_path):
    from live_contentops.v1_simple_epistemic_state_v1 import candidate_report_provenance
    source_fixture(tmp_path / "source", publisher="Bloomberg")
    research = RetainedSourceResearch(tmp_path / "source")
    record = research.records["controlled-original"]
    request = {"headline_ids": ["controlled-original"], "story_context": {
        "leaf_summaries": [record["headline_text"]], "report_provenance": candidate_report_provenance({
            "headline_text": record["headline_text"] + " - Bloomberg"})}}
    accepted = research.evidence(request, cutoff_utc="2026-10-31T01:00:00Z")
    assert accepted["status"] == "PASS" and accepted["epistemic_state"]["event_truth_supported"] is False
    assert accepted["epistemic_state"]["primary_reporting_publisher"] == "Bloomberg"
    permission = record["source_permissions"]
    assert permission["public_expression_reuse_allowed"] is False
    assert permission["images_logos_exhibits_reuse_allowed"] is False
    request["story_context"]["report_provenance"]["primary_reporting_source_identity"] = "reuters.com"
    refused = research.evidence(request, cutoff_utc="2026-10-31T01:00:00Z")
    assert refused["status"] == "BLOCKED" and "epistemic_report_provenance_not_governed" in refused["blockers"]
