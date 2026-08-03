from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.fast_one_cycle_automation_v0 import run_fast_one_cycle

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "cc_artifact_packet_v0"
SAMPLE_PATH = FIXTURE_DIR / "sample_internal_draft_packet_v0.json"


@pytest.fixture(autouse=True)
def _exercise_historical_fast_cycle_mechanics(monkeypatch):
    from types import SimpleNamespace

    import live_contentops.fast_one_cycle_automation_v0 as legacy_runner

    monkeypatch.setattr(legacy_runner, "quarantine", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(legacy_runner, "os", SimpleNamespace(environ={}), raising=False)


def test_fast_one_cycle_run(tmp_path: Path) -> None:
    intake_dir = tmp_path / "intake"
    decision_dir = tmp_path / "decision"
    public_preview_dir = tmp_path / "public_preview"
    output_dir = tmp_path / "fast_out"

    res = run_fast_one_cycle(
        packet_path=SAMPLE_PATH,
        intake_dir=intake_dir,
        decision_dir=decision_dir,
        public_preview_dir=public_preview_dir,
        output_dir=output_dir,
        dispatch_live=False,
    )

    evidence = res["run_evidence"]
    assert evidence["topic"] == "US Macro & Alternative Ingestion Audit"
    assert evidence["intake_status"] == "PASS_WITH_CAVEAT_CONTENTOPS_CC_PACKET_INTAKE_V0"
    assert evidence["decision_status"] == "PUBLIC_CANDIDATE_ALLOWED_WITH_CAVEATS"
    assert evidence["public_ready"] is True
    assert evidence["dispatch_status"] == "NOT_ATTEMPTED"

    # Verify generated files
    assert (output_dir / "article.md").exists()
    assert (output_dir / "platform_payloads.json").exists()
    assert (output_dir / "dispatch_results.json").exists()
    assert (output_dir / "run_evidence.json").exists()

    article_content = (output_dir / "article.md").read_text(encoding="utf-8")
    assert "Internal candidate analysis" in article_content
    assert "DQR status: BLOCKED" in article_content

    payloads = json.loads((output_dir / "platform_payloads.json").read_text(encoding="utf-8"))
    platform_data = payloads.get("payloads", {})
    assert "discord" in platform_data
    assert "substack" in platform_data
    assert "x" in platform_data
    assert "linkedin" in platform_data
