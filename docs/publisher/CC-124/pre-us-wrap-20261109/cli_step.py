"""One foreground call to the existing CLI, with bounded evidence output."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
BINDING = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-pre-us-wrap-20261109-v1\binding.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("command")
    args, extra = parser.parse_known_args()
    assert all(c.isalnum() or c in "-_" for c in args.name)
    command = [sys.executable, str(LIVE / "scripts/run_native_desktop_editorial.py"), args.command,
               "--binding", str(BINDING), *extra]
    if args.command.startswith("publication-") and "--rollout" not in extra:
        command += ["--rollout", str(LIVE / "config/native_desktop_rollout_v1.json")]
    if args.command.startswith("publication-") and "--native-invocation-id" not in extra:
        command += ["--native-invocation-id", "/root"]
    raw = HERE / (args.name + "-raw.json")
    expanded = HERE / (args.name + ".json")
    assert not raw.exists(), "A recorded CLI step must not be repeated under the same name."
    done = subprocess.run(command, cwd=LIVE, capture_output=True,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    raw.write_bytes(done.stdout)
    if done.stderr:
        (HERE / (args.name + "-stderr.txt")).write_bytes(done.stderr)
    value = json.loads(done.stdout)
    if value.get("classification") == "TOOL_OUTPUT_IN_FILE":
        data = Path(value["output"]["path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == value["output"]["sha256"]
        value = json.loads(data)
    expanded.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    simple = {k: v for k, v in value.items() if k in (
        "classification", "stage", "request_path", "request_sha256", "blocker", "error",
        "cause", "article_identity", "review_id", "prepared", "qualified_article_count",
        "canonical_url", "canonical_confirmed", "publication_status", "status",
        "next_action", "next_operation", "asset_count", "tool_request_sha256")}
    simple["keys"] = list(value)
    calls = value.get("next_native_calls") or ([value["next_native_call"]] if value.get("next_native_call") else [])
    simple["native_calls"] = [{"tool": c.get("tool"), "stage": c.get("native_stage"),
        "arguments": {k: v for k, v in c.get("arguments", {}).items() if k != "message"},
        "result_path": c.get("result_path")} for c in calls]
    for key in ("request", "pending_request", "pending_native_tool_requests"):
        pending = value.get(key)
        if pending:
            rows = pending if isinstance(pending, list) else [pending]
            simple[key] = [{k: p.get(k) for k in ("request_sha256", "action", "destination", "public_object_url", "status")}
                           for p in rows if isinstance(p, dict)]
    print(json.dumps(simple, ensure_ascii=True))
    return done.returncode


if __name__ == "__main__":
    raise SystemExit(main())
