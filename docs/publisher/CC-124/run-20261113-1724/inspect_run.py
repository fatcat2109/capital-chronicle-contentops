"""One CC-124 assessment through installed source, clock and count consumers."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BUILDER = HERE.parents[3]
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
RESEARCH = Path(r"A:\Capital Chronicle\ResearchRuns")
MAIN = RESEARCH / "claude-main-research"
TOWER = Path(r"A:\Capital Chronicle\control-tower-reporting-closeout-20261018\docs\project_control_tower")
PREVIOUS = HERE.parent / "run-20261113-1256/source-assessment.json"
sys.path.insert(0, str(LIVE))

from live_contentops.main_report_projection_source_v1 import verify_projection
from live_contentops.plan_status_posts_v1 import read_export
from live_contentops.published_images_v1 import PublishedImages, daily_limit, day_of
from live_contentops.reader_article_contract_v1 import contract_for, validate_publication_clock


def info(path):
    digest = sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def load(path):
    return json.loads(path.read_bytes())


def save(name, value):
    with (HERE / name).open("w", encoding="utf-8", newline="\n") as output:
        json.dump(value, output, indent=2, ensure_ascii=True)
        output.write("\n")


def clock_check(identity, cutoff):
    contract = contract_for({"source_pack": [{"document_id": identity, "data_cutoff_utc": cutoff}]})
    cause = None
    try:
        validate_publication_clock({"reader_article_contract": contract}, now=now, destination="substack")
    except ValueError as exc:
        cause = str(exc)
    return {"reader_contract": contract, "publication_clock_cause": cause,
            "publication_deadline_utc": (datetime.fromisoformat(cutoff.replace("Z", "+00:00"))
                                         + timedelta(minutes=60)).isoformat() if cutoff else None}


def latest_files(root, limit=3):
    if not root.exists():
        return []
    paths = (p for p in root.rglob("*") if p.is_file() and p.suffix in {".md", ".json", ".txt"}
             and not any(word in p.name.lower() for word in
                         ("secret", "credential", "account", ".env", "claude-response", "prompt")))
    return [info(p) for p in sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True)[:limit]]


now = datetime.now(timezone.utc)
feed = RUNTIME / "published_content_v1.jsonl"
feed_before = info(feed)
preserved = []
for root in (BUILDER, LIVE):
    names = subprocess.check_output(["git", "-C", str(root), "diff", "--name-only"], text=True).splitlines()
    for name in names:
        preserved.append({"root": str(root), "relative_path": name, **info(root / name)})
save("preserved-work.json", preserved)

prior = load(PREVIOUS)
prior_hashes = {row["path"]: row["sha256"] for row in prior["retained_reports"]}
reports = []
for name in ("owner-native.json", "analysis-native.json"):
    for path in MAIN.rglob(name):
        source = info(path)
        capture = path.parent / "capture.json"
        cutoff = load(capture).get("known_at_utc") if capture.exists() else None
        document = load(path)
        canonical_hash = sha256(json.dumps(document, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        synthesis = document.get("native_synthesis", document)
        proof = path.parent / "analysis-end.json"
        accepted = name == "owner-native.json"
        proof_record = None
        if name == "analysis-native.json" and proof.exists():
            end = load(proof)
            accepted = end.get("output_sha256") == canonical_hash and not end.get("schema_errors")
            proof_record = {**info(proof), "completed_at_utc": end.get("completed_at_utc"),
                            "output_hash_matches": end.get("output_sha256") == canonical_hash,
                            "hash_basis": "Main proof hashes canonical JSON; source sha256 hashes exact file bytes.",
                            "canonical_output_sha256": canonical_hash}
        reports.append({**source, "capture_known_at_utc": cutoff, "completed_output": accepted,
                        "acceptance_evidence": proof_record,
                        "changed_from_prior_native_inventory": prior_hashes.get(str(path)) != source["sha256"],
                        "summary_count": len(synthesis.get("summary", [])),
                        "summary_sha256": sha256(json.dumps(synthesis.get("summary", []), sort_keys=True).encode()).hexdigest(),
                        "candidate_count": len(synthesis.get("candidates", [])),
                        **clock_check(str(path), cutoff)})
reports.sort(key=lambda row: row["capture_known_at_utc"] or "", reverse=True)
completed = [r for r in reports if r["completed_output"]]
latest = completed[0]
assert Path(latest["path"]).name == "analysis-native.json", "Assess today's new single-pass output"

# Reuse the existing public-excerpt consumer as well; unchanged prose keeps its clock.
spec = dict(prior["installed_projection"]["spec"])
spec.update(source_url="urn:cc-public-report:cc124-main-20261113-1724",
            headline_id="cc124-main-20261113-1724", revision_at_utc=now.isoformat())
projection = verify_projection(spec)
projection_contract = contract_for({"source_pack": [projection["document"]], "selected_candidate": projection})
t2_path = max((MAIN / "t2-runs").rglob("run.json"), key=lambda p: p.stat().st_mtime)
t2 = load(t2_path)
t2_capture = Path(t2["t2_capture"].get("request") or t2["screen_request"]) / "capture.json"
t2_cutoff = load(t2_capture)["known_at_utc"]
t2_output = t2_path.parent / "t2-output.json"
if t2.get("capture_known_at_utc"):
    assert t2_cutoff == t2["capture_known_at_utc"]
brain_path = max((MAIN / "brain-runs").glob("*/run.json"), key=lambda p: p.stat().st_mtime)
brain = load(brain_path)
additional = []
for root in (MAIN / "horizon-runs", RESEARCH / "claude-main-events-20261029",
             RESEARCH / "claude-main-events-catchup", MAIN / "20261113-ppi",
             Path(r"C:\CapitalChronicleScratch\ResearchRuns\claude-builder-ppi-page-path-20261107"),
             TOWER / "report_upgrade_review_20261105/strategy",
             Path(r"A:\Capital Chronicle\Worktrees\codex-data-backlog\data\research"),
             BUILDER / "data/research", LIVE / "data/research"):
    additional.append({"root": str(root), "exists": root.exists(), "latest_files": latest_files(root)})
searches = []
for name in ("BACKLOG.md", "BACKLOG_ARCHIVE.md"):
    path = TOWER / name
    matches = [i + 1 for i, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines())
               if any(word in line for word in ("CC-124", "CC-403", "post-CPI", "scenario", "Main report"))]
    searches.append({**info(path), "matching_lines": matches})
binding_path = LIVE / "config/native_desktop_operator_main_feed_binding_v1.json"
binding = load(binding_path)
save("source-assessment.json", {"observed_at_utc": now.isoformat(), "previous_assessment": info(PREVIOUS),
     "retained_reports": reports, "latest_completed_analysis": latest,
     "legacy_owner_native_files": sum(Path(r["path"]).name == "owner-native.json" for r in reports),
     "single_pass_analysis_files": sum(Path(r["path"]).name == "analysis-native.json" for r in reports),
     "latest_brain_run": {**info(brain_path), "outcome": brain["outcome"],
                          "started_at_utc": brain.get("started_at_utc"),
                          "finished_at_utc": brain.get("finished_at_utc"), "analysis": brain.get("analysis")},
     "installed_projection": {"spec": spec, "reader_contract": projection_contract,
          "public_passage_sha256": sha256(projection["document"]["canonical_content_text"].encode()).hexdigest()},
     "latest_t2_selection": {"run": info(t2_path), "output": info(t2_output),
          "original_capture": {**info(t2_capture), "known_at_utc": t2_cutoff},
          "thesis_count": len(load(t2_output).get("theses", [])),
          "output_cutoff_utc": load(t2_output).get("cutoff_utc"), "decision_at_utc": t2.get("decision_at_utc"),
          **clock_check("latest-main-t2-ranking", t2_cutoff)},
     "use": "The latest completed single-pass analysis and T2 ranking are used with retained reports and exported plans to assess the due piece. Their original capture clocks exceed CC-403's publication deadline; completion, decision and retrieval do not refresh it.",
     "additional_held_outputs": additional, "backlog_archive_search": searches,
     "configured_public_main_feed": {"binding": info(binding_path), "root": binding["public_export_root"],
                                    "latest_files": latest_files(Path(binding["public_export_root"]))}})

export = read_export()["status"]
latest_registration = max((p.get("registered_at_utc") or "") for p in export["plans"])
register = PublishedImages(RUNTIME / "published_images_v1.jsonl", published_feed=feed)
pieces = sorted(register._daily_pieces(register.records(), now))
with sqlite3.connect((RUNTIME / "contentops_daily_app_v1.sqlite3").as_uri() + "?mode=ro", uri=True) as conn:
    conn.row_factory = sqlite3.Row
    leases = [dict(row) for row in conn.execute("SELECT lease_id,lease_key,status,expires_at FROM leases WHERE status='ACTIVE'")
              if datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00")) > now]
save("installed-consumers.json", {"observed_at_utc": now.isoformat(), "production_day": day_of(now),
     "daily_article_limit": daily_limit(now), "article_slots_in_use": pieces, "active_leases": leases,
     "main_plan_export": {"generated_at_utc": export["generated_at_utc"], "content_hash": export.get("content_hash"),
          "plan_count": len(export["plans"]), "latest_plan_registration_utc": latest_registration},
     "clock_use": "Export generation does not refresh original analysis capture.",
     "operation_allocated": True, "channel_readbacks": "None performed by this run."})

# A newly eligible source means continue editorial work, not a no-article result.
assert all(r["publication_clock_cause"] for r in completed), "Eligible Main analysis requires editorial work"
assert latest["publication_clock_cause"].startswith("ARTICLE_DATA_CUTOFF_EXPIRED:")
assert clock_check("latest-main-t2-ranking", t2_cutoff)["publication_clock_cause"].startswith("ARTICLE_DATA_CUTOFF_EXPIRED:")
verification = {"execution_python": sys.executable, "installed_modules": {name: str(sys.modules[name].__file__) for name in
     ("live_contentops.main_report_projection_source_v1", "live_contentops.reader_article_contract_v1",
      "live_contentops.plan_status_posts_v1", "live_contentops.published_images_v1")},
     "latest_single_pass_analysis_assessed": Path(latest["path"]).name == "analysis-native.json",
     "completed_source_count": len(completed), "eligible_completed_sources": 0,
     "exact_public_excerpt_admitted": True, "validated_plan_export_consumed": True,
     "publication_feed_before": feed_before, "publication_feed_after": info(feed),
     "inherited_work_unchanged": all(info(Path(r["path"]))["sha256"] == r["sha256"] for r in preserved),
     "new_operations": 1, "editorial_model_calls": 2, "public_writes_by_this_run": 0,
     "pytest_processes_started": 0, "chat_messages": 0, "schedule_changes": 0}
verification["publication_feed_unchanged_during_assessment"] = feed_before["sha256"] == verification["publication_feed_after"]["sha256"]
assert verification["inherited_work_unchanged"]
save("verification.json", verification)
save("result.json", {"item": "CC-124", "observed_at_utc": now.isoformat(), "new_articles": 0,
     "first_cause": latest["publication_clock_cause"], "standing_status": "OPEN",
     "choice": "Select the new Main PPI dossier in the existing native operation; retain its exact cutoff and close the pre-writer stage on expiry instead of issuing stale public copy. Decisions 89 and 98 and the root CC-403 deadline apply.",
     "authority": ["JIM_DECISION_89", "JIM_DECISION_93", "JIM_DECISION_98", "ROOT_CC403_READER_ARTICLE_V1"],
     "next_due_gmt7": "13 Nov 2026 18:15 GMT+7",
     "next_due_reason": "Recheck the Main feed at 18:15 GMT+7 before decision 98's 18:30 preview deadline; no host schedule change.",
     "next_action": "Consume any new completed Main analysis at the next standing opportunity. The PPI preview is 13 November's wrap (decision 98).",
     "next_actor": "Codex Publisher; Ops Live owns Main analysis production.",
     "acceptance": "Installed consumers executed successfully. No new publication/readback acceptance claimed."})
print(json.dumps({"latest_data_cutoff_utc": latest["capture_known_at_utc"], "first_cause": latest["publication_clock_cause"],
     "completed_sources": len(completed), "article_slots_used": len(pieces), "active_leases": leases,
     "inherited_work_unchanged": verification["inherited_work_unchanged"], "new_articles": 0}))
