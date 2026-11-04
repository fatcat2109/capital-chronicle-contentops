"""Save one exact call to the existing newsroom CLI; no alternate runtime."""
import json
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parent
BINDING = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-a\binding.json")
label, command, *rest = sys.argv[1:]
args = [sys.executable, "scripts/run_native_desktop_editorial.py", command, "--binding", str(BINDING), *rest]
p = subprocess.run(args, cwd=r"A:\Capital Chronicle\ContentOps", capture_output=True, text=True, encoding="utf-8")
(ROOT / (label + ".json")).write_text(p.stdout, encoding="utf-8")
(ROOT / (label + ".stderr.txt")).write_text(p.stderr, encoding="utf-8")
try:
    d = json.loads(p.stdout)
    keep = ("classification", "stage", "request_path", "request_sha256", "binding_path", "blocker", "next_source_action", "next_command", "exact_next_blocker", "native_tool_request", "public_write_performed")
    print(json.dumps({k: d[k] for k in keep if k in d}, ensure_ascii=True)[:9000])
    call = d.get("next_native_call")
    if call:
        print(json.dumps(call, ensure_ascii=True)[:10500])
except ValueError:
    print(p.stdout[:1600], p.stderr[:1600])
print("saved", ROOT / (label + ".json"), "exit", p.returncode)
raise SystemExit(p.returncode)
