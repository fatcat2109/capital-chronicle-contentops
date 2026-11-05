"""Compact references to the actual CC-216 native results; never image bytes."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import native_review_revision

BASE = Path("A:/Capital Chronicle/Runtime/ContentOps/daily_app_outputs/owner-manual")
HERE = Path(__file__).resolve().parent


def file_record(path):
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path.read_bytes()).hexdigest()}


def main():
    store = ContentOpsDurableStore(
        "A:/Capital Chronicle/Runtime/ContentOps/contentops_daily_app_v1.sqlite3", auto_migrate=False)
    readback = json.loads((HERE / "reviewed-background-readback.json").read_bytes())
    results = {}
    for name in ("nfp", "cpi", "ppi"):
        root = BASE / ("cc216-" + name + "-background-20261105-v1")
        final = json.loads(store.get_outbox_message("cc-editorial-final-" + sha256_of(root.name))["payload"])
        review = json.loads((HERE / (name + "-background-review-result.json")).read_bytes())
        assert review["decision"] == "KEEP" and review["package_revision"] == native_review_revision(final)
        assert readback[name]["article_revision"] == review["package_revision"]
        reference = review["final_visual_review"]
        stage = reference["stage"]
        response = root / ("desktop_response_" + stage + ".json")
        actual = json.loads(response.read_bytes())
        assert actual["output"]["decision"] == "ACCEPT"
        request = json.loads((root / ("desktop_request_" + stage + ".json")).read_bytes())
        assert request["request_sha256"] == actual["request_sha256"]
        binding = request["governed_input"]["binding"]
        roles = []
        for path in sorted(root.glob("desktop_response_*.json")):
            value = json.loads(path.read_bytes())
            observation = value["invocation_observation"]
            roles.append({**file_record(path), "request_sha256": value["request_sha256"],
                "invocation_observation": observation})
        results[name] = {**readback[name], "background_review": file_record(HERE / (name + "-background-review-result.json")),
            "accepted_final_response": file_record(response), "final_visual_request_sha256": actual["request_sha256"],
            "accepted_render_count": len(binding["renders"]), "derivative_package_count": len(final["previews"]),
            "media_assets": [{"asset_id": a["asset_id"], **file_record(Path(a["path"]))} for a in final["media_assets"]],
            "actual_writer_invocation": actual["invocation_observation"]["invocation_id"], "native_returns": roles}
        assert results[name]["accepted_render_count"] == 18 and results[name]["derivative_package_count"] == 8
    evidence = {"recorded_at_utc": datetime.now(timezone.utc).isoformat(), "backgrounds": results,
        "public_write_performed": False, "schedule_changed": False,
        "remaining_owner": "CC-107", "remaining_cause": "FROZEN_EVENT_DOSSIERS_NOT_YET_CREATED",
        "earliest_existing_backlog_restart": "2026-11-06T11:00:00Z",
        "capture_metadata_correction": {"ppi": {"actual_neo_page_id": 417,
            "initial_binding_page_id": 413, "note": "Metadata correction; exact saved PNG/HTML hashes remain unchanged."}}}
    output = HERE / "background-completion-evidence.json"
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"path": str(output), "sha256": sha256(output.read_bytes()).hexdigest(),
        "accepted_backgrounds": len(results), "accepted_renders": 54, "derivative_previews": 24,
        "public_write_performed": False}))


if __name__ == "__main__":
    main()
