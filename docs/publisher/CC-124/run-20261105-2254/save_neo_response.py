"""Bind an actual saved Neo observation to the existing coordinator request."""
import json
from pathlib import Path
import sys

begin_path, observation_path, output_path = map(Path, sys.argv[1:])
begin = json.loads(begin_path.read_bytes())
if begin.get("classification") == "TOOL_OUTPUT_IN_FILE":
    begin = json.loads(Path(begin["output"]["path"]).read_bytes())
observation = json.loads(observation_path.read_bytes())
assert observation.get("observation_source") and observation.get("observed_at_utc")
value = {"tool_request_sha256": begin["tool_request_sha256"],
    "tool_observation": {"surface": "CODEX_EXEC", "tool_name": begin["required_tool"],
        "native_invocation_id": "/root", "observed_at_utc": observation["observed_at_utc"],
        "observation_source": observation["observation_source"]},
    "result": {"request_sha256": begin["request"]["request_sha256"],
        **{k: v for k, v in observation.items()
           if k not in {"request_sha256", "observed_at_utc", "observation_source", "dispatched_at_utc", "composed"}}}}
if observation.get("dispatched_at_utc"):
    value["tool_observation"]["dispatched_at_utc"] = observation["dispatched_at_utc"]
if observation.get("composed"):
    value["composed"] = observation["composed"]
output_path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
print(json.dumps({"response_path": str(output_path), "request_sha256": value["result"]["request_sha256"],
    "status": value["result"].get("status"), "public_write_performed": value["result"].get("public_write_performed")}))
