"""CC-306: queue one post per new plan-state change for the six markets (run from an existing tick).

    python scripts/plan_status_posts.py [--export-dir DIR] [--store PATH]

Reads Main's plan-status export and registers one READY_FOR_PUBLISHER outbox row per new
transition in the ContentOps store. Repeats change nothing. No public write here: Codex
Publisher posts each row through the existing publication path.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore  # noqa: E402
from live_contentops.plan_status_posts_v1 import queue_posts  # noqa: E402
from live_contentops.published_content_v1 import PRODUCTION_STORE  # noqa: E402

DEFAULT_EXPORT = Path(r"A:\Capital Chronicle\ResearchRuns\plan-status-v1")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--store", type=Path, default=PRODUCTION_STORE)
    args = parser.parse_args(argv)
    result = queue_posts(ContentOpsDurableStore(str(args.store), auto_migrate=False), args.export_dir)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
