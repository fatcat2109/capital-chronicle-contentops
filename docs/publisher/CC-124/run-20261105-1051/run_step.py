"""Run one explicit command on CC-124's existing binding and save its actual return."""
from pathlib import Path
import argparse
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
OPERATING = Path(r"A:\Capital Chronicle\ContentOps")
BINDING = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-c\binding.json")
INVOCATION = "01a1a9d5-9a22-73a1-ab8d-6c0e1e84c9ee"

parser = argparse.ArgumentParser()
parser.add_argument("label")
parser.add_argument("command")
args, extra = parser.parse_known_args()
assert args.label.replace("-", "").replace("_", "").isalnum()
common = ["--binding", str(BINDING)]
if args.command.startswith("publication-"):
    common += ["--rollout", "config/native_desktop_rollout_v1.json",
               "--native-invocation-id", INVOCATION]
result = subprocess.run([sys.executable, "-X", "utf8", "scripts/run_native_desktop_editorial.py",
    args.command, *common, *extra], cwd=OPERATING, capture_output=True, text=True, encoding="utf-8")
(ROOT / (args.label + ".json")).write_text(result.stdout, encoding="utf-8")
(ROOT / (args.label + ".stderr.txt")).write_text(result.stderr, encoding="utf-8")
value = json.loads(result.stdout)
if value.get("classification") == "TOOL_OUTPUT_IN_FILE":
    value = json.loads(Path(value["output"]["path"]).read_bytes())
    (ROOT / (args.label + "-expanded.json")).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
publication = value.get("publication") or value
pending = publication.get("pending_requests", [])
summary = {"exit_code": result.returncode, **{key: value[key] for key in (
    "classification", "blocker", "decision", "review_id", "request_sha256", "tool_return_sha256") if key in value},
    **{key: publication[key] for key in ("state", "canonical_url", "canonical_article_real_published",
        "unknown_write_count", "site_publication_confirmed") if key in publication}}
if value.get("request"):
    pending = [value]
summary["pending"] = [{"action": item["request"].get("action"),
    "destination": item["request"].get("destination"),
    "request_sha256": item["request"]["request_sha256"],
    "tool_request_sha256": item.get("tool_request_sha256"),
    "action_claimed": item.get("action_claimed")} for item in pending]
summary["destinations"] = [{key: item.get(key) for key in (
    "destination", "status", "reconciliation_status", "public_object_id", "public_object_url")}
    for item in publication.get("destinations", [])]
print(json.dumps(summary))
sys.exit(result.returncode)
