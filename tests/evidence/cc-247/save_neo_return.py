"""Wrap an actual Neo observation in its claimed exact tool return."""
from pathlib import Path
from datetime import datetime, timezone
import os, json, sys
here = Path(__file__).resolve().parent
prefix, destination, observation = sys.argv[1:4]
packet = json.loads((here / (prefix + "-" + destination + "-publication-tool-begin.json")).read_bytes())
result = json.loads(Path(observation).read_bytes())
response = {"tool_request_sha256": packet["tool_request_sha256"], "result": result,
    "tool_observation": {"tool_name": "mcp__browseros_neo__run", "surface": "CODEX_EXEC",
        "native_invocation_id": os.environ["CODEX_THREAD_ID"],
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "observation_source": "Actual BrowserOS Neo return; " + str(Path(observation).resolve())}}
out = here / (prefix + "-" + destination + "-tool-return-" + result["request_sha256"] + ".json")
out.write_text(json.dumps(response, indent=2), encoding="utf-8")
print(out)
