"""CC-748: one tick of Jim's manual posting desk, in its own Windows task (Ops Product, 23 Nov 2026).

The desk first ran inside the minute posting job, after that job's slow phases, so the job's five-minute limit
could stop a phone push midway (22 Nov 21:12Z: the first pack stopped after its SENDING line). Its own task gives
it its own minute, and a desk failure can never reach posting.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REPORTED = ("status", "cause", "packs", "released", "pushed", "pulls", "overdue")


def main(argv=None):
    from live_contentops.published_content_v1 import PRODUCTION_STORE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=PRODUCTION_STORE)
    args = parser.parse_args(argv)
    try:
        from live_contentops.manual_desk_v1 import minute_hook
        result = minute_hook(args.store, desk_root=args.store.parent / "manual_desk",
                             binding_path=args.store.parent / "control/x_reply_bot_binding.json")
    except Exception as exc:  # a desk failure is reported, never raised
        result = {"status": "DESK_FAILED", "cause": type(exc).__name__, "public_submit_actions": 0}
    result = result if isinstance(result, dict) else {"status": "DESK_RESULT_INVALID"}
    print(json.dumps({key: result[key] for key in REPORTED if key in result}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
