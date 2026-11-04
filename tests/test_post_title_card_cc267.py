"""CC-267: a NEWS/POLICY post with no admitted public fact still publishes, with a title card.

Local synthetic contracts; the fixtures are neither posts nor MAX reviews.
"""
import json
import re
from pathlib import Path

import pytest
from PIL import Image

from live_contentops.post_visuals_v1 import (
    POLICY, DESTINATIONS, TITLE_CARD, build_post_data_card, card_title,
    complete_post_visuals, require_publication_image, validate_post_data_card,
)
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.native_desktop_editorial_v1 import validate_release_media
from live_contentops.v1_simple_gemini_newsroom_v1 import _native_preview_bundle
from test_post_visuals_v1 import packet

ISM_TITLE = "ISM services index rises to 52.4 as prices paid climb"
ISM_CARD_TITLE = "ISM services index rises as prices paid climb"
ISM_URL = "https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/services/october/"


TITLE_CASES = [
    # Ops Product's 5 Nov check. The two that read wrong first:
    ("S&P Global US services PMI 54.8 vs 55.2 expected", "S&P Global US services PMI"),
    ("US layoffs hit 153,074 in October, highest since 2020, Challenger says", "Challenger job cuts: October report"),
    # ...and those that read fine (inputs rebuilt from the outputs in the check).
    ("Challenger job cuts fall 18% to 125,000 in October", "Challenger job cuts fall in October"),
    ("ADP: private payrolls rise 42,000 in October, beating forecast",
     "ADP: private payrolls rise in October, beating forecast"),
    ("ISM manufacturing PMI slips to 48.7, eighth month of contraction",
     "ISM manufacturing PMI slips, eighth month of contraction"),
    ("ADP: hiring slows to 42,000, wages rise 4.5%", "ADP: hiring slows, wages rise"),
    (ISM_TITLE, ISM_CARD_TITLE),
    ("Challenger job cuts jump 183% to 153,074 in October", "Challenger job cuts jump in October"),
    ("S&P Global flash PMI slips to 51.2 (52.0 expected)", "S&P Global flash PMI slips"),
    ("UMich sentiment falls to 50.3, lowest since 2022, survey shows",
     "UMich sentiment falls, lowest since 2022, survey shows"),
    ("Prices paid at 70.0 keep pressure on the Fed", "Prices paid keep pressure on the Fed"),
    ("52.4: what the ISM services reading says", "What the ISM services reading says"),
    ("Conference Board confidence drops 5.4 points to 94.6", "Conference Board confidence drops"),
    ("Yields climb 12bp after ISM", "Yields climb after ISM"),
    ("Q3 GDP grows 2.8% annualised", "Q3 GDP grows"),
    # A verb that lost its object, a lone 'consensus' or a one-word clause falls back.
    ("ADP: hiring slows to +42k, wages +4.5%", "ADP: hiring slows"),
    ("ISM services PMI tops 55 for first time since 2024", "ISM services PMI: latest report"),
    ("UMich sentiment 50.3 vs 51.0 consensus", "UMich consumer sentiment: latest report"),
    ("Private payrolls add 42,000 in October", "Capital Chronicle news brief"),
    # Dates, maturities, index and legal names keep their numbers.
    ("The Fed held on October 28. Both dissenters wanted a hike.",
     "The Fed held on October 28. Both dissenters wanted a hike."),
    ("September 2026 jobs: private gains beneath a weak headline",
     "September 2026 jobs: private gains beneath a weak headline"),
    ("S&P 500 falls 1.2% as 10-year yield rises to 4.3%", "S&P 500 falls as 10-year yield rises"),
    ("Trump expands Section 232 steel tariffs to 50%", "Trump expands Section 232 steel tariffs"),
]


@pytest.mark.parametrize("title, expected", TITLE_CASES)
def test_card_title_reads_cleanly_without_figures(title, expected):
    shown = card_title({"title": title})
    assert shown == expected
    kept = re.findall(r"October 28|2026|2024|2022|2020|10-year|S&P 500|Section 232|Q3", title)
    figures = [f for f in re.findall(r"[-+]?\d[\d,.]*\d|\d", title) if not any(f in k for k in kept)]
    assert not any(re.search(r"(?<![\d.,])" + re.escape(f) + r"(?![\d.,])", shown) for f in figures)
    assert not re.search(r"\b(?:since|vs|than)\s*(?:[,.;:]|$)", shown)


def test_card_title_falls_back_to_the_clean_dek_before_a_release_title():
    article = {"title": "US layoffs hit 153,074 in October",
               "dek": "Employers announced 153,074 job cuts in October, the most since 2020."}
    assert card_title(article) == "Employers announced job cuts in October, the most since 2020."
    article["dek"] = "Challenger said layoffs hit 153,074."
    assert card_title(article) == "Challenger job cuts: October report"


def ism_only_packet():
    """The public fixture, published by a private survey: decision 44 admits no card fact."""
    article, claims, docs = packet()
    docs[0].update(publisher="Institute for Supply Management", url=ISM_URL)
    article["title"] = ISM_TITLE
    article["visual_editorial_decision"]["story_kind"] = "NEWS"
    return article, claims, docs


def test_private_survey_post_gets_one_title_card_through_every_release_check(tmp_path):
    article, claims, docs = ism_only_packet()
    with pytest.raises(ValueError, match="NO_ADMITTED_PUBLIC_VISUAL_FACTS"):
        build_post_data_card(article, claims, docs, output_dir=tmp_path)  # unchanged contract
    article, assets = complete_post_visuals(article, claims, docs, [], output_dir=tmp_path)
    assert len(assets) == 1
    card = assets[0]
    card_packet = card["data_card_packet"]
    assert card["modality"] == "source_bound_data_card" and card["card_kind"] == "TITLE_ONLY"
    assert card_packet == {"policy": POLICY, "kind": TITLE_CARD, "facts": [], "design": card_packet["design"],
                           "title": ISM_CARD_TITLE, "dated_line": "Capital Chronicle"}
    assert card["title_card_reason"] == "DATA_CARD_NO_ADMITTED_PUBLIC_VISUAL_FACTS"
    # No survey figure anywhere the card or its text shows.
    for text in (card_packet["title"], card_packet["dated_line"], card["caption"], card["alt_text"]):
        assert not re.search(r"\d", text)
    assert card["source_links"] == [] and card["source_lineage"][0]["source_url"] == ISM_URL
    with Image.open(card["path"]) as pixels:
        assert pixels.size == (1080, 1350)
    validate_post_data_card(card, article, docs)
    counts = validate_release_media({"article": article, "media_assets": assets, "evidence": docs})
    assert counts["data_card_count"] == 1 and counts["photo_count"] == 0
    assert article["post_visual_destination_media"] == {d: [card["asset_id"]] for d in DESTINATIONS}
    bundle, _ = _native_preview_bundle(article=article, article_mode="BREAKING_BRIEF", article_identity="c" * 64,
        media_assets=assets, media_asset_ids=[card["asset_id"]])
    assert len(bundle["packages"]) == 8
    assert all(p["media_asset_ids"] == [card["asset_id"]] for p in bundle["packages"].values())
    for destination in ("x", "telegram", "linkedin", "youtube"):
        require_publication_image(destination, {"media_assets": assets, "payloads": bundle["packages"]})


def test_title_card_is_checked_and_a_fact_card_still_is_checked_as_today(tmp_path):
    article, claims, docs = ism_only_packet()
    article, assets = complete_post_visuals(article, claims, docs, [], output_dir=tmp_path / "title")
    card = assets[0]

    def resealed(change):
        changed = json.loads(json.dumps(card))
        change(changed["data_card_packet"])
        changed["transform_sha256"] = sha256_of(changed["data_card_packet"])
        return changed

    with pytest.raises(ValueError, match="DATA_CARD_TITLE_CARD_CHANGED"):
        validate_post_data_card(card, {**article, "title": "A different headline for this post"}, docs)
    with pytest.raises(ValueError, match="DATA_CARD_TITLE_CARD_CHANGED"):
        validate_post_data_card(resealed(lambda p: p.update(title=ISM_TITLE)), article, docs)
    with pytest.raises(ValueError, match="DATA_CARD_TITLE_CARD_CHANGED"):
        validate_post_data_card(resealed(lambda p: p["facts"].append({"text": "The index rose to 52.4."})),
                                article, docs)
    with pytest.raises(ValueError, match="DATA_CARD_TITLE_CARD_CHANGED"):
        validate_post_data_card(resealed(lambda p: p.update(dated_line="Elsewhere")), article, docs)
    with pytest.raises(ValueError, match="DATA_CARD_PACKET_REQUIRED"):
        validate_post_data_card(resealed(lambda p: p.pop("kind")), article, docs)
    with pytest.raises(ValueError, match="DATA_CARD_PACKET_OR_BYTES_CHANGED"):
        validate_post_data_card({**card, "transform_sha256": "0" * 64}, article, docs)
    Path(card["path"]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="DATA_CARD_PACKET_OR_BYTES_CHANGED"):
        validate_post_data_card(card, article, docs)
    # A public fact card is unchanged: no title kind, its facts rebound as before, and it
    # cannot pass as a title card to skip that check.
    public, public_claims, public_docs = packet()
    fact_card = build_post_data_card(public, public_claims, public_docs, output_dir=tmp_path / "facts")
    assert "kind" not in fact_card["data_card_packet"] and len(fact_card["data_card_packet"]["facts"]) == 2
    validate_post_data_card(fact_card, public, public_docs)
    disguised = json.loads(json.dumps(fact_card))
    disguised["data_card_packet"]["kind"] = TITLE_CARD
    disguised["transform_sha256"] = sha256_of(disguised["data_card_packet"])
    with pytest.raises(ValueError, match="DATA_CARD_TITLE_CARD_CHANGED"):
        validate_post_data_card(disguised, public, public_docs)


def test_a_card_that_cannot_be_built_never_stops_the_run(tmp_path):
    # A series the owner rejects falls back to the facts alone.
    article, claims, docs = packet()
    article["visual_editorial_decision"]["data_card_series"] = {
        "series": [{"points": [{"value": "120", "inputs": [{"document_id": "not-in-this-post"}]}]}]}
    article, assets = complete_post_visuals(article, claims, docs, [], output_dir=tmp_path / "series")
    assert len(assets[0]["data_card_packet"]["facts"]) == 2
    assert "series_asset" not in assets[0]["data_card_packet"]
    assert assets[0]["series_dropped_reason"] == "DATA_CARD_SERIES_SOURCE_REQUIRED"
    validate_post_data_card(assets[0], article, docs)
    # A claim without a source stopped the card builder; the post now takes the title card.
    article, claims, docs = packet()
    claims[0]["source_id"] = None
    article, assets = complete_post_visuals(article, claims, docs, [], output_dir=tmp_path / "unsourced")
    assert assets[0]["card_kind"] == "TITLE_ONLY"
    assert assets[0]["title_card_reason"] == "DATA_CARD_FACT_SOURCE_REQUIRED"
    assert validate_release_media({"article": article, "media_assets": assets, "evidence": docs})["data_card_count"] == 1
    # Analysis keeps its own chart requirement: no card is made for it here.
    article, claims, docs = packet()
    article["visual_editorial_decision"]["story_kind"] = "ANALYSIS"
    with pytest.raises(ValueError, match="EVERY_POST_IMAGE"):
        complete_post_visuals(article, claims, docs, [], output_dir=tmp_path / "analysis")


_ISM_TEXT = {
    "Nvidia financing plan leaves commitment details undisclosed": ISM_TITLE,
    "Nvidia described a large financing plan but did not disclose individual commitments or a deployment timetable.":
        "The Institute for Supply Management said its services index rose to 52.4 in October from 50.0 in September.",
    "The company said the financing framework would support data centres, chip factories and power infrastructure.":
        "The ISM said prices paid climbed to 70.0, the highest reading since 2022.",
    "The disclosed aggregate scale did not include project-by-project funding schedules.":
        "Respondents cited tariffs and slower hiring.",
    "Nvidia financing plan: what remains undisclosed": "ISM services: what the prices paid reading signals",
    "The financing framework leaves individual commitments and deployment timing unclear.":
        "Prices paid and hiring matter more than the headline index.",
    "The headline number is large; the missing commitment detail matters more.":
        "The headline index matters less than prices paid.",
    "Nvidia financing plan current": "ISM services index current",
    "https://www.reuters.com/technology/nvidia-financing-plan": ISM_URL,
    "reuters.com": "ismworld.org",
    "Reuters": "Institute for Supply Management",
}


def _ism(value):
    text = json.dumps(value)
    for old, new in _ISM_TEXT.items():
        text = text.replace(old, new)
    return json.loads(text)


def test_ism_only_news_post_runs_through_the_newsroom_with_its_title_card(tmp_path):
    """Acceptance: run_v1_simple_gemini_newsroom reaches a post whose one card shows the
    title and date and no survey figure (before CC-267 the run stopped here)."""
    from test_v1_simple_gemini_newsroom_v1 import (
        _headlines, _candidate_ids, _selection, _article_output, _evidence_result, CUTOFF,
    )
    from live_contentops.v1_simple_gemini_newsroom_v1 import run_v1_simple_gemini_newsroom
    from live_contentops.nine_router_llm_seam_v2 import ROLE_V1_SIMPLE_SELECTION
    rolling = _ism(_headlines(1))
    selected = _selection(*_candidate_ids(rolling))
    selected["ordered_candidate_plan"][0]["article_mode"] = "BREAKING_BRIEF"
    visual = ism_only_packet()[0]["visual_editorial_decision"]

    class ControlledNative:
        native_desktop_protocol = True

        def frozen_request(self, stage):
            return None

        def __call__(self, **kwargs):
            if kwargs["role_task_id"] == ROLE_V1_SIMPLE_SELECTION:
                output = selected
            else:
                output = _ism(_article_output())
                output["article"].update(reader_first_version="DATA_JOURNALISM_V1", visual_editorial_decision=visual)
            return output, {"provider": "NATIVE_CODEX_DESKTOP", "selected_model": "gpt-6.1-sol",
                "reasoning_effort": "max", "observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF"}

        def admitted_editorial_media(self):
            return []

        def telemetry(self):
            return {"observations": [{"observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF"}]}

    def evidence(request):
        result = _ism(_evidence_result())
        # Even with reuse terms on file, a private survey's figures never reach a card (decision 44).
        result["evidence_documents"][0]["source_reuse_constraints"] = packet()[2][0]["source_reuse_constraints"]
        return result

    result = run_v1_simple_gemini_newsroom(output_dir=tmp_path, cutoff_utc=CUTOFF, rolling_input=rolling,
        llm_invoke=ControlledNative(), evidence_loader=evidence, run_id="controlled-ism-title-card")
    assert result["qualified_article_count"] == 1
    cards = [a for a in result["media_assets"] if a["modality"] == "source_bound_data_card"]
    assert len(cards) == 1 and cards[0]["card_kind"] == "TITLE_ONLY"
    shown = cards[0]["data_card_packet"]
    assert shown["title"] == ISM_CARD_TITLE and shown["facts"] == []
    assert shown["dated_line"].startswith("Capital Chronicle")
    for figure in ("52.4", "50.0", "70.0"):
        assert figure not in json.dumps(shown) and figure not in cards[0]["alt_text"]
    article = json.loads((tmp_path / "article_manifest_v1.json").read_bytes())
    assert article["post_visual_policy"] == POLICY
    assert "52.4" in json.dumps(article)  # the post itself keeps the attributed figure
    previews = json.loads((tmp_path / "native_derivative_previews_v1.json").read_bytes())
    assert all(p["media_asset_ids"] == [cards[0]["asset_id"]] for p in previews["packages"].values())
    assert result["publication_lifecycle_plan"]["skipped_derivative_destinations"] == []
