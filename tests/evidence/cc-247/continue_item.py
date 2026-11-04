"""Thin CC-247 invocation of the existing bound publication owner, one action."""
from pathlib import Path
import json, sys, os
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.run_native_desktop_editorial import operation

here = Path(__file__).resolve().parent
prefix, command, destination = sys.argv[1:4]
run = "cc124-prepare-20261103-a" if prefix == "cpi" else "cc124-next-article-20261103-b"
root = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual") / run
binding = json.loads((root / "binding.json").read_bytes())
ref_path = here / (prefix + "-review-reference.json")
response = {"destination": destination, "review_reference": json.loads(ref_path.read_bytes())}
request_hash = None
if command in {"publication-tool-begin", "publication-tool-submit"}:
    request_hash = sys.argv[4]
    response = json.loads(Path(sys.argv[5]).read_bytes()) if len(sys.argv) > 5 else None
elif len(sys.argv) > 4:
    response = json.loads(Path(sys.argv[4]).read_bytes())
result = operation(binding, command=command, response=response,
    rollout=json.loads((Path(__file__).resolve().parents[3] / "config/native_desktop_rollout_v1.json").read_bytes()),
    native_invocation_id=os.environ["CODEX_THREAD_ID"], request_hash=request_hash)
out = here / (prefix + "-" + destination + "-" + command + ".json")
out.write_text(json.dumps(result, indent=2), encoding="utf-8")
co = result.get("coordinator_result", result)
pending = (co.get("native_tool_request") or {}).get("request", {})
print(json.dumps({"artifact": str(out), "classification": result.get("classification"),
    "status": co.get("status", co.get("state")), "cause": result.get("cause"),
    "request_sha256": pending.get("request_sha256"), "action": pending.get("action"),
    "public_object_url": co.get("public_object_url")}))
