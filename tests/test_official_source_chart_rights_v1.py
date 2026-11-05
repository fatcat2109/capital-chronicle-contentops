"""A verified official record supplies its existing rights to the chart consumer."""
from hashlib import sha256

from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_editorial_data_chart, validate_editorial_data_chart
from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack
from tests.test_contentops_source_research_v1 import ROOT, NOW


def test_official_held_fact_reaches_chart_with_exact_capture_and_policy(tmp_path):
    research = RetainedSourceResearch(ROOT)
    record = research.records["goal20-bls-cpi-september"]
    admitted = research.evidence({"headline_ids": [record["headline_id"]]}, cutoff_utc=NOW)
    docs = _source_pack(admitted["official_source_documents"])
    doc = docs[0]
    rights = doc["source_reuse_constraints"]
    assert rights["source_capture_sha256"] == record["source_capture_sha256"]
    assert rights["policy_capture_sha256"] == record["rights_evidence_sha256"]
    excerpt = doc["canonical_content_text"]
    assert "0.6" in excerpt and "September" in excerpt
    packet = {"asset_id": "controlled-held-cpi", "chart_type": "grouped_bar", "title": "September CPI",
        "subtitle": "Controlled retained source", "question": "What was the reported monthly change?",
        "unit": "Percent", "placement_after": "Reported change", "source_caption": "U.S. Bureau of Labor Statistics",
        "series": [{"name": "CPI monthly change", "points": [{"period": "2026-09", "value": 0.6,
            "observation_kind": "REPORTED_ACTUAL", "inputs": [{"document_id": doc["document_id"],
                "source_content_sha256": sha256(excerpt.encode()).hexdigest(), "support_excerpt": excerpt,
                "value_text": "0.6", "source_period_text": "September", "prepared_period": "2026-09",
                "metric": "CPI monthly change", "unit": "Percent", "period_basis": {"kind": "RETAINED_EXACT_RELEASE"}}]}]}]}
    asset = build_editorial_data_chart(packet, docs, output_dir=tmp_path)
    validate_editorial_data_chart(asset, docs)
    assert asset["computed_values"] == [[0.6]]
