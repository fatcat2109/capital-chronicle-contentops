from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs" / "automation" / "FAST_ONE_CYCLE_AUTOMATION_V0"
RUN_EVIDENCE = DOCS_DIR / "run_evidence.json"
DISPATCH_RESULTS = DOCS_DIR / "dispatch_results.json"
PLATFORM_PAYLOADS = DOCS_DIR / "platform_payloads.json"
RECONCILIATION = DOCS_DIR / "post_dispatch_reconciliation_v0.json"
README = DOCS_DIR / "README.md"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def test_committed_fast_one_cycle_reconciliation_matches_evidence() -> None:
    run_evidence = _load(RUN_EVIDENCE)
    dispatch_results = _load(DISPATCH_RESULTS)
    platform_payloads = _load(PLATFORM_PAYLOADS)
    reconciliation = _load(RECONCILIATION)

    assert reconciliation["classification"] == "PASS_FAST_ONE_CYCLE_DISCORD_POST_RECONCILED_WITH_CAVEATS"
    assert reconciliation["reconciled_dispatch"]["dispatch_id"] == run_evidence["dispatch_id"]
    assert reconciliation["reconciled_dispatch"]["dispatch_id"] == dispatch_results["id"]
    assert reconciliation["reconciled_dispatch"]["platform"] == run_evidence["dispatch_platform"]
    assert reconciliation["reconciled_dispatch"]["platform"] == dispatch_results["platform"]
    assert reconciliation["reconciled_dispatch"]["dispatch_status"] == dispatch_results["status"]
    assert reconciliation["reconciled_dispatch"]["dispatch_timestamp"] == dispatch_results["response"]["timestamp"]
    assert reconciliation["reconciled_dispatch"]["redispatch_attempted"] is False
    assert reconciliation["reconciled_dispatch"]["webhook_recontacted"] is False
    assert reconciliation["reconciled_dispatch"]["provider_probe_attempted"] is False
    assert reconciliation["scope_findings"]["fixture_based_candidate_dispatch"] is True
    assert reconciliation["scope_findings"]["only_discord_live_dispatch_proven"] is True
    assert reconciliation["scope_findings"]["full_cdp_to_public_post_pipeline_proven"] is False
    assert reconciliation["scope_findings"]["multi_platform_public_dispatch_proven"] is False
    assert platform_payloads["payloads"]["discord"]["text"] == dispatch_results["response"]["content"]
    assert reconciliation["consistency_checks"]["discord_payload_text_matches_dispatch_response"] is True


def test_fast_one_cycle_readme_preserves_caveated_scope() -> None:
    text = README.read_text(encoding="utf-8-sig")

    assert "fixture-based candidate commentary" in text
    assert "did **not** prove full CDP -> trusted local database -> article -> media -> multi-platform public dispatch automation" in text
    assert "1524780271814311966" in text
    assert "9f0d55875ae11d07e594d36bff25a28e5086b45f" in text
    assert "PASS_FAST_ONE_CYCLE_DISCORD_POST_RECONCILED_WITH_CAVEATS" in text
