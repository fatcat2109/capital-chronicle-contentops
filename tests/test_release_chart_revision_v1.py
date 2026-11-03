"""Isolated exact-object revisions; synthetic fixtures are no publication proof."""
from copy import deepcopy
from hashlib import sha256
import json

import pytest

from test_official_release_history_v1 import archive, load  # noqa: F401
from test_reader_presentation_revision_v1 import revised  # noqa: F401
from live_contentops.official_release_history_v1 import history_documents, history_chart_packet
from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_editorial_data_chart
from live_contentops.release_chart_revision_v1 import POLICY
from live_contentops.native_desktop_editorial_v1 import build_reader_presentation_revision, reader_presentation_revision_view
from live_contentops.visual_asset_discovery_v1 import _contextual_license_url


@pytest.fixture
def chart_revision(archive, revised, tmp_path, monkeypatch):  # noqa: F811 - shared pytest fixtures
    store, run, result, footer_proposal, _ = revised
    history = load(archive)
    history["components"] = {"table_id": "cpipress6", "source_url": "https://www.bls.gov/news.release/archives/cpi_10142026.htm#cpipress6",
        "capture_sha256": "c"*64, "release_datetime_utc": history["cutoff_utc"], "period": "2026-09",
        "effects": [{"name": "Energy", "official_series_id": "CUSR0000SA0E", "period": "2026-09",
            "native_value": "0.1", "value": 0.1, "unit": "percentage points", "seasonal_adjustment": "SA"}]}
    monkeypatch.setattr("live_contentops.official_release_history_v1.load_cc010_history", lambda *a, **kw: deepcopy(history))
    docs = history_documents(history)
    assets, choices = [], []
    for i, names in enumerate((("CPI_HEADLINE_MOM", "CPI_CORE_MOM"), ("CPI_HEADLINE_YOY", "CPI_CORE_YOY"))):
        packet = history_chart_packet(history, series_names=names, asset_id=f"controlled-cpi-{i}",
            title="Controlled", question=f"Controlled distinct question {i}", placement_after=f"Section {i}")
        assets.append(build_editorial_data_chart(packet, docs, output_dir=tmp_path / "controlled-media"))
        choices.append({"asset_id": packet["asset_id"], "question": packet["question"], "why_useful": "Controlled",
            "placement_after": packet["placement_after"], "data_spec": {"source": "CONTROLLED"}})
    packet = deepcopy(packet)
    doc = docs[-1]
    packet.update(asset_id="controlled-effect", chart_type="grouped_bar", question="Controlled effect", unit="percentage points",
        placement_after="Section 2", history_lineage=None, component_lineage=history["components"], series=[{
            "name": "Controlled effect", "points": [{"period": "2026-09", "value": 0.1,
                "observation_kind": "REPORTED_ACTUAL", "inputs": [{"document_id": doc["document_id"],
                    "support_excerpt": doc["canonical_content_text"], "value_text": "0.1", "source_period_text": "2026-09",
                    "source_content_sha256": doc["canonical_content_sha256"], "metric": "Energy", "unit": "percentage points",
                    "prepared_period": "2026-09", "period_basis": {"basis": "CONTROLLED"}}]}]}])
    assets.append(build_editorial_data_chart(packet, docs, output_dir=tmp_path / "controlled-media"))
    choices.append({"asset_id": packet["asset_id"], "question": packet["question"], "why_useful": "Controlled",
        "placement_after": "Section 2", "data_spec": {"source": "CONTROLLED"}})
    for a in assets:
        a["visual_review"] = {"asset_sha256": a["sha256"], "pixels_inspected": True,
            "labels_and_units_legible": True, "reviewer": "CONTROLLED_TEST_NOT_VISUAL_PROOF"}
    body = "\n\n".join(["## Section 0", "Controlled history.", "## Section 1", "Controlled pace.",
        "## Section 2", "Controlled effects.", "Analysis, not financial advice. Readers decide whether to trade."])
    request = tmp_path / "controlled-writer-request.json"
    request.write_text('{"controlled": true}', encoding="utf-8")
    request_sha = sha256(request.read_bytes()).hexdigest()
    response = tmp_path / "controlled-writer-response.json"
    response.write_text(json.dumps({"request_sha256": request_sha, "revised_article_markdown": "# Controlled title\n\n"+body}), encoding="utf-8")
    decision = {"reader_first_version": "DATA_JOURNALISM_V1", "story_kind": "ANALYSIS", "editorial_thesis": "Controlled",
        "charts": choices, "channel_media": {p["destination"]: [] for p in result["previews"]}}
    proposal = {"policy": POLICY, "run_id": run, "article_identity": result["article_identity"],
        "article": {**result["article"], "news_item_kind": "ANALYSIS", "substack_body_markdown": body,
            "visual_editorial_decision": decision}, "visual_editorial_decision": decision,
        "official_history": history, "additional_evidence": docs, "media_assets": assets,
        "objects": {"substack": footer_proposal["canonical_amendment"]["existing_public_identity"]},
        "amendment_writer": {"request_path": str(request), "request_sha256": request_sha,
            "response_path": str(response), "response_sha256": sha256(response.read_bytes()).hexdigest(),
            "invocation_observation": {"surface": "CODEX_NATIVE_SUBAGENT", "invocation_id": "CONTROLLED_NEW_MAX",
                "model": "gpt-6.1-sol", "reasoning_effort": "max"}}}
    return store, run, result, proposal


def test_same_confirmed_object_gets_reviewable_charts_without_mutating_sent_packet(chart_revision):
    store, run, result, proposal = chart_revision
    before = deepcopy(result)
    revision = build_reader_presentation_revision(store, run_id=run, proposal=proposal,
        owner_authority_ref="human:JIM_DECISIONS_20261030_DECISION_41_CC142")
    view = reader_presentation_revision_view(store, run_id=run, result=result, revision=revision)
    assert result == before and len(view["media_assets"]) == 3
    assert revision["objects"]["substack"]["public_object_id"] == "123"
    assert len(view["evidence"]) == len(result["evidence"]) + 5
    store.set_dispatch_status("dispatch-substack", "UNKNOWN_WRITE")
    with pytest.raises(ValueError, match="EXACT_CONFIRMED_OBJECT"):
        reader_presentation_revision_view(store, run_id=run, result=result, revision=revision)


@pytest.mark.parametrize("fault", ["authority", "title", "history", "writer", "no_charts"])
def test_revision_rejects_unbound_authority_copy_history_and_writer(chart_revision, fault):
    store, run, result, proposal = chart_revision
    authority = "human:JIM_DECISIONS_20261030_DECISION_41_CC142"
    if fault == "authority":
        authority = "human:UNRELATED"
    if fault == "title":
        proposal["article"]["title"] = "Another post"
    if fault == "history":
        proposal["additional_evidence"][0]["canonical_content_text"] += " changed"
    if fault == "writer":
        proposal["amendment_writer"]["response_sha256"] = "e"*64
    if fault == "no_charts":
        proposal["media_assets"] = []
    with pytest.raises(ValueError, match="CHART_REVISION_"):
        build_reader_presentation_revision(store, run_id=run, proposal=proposal, owner_authority_ref=authority)


def test_usda_public_domain_subtype_requires_the_same_exact_policy_and_metadata(tmp_path):
    p = tmp_path / "CONTROLLED_POLICY.json"
    url = "https://commons.wikimedia.org/wiki/Template:PD-USGov"
    p.write_text(json.dumps({"status": "PASS", "final_url": url,
        "retrieval_method": "READ_ONLY_BROWSEROS_NEO_PUBLIC_LICENSE",
        "canonical_content_text": "Public domain United States Federal Government official duties Section 105",
        "credential_or_session_material_read": False, "public_write_performed": False}))
    receipt = {"public_domain_basis": {"policy_url": url, "policy_capture_path": str(p),
        "policy_capture_sha256": sha256(p.read_bytes()).hexdigest()}}
    meta = {"License": {"value": "pd"}, "LicenseShortName": {"value": "Public domain"}, "Copyrighted": {"value": "False"}}
    provider = {"page": {"license_wikitext": "{{PD-USGov-USDA}}"}}
    assert _contextual_license_url(receipt, provider, meta) == url
    provider["page"]["license_wikitext"] = "{{UNKNOWN_FREE_IMAGE}}"
    with pytest.raises(ValueError, match="PUBLIC_DOMAIN_BASIS_REQUIRED"):
        _contextual_license_url(receipt, provider, meta)
