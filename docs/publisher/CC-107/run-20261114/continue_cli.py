"""Capture one exact continuation of CC-107's existing native operation."""
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
label, command, *extra = sys.argv[1:]
binding = Path(r"C:\Users\bullw\AppData\Local\CapitalChronicle\ContentOps\editorial-previews\cc107-nfp-dated-review-20261114-v1\binding.json")
args = [sys.executable, "-B", "scripts/run_native_desktop_editorial.py", command,
        "--binding", str(binding), *extra]
result = subprocess.run(args, cwd=ROOT, capture_output=True)
(HERE / (label + ".json")).write_bytes(result.stdout)
if result.stderr:
    (HERE / (label + ".stderr.txt")).write_bytes(result.stderr)
value = json.loads(result.stdout)
while value.get("classification") == "TOOL_OUTPUT_IN_FILE":
    value = json.loads(Path(value["output"]["path"]).read_bytes())
(HERE / (label + "-expanded.json")).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"exit_code": result.returncode, "classification": value.get("classification"),
    "blocker": value.get("blocker"), "stage": value.get("stage"), "request_path": value.get("request_path"),
    "request_sha256": value.get("request_sha256"), "next_native_call": value.get("next_native_call"),
    "qualified_article_count": value.get("qualified_article_count"),
    "keys": list(value)}, ensure_ascii=False))
sys.exit(result.returncode)
