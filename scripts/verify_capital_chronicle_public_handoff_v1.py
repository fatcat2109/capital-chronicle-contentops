"""Verify an immutable Main public handoff, cold-start admission, then restart replay.

Reads only the fixed public handoff/schema/export Git paths and the configured
public export root. Output and SQLite state are new, isolated proof artifacts.
No model, scheduler, broker, private Main report, or publication call is made.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker
from live_contentops.capital_chronicle_public_manifest_v1 import CONFIG_SCHEMA, MANIFEST_SCHEMAS, PATH, REPOSITORY
from live_contentops.capital_chronicle_report_feed_v1 import MainReportFeed
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.llm_operator_control_v1 import llm_operator_pause_active, operator_pause_path

HANDOFF = "docs/research/analysis_reporting/goal20/COMPATIBILITY_HANDOFF.json"
GOAL21_HANDOFF = "docs/research/analysis_reporting/goal21/COMPATIBILITY_HANDOFF.json"
SCHEMA_PATHS = {
    "schemas/analysis_reporting/CapitalChroniclePublicReportExportManifestV1.schema.json",
    "schemas/analysis_reporting/v1.1/CapitalChroniclePublicReportExportManifestV1.schema.json",
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--producer-checkout", required=True, type=Path)
    parser.add_argument("--producer-commit", required=True)
    parser.add_argument("--goal21", action="store_true", help="Read the explicit public Goal21 multi-asset handoff")
    parser.add_argument("--library-root", type=Path, help="Join existing verified editorial research/packages into this same isolated proof store")
    parser.add_argument("--expected-public-root", type=Path, default=Path("A:/Capital Chronicle/Runtime/MainPublicReports-v1"))
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[0-9a-f]{40}", args.producer_commit):
        parser.error("Exact Main commit required")
    if args.output_dir.exists():
        parser.error("Use a new proof directory; preserve earlier evidence")
    pause_path = operator_pause_path()
    if not llm_operator_pause_active():
        raise ValueError("EXPECTED_EXISTING_LLM_PAUSE_NOT_ACTIVE")
    pause_sha = hashlib.sha256(pause_path.read_bytes()).hexdigest()
    checkout = args.producer_checkout.resolve()
    origin = subprocess.check_output(["git", "-C", str(checkout), "remote", "get-url", "origin"], text=True).strip().removesuffix(".git")
    if origin != REPOSITORY:
        raise ValueError("MAIN_PRODUCER_REMOTE_MISMATCH")

    def read_git(path):
        if path not in {HANDOFF, GOAL21_HANDOFF, *SCHEMA_PATHS} and not path.startswith(("docs/research/analysis_reporting/goal20/compatibility-example", "docs/research/analysis_reporting/goal21/public-handoff/")):
            raise ValueError("MAIN_PRODUCER_PATH_OUTSIDE_PUBLIC_HANDOFF")
        p = PurePosixPath(path)
        if p.is_absolute() or ".." in p.parts or "\\" in path or ":" in path:
            raise ValueError("MAIN_PRODUCER_PATH_INVALID")
        spec = args.producer_commit + ":" + path
        size = int(subprocess.check_output(["git", "-C", str(checkout), "cat-file", "-s", spec]))
        if not 0 < size <= 8 * 1024 * 1024:
            raise ValueError("MAIN_PRODUCER_ARTIFACT_SIZE_INVALID")
        return subprocess.check_output(["git", "-C", str(checkout), "show", spec])

    handoff_raw = read_git(GOAL21_HANDOFF if args.goal21 else HANDOFF)
    handoff = json.loads(handoff_raw)
    if args.goal21:
        if (handoff.get("schema") != "CapitalChronicleGoal21ImmutableMultiAssetHandoffV1"
                or handoff.get("internal_native_bytes_in_package") is not False
                or handoff.get("private_fields_found") is not False
                or handoff.get("publications") != 0):
            raise ValueError("MAIN_GOAL21_PUBLIC_HANDOFF_INVALID")
        subprocess.check_call(["git", "-C", str(checkout), "merge-base", "--is-ancestor", handoff["producer_source_commit"], args.producer_commit])
        table = handoff["files"]
        if not isinstance(table, list) or not 1 <= len(table) <= 1024 or len({f["path"] for f in table}) != len(table):
            raise ValueError("MAIN_GOAL21_PUBLIC_FILES_INVALID")
        handoff = {**handoff, "schema": "CapitalChronicleGoal20PublicReportManifestCompatibilityHandoffV1",
            "private_account_export_allowed": False, "publication_authority": False,
            "manifest_schema": "schemas/analysis_reporting/v1.1/CapitalChroniclePublicReportExportManifestV1.schema.json",
            "manifest_schema_bytes_sha256": MANIFEST_SCHEMAS["1.1.0"][1],
            "configured_export_root": str(args.expected_public_root),
            "public_export_root_id": "capital-chronicle-public-analysis-reports-v1",
            "example_root": "docs/research/analysis_reporting/goal21/public-handoff",
            "example_bytes_sha256": {f["path"]: f["bytes_sha256"] for f in table}}
    if (handoff.get("schema") != "CapitalChronicleGoal20PublicReportManifestCompatibilityHandoffV1"
            or handoff.get("private_account_export_allowed") is not False
            or handoff.get("publication_authority") is not False
            or handoff.get("manifest_schema") not in SCHEMA_PATHS):
        raise ValueError("MAIN_PRODUCER_HANDOFF_INVALID")
    schema_raw = read_git(handoff["manifest_schema"])
    version = json.loads(schema_raw)["properties"]["version"]["const"]
    digest = hashlib.sha256(schema_raw).hexdigest()
    if (version not in MANIFEST_SCHEMAS or digest != MANIFEST_SCHEMAS[version][1]
            or digest != handoff["manifest_schema_bytes_sha256"]):
        raise ValueError("MAIN_MANIFEST_SCHEMA_HANDOFF_MISMATCH")
    export_root = Path(handoff["configured_export_root"])
    if not export_root.is_absolute():
        raise ValueError("MAIN_PUBLIC_ROOT_NOT_ABSOLUTE")
    export_root = export_root.resolve()
    if export_root != args.expected_public_root.resolve():
        raise ValueError("MAIN_PUBLIC_ROOT_DIFFERS_FROM_EXPLICIT_PROOF_BINDING")
    files = handoff["example_bytes_sha256"]
    if not isinstance(files, dict) or not 1 <= len(files) <= 1024:
        raise ValueError("MAIN_PUBLIC_EXAMPLE_FILE_BOUND")
    retained = {}
    for relative, digest in files.items():
        if relative != "latest-manifest.json" and not PATH.fullmatch(relative):
            raise ValueError("MAIN_EXAMPLE_PATH_OUTSIDE_EXPORT_CONTRACT")
        raw = read_git(handoff["example_root"] + "/" + relative)
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError("MAIN_EXAMPLE_GIT_BYTES_MISMATCH")
        live = (export_root / relative).resolve()
        if not live.is_relative_to(export_root) or live.stat().st_size > 8 * 1024 * 1024:
            raise ValueError("MAIN_CONFIGURED_PUBLIC_ARTIFACT_PATH_OR_SIZE_INVALID")
        if live.read_bytes() != raw:
            raise ValueError("MAIN_CONFIGURED_PUBLIC_ARTIFACT_DIFFERS_FROM_HANDOFF:" + relative)
        retained[relative] = raw
    args.output_dir.mkdir(parents=True)
    public = args.output_dir / "public-export"
    for relative, raw in retained.items():
        target = public / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (args.output_dir / "producer-handoff.json").write_bytes(handoff_raw)
    (args.output_dir / "producer-manifest-schema.json").write_bytes(schema_raw)
    pointer = {"schema_version": CONFIG_SCHEMA, "producer_repository": REPOSITORY,
               "producer_commit": args.producer_commit, "export_root_id": handoff["public_export_root_id"],
               "public_export_root": str(public.resolve())}
    store_path = args.output_dir / "isolated-proof.sqlite3"
    tracker = LatestReportDeliveryTracker(ContentOpsDurableStore(store_path))
    cutoff = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    feed = MainReportFeed(tracker, pointer, headline_paths=[])
    first = feed.poll(cutoff_utc=cutoff)
    before = len(tracker.receipts())
    restarted = MainReportFeed(LatestReportDeliveryTracker(ContentOpsDurableStore(store_path)), pointer, headline_paths=[])
    second = restarted.poll(cutoff_utc=cutoff)
    if args.library_root:
        from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
        from live_contentops.contentops_foundation_library_v1 import persist_library, persist_research_package
        from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection
        research = RetainedSourceResearch(args.library_root / "retained_research")
        briefs = json.loads((args.library_root / "editorial_briefs.json").read_bytes())["briefs"]
        persist_library(restarted.tracker, research, cutoff_utc=cutoff, briefs=briefs)
        for package in json.loads((args.library_root / "integrated/packages.json").read_bytes()):
            persist_research_package(restarted.tracker, package, research_revision=research.revision)
        workspace = report_workspace_projection(restarted.tracker.store.list_outbox_messages())
        (args.output_dir / "workspace.json").write_text(json.dumps(workspace, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    admitted_states = {"ADMITTED", "LINEAGE_ONLY_NOOP", "NO_MATERIAL_CHANGE_NOOP", "INVALIDATION_WITHDRAWAL_NOOP", "CLAIMS_WITHDRAWN"}
    latest = {a: r for r in restarted.pending() for a in r.get("asset_ids", [])}
    declared_latest_match = (not args.goal21 or (
        set(latest) == set(handoff["latest_assets"])
        and all(latest[a]["source_report_sha256"] == row["report_sha256"]
                and latest[a]["report_version"] == row["report_version"]
                for a, row in handoff["latest_reports"].items())))
    pause_unchanged = llm_operator_pause_active() and hashlib.sha256(pause_path.read_bytes()).hexdigest() == pause_sha
    ok = (not first["gaps"] and not second["gaps"] and bool(first["events"])
          and pause_unchanged
          and declared_latest_match
          and any(e["state"] == "ADMITTED" for e in first["events"])
          and all(e["state"] in admitted_states for e in first["events"])
          and second["new_events"] == 0 and len(restarted.tracker.receipts()) == before
          and all(e["state"] in {"DUPLICATE_NOOP", "DUPLICATE_WITHDRAWAL_NOOP"} for e in second["events"]))
    receipt = {"status": "PASS_REAL_IMMUTABLE_COLD_START_AND_RESTART" if ok else "BLOCKED_REAL_HANDOFF_ADMISSION",
               "observed_at_utc": cutoff, "producer_commit": args.producer_commit,
               "producer_handoff_sha256": hashlib.sha256(handoff_raw).hexdigest(),
               "manifest_schema_sha256": hashlib.sha256(schema_raw).hexdigest(),
               "manifest_sha256": first.get("manifest_sha256"),
               "declared_latest_assets_match": declared_latest_match,
               "configured_public_root": str(export_root), "exact_public_files_verified": len(retained),
               "first_scan": first, "restart_scan": second,
               "ancestor_only_events": sum(e["state"] == "LINEAGE_ONLY_NOOP" for e in first["events"]),
               "editorial_ready_events": sum(e["state"] == "ADMITTED" for e in first["events"]),
               "receipt_count_before_restart": before, "receipt_count_after_restart": len(restarted.tracker.receipts()),
               "admitted_receipts": [{k: r.get(k) for k in (
                   "report_id", "report_version", "source_report_sha256", "parent_report_sha256",
                   "known_at_cutoff_utc", "status", "lineage_only", "delivery_status")}
                   for r in restarted.tracker.receipts()],
               "pending_editorial_reports": [{"report_id": r["report_id"], "report_version": r["report_version"]} for r in restarted.pending()],
               "latest_assets": sorted({a for r in restarted.pending() for a in r.get("asset_ids", [])}),
               "joined_library": ({"counts": workspace["foundation_library"]["counts"],
                    "input_composition": workspace["foundation_library"]["input_composition"],
                    "main_reports": workspace["foundation_library"]["main_reports"]} if args.library_root else None),
               "fresh_model_calls": 0, "private_main_paths_read": False, "public_writes": 0,
               "llm_pause_active_and_unchanged": pause_unchanged, "llm_pause_marker_sha256": pause_sha,
               "runtime_started": False, "schedule_started": False}
    (args.output_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
