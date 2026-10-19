"""Exact editorial decisions, selective invalidation, API boundary and paused composition."""
from copy import deepcopy
import json
from pathlib import Path
import threading
from http.server import HTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker, sha256_of
from live_contentops.contentops_editorial_desk_v1 import read_reviews, record_review
from live_contentops.contentops_foundation_library_v1 import persist_library, persist_research_package, library_projection, source_binding
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

ROOT = Path(__file__).parents[1] / "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal22"
CUTOFF = "2026-10-19T14:00:00Z"


def seeded(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "desk.sqlite")
    tracker = LatestReportDeliveryTracker(store)
    research = RetainedSourceResearch(ROOT / "retained_research")
    briefs = json.loads((ROOT / "editorial_briefs.json").read_bytes())["briefs"]
    snap = persist_library(tracker, research, cutoff_utc=CUTOFF, briefs=briefs)
    # Only one public Main dependent package is omitted in this source-change control;
    # the integrated proof covers the actual three Main reports and dependent gas package.
    for b in snap["briefs"]:
        if b["brief_id"] == "gas-vintage":
            continue
        article = {"title": b["title"], "substack_body_markdown": "Focused deterministic revision-control specimen"}
        persist_research_package(tracker, {"brief_id": b["brief_id"], "brief_sha256": b["brief_sha256"],
            "article": article, "article_identity": sha256_of(article),
            "source_binding_sha256": source_binding([i for i in snap["items"] if i["item_id"] in b["source_item_ids"]]),
            "stage": "EDITOR_AUTHORED_RESEARCH_PACKAGE", "validation": {"status": "PASS", "blockers": []},
            "previews": {}, "media_assets": [], "qualified": False, "published": False, "fresh_provider_draft": False},
            research_revision=research.revision)
    return store, tracker, research, briefs


def view(store):
    return library_projection(store.list_outbox_messages(), read_reviews(store))


def decide(store, p, decision="KEEP"):
    return record_review(store, brief_id=p["brief_id"], package_revision=p["package_revision"], decision=decision,
                         rationale="Reviewed exact source support and competing explanations for research only.",
                         expected_review_id=p["review"]["latest_review_id"])


def test_source_change_invalidates_only_dependents_and_survives_restart(tmp_path):
    store, tracker, research, briefs = seeded(tmp_path)
    for p in view(store)["packages"]:
        decide(store, p)
    changed = deepcopy(research)
    changed.revision = "different-global-index"
    # An unrelated index revision or scan clock cannot revoke six unchanged decisions.
    persist_library(tracker, changed, cutoff_utc=CUTOFF, briefs=briefs)
    assert view(store)["desk"]["decisions"]["KEEP"] == 6
    changed.records["goal21-fed-policy"]["headline_text"] += " Changed claim control."
    changed.records["goal21-fed-policy"]["text_sha256"] = "f" * 64
    persist_library(tracker, changed, cutoff_utc=CUTOFF, briefs=briefs)
    restarted = ContentOpsDurableStore(store.db_path)
    stale = {p["brief_id"] for p in view(restarted)["packages"] if p["review"]["state"] == "STALE"}
    assert stale == {"rates-fx-transmission", "cross-asset-price-versus-custody"}
    requests = [json.loads(r["payload"]) for r in store.list_outbox_messages() if r["destination"] == "internal:cc-foundation-revision-request"]
    assert {r["brief_id"] for r in requests} == stale
    before = len(requests)
    persist_library(tracker, changed, cutoff_utc=CUTOFF, briefs=briefs)
    assert sum(r["destination"] == "internal:cc-foundation-revision-request" for r in store.list_outbox_messages()) == before
    with pytest.raises(ValueError, match="PACKAGE_REVISION_CONFLICT"):
        decide(store, next(p for p in view(store)["packages"] if p["brief_id"] in stale))
    assert view(restarted)["desk"]["decisions"]["KEEP"] == 4


def test_exact_preview_revision_and_concurrent_review_fail_closed(tmp_path):
    store, tracker, research, _ = seeded(tmp_path)
    p = view(store)["packages"][0]
    first = decide(store, p, "HOLD")
    with pytest.raises(ValueError, match="REVIEW_VERSION_CONFLICT"):
        decide(store, p)
    current = next(v for v in view(store)["packages"] if v["brief_id"] == p["brief_id"])
    assert current["review"]["latest_review_id"] == first["review_id"]
    package = {k: v for k, v in current.items() if k not in {"package_sequence", "review", "package_revision", "source_revision_current"}}
    package["previews"] = {"telegram": {"text": "Meaningfully revised reader-facing preview"}}
    persist_research_package(tracker, package, research_revision=research.revision)
    latest = next(v for v in view(store)["packages"] if v["brief_id"] == p["brief_id"])
    assert latest["review"]["state"] == "STALE" and latest["source_revision_current"]
    assert latest["package_revision"] != p["package_revision"]
    assert len(latest["review"]["history"]) == 1


def test_public_Main_claim_revision_invalidates_only_bound_package(tmp_path):
    from live_contentops.capital_chronicle_report_feed_v1 import _persist
    store, tracker, research, briefs = seeded(tmp_path)
    batch = ROOT.parent / "goal21/main_batch/final_workspace.json"
    source = json.loads(batch.read_bytes())["workspaces"]
    for w in source:
        r = w["latest_report"]
        _persist(store, "controlled-main-" + r["report_id"], r, "internal:cc-report-receipt")
    persist_library(tracker, research, cutoff_utc=CUTOFF, briefs=briefs)
    gas = next(p for p in json.loads((ROOT / "revised/packages.json").read_bytes()) if p["brief_id"] == "gas-vintage")
    persist_research_package(tracker, gas, research_revision=research.revision)
    for p in view(store)["packages"]:
        decide(store, p)
    old = next(w["latest_report"] for w in source if w["latest_report"]["report_id"] == "asset-report:XNGUSD")
    # Controlled changed-public-report projection; does not claim another Main admission.
    new = {**old, "report_version": old["report_version"] + 1, "source_report_sha256": "d" * 64}
    _persist(store, "controlled-new-main", new, "internal:cc-report-receipt")
    persist_library(tracker, research, cutoff_utc=CUTOFF, briefs=briefs)
    assert {p["brief_id"] for p in view(store)["packages"] if p["review"]["state"] == "STALE"} == {"gas-vintage"}
    assert view(store)["desk"]["decisions"]["KEEP"] == 6


def test_review_api_origin_exact_revision_and_daily_app_readback(tmp_path):
    from live_contentops.server import make_handler
    from live_contentops.daily_app_ui_read_model_v1 import build_daily_app_snapshot
    store, _, _, _ = seeded(tmp_path)
    p = view(store)["packages"][0]
    server = HTTPServer(("127.0.0.1", 0), make_handler(store.db_path))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    body = {"brief_id": p["brief_id"], "package_revision": p["package_revision"], "decision": "HOLD",
            "rationale": "Hold exact package until its named current-input gap is closed.", "expected_review_id": None}
    try:
        url = f"http://127.0.0.1:{server.server_port}/api/daily-app/editorial-review"
        with pytest.raises(HTTPError) as e:
            urlopen(Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "Origin": "https://example.org"}))
        assert e.value.code == 403
        request = Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "Origin": "http://127.0.0.1:4174"})
        with urlopen(request) as response:
            assert json.load(response)["decision"] == "HOLD"
        with pytest.raises(HTTPError) as e:
            urlopen(request)
        assert e.value.code == 409
        snapshot = build_daily_app_snapshot(store.db_path)
        assert snapshot["today"]["report_bridge"]["foundation_library"]["desk"]["decisions"]["HOLD"] == 1
        assert len(read_reviews(ContentOpsDurableStore(store.db_path))) == 1
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_configured_feed_adopts_current_packages_and_holds_only_their_exclusive_candidates(tmp_path, monkeypatch):
    from tests.test_capital_chronicle_report_feed_v1 import feed
    monkeypatch.setattr("live_contentops.capital_chronicle_report_editorial_workspace_v1.llm_operator_pause_active", lambda: True)
    runtime = feed(tmp_path)
    runtime.retained_research = RetainedSourceResearch(ROOT / "retained_research")
    runtime.refresh_research_library(cutoff_utc=CUTOFF)
    first = view(runtime.tracker.store)
    assert len(first["packages"]) == 7
    p = next(p for p in first["packages"] if p["brief_id"] == "options-positioning")
    decide(runtime.tracker.store, p, "HOLD")
    old_rows = sum(r["destination"] == "internal:cc-foundation-library-package" for r in runtime.tracker.store.list_outbox_messages())
    runtime.refresh_research_library(cutoff_utc=CUTOFF)
    assert sum(r["destination"] == "internal:cc-foundation-library-package" for r in runtime.tracker.store.list_outbox_messages()) == old_rows
    runtime.opportunity(output_dir=tmp_path / "paused", cutoff_utc=CUTOFF, run_id="held-package-control",
                        rolling_input={"headlines": [], "cutoff_utc": CUTOFF})
    stages = [json.loads(r["payload"]) for r in runtime.tracker.store.list_outbox_messages() if r["destination"] == "internal:cc-report-editorial-stage"]
    args = next(s["args"] for s in stages if "args" in s)
    assert not {"goal21-futures-option", "goal21-futures-hedgers"}.intersection(r["headline_id"] for r in args["rolling_input"]["headlines"])
    assert args["capital_chronicle_context"]["foundation_library"]["editorial_desk"]["decisions"]["HOLD"] == 1


def test_affected_render_applies_one_package_preserving_other_exact_revisions(tmp_path, monkeypatch):
    import shutil
    from scripts.render_contentops_research_library_v1 import render
    root = tmp_path / "research"
    shutil.copytree(ROOT / "retained_research", root / "retained_research")
    shutil.copyfile(ROOT / "editorial_briefs.json", root / "editorial_briefs.json")
    target = root / "retained_research/packages.json"
    before = {p["brief_id"]: p for p in json.loads(target.read_bytes())}
    monkeypatch.setattr("scripts.render_contentops_research_library_v1.llm_operator_pause_active", lambda: True)
    receipt = render(root, tmp_path / "rendered", tmp_path / "render.sqlite", ROOT / "revised/packages.json",
                     ["metals-exposure"], target)
    after = {p["brief_id"]: p for p in json.loads(target.read_bytes())}
    assert receipt["editor_authored_packages"] == 1 and receipt["fresh_provider_calls"] == 0
    assert set(before) == set(after)
    assert all(before[k] == after[k] for k in before if k != "metals-exposure")
    assert list(target.parent.glob("packages.previous-*.json"))
    assert not list((tmp_path / "rendered").rglob("*.png"))  # exact unchanged media reused
    stale = list(before.values())
    next(p for p in stale if p["brief_id"] == "metals-exposure")["source_binding_sha256"] = "f" * 64
    stale_path = tmp_path / "stale-media-binding.json"
    stale_path.write_text(json.dumps(stale), encoding="utf-8")

    def must_rebuild(*_args, **_kwargs):
        raise ValueError("SOURCE_CHANGED_MEDIA_REBUILD_REQUIRED")

    monkeypatch.setattr("scripts.render_contentops_research_library_v1.build_source_backed_media_assets", must_rebuild)
    with pytest.raises(ValueError, match="SOURCE_CHANGED_MEDIA_REBUILD_REQUIRED"):
        render(root, tmp_path / "changed-source", tmp_path / "changed.sqlite", stale_path, ["metals-exposure"])
