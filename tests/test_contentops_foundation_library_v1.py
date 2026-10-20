"""Real retained wave, rights/clock boundaries, and the existing durable workspace projection."""
import json
from copy import deepcopy
from pathlib import Path
import pytest

from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.contentops_foundation_library_v1 import persist_library, research_library
from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection
from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

ROOT = Path(__file__).parents[1] / "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal21"
CUTOFF = "2026-10-19T12:00:00Z"


def test_real_six_family_wave_is_research_ready_with_explicit_missing_market_inputs():
    research = RetainedSourceResearch(ROOT / "retained_research")
    briefs = json.loads((ROOT / "editorial_briefs.json").read_bytes())["briefs"]
    library = research_library(research, cutoff_utc=CUTOFF, briefs=briefs)
    assert not library["gaps"]
    assert library["counts"] == {"independent_items": 14, "useful_families": 6, "briefs": 7,
                                  "independent_documents": 8, "fresh_provider_drafts": 0, "qualified": 0, "published": 0}
    assert all(f["missing_inputs"] for f in library["families"])
    assert all(not item["current_market_state_verified"] for item in library["items"])
    assert any(i["published_at_utc"] is None for i in library["items"])
    assert next(i for i in library["items"] if i["item_id"] == "goal21-gas-storage")["context_kind"].startswith("HISTORICAL")
    assert all(not b["fresh_provider_draft"] and not b["qualified"] for b in library["briefs"])


def test_source_missing_and_future_research_do_not_create_supported_briefs():
    research = RetainedSourceResearch(ROOT / "retained_research")
    briefs = json.loads((ROOT / "editorial_briefs.json").read_bytes())["briefs"]
    library = research_library(research, cutoff_utc="2026-10-18T00:00:00Z", briefs=briefs)
    assert not library["items"] and not library["briefs"]
    assert len(library["gaps"]) == 7


def test_same_revision_persists_once_in_existing_store_and_reaches_daily_workspace(tmp_path):
    tracker = LatestReportDeliveryTracker(ContentOpsDurableStore(tmp_path / "isolated.sqlite"))
    research = RetainedSourceResearch(ROOT / "retained_research")
    briefs = json.loads((ROOT / "editorial_briefs.json").read_bytes())["briefs"]
    persist_library(tracker, research, cutoff_utc=CUTOFF, briefs=briefs)
    before = len(tracker.store.list_outbox_messages())
    persist_library(tracker, research, cutoff_utc=CUTOFF, briefs=briefs)
    assert len(tracker.store.list_outbox_messages()) == before == 1
    view = report_workspace_projection(tracker.store.list_outbox_messages())
    assert view["foundation_library"]["counts"]["briefs"] == 7
    assert view["foundation_library"]["main_reports"] == []


def test_later_cutoff_and_correction_revise_library_without_reusing_a_stale_brief(tmp_path):
    tracker = LatestReportDeliveryTracker(ContentOpsDurableStore(tmp_path / "isolated.sqlite"))
    research = RetainedSourceResearch(ROOT / "retained_research")
    persist_library(tracker, research, cutoff_utc="2026-10-18T00:00:00Z")
    persist_library(tracker, research, cutoff_utc=CUTOFF)
    view = report_workspace_projection(tracker.store.list_outbox_messages())["foundation_library"]
    assert view["counts"]["independent_items"] == 14
    # Correction lifecycle control only; does not create a real new research capture.
    corrected = deepcopy(research.records["goal21-fed-policy"])
    corrected.update(headline_id="correction-control", correction_of="goal21-fed-policy")
    research.records["correction-control"] = corrected
    briefs = json.loads((ROOT / "editorial_briefs.json").read_bytes())["briefs"]
    updated = research_library(research, cutoff_utc=CUTOFF, briefs=briefs)
    assert next(i for i in updated["items"] if i["item_id"] == "goal21-fed-policy")["stage"] == "RESEARCH_SUPERSEDED"
    assert updated["counts"]["independent_items"] == 14
    assert {b["brief_id"] for b in updated["briefs"]}.isdisjoint({"rates-fx-transmission", "cross-asset-price-versus-custody"})


def test_new_media_comparison_requires_both_exact_permitted_excerpts(tmp_path):
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_source_comparison_card, GroundedArticleBuilderError
    research = RetainedSourceResearch(ROOT / "retained_research")
    docs = []
    for key in ("goal21-fed-policy", "goal21-crypto-custody-proposal"):
        row = research.records[key]
        docs.append({**row["document"], "canonical_content_text": row["permitted_source_text"],
                     "render_excerpt_text": row["headline_text"], "rights_evidence_sha256": row["rights_evidence_sha256"],
                     "underlying_reuse_classification": "governed_government_public_domain"})
    media = build_source_comparison_card(docs, output_dir=tmp_path, title="Dated official source comparison")
    assert len(media["source_lineage"]) == 2 and Path(media["path"]).is_file()
    docs[1]["render_excerpt_text"] = "An unbound assertion that is absent from the captured document."
    with pytest.raises(GroundedArticleBuilderError, match="source_or_rights_unbound"):
        build_source_comparison_card(docs, output_dir=tmp_path, title="Not permitted")


def test_existing_feed_exposes_independent_library_even_when_Main_root_is_unavailable(tmp_path):
    from live_contentops.capital_chronicle_report_feed_v1 import MainReportFeed
    from live_contentops.capital_chronicle_public_manifest_v1 import CONFIG_SCHEMA, REPOSITORY
    research = RetainedSourceResearch(ROOT / "retained_research")
    tracker = LatestReportDeliveryTracker(ContentOpsDurableStore(tmp_path / "isolated.sqlite"))
    pointer = {"schema_version": CONFIG_SCHEMA, "producer_repository": REPOSITORY,
               "export_root_id": "missing-public-root-control", "public_export_root": str(tmp_path / "missing")}
    scan = MainReportFeed(tracker, pointer, headline_paths=[], retained_research=research).poll(cutoff_utc=CUTOFF)
    assert scan["gaps"]
    view = report_workspace_projection(tracker.store.list_outbox_messages())["foundation_library"]
    assert view["counts"]["independent_items"] == 14 and view["counts"]["briefs"] == 7
    assert view["input_composition"]["routine_window_count"] == 4
    assert view["input_composition"]["owner"] == "NATIVE_CODEX_DESKTOP"


def test_source_policy_tampering_does_not_inherit_rights_from_an_official_hostname(tmp_path):
    import shutil
    copied = tmp_path / "research"
    shutil.copytree(ROOT / "retained_research", copied)
    policy = copied / "neo-page-65-rendered.json"
    policy.write_bytes(policy.read_bytes() + b" ")
    research = RetainedSourceResearch(copied)
    assert len(research.records) < 14
    assert any(g["state"] == "SOURCE_PERMISSION_CAPTURE_MISMATCH" for g in research.gaps)


def test_existing_paused_opportunity_freezes_library_questions_with_its_single_input_pool(tmp_path, monkeypatch):
    from tests.test_capital_chronicle_report_feed_v1 import feed
    monkeypatch.setattr("live_contentops.capital_chronicle_report_editorial_workspace_v1.llm_operator_pause_active", lambda: True)
    runtime = feed(tmp_path)
    runtime.retained_research = RetainedSourceResearch(ROOT / "retained_research")
    result = runtime.opportunity(output_dir=tmp_path / "paused", cutoff_utc=CUTOFF,
                                 run_id="library-composition-control", rolling_input={"headlines": [], "cutoff_utc": CUTOFF})
    stages = [json.loads(r["payload"]) for r in runtime.tracker.store.list_outbox_messages()
              if r["destination"] == "internal:cc-report-editorial-stage"]
    pool = next(s for s in stages if "args" in s)
    library = pool["args"]["capital_chronicle_context"]["foundation_library"]
    assert len(library["briefs"]) == 7 and library["research_revision"] == runtime.retained_research.revision
    assert len(pool["args"]["rolling_input"]["headlines"]) >= 14
    assert result["report_workspace_result"]["exact_next_blocker"] == "LLM_OPERATOR_PAUSED"


def test_retained_real_Main_multiasset_batch_and_independent_library_share_existing_read_model(tmp_path):
    import hashlib
    from live_contentops.capital_chronicle_report_feed_v1 import MainReportFeed
    from live_contentops.capital_chronicle_public_manifest_v1 import CONFIG_SCHEMA, REPOSITORY
    batch = ROOT / "main_batch"
    handoff = json.loads((batch / "producer-handoff.json").read_bytes())
    receipt = json.loads((batch / "receipt.json").read_bytes())
    for f in handoff["files"]:
        assert hashlib.sha256((batch / "public-export" / f["path"]).read_bytes()).hexdigest() == f["bytes_sha256"]
    pointer = {"schema_version": CONFIG_SCHEMA, "producer_repository": REPOSITORY,
               "export_root_id": "capital-chronicle-public-analysis-reports-v1",
               "producer_commit": receipt["producer_commit"], "public_export_root": str((batch / "public-export").resolve())}
    runtime = MainReportFeed(LatestReportDeliveryTracker(ContentOpsDurableStore(tmp_path / "isolated.sqlite")),
                             pointer, headline_paths=[], retained_research=RetainedSourceResearch(ROOT / "retained_research"))
    first = runtime.poll(cutoff_utc=receipt["observed_at_utc"])
    assert not first["gaps"] and len(runtime.tracker.receipts()) == 8
    assert sum(e["state"] == "LINEAGE_ONLY_NOOP" for e in first["events"]) == 4
    assert {a for r in runtime.pending() for a in r["asset_ids"]} == {"UKOIL", "USOIL", "XNGUSD"}
    replay = runtime.poll(cutoff_utc=receipt["observed_at_utc"])
    assert replay["new_events"] == 0 and replay["unchanged_artifact_bundles_reused"] == 8
    view = report_workspace_projection(runtime.tracker.store.list_outbox_messages())["foundation_library"]
    assert view["counts"]["independent_items"] == 14 and len(view["main_reports"]) == 3
    assert view["input_composition"]["main_editorial_reports"] == 3
    assert all(r["originality"] == "MAIN_ORIGIN_RECIRCULATION" and not r["current_market_state_verified"] for r in view["main_reports"])
    assert all(c["freshness_state"] and c["evidence"] and c["basis_risk"]
               for r in view["main_reports"] for c in r["public_claims"])
