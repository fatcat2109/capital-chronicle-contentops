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
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, DesktopInputRequired
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.codex_desktop_newsroom_operator_v1 import native_role_call
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.native_editorial_continuation_v1 import next_editorial_action
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of


class FrozenReplayResearch:
    """Resolve retained evidence; never fall through to a fresh network acquisition."""

    def __init__(self, retained):
        self.retained = retained
        self.revision = retained.revision
        self.records = retained.records
        self.evidence_cache_revision = "FROZEN_CANONICAL_RELAY_V1"

    def evidence(self, request, *, cutoff_utc):
        retained = self.retained.evidence(request, cutoff_utc=cutoff_utc)
        if retained:
            return retained
        from live_contentops.v1_simple_evidence_resolver_v1 import SimpleFirstPartyAwareEvidenceResolver
        from live_contentops.v1_simple_epistemic_state_v1 import canonical_x_report_document
        document, _ = canonical_x_report_document(request)
        if document is not None:
            # This is the existing exact captured-word route; no new GET,
            # publisher-original claim, rights grant or underlying event proof.
            resolver = SimpleFirstPartyAwareEvidenceResolver(evaluation_as_of_utc=cutoff_utc)
            profile = (request.get("story_context") or {}).get("report_provenance") or {}
            route = "TRUSTED_RELAY_ATTRIBUTED_REPORT" if profile.get("explicit_reputable_attribution") else "TRUSTED_MARKET_RUMOR"
            value = {"status": "PASS", "evidence_documents": [document],
                "provided_evidence_capabilities": ["attributed_report_provenance"], "blockers": [],
                "provenance": {"request_count": 0}}
            accepted, state, blockers = resolver._accepted_epistemic_route(request, value, route=route)
            if accepted and state is not None:
                return resolver._normalized_result(request=request, result=value,
                    route_history=[{"route": route, "status": "PASS", "request_count_for_route": 0,
                        "accepted_document_count": len(accepted), "blockers": blockers}],
                    call_start=0, selected_route=route, epistemic_state=state, accepted_documents=accepted)
        return {
            "status": "BLOCKED", "evidence_documents": [],
            "blockers": ["FROZEN_REPLAY_NO_ADMITTED_SOURCE"],
            "provenance": {"request_count_for_call": 0, "network_acquisition_on_replay": False}}


def pending_result(requests, binding, *, same_writer=None, same_writer_configuration=None):
    first = requests[0]
    result = {"classification": "NATIVE_DESKTOP_INPUT_REQUIRED", "stage": first["stage"],
              "filter_progress": first.get("filter_progress", {})}
    if not first.get("requested_model"):
        if len(requests) != 1 or first["stage"] != "media-plan":
            raise ValueError("EXACT_PENDING_EDITORIAL_COMMAND_REQUIRED")
        result["next_command"] = {"command": "media-plan", "binding_path": str(Path(binding["output_dir"]) / "binding.json")}
    else:
        result["next_native_calls"] = [native_role_call(r, binding,
            binding_path=Path(binding["output_dir"]) / "binding.json",
            same_writer_invocation=same_writer if r["role"] not in {"filter", "select"} else None,
            same_writer_configuration=same_writer_configuration)
            for r in requests]
    result["coordinator_action"] = next_editorial_action(result)
    return result


def resume_frozen_window(store, binding, args, reports, research):
    """Use the canonical result owner, including its durable final article record."""
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker
    from live_contentops.capital_chronicle_report_editorial_workspace_v1 import run_report_editorial_cycle, _Stages
    pool_key = "cc-editorial-pool-" + sha256_of(binding["run_id"])
    if (not store.get_outbox_message(pool_key)
            and not store.get_outbox_message("cc-editorial-final-" + sha256_of(binding["run_id"]))):
        # Adopt exactly the original pool, including prepared report inputs and
        # its research revision. Do not reconstruct a pool from later sources.
        matches = [json.loads(row["payload"]) for row in store.list_outbox_messages()
            if row["message_id"].startswith("cc-editorial-pool-")
            and json.loads(row["payload"]).get("args") == args
            and json.loads(row["payload"]).get("reports") == reports]
        if not matches or any(value != matches[0] for value in matches):
            raise ValueError("EXACT_ORIGINAL_FROZEN_POOL_REQUIRED")
        _Stages(LatestReportDeliveryTracker(store), "independent-" + sha256_of(binding["run_id"]),
                binding["run_id"]).put(pool_key, matches[0])
    turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=binding["output_dir"], owner_manual_validation=True)
    root = Path(binding["output_dir"])
    evidence_path = root / "simple_gemini_evidence_v1.json"
    if evidence_path.is_file() and not turn.frozen_request("write"):
        old = json.loads(evidence_path.read_bytes())
        if old.get("status") == "BLOCKED" and any("FROZEN_REPLAY_NO_ADMITTED_SOURCE" in a.get("blockers", [])
                for a in old.get("candidate_attempt_history", [])):
            # Preserve failed attempt artifacts before a corrected deterministic
            # source route can produce different evidence. Accepted native
            # requests/returns and the original cached failures remain intact.
            history = root / "blocked-attempts" / sha256_of(old)
            history.mkdir(parents=True, exist_ok=True)
            for name in ("simple_gemini_evidence_v1.json", "simple_gemini_newsroom_receipt_v1.json"):
                source, target = root / name, history / name
                if source.is_file():
                    if target.exists():
                        if target.read_bytes() != source.read_bytes():
                            raise ValueError("FROZEN_REPLAY_FAILED_HISTORY_CONFLICT")
                    else:
                        source.rename(target)
    return run_report_editorial_cycle(LatestReportDeliveryTracker(store),
        receipt_id=reports[0]["receipt_id"] if reports else "independent-" + sha256_of(binding["run_id"]),
        admission=reports[0] if reports else None, additional_reports=reports[1:],
        output_dir=binding["output_dir"], cutoff_utc=binding["cutoff_utc"],
        run_id=binding["run_id"], opportunity_id=binding["run_id"], llm_invoke=turn,
        retained_research=FrozenReplayResearch(research))


def editorial_command(store, binding, command, response=None):
    # Only local editorial commands are exposed. The production CLI supplies
    # media, final-review and review validation; publication is never routed.
    from scripts.run_native_desktop_editorial import operation, BINDING_SCHEMA
    root = Path(binding["output_dir"])
    local = {**binding, "schema_version": BINDING_SCHEMA,
        "feed_pointer_path": str(root / "unused-frozen-feed-pointer.json"),
        "published_memory_store": binding["store_path"], "published_memory_output_root": str(root)}
    return operation(local, command=command, response=response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "filter", "advance", "submit", "media-plan", "media", "final-visual-review", "review", "handoff"])
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
    if (Path(binding["store_path"]).resolve() != root / "copied.sqlite3"
            or Path(binding["output_dir"]).resolve() != root or binding.get("owner_manual_validation") is not True):
        raise ValueError("COPIED_STORE_REQUIRED")
    store = ContentOpsDurableStore(root / "copied.sqlite3", auto_migrate=False)
    if store.get_operating_control()["operating_mode"] != "SHADOW_ONLY":
        raise ValueError("COPIED_STORE_SHADOW_MODE_REQUIRED")
    turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=root, owner_manual_validation=True)
    args = json.loads((root / "frozen-pool.json").read_bytes())
    if options.command == "submit":
        result = turn.submit(options.stage, json.loads(options.response.read_bytes()))
    elif options.command in {"media-plan", "media", "final-visual-review", "review", "handoff"}:
        result = editorial_command(store, binding, options.command,
            json.loads(options.response.read_bytes()) if options.response else None)
    else:
        try:
            if options.command == "filter":
                _, receipt = turn.filter_headlines(args["rolling_input"])
                (root / "filter-result.json").write_text(json.dumps(receipt), encoding="utf-8")
                result = {"classification": "FILTER_COMPLETE", "seen": receipt["seen"], "remaining_unprocessed": receipt["remaining_unprocessed"]}
            else:
                research = RetainedSourceResearch(repository / "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal23/retained_research")
                reports = json.loads((root / "frozen-reports.json").read_bytes())
                result = resume_frozen_window(store, binding, args, reports, research)
                (root / "window-result.json").write_text(json.dumps(result, default=str), encoding="utf-8")
                result = {k:result.get(k) for k in ("classification", "qualified_article_count", "exact_next_blocker", "article_path")}
        except DesktopInputRequired as pending:
            requests = pending.request.get("parallel_requests", [pending.request])
            prior = turn._get("write", "response") or turn.visual_response()
            writer = prior["invocation_observation"]["invocation_id"] if prior else options.same_writer
            result = pending_result(requests, binding, same_writer=writer,
                same_writer_configuration=prior["invocation_observation"] if prior else None)
            (root / "pending-calls.json").write_text(json.dumps(result.get("next_native_calls", []), indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True, default=str))


if __name__ == "__main__":
    main()
