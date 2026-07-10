"""CLI wrapper for the Substack-first north-star ContentOps loop."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.substack_first_north_star_pipeline_loop_v1 import main


if __name__ == "__main__":
    raise SystemExit(main())
