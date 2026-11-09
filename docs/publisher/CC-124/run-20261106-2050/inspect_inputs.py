"""Read current CC-124 inputs; preserve private originals and existing owners."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import json
import sqlite3
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
EVENT = Path(r"A:\Capital Chronicle\ResearchRuns\claude-main-events-20261029")
STORE = Path(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3")
now = datetime.now(timezone.utc).isoformat()
files = [EVENT / "20261106-1320-arrival-nfp/RESULT.md",
         EVENT / "20261106-1320-arrival-nfp/run.json",
         EVENT / "20261106-0930-dossier-nfp/DOSSIER.md"]
with sqlite3.connect(STORE.as_uri() + "?mode=ro", uri=True) as conn:
    conn.row_factory = sqlite3.Row
    leases = [dict(r) for r in conn.execute(
        "SELECT lease_key,owner_ref,acquired_at,expires_at FROM leases "
        "WHERE status='ACTIVE' AND expires_at>?", (now,))]
record = {
    "item": "CC-124", "observed_at_utc": now,
    "operation_id": "cc124-nfp-arrival-review-20261106-v1",
    "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
    "remote_default_commit": subprocess.check_output(["git", "rev-parse", "origin/master"], cwd=REPO, text=True).strip(),
    "base_reason": "Current Publisher operating HEAD includes origin/master and integrated live consumers.",
    "configured_model": "gpt-6.1-sol", "configured_effort": "max",
    "configuration_status": "CONFIGURED_NOT_OBSERVED",
    "configuration_source": "Active codex exec launch arguments read back through Win32_Process; runtime model telemetry unavailable.",
    "active_leases": leases,
    "sources": [{"path": str(p), "sha256": sha256(p.read_bytes()).hexdigest()} for p in files],
    "inherited_files_sha256": {p: sha256((REPO / p).read_bytes()).hexdigest() for p in (
        "docs/automation/V6_LIVE_TELEMETRY/live_telemetry_registry_v6.jsonl",
        "docs/automation/V6_PUBLIC_DISPATCH_FREEZE/public_dispatch_duplicate_ledger_v6.jsonl")},
    "test_window": "No test run 18:30-22:30 GMT+7 on 6 November; use actual product validators and readbacks.",
}
(HERE / "main-input-check.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
request = {
    "operation_id": record["operation_id"], "stage": "main-report-source-preparation",
    "sources": record["sources"], "role": {"model": "gpt-6.1-sol", "effort": "low"},
    "source_root": str(HERE / "source"), "result_path": str(HERE / "source-preparation-result.json"),
    "known_at_utc": "2026-11-06T13:34:06Z",
    "previous_article": str(REPO / "docs/publisher/CC-107/run-20261106/article-draft.md"),
    "requirements": [
        "Prepare exact Main-report excerpts through main_report_projection_source_v1.verify_projection. Use prior CC-107 nfp-review-held-arrival.json source_spec and add useful bounded qualitative mechanism/countercase excerpts from DOSSIER.md. Preserve exact source bytes and fragment offsets; do not paraphrase source spans.",
        "Create source/index.json with contentops.retained_source_research.v1 and one CAPITAL_CHRONICLE_MAIN_REPORT_PROJECTION record, authority_ref JIM_DECISION_89, headline_id cc124-nfp-arrival-review-20261106, urn source_url, exact known_at and actual revision_at. Explain outcome +165K payrolls and unemployment 4.1%, while Main's pre-event strong condition held. Exclude private execution/account identifiers, entry/stop/target/size, raw third-party prices/tables, uncalibrated numerical probabilities and private consensus rows. No market reaction or fill/performance claim without evidence. Main report is attributed analysis; use report truth semantics.",
        "Create source-claim-trace.json plus result path with actual native task identity, configured model/effort labelled CONFIGURED_NOT_OBSERVED, paths/hashes, novelty, limits and chart/data requirements. Review source spans with existing verifier. No public copy, commits, tests, browser, source fetching, code edits outside this run folder, publication or chat messages.",
        "The parent handles official supporting history and components separately, then invokes the native selection request; do not require new Main work or a full first-day reaction timeline to use held release facts. Public times ET; records UTC."
    ]
}
raw = json.dumps(request, indent=2).encode()
(HERE / "source-preparation-request.json").write_bytes(raw + b"\n")
print(json.dumps({"active_leases": leases, "source_request_path": str(HERE / "source-preparation-request.json"),
                  "source_request_sha256": sha256(raw + b"\n").hexdigest(), "base": record["base_commit"]}))
