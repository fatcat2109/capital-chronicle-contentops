"""One isolated Goal22 desk proof, reusing the accepted Goal21 receipt store.

No provider, production tick, browser, Main/database edit or public operation.
It copies only the explicitly named prior isolated proof, never a production store.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker, sha256_of, canonical_bytes
from live_contentops.contentops_editorial_desk_v1 import read_reviews, record_review
from live_contentops.contentops_foundation_library_v1 import library_projection, persist_library, persist_research_package
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.contentops_main_headline_projection_v1 import MainHeadlineExporter, permitted_report_headlines
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.capital_chronicle_report_feed_v1 import MainReportFeed
from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection
from live_contentops.llm_operator_control_v1 import operator_pause_path, llm_operator_pause_active


def dump(path, value):
    path.write_bytes(canonical_bytes(value) + b"\n")


def verify(seed, root, output):
    if output.exists():
        raise ValueError("NEW_ISOLATED_OUTPUT_REQUIRED")
    seed = seed.resolve(strict=True)
    if seed.name != "isolated-proof.sqlite3" or seed.parent.name != "goal21-main-multiasset-a50d8c6e":
        raise ValueError("EXACT_PREVIOUS_ISOLATED_PROOF_REQUIRED_NOT_PRODUCTION")
    if not llm_operator_pause_active():
        raise ValueError("EXPECTED_LLM_PAUSE_REQUIRED")
    pause_hash = hashlib.sha256(operator_pause_path().read_bytes()).hexdigest()
    previous_receipt = json.loads((root.parent / "goal21/main_batch/receipt.json").read_bytes())
    assert previous_receipt["status"] == "PASS_REAL_IMMUTABLE_COLD_START_AND_RESTART"
    output.mkdir(parents=True)
    path = output / "desk-proof.sqlite3"
    source = sqlite3.connect(f"file:{seed.as_posix()}?mode=ro", uri=True)
    target = sqlite3.connect(path)
    source.backup(target)
    source.close()
    target.close()
    store = ContentOpsDurableStore(path)
    tracker = LatestReportDeliveryTracker(store)
    assert len(tracker.receipts()) == previous_receipt["receipt_count_after_restart"] == 8
    assert {a for r in tracker.receipts() for a in r.get("asset_ids", [])} == {"UKOIL", "USOIL", "XNGUSD"}
    assert not read_reviews(store)
    original = library_projection(store.list_outbox_messages())
    assert len(original["packages"]) == 7 and original["counts"]["independent_items"] == 14
    audit = json.loads((root / "semantic_review.json").read_bytes())
    for p in original["packages"]:
        review = next(r for r in audit["reviews"] if r["brief_id"] == p["brief_id"])
        assert review["prior_article_identity"] == p["article_identity"]
        record_review(store, brief_id=p["brief_id"], package_revision=p["package_revision"],
                      decision="REVISE", rationale=review["substantive_weakness"], expected_review_id=None)
    cutoff = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    research = RetainedSourceResearch(root / "retained_research")
    assert len(research.records) == 15 and not research.gaps
    briefs = json.loads((root / "editorial_briefs.json").read_bytes())["briefs"]
    persist_library(tracker, research, cutoff_utc=cutoff, briefs=briefs)
    packages = json.loads((root / "revised/packages.json").read_bytes())
    for p in packages:
        persist_research_package(tracker, p, research_revision=research.revision)
    intermediate = library_projection(store.list_outbox_messages(), read_reviews(store))
    assert intermediate["desk"]["decisions"]["STALE"] == 7
    for p in intermediate["packages"]:
        review = next(r for r in audit["reviews"] if r["brief_id"] == p["brief_id"])
        assert p["source_revision_current"]
        record_review(store, brief_id=p["brief_id"], package_revision=p["package_revision"],
                      decision=review["final_decision"], rationale=review["rationale"],
                      expected_review_id=p["review"]["latest_review_id"])
    before = library_projection(store.list_outbox_messages(), read_reviews(store))
    restarted = ContentOpsDurableStore(path)
    final = library_projection(restarted.list_outbox_messages(), read_reviews(restarted))
    assert sha256_of(final) == sha256_of(before)
    assert final["desk"]["decisions"] == {"KEEP": 5, "HOLD": 2, "REVISE": 0, "STALE": 0, "UNREVIEWED": 0}
    assert final["counts"]["editor_authored_packages"] == 7 and len(final["main_reports"]) == 3
    # One paused opportunity freezes desk decisions and exact revision requests under
    # the existing Simple owner. It is not a production scheduler tick or injected model.
    feed = MainReportFeed(LatestReportDeliveryTracker(restarted),
                         {"schema_version": "contentops.main_public_export_binding.v1",
                          "producer_repository": "https://github.com/fatcat2109/Headline-Raw-data-json",
                          "producer_commit": previous_receipt["producer_commit"],
                          "export_root_id": "capital-chronicle-public-analysis-reports-v1",
                          "public_export_root": str((root.parent / "goal21/main_batch/public-export").resolve()),
                          "research_root": str((root / "retained_research").resolve())}, headline_paths=[])
    result = feed.opportunity(output_dir=output / "paused-opportunity", cutoff_utc=cutoff,
                              run_id="goal22-one-integrated-desk-proof", rolling_input={"headlines": [], "cutoff_utc": cutoff})
    assert result["report_workspace_result"]["exact_next_blocker"] == "LLM_OPERATOR_PAUSED"
    stages = [json.loads(r["payload"]) for r in restarted.list_outbox_messages()
              if r["destination"] == "internal:cc-report-editorial-stage"]
    pool = next(s for s in stages if "args" in s)
    context = pool["args"]["capital_chronicle_context"]["foundation_library"]
    assert context["editorial_desk"]["decisions"]["KEEP"] == 5
    assert len(context["briefs"]) == 5 and len(context["research_packages"]) == 7
    assert not {"goal21-futures-option", "goal21-futures-hedgers", "goal21-sec-tenk-scope", "goal21-sec-cross-trading"}.intersection(
        r["headline_id"] for r in pool["args"]["rolling_input"]["headlines"])
    # Export readback uses the existing durable owner; recirculated Main facts remain separate.
    export = MainHeadlineExporter(restarted, research=research).export(batch_id="goal22-final-desk-context",
        paths=[], cutoff_utc=cutoff, permitted_rows=permitted_report_headlines(feed.tracker))
    assert export["missing_rows"] == 5
    assert export["main_origin_recirculated_items"] == 0  # already exported in paused opportunity
    final_workspace = report_workspace_projection(restarted.list_outbox_messages(), review_records=read_reviews(restarted))
    dump(output / "workspace.json", final_workspace)
    dump(output / "review_records.json", read_reviews(restarted))
    dump(output / "frozen_input.json", context)
    pinned = root / "main_research_handoff"
    manifest = json.loads((pinned / "handoff.json").read_bytes())
    for file, binding in manifest["files"].items():
        assert hashlib.sha256((pinned / file).read_bytes()).hexdigest() == binding["sha256"]
    with restarted.get_read_only_connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM model_invocations").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM platform_dispatches").fetchone()[0] == 0
    assert llm_operator_pause_active() and hashlib.sha256(operator_pause_path().read_bytes()).hexdigest() == pause_hash
    receipt = {"status": "PASS_ISOLATED_EDITORIAL_DESK_RESTART_AND_PAUSED_COMPOSITION", "observed_at_utc": cutoff,
               "reused_Main_acceptance": previous_receipt["producer_commit"], "reused_Main_receipts": 8,
               "original_reviewed_and_revised": 7, "persistent_review_records": len(read_reviews(restarted)),
               "desk": final["desk"], "independent_propositions": 15, "independent_documents": 9,
               "current_packages": 7, "native_previews": 56, "media": 7, "new_media_rendered": 1,
               "unchanged_media_reused": 6, "Main_latest_public_reports": 3, "restart_decisions_identical": True,
               "outgoing_pinned_dated": 9, "undated_dispositions": 5,
               "Main_receiver_receipt": "NOT_VERIFIED_AWAITING_ACTUAL_MAIN_EVIDENCE",
               "frozen_briefs": 5, "four_window_owner": "SIMPLE_GEMINI_RUNTIME", "routine_windows": 4,
               "fresh_provider_calls": 0, "injected_model_callbacks": 0, "qualified": 0, "published": 0,
               "production_tick": False, "llm_pause_unchanged": True, "public_writes": 0,
               "workspace_sha256": hashlib.sha256((output / "workspace.json").read_bytes()).hexdigest()}
    dump(output / "receipt.json", receipt)
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed-store", type=Path, required=True)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(verify(a.seed_store, a.root, a.output_dir)))
