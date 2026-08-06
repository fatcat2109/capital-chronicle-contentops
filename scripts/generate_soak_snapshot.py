"""Generate the V5 soak data module from a real soak run output.

The snapshot is produced by the pipeline, not hand-authored, so the operator surface
cannot drift from what actually ran.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

snapshot_path = Path(sys.argv[1])
target = Path(sys.argv[2])
data = json.loads(snapshot_path.read_text(encoding="utf-8"))

body = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
target.write_text(
    "// Generated from a real `core-v0-shadow-soak` run.\n"
    "// Do not hand-edit: regenerate with scripts/generate_soak_snapshot.py.\n"
    f"export const coreV0SoakSnapshot = {body} as const;\n\n"
    "export type CoreV0SoakSnapshot = typeof coreV0SoakSnapshot;\n",
    encoding="utf-8",
)
print(f"wrote {target} ({len(body)} bytes of snapshot)")
