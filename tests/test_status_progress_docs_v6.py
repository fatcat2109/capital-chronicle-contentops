from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS_DIR = ROOT / "docs" / "status"
PLAN = ROOT / "docs" / "automation" / "V6_FINAL_PRODUCT_EXECUTION_PLAN" / "current_v6_master_plan.md"
LEDGER = ROOT / "docs" / "automation" / "V6_FINAL_PRODUCT_EXECUTION_PLAN" / "v6_25_task_ledger.md"
PROGRESS = STATUS_DIR / "PROJECT_PROGRESS_LEDGER.md"
MAP = STATUS_DIR / "STATUS_AND_PROGRESS_DOCS_MAP.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def test_required_status_progress_files_exist() -> None:
    for path in [
        STATUS_DIR / "CURRENT_PROJECT_STATUS.md",
        STATUS_DIR / "current_project_status.json",
        STATUS_DIR / "STATUS_LEDGER_SHA_MODEL.md",
        PROGRESS,
        MAP,
        PLAN,
        LEDGER,
    ]:
        assert path.exists(), path


def test_master_plan_contains_v6_loop_without_mojibake_arrows() -> None:
    text = _read(PLAN)
    assert "V6 North-Star Loop" in text
    assert "→ AI research and grounding" in text
    assert "→ canonical Substack long-form article" in text
    loop = text.split("```text", 1)[1].split("```", 1)[0]
    assert "? AI research" not in loop
    assert "? canonical" not in loop


def test_roadmap_ledger_mentions_manual_publication_lanes() -> None:
    text = _read(LEDGER).lower()
    assert "substack manual publication evidence" in text
    assert "linkedin manual publication evidence" in text
    assert "complete_fixture_only" in text


def test_project_progress_ledger_includes_linkedin_and_substack() -> None:
    text = _read(PROGRESS).lower()
    assert "linkedin manual publication evidence" in text
    assert "substack manual export / publication evidence" in text
    assert "83c53fd3a39b377d9f74fa70cd8b6a5357689ecb" in text


def test_status_progress_docs_map_defines_update_cadence() -> None:
    text = _read(MAP).lower()
    assert "every non-read-only task" in text
    assert "accepted milestone or lane completion" in text
    assert "major product/north-star strategy changes only" in text
    assert "soft recommendations only" in text
    assert "github remote" in text and "project sources" in text


def test_governance_docs_do_not_contain_secret_patterns() -> None:
    combined = "\n".join(_read(path) for path in [PLAN, LEDGER, PROGRESS, MAP])
    forbidden = [
        r"https://discord(?:app)?\.com/api/webhooks/",
        r"sk-[a-zA-Z0-9]{12,}",
        r"xox[baprs]-",
        r"ghp_[A-Za-z0-9]",
        r"bearer\s+[A-Za-z0-9._-]{12,}",
        r"cookie\s*[:=]",
        r"localstorage\s*[:=]",
        r"sessionstorage\s*[:=]",
        r"browser session data\s*[:=]",
    ]
    for pattern in forbidden:
        assert not re.search(pattern, combined, flags=re.IGNORECASE)
