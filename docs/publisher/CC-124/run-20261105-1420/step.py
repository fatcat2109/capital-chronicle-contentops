"""Run one explicit existing CLI step and retain its bounded result for CC-124."""
from pathlib import Path
import json
import subprocess
import sys

root = Path(__file__).resolve().parent
binding = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-d\binding.json")
label, command, *extra = sys.argv[1:]
if command.startswith("publication-"):
    extra = ["--rollout", "config/native_desktop_rollout_v1.json",
             "--native-invocation-id", "/root", *extra]
result = subprocess.run(
    [sys.executable, "-X", "utf8", "scripts/run_native_desktop_editorial.py", command,
     "--binding", str(binding), *extra],
    capture_output=True, encoding="utf-8", errors="replace",
)
(root / (label + ".json")).write_text(result.stdout, encoding="utf-8")
(root / (label + ".stderr.txt")).write_text(result.stderr, encoding="utf-8")
try:
    value = json.loads(result.stdout)
    if value.get("classification") == "TOOL_OUTPUT_IN_FILE":
        raw = Path(value["output"]["path"]).read_bytes()
        (root / (label + "-expanded.json")).write_bytes(raw)
        value = json.loads(raw)
    keys = ("classification", "stage", "blocker", "error", "request_path", "request_sha256",
            "filter_progress", "binding_path", "status", "article_identity",
            "review_id", "next_action", "result", "native_tool_request")
    for key in keys:
        if key in value:
            print(key, json.dumps(value[key], ensure_ascii=True)[:4800])
    calls = value.get("next_native_calls") or ([value["next_native_call"]] if value.get("next_native_call") else [])
    for call in calls:
        args = call.get("arguments", {})
        print("next_native_call", json.dumps({
            "tool": call.get("tool"), "task_name": args.get("task_name"),
            "model": args.get("model"), "effort": args.get("reasoning_effort"),
            "native_stage": call.get("native_stage"), "result_path": call.get("result_path"),
        }, ensure_ascii=True))
    publication = value.get("publication") or value
    if publication.get("destinations") or publication.get("pending_requests"):
        print("publication", json.dumps({
            **{k: publication[k] for k in ("state", "canonical_url", "unknown_write_count") if k in publication},
            "destinations": [{k: d.get(k) for k in ("destination", "status", "reconciliation_status", "public_object_url")}
                             for d in publication.get("destinations", [])],
            "pending": [{"destination": p["request"].get("destination"), "action": p["request"].get("action"),
                         "request_sha256": p["request"]["request_sha256"],
                         "tool_request_sha256": p.get("tool_request_sha256")}
                        for p in publication.get("pending_requests", [])],
        }, ensure_ascii=True))
    print("saved", str(root / (label + ".json")), "keys", list(value))
except (ValueError, KeyError):
    print("CLI output was not JSON; inspect saved output and stderr.")
if result.stderr:
    print("stderr", result.stderr[-1800:])
sys.exit(result.returncode)
