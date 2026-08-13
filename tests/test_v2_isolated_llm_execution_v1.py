from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import live_contentops.llm_operator_control_v1 as shared_control
import live_contentops.nine_router_provider_adapter_v2 as adapter
import live_contentops.v2_isolated_llm_execution_v1 as isolated
from live_contentops.nine_router_ordered_model_router_v2 import ProviderResult


def _active_test_lease(tmp_path: Path, monkeypatch) -> isolated.V2ExecutionLease:
    marker = tmp_path / "shared" / shared_control.LLM_OPERATOR_PAUSE_FILENAME
    marker.parent.mkdir()
    marker.write_text("PAUSED\n", encoding="utf-8")
    monkeypatch.setattr(isolated, "operator_pause_path", lambda: marker)
    control = tmp_path / "v2-control"
    nonce = "test-nonce"
    now = datetime.now(timezone.utc)
    lease = isolated.V2ExecutionLease(
        domain_id="v2-01-test", task_id=isolated.TASK_ID, branch=isolated.BRANCH,
        worktree=str(tmp_path), run_id=isolated.RUN_ID, brain=isolated.BRAIN,
        control_root=control, lease_path=control / "lease.json",
        audit_path=control / "audit.json", nonce=nonce,
        created_at_utc=isolated._iso(now),
        expires_at_utc=isolated._iso(now + timedelta(hours=1)),
    )
    common = {
        "schema_version": isolated.SCHEMA_VERSION, "state": "ACTIVE",
        "domain_id": lease.domain_id, "task_id": isolated.TASK_ID,
        "branch": isolated.BRANCH, "worktree": lease.worktree,
        "run_id": isolated.RUN_ID, "brain": isolated.BRAIN,
        "zero_public_write": True,
        "nonce_sha256": hashlib.sha256(nonce.encode()).hexdigest(),
        "expires_at_utc": lease.expires_at_utc,
        "shared_global_pause": {
            "path": str(marker), "present": True,
            "sha256": hashlib.sha256(marker.read_bytes()).hexdigest(),
        },
    }
    isolated._atomic_json(lease.lease_path, common)
    isolated._atomic_json(lease.audit_path, common | {
        "provider_attempts": [], "logical_invocations": [],
    })
    return lease


def test_only_replacement_runner_can_issue_lease(tmp_path: Path) -> None:
    with pytest.raises(isolated.V2ExecutionLeaseError, match="issuer_not_v2_replacement_runner"):
        isolated.issue_v2_execution_lease(repo_root=tmp_path, runtime=tmp_path)


def test_absent_lease_and_public_write_fail_closed(tmp_path: Path, monkeypatch) -> None:
    with pytest.raises(isolated.V2ExecutionLeaseError, match="not_active"):
        isolated.assert_v2_execution_authorized(
            role_task_id="V2_CREATIVE_EDITOR", logical_invocation_id="inv_v2_test",
            component=isolated.BRAIN,
        )
    lease = _active_test_lease(tmp_path, monkeypatch)
    token = isolated._ACTIVE_LEASE.set(lease)
    try:
        with pytest.raises(isolated.V2ExecutionLeaseError, match="zero_public_write"):
            isolated.assert_v2_execution_authorized(
                role_task_id="V2_CREATIVE_EDITOR", logical_invocation_id="inv_v2_test",
                component=isolated.BRAIN, public_write=True,
            )
        with pytest.raises(isolated.V2ExecutionLeaseError, match="model_not_authorized"):
            isolated.assert_v2_execution_authorized(
                role_task_id="V2_CREATIVE_EDITOR", logical_invocation_id="inv_v2_test",
                component=isolated.BRAIN, model="new/claude-fable-5",
            )
    finally:
        isolated._ACTIVE_LEASE.reset(token)


def test_generic_adapter_remains_blocked_inside_v2_lease(tmp_path: Path, monkeypatch) -> None:
    lease = _active_test_lease(tmp_path, monkeypatch)
    monkeypatch.setattr(shared_control, "RUNTIME_CONTROL_ROOT", tmp_path / "shared")
    token = isolated._ACTIVE_LEASE.set(lease)
    try:
        with pytest.raises(shared_control.LLMOperatorPausedError):
            adapter.call_nine_router("never sent", "new/gpt-5.6-sol-xhigh", 1)
    finally:
        isolated._ACTIVE_LEASE.reset(token)


def test_isolated_adapter_requires_exact_lease_and_records_sanitized_attempt(
    tmp_path: Path, monkeypatch,
) -> None:
    lease = _active_test_lease(tmp_path, monkeypatch)
    monkeypatch.setattr(
        adapter, "_call_nine_router_impl",
        lambda *args, **kwargs: ProviderResult(
            text="READY", resolved_model="gpt-5.6-sol", status_code=200,
            provider_invocation_id="provider-secret-id",
        ),
    )
    token = isolated._ACTIVE_LEASE.set(lease)
    try:
        result = adapter.call_nine_router_v2_isolated(
            "prompt", "new/gpt-5.6-sol-xhigh", 1,
            role_task_id="V2_CREATIVE_EDITOR", logical_invocation_id="inv_v2_test",
            component=isolated.BRAIN,
        )
    finally:
        isolated._ACTIVE_LEASE.reset(token)
    assert result.text == "READY"
    audit = json.loads(lease.audit_path.read_text(encoding="utf-8"))
    assert len(audit["provider_attempts"]) == 1
    blob = json.dumps(audit)
    assert "provider-secret-id" not in blob
    assert audit["provider_attempts"][0]["public_write"] is False


def test_minimal_raw_isolated_adapter_uses_same_exact_lease_and_audit(
    tmp_path: Path, monkeypatch,
) -> None:
    lease = _active_test_lease(tmp_path, monkeypatch)
    observed = {}

    def fake_minimal(*args, **kwargs):
        observed.update(kwargs)
        return ProviderResult(
            text="{}", resolved_model="gpt-5.6-sol-xhigh", status_code=200
        )

    monkeypatch.setattr(adapter, "_call_nine_router_minimal_raw_impl", fake_minimal)
    token = isolated._ACTIVE_LEASE.set(lease)
    try:
        result = adapter.call_nine_router_v2_isolated_minimal_raw(
            "prompt",
            "new/gpt-5.6-sol-xhigh",
            600,
            role_task_id="V2_CREATIVE_EDITOR",
            logical_invocation_id="inv_v2_minimal_test",
            component=isolated.BRAIN,
            evidence_dir=tmp_path / "evidence",
        )
    finally:
        isolated._ACTIVE_LEASE.reset(token)
    assert result.status_code == 200
    assert observed["isolated_execution_domain_id"] == lease.domain_id
    audit = json.loads(lease.audit_path.read_text(encoding="utf-8"))
    assert len(audit["provider_attempts"]) == 1
    assert audit["provider_attempts"][0]["requested_model"] == (
        "new/gpt-5.6-sol-xhigh"
    )
    assert audit["provider_attempts"][0]["public_write"] is False
