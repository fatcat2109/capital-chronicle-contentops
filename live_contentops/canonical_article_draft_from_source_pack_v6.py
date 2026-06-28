"""V6 Canonical Article Draft From Verified Source Pack Coordinator.

Main runner driving source pack gating, claim binding checks, template-based draft rendering, safety audits, and artifact generation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import verified_source_pack_v6 as source_pack_module
from live_contentops import canonical_article_draft_gate_v6 as draft_gate
from live_contentops import source_claim_binding_validator_v6 as binding_module
from live_contentops import canonical_article_draft_safety_validator_v6 as safety_validator

TASK_LABEL = "TASK_CONTENTOPS_V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK_DRY_RUN_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK")


def load_json_or_fallback(path: str | Path, default_val: Any) -> Any:
    p = Path(path)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default_val


def render_blocked_markdown(
    title: str,
    requirements: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    blockers: list[str]
) -> str:
    """Renders a review-only blocked draft planning preview."""
    blocker_bullets = "\n".join(f"- `{b}`" for b in blockers)

    req_rows = []
    for r in requirements:
        req_rows.append(
            f"| {r['research_requirement_id']} | {r['required_source_type']} | {r['source_name_placeholder']} | {r['source_verification_status']} |"
        )
    req_table = "\n".join(req_rows)

    claim_rows = []
    for c in claims:
        claim_rows.append(
            f"- **[{c['claim_id']}]** (*{c['verification_status']}*): {c['claim_text_draft']}"
        )
    claims_text = "\n".join(claim_rows)

    return f"""# Canonical Article Draft Planning Preview

> [!WARNING]
> **DRAFT COPY GENERATION BLOCKED: MISSING REQUIRED SOURCE VERIFICATION**

## Article Planning Title
**{title}**

## Active Blockers
{blocker_bullets}

## Required Research Sources
| ID | Category | Placeholder | Status |
| --- | --- | --- | --- |
{req_table}

## Scaffold Claims
{claims_text}

## Required Caveats
- Macroeconomic parameters are highly uncertain and model-dependent.
- This analysis is for educational purposes only; consult licensed financial professionals.

## Next Operator Actions
1. Operator must verify sources for all missing requirements.
2. Operator must bind claims to retrieved evidence.
"""


def render_verified_markdown(
    title: str,
    claims: list[dict[str, Any]],
    source_pack: dict[str, Any]
) -> str:
    """Renders the canonical article draft when source pack is fully verified."""
    claim_details = []
    for c in claims:
        # Find matching source entries
        refs = c.get("source_requirement_refs", [])
        entry_names = []
        for ref in refs:
            entry = next((e for e in source_pack.get("source_entries", []) if e["source_requirement_id"] == ref), None)
            if entry:
                entry_names.append(f"{entry.get('source_name')} ({entry.get('source_publisher')})")
        citations = ", ".join(entry_names)
        claim_details.append(
            f"- **Claim**: {c['claim_text_draft']}\n  *Sourced from*: {citations}"
        )
    claims_text = "\n".join(claim_details)

    return f"""# Refined Study: source verification and data provenance of recent macroeconomic reports

## Executive Summary
This analysis reviews interest rate structures and macroeconomic data provenance.

## Verified Grounding Details
{claims_text}

## Structural Caveats
- Macroeconomic parameters are highly uncertain and model-dependent.
- This analysis is for educational purposes only; consult licensed financial professionals.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Canonical Article Draft From Verified Source Pack coordinator")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--custom-source-pack", default=None, help="Path to custom verified source pack JSON")
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load planning inputs
    packet = load_json_or_fallback(
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/next_canonical_article_packet.json",
        {}
    )
    requirements = load_json_or_fallback(
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/article_research_requirements.json",
        []
    )
    claims = load_json_or_fallback(
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/article_claim_ledger_scaffold.json",
        []
    )

    # 2. Write schema
    schema = source_pack_module.get_verified_source_pack_schema()
    Path(out_dir / "verified_source_pack_schema.json").write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )

    # 3. Generate and write default missing source pack
    missing_pack = source_pack_module.generate_default_missing_source_pack(requirements)
    Path(out_dir / "verified_source_pack_missing_default.json").write_text(
        json.dumps(missing_pack, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )

    # 4. Load the active source pack (custom if provided, otherwise default missing pack)
    if args.custom_source_pack:
        active_pack = load_json_or_fallback(args.custom_source_pack, missing_pack)
    else:
        active_pack = missing_pack

    # 5. Evaluate the draft gate
    gate_report, gate_blockers = draft_gate.evaluate_draft_gate(active_pack, requirements, claims)

    # 6. Generate source-claim binding report
    binding_report = binding_module.generate_source_claim_binding_report(claims, active_pack)

    # 7. Generate draft preview
    gate_passed = gate_report.get("gate_status") == "PASSED"
    title = packet.get("title_candidate", "Macroeconomic Providence Study")

    if gate_passed:
        draft_markdown = render_verified_markdown(title, claims, active_pack)
        article_copy_generated = True
        draft_preview_is_placeholder = False
        draft_status = "READY_FOR_OPERATOR_REVIEW"
    else:
        draft_markdown = render_blocked_markdown(title, requirements, claims, gate_blockers)
        article_copy_generated = False
        draft_preview_is_placeholder = True
        draft_status = "BLOCKED_MISSING_VERIFIED_SOURCE_PACK"

    Path(out_dir / "canonical_article_draft_preview.md").write_text(draft_markdown, encoding="utf-8")

    # 8. Assemble canonical article draft packet
    draft_packet = {
        "canonical_article_draft_status": draft_status,
        "article_copy_generated": article_copy_generated,
        "draft_copy_generation_allowed": gate_passed,
        "draft_markdown_created": True,
        "draft_preview_is_placeholder": draft_preview_is_placeholder,
        "source_verification_required": True,
        "claim_ledger_required": True,
        "all_claims_bound_to_sources": binding_report.get("all_claims_bound_to_sources", False),
        "allowed_for_publication": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "provider_call_performed": False,
        "llm_provider_call_performed": False,
        "browser_session_started": False,
        "credentials_hydrated": False,
        "human_review_required": True,
        "kill_switch_active": True,
        "title_candidate": title,
        "thesis_candidate": packet.get("thesis_candidate", "")
    }

    # 9. Perform compliance checks
    validation_report, all_blockers = safety_validator.validate_article_draft(
        draft_packet, active_pack, gate_report, binding_report, draft_markdown
    )

    draft_packet["blockers"] = all_blockers
    draft_packet["blocker_count"] = len(all_blockers)

    # 10. Write remaining JSON artifacts
    artifacts = {
        "source_pack_gate_report.json": gate_report,
        "source_claim_binding_report.json": binding_report,
        "canonical_article_draft_packet.json": draft_packet,
        "canonical_article_draft_validation_report.json": validation_report
    }

    for name, data in artifacts.items():
        Path(out_dir / name).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )

    # 11. Write Markdown files
    # blockers report
    blocker_bullets = "\n".join(f"- `{b}`" for b in all_blockers) if all_blockers else "- None"
    blocker_report = f"""# Article Draft Blocker Report

- **Task Label**: {TASK_LABEL}
- **Loop Status**: {draft_status}
- **Blocker Count**: {len(all_blockers)}

## Active Blockers
{blocker_bullets}
"""
    Path(out_dir / "canonical_article_draft_blocker_report.md").write_text(blocker_report, encoding="utf-8")

    # runbook
    runbook = """# Canonical Article Draft Runbook

Validates source packs and binds claims to generate Substack canonical drafts.

## Instructions
1. Load verified source pack.
2. Confirm Nelso-Siegel curves and statistics are bound.
3. Keep publication flags locked.
"""
    Path(out_dir / "canonical_article_draft_runbook.md").write_text(runbook, encoding="utf-8")

    # implementation report
    implementation = f"""# Article Draft Implementation Report

- **Task Label**: {TASK_LABEL}
- **Baseline starting HEAD**: aba1d6448cd545df2035bcc0d0e4082779106a47
- **Safety posture**: review-only drafting constraints enforced; validator status remains FAILED_WITH_BLOCKERS because the default source pack is missing.
"""
    Path(out_dir / "implementation_report.md").write_text(implementation, encoding="utf-8")

    # next task pointer
    next_task = """# Next Task Pointer

Recommended next task:

`TASK_CONTENTOPS_V6_SOURCE_PACK_VERIFICATION_UI_AND_OPERATOR_RESEARCH_CHECKLIST_HEAVY_BATCH_V0`
"""
    Path(out_dir / "next_task_pointer.md").write_text(next_task, encoding="utf-8")

    print(json.dumps({
        "canonical_article_draft_status": draft_packet["canonical_article_draft_status"],
        "blockers": all_blockers
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
