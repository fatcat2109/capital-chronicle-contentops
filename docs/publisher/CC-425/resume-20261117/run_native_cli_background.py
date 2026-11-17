"""Run one existing native CLI command, with durable stdout and no console."""
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path.cwd()))
from scripts.run_native_desktop_editorial import main

root = Path(__file__).resolve().parent
command, label = sys.argv[1:3]
started = {"pid": os.getpid(), "command": command,
           "started_at_utc": datetime.now(timezone.utc).isoformat()}
(root / (label + "-start.json")).write_text(json.dumps(started, indent=2), encoding="utf-8")
args = [command, "--binding", r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc425-cpi-reaction-history-20261111-v1\binding.json",
        "--rollout", str(Path.cwd() / "config/native_desktop_rollout_v1.json"),
        "--native-invocation-id", os.environ["CODEX_THREAD_ID"], *sys.argv[3:]]
with (root / (label + ".json")).open("w", encoding="utf-8") as out, (root / (label + ".stderr.txt")).open("w", encoding="utf-8") as err:
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = main(args)
        except SystemExit as exc:
            code = exc.code
        except Exception:
            traceback.print_exc()
            code = 1
(root / (label + "-end.json")).write_text(json.dumps({**started, "exit_code": code,
    "finished_at_utc": datetime.now(timezone.utc).isoformat()}, indent=2), encoding="utf-8")
