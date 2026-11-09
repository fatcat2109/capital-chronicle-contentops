"""Retain bounded CLI evidence for this CC-124 run; the existing CLI owns all work."""
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
label, *arguments = sys.argv[1:]
result = subprocess.run(
    [sys.executable, "scripts/run_native_desktop_editorial.py", *arguments],
    cwd=r"A:\Capital Chronicle\ContentOps", capture_output=True,
)
(HERE / (label + ".json")).write_bytes(result.stdout)
if result.stderr:
    (HERE / (label + ".stderr.txt")).write_bytes(result.stderr)
try:
    payload = json.loads(result.stdout)
    if payload.get("classification") == "TOOL_OUTPUT_IN_FILE":
        payload = json.loads(Path(payload["output"]["path"]).read_bytes())
        (HERE / (label + "-expanded.json")).write_text(
            json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    keys = ("classification", "stage", "blocker", "error", "binding_path",
            "request_path", "request_sha256", "public_write_performed", "filter_progress")
    print(json.dumps({"exit_code": result.returncode,
                      **{k: payload[k] for k in keys if k in payload}}, ensure_ascii=True))
    publication = payload.get("publication") or payload
    if publication.get("state") or publication.get("pending_requests"):
        print(json.dumps({"state": publication.get("state"), "unknown_write_count": publication.get("unknown_write_count"),
            "destinations": [{k: d.get(k) for k in ("destination", "status", "public_object_url", "first_blocking_cause")}
                             for d in publication.get("destinations", [])],
            "pending": [{k: p.get("request", p).get(k) for k in ("destination", "action", "request_sha256")}
                        for p in publication.get("pending_requests", [])]}, ensure_ascii=True))
    for call in payload.get("next_native_calls", []) or [payload.get("next_native_call")]:
        if call:
            print(json.dumps({"tool": call.get("tool"), "native_stage": call.get("native_stage"),
                              "result_path": call.get("result_path")}, ensure_ascii=True))
except (ValueError, KeyError, TypeError) as exc:
    print(json.dumps({"exit_code": result.returncode, "output_path": str(HERE / (label + ".json")),
                      "decode_error": str(exc), "stderr_bytes": len(result.stderr)}))
sys.exit(result.returncode)
