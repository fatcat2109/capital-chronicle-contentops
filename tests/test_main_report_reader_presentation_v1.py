from copy import deepcopy

import pytest

from live_contentops import fact_card_design_v1 as design
from live_contentops.post_visuals_v1 import build_post_data_card, validate_post_data_card
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    SimpleGeminiNewsroomError, _native_preview_bundle, _reader_safe_native_article,
)
from tests.test_post_visuals_v1 import packet


def report_article():
    article = deepcopy(packet()[0])
    article.pop("reader_first_version")
    article["title"] = "Capital Chronicle's oil review weighs competing explanations"
    text = "Capital Chronicle's review weighs supply risk; the event is not confirmed."
    for key in ("dek", "social_hook", "social_mechanism_summary", "social_policy_summary",
                "social_cross_asset_summary", "substack_body_markdown"):
        article[key] = text
    state = {"evidence_basis": "GOVERNED_CAPITAL_CHRONICLE_REPORT",
             "primary_reporting_publisher": "Capital Chronicle",
             "event_confirmation_state": "UNCONFIRMED",
             "report_scope_notice": "The event is not confirmed.",
             "reader_visible_epistemic_label": "DATED CAPITAL CHRONICLE REVIEW"}
    return article, state


def test_natural_main_attribution_reaches_all_eight_packages_without_prefix():
    article, state = report_article()
    bundle, _ = _native_preview_bundle(article=article, article_mode="DATA_OR_DOCUMENT_LENS",
        article_identity="a" * 64, epistemic_state=state, media_asset_ids=["controlled-card"])
    assert len(bundle["packages"]) == 8
    for payload in bundle["packages"].values():
        rendered = str(payload)
        assert "DATED CAPITAL CHRONICLE REVIEW" not in rendered
        assert "Capital Chronicle" in rendered
        assert "not confirmed" in rendered


def test_unattributed_title_and_relay_still_retain_reporting_label():
    article, state = report_article()
    article["title"] = "An oil supply test"
    rendered = _reader_safe_native_article(article, article_mode="DATA_OR_DOCUMENT_LENS",
        epistemic_state=state, legacy_presentation=False)
    assert rendered["title"].startswith("DATED CAPITAL CHRONICLE REVIEW | ")
    article, state = report_article()
    state.update(evidence_basis="TRUSTED_RELAY_ATTRIBUTED_REPORT",
                 primary_reporting_publisher="Reuters", reader_visible_epistemic_label="RELAYED / UNCONFIRMED")
    rendered = _reader_safe_native_article(article, article_mode="DATA_OR_DOCUMENT_LENS",
        epistemic_state=state, legacy_presentation=False)
    assert rendered["title"].startswith("RELAYED / UNCONFIRMED | ")


def test_natural_main_attribution_does_not_admit_false_event_confirmation():
    article, state = report_article()
    for key in ("dek", "social_hook", "social_mechanism_summary", "social_policy_summary",
                "social_cross_asset_summary", "substack_body_markdown"):
        article[key] = "Capital Chronicle confirmed the agreement."
    with pytest.raises(SimpleGeminiNewsroomError, match="native_preview_epistemic_certainty_inflation"):
        _native_preview_bundle(article=article, article_mode="DATA_OR_DOCUMENT_LENS",
            article_identity="b" * 64, epistemic_state=state, media_asset_ids=["controlled-card"])


@pytest.mark.parametrize("instant, expected", [
    ("2026-11-06T02:00:00Z", "November 5, 2026"),
    ("2026-07-01T02:00:00Z", "June 30, 2026"),
])
def test_main_review_date_reaches_actual_card_renderer_in_new_york(tmp_path, monkeypatch, instant, expected):
    article, claims, docs = packet()
    doc = docs[0]
    digest = "d" * 64
    doc.update(publisher="Capital Chronicle", url="urn:cc-public-report:main-retained:" + digest,
        source_authority_class="governed_capital_chronicle_report_only", published_at_utc=instant,
        report_lineage={"report_projection_sha256": digest}, source_reuse_constraints={
            "scope": "CAPITAL_CHRONICLE_OWN_REPORT_PUBLIC_EXCERPTS", "authority_ref": "JIM_DECISION_89",
            "source_capture_sha256": digest})
    drawn = []
    render = design.render_fact_card

    def capture(path, spec, **kwargs):
        drawn.append(spec.source_line)
        return render(path, spec, **kwargs)

    monkeypatch.setattr(design, "render_fact_card", capture)
    card = build_post_data_card(article, claims, docs, output_dir=tmp_path)
    validate_post_data_card(card, article, docs)
    assert drawn[-1] == f"Source: Capital Chronicle review, {expected} (ET)."
    assert card["data_card_packet"]["source_line"] == drawn[-1]


@pytest.mark.parametrize("editorial_key", [None, "2026", "65.00K"])
@pytest.mark.parametrize("source_count", ["65.00K", "65,000", "65000"])
def test_main_review_count_leads_actual_card_in_full_without_changing_source(tmp_path, monkeypatch, editorial_key, source_count):
    article, claims, docs = packet()
    text = f"Nonfarm payrolls rose by {source_count}; the unemployment rate was 4.1%."
    article.update(title="The jobs review", substack_body_markdown=text, dek=text)
    claims = [{"claim_id": "payrolls", "claim_text": text, "source_id": "SOURCE_1", "support_excerpt": text}]
    doc = docs[0]
    digest = "d" * 64
    doc.update(publisher="Capital Chronicle", url="urn:cc-public-report:main-retained:" + digest,
        canonical_content_text=text, source_authority_class="governed_capital_chronicle_report_only",
        published_at_utc="2026-11-06T14:00:00Z", report_lineage={"report_projection_sha256": digest},
        source_reuse_constraints={"scope": "CAPITAL_CHRONICLE_OWN_REPORT_PUBLIC_EXCERPTS",
            "authority_ref": "JIM_DECISION_89", "source_capture_sha256": digest})
    if editorial_key:
        article["visual_editorial_decision"]["post_data_card_plan"] = {
            "title": "The jobs review", "key_label": "Payrolls", "key_value": editorial_key,
            "facts": [{"text": text, "label": "Payrolls"}]}
    drawn = []
    render = design.render_fact_card
    def capture(path, spec, **kwargs):
        drawn.append(spec)
        return render(path, spec, **kwargs)
    monkeypatch.setattr(design, "render_fact_card", capture)
    card = build_post_data_card(article, claims, docs, output_dir=tmp_path)
    validate_post_data_card(card, article, docs)
    assert drawn[-1].key_value == "65,000"
    assert "65,000" in drawn[-1].facts[0][1] and "65.00K" not in drawn[-1].facts[0][1]
    assert card["data_card_packet"]["facts"][0]["text"] == text
    assert doc["canonical_content_text"] == text
