"""Bounded CC-041 copied-store replay; never publication or a scheduler.

The parent conversation supplies real native returns. Raw replay inputs/results stay
private locally. The copied store is prepared with SQLite's read-only online backup.
"""
from pathlib import Path
import argparse
import json
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, DesktopInputRequired, run_native_desktop_newsroom
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.codex_desktop_newsroom_operator_v1 import native_role_call
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.native_editorial_continuation_v1 import next_editorial_action
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "filter", "advance", "submit"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--response", type=Path)
    parser.add_argument("--stage")
    parser.add_argument("--same-writer")
    options = parser.parse_args()
    root = options.root.resolve()
    repository = Path(__file__).resolve().parents[1]
    if root != repository / "tests/evidence/cc-041/private-replay":
        raise ValueError("EXACT_CC041_ISOLATED_COPY_REQUIRED")
    if options.command == "prepare":
        root.mkdir(parents=True, exist_ok=True)
        copy_path = root / "copied.sqlite3"
        if not copy_path.exists():
            source = Path("A:/Capital Chronicle/Runtime/ContentOps/contentops_daily_app_v1.sqlite3")
            with sqlite3.connect(source.as_uri()+"?mode=ro", uri=True) as original, sqlite3.connect(copy_path) as copied:
                original.backup(copied)
        store = ContentOpsDurableStore(copy_path, auto_migrate=False)
        with store.get_read_only_connection() as connection:
            row = connection.execute("SELECT payload FROM outbox_messages WHERE message_id LIKE 'cc-editorial-pool-%' ORDER BY rowid DESC LIMIT 1").fetchone()
        if row is None:
            raise ValueError("COPIED_FROZEN_WINDOW_POOL_MISSING")
        pool = json.loads(row[0])
        run_id = "cc-041-copied-window-20261030"
        binding = {"run_id": run_id, "output_dir": str(root), "store_path": str(copy_path),
                   "owner_manual_validation": True, "cutoff_utc": pool["args"]["cutoff_utc"]}
        for name, value in (("frozen-pool.json", pool["args"]), ("frozen-reports.json", pool["reports"]), ("binding.json", binding)):
            path = root/name
            if path.exists():
                if json.loads(path.read_bytes()) != value:
                    raise ValueError("EXISTING_REPLAY_BINDING_CHANGED")
            else:
                path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        work = "cc-opportunity-"+sha256_of(run_id)
        store.create_work_item(story_id=work, work_item_id=work, title="CC-041 copied-store replay", target_surface="CONTENTOPS_EDITORIAL_ONLY")
        control = store.get_operating_control()
        if control["operating_mode"] != "SHADOW_ONLY":
            store.update_operating_control(expected_state_version=control["state_version"], operating_mode="SHADOW_ONLY", control_source="CC041_COPIED_STORE_ZERO_WRITE_ACCEPTANCE")
        print(json.dumps({"copied_store": str(copy_path), "mode": "SHADOW_ONLY", "live_store_written": False}))
        return
    binding = json.loads((root / "binding.json").read_bytes())
    if Path(binding["store_path"]).resolve() != root / "copied.sqlite3":
        raise ValueError("COPIED_STORE_REQUIRED")
    store = ContentOpsDurableStore(root / "copied.sqlite3", auto_migrate=False)
    turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=root, owner_manual_validation=True)
    args = json.loads((root / "frozen-pool.json").read_bytes())
    if options.command == "submit":
        result = turn.submit(options.stage, json.loads(options.response.read_bytes()))
    else:
        try:
            if options.command == "filter":
                _, receipt = turn.filter_headlines(args["rolling_input"])
                (root / "filter-result.json").write_text(json.dumps(receipt), encoding="utf-8")
                result = {"classification": "FILTER_COMPLETE", "seen": receipt["seen"], "remaining_unprocessed": receipt["remaining_unprocessed"]}
            else:
                research = RetainedSourceResearch(repository / "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal23/retained_research")
                from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_evidence
                reports = json.loads((root / "frozen-reports.json").read_bytes())
                by_headline = {"cc-report:" + r["envelope_sha256"]: r for r in reports}
                def loader(request):
                    report = next((by_headline[h] for h in request.get("headline_ids", []) if h in by_headline), None)
                    if report is not None:
                        return report_evidence(report)
                    return research.evidence(request, cutoff_utc=args["cutoff_utc"]) or {
                        "status": "BLOCKED", "evidence_documents": [],
                        "blockers": ["FROZEN_REPLAY_NO_ADMITTED_SOURCE"],
                        "provenance": {"request_count_for_call": 0, "network_acquisition_on_replay": False}}
                allowed = {k:args[k] for k in ("cutoff_utc", "rolling_input", "published_memory", "capital_chronicle_context", "source_route_health", "attempted_candidate_ids") if k in args}
                result = run_native_desktop_newsroom(output_dir=root, run_id=binding["run_id"], llm_invoke=turn, evidence_loader=loader, **allowed)
                (root / "window-result.json").write_text(json.dumps(result, default=str), encoding="utf-8")
                result = {k:result.get(k) for k in ("classification", "qualified_article_count", "exact_next_blocker", "article_path")}
        except DesktopInputRequired as pending:
            requests = pending.request.get("parallel_requests", [pending.request])
            calls = [native_role_call(r, binding, binding_path=root / "binding.json", same_writer_invocation=options.same_writer if r["role"] not in {"filter", "select"} else None) for r in requests]
            (root / "pending-calls.json").write_text(json.dumps(calls, indent=2), encoding="utf-8")
            result = {"classification": "NATIVE_DESKTOP_INPUT_REQUIRED", "stage": pending.request["stage"], "filter_progress": pending.request.get("filter_progress", {}), "next_native_calls": calls}
            result["coordinator_action"] = next_editorial_action(result)["action"]
    print(json.dumps(result, ensure_ascii=True, default=str))


if __name__ == "__main__":
    main()
