"""Thin CLI invocation/evidence helper for this exact CC-124 run; no transport."""
import json
from pathlib import Path
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261104-a")
label, command, *args = sys.argv[1:]
result = subprocess.run([sys.executable, "-X", "utf8",
    r"A:\Capital Chronicle\ContentOps\scripts\run_native_desktop_editorial.py", command, *args,
    "--binding", str(ROOT / "binding.json"), "--rollout",
    r"A:\Capital Chronicle\ContentOps\config\native_desktop_rollout_v1.json",
    "--native-invocation-id", "01a1a4d5-297b-7a72-bf56-c0af786aba7c"],
    cwd=r"A:\Capital Chronicle\ContentOps", capture_output=True)
(OUT / (label + ".json")).write_bytes(result.stdout)
(OUT / (label + ".stderr.txt")).write_bytes(result.stderr)
if not result.stdout:
    print(result.stderr.decode(errors="replace")[:1800])
    raise SystemExit(result.returncode or 1)
value = json.loads(result.stdout)
found = {}

def inspect(node):
    if isinstance(node, dict):
        if node.get("schema_version") == "contentops.native_neo_tool_request.v1":
            found[node["tool_request_sha256"]] = node
            return
        for child in node.values():
            inspect(child)
    elif isinstance(node, list):
        for child in node:
            inspect(child)

inspect(value)
pending = []
for request in found.values():
    action = request["request"]
    path = OUT / ("next-" + action["destination"] + "-" + action["action"].lower() + ".json")
    path.write_text(json.dumps(request, indent=2), encoding="utf-8")
    pending.append({k: action[k] for k in ("destination", "action", "request_sha256")})
print(json.dumps({"classification": value.get("classification"), "blocker": value.get("blocker"),
    "state": value.get("coordinator_result", {}).get("state"), "next": pending}))
raise SystemExit(result.returncode)
