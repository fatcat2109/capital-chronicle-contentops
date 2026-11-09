"""Save this item's exact existing-CLI result and print bounded continuation details."""
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
label, command, *arguments = sys.argv[1:]
common = ["--binding", r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc107-nfp-preview-20261106-v1\binding.json",
    "--rollout", "config/native_desktop_rollout_v1.json", "--native-invocation-id", "01a1b092-b78e-7203-aeb6-664d04f8765a"]
result = subprocess.run([sys.executable, "scripts/run_native_desktop_editorial.py", command, *common, *arguments],
    cwd=ROOT, capture_output=True)
(HERE / (label + ".json")).write_bytes(result.stdout)
if result.stderr:
    (HERE / (label + ".stderr.txt")).write_bytes(result.stderr)
value = json.loads(result.stdout)
while value.get("classification") == "TOOL_OUTPUT_IN_FILE":
    value = json.loads(Path(value["output"]["path"]).read_bytes())
(HERE / (label + "-expanded.json")).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
publication = value.get("publication", value)
coordinator = value.get("coordinator_result") or {}
pending = publication.get("pending_requests", [])
if coordinator.get("native_tool_request"):
    pending = [coordinator["native_tool_request"], *pending]
print(json.dumps({"exit_code": result.returncode, "classification": value.get("classification"),
    "blocker": value.get("blocker"), "state": publication.get("state"),
    "pending": [{k: p.get("request", p).get(k) for k in ["destination", "action", "request_sha256"]} for p in pending],
    "destinations": [{k: d.get(k) for k in ["destination", "status", "public_object_url", "blocker"]}
                     for d in publication.get("destinations", [])]}))
sys.exit(result.returncode)
