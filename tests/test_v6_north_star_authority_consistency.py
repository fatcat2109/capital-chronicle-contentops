from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN"
STATUS_PATH = ROOT / "docs/status/current_project_status.json"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_current_authorities_do_not_reinstate_stale_blockers() -> None:
    targets = [
        PLAN / "current_v6_master_plan.md",
        PLAN / "next_task_pointer.md",
        ROOT / "docs/status/CURRENT_PROJECT_STATUS.md",
        ROOT / "docs/CONTENTOPS_FINAL_AUTOMATION_PIPELINE_READINESS_REPORT.md",
    ]
    stale = [
        "blocked_requires_chrome_extension_file_url_access",
        "substack not yet public",
        "youtube remains future text/image",
        "hard truncation is acceptable",
    ]
    for path in targets:
        text = _read(path).lower()
        assert not any(fragment in text for fragment in stale), path


