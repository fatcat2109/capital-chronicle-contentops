"""Explicit controlled-output acceptance over real retained source and Main bytes.

No provider, runtime activation, canonical-store mutation or public action. The
unchanged Goal19 Main contract examples prove compatibility only; they are not
new independent intake or new Goal20 Main production.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker
from live_contentops.capital_chronicle_report_feed_v1 import MainReportFeed
from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from tests.test_contentops_source_research_v1 import independent_writer
from tests.test_capital_chronicle_report_editorial_workspace_v1 import controlled_writer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    cutoff = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    store_path = Path(tempfile.mkdtemp(prefix="goal20-connected-")) / "isolated.sqlite3"
    tracker = LatestReportDeliveryTracker(ContentOpsDurableStore(store_path))
    pointer = json.loads((Path(__file__).parents[1] / "goal19/main_producer_pointer.json").read_bytes())
    research = RetainedSourceResearch(Path(__file__).parent / "retained_research")
    feed = MainReportFeed(tracker, pointer, headline_paths=[], retained_research=research)
    scan = feed.poll(cutoff_utc=cutoff)
    calls, results = [], []
    for target in ("goal20-eia-grid-peaks", "goal20-eia-smallscale-solar", "goal20-bls-cpi-september", "asset-report:USOIL", "asset-report:XNGUSD"):
        key = target.replace(":", "-")
        if target.startswith("goal20-"):
            invoke = independent_writer(research, calls, target)
        else:
            main_control = controlled_writer(calls)
            def invoke(target=target, **kwargs):
                g = kwargs["governed_input"]
                if "candidates" in g:
                    result, receipt = main_control(**kwargs)
                    selected = next(c for c in g["candidates"] if c["report_editorial_context"].get("report_id") == target)
                    result["ordered_candidate_plan"][0]["candidate_id"] = selected["candidate_id"]
                    return result, receipt
                result, receipt = main_control(**kwargs)
                oil = target.endswith("USOIL")
                title = "Capital Chronicle report: oil stocks and conflicting product signals" if oil else "Capital Chronicle report: gas injection and seasonal balance"
                article = result["article"]
                for field in ("title", "dek", "search_title", "meta_description", "social_hook"):
                    old = article[field]
                    article[field] = title if field in {"title", "search_title"} else "CC REPORT / EVENT UNCONFIRMED. " + title + ". Proxy and cost limits remain unresolved."
                    for claim in result["material_claim_bindings"]:
                        if claim["claim_text"] == old:
                            claim["claim_text"] = article[field]
                return result, receipt
        result = feed.opportunity(output_dir=args.output_dir / key, cutoff_utc=cutoff, run_id="goal20-controlled-" + key,
                                  rolling_input={"headlines": []}, llm_invoke=invoke)
        workspace = result["report_workspace_result"]
        if workspace["draft_count"] != 1:
            raise AssertionError({"target": target, "classification": workspace["classification"], "blocker": workspace.get("exact_next_blocker"), "validation": result.get("validation_blockers")})
        results.append(workspace)
        before = len(calls)
        feed.opportunity(output_dir=args.output_dir / key, cutoff_utc=cutoff, run_id="goal20-controlled-" + key,
                         llm_invoke=lambda **_: (_ for _ in ()).throw(AssertionError("repeated model call")))
        assert len(calls) == before
    # One actual pause observation, zero provider calls. Existing marker remains untouched.
    paused = feed.opportunity(output_dir=args.output_dir / "paused", cutoff_utc=cutoff, run_id="goal20-pause-observation", rolling_input={"headlines": []})
    workspace = report_workspace_projection(tracker.store.list_outbox_messages())
    receipt = {"observed_at_utc": cutoff, "isolated_store": str(store_path), "main_contract_scan": scan,
               "independent_acquired_admitted": len(research.records), "compatibility_main_events": scan["new_events"],
               "goal20_new_main_manifest_events": 0, "controlled_drafts": len(results), "native_previews": sum(len(r["previews"]) for r in results),
               "rendered_media": sum(len(r.get("media_assets", [])) for r in results), "injected_callbacks": len(calls),
               "fresh_provider_calls": 0, "public_writes": 0, "runtime_started": False,
               "pause_state": paused["report_workspace_result"]["model_execution_state"],
               "main_manifest_state": "MAIN_OWNER_IMMUTABLE_HANDOFF_PENDING"}
    for name, value in (("receipt.json", receipt), ("workspace.json", workspace)):
        (args.output_dir / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf8")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
