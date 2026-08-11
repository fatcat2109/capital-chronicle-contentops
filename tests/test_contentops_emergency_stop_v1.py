from __future__ import annotations

from pathlib import Path

import pytest

from live_contentops import llm_operator_control_v1 as control
from live_contentops.llm_cost_governor_v1 import llm_cycle_budget_scope
from live_contentops.nine_router_llm_seam_v2 import (
    ROLE_ARTICLE_WRITING,
    routed_llm_invocation,
)
from live_contentops.nine_router_ordered_model_router_v2 import ProviderResult
from live_contentops.nine_router_provider_adapter_v2 import call_nine_router


ROOT = Path(__file__).resolve().parents[1]


def test_pause_marker_is_persistent_fail_closed_and_contains_no_secret(tmp_path):
    payload = control.activate_llm_operator_pause(
        tmp_path, activated_at_utc="2026-08-11T00:00:00Z"
    )
    marker = control.operator_pause_path(tmp_path)

    assert marker.is_file()
    assert control.llm_operator_pause_active(tmp_path) is True
    assert payload["state"] == "PAUSED_BY_OPERATOR"
    assert payload["contains_secrets"] is False
    assert "token" not in marker.read_text(encoding="utf-8").lower()

    marker.write_text("malformed but still paused", encoding="utf-8")
    with pytest.raises(control.LLMOperatorPausedError, match="^LLM_OPERATOR_PAUSED$"):
        control.assert_llm_operator_execution_enabled(tmp_path)

    assert control.resume_llm_operator_execution(tmp_path) is True
    assert control.llm_operator_pause_active(tmp_path) is False
    assert control.resume_llm_operator_execution(tmp_path) is False


def test_paused_canonical_seam_performs_zero_provider_calls(tmp_path, monkeypatch):
    monkeypatch.setattr(control, "RUNTIME_CONTROL_ROOT", tmp_path)
    control.activate_llm_operator_pause()
    provider_calls = 0

    def network_spy(prompt: str, model: str, timeout: float) -> ProviderResult:
        nonlocal provider_calls
        provider_calls += 1
        return ProviderResult(output="must not be reached", resolved_model=model)

    with pytest.raises(control.LLMOperatorPausedError, match="^LLM_OPERATOR_PAUSED$"):
        routed_llm_invocation(
            prompt="bounded test",
            role_task_id=ROLE_ARTICLE_WRITING,
            logical_invocation_id="paused_test",
            provider_call=network_spy,
        )

    assert provider_calls == 0


def test_pause_activated_during_fallback_allows_no_second_outbound_call(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(control, "RUNTIME_CONTROL_ROOT", tmp_path)
    provider_calls = 0

    def network_spy(prompt: str, model: str, timeout: float) -> ProviderResult:
        nonlocal provider_calls
        provider_calls += 1
        control.activate_llm_operator_pause()
        return ProviderResult(
            failure_class="quota_exhausted",
            resolved_model=None,
            usage={"total_tokens": 1},
        )

    with llm_cycle_budget_scope(
        "pause-during-fallback", control_root=tmp_path
    ):
        result = routed_llm_invocation(
            prompt="bounded fallback pause test",
            role_task_id=ROLE_ARTICLE_WRITING,
            logical_invocation_id="pause_during_fallback",
            provider_call=network_spy,
        )

    assert provider_calls == 1
    assert result["terminal_disposition"] == "LLM_TERMINAL_NON_RETRYABLE_FAILURE"
    assert result["attempts"][-1]["failure_class"] == "unclassified_failure"


def test_direct_adapter_honors_pause_before_credentials_or_network(tmp_path, monkeypatch):
    monkeypatch.setattr(control, "RUNTIME_CONTROL_ROOT", tmp_path)
    control.activate_llm_operator_pause()
    monkeypatch.delenv("NINEROUTER_API_KEY", raising=False)

    with pytest.raises(control.LLMOperatorPausedError, match="^LLM_OPERATOR_PAUSED$"):
        call_nine_router("bounded test", "vx/gemini-3.1-pro-preview", 1.0)


def test_one_click_stop_activates_pause_before_inventory_and_preserves_browsers():
    stop = (ROOT / "scripts" / "Stop-ContentOpsBackground.ps1").read_text(encoding="utf-8")
    stop_cmd = (ROOT / "STOP_ALL_CONTENTOPS_BACKGROUND.cmd").read_text(encoding="utf-8")
    resume = (ROOT / "scripts" / "Resume-ContentOpsLLM.ps1").read_text(encoding="utf-8")

    marker_write = stop.index("Move-Item -LiteralPath $temporaryMarker")
    inventory = stop.index("Get-CimInstance Win32_Process")
    termination = stop.index("Stop-Process -Id $targetPid")
    assert marker_write < inventory < termination
    assert "chrome.exe" in stop and "msedge.exe" in stop
    assert "AMBIGUOUS PROCESSES: NOT KILLED" in stop
    assert "Stop-ContentOpsBackground.ps1" in stop_cmd
    assert "Remove-Item -LiteralPath $pauseMarker" in resume
    assert "Start-Process" not in resume
