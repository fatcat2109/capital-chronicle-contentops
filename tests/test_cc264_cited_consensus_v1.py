"""CC-264 (Jim's decision 72 b): articles cite the consensus with its source and date and carry our model outputs.

ContentOps' guards follow CC-262's rule. Consensus, forecast, surprise, beat, miss and gamma are ordinary words; DEMO
identifiers, broker servers, lot sizes, R multiples, prediction-market numbers and unconditional calls stay refused;
every number stays bound to a citation or a model output (host rule 7). Inputs are CC-262's regenerated 1.4.0 fixture
(the 5 Nov replay of real inputs, marked as a fixture) and synthetic event packets; nothing is published.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_desk_record_source_v1 import read_export, validate_article_citations
from live_contentops.event_article_guard_v1 import (
    CONFLICTS_NOTICE, PublicOutputError, check_public_event_article, cited_date_pattern,
    public_execution_copy_forbidden,
)
from tests.test_event_article_guard_v1 import packet
from tools.product.desk_record_projection_v1 import MODEL_ESTIMATE_NOTICES, public_text_problems

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/desk_record_export_v1/desk_record_export_v1_4.fixture.json"
CUTOFF = "2026-11-05T12:00:00Z"
# Git blob of tools/product/desk_record_projection_v1.py in the Main repository at CC-262's head 3bad55b22.
CANONICAL_PROJECTION_BLOB = "8335ad95f81d2b6de970e20e5f716b1a7da4d5af"

NFP_CONSENSUS = "event:US_NFP_20261106/consensus_citation/value"
SEP_ANCHOR = ("event:US_NFP_20261106/expectation_anchors/"
              "fomc:unemployment_rate:2026:percent_q4_average:2026-09-16/value")
US500_REGIME = "asset:US500/options_positioning/regime"
NFP_PARAGRAPH = ("Investing.com's consensus for October nonfarm payrolls is 63 thousand jobs, observed on 4 November. "
                 "A print well above it would be a beat that could lift yields; a miss would revive the case for a cut.")
SEP_SENTENCE = ("The Federal Reserve Board FOMC Summary of Economic Projections, released 16 September, put the "
                "unemployment rate at 4.1 percent for the fourth quarter.")
REGIME_SENTENCE = ("Capital Chronicle model estimate: the S&P 500 options regime is negative gamma, which can amplify "
                   "a move after the release in either direction. " + " ".join(MODEL_ESTIMATE_NOTICES))
NOTES = "Fixture, not current data. Analysis, not financial advice."


# --- the canonical projection copy --------------------------------------------------------------------------------

def test_projection_copy_is_cc262s_canonical_file():
    data = (ROOT / "tools/product/desk_record_projection_v1.py").read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() == CANONICAL_PROJECTION_BLOB


# CC-262's acceptance texts (Main tests/test_desk_record_model_estimates_v1.py), run against ContentOps' copy.
PASS = [
    "payrolls 175,000 vs consensus 175,000 (Bloomberg survey)",
    "Our forecast for CPI is 0.3%",
    "Positive gamma regime, flip at 6800",
    "Payrolls consensus 63k (Investing.com, 4 Nov 2026).",
    "Payrolls came in line with the consensus; a beat or a miss of 50k would move USDJPY.",
    "Payrolls ran 112.5 thousand above expectations, a surprise.",
    "Dealer gamma was negative into the week; GEX turned positive near 6,850.",
    "Kalshi traders leaned toward a hold before the 10 Nov release.",
]
FAIL = [
    ("Our DEMO login 279805139 holds the position.", "DEMO"),
    ("Orders route to Exness-MT5Trial8.", "broker server"),
    ("We bought 0.10 lots of gold.", "lot size"),
    ("The trade lost 0.8R after the release.", "R multiple"),
    ("Kalshi priced a 62% chance of a hold.", "prediction-market number"),
    ("6800 strike: open interest 12,345 contracts, implied volatility 18.4%.", "option-chain row"),
]


@pytest.mark.parametrize("text", PASS)
def test_canonical_check_passes_consensus_figures_and_model_levels(text):
    assert public_text_problems(text) == [], text


@pytest.mark.parametrize("text,kind", FAIL, ids=[k for _, k in FAIL])
def test_canonical_check_refuses_demo_identifiers_and_raw_rows(text, kind):
    assert any(kind in p for p in public_text_problems(text)), text


# --- desk-record articles (the newsroom's MAIN_DESK_RECORD_FIELDS route) --------------------------------------------

@pytest.fixture(scope="module")
def records():
    raw = FIXTURE.read_bytes()
    return read_export({"path": str(FIXTURE), "sha256": hashlib.sha256(raw).hexdigest(),
                        "allow_fixture_private_preview": True}, cutoff_utc=CUTOFF)


def field(records, tail):
    return next(f for r in records for f in r["binding"]["fields"] if f["citation"].endswith("#" + tail))


def desk_article(records, body, *tails, title="October payrolls preview: what a beat or a miss would mean"):
    cites = [{k: f[k] for k in ("citation", "value", "display", "decimals", "unit") if k in f}
             for f in (field(records, tail) for tail in tails)]
    return {"title": title, "substack_body_markdown": body, "desk_record_citations": cites}


def test_the_export_carries_one_cited_consensus_figure_with_its_source_and_date(records):
    nfp = field(records, NFP_CONSENSUS)
    assert (nfp["display"], nfp["unit"], nfp["rights_class"], nfp["use_label"]) == (
        "63", "thousands_of_jobs", "CITED_THIRD_PARTY_FACT", "PUBLIC_WITH_ATTRIBUTION")
    assert (nfp["cited_provider"], nfp["cited_on"]) == ("Investing.com", "2026-11-04")
    assert all(not f.get("rights_class", "").endswith("PRIVATE_ONLY") for r in records for f in r["binding"]["fields"])


def test_nfp_preview_prints_the_consensus_with_its_source_and_date(records):
    article = desk_article(records, NFP_PARAGRAPH + " " + NOTES, NFP_CONSENSUS)
    result = validate_article_citations(article, records)
    assert result["citation_count"] == 1
    assert result["required_source_ids"] == ["src:cite:investing:us_nfp_20261106"]


def test_a_cited_official_expectation_passes_like_a_cited_consensus(records):
    sep = field(records, SEP_ANCHOR)
    assert (sep["display"], sep["cited_on"], sep["cited_label"]) == ("4.1", "2026-09-16", "Cited official expectation")
    body = " ".join((NFP_PARAGRAPH, SEP_SENTENCE, NOTES))
    assert validate_article_citations(desk_article(records, body, NFP_CONSENSUS, SEP_ANCHOR), records)[
        "citation_count"] == 2
    with pytest.raises(ValueError, match="DESK_ARTICLE_CITED_FACT_DATE_REQUIRED"):
        validate_article_citations(desk_article(records, body.replace(", released 16 September,", ""),
                                                NFP_CONSENSUS, SEP_ANCHOR), records)


@pytest.mark.parametrize("change,error", [
    ((", observed on 4 November", ""), "DESK_ARTICLE_CITED_FACT_DATE_REQUIRED"),
    (("4 November", "5 November"), "DESK_ARTICLE_CITED_FACT_DATE_REQUIRED"),
    (("Investing.com's consensus", "The consensus"), "DESK_ARTICLE_SOURCE_ATTRIBUTION_REQUIRED"),
])
def test_a_cited_figure_without_its_source_or_date_is_refused(records, change, error):
    body = (NFP_PARAGRAPH + " " + NOTES).replace(*change)
    with pytest.raises(ValueError, match=error):
        validate_article_citations(desk_article(records, body, NFP_CONSENSUS), records)


def test_only_the_cited_figures_own_date_is_part_of_its_citation(records):
    body = NFP_PARAGRAPH.replace("observed on 4 November", "observed on 4 November before the 6 November release")
    with pytest.raises(ValueError, match="DESK_ARTICLE_UNBOUND_OR_CHANGED_NUMBER"):
        validate_article_citations(desk_article(records, body + " " + NOTES, NFP_CONSENSUS), records)


def test_the_us500_gex_regime_reaches_an_article_with_its_model_estimate_label_and_notices(records):
    regime = field(records, US500_REGIME)
    assert regime["display"] == "NEGATIVE" and regime["rights_class"] == "CC_MODEL_ESTIMATE"
    assert regime["estimate_label"] == "Capital Chronicle model estimate"
    body = " ".join((NFP_PARAGRAPH, REGIME_SENTENCE, NOTES))
    assert validate_article_citations(desk_article(records, body, NFP_CONSENSUS, US500_REGIME), records)[
        "citation_count"] == 2


@pytest.mark.parametrize("change,error", [
    (("Capital Chronicle model estimate: the", "The"), "DESK_ARTICLE_MODEL_ESTIMATE_LABEL_REQUIRED"),
    ((CONFLICTS_NOTICE, ""), "DESK_ARTICLE_MODEL_ESTIMATE_NOTICES_REQUIRED"),
])
def test_a_model_output_without_its_label_or_notices_is_refused(records, change, error):
    body = " ".join((NFP_PARAGRAPH, REGIME_SENTENCE.replace(*change), NOTES))
    with pytest.raises(ValueError, match=error):
        validate_article_citations(desk_article(records, body, NFP_CONSENSUS, US500_REGIME), records)


def test_approved_notice_uses_the_held_model_output_without_changing_its_source(records):
    body = " ".join((NFP_PARAGRAPH, REGIME_SENTENCE, NOTES))
    assert validate_article_citations(desk_article(records, body, NFP_CONSENSUS, US500_REGIME), records)["citation_count"] == 2
    assert field(records, US500_REGIME)["notices"][-1] == CONFLICTS_NOTICE
    with pytest.raises(ValueError, match="DESK_ARTICLE_PRIVATE_OR_RAW_TEXT"):
        validate_article_citations(desk_article(records, body + " Account number 279805139.", NFP_CONSENSUS, US500_REGIME), records)


@pytest.mark.parametrize("title", [
    "Payrolls preview: consensus, forecast and the surprise", "A beat or a miss against the consensus",
    "Negative gamma into the jobs report", "Will payrolls come in line with consensus?",
])
def test_consensus_forecast_surprise_beat_miss_and_gamma_are_ordinary_words(records, title):
    article = desk_article(records, NFP_PARAGRAPH + " " + NOTES, NFP_CONSENSUS, title=title)
    assert validate_article_citations(article, records)["citation_count"] == 1


@pytest.mark.parametrize("extra,error", [
    ("Our DEMO account balance rose.", "DESK_ARTICLE_PRIVATE_OR_RAW_TEXT"),
    ("Orders route to Exness-MT5Trial8.", "DESK_ARTICLE_PRIVATE_OR_RAW_TEXT"),
    ("Kalshi priced a 62% chance of a hold.", "DESK_ARTICLE_PRIVATE_OR_RAW_TEXT"),
    # The raw consensus table (CC-068's Myfxbook rows): never cited fields, so never bound numbers.
    ("Myfxbook lists payrolls 65, unemployment 4.2, earnings 0.3 and 2.9.", "DESK_ARTICLE_UNBOUND_OR_CHANGED_NUMBER"),
])
def test_demo_identifiers_kalshi_numbers_and_raw_consensus_tables_are_refused(records, extra, error):
    body = " ".join((NFP_PARAGRAPH, extra, NOTES))
    with pytest.raises(ValueError, match=error):
        validate_article_citations(desk_article(records, body, NFP_CONSENSUS), records)


# --- event previews and reviews (CC-107's guard) -------------------------------------------------------------------

def admit(evidence, ref, display, *, rights="CITED_THIRD_PARTY_FACT", **extra):
    evidence["facts"][ref] = {
        "display": display, "source_ref": "https://source.invalid/cc264-synthetic", "source_sha256": "b" * 64,
        "known_at_utc": "2026-11-04T17:10:51Z", "rights_class": rights, "public_use_allowed": True,
        "rights_evidence_ref": "JIM_DECISION_72B/HOST_RULE_7_CITATIONS", "use_label": "PUBLIC_WITH_ATTRIBUTION",
        **extra}
    return evidence["facts"][ref]


def put(article, section, text, figure, ref):
    article["copy"][section] = text
    start = text.index(figure)
    article["numeric_bindings"].append({"copy_path": "copy." + section, "start": start,
                                        "end": start + len(figure), "evidence_ref": ref})


CONSENSUS_TEXT = ("Investing.com's consensus for October payrolls is 63,000 jobs, observed on 4 November; a beat or a "
                  "miss against it is the surprise the market will trade.")


def consensus_packet():
    article, evidence = packet()
    admit(evidence, "nfp-consensus", "63,000", attribution="Investing.com", cited_on="2026-11-04")
    put(article, "context", CONSENSUS_TEXT, "63,000", "nfp-consensus")
    return article, evidence


def refused(article, evidence, cause):
    with pytest.raises(PublicOutputError) as failure:
        check_public_event_article(article, evidence=evidence)
    assert failure.value.cause == cause
    return failure.value


def test_event_preview_prints_the_consensus_with_its_source_and_date():
    article, evidence = consensus_packet()
    assert check_public_event_article(article, evidence=evidence)["numeric_bindings"] == 1


def test_event_preview_passes_a_cited_official_expectation_like_a_cited_consensus():
    article, evidence = consensus_packet()
    admit(evidence, "sep-unemployment", "4.1%", attribution="FOMC Summary of Economic Projections",
          cited_on="2026-09-16")
    put(article, "probability_basis", "The FOMC Summary of Economic Projections, released September 16, 2026, put "
        "unemployment at 4.1% for the fourth quarter.", "4.1%", "sep-unemployment")
    assert check_public_event_article(article, evidence=evidence)["numeric_bindings"] == 2


def test_event_preview_carries_a_model_output_and_the_us500_regime_with_the_label():
    article, evidence = consensus_packet()
    admit(evidence, "us500-base-weight", "80%", rights="CC_MODEL_ESTIMATE", use_label="PUBLIC_MODEL_ESTIMATE_NOT_ADVICE",
          estimate_label="Capital Chronicle model estimate")
    put(article, "scenarios", "Capital Chronicle model estimate: the base case carries an 80% weight, an "
        "uncalibrated share rather than a probability.", "80%", "us500-base-weight")
    article["copy"]["market_reactions"]["indices"] = (
        "Capital Chronicle model estimate: the S&P 500 options regime is negative gamma, so a surprise in either "
        "direction could be amplified.")
    article["copy"]["view_changes"] = "A positive gamma regime would damp the move. " + CONFLICTS_NOTICE
    assert check_public_event_article(article, evidence=evidence)["numeric_bindings"] == 2


@pytest.mark.parametrize("word", ["consensus", "forecast", "surprise", "beat", "miss", "gamma", "GEX", "in line with"])
@pytest.mark.parametrize("section", ["headline", "dek", "context", "scenarios", "probability_basis", "view_changes"])
def test_consensus_words_pass_on_every_event_surface(word, section):
    article, evidence = packet()
    article["copy"][section] = f"The {word} question frames the release."
    article["copy"]["market_reactions"]["rates"] = f"Yields respond to the {word} question."
    assert check_public_event_article(article, evidence=evidence)["status"] == "PASS"


@pytest.mark.parametrize("text", [
    "Our DEMO login is private.", "The account 279805139 is flat.", "Orders route to Exness-MT5Trial8.",
    "MetaTrader 5 holds the order.", "We bought 0.10 lots of gold.", "One lot of gold was bought.",
    "The lot size is unchanged.", "The trade lost 0.8R.",
])
def test_demo_identifiers_broker_servers_lot_sizes_and_r_multiples_stay_refused(text):
    assert public_execution_copy_forbidden(text)
    article, evidence = packet()
    article["copy"]["market_reactions"]["gold"] = text
    refused(article, evidence, "PRIVATE_OR_EXECUTION_COPY_FORBIDDEN")


@pytest.mark.parametrize("text", ["A lot rides on the payrolls print.", "Lots of revisions are possible."])
def test_ordinary_lot_wording_is_not_a_position_size(text):
    assert not public_execution_copy_forbidden(text)


def test_a_kalshi_number_and_an_unconditional_call_stay_refused():
    for text in ("Kalshi priced a 62% chance of a hold.", "Kalshi's US500 market traded at 62 cents."):
        article, evidence = packet()
        article["copy"]["context"] = text
        refused(article, evidence, "PREDICTION_MARKET_NUMBER_FORBIDDEN")
    article, evidence = packet()
    article["copy"]["context"] = "Kalshi traders favour a stronger print and the S&P 500 closing higher."
    assert check_public_event_article(article, evidence=evidence)["status"] == "PASS"  # odds in words only
    article["copy"]["context"] = "The desk is bullish on gold."
    refused(article, evidence, "UNCONDITIONAL_CALL_FORBIDDEN")


@pytest.mark.parametrize("text", [
    "The S&P 500 and the Nasdaq 100 lead risk assets.", "The 10-year yield and the 2-year note move first.",
    "US500 options carry the regime.", "Q4 growth and the G7 backdrop matter.",
])
def test_index_maturity_and_quarter_names_are_not_unbound_figures(text):
    article, evidence = packet()
    article["copy"]["market_reactions"]["indices"] = text
    assert check_public_event_article(article, evidence=evidence)["status"] == "PASS"


def test_a_figure_beside_an_index_name_still_needs_its_binding():
    article, evidence = packet()
    article["copy"]["market_reactions"]["indices"] = "The S&P 500 closed at 6,812."
    refused(article, evidence, "UNBOUND_PUBLIC_NUMBER")


def test_a_raw_consensus_table_is_refused_even_when_relabelled_as_cited_facts():
    article, evidence = packet()
    rows = [("payrolls", "63,000"), ("unemployment", "4.2%"), ("earnings", "0.3%"), ("annual earnings", "3.8%")]
    text = "Investing.com's calendar, observed on 4 November: " + ", ".join(f"{k} {v}" for k, v in rows) + "."
    article["copy"]["context"] = text
    for name, figure in rows:
        admit(evidence, name, figure, attribution="Investing.com", cited_on="2026-11-04")
        start = text.index(figure)
        article["numeric_bindings"].append({"copy_path": "copy.context", "start": start,
                                            "end": start + len(figure), "evidence_ref": name})
    refused(article, evidence, "THIRD_PARTY_TABLE_OR_SERIES_FORBIDDEN")
    for name, _ in rows:
        evidence["facts"][name]["rights_class"] = "MARKET_CONSENSUS_PRIVATE_ONLY"
    refused(article, evidence, "PUBLIC_REUSE_RIGHTS_NOT_ADMITTED")


@pytest.mark.parametrize("change", [
    ("text", ", observed on 4 November", ""), ("text", "Investing.com's consensus", "The consensus"),
    ("fact", "cited_on", None), ("fact", "cited_on", "4 Nov"), ("fact", "attribution", " "),
])
def test_a_cited_figure_without_its_source_or_date_is_refused_in_event_copy(change):
    article, evidence = consensus_packet()
    kind, old, new = change
    if kind == "text":
        article, evidence = packet()
        admit(evidence, "nfp-consensus", "63,000", attribution="Investing.com", cited_on="2026-11-04")
        put(article, "context", CONSENSUS_TEXT.replace(old, new), "63,000", "nfp-consensus")
    elif new is None:
        evidence["facts"]["nfp-consensus"].pop(old)
    else:
        evidence["facts"]["nfp-consensus"][old] = new
    refused(article, evidence, "CITED_FACT_SOURCE_AND_DATE_REQUIRED")


def test_another_date_beside_a_cited_figure_stays_an_unbound_number():
    article, evidence = packet()
    admit(evidence, "nfp-consensus", "63,000", attribution="Investing.com", cited_on="2026-11-04")
    put(article, "context", CONSENSUS_TEXT.replace("4 November;", "4 November, before the 6 November release;"),
        "63,000", "nfp-consensus")
    refused(article, evidence, "UNBOUND_PUBLIC_NUMBER")


def test_a_model_output_needs_its_label_in_its_section_and_the_conflicts_notice():
    article, evidence = consensus_packet()
    fact = admit(evidence, "weight", "80%", rights="CC_MODEL_ESTIMATE", estimate_label="Capital Chronicle model estimate")
    put(article, "scenarios", "The base case carries an 80% weight.", "80%", "weight")
    article["copy"]["view_changes"] = CONFLICTS_NOTICE
    refused(article, evidence, "MODEL_ESTIMATE_LABEL_REQUIRED")
    article["copy"]["scenarios"] = "Capital Chronicle model estimate: the base case carries an 80% weight."
    article["numeric_bindings"][-1].update(start=article["copy"]["scenarios"].index("80%"),
                                           end=article["copy"]["scenarios"].index("80%") + 3)
    assert check_public_event_article(article, evidence=evidence)["status"] == "PASS"
    article["copy"]["view_changes"] = "A positive regime would damp the move."
    refused(article, evidence, "CONFLICTS_NOTICE_REQUIRED")
    article["copy"]["view_changes"] = CONFLICTS_NOTICE
    fact.pop("estimate_label")
    refused(article, evidence, "MODEL_ESTIMATE_LABEL_REQUIRED")


@pytest.mark.parametrize("written", ["2026-11-04", "4 November", "4 Nov", "4 Nov.", "4th November 2026",
                                     "November 4", "Nov. 4", "November 4, 2026", "04 November", "4 of November"])
def test_a_cited_date_is_recognised_in_its_usual_forms(written):
    assert cited_date_pattern("2026-11-04").search(f"Observed on {written}, the figure stood.")


@pytest.mark.parametrize("written", ["14 November", "November 14", "4.5 November", "November 40", "5 November",
                                     "4 October", "Novel 4"])
def test_another_date_or_number_is_not_the_cited_date(written):
    assert not cited_date_pattern("2026-11-04").search(f"Observed on {written}, the figure stood.")


# --- the newsroom's own guard and the writer's instruction ---------------------------------------------------------

def test_capital_chronicle_scenario_wording_passes_only_with_a_cited_model_estimate_and_its_label(records):
    from live_contentops.v1_simple_gemini_newsroom_v1 import _carries_model_estimates, _editorial_growth_edge_blockers
    us500 = next(r for r in records if r["binding"]["record_id"] == "asset:US500")
    assert _carries_model_estimates({"desk_record_binding": us500["binding"]})
    assert _carries_model_estimates({"source_reuse_constraints": {"rights_class": "CC_MODEL_ESTIMATE"}})
    assert not _carries_model_estimates({"source_reuse_constraints": {"scope": "BLS_PUBLIC_DOMAIN"}})
    labelled = {"title": "Capital Chronicle's scenario weights put the base case at 80% "
                         "(Capital Chronicle model estimate)."}
    blocker = "capital_chronicle_reserved_numeric_authority_unavailable"
    assert _editorial_growth_edge_blockers(labelled, article_mode="WEEK_AHEAD_OR_WATCH",
                                           model_estimates_cited=True) == []
    # Without a cited model-estimate source the same claim would be invented (host rule 8); unlabelled it is refused.
    assert blocker in _editorial_growth_edge_blockers(labelled, article_mode="WEEK_AHEAD_OR_WATCH")
    unlabelled = {"title": "Capital Chronicle's scenario weights put the base case at 80%."}
    assert blocker in _editorial_growth_edge_blockers(unlabelled, article_mode="WEEK_AHEAD_OR_WATCH",
                                                      model_estimates_cited=True)


def test_a_new_desk_record_writer_request_carries_decision_72b_wording(tmp_path):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.native_desktop_editorial_v1 import DesktopInputRequired, NativeDesktopTurn
    from live_contentops.native_newsroom_volume_v1 import volume_policy
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    run = "cc264-desk-writer"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled prompt", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)
    turn.volume_policy = volume_policy(CUTOFF)
    args = {"logical_invocation_id": run + ":write", "prompt": "Exact controlled request",
            "governed_input": {"desk_record_binding": {"CONTROLLED_TEST_ONLY": True}},
            "validator": lambda raw: (True, None, json.loads(raw), None)}
    with pytest.raises(DesktopInputRequired) as first:
        turn(**args)
    prompt = first.value.request["prompt"]
    assert "MAIN_DESK_RECORD_FIELDS" in prompt
    assert "A consensus figure or official expectation appears as one cited fact with its source and date" in prompt
    assert "say 'Capital Chronicle model estimate'" in prompt
    assert CONFLICTS_NOTICE in prompt
    assert "model positions on a demo account" not in prompt.casefold()
    assert "state a consensus judgement" not in prompt
    with pytest.raises(DesktopInputRequired) as resumed:
        turn(**args)
    assert resumed.value.request == first.value.request


def test_cc423_resumes_a_pre_amendment_writer_request_without_changing_its_hash(tmp_path, monkeypatch):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.native_desktop_editorial_v1 import DesktopInputRequired, NativeDesktopTurn
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    run = "cc423-frozen-writer"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled prompt", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)
    args = {"logical_invocation_id": run + ":write", "prompt": "Exact controlled request",
            "governed_input": {"desk_record_binding": {"CONTROLLED_TEST_ONLY": True}},
            "validator": lambda raw: (True, None, json.loads(raw), None)}
    with pytest.raises(DesktopInputRequired) as first:
        turn(**args)
    frozen = {k: v for k, v in first.value.request.items() if k != "request_path"}
    instruction = "Every reader-facing piece also carries this exact positions notice: " + CONFLICTS_NOTICE + "\n"
    frozen["prompt"] = frozen["prompt"].replace(instruction, "")
    frozen["request_sha256"] = sha256_of({k: v for k, v in frozen.items() if k != "request_sha256"})
    get = turn._get
    monkeypatch.setattr(turn, "_get", lambda stage, kind: frozen if (stage, kind) == ("write", "request") else get(stage, kind))
    def unchanged(stage, kind, value):
        assert (stage, kind) == ("write", "request")
        assert value == frozen
    monkeypatch.setattr(turn, "_put", unchanged)
    with pytest.raises(DesktopInputRequired) as resumed:
        turn(**args)
    assert {k: v for k, v in resumed.value.request.items() if k != "request_path"} == frozen
