"""Guard tests for the Institutional Cockpit Master Plan authority document.

These tests prove the operator-added master plan exists as a durable repo
authority and contains the required institutional cockpit sections, the product
safety boundaries, and the worker-platform discipline (Cline CLI implementation
vs Antigravity browser QA vs ChatGPT audit). They are intentionally strict so the
file cannot decay into a decorative stub.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER_PLAN = ROOT / "docs" / "CAPITAL_CHRONICLE_CONTENTOPS_INSTITUTIONAL_COCKPIT_MASTER_PLAN.md"


def _text() -> str:
    return MASTER_PLAN.read_text(encoding="utf-8")


def test_master_plan_exists():
    assert MASTER_PLAN.is_file(), str(MASTER_PLAN)


def test_master_plan_contains_required_sections():
    text = _text()
    required = [
        "Capital Chronicle ContentOps Institutional Cockpit Master Plan",
        "95–98/100",
        "State Before Action",
        "Canonical Truth Model",
        "Screen Grammar Standard",
        "Status Token System",
        "Command Center Redesign",
        "Evidence Vault Redesign",
        "Publish Readiness Tower Redesign",
        "Content Studio Redesign",
        "Calendar / Workflow Board Redesign",
        "Visual Export / Screenshot-Safe Mode",
        "Settings / Safety Policy Screen",
        "Affordance Discipline",
        "Layout Robustness",
        "Accessibility and Readability",
        "Automated UI Quality Gates",
        "Browser QA Plan",
        "Execution Roadmap to 95–98",
        "Scoring Rubric",
        "Non-Negotiable Safety Boundaries",
        "Final Definition of Done",
    ]
    for phrase in required:
        assert phrase in text, phrase


def test_master_plan_preserves_safety_boundaries():
    text = _text().lower()
    required = [
        "local-first",
        "evidence-grade",
        "institutional cockpit",
        "not a pretty dashboard",
        "not a social media scheduler",
        "not a trading terminal",
        "read-only by default",
        "no live posting",
        "no scheduler",
        "no platform api",
        "no credential/env reads",
        "no financial advice",
        "no signal language",
        "no market-direction color semantics",
    ]
    for phrase in required:
        assert phrase in text, phrase


def test_master_plan_defines_worker_platform_discipline():
    text = _text().lower()
    required = [
        "cline cli",
        "frontend/design/build tasks must read this master plan",
        "antigravity",
        "browser qa",
        "screenshot",
        "chatgpt audits",
        "worker pass claims",
    ]
    for phrase in required:
        assert phrase in text, phrase
