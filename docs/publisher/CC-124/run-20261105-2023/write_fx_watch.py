"""Save this native writer's authored return after deterministic local checks."""

from decimal import Decimal, localcontext
from hashlib import sha256
from pathlib import Path
import json
import re

from live_contentops.native_desktop_editorial_v1 import validate_native_configuration
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    SimpleGeminiNewsroomError,
    _derivative_media_attribution,
    _native_preview_bundle,
    _reader_safe_native_article,
    _validate_article_against_source_pack,
    _validate_worker_text,
)
from live_contentops.eight_platform_substack_first_pipeline_v1 import build_native_derivative_payloads


BASE = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-jobs-fx-watch-20261105-f")
REQUEST_PATH = BASE / "desktop_request_write.json"
REQUEST = json.loads(REQUEST_PATH.read_bytes())
assert REQUEST["request_sha256"] == "0f94fa056a5fc42e6e23f6b9c26384f128fd6e9f017fc4b86883ea3c6b76b991"
GOVERNED = REQUEST["governed_input"]
SOURCES = {s["source_id"]: s for s in GOVERNED["source_pack"]}
SUMMARY_PATH = Path(__file__).with_name("fx-official-data-summary.json")
SUMMARY = json.loads(SUMMARY_PATH.read_bytes())

TITLE = "EURUSD and USDJPY: two falling quotes, two dollar directions"
DEK = "Fed reference rates for October 26-30 show the dollar gaining against the euro and slipping against the yen. The quote convention changes the meaning of the move."
SEARCH_TITLE = "EURUSD vs USDJPY: how to read the dollar's direction"
DESCRIPTION = "Fed reference rates for October 26-30 show a stronger dollar against the euro and a weaker one against the yen. Read both pairs alongside Treasury yields."
HOOK = "EURUSD fell. USDJPY fell. Those October 26-30 Fed reference rates meant a stronger dollar against the euro and a weaker one against the yen."

MECHANISM = "A higher US yield could support the dollar if it makes dollar assets relatively more attractive."
COUNTERCASE = "Euro- or yen-specific policy expectations and demand for safer assets could outweigh the US yield channel. The October 26-30 comparison cannot identify which driver dominated."
WATCH = "A split dollar response across the two currencies would challenge an explanation built on one common dollar driver."

LEAD = "In the Federal Reserve's November 2 H.10 release, EURUSD fell from 1.1178 to 1.1163 over October 26-30, while USDJPY fell from 157.5800 to 157.4700. Both quotes went down. The dollar strengthened against the euro and weakened against the yen."
FRAME = "Capital Chronicle's view is that a dollar thesis needs this two-currency check before it is compared with Treasury yields. The small moves in this five-date window show why a dollar view needs a named currency counterpart."
UNITS = "EURUSD is quoted in US dollars per euro. When that number falls, one euro buys fewer dollars, so the dollar is stronger against the euro. USDJPY is quoted in yen per dollar. A fall means one dollar buys fewer yen, so the dollar is weaker against the yen."
NORMALIZED = "The first chart puts both relationships into currency units per dollar and measures their change from October 26. For the euro, that requires taking the reciprocal of EURUSD; the yen quote already measures what one dollar buys. On this basis, the dollar ended October 30 up 0.13% against the euro and down 0.07% against the yen. The inverted euro rate is calculated from the Fed quote."
YIELDS = "Treasury's nominal 10-year par yield moved from 5.00% to 4.94% over the same October 26-30 window, a six-basis-point decline. It reached 5.05% on October 28. The endpoint fall was not a steady daily decline."
ALIGNMENT = "Matching dates make the comparison fairer, but these daily observations are not synchronized intraday prices. They do not establish that Treasury yields caused either currency move."
LATER = "The later Treasury reading was 4.90% on November 4. It is a separate context point: the FX observations compared here still end on October 30."
CHANNEL = "Capital Chronicle's analysis is conditional. " + MECHANISM + " A fall in EURUSD alongside a rise in USDJPY would show the dollar strengthening against both currencies. That consistent direction would fit the proposed channel; it would not prove that the yield move caused the currency moves."
COUNTER = COUNTERCASE + " " + WATCH + " The October 26-30 endpoint split is already a reason to avoid treating the two pairs as one interchangeable dollar position."
CALENDAR = "The Bureau of Labor Statistics schedules the October Employment Situation for November 6 at 8:30 a.m. EST. After the release, first read the observed Treasury yield response, then translate each currency pair into the dollar's direction. The question is whether both currencies support the same dollar interpretation."
NOTICES = "Analysis, not financial advice. Readers decide whether to trade. Capital Chronicle may hold positions in the markets it covers."

PARAGRAPHS = [
    LEAD + " [[SOURCE:SOURCE_3]]",
    FRAME + " [[SOURCE:SOURCE_3]] [[SOURCE:SOURCE_1]]",
    "## Two falling quotes, two dollar directions",
    UNITS + " [[SOURCE:SOURCE_3]]",
    NORMALIZED + " [[SOURCE:SOURCE_3]]",
    "## Match the yield dates before telling the story",
    YIELDS + " [[SOURCE:SOURCE_1]]",
    ALIGNMENT + " [[SOURCE:SOURCE_1]] [[SOURCE:SOURCE_3]]",
    LATER + " [[SOURCE:SOURCE_1]] [[SOURCE:SOURCE_3]]",
    "## A yield channel, with a countercase",
    CHANNEL + " [[SOURCE:SOURCE_1]] [[SOURCE:SOURCE_3]]",
    COUNTER + " [[SOURCE:SOURCE_1]] [[SOURCE:SOURCE_3]]",
    "## The next check",
    CALENDAR + " [[SOURCE:SOURCE_2]] [[SOURCE:SOURCE_1]] [[SOURCE:SOURCE_3]]",
    NOTICES + " [[SOURCE:SOURCE_3]]",
]

ARTICLE = {
    "title": TITLE,
    "dek": DEK,
    "search_title": SEARCH_TITLE,
    "meta_description": DESCRIPTION,
    "social_hook": HOOK,
    "substack_body_markdown": "\n\n".join(PARAGRAPHS),
    "reader_first_version": "DATA_JOURNALISM_V1",
    "visual_editorial_decision": GOVERNED["visual_editorial_decision"],
    "display_date": "5 November 2026",
    "social_mechanism_summary": MECHANISM,
    "social_policy_summary": COUNTERCASE,
    "social_cross_asset_summary": WATCH,
    "canonical_slug_candidate": "dollar-euro-yen-two-directions",
    "primary_reader_question": GOVERNED["primary_reader_question"],
    "secondary_reader_questions": [
        "Why does a fall in EURUSD mean something different from a fall in USDJPY?",
        "How did the two dollar relationships compare with Treasury yields over October 26-30?",
        "What would challenge a common dollar explanation after the November 6 jobs release?",
    ],
    "entities": ["US dollar", "Euro", "Japanese yen", "Federal Reserve", "U.S. Treasury", "U.S. Bureau of Labor Statistics"],
    "topics": ["Foreign exchange rates", "EURUSD", "USDJPY", "Treasury yields", "Employment Situation"],
    "search_freshness_class": "DATED_CURRENCY_EXPLANATION_WITH_SCHEDULED_WATCH",
    "internal_link_candidates": [],
}

EUR_ROW = "| *EMU MEMBERS | EURO | 1.1178 | 1.1144 | 1.1140 | 1.1165 | 1.1163 |"
YEN_ROW = "| JAPAN | YEN | 157.5800 | 157.8600 | 158.2400 | 157.8300 | 157.4700 |"
CONVENTION = "(Rates in currency units per U.S. dollar except as noted by an asterisk)\n\n* U.S. dollars per currency unit."
FX_RELEASE = "Release Date: November 2, 2026"
YIELD_WINDOW = "2026-10-26 5.00\n2026-10-27 4.99\n2026-10-28 5.05\n2026-10-29 4.98\n2026-10-30 4.94"
YIELD_NAME = "U.S. Treasury nominal 10-year par yields, 2 January through 4 November 2026; percent."
BLS_CALENDAR = SOURCES["SOURCE_2"]["canonical_content_text"]
CLAIMS = []


def bind(claim_id, text, source_id, excerpt, kind="FACT"):
    assert excerpt in SOURCES[source_id]["canonical_content_text"], claim_id
    assert text in " ".join(str(ARTICLE.get(k, "")) for k in (
        "title", "dek", "search_title", "meta_description", "social_hook", "substack_body_markdown")), claim_id
    CLAIMS.append({"claim_id": claim_id, "claim_text": text, "claim_kind": kind,
        "source_id": source_id, "support_excerpt": excerpt, "attribution_required": True})


for field, text in (("title", TITLE), ("dek", DEK), ("search", SEARCH_TITLE), ("description", DESCRIPTION), ("hook", HOOK)):
    bind(field + "-euro", text, "SOURCE_3", EUR_ROW)
    bind(field + "-yen", text, "SOURCE_3", YEN_ROW)
    bind(field + "-convention", text, "SOURCE_3", CONVENTION)
bind("description-treasury-context", DESCRIPTION, "SOURCE_1", YIELD_NAME)

bind("release-date", "In the Federal Reserve's November 2 H.10 release,", "SOURCE_3", FX_RELEASE)
bind("lead-euro-values", "EURUSD fell from 1.1178 to 1.1163 over October 26-30", "SOURCE_3", EUR_ROW, "NUMBER")
bind("lead-yen-values", "USDJPY fell from 157.5800 to 157.4700.", "SOURCE_3", YEN_ROW, "NUMBER")
bind("two-quotes-fell-euro", "Both quotes went down.", "SOURCE_3", EUR_ROW)
bind("two-quotes-fell-yen", "Both quotes went down.", "SOURCE_3", YEN_ROW)
bind("lead-direction-euro", "The dollar strengthened against the euro and weakened against the yen.", "SOURCE_3", EUR_ROW)
bind("lead-direction-yen", "The dollar strengthened against the euro and weakened against the yen.", "SOURCE_3", YEN_ROW)
bind("lead-direction-convention", "The dollar strengthened against the euro and weakened against the yen.", "SOURCE_3", CONVENTION)
bind("labeled-house-view", "Capital Chronicle's view is that a dollar thesis needs this two-currency check before it is compared with Treasury yields.", "SOURCE_3", CONVENTION)
bind("five-date-frame", "The small moves in this five-date window show why a dollar view needs a named currency counterpart.", "SOURCE_3", EUR_ROW)
bind("euro-quote-unit", "EURUSD is quoted in US dollars per euro.", "SOURCE_3", CONVENTION)
bind("euro-quote-direction", "When that number falls, one euro buys fewer dollars, so the dollar is stronger against the euro.", "SOURCE_3", CONVENTION)
bind("yen-quote-unit", "USDJPY is quoted in yen per dollar.", "SOURCE_3", CONVENTION)
bind("yen-quote-direction", "A fall means one dollar buys fewer yen, so the dollar is weaker against the yen.", "SOURCE_3", CONVENTION)
bind("normalization-explanation", "The first chart puts both relationships into currency units per dollar and measures their change from October 26.", "SOURCE_3", CONVENTION)
bind("reciprocal-explanation", "For the euro, that requires taking the reciprocal of EURUSD; the yen quote already measures what one dollar buys.", "SOURCE_3", CONVENTION)
bind("normalized-euro-endpoint", "On this basis, the dollar ended October 30 up 0.13% against the euro and down 0.07% against the yen.", "SOURCE_3", EUR_ROW, "NUMBER")
bind("normalized-yen-endpoint", "On this basis, the dollar ended October 30 up 0.13% against the euro and down 0.07% against the yen.", "SOURCE_3", YEN_ROW, "NUMBER")
bind("calculated-inverse", "The inverted euro rate is calculated from the Fed quote.", "SOURCE_3", CONVENTION)
bind("matched-yield-levels-and-change", "Treasury's nominal 10-year par yield moved from 5.00% to 4.94% over the same October 26-30 window, a six-basis-point decline.", "SOURCE_1", YIELD_WINDOW, "NUMBER")
bind("matched-yield-midweek", "It reached 5.05% on October 28.", "SOURCE_1", "2026-10-28 5.05", "NUMBER")
bind("yield-path-description", "The endpoint fall was not a steady daily decline.", "SOURCE_1", YIELD_WINDOW)
bind("date-alignment-treasury", ALIGNMENT, "SOURCE_1", YIELD_WINDOW)
bind("date-alignment-fx", ALIGNMENT, "SOURCE_3", EUR_ROW)
bind("later-yield-dated", "The later Treasury reading was 4.90% on November 4.", "SOURCE_1", "2026-11-04 4.90", "NUMBER")
bind("later-yield-separation", "It is a separate context point: the FX observations compared here still end on October 30.", "SOURCE_3", EUR_ROW)
bind("conditional-house-label", "Capital Chronicle's analysis is conditional.", "SOURCE_1", YIELD_NAME)
bind("conditional-yield-channel", MECHANISM, "SOURCE_1", YIELD_NAME, "CAUSALITY")
bind("conditional-two-currency-direction", "A fall in EURUSD alongside a rise in USDJPY would show the dollar strengthening against both currencies.", "SOURCE_3", CONVENTION)
bind("channel-versus-cause-treasury", "That consistent direction would fit the proposed channel; it would not prove that the yield move caused the currency moves.", "SOURCE_1", YIELD_NAME, "CAUSALITY")
bind("channel-versus-cause-fx", "That consistent direction would fit the proposed channel; it would not prove that the yield move caused the currency moves.", "SOURCE_3", CONVENTION, "CAUSALITY")
bind("conditional-countercase", COUNTERCASE, "SOURCE_3", CONVENTION, "CAUSALITY")
bind("conditional-challenge", WATCH, "SOURCE_3", CONVENTION, "CAUSALITY")
bind("observed-split-house-reading-euro", "The October 26-30 endpoint split is already a reason to avoid treating the two pairs as one interchangeable dollar position.", "SOURCE_3", EUR_ROW)
bind("observed-split-house-reading-yen", "The October 26-30 endpoint split is already a reason to avoid treating the two pairs as one interchangeable dollar position.", "SOURCE_3", YEN_ROW)
bind("release-calendar", "The Bureau of Labor Statistics schedules the October Employment Situation for November 6 at 8:30 a.m. EST.", "SOURCE_2", BLS_CALENDAR)
bind("next-check-calendar", "After the release, first read the observed Treasury yield response, then translate each currency pair into the dollar's direction.", "SOURCE_2", BLS_CALENDAR)
bind("next-check-yield", "After the release, first read the observed Treasury yield response, then translate each currency pair into the dollar's direction.", "SOURCE_1", YIELD_NAME)
bind("next-check-fx", "The question is whether both currencies support the same dollar interpretation.", "SOURCE_3", CONVENTION)

OUTPUT = {"schema_version": "contentops.v1_simple_gemini_article.v1", "article": ARTICLE,
    "cited_sources": [{k: s[k] for k in ("source_id", "url", "publisher", "published_at_utc")} for s in GOVERNED["source_pack"]],
    "material_claim_bindings": CLAIMS, "public_write_attempted": False}

with localcontext() as ctx:
    ctx.prec = 40
    euro_change = (Decimal("1.1178") / Decimal("1.1163") - 1) * 100
    yen_change = (Decimal("157.4700") / Decimal("157.5800") - 1) * 100
assert euro_change.quantize(Decimal("0.01")) == Decimal("0.13")
assert yen_change.quantize(Decimal("0.01")) == Decimal("-0.07")
assert (Decimal("4.94") - Decimal("5.00")) * 100 == Decimal("-6")
assert SUMMARY["later_treasury_observation"] == {"date": "2026-11-04", "yield_percent": "4.90", "matched_fx_observation": None}
assert SUMMARY["jobs_calendar"]["date_correct_utc"] == "2026-11-06T13:30:00Z"
assert SUMMARY["jobs_calendar"]["result"] is None
assert len(DESCRIPTION) <= 160
for key in ("social_mechanism_summary", "social_policy_summary", "social_cross_asset_summary"):
    assert ARTICLE[key] in ARTICLE["substack_body_markdown"]
assert ARTICLE["visual_editorial_decision"] == GOVERNED["visual_editorial_decision"]
assert "\ufffd" not in " ".join(ARTICLE[k] for k in ("title", "dek", "search_title", "meta_description", "social_hook", "substack_body_markdown"))
ok, failure_class, _, reason = _validate_worker_text(json.dumps(OUTPUT))
assert ok, (failure_class, reason)
validated_article, validation = _validate_article_against_source_pack(OUTPUT, GOVERNED["source_pack"],
    selected_candidate=GOVERNED["selected_candidate"], article_mode=GOVERNED["article_mode"], epistemic_state=GOVERNED["epistemic_state"])

preview_article = dict(validated_article)
preview_article.update(public_source_bindings=OUTPUT["cited_sources"], reader_attribution_policy=GOVERNED["reader_attribution_policy"])
media = GOVERNED["editorial_media_plan"]["assets"]
preview_gate = {"status": "PASS"}
try:
    bundle, rows = _native_preview_bundle(article=preview_article, article_mode=GOVERNED["article_mode"],
        article_identity=REQUEST["run_id"], epistemic_state=GOVERNED["epistemic_state"],
        media_asset_ids=[a["asset_id"] for a in media], media_assets=media)
except SimpleGeminiNewsroomError as exc:
    preview_gate = {"status": "FAILED", "error": str(exc), "details": exc.details}
    compiler_article = _reader_safe_native_article(preview_article, article_mode=GOVERNED["article_mode"],
        epistemic_state=GOVERNED["epistemic_state"], legacy_presentation=False)
    compiler_article["native_media_sources"] = {a["asset_id"]: a["source_links"] for a in media if a.get("source_links")}
    compiler_article["native_destination_credits"] = {d: _derivative_media_attribution(
        [a for a in media if a["asset_id"] in ids], compact=True) for d, ids in compiler_article["native_destination_media"].items()}
    payloads = build_native_derivative_payloads(article=compiler_article, selection={},
        canonical_url="https://capitalchronicle.substack.com/p/pending-publication-cc124-fx-watch",
        media_asset_ids=[a["asset_id"] for a in media])
    bundle = {"packages": payloads, "local_payload_audit_only": True, "owner_gate": preview_gate}
    rows = []


def weighted_length(text):
    count = 0
    cursor = 0
    for match in re.finditer(r"https?://[^\s)]+", text):
        count += sum(1 if ord(c) <= 0x10FF or 0x2000 <= ord(c) <= 0x200D or 0x2010 <= ord(c) <= 0x201F or 0x2032 <= ord(c) <= 0x2037 else 2 for c in text[cursor:match.start()]) + 23
        cursor = match.end()
    return count + sum(1 if ord(c) <= 0x10FF or 0x2000 <= ord(c) <= 0x200D or 0x2010 <= ord(c) <= 0x201F or 0x2032 <= ord(c) <= 0x2037 else 2 for c in text[cursor:])


payload_audit = {}
assert set(bundle["packages"]) == {"telegram", "discord", "x", "linkedin", "facebook_page", "instagram_business", "threads", "youtube"}
for destination, payload in bundle["packages"].items():
    posts = payload.get("posts") or []
    texts = [p["text"] for p in posts] if posts else [str(payload.get(k) or "") for k in ("text", "full_text", "root_text", "caption")]
    visible = "\n\n".join(texts)
    for notice in ("Analysis, not financial advice.", "Capital Chronicle may hold positions in the markets it covers."):
        assert notice in visible, (destination, notice)
    assert "October 26-30" in visible, (destination, "dated comparison window")
    assert payload.get("media_asset_ids"), destination
    assert not re.search(r"(?:localhost|127\.0\.0\.1|trycloudflare|github\.io|pages\.dev|vercel\.app|netlify\.app)", visible, re.I), destination
    payload_audit[destination] = {"both_notices_present": True, "media_asset_ids": payload.get("media_asset_ids"), "post_count": len(posts), "no_preview_site_link": True, "dated_comparison_window_present": True}
    if destination in {"x", "threads"}:
        metrics = payload["quality_metrics"]
        assert metrics["sentence_boundary_pass"] is True
        assert metrics["orphan_fragment_count"] == 0
        assert metrics["hard_character_slicing_used"] is False
        limit = 280 if destination == "x" else 500
        assert all(weighted_length(text) <= limit for text in texts), (destination, max(map(weighted_length, texts)))
        payload_audit[destination].update(max_weighted_characters=max(map(weighted_length, texts)), platform_limit=limit, complete_sentences=True)

OBSERVATION = dict(json.loads((BASE / "desktop_response_visual-edit.json").read_bytes())["invocation_observation"])
OBSERVATION["configuration_source"] = "Explicit supported parent assignment and continuation in the SAME native task /root/native_max_fx_42ae7362164c; exact frozen write request 0f94fa056a5fc42e6e23f6b9c26384f128fd6e9f017fc4b86883ea3c6b76b991 requests gpt-6.1-sol/max. These are configured values, not observed runtime model or effort telemetry."
OBSERVATION["observation_source"] = "Supported native subagent task identity /root/native_max_fx_42ae7362164c, continuing from actual visual planning and exact local asset inspection to this authored write return. Actual model and reasoning-effort telemetry is unavailable."
OBSERVATION["writer_input"] = {"path": str(REQUEST_PATH), "sha256": sha256(REQUEST_PATH.read_bytes()).hexdigest(), "request_sha256": REQUEST["request_sha256"], "same_native_context": True}
assert OBSERVATION["invocation_id"] == "/root/native_max_fx_42ae7362164c"
assert OBSERVATION["model"] is None and OBSERVATION["reasoning_effort"] is None
validate_native_configuration(OBSERVATION, {"model": "gpt-6.1-sol", "reasoning_effort": "max"})
RESPONSE = {"request_sha256": REQUEST["request_sha256"], "output": OUTPUT, "invocation_observation": OBSERVATION}


def main():
    response_path = BASE / "desktop_response_write.json"
    if response_path.exists():
        prior_bytes = response_path.read_bytes()
        prior = json.loads(prior_bytes)
        assert prior["request_sha256"] == REQUEST["request_sha256"]
        assert prior["invocation_observation"]["invocation_id"] == "/root/native_max_fx_42ae7362164c"
        archive_path = BASE / ("desktop_response_write.local-before-date-fix." + sha256(prior_bytes).hexdigest() + ".json")
        if archive_path.exists():
            assert archive_path.read_bytes() == prior_bytes
        else:
            archive_path.write_bytes(prior_bytes)
    response_path.write_text(json.dumps(RESPONSE, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence_path = Path(__file__).with_name("writer-local-validation.json")
    evidence = {"request_sha256": REQUEST["request_sha256"], "response_sha256": sha256(response_path.read_bytes()).hexdigest(),
        "source_validation": validation, "local_preview_bundle": bundle, "local_preview_rows": rows,
        "native_preview_owner_gate": preview_gate, "payload_audit": payload_audit,
        "calculation_checks": {"owner": "Python Decimal, precision 40", "dollar_vs_euro_percent_change": str(euro_change),
            "dollar_vs_yen_percent_change": str(yen_change), "rounded_public_endpoints": ["+0.13%", "-0.07%"],
            "matched_treasury_change_basis_points": "-6", "summary_path": str(SUMMARY_PATH), "summary_sha256": sha256(SUMMARY_PATH.read_bytes()).hexdigest()},
        "public_write_attempted": False, "final_assembled_pixel_review": "PENDING"}
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"response_path": str(response_path), "response_sha256": evidence["response_sha256"],
        "validation_path": str(evidence_path), "schema": "PASS", "source_validation": validation["status"],
        "supported_material_claim_count": validation["supported_material_claim_count"], "native_preview_owner_gate": preview_gate,
        "payload_audit": payload_audit}, ensure_ascii=True))


if __name__ == "__main__":
    main()
