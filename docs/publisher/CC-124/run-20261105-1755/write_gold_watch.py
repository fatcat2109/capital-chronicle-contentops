"""Author and locally check this exact native writer return; no runtime writes."""

import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path

from live_contentops.v1_simple_gemini_newsroom_v1 import (
    SimpleGeminiNewsroomError,
    _derivative_media_attribution,
    _native_preview_bundle,
    _reader_safe_native_article,
    _validate_article_against_source_pack,
    _validate_worker_text,
)
from live_contentops.eight_platform_substack_first_pipeline_v1 import build_native_derivative_payloads


BASE = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-gold-yields-20261105-e")
REQUEST = json.loads((BASE / "desktop_request_write.json").read_text(encoding="utf-8-sig"))
GOVERNED = REQUEST["governed_input"]
SOURCES = {s["source_id"]: s for s in GOVERNED["source_pack"]}
assert REQUEST["request_sha256"] == "3a768a46f25b3e19a9be67efe17dea1f890883e03e09025653b364038edb87ac"

TITLE = "Gold before the jobs report: beyond the Fed's target range"
DEK = "Treasury's nominal 10-year yield fell 5 basis points on November 4; its real yield fell 1. The next question for gold is how real yields respond to the November 6 jobs report."
SEARCH_TITLE = "Gold and real Treasury yields before the November 6 jobs report"
DESCRIPTION = "Treasury's November 4 nominal yield fell more than its real yield. A gold watch before the November 6 jobs report, with conditions that would change the view."
HOOK = "Treasury's nominal yield fell 5 basis points on November 4. Its real yield fell 1. Gold's jobs-report watch needs both."

MECHANISM = "Lower real Treasury yields would reduce one cost of holding gold: the inflation-adjusted return available from a competing asset."
COUNTERCASE = "Currency moves or demand for safety could outweigh the real-yield channel. That would make a simple bond-yield explanation inadequate."
WATCH = "A sustained real-yield rise after the jobs report would weaken this particular support for gold."

PARAGRAPHS = [
    "A lower Treasury yield is an incomplete guide to gold. On November 4, Treasury's nominal 10-year par yield was 4.90%, down from 4.95% on November 3. Its real 10-year yield was 2.64%, down from 2.65% on the same dates. [[SOURCE:SOURCE_2]] [[SOURCE:SOURCE_3]]",
    "The Bureau of Labor Statistics schedules the October Employment Situation for November 6 at 8:30 a.m. EST. Capital Chronicle's view is that the useful follow-up for gold is whether the inflation-adjusted yield moves lower. The jobs outcome is still ahead. [[SOURCE:SOURCE_4]] [[SOURCE:SOURCE_3]]",
    "## Two yields, two questions",
    "The nominal Treasury series quotes a yield without an adjustment for inflation; the real series is its inflation-adjusted counterpart. " + MECHANISM + " That is the economic channel being watched, rather than a measurement of gold's reaction. [[SOURCE:SOURCE_2]] [[SOURCE:SOURCE_3]]",
    "The [[CITE:SOURCE_1|Federal Reserve's October 28 statement]] recorded a target range for the federal funds rate of 3.75%-4.00%. That dated policy range anchors the discussion, but it is a different measure from the 10-year bond yields relevant to this watch. [[SOURCE:SOURCE_1]] [[SOURCE:SOURCE_2]] [[SOURCE:SOURCE_3]]",
    "## The latest fall was mostly nominal",
    "Calculated from Treasury's November 3 and 4 observations, the nominal decline was 5 basis points and the real decline was 1 basis point. One basis point is 0.01 percentage point. The daily comparison therefore shows much less easing in the real measure. These yield observations do not establish how gold traded. [[SOURCE:SOURCE_2]] [[SOURCE:SOURCE_3]]",
    "## What to watch after the jobs report",
    "After the release, a sustained fall in the real 10-year yield would strengthen this particular case for gold. A fall in the nominal yield with the real yield little changed would offer less support through the same channel. " + WATCH + " [[SOURCE:SOURCE_3]] [[SOURCE:SOURCE_4]]",
    "## What would weaken the argument",
    COUNTERCASE + " A gold rise alongside rising real yields, or a gold decline alongside falling real yields, would challenge a one-channel reading. The checkpoint is the observed real-yield response after the release, then whether gold moves consistently with that mechanism. [[SOURCE:SOURCE_3]] [[SOURCE:SOURCE_4]]",
    "Analysis, not financial advice. Readers decide whether to trade. Capital Chronicle may hold positions in the markets it covers. [[SOURCE:SOURCE_1]]",
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
    "canonical_slug_candidate": "gold-real-yields-november-jobs-watch-2026-11-05",
    "primary_reader_question": GOVERNED["primary_reader_question"],
    "secondary_reader_questions": [
        "How did nominal and real Treasury yields change on November 4?",
        "Which yield response after the jobs report would strengthen or weaken the opportunity-cost channel for gold?",
    ],
    "entities": ["Gold", "U.S. Treasury", "Federal Reserve", "U.S. Bureau of Labor Statistics"],
    "topics": ["Gold", "Real yields", "Treasury yields", "Employment Situation"],
    "search_freshness_class": "DATED_PRE_RELEASE_WATCH",
    "internal_link_candidates": [],
}

CLAIMS = []


def bind(claim_id, text, source_id, excerpt, kind="FACT"):
    assert excerpt in SOURCES[source_id]["canonical_content_text"], claim_id
    assert text in " ".join(str(ARTICLE.get(k, "")) for k in (
        "title", "dek", "search_title", "meta_description", "social_hook", "substack_body_markdown")), claim_id
    CLAIMS.append({
        "claim_id": claim_id,
        "claim_text": text,
        "claim_kind": kind,
        "source_id": source_id,
        "support_excerpt": excerpt,
        "attribution_required": True,
    })


NOMINAL = "2026-11-03 4.95\n2026-11-04 4.90"
REAL = "2026-11-03 2.65\n2026-11-04 2.64"
NOMINAL_SERIES = "U.S. Treasury nominal 10-year par yields, 2 January through 4 November 2026; percent."
REAL_SERIES = "U.S. Treasury real 10-year par yields, 2 January through 4 November 2026; percent."
FED = "Federal funds target range lower bound: 3.75 percent; basis POLICY_TARGET_RANGE_LOWER_BOUND. Federal funds target range upper bound: 4.0 percent; basis POLICY_TARGET_RANGE_UPPER_BOUND. Reference period: 2026-10-28."
CALENDAR = SOURCES["SOURCE_4"]["canonical_content_text"]

# Metadata bindings preserve complete public strings. Repeated strings with
# separate sources express their multiple factual anchors; they do not turn
# the writer's qualitative synthesis into a quotation or a measured gold move.
bind("title-policy-anchor", TITLE, "SOURCE_1", FED)
bind("title-yield-anchor", TITLE, "SOURCE_3", REAL_SERIES, "CAUSALITY")
for field, text in (("dek", DEK), ("search", SEARCH_TITLE), ("description", DESCRIPTION), ("hook", HOOK)):
    bind(field + "-nominal", text, "SOURCE_2", NOMINAL, "NUMBER" if field in {"dek", "hook"} else "FACT")
    bind(field + "-real", text, "SOURCE_3", REAL, "NUMBER" if field in {"dek", "hook"} else "FACT")
    if field != "hook":
        bind(field + "-calendar", text, "SOURCE_4", CALENDAR)

bind("lead-qualitative-frame", "A lower Treasury yield is an incomplete guide to gold.", "SOURCE_3", REAL_SERIES, "CAUSALITY")
bind("lead-nominal-levels", "On November 4, Treasury's nominal 10-year par yield was 4.90%, down from 4.95% on November 3.", "SOURCE_2", NOMINAL, "NUMBER")
bind("lead-real-levels", "Its real 10-year yield was 2.64%, down from 2.65% on the same dates.", "SOURCE_3", REAL, "NUMBER")
bind("release-calendar", "The Bureau of Labor Statistics schedules the October Employment Situation for November 6 at 8:30 a.m. EST.", "SOURCE_4", CALENDAR)
bind("release-future-status", "The jobs outcome is still ahead.", "SOURCE_4", CALENDAR)
bind("labeled-house-watch", "Capital Chronicle's view is that the useful follow-up for gold is whether the inflation-adjusted yield moves lower.", "SOURCE_3", REAL_SERIES, "CAUSALITY")
bind("series-nominal-meaning", "The nominal Treasury series quotes a yield without an adjustment for inflation; the real series is its inflation-adjusted counterpart.", "SOURCE_2", NOMINAL_SERIES)
bind("series-real-meaning", "The nominal Treasury series quotes a yield without an adjustment for inflation; the real series is its inflation-adjusted counterpart.", "SOURCE_3", REAL_SERIES)
bind("conditional-opportunity-cost", MECHANISM, "SOURCE_3", REAL_SERIES, "CAUSALITY")
bind("not-measured-gold-reaction", "That is the economic channel being watched, rather than a measurement of gold's reaction.", "SOURCE_3", REAL_SERIES)
bind("dated-policy-range", "recorded a target range for the federal funds rate of 3.75%-4.00%.", "SOURCE_1", FED, "NUMBER")
bind("policy-versus-market-measure", "That dated policy range anchors the discussion, but it is a different measure from the 10-year bond yields relevant to this watch.", "SOURCE_1", FED)
bind("daily-nominal-change", "the nominal decline was 5 basis points", "SOURCE_2", NOMINAL, "NUMBER")
bind("daily-real-change", "the real decline was 1 basis point.", "SOURCE_3", REAL, "NUMBER")
bind("basis-point-unit", "One basis point is 0.01 percentage point.", "SOURCE_2", NOMINAL, "NUMBER")
bind("daily-qualitative-comparison-nominal", "The daily comparison therefore shows much less easing in the real measure.", "SOURCE_2", NOMINAL)
bind("daily-qualitative-comparison-real", "The daily comparison therefore shows much less easing in the real measure.", "SOURCE_3", REAL)
bind("no-observed-gold-inference", "These yield observations do not establish how gold traded.", "SOURCE_3", REAL_SERIES)
bind("conditional-support", "After the release, a sustained fall in the real 10-year yield would strengthen this particular case for gold.", "SOURCE_3", REAL_SERIES, "CAUSALITY")
bind("conditional-less-support", "A fall in the nominal yield with the real yield little changed would offer less support through the same channel.", "SOURCE_3", REAL_SERIES, "CAUSALITY")
bind("conditional-invalidation", WATCH, "SOURCE_3", REAL_SERIES, "CAUSALITY")
bind("competing-channels", COUNTERCASE, "SOURCE_3", REAL_SERIES, "CAUSALITY")
bind("observable-countercase", "A gold rise alongside rising real yields, or a gold decline alongside falling real yields, would challenge a one-channel reading.", "SOURCE_3", REAL_SERIES, "CAUSALITY")
bind("release-followup-checkpoint", "The checkpoint is the observed real-yield response after the release, then whether gold moves consistently with that mechanism.", "SOURCE_4", CALENDAR, "CAUSALITY")

OUTPUT = {
    "schema_version": "contentops.v1_simple_gemini_article.v1",
    "article": ARTICLE,
    "cited_sources": [{k: source[k] for k in ("source_id", "url", "publisher", "published_at_utc")}
                      for source in GOVERNED["source_pack"]],
    "material_claim_bindings": CLAIMS,
    "public_write_attempted": False,
}

# Arithmetic and clock conversion are existing code facts, not new model data.
assert (Decimal("4.90") - Decimal("4.95")) * 100 == Decimal("-5")
assert (Decimal("2.64") - Decimal("2.65")) * 100 == Decimal("-1")
CLOCK = json.loads(Path(__file__).with_name("calendar-clock-check.json").read_text(encoding="utf-8-sig"))
assert CLOCK["release_source_local"] == "2026-11-06T08:30:00-05:00"
assert CLOCK["source_timezone_abbreviation"] == "EST"

ok, failure_class, _, reason = _validate_worker_text(json.dumps(OUTPUT))
assert ok, (failure_class, reason)
validated_article, validation = _validate_article_against_source_pack(
    OUTPUT,
    GOVERNED["source_pack"],
    selected_candidate=GOVERNED["selected_candidate"],
    article_mode=GOVERNED["article_mode"],
    epistemic_state=GOVERNED["epistemic_state"],
)
assert ARTICLE["visual_editorial_decision"] == GOVERNED["visual_editorial_decision"]
for key in ("social_mechanism_summary", "social_policy_summary", "social_cross_asset_summary"):
    assert ARTICLE[key] in ARTICLE["substack_body_markdown"]

# Compile only local previews with the same accepted code. This does not prepare
# a publication or write an operating-store return.
preview_article = dict(validated_article)
preview_article.update(
    public_source_bindings=OUTPUT["cited_sources"],
    reader_attribution_policy=GOVERNED["reader_attribution_policy"],
)
media = GOVERNED["editorial_media_plan"]["assets"]
preview_gate = {"status": "PASS"}
try:
    bundle, rows = _native_preview_bundle(
        article=preview_article,
        article_mode=GOVERNED["article_mode"],
        article_identity="cc124-gold-yields-20261105-e",
        epistemic_state=GOVERNED["epistemic_state"],
        media_asset_ids=[a["asset_id"] for a in media],
        media_assets=media,
    )
except SimpleGeminiNewsroomError as exc:
    # Preserve the actual owner-gate failure. A direct local payload inspection
    # below checks copy without asserting that this failed owner gate passed.
    preview_gate = {"status": "FAILED", "error": str(exc), "details": exc.details}
    compiler_article = _reader_safe_native_article(
        preview_article, article_mode=GOVERNED["article_mode"],
        epistemic_state=GOVERNED["epistemic_state"], legacy_presentation=False)
    compiler_article["native_media_sources"] = {a["asset_id"]: a["source_links"] for a in media if a.get("source_links")}
    compiler_article["native_destination_credits"] = {
        d: _derivative_media_attribution([a for a in media if a["asset_id"] in ids], compact=True)
        for d, ids in compiler_article["native_destination_media"].items()}
    payloads = build_native_derivative_payloads(
        article=compiler_article, selection={},
        canonical_url="https://capitalchronicle.substack.com/p/pending-publication-cc124-gold-yield",
        media_asset_ids=[a["asset_id"] for a in media])
    bundle = {"packages": payloads, "local_payload_audit_only": True, "owner_gate": preview_gate}
    rows = []


def weighted_length(text):
    # Twitter-text weights: URL = 23, default Unicode weight = 2, and its
    # standard four single-weight ranges. These copies contain no emoji.
    count = 0
    cursor = 0
    for match in re.finditer(r"https?://[^\s)]+", text):
        count += sum(1 if ord(c) <= 0x10FF or 0x2000 <= ord(c) <= 0x200D
                     or 0x2010 <= ord(c) <= 0x201F or 0x2032 <= ord(c) <= 0x2037 else 2
                     for c in text[cursor:match.start()]) + 23
        cursor = match.end()
    count += sum(1 if ord(c) <= 0x10FF or 0x2000 <= ord(c) <= 0x200D
                 or 0x2010 <= ord(c) <= 0x201F or 0x2032 <= ord(c) <= 0x2037 else 2
                 for c in text[cursor:])
    return count


payload_audit = {}
assert len(bundle["packages"]) == 8
for destination, payload in bundle["packages"].items():
    posts = payload.get("posts") or []
    texts = [p["text"] for p in posts] if posts else [str(payload.get(k) or "") for k in ("text", "full_text", "root_text", "caption")]
    visible = "\n\n".join(texts)
    for notice in ("Analysis, not financial advice.", "Capital Chronicle may hold positions in the markets it covers."):
        assert notice in visible, (destination, notice)
    payload_audit[destination] = {"both_notices_present": True, "media_asset_ids": payload.get("media_asset_ids"), "post_count": len(posts)}
    if destination in {"x", "threads"}:
        metrics = payload["quality_metrics"]
        assert metrics["sentence_boundary_pass"] is True
        assert metrics["orphan_fragment_count"] == 0
        assert metrics["hard_character_slicing_used"] is False
        limit = 280 if destination == "x" else 500
        assert all(weighted_length(text) <= limit for text in texts)
        payload_audit[destination].update(max_weighted_characters=max(map(weighted_length, texts)), platform_limit=limit, complete_sentences=True)

OBSERVATION = dict(json.loads((BASE / "desktop_response_visual-edit.json").read_text(encoding="utf-8"))["invocation_observation"])
OBSERVATION["configuration_source"] = "This exact supported continuation in the SAME native task context and frozen write request 3a768a46f25b3e19a9be67efe17dea1f890883e03e09025653b364038edb87ac request gpt-6.1-sol/max; configuration is not observed runtime telemetry."
RESPONSE = {"request_sha256": REQUEST["request_sha256"], "output": OUTPUT, "invocation_observation": OBSERVATION}


def main():
    response_path = BASE / "desktop_response_write.json"
    assert not response_path.exists(), "Preserve an already saved native writer return"
    response_path.write_text(json.dumps(RESPONSE, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence_path = Path(__file__).with_name("writer-local-validation.json")
    evidence = {
        "request_sha256": REQUEST["request_sha256"],
        "response_sha256": hashlib.sha256(response_path.read_bytes()).hexdigest(),
        "source_validation": validation,
        "local_preview_bundle": bundle,
        "local_preview_rows": rows,
        "native_preview_owner_gate": preview_gate,
        "payload_audit": payload_audit,
        "public_write_attempted": False,
        "final_assembled_pixel_review": "PENDING",
    }
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"response_path": str(response_path), "response_sha256": evidence["response_sha256"],
                      "validation_path": str(evidence_path), "schema": "PASS", "source_validation": validation["status"],
                      "supported_material_claim_count": validation["supported_material_claim_count"],
                      "native_preview_owner_gate": preview_gate,
                      "payload_audit": payload_audit}, ensure_ascii=False))


if __name__ == "__main__":
    main()
