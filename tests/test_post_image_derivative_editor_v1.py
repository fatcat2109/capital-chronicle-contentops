"""The current MAX run reviews a dated image copy on the existing short path."""
from copy import deepcopy

import pytest

from live_contentops.native_desktop_editorial_v1 import (
    DesktopInputRequired, NativeDesktopTurn, request_final_visual_review,
    dated_distribution_recovery_acceptance,
)
from test_linkedin_neo_recovery_v1 import linkedin_recovery


def test_current_editor_uses_one_check_and_image_consumer_without_named_writer_or_screenshots(tmp_path, monkeypatch):
    store, binding, result, coordinator, runtime, recovery, ids = linkedin_recovery(tmp_path, monkeypatch)
    monkeypatch.setattr("live_contentops.native_publication_latency_v1.uses_short_path",
        lambda *a, **k: any(p["destination"] == "linkedin" and
            p["payload"].get("text", "").startswith(recovery["date_label"])
            for p in k["result"].get("previews", [])))
    turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=binding["output_dir"], owner_manual_validation=True)
    with pytest.raises(DesktopInputRequired) as pending:
        request_final_visual_review(turn, renders=None, distribution_recovery=recovery)
    request = pending.value.request
    assert request["governed_input"]["binding"]["renders"] == []
    observation = deepcopy(turn._get("write", "response")["invocation_observation"])
    observation.update(surface="CODEX_EXEC", invocation_id="current-max-editor-not-the-historical-writer")
    turn.submit(request["stage"], {"request_sha256": request["request_sha256"],
        "invocation_observation": observation, "output": {"decision": "ACCEPT",
            "rationale": "Fixture editor checks unchanged source facts, dated copy, exact canonical and admitted image selection."}})
    ref = {"stage": request["stage"], "request_sha256": request["request_sha256"], "output_dir": binding["output_dir"]}
    accepted, acceptance = dated_distribution_recovery_acceptance(store, run_id=binding["run_id"], reference=ref)
    assert acceptance["pixels_inspected"] is False
    assert acceptance["automated_media_check"]["findings"]
    store.set_dispatch_status(ids["dispatch_id"], "RECONCILED_ABSENT_SAFE_TO_RETRY")
    store.register_reconciliation(reconciliation_id=ids["reconciliation_id"], work_item_id=binding["run_id"],
        status="RECONCILED_ABSENT_SAFE_TO_RETRY")
    from types import SimpleNamespace
    runtime._neo_transport = SimpleNamespace(native_executor=SimpleNamespace(native_neo_protocol=True,
        readiness=lambda _: {"authenticated": True, "native_executor_bound": True,
            "proof_fresh": True, "public_handle": "linkedin:jimcc"}))
    coordinator.complete_dated_distribution_recovery(ids["message_id"], review_reference=ref)
    assert runtime.publish_calls == ["linkedin"]
    assert runtime.sent[0]["native_payload"] == accepted["payloads"]["linkedin"]
    assert runtime.sent[0]["native_payload"]["media_asset_ids"] == [a["asset_id"] for a in result["media_assets"]]
