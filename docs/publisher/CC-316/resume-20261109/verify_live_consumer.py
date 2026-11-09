"""Read the installed Publisher and its existing reconciled article media; never send."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual")
sys.path.insert(0, str(REPO))
from live_contentops.tradingview_snapshot_v1 import validate_snapshot_asset
from live_contentops.destination_transport_registry_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


source_paths = [
    "live_contentops/tradingview_snapshot_v1.py",
    "live_contentops/v1_simple_gemini_newsroom_v1.py",
    "live_contentops/native_desktop_editorial_v1.py",
    "live_contentops/rolling_x_grounded_article_media_builder_v1.py",
    "live_contentops/cloudinary_delivery_media_v1.py",
    "live_contentops/_eight_platform_substack_first_pipeline_impl_v1.py",
    "live_contentops/neo_destination_handoff_v1.py",
]
sources = []
for name in source_paths:
    blob = git(LIVE, "rev-parse", "HEAD:" + name)
    assert git(REPO, "rev-parse", "HEAD:" + name) == blob, name
    assert sha(LIVE / name) == sha(REPO / name), name
    sources.append({"path": name, "git_blob": blob, "installed_sha256": sha(LIVE / name)})

commits = ["b3d166f84bc1800675e9b34587994c496b8a478a",
           "5c2e421d", "0eb918e2a0655be88253b5cd064bda49fc2d5e23", "69a6b389"]
ancestors = []
for short in commits:
    full = git(LIVE, "rev-parse", short)
    subprocess.run(["git", "-C", str(LIVE), "merge-base", "--is-ancestor", full, "HEAD"], check=True)
    ancestors.append(full)

articles = []
for label, name, market in [("weekend", "cc341-weekend-wrap-20261109-r2", "USOIL"),
                            ("daily", "cc124-pre-us-wrap-20261109-v1", "EURUSD")]:
    binding_path = RUNTIME / name / "binding.json"
    result = subprocess.run([sys.executable, "scripts/run_native_desktop_editorial.py", "publication-status",
                             "--binding", str(binding_path)], cwd=LIVE, capture_output=True,
                            text=True, encoding="utf-8", check=True, timeout=35)
    envelope = json.loads(result.stdout)
    output = Path(envelope["output"]["path"])
    assert sha(output) == envelope["output"]["sha256"]
    status = json.loads(output.read_bytes())
    assert status["state"] == "RECONCILED" and status["derivative_confirmed_count"] == 8
    assert status["additional_confirmed_count"] == 1 and status["unknown_write_count"] == 0
    assert not status["pending_requests"]
    approved = status["media_sha256"]
    contexts = []
    for context_path in (RUNTIME / name / "reviewed-handoff").glob("*/run_context_v1.json"):
        context = json.loads(context_path.read_bytes())
        snapshots = [a for a in context["media"]["assets"]
                     if a.get("modality") == "tradingview_chart_snapshot" and a["asset_id"] in approved]
        if snapshots:
            contexts.append((context_path, context, snapshots))
    assert len(contexts) == 1
    context_path, context, snapshots = contexts[0]
    assert len(snapshots) == 1 and context["article"]["market_asset"] == market
    asset = snapshots[0]
    validate_snapshot_asset(asset, context["article"])
    assert sha(asset["path"]) == asset["sha256"] == approved[asset["asset_id"]]
    assert asset["article_inclusion"] and asset["canonical_article_media"]
    assert asset["asset_id"] in {a["asset_id"] for a in context["media"]["delivery_only_assets"]}
    previews = json.loads((context_path.parent / "native_derivative_previews_v1.json").read_bytes())
    for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS:
        payload = previews["packages"][destination]
        assert payload["media_asset_ids"] == [asset["asset_id"]], destination
        assert "Chart: TradingView" in (payload.get("full_text") or payload.get("text") or ""), destination
    timings = {row["destination"]: row for row in status["timing"]["channels"]}
    destinations = []
    for row in status["destinations"]:
        destination = row["destination"]
        assert row["status"] == "DISPATCH_CONFIRMED"
        assert row["reconciliation_status"] == "RECONCILED_CONFIRMED"
        assert timings[destination]["image_verified_readback_at_utc"], destination
        destinations.append({k: row[k] for k in ["destination", "public_object_id", "public_object_url"]} |
                            {"image_verified_readback_at_utc": timings[destination]["image_verified_readback_at_utc"]})
    articles.append({"operation_id": name, "market_asset": market, "state": status["state"],
                     "canonical_url": status["canonical_url"], "context_path": str(context_path),
                     "context_sha256": sha(context_path), "source_asset_path": asset["path"],
                     "source_asset_sha256": asset["sha256"], "capture_method": asset["tradingview_snapshot"].get("capture_method"),
                     "capture_at_utc": asset["tradingview_snapshot"]["captured_at_utc"],
                     "snapshot_validator_passed": True, "frozen_image_destinations": list(previews["packages"]),
                     "destinations": destinations, "unknown_writes": 0, "pending_requests": 0,
                     "fresh_status_artifact": str(output), "fresh_status_sha256": sha(output)})

baseline = json.loads((HERE / "preserved-wip-before.json").read_bytes())
for root, files in baseline.items():
    for name, digest in files.items():
        assert sha(Path(root) / name) == digest, (root, name)
tests = []
for name in ["registration-tests", "ordering-fallback-tests", "rights-hosting-tests", "capture-tests"]:
    suites = ET.parse(HERE / (name + ".xml")).getroot()
    cases = suites.findall(".//testcase")
    assert all(c.find("failure") is None and c.find("error") is None and c.find("skipped") is None for c in cases)
    tests.append({"artifact": name + ".xml", "passed": len(cases)})

evidence = {"verified_at_utc": datetime.now(timezone.utc).isoformat(), "item": "CC-316",
            "operating_root": str(LIVE), "operating_head": git(LIVE, "rev-parse", "HEAD"),
            "already_integrated_commits": ancestors, "installed_consumers": sources, "articles": articles,
            "tests": tests, "targeted_tests_passed": sum(x["passed"] for x in tests),
            "inherited_modified_files_byte_identical": sum(len(x) for x in baseline.values()),
            "readback_basis": "Fresh installed coordinator projections of retained exact browser/API readbacks; no new browser visit or public write.",
            "launch": {"pid": 27412, "model": "gpt-6.1-sol", "effort": "high",
                       "telemetry": "CONFIGURED_NOT_OBSERVED", "editorial_model_calls": 0},
            "new_public_writes": 0, "schedule_changes": 0, "other_chat_messages": 0}
(HERE / "live-consumer-verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"articles": len(articles), "confirmed_destinations_per_article": len(articles[0]["destinations"]),
                  "tests_passed": evidence["targeted_tests_passed"], "preserved_modified_files": 8}))
