"""Resume an exact existing digest through its installed publication owner."""
import argparse
import json
from pathlib import Path
import sys

LIVE = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(LIVE))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.substack_daily_digest_v1 import packets, continue_daily_digest, digest_status

p = argparse.ArgumentParser()
p.add_argument("day")
p.add_argument("command", choices=("status", "resume", "begin", "submit"))
p.add_argument("--invocation", required=True)
p.add_argument("--request")
p.add_argument("--response", type=Path)
p.add_argument("--output", type=Path, required=True)
a = p.parse_args()
rollout = json.loads((LIVE / "config/native_desktop_rollout_v1.json").read_bytes())
store = ContentOpsDurableStore(rollout["store_path"], auto_migrate=False)
packet = next(p for p in packets(store) if p["digest_id"] == "cc143-digest-" + a.day)
result = digest_status(store, packet) if a.command == "status" else continue_daily_digest(
    store, packet, output_dir=Path(rollout["editorial_output_root"]) / "owner-manual" / packet["digest_id"] / "native-tools",
    invocation_id=a.invocation, rollout=rollout, command=a.command,
    request_hash=a.request, response=json.loads(a.response.read_bytes()) if a.response else None)
a.output.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
pending = ([result["native_tool_request"]] if result.get("native_tool_request") else result.get("pending_requests", []))
print(json.dumps({"output":str(a.output), **{k:v for k,v in result.items() if k in ("state","confirmed","web_confirmed","email_confirmed","public_object_id","status")},
    "pending":[{"action":r["request"]["action"],"request":r["request"]["request_sha256"],"tool_request":r["tool_request_sha256"]} for r in pending]}))
