from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.terra_ultra_north_star_full_automation_v1 import main


if __name__ == "__main__":
    raise SystemExit(main())
