"""Guard test for the Operator Cockpit V4 final QA acceptance record (0174X).

Deterministic, local, documentation-only assertions. No browser, no network.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs" / "TASK_CONTENTOPS_0174X_OPERATOR_COCKPIT_V4_FINAL_QA_ACCEPTANCE_RECORD.md"

FULL_HEAD = "c81b3158fc3de5567f58f6c090f816d89e64419a"
SHORT_HEAD = "c81b315"
CLASSIFICATION = "PASS_FINAL_QA_READY_WITH_MINOR_VISUAL_CAVEATS"

SEVEN_SCREENS = [
    "Command Center",
    "Content Studio",
    "Publish Readiness Tower",
    "Evidence Vault",
    "Content Calendar / Workflow",
    "Visual Export / Screenshot-Safe",
    "Settings / Safety Policy",
]

VIEWPORTS = ["1440x900", "1366x768", "1536x864", "1920x1080"]


def _text() -> str:
    return RECORD.read_text(encoding="utf-8")


def test_acceptance_record_exists():
    assert RECORD.is_file()


def test_record_contains_full_and_short_head():
    text = _text()
    assert FULL_HEAD in text
    assert SHORT_HEAD in text


def test_record_contains_classification():
    assert CLASSIFICATION in _text()


def test_record_names_all_seven_screens():
    text = _text()
    for screen in SEVEN_SCREENS:
        assert screen in text, "missing screen: " + screen


def test_record_names_all_tested_viewports():
    text = _text()
    for vp in VIEWPORTS:
        assert vp in text, "missing viewport: " + vp


def test_record_states_v4_is_current_baseline():
    assert "current local static UI baseline" in _text()


def test_record_preserves_minor_caveats_as_non_blocking():
    text = _text().lower()
    assert "non-blocking" in text
    assert "truth rail remains dense" in text
    assert "reason label spacing" in text


def test_record_states_no_platform_or_live_behavior():
    text = _text().lower()
    for token in ["platform api", "provider api", "scheduler", "live posting",
                  "credential"]:
        assert token in text, "missing safety boundary token: " + token


def test_record_states_v2_v3_historical_only():
    assert "historical only" in _text().lower()


def test_record_states_design_references_reference_only():
    assert "reference-only" in _text().lower()


def test_record_states_future_ui_reads_master_plan_first():
    text = _text()
    assert "master plan first" in text.lower()
    assert "CAPITAL_CHRONICLE_CONTENTOPS_INSTITUTIONAL_COCKPIT_MASTER_PLAN.md" in text


def test_record_states_platform_roles():
    text = _text().lower()
    assert "antigravity remains browser qa" in text
    assert "cline remains implementation" in text
