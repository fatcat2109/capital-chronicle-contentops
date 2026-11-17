"""CC-548: the held digest intent and the sole publisher's failure record."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from live_contentops import publication_image_contract_v1 as contract
from test_publication_image_contract_cc463 import message_with


FIXTURES = Path(__file__).parent / "fixtures/cc548"
INTENT_SHA256 = "df874981e4d393a59154d6a7b1a9db4b86ad159e6f220549089a4653ff4d2e5d"
NOW = datetime(2026, 11, 13, 12, 15, tzinfo=timezone.utc)


def saved_intent():
    return json.loads((FIXTURES / "stored-12nov-intent.json").read_bytes())


def folderless_coordinator():
    return SimpleNamespace(store=None, _clock=lambda: NOW)


def test_stored_12nov_digest_intent_passes_without_reading_a_run_folder(tmp_path, monkeypatch):
    from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline

    raw = (FIXTURES / "stored-12nov-intent.json").read_bytes()
    assert sha256(raw).hexdigest() == INTENT_SHA256
    intent = json.loads(raw)
    before = deepcopy(intent)
    assert intent["output_dir"] is None
    assert intent["attempt_identity"] == "dispatch_eb2b3966e02acc41dff6e05958a7f067"
    assert intent["media_assets"][0]["asset_id"] == "digest-card-26c7481eb7ff825f1fdf"
    monkeypatch.chdir(tmp_path)
    (tmp_path / "run_context_v1.json").write_text(json.dumps({
        "article": {"market_asset": "XAUUSD"}}), encoding="utf-8")
    monkeypatch.setattr(pipeline, "_durable_intent_inputs",
                        lambda _: pytest.fail("a folderless digest tried to read run_context_v1.json"))
    assert contract.validate_write(folderless_coordinator(), intent, "substack") is None
    assert intent == before


@pytest.mark.parametrize("fields,cause", [
    ({"market_asset": "XAUUSD"}, "TRADINGVIEW_FIRST_IMAGE_REQUIRED"),
    ({"release_analysis": True}, "MACRO_SOURCE_GRAPH_REQUIRED"),
])
def test_folderless_market_or_release_still_needs_its_chart(fields, cause):
    intent = {"output_dir": None, "article": fields, "media_assets": []}
    with pytest.raises(contract.ImageContractError, match=cause):
        contract.validate_write(folderless_coordinator(), intent, "substack")


def test_folderless_image_template_still_uses_its_pixel_and_review_checks(tmp_path):
    intent = saved_intent()
    intent["media_assets"] = [{"asset_id": "invalid-template", "path": str(tmp_path / "missing.png"),
                               "image_template": {"template": "weekly"}}]
    with pytest.raises(contract.ImageContractError):
        contract.validate_write(folderless_coordinator(), intent, "substack")


def test_market_run_without_a_chart_is_refused_at_the_real_coordinator(tmp_path):
    _, runtime, coordinator, message = message_with(tmp_path, [])
    coordinator._readiness = lambda *a: pytest.fail("a missing chart reached a destination probe")
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == "DEFINITE_NO_WRITE"
    assert result["reason_code"] == "TRADINGVIEW_FIRST_IMAGE_REQUIRED"
    assert runtime.publish_calls == []


def test_first_exception_and_missing_path_survive_a_coordinator_restart(tmp_path, monkeypatch):
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

    store, runtime, coordinator, message = message_with(tmp_path, [])
    intent = json.loads(message["payload"])
    missing = Path(intent["output_dir"]) / "run_context_v1.json"
    missing.unlink()
    coordinator._readiness = lambda *a: pytest.fail("an invalid image contract reached a destination probe")
    result = coordinator._dispatch_message(message, canonical_url=None)
    assert result["status"] == "DEFINITE_NO_WRITE"
    assert result["reason_code"] == "PUBLICATION_IMAGE_CONTRACT_INVALID"
    assert result["image_contract_details"]["exception_type"] == "FileNotFoundError"
    assert result["image_contract_details"]["filename"] == str(missing)
    coordinator.store = ContentOpsDurableStore(store.db_path, auto_migrate=False)
    held = coordinator.store.get_reconciliations_for_work_item(intent["work_item_id"])
    record = next(r for r in held if r["reconciliation_id"] == coordinator._ids(
        intent["work_item_id"], intent["plan_hash"], "substack")["reconciliation_id"])
    reason, details = record["status"].split(": ", 1)
    assert reason == "PUBLICATION_IMAGE_CONTRACT_INVALID"
    assert json.loads(details) == result["image_contract_details"]
    monkeypatch.setattr(contract, "validate_write", lambda *a: pytest.fail("restart reproduced the failure"))
    again = coordinator._dispatch_message(message, canonical_url=None)
    assert again["reconciliation_status"] == record["status"]
    assert runtime.publish_calls == []
