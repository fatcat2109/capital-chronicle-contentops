"""Final visual/repair contract in disposable fixtures, never proof of visual judgment."""
import copy
import json
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.contentops_editorial_desk_v1 import record_native_article_review
from live_contentops.native_desktop_editorial_v1 import (
    require_current_final_visual_review, native_review_revision, bind_editorial_media,
)
from native_final_visual_fixture_v1 import visual_request_fixture
from test_native_desktop_publication_v1 import seeded, composed


def accept(store, binding, result, review, turn, request, response):
    turn.submit(request["stage"], response)
    return record_native_article_review(store, run_id=binding["run_id"], article_identity=result["article_identity"],
        decision="KEEP", expected_review_id=review["review_id"],
        rationale="Controlled final-media contract acceptance, not actual model/pixel judgment proof.",
        final_visual_review={"stage": request["stage"], "request_sha256": request["request_sha256"], "output_dir": str(turn.root)})


def test_missing_actual_final_acceptance_cannot_enter_native_publication(tmp_path, monkeypatch):
    store, binding, rollout, _, _ = seeded(tmp_path, monkeypatch, final_visual=False)
    pub, _, transport = composed(store, binding, rollout, monkeypatch)
    with pytest.raises(ValueError, match="ACTUAL_FINAL_MAX_VISUAL_REVIEW_REQUIRED"):
        pub.resume()
    assert transport.calls == []
    plan, _ = pub.validate()
    store.create_work_item(story_id=binding["run_id"], work_item_id=binding["run_id"],
        title="Controlled direct coordinator dispatch guard", target_surface="TEST")
    pub.coordinator.register_plan(binding["run_id"], plan)
    item = next(m for m in store.list_outbox_messages() if m["work_item_id"] == binding["run_id"] and m["destination"] == "substack")
    outcome = pub.coordinator._dispatch_message(item, canonical_url=None)
    assert outcome["status"] == "FINAL_VISUAL_REPAIR_OR_REVIEW_REQUIRED" and outcome["publish_called"] is False


@pytest.mark.parametrize("field,value", [("model", "gpt-6-luna"), ("model", None),
    ("reasoning_effort", "low"), ("invocation_id", "ANOTHER_REVIEWER")])
def test_wrong_or_unobserved_model_effort_and_other_writer_rejected(tmp_path, monkeypatch, field, value):
    store, binding, _, result, _ = seeded(tmp_path, monkeypatch, final_visual=False)
    turn, request, response = visual_request_fixture(store, binding, result)
    response["invocation_observation"][field] = value
    with pytest.raises(ValueError, match="MODEL_MISMATCH|ROLE_EFFORT_MISMATCH|ACTUAL_SAME_SOL61_MAX"):
        turn.submit(request["stage"], response)
    assert turn._get(request["stage"], "response") is None


@pytest.mark.parametrize("defect", ["zero_baseline_scale", "labels_legend", "transformation_rounding"])
def test_material_sign_label_rounding_findings_require_same_product_correction(tmp_path, monkeypatch, defect):
    store, binding, _, result, review = seeded(tmp_path, monkeypatch, final_visual=False)
    turn, request, response = visual_request_fixture(store, binding, result)
    chart = next(f for f in response["output"]["asset_findings"] if defect in f["checks"])
    chart["checks"][defect] = "FAIL"
    chart["findings"] = ["Concrete controlled defect in " + defect + "; correct only the affected presentation."]
    with pytest.raises(ValueError, match="UNRESOLVED_ISSUE"):
        turn.submit(request["stage"], response)
    response["output"]["decision"] = "REPAIR_REQUIRED"
    turn.submit(request["stage"], response)
    with pytest.raises(ValueError, match="TARGETED_REPAIR_REQUIRED"):
        record_native_article_review(store, run_id=binding["run_id"], article_identity=result["article_identity"],
            decision="KEEP", expected_review_id=review["review_id"], rationale="Cannot accept a controlled unresolved chart defect.",
            final_visual_review={"stage": request["stage"], "request_sha256": request["request_sha256"], "output_dir": str(turn.root)})
    # Corrected affected presentation is a new immutable request in the same run;
    # original sources, article and accepted filter/plan/writer records are reused.
    corrected, new_request, new_response = visual_request_fixture(store, binding, result, revision_tag="corrected-"+defect)
    assert new_request["stage"] != request["stage"] and corrected.run_id == turn.run_id
    accept(store, binding, result, review, corrected, new_request, new_response)
    acceptance = require_current_final_visual_review(store, run_id=binding["run_id"])
    assert acceptance["invocation_observation"]["invocation_id"] == response["invocation_observation"]["invocation_id"]
    assert turn._get(request["stage"], "response")["output"]["decision"] == "REPAIR_REQUIRED"


@pytest.mark.parametrize("change", ["render", "render_source", "asset", "preview"])
def test_changed_render_media_or_variant_invalidates_acceptance(tmp_path, monkeypatch, change):
    store, binding, _, result, review = seeded(tmp_path, monkeypatch)
    reference = review["final_visual_review"]
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn
    turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=binding["output_dir"], owner_manual_validation=True)
    rendered = turn.frozen_request(reference["stage"])["governed_input"]["binding"]["renders"][0]
    if change == "render":
        Path(rendered["path"]).write_bytes(b"changed pixels")
    elif change == "render_source":
        Path(rendered["render_source"]["path"]).write_text("changed layout")
    elif change == "asset":
        Path(result["media_assets"][0]["path"]).write_bytes(b"changed asset")
    else:
        changed = copy.deepcopy(result)
        changed["previews"][0]["payload"] = {"text": "Changed channel copy"}
        store.finalize_outbox_payload_before_dispatch(message_id="cc-editorial-final-"+sha256_of(binding["run_id"]),
            payload=json.dumps(changed), status="EDITORIAL_INTERNAL")
    with pytest.raises(ValueError, match="CHANGED|UNBOUND"):
        require_current_final_visual_review(store, run_id=binding["run_id"])


def test_same_max_targeted_media_edit_keeps_the_article_and_invalidates_only_old_review(tmp_path, monkeypatch):
    store, binding, _, result, _ = seeded(tmp_path, monkeypatch, final_visual=False)
    turn, request, response = visual_request_fixture(store, binding, result)
    photo = next(a for a in response["output"]["asset_findings"] if "caption_credit_alt" in a["checks"])
    photo["checks"]["caption_credit_alt"] = "FAIL"
    photo["findings"] = ["Controlled alt-text clarity defect; preserve lawful original pixels."]
    response["output"]["decision"] = "REPAIR_REQUIRED"
    turn.submit(request["stage"], response)
    assets = copy.deepcopy(result["media_assets"])
    assets[0]["alt_text"] += " Controlled targeted clarity correction."
    repair = {"stage": request["stage"], "request_sha256": request["request_sha256"],
        "output_dir": binding["output_dir"], "invocation_id": response["invocation_observation"]["invocation_id"],
        "findings_addressed": ["Controlled alt-text clarity defect"]}
    outcome = bind_editorial_media(store, run_id=binding["run_id"], article_identity=result["article_identity"],
        assets=assets, expected_package_revision=native_review_revision(result), final_visual_repair=repair)
    assert outcome["article_identity"] == result["article_identity"]
    updated = json.loads(store.get_outbox_message("cc-editorial-final-"+sha256_of(binding["run_id"]))["payload"])
    assert updated["article"] == result["article"] and updated["evidence"] == result["evidence"]
    assert native_review_revision(updated) != native_review_revision(result)
    assert any(m["destination"] == "internal:native-editorial-package-history" for m in store.list_outbox_messages())


def test_matching_current_acceptance_allows_existing_continuation(tmp_path, monkeypatch):
    store, binding, rollout, _, _ = seeded(tmp_path, monkeypatch)
    require_current_final_visual_review(store, run_id=binding["run_id"])
    pub, _, _ = composed(store, binding, rollout, monkeypatch)
    # This is the existing actual-tool request boundary, not real provider proof.
    outcome = pub.resume()
    assert outcome["classification"] == "NATIVE_PUBLICATION_CONTINUATION"


def test_unavailable_pixels_are_preserved_as_unverified_without_acceptance(tmp_path, monkeypatch):
    store, binding, _, result, _ = seeded(tmp_path, monkeypatch, final_visual=False)
    turn, request, response = visual_request_fixture(store, binding, result)
    finding = response["output"]["render_findings"][0]
    finding.update(pixels_inspected=False, findings=["Controlled visual access is unavailable; preserve this exact article/view."])
    finding["checks"]["crop_distortion"] = "UNVERIFIED"
    with pytest.raises(ValueError, match="UNRESOLVED_ISSUE"):
        turn.submit(request["stage"], response)
    response["output"]["decision"] = "EXTERNAL_BLOCK"
    turn.submit(request["stage"], response)
    assert turn._get(request["stage"], "response")["output"]["decision"] == "EXTERNAL_BLOCK"
    with pytest.raises(ValueError, match="ACTUAL_FINAL_MAX_VISUAL_REVIEW_REQUIRED"):
        require_current_final_visual_review(store, run_id=binding["run_id"])


def test_same_max_copy_correction_uses_existing_source_validator_without_restarting(tmp_path, monkeypatch):
    store, binding, _, result, _ = seeded(tmp_path, monkeypatch, final_visual=False)
    turn, request, response = visual_request_fixture(store, binding, result)
    finding = response["output"]["render_findings"][0]
    finding["checks"]["placement"] = "FAIL"
    finding["findings"] = ["Controlled dek needs a precise reader-facing clarification."]
    response["output"]["decision"] = "REPAIR_REQUIRED"
    turn.submit(request["stage"], response)
    worker = json.loads((Path(__file__).resolve().parents[1] /
        "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal31/goal31-company-machine-reading-write-output.json").read_bytes())
    prior_dek = worker["article"]["dek"]
    worker["article"]["dek"] += " A focused reading."
    for claim in worker["material_claim_bindings"]:
        if claim["claim_text"] == prior_dek:
            claim["claim_text"] = worker["article"]["dek"]
    repair = {"stage": request["stage"], "request_sha256": request["request_sha256"],
        "output_dir": binding["output_dir"], "invocation_id": response["invocation_observation"]["invocation_id"],
        "findings_addressed": finding["findings"]}
    original_record = (Path(binding["output_dir"]) / "qualified_article_record_v1.json").read_bytes()
    outcome = bind_editorial_media(store, run_id=binding["run_id"], article_identity=result["article_identity"],
        assets=result["media_assets"], expected_package_revision=native_review_revision(result),
        final_visual_repair=repair, corrected_worker_output=worker)
    assert outcome["public_write_performed"] is False
    updated = json.loads(store.get_outbox_message("cc-editorial-final-"+sha256_of(binding["run_id"]))["payload"])
    assert updated["article"]["dek"].endswith(" A focused reading.")
    assert updated["evidence"] == result["evidence"] and updated["visual_repair_revision"]["intake_restarted"] is False
    assert (Path(binding["output_dir"]) / "qualified_article_record_v1.json").read_bytes() == original_record
    assert Path(updated["visual_repair_revision"]["qualified_record_path"]).is_file()
