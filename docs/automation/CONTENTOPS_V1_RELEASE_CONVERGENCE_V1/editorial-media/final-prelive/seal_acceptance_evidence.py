"""Seal observed local acceptance evidence; never execute a model or publisher."""
import hashlib
import json
import subprocess
import tomllib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
BASELINE = "c9dfcdc5eb848114db0ffb4b3ebb69e82871ee03"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO).decode().strip()


def main():
    now = datetime.now(timezone.utc).isoformat()
    workspace = read(ROOT / "renders/workspace.json")
    edition = workspace["owner_edition"]
    assert (edition["ready"], edition["missing"], edition["held"], edition["preview_count"]) == (7, 0, 1, 56)
    inspected = read(ROOT / "renders/inspected-content-sha256.json")
    cases = {
        "v1-media-oil-r1": "../oil",
        "v1-media-ibm-r1": "../ibm",
        "v1-media-meta-r1": "../meta",
        "v1-prelive-tesla-r2": "tesla-r2",
        "v1-prelive-southwest-r2": "southwest-r2",
        "v1-prelive-fed-policy": "policy",
        "v1-prelive-gold-oct23": "gold",
    }
    articles = []
    for item in workspace["native_edition"]:
        run = item["run_id"]
        content = {key: item[key] for key in ("article", "previews", "media_assets")}
        current = digest(json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())
        assert current == inspected[run], (run, "READER_CONTENT_CHANGED_SINCE_INSPECTION")
        assert item["review"]["decision"] == "KEEP"
        publication = item["publication"]
        assert publication["state"] == "PREPARED" and publication["publication_authority"] is False
        assert publication["operation_scope"] == "OWNER_MANUAL_ISOLATED"
        destinations = publication["destinations"]
        assert len(destinations) == 9 and all(d["status"] == "NOT_DISPATCHED" and not d["public_object_url"] for d in destinations)
        assert len(item["previews"]) == 8 and len(item["media_assets"]) == 2
        for asset in item["media_assets"]:
            assert digest(Path(asset["path"]).read_bytes()) == asset["sha256"]
        case = cases[run]
        article = item["article"]
        if not case.startswith("../"):
            (ROOT / case / "article.md").write_text("# " + article["title"] + "\n\n" + article["dek"] + "\n\n" + article["substack_body_markdown"] + "\n", encoding="utf-8")
        articles.append({
            "operation_id": run, "article_identity": item["article_identity"], "title": article["title"],
            "mode": item["mode"], "source_notice": article["source_date_notice"],
            "story_identity": article["story_identity"], "update_chain_identity": article["update_chain_identity"],
            "prior_article_identity": article.get("prior_article_identity"),
            "review_id": item["review"]["review_id"], "decision": "KEEP", "publication_state": "PREPARED",
            "publication_authority": False, "destinations_not_dispatched": len(destinations),
            "native_packages": len(item["previews"]), "inspected_content_sha256": current,
            "evidence_directory": case, "sources": article["public_source_bindings"],
            "media": [{k: a.get(k) for k in ("asset_id", "path", "sha256", "source_page_url", "license_url", "caption", "alt_text")} for a in item["media_assets"]],
        })
    assert {a["operation_id"] for a in articles} == set(cases)
    verification = read(ROOT / "verification-source-hashes.json")
    mismatches = [f for f, expected in verification["files"].items() if digest((REPO / f).read_bytes()) != expected]
    assert not mismatches, ("TESTED_SOURCE_CHANGED", mismatches)
    backend = set()
    for name, expected in verification["tests"].items():
        tree = ET.parse(ROOT / name)
        rows = tree.findall(".//testcase")
        assert len(rows) == expected["cases"] and not tree.findall(".//failure") and not tree.findall(".//error")
        if not name.startswith("ui-"):
            keys = {(t.get("classname"), t.get("name")) for t in rows}
            assert not backend.intersection(keys), "OVERLAPPING_BACKEND_CASES"
            backend.update(keys)
    assert len(backend) == verification["backend_distinct_cases"] == 81 and verification["ui_cases"] == 13
    verification["source_bytes_reverified_at_utc"] = now
    write(ROOT / "verification-source-hashes.json", verification)
    old_host = read(ROOT / "host-boundary-readback.json")
    hosts = []
    for old in old_host["four_automations"]:
        path = Path("C:/Users/bullw/.codex/automations") / old["id"] / "automation.toml"
        raw = path.read_bytes()
        doc = tomllib.loads(raw.decode())
        assert digest(raw) == old["file_sha256"] and doc["status"] == "PAUSED"
        hosts.append({**old, "model": doc["model"], "reasoning_effort": doc["reasoning_effort"], "prompt_sha256": digest(doc["prompt"].encode())})
    pause = Path("A:/Capital Chronicle/Runtime/ContentOps/control/llm_operator_pause.flag")
    assert digest(pause.read_bytes()) == old_host["pause_sha256"]
    write(ROOT / "host-boundary-final-readback.json", {
        **old_host, "observed_at_utc": now, "four_automations": hosts,
        "pause_path": str(pause), "mutations_performed": 0,
    })
    prior = read(ROOT / "preservation.json")
    prior_paths = ["docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal35"] + [
        "docs/automation/CONTENTOPS_V1_RELEASE_CONVERGENCE_V1/editorial-media/" + c for c in ("oil", "ibm", "tesla", "meta", "southwest")]
    # Use the original enumerated preservation scope; exact old artifacts stay unchanged.
    historical = git("ls-files", "--", *prior_paths).splitlines()
    assert len(historical) == prior["tracked_prior_files"] == 430
    assert not git("diff", BASELINE, "--", *prior_paths)
    write(ROOT / "final-reader-content-receipt.json", {
        "observed_at_utc": now, "source": "Actual owner outbox/review/publication projection",
        "all_seven_article_preview_media_objects_equal_inspected_content": True,
        "hash_method": "SHA256 UTF8 json.dumps({article,previews,media_assets}, ensure_ascii=False, sort_keys=True, separators=(',',':'))",
        "content_sha256": inspected, "ready": 7, "required": 7, "missing": 0, "held": 1,
        "previews": 56, "exact_keep_prepared": 7, "destinations_not_dispatched": 63,
        "published": 0, "projection_sha256": digest((ROOT / "renders/workspace.json").read_bytes()),
        "html_sha256": digest((ROOT / "renders/index.html").read_bytes()),
        "review_metadata_refreshed_after_inspection": True,
        "public_write_performed": False,
    })
    write(ROOT / "completion-evidence.json", {
        "schema_version": "contentops.final_prelive_editorial_acceptance_evidence.v1",
        "observed_at_utc": now, "goal": "CONTENTOPS_V1_FINAL_PRELIVE_EDITORIAL_ACCEPTANCE_V1",
        "native_goal_created_at": 1792798166, "local_acceptance": "COMPLETE_FOR_L2_INTERNAL_AUDIT",
        "counts": {"ready": 7, "required": 7, "missing": 0, "held_fx": 1, "photos": 7, "charts_and_data": 7,
                   "native_packages": 56, "keep_prepared": 7, "destinations_not_dispatched": 63, "published": 0,
                   "unchanged_c9_articles": 3, "bounded_c9_copy_revisions": 2, "new_dated_policy_explainer": 1,
                   "new_october23_attributed_news_report": 1},
        "articles": articles, "four_new_changed_native_writer_returns": "frozen-writer-requests.json and per-case native_write_execution.md/native_write_output.json",
        "new_changed_visual_review": "renders/final/visual-review.json", "prior_unchanged_visual_review": "../renders/final/visual-review.json",
        "final_content_equality": "final-reader-content-receipt.json", "five_copy_assessment": "FIVE_ARTICLE_ASSESSMENT.md",
        "six_requirement_matrix": "../COMPLETION_AUDIT.md", "focused_verification": "verification-source-hashes.json",
        "focused_backend_distinct_cases": len(backend), "focused_ui_cases": 13, "typescript_and_vite": "PASS",
        "prior_history": {**prior, "final_scope_unchanged": True, "final_enumerated_paths": len(historical)},
        "host_final_readback": "host-boundary-final-readback.json", "current_audience_context": "audience-context-readback.json",
        "not_proven": ["accepted-master integration", "deployment", "natural calendar execution", "sustained 5-8 useful published articles/day", "live platform UI or current identity/readiness", "SEO ranking", "audience uplift", "publisher parity"],
        "merged": False, "deployed": False, "public_write_performed": False, "production": "PAUSED",
        "four_automations": "PAUSED_BYTE_IDENTICAL", "v2_v3": "OWNER_PAUSED", "release_authority": "NOT_GRANTED",
        "source_pr_graph_proposal_seal": "Owning release-evidence.json and CHECKPOINT.md; no activation inferred",
        "completion_notice": "NOT_SENT_AT_LOCAL_EVIDENCE_SEAL",
    })
    print(json.dumps({"ready": 7, "required": 7, "missing": 0, "held": 1, "packages": 56,
                      "keep_prepared": 7, "not_dispatched": 63, "backend_cases": len(backend), "ui_cases": 13,
                      "content_equality": True, "host_unchanged": True}))


if __name__ == "__main__":
    main()
