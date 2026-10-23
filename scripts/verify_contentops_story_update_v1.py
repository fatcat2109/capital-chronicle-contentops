"""One isolated evolving-story update/restart/composition proof over accepted Goal22.

Uses the real existing four-window scheduler delegate, without ticking a window,
clearing pause, injecting a model result, or opening production for writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker, canonical_bytes, sha256_of
from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection
from live_contentops.contentops_editorial_desk_v1 import read_reviews, record_review
from live_contentops.contentops_foundation_library_v1 import library_projection, persist_library, persist_research_package
from live_contentops.contentops_main_headline_projection_v1 import MainHeadlineExporter
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.llm_operator_control_v1 import operator_pause_path, llm_operator_pause_active
from live_contentops.newsroom_assignment_scheduler_v1 import load_rolling_x_headline_sidecars
from live_contentops.published_corpus_read_model_v1 import load_canonical_published_memory_read_only
from live_contentops.v1_simple_gemini_newsroom_v1 import _candidate_packet_and_preselection
from live_contentops.v1_simple_gemini_scheduler_v1 import SimpleGeminiLocalScheduler


def dump(path, value):
    path.write_bytes(canonical_bytes(value) + b"\n")


def verify(seed, root, output, memory_store, memory_output):
    seed = seed.resolve(strict=True)
    if seed.name != "desk-proof.sqlite3" or seed.parent.name != "goal22-integrated-desk-final" or output.exists():
        raise ValueError("EXACT_GOAL22_ISOLATED_SEED_AND_NEW_OUTPUT_REQUIRED")
    if not llm_operator_pause_active():
        raise ValueError("CURRENT_LLM_PAUSE_REQUIRED")
    pause_hash = hashlib.sha256(operator_pause_path().read_bytes()).hexdigest()
    output.mkdir(parents=True)
    path = output / "story-proof.sqlite3"
    source = sqlite3.connect(f"file:{seed.as_posix()}?mode=ro", uri=True)
    target = sqlite3.connect(path)
    source.backup(target)
    source.close()
    target.close()
    store = ContentOpsDurableStore(path)
    tracker = LatestReportDeliveryTracker(store)
    before = library_projection(store.list_outbox_messages(), read_reviews(store))
    assert before["desk"]["decisions"]["KEEP"] == 5 and before["desk"]["decisions"]["HOLD"] == 2
    dump(output / "before_workspace.json", report_workspace_projection(store.list_outbox_messages(), review_records=read_reviews(store)))
    cutoff = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    research = RetainedSourceResearch(root / "retained_research")
    briefs = json.loads((root / "editorial_briefs.json").read_bytes())["briefs"]
    persist_library(tracker, research, cutoff_utc=cutoff, briefs=briefs)
    invalidated = library_projection(store.list_outbox_messages(), read_reviews(store))
    stale = {p["brief_id"] for p in invalidated["packages"] if p["review"]["state"] == "STALE"}
    assert stale == {"gas-vintage", "options-positioning", "company-sec-context"}
    dump(output / "input_change_workspace.json", report_workspace_projection(store.list_outbox_messages(), review_records=read_reviews(store)))
    packages = json.loads((root / "retained_research/packages.json").read_bytes())
    for package in packages:
        persist_research_package(tracker, package, research_revision=research.revision)
    current = library_projection(store.list_outbox_messages(), read_reviews(store))
    rationales = {
        "gas-vintage": "KEEP nghiên cứu: đối chiếu đúng XNGUSD v2 với EIA ngày 15/10 cho tuần 9/10. Không nhận là số mới; phân biệt mùa vụ với kỳ vọng trước công bố, giữ điều kiện thời tiết/LNG/curve và quyền dùng. Đã đọc bài, tám native previews và media giữ nguyên.",
        "energy-balance-transmission": "KEEP nghiên cứu: dầu Mỹ, Brent và gas có cơ chế khác nhau; dữ kiện dầu được quy nguồn Main công khai, gas đối chiếu EIA độc lập cùng số. Không biến ba bản Main thành ba xác nhận; có phản đề nhập khẩu, tích kho xăng và spread. Không target hay giá hiện tại.",
    }
    for p in current["packages"]:
        b = next(b for b in briefs if b["brief_id"] == p["brief_id"])
        if p["brief_id"] in rationales or b.get("hold_reason"):
            record_review(store, brief_id=p["brief_id"], package_revision=p["package_revision"],
                decision="HOLD" if b.get("hold_reason") else "KEEP", rationale=b.get("hold_reason") or rationales[p["brief_id"]],
                expected_review_id=p["review"]["latest_review_id"])
    memory, memory_proof = load_canonical_published_memory_read_only(store_path=memory_store, output_root=memory_output)
    dump(output / "published_memory_access.json", memory_proof)
    # Reuse the real existing sidecar loader. No synthetic current-news candidate.
    rolling = load_rolling_x_headline_sidecars(cutoff_utc=cutoff)
    pointer_path = root / "provider_resume_binding.json"
    prior_pointer = os.environ.get("CONTENTOPS_MAIN_REPORT_FEED_POINTER")
    os.environ["CONTENTOPS_MAIN_REPORT_FEED_POINTER"] = str(pointer_path.resolve())
    try:
        scheduler = SimpleGeminiLocalScheduler(scheduler_root=output / "existing-scheduler-composition",
            published_memory_store=path, published_memory_output_root=memory_output,
            published_memory_loader=lambda: (memory, memory_proof))
        assert scheduler._report_feed is not None and len(scheduler.policy.core_windows) == 4
        result = scheduler._execute_canonical_simple_operation(output_dir=output / "opportunity", cutoff_utc=cutoff,
            run_id="goal23-existing-four-window-story-pool", published_memory=memory, rolling_input=rolling)
        assert result["exact_next_blocker"] == "LLM_OPERATOR_PAUSED"
        # Restart the same owner and stable run; the exact pool remains frozen.
        restarted = SimpleGeminiLocalScheduler(scheduler_root=output / "existing-scheduler-composition",
            published_memory_store=path, published_memory_output_root=memory_output,
            published_memory_loader=lambda: (memory, memory_proof))
        repeated = restarted._execute_canonical_simple_operation(output_dir=output / "opportunity", cutoff_utc=cutoff,
            run_id="goal23-existing-four-window-story-pool", published_memory=memory, rolling_input=rolling)
        assert sha256_of(result) == sha256_of(repeated)
    finally:
        if prior_pointer is None:
            os.environ.pop("CONTENTOPS_MAIN_REPORT_FEED_POINTER", None)
        else:
            os.environ["CONTENTOPS_MAIN_REPORT_FEED_POINTER"] = prior_pointer
    pools = [json.loads(r["payload"]) for r in store.list_outbox_messages() if r["destination"] == "internal:cc-report-editorial-stage" and "args" in json.loads(r["payload"])]
    pool = next(p for p in reversed(pools) if p["args"]["capital_chronicle_context"].get("foundation_library", {}).get("research_revision") == research.revision)
    assert len(pool["args"]["published_memory"]) == len(memory)
    assert all(s["canonical_memory_article_count"] == len(memory) for s in pool["args"]["capital_chronicle_context"]["foundation_library"]["stories"])
    candidates, order = _candidate_packet_and_preselection(pool["args"]["rolling_input"], pool["args"]["published_memory"])
    assert len(candidates) <= 32
    contexts = [s for c in candidates for s in c.get("evolving_story_context", [])]
    assert any(c["brief_id"] == "gas-vintage" for c in contexts)
    assert not any(c["current_review"].get("state") == "HOLD" for c in contexts)
    dump(output / "candidate_packet.json", {"candidates": candidates, "preselection": order, "ordinary_intake_headlines": len(rolling.get("headlines", []))})
    dump(output / "frozen_pool.json", pool)
    dump(output / "paused_result.json", result)
    # An identical rescan on the next day does not register article/media/review/library work.
    before_rows = len(store.list_outbox_messages())
    persist_library(tracker, research, cutoff_utc=(datetime.fromisoformat(cutoff.replace("Z", "+00:00")) + timedelta(days=1)).isoformat().replace("+00:00", "Z"), briefs=briefs)
    assert len(store.list_outbox_messages()) == before_rows
    export = MainHeadlineExporter(store, research=research).export(batch_id="goal23-identical-scan-zero-delta", paths=[], cutoff_utc=cutoff)
    assert export["eligible_rows"] == 0 and export["new_independent_observations"] == 0
    dump(output / "zero_delta_export_page.json", export)
    final = library_projection(store.list_outbox_messages(), read_reviews(store))
    unchanged = {p["brief_id"] for p in final["packages"] if any(old["brief_id"] == p["brief_id"] and old["article_identity"] == p["article_identity"] for old in before["packages"])}
    assert unchanged == {"rates-fx-transmission", "metals-exposure", "options-positioning", "company-sec-context", "crypto-custody", "cross-asset-price-versus-custody"}
    assert final["desk"]["decisions"] == {"KEEP": 6, "HOLD": 2, "REVISE": 0, "STALE": 0, "UNREVIEWED": 0}
    assert len(tracker.receipts()) == 8
    assert hashlib.sha256(operator_pause_path().read_bytes()).hexdigest() == pause_hash
    dump(output / "final_workspace.json", report_workspace_projection(store.list_outbox_messages(), review_records=read_reviews(store)))
    dump(output / "review_records.json", read_reviews(store))
    receipt = {"status": "PASS_ISOLATED_STORY_UPDATE_RESTART_EXISTING_FOUR_WINDOW_COMPOSITION", "store": str(path.resolve()),
        "canonical_memory": memory_proof, "ordinary_intake_headlines": len(rolling.get("headlines", [])), "candidate_count": len(candidates),
        "exact_same_pool_restart": True, "next_day_identical_scan_new_work": 0, "changed_articles": 1, "new_articles": 1,
        "unchanged_article_ids": sorted(unchanged), "decisions": final["desk"]["decisions"], "main_receipts": len(tracker.receipts()),
        "provider_calls": 0, "injected_model_callbacks": 0, "qualified_simple_articles": 0, "public_writes": 0,
        "production_tick": False, "llm_pause_sha256": pause_hash, "main_receiver": "MAIN_GOAL23_OWNS_RECEIVER_NOT_INVOKED"}
    dump(output / "receipt.json", receipt)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("seed", "root", "output", "memory-store", "memory-output"):
        parser.add_argument("--" + name, type=Path, required=True)
    a = parser.parse_args()
    print(json.dumps(verify(a.seed, a.root, a.output, a.memory_store, a.memory_output)))
