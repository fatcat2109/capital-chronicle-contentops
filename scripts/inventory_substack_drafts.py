"""Write the CC-173 CSV from Neo-captured draft metadata and a read-only store."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.substack_draft_inventory_v1 import write_inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", action="append", required=True, type=Path)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    batches = [batch for path in args.batch for batch in json.loads(path.read_text(encoding="utf-8"))]
    print(json.dumps(write_inventory(batches=batches, store_path=args.store, output_path=args.output), indent=2))


if __name__ == "__main__":
    main()
