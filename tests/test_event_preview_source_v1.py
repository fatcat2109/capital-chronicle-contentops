"""Frozen public preview admission, privacy and existing-owner resume boundaries."""
from hashlib import sha256
import json
from pathlib import Path

import pytest

from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops import event_preview_source_v1 as adapter


@pytest.fixture(autouse=True)
def host_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "HOST_BACKLOG", tmp_path / "authority.txt")
    monkeypatch.setattr(adapter, "FROZEN_PREVIEW", tmp_path / "PREVIEW.md")


def fixture(tmp_path, text=None):
    text = text or "# Controlled election preview\n\nThe chambers could split. Prediction markets favour a split.\n"
    raw = text.encode()
    (tmp_path / "PREVIEW.md").write_bytes(raw)
    approval = ("CC-107\nOps reviewed it against decisions 35 and 40. It passes.\n"
                "Publish it web-only (decision 42)").encode()
    (tmp_path / "approval.txt").write_bytes(approval)
    (tmp_path / "authority.txt").write_bytes(approval)
    digest = sha256(raw).hexdigest()
    (tmp_path / "MANIFEST.sha256").write_text(digest + "  PREVIEW.md\n", encoding="utf-8")
    spec = {"authorship_class": "CAPITAL_CHRONICLE_OPS_APPROVED_EVENT_PREVIEW",
            "headline_id": "controlled-event-preview", "capture_path": "PREVIEW.md",
            "source_capture_sha256": digest,
            "frozen_manifest_path": str(tmp_path / "MANIFEST.sha256"),
            "approval_capture_path": "approval.txt", "approval_capture_sha256": sha256(approval).hexdigest(),
            "known_at_utc": "2026-11-02T23:35:08Z", "revision_at_utc": "2026-11-03T01:03:00Z",
            "source_url": "https://example.test/exact-authored-preview"}
    write_index(tmp_path, spec)
    return spec


def write_index(root, spec):
    (root / "index.json").write_text(json.dumps({"schema_version": "contentops.retained_source_research.v1",
                                                "records": [spec]}), encoding="utf-8")


def test_exact_public_preview_reuses_existing_source_owner(tmp_path):
    fixture(tmp_path)
    research = RetainedSourceResearch(tmp_path)
    assert not research.gaps
    rows = research.headlines(cutoff_utc="2026-11-03T02:00:00Z")
    assert len(rows) == 1
    assert research.permission_for(rows[0], "2026-11-03T02:00:00Z")
    evidence = research.evidence({"headline_ids": [rows[0]["headline_id"]]}, cutoff_utc="2026-11-03T02:00:00Z")
    assert "official_source_documents" not in evidence
    assert evidence["epistemic_state"]["event_truth_supported"] is False
    assert evidence["publication_authority"] is False
    assert evidence["provenance"]["new_external_acquisition"] is False
    restored = RetainedSourceResearch.from_frozen_snapshot(research.frozen_snapshot())
    assert restored.evidence({"headline_ids": [rows[0]["headline_id"]]}) == evidence


@pytest.mark.parametrize("change,cause", [
    ("preview", "EVENT_PREVIEW_BYTES_CHANGED"),
    ("manifest", "EVENT_PREVIEW_FROZEN_MANIFEST_MISMATCH"),
    ("approval", "EVENT_PREVIEW_APPROVAL_CHANGED"),
    ("clock", "EVENT_PREVIEW_CLOCK_ORDER_INVALID"),
    ("unreviewed", "EVENT_PREVIEW_EXACT_OPS_REVIEW_REQUIRED"),
])
def test_admission_refuses_changed_or_unreviewed_input(tmp_path, change, cause):
    spec = fixture(tmp_path)
    if change == "preview":
        (tmp_path / "PREVIEW.md").write_text("Changed source", encoding="utf-8")
    elif change == "manifest":
        (tmp_path / "MANIFEST.sha256").write_text("0" * 64 + "  PREVIEW.md\n", encoding="utf-8")
    elif change == "approval":
        (tmp_path / "approval.txt").write_text("Changed approval", encoding="utf-8")
    elif change == "clock":
        spec["known_at_utc"] = "2026-11-04T00:00:00Z"
    else:
        raw = b"No actual review"
        (tmp_path / "approval.txt").write_bytes(raw)
        spec["approval_capture_sha256"] = sha256(raw).hexdigest()
    write_index(tmp_path, spec)
    research = RetainedSourceResearch(tmp_path)
    assert not research.records
    assert research.gaps[0]["state"] == cause


@pytest.mark.parametrize("text,cause", [
    ("# Preview\n\nOur positions are private.", "PRIVATE_OR_EXECUTION_COPY_FORBIDDEN"),
    ("# Preview\n\nKalshi gives Democrats 70%.", "PREDICTION_MARKET_NUMBER_FORBIDDEN"),
    ("# Preview\n\nBuy gold now.", "PRIVATE_OR_EXECUTION_COPY_FORBIDDEN"),
])
def test_public_preview_does_not_admit_private_dossier_copy(tmp_path, text, cause):
    fixture(tmp_path, text)
    research = RetainedSourceResearch(tmp_path)
    assert not research.records
    assert research.gaps[0]["state"] == cause


def test_future_admission_stays_out_of_frozen_opportunity(tmp_path):
    fixture(tmp_path)
    research = RetainedSourceResearch(tmp_path)
    cutoff = "2026-11-03T00:00:00Z"
    assert research.headlines(cutoff_utc=cutoff) == []
    assert research.evidence({"headline_ids": ["controlled-event-preview"]}, cutoff_utc=cutoff) is None


def test_matching_approval_words_cannot_replace_actual_host_review(tmp_path):
    fixture(tmp_path)
    (tmp_path / "authority.txt").write_text("No host approval exists", encoding="utf-8")
    research = RetainedSourceResearch(tmp_path)
    assert not research.records
    assert research.gaps[0]["state"] == "EVENT_PREVIEW_REVIEW_NOT_IN_HOST_BACKLOG"


def test_caller_cannot_substitute_another_frozen_manifest(tmp_path):
    spec = fixture(tmp_path)
    other = tmp_path / "other-manifest.sha256"
    other.write_bytes((tmp_path / "MANIFEST.sha256").read_bytes())
    spec["frozen_manifest_path"] = str(other)
    write_index(tmp_path, spec)
    research = RetainedSourceResearch(tmp_path)
    assert not research.records
    assert research.gaps[0]["state"] == "EVENT_PREVIEW_HOST_ORIGIN_MISMATCH"


def test_event_numeric_admission_is_code_owned_and_source_exact(tmp_path):
    fixture(tmp_path, "# Controlled preview\n\nThe poll reports 51.1% and 42.8%. First polls close at 23:00 UTC.\n")
    record = next(iter(RetainedSourceResearch(tmp_path).records.values()))
    from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import _private
    pack = _source_pack([record["document"]])
    context = adapter.public_preview_event_evidence(pack)
    assert context["event_id"] == "US_MIDTERMS_20261103"
    assert not _private(context)
    assert {"51.1%", "42.8%", "23", "00"} <= {f["display"] for f in context["facts"].values()}
    text = record["permitted_source_text"]
    for fact in context["facts"].values():
        a, b = fact["source_span"]
        assert text[a:b].strip() == fact["display"]
    assert adapter.public_preview_chart_rights_bound(pack[0])
    rights = pack[0]["source_reuse_constraints"]
    rights["public_expression_reuse_allowed"] = False
    assert not adapter.public_preview_chart_rights_bound(pack[0])
    rights["public_expression_reuse_allowed"] = True
    pack[0]["canonical_content_text"] = "Changed writer context"
    assert not adapter.public_preview_chart_rights_bound(pack[0])
    with pytest.raises(ValueError, match="EVENT_PREVIEW_WRITER_SOURCE_CHANGED"):
        adapter.public_preview_event_evidence(pack)
    assert adapter.public_preview_event_evidence([]) is None


def test_retained_capitol_photo_requires_the_exact_federal_authorship_record():
    from copy import deepcopy
    from live_contentops.visual_asset_discovery_v1 import _validate_commons_contextual_rights
    root = Path(__file__).resolve().parents[1] / "docs/publisher/EVENT_ARTICLES_V1/midterm-20261103/media"
    asset = json.loads((root / "photo-asset-unreviewed.json").read_bytes())
    receipt = json.loads((root / "photo-rights.json").read_bytes())
    receipt["public_domain_basis"]["policy_capture_path"] = str(root / "pd-usgov-policy.json")
    digest = sha256((root / "capitol-west-front-1997.jpg").read_bytes()).hexdigest()
    _validate_commons_contextual_rights(asset, receipt, receipt["provider_metadata"], digest)
    changed = deepcopy(receipt)
    changed["provider_metadata"]["page"]["license_wikitext"] = "No retained federal authorship declaration"
    with pytest.raises(ValueError, match="PHOTO_PUBLIC_DOMAIN_BASIS_REQUIRED"):
        _validate_commons_contextual_rights(asset, changed, changed["provider_metadata"], digest)
