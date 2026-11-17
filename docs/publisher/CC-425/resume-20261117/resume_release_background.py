"""One existing CC-425 release call; survives a disconnected exec transport."""
import faulthandler
import json
import os
from pathlib import Path
import sys
import traceback
from datetime import datetime, timezone

sys.path.insert(0, str(Path.cwd()))
from live_contentops.native_finished_publication_v1 import release_finished_piece

root = Path(__file__).resolve().parent
started = {"pid": os.getpid(), "started_at_utc": datetime.now(timezone.utc).isoformat(),
           "operation": "cc425-cpi-reaction-history-20261111-v1"}
(root / "background-release-start.json").write_text(json.dumps(started, indent=2), encoding="utf-8")
with (root / "background-release-trace.txt").open("w", encoding="utf-8") as trace:
    faulthandler.dump_traceback_later(90, repeat=False, file=trace)
    try:
        result = release_finished_piece(
            r"C:\Users\bullw\AppData\Local\CapitalChronicle\ContentOps\editorial-previews\cc425-cpi-reaction-history-20261111-v1\binding.json",
            json.loads(Path("config/native_desktop_rollout_v1.json").read_bytes()))
    except Exception as exc:
        traceback.print_exc(file=trace)
        result = {"error": type(exc).__name__, "detail": str(exc)}
    faulthandler.cancel_dump_traceback_later()
(root / "background-release-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
summary = {**started, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
           **{k: v for k, v in result.items() if k in {"classification", "binding_path", "error", "detail"}}}
(root / "background-release-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
