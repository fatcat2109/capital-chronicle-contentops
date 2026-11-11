"""CC-306: queue one post per new plan-state change for the six markets (one run, then exit).

    python scripts/plan_status_posts.py [--dry-run] [--export-dir DIR] [--store PATH]
                                        [--window-minutes N] [--main-root DIR]

Reads Main's plan-status export through CC-307's own reader (read_public_status and
read_public_transitions, run in Main's live root) and registers one READY_FOR_PUBLISHER outbox
row per new transition in the ContentOps store. Repeats change nothing. --publish continues
through the existing coordinator. --dry-run uses SQLite read-only access, renders each
candidate and retained format-4 post through the destination compiler, and reports
validation PASS/FAIL with a failing field path. It queues, publishes and records nothing,
including when --publish is also supplied.

An export written more than 10 minutes before the run is refused (EXPORT_STALE): nothing is
queued or posted in that run. Every run except a dry run appends one line (status, cause, the
export's clock and age, counts) to daily_app_outputs/plan_status_post_runs/runs-YYYYMMDD.jsonl
beside the store.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore  # noqa: E402
from live_contentops.plan_status_posts_v1 import (  # noqa: E402
    EXPORT_DIR, MAIN_ROOT, POSTING_WINDOW_MINUTES, queue_posts,
)
from live_contentops.published_content_v1 import PRODUCTION_STORE  # noqa: E402


class _ReadOnlyStore(ContentOpsDurableStore):
    """Reuse the existing store's reads with SQLite enforcing no writes."""
    get_connection = ContentOpsDurableStore.get_read_only_connection


def child_python() -> str:
    # Under pythonw the reader child still needs a console-less interpreter with jsonschema.
    here = Path(sys.executable)
    sibling = here.with_name("python.exe")
    return str(sibling if here.name.lower() == "pythonw.exe" and sibling.is_file() else here)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="validate the export and render posts without writes")
    parser.add_argument("--export-dir", type=Path, default=EXPORT_DIR)
    parser.add_argument("--store", type=Path, default=PRODUCTION_STORE)
    parser.add_argument("--window-minutes", type=int, default=POSTING_WINDOW_MINUTES)
    parser.add_argument("--main-root", type=Path, default=MAIN_ROOT)
    parser.add_argument("--publish", action="store_true",
                        help="after queueing, post queued rows through the coordinator")
    parser.add_argument("--scorecard-only", action="store_true",
                        help="update only the pinned Telegram result record, without queueing feed posts")
    parser.add_argument("--pending-x", action="store_true", help="list status posts' X requests for an agent")
    parser.add_argument("--x-start", metavar="KEY", help="register this post's X copy through Neo")
    parser.add_argument("--x-begin", nargs=2, metavar=("KEY", "REQUEST_SHA256"))
    parser.add_argument("--x-submit", nargs=3, metavar=("KEY", "REQUEST_SHA256", "RESPONSE_JSON"))
    parser.add_argument("--pending-notes", action="store_true", help="list status posts' Substack Notes requests")
    parser.add_argument("--notes-start", metavar="KEY", help="register this post's full Substack Note through Neo")
    parser.add_argument("--notes-begin", nargs=2, metavar=("KEY", "REQUEST_SHA256"))
    parser.add_argument("--notes-submit", nargs=3, metavar=("KEY", "REQUEST_SHA256", "RESPONSE_JSON"))
    parser.add_argument("--native-invocation-id", default="")
    args = parser.parse_args(argv)
    store_type = _ReadOnlyStore if args.dry_run else ContentOpsDurableStore
    store = store_type(args.store, auto_migrate=False)
    from live_contentops import plan_status_posts_v1 as posts
    if args.dry_run and (args.pending_x or args.x_start or args.x_begin or args.x_submit
                         or args.pending_notes or args.notes_start or args.notes_begin or args.notes_submit):
        parser.error("--dry-run renders the export; use it without agent request actions")
    if (args.pending_x or args.x_start or args.x_begin or args.x_submit
            or args.pending_notes or args.notes_start or args.notes_begin or args.notes_submit):
        if args.pending_x or args.pending_notes:
            destination = "substack_notes" if args.pending_notes else "x"
            result = {"status": "OK", "pending_" + destination: posts.pending_x(store, destination=destination)}
        elif not args.native_invocation_id:
            result = {"status": "NATIVE_INVOCATION_ID_REQUIRED"}
        elif args.x_start or args.notes_start:
            result = {"status": "OK", "start": posts.start_x(store, args.x_start or args.notes_start,
                destination="substack_notes" if args.notes_start else "x",
                native_invocation_id=args.native_invocation_id)}
        elif args.x_begin or args.notes_begin:
            result = {"status": "OK", "begin": posts.begin_x(store, *(args.x_begin or args.notes_begin),
                native_invocation_id=args.native_invocation_id)}
        else:
            key, request_hash, response = args.x_submit or args.notes_submit
            result = {"status": "OK", "submit": posts.submit_x(store, key, request_hash,
                json.loads(Path(response).read_text(encoding="utf-8")),
                native_invocation_id=args.native_invocation_id)}

    elif args.scorecard_only:
        from live_contentops.pinned_result_scorecard_v1 import refresh_scorecard
        result = {"scorecard": refresh_scorecard(store, args.export_dir, main_root=args.main_root,
            python=child_python(), dry_run=args.dry_run)}
        result["status"] = "OK" if result["scorecard"]["status"] in {"CONFIRMED", "PREVIEW"} else "SCORECARD_NOT_CONFIRMED"
    else:
        # Decision 124: run private reply delivery first, before potentially slow
        # chart/publication work. This reuses the minute entry without a new schedule.
        reply_bot = None
        if args.publish and not args.dry_run:
            from live_contentops.x_reply_bot_v1 import refresh_due as bot_refresh
            try:
                reply_bot = bot_refresh(store, binding_path=args.store.parent / "control/x_reply_bot_binding.json")
            except Exception as exc:
                reply_bot = {"status": "REPLY_BOT_FAILED", "cause": type(exc).__name__, "public_submit_actions": 0}
        from live_contentops.instagram_adapter_v6 import readback_analysis_profile_link
        result = queue_posts(store, args.export_dir, window_minutes=args.window_minutes, dry_run=args.dry_run,
                             render_all=args.dry_run,
                             instagram_profile_reader=readback_analysis_profile_link if args.publish and not args.dry_run else None,
                             main_root=args.main_root, python=child_python())
        if reply_bot is not None:
            result["reply_bot"] = reply_bot
        if args.dry_run:
            result["validation"] = "PASS" if result["status"] == "OK" else "FAIL"
        if args.publish and not args.dry_run and result["status"] == "OK":
            from live_contentops.pinned_result_scorecard_v1 import refresh_scorecard
            result["scorecard"] = refresh_scorecard(store, args.export_dir, main_root=args.main_root,
                                                  python=child_python())
            result["publication"] = posts.publish_ready(store, latest_states=result.get("latest_states"),
                                                       active_recoveries=result.get("active_recoveries"), automatic_neo=True)
            from live_contentops.plan_analysis_pages_v1 import resume_discord_links
            result["publication"].setdefault("posts", []).extend(resume_discord_links(store,
                latest_states=result.get("latest_states") or {}, now=datetime.now(timezone.utc)))
            from live_contentops.neo_endpoint_executor_v1 import resume_stored_requests
            result["publication"]["neo_stored_requests"] = resume_stored_requests(store)
        if not args.dry_run:
            if args.publish:
                # Decision 123: reuse this minute entry with a two-hour gate.
                # Reply drafts do not depend on Main's status-export freshness.
                from live_contentops.x_reply_tabs_v1 import refresh_due
                try:
                    result["reply_tabs"] = refresh_due(store,
                        control_path=args.store.parent / "control/x_reply_tabs.json",
                        output_root=args.store.parent / "daily_app_outputs/x_reply_pack",
                        feed_path=args.store.parent / "x_list_feed/x_list_feed_v1.json")
                except Exception as exc:
                    result["reply_tabs"] = {"status": "REFRESH_FAILED", "cause": type(exc).__name__,
                                            "public_submit_actions": 0}
            from live_contentops.event_timestamp_v1 import maintain_timestamps
            try:
                proof = maintain_timestamps()
                result["event_timestamp"] = {k: proof.get(k) for k in
                    ("status", "event_id", "proof_sha256", "bitcoin_verified", "cause") if k in proof}
            except (OSError, ValueError) as exc:
                result["event_timestamp"] = {"status": "STAMP_ERROR", "cause": type(exc).__name__}
            from live_contentops.event_pack_v1 import run_due_packs
            result["event_packs"] = run_due_packs(store, publish=args.publish)
            # pythonw has no stdout: each run's status, the export's age and any refusal go to the run record.
            try:
                result["run_record"] = str(posts.record_run(result, args.store.parent / posts.RUN_RECORD_FOLDER))
            except OSError as exc:
                result["run_record_error"] = type(exc).__name__
    if sys.stdout is not None:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=1) + "\n")
    return 0 if result["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
