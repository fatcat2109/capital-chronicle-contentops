"""Save the same native MAX writer's source-bound jobs-watch return."""

from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime
import json
import re

from live_contentops.native_desktop_editorial_v1 import validate_native_configuration
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    _validate_article_against_source_pack,
    _validate_worker_text,
)


BASE = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-nfp-us500-preview-20261105-g")
REQUEST = json.loads((BASE / "desktop_request_write.json").read_bytes())
assert REQUEST["request_sha256"] == "d897bc7ae5664d1bf5b645e8a29de389b5917396ce5721cb014fcea375e3d66f"
GOVERNED = REQUEST["governed_input"]
SOURCES = {s["source_id"]: s for s in GOVERNED["source_pack"]}

TITLE = "Jobs watch: weaker hiring can cut both ways for US stocks"
DEK = "September payrolls rose just 29,000, according to BLS. Ahead of the November 6 report, lower yields offer one possible offset to a weaker growth outlook."
SEARCH_TITLE = "Jobs report preview: rates relief versus S&P 500 earnings"
DESCRIPTION = "Why softer US hiring can ease rate pressure yet threaten earnings, and what unemployment, wages and revisions can clarify in the November 6 jobs report."
HOOK = "A weak jobs headline can ease rate pressure and weaken the earnings outlook at the same time. The S&P 500 needs both sides of that story."

MECHANISM = "Lower Treasury yields could support equity valuations if investors also lower the rate they use to value future profits."
COUNTERCASE = "Continued hiring, stable unemployment and moderating wage growth would fit orderly cooling. Rising unemployment and further downward revisions would strengthen the growth-risk interpretation."
WATCH = "A falling yield by itself will not distinguish relief about rates from worry about growth."

LEAD = "September's 29,000-job payroll gain leaves a useful question for US equity readers before Friday's report: is hiring cooling enough to ease rate pressure, or weakening enough to threaten profits? The Bureau of Labor Statistics schedules October's Employment Situation for November 6 at 8:30 a.m. EST. The result is still ahead."
FRAME = "Capital Chronicle's analysis is that the two channels need to be read separately. A lower discount rate, the rate used to translate future profits into today's value, could support share valuations. A weaker path for those profits could offset that support."
YIELDS = "Treasury's official nominal 10-year par yield was 4.90% on November 4, down from 5.31% on October 5. These are dated daily Treasury readings, not live prices. They do not establish what drove yields or how stocks responded."
RATE_CHANNEL = MECHANISM + " That support is conditional: investors could demand more compensation for owning equities, or cut their profit expectations."
EMPLOYMENT = "In its October 2 release, BLS put September payroll growth at 29,000 and unemployment at 4.2%. Private employers added 46,000 jobs: 18,000 in goods-producing industries and 28,000 in services. Subtracting the private gain from the total implies 17,000 fewer government jobs."
COMPOSITION = "That composition matters. A small overall gain can coexist with continued private hiring when government employment falls. The headline alone cannot tell us whether household demand or listed-company earnings will deteriorate."
REVISIONS = "The revisions softened the starting point. BLS put July and August employment a combined 60,000 below the previously reported levels. September's average hourly earnings for all private nonfarm employees rose 0.1% over the month and 3.0% over the year. These are September observations from the October 2 release."
UNEMPLOYMENT_CHECK = "First, unemployment: does a soft payroll number come with a stable unemployment rate, or a rise that points to a weaker labour market? September's 4.2% is the dated starting point."
WAGE_CHECK = "Second, wages: does slower hiring accompany moderating pay growth? That combination could be consistent with easing cost pressure. Persistent wage pressure alongside weak hiring would offer less reassurance; wages alone cannot establish the future path of inflation or company margins."
REVISION_CHECK = "Third, revisions and hiring breadth: do earlier gains hold up, and is hiring weakness broadening beyond the groups already losing jobs? The earlier downward revisions make that check useful, but they do not predict the next revision."
COUNTER = "The countercase to an earnings scare is orderly cooling. " + COUNTERCASE
NEXT = "After the release, compare those employment details with the observed Treasury yield response. " + WATCH
NOTICES = "Analysis, not financial advice. Readers decide whether to trade. Capital Chronicle may hold positions in the markets it covers."

PARAGRAPHS = [
    LEAD + " [[SOURCE:SOURCE_1]] [[SOURCE:SOURCE_3]]",
    FRAME + " [[SOURCE:SOURCE_1]] [[SOURCE:SOURCE_2]]",
    "## A lower yield is only half the equity story",
    YIELDS + " [[SOURCE:SOURCE_2]]",
    RATE_CHANNEL + " [[SOURCE:SOURCE_1]] [[SOURCE:SOURCE_2]]",
    "## The last jobs report was weak, but not uniform",
    EMPLOYMENT + " [[SOURCE:SOURCE_1]]",
    COMPOSITION + " [[SOURCE:SOURCE_1]]",
    REVISIONS + " [[SOURCE:SOURCE_1]]",
    "## Three checks beyond the payroll headline",
    UNEMPLOYMENT_CHECK + " [[SOURCE:SOURCE_1]]",
    WAGE_CHECK + " [[SOURCE:SOURCE_1]]",
    REVISION_CHECK + " [[SOURCE:SOURCE_1]]",
    COUNTER + " [[SOURCE:SOURCE_1]]",
    NEXT + " [[SOURCE:SOURCE_1]] [[SOURCE:SOURCE_2]] [[SOURCE:SOURCE_3]]",
    NOTICES + " [[SOURCE:SOURCE_1]]",
]

ARTICLE = {
    "title": TITLE,
    "dek": DEK,
    "search_title": SEARCH_TITLE,
    "meta_description": DESCRIPTION,
    "social_hook": HOOK,
    "substack_body_markdown": "\n\n".join(PARAGRAPHS),
    "reader_first_version": "DATA_JOURNALISM_V1",
    "reader_attribution_policy": GOVERNED["reader_attribution_policy"],
    "visual_editorial_decision": GOVERNED["visual_editorial_decision"],
    "analysis_scope": "OTHER_ANALYSIS",
    "analysis_scope_reason": GOVERNED["visual_editorial_decision"]["analysis_scope_reason"],
    "display_date": "5 November 2026",
    "social_mechanism_summary": MECHANISM,
    "social_policy_summary": COUNTERCASE,
    "social_cross_asset_summary": WATCH,
    "canonical_slug_candidate": GOVERNED["visual_editorial_decision"]["slug"],
    "primary_reader_question": "How can softer hiring ease rate pressure yet worsen the earnings outlook for US stocks?",
    "secondary_reader_questions": [
        "What does September's payroll composition add to the headline number?",
        "Why does a lower Treasury yield not settle the equity question?",
        "What would distinguish orderly labour-market cooling from growing demand risk?",
    ],
    "entities": ["S&P 500", "US equities", "U.S. Treasury", "U.S. Bureau of Labor Statistics"],
    "topics": ["Employment Situation", "Nonfarm payrolls", "Unemployment", "Wages", "Treasury yields", "Equity valuations"],
    "search_freshness_class": "DATED_EQUITY_RATES_EXPLANATION_WITH_SCHEDULED_JOBS_WATCH",
    "internal_link_candidates": [],
}

PAYROLL = "Both nonfarm payroll employment (+29,000) and the unemployment rate (4.2 percent) changed little in September, the U.S. Bureau of Labor Statistics reported today."
SURVEYS = "The household survey measures labor force status, including unemployment, by demographic characteristics. The establishment survey measures nonfarm employment, hours, and earnings by industry."
WAGES = "In September, average hourly earnings for all employees on private nonfarm payrolls edged up by 5 cents, or 0.1 percent, to $37.81. Over the past 12 months, average hourly earnings have increased by 3.0 percent."
REVISED = "With these revisions, employment in July and August combined is 60,000 lower than previously reported."
TABLE = SOURCES["SOURCE_1"]["canonical_content_text"].split("Table B-1.", 1)[1].strip()
CALENDAR = SOURCES["SOURCE_3"]["canonical_content_text"]
YIELD_NAME = "U.S. Treasury nominal 10-year par yields, 2 January through 4 November 2026; percent."
CLAIMS = []


def bind(claim_id, text, source_id, excerpt, kind="FACT"):
    assert excerpt in SOURCES[source_id]["canonical_content_text"], claim_id
    assert text in " ".join(str(ARTICLE.get(k, "")) for k in (
        "title", "dek", "search_title", "meta_description", "social_hook", "substack_body_markdown")), claim_id
    CLAIMS.append({
        "claim_id": claim_id, "claim_text": text, "claim_kind": kind,
        "source_id": source_id, "support_excerpt": excerpt, "attribution_required": True,
    })


# Conditional analysis binds to its factual premises; it is identified in the
# article as Capital Chronicle's analysis, never represented as a BLS forecast.
for field, text in (("title", TITLE), ("dek", DEK), ("search", SEARCH_TITLE), ("description", DESCRIPTION), ("hook", HOOK)):
    bind(field + "-jobs-premise", text, "SOURCE_1", PAYROLL, "CAUSALITY" if field != "dek" else "FACT")
    bind(field + "-rate-premise", text, "SOURCE_2", YIELD_NAME, "CAUSALITY")
for field, text in (("dek", DEK), ("description", DESCRIPTION)):
    bind(field + "-calendar", text, "SOURCE_3", CALENDAR)

bind("lead-dated-payroll", "September's 29,000-job payroll gain", "SOURCE_1", PAYROLL, "NUMBER")
bind("lead-conditional-reader-question", "is hiring cooling enough to ease rate pressure, or weakening enough to threaten profits?", "SOURCE_1", PAYROLL, "CAUSALITY")
bind("release-calendar", "The Bureau of Labor Statistics schedules October's Employment Situation for November 6 at 8:30 a.m. EST.", "SOURCE_3", CALENDAR)
bind("future-outcome-separation", "The result is still ahead.", "SOURCE_3", CALENDAR)
bind("house-analysis-label", "Capital Chronicle's analysis is that the two channels need to be read separately.", "SOURCE_1", PAYROLL)
bind("discount-rate-channel", "A lower discount rate, the rate used to translate future profits into today's value, could support share valuations.", "SOURCE_2", YIELD_NAME, "CAUSALITY")
bind("earnings-offset", "A weaker path for those profits could offset that support.", "SOURCE_1", PAYROLL, "CAUSALITY")
bind("yield-latest", "Treasury's official nominal 10-year par yield was 4.90% on November 4", "SOURCE_2", "2026-11-04 4.90", "NUMBER")
bind("yield-comparison", "down from 5.31% on October 5.", "SOURCE_2", "2026-10-05 5.31", "NUMBER")
bind("yield-date-meaning", "These are dated daily Treasury readings, not live prices.", "SOURCE_2", YIELD_NAME)
bind("causal-limitation", "They do not establish what drove yields or how stocks responded.", "SOURCE_2", YIELD_NAME, "CAUSALITY")
bind("conditional-mechanism", MECHANISM, "SOURCE_2", YIELD_NAME, "CAUSALITY")
bind("conditional-equity-offset", "That support is conditional: investors could demand more compensation for owning equities, or cut their profit expectations.", "SOURCE_2", YIELD_NAME, "CAUSALITY")
bind("dated-release-payroll-unemployment", "In its October 2 release, BLS put September payroll growth at 29,000 and unemployment at 4.2%.", "SOURCE_1", PAYROLL, "NUMBER")
bind("private-employer-groups", "Private employers added 46,000 jobs: 18,000 in goods-producing industries and 28,000 in services.", "SOURCE_1", TABLE, "NUMBER")
bind("government-derived", "Subtracting the private gain from the total implies 17,000 fewer government jobs.", "SOURCE_1", TABLE, "NUMBER")
bind("composition-reading", "A small overall gain can coexist with continued private hiring when government employment falls.", "SOURCE_1", TABLE)
bind("earnings-not-observed", "The headline alone cannot tell us whether household demand or listed-company earnings will deteriorate.", "SOURCE_1", PAYROLL, "CAUSALITY")
bind("revision-interpretation", "The revisions softened the starting point.", "SOURCE_1", REVISED)
bind("prior-month-revisions", "BLS put July and August employment a combined 60,000 below the previously reported levels.", "SOURCE_1", REVISED, "NUMBER")
bind("wages-dated", "September's average hourly earnings for all private nonfarm employees rose 0.1% over the month and 3.0% over the year.", "SOURCE_1", WAGES, "NUMBER")
bind("employment-period-separation", "These are September observations from the October 2 release.", "SOURCE_1", WAGES)
bind("unemployment-check", UNEMPLOYMENT_CHECK, "SOURCE_1", PAYROLL, "CAUSALITY")
bind("wages-check", WAGE_CHECK, "SOURCE_1", WAGES, "CAUSALITY")
bind("revision-check", REVISION_CHECK, "SOURCE_1", REVISED)
bind("revision-breadth-check", REVISION_CHECK, "SOURCE_1", TABLE)
bind("orderly-cooling-countercase", COUNTERCASE, "SOURCE_1", PAYROLL, "CAUSALITY")
bind("countercase-wage-premise", COUNTERCASE, "SOURCE_1", WAGES, "CAUSALITY")
bind("countercase-revision-premise", COUNTERCASE, "SOURCE_1", REVISED, "CAUSALITY")
bind("next-employment-check", "After the release, compare those employment details with the observed Treasury yield response.", "SOURCE_3", CALENDAR)
bind("next-yield-check", WATCH, "SOURCE_2", YIELD_NAME, "CAUSALITY")

USED = {"SOURCE_1", "SOURCE_2", "SOURCE_3"}
OUTPUT = {
    "schema_version": "contentops.v1_simple_gemini_article.v1",
    "article": ARTICLE,
    "cited_sources": [{k: s[k] for k in ("source_id", "url", "publisher", "published_at_utc")}
        for s in GOVERNED["source_pack"] if s["source_id"] in USED],
    "material_claim_bindings": CLAIMS,
    "public_write_attempted": False,
}

assert Decimal("29") - Decimal("46") == Decimal("-17")
assert Decimal("18") + Decimal("28") - Decimal("17") == Decimal("29")
assert Decimal("159015") - Decimal("135671") == Decimal("23344")
assert Decimal("159044") - Decimal("135717") == Decimal("23327")
assert Decimal("23327") - Decimal("23344") == Decimal("-17")
assert Decimal("4.90") < Decimal("5.31")
release = datetime(2026, 11, 6, 8, 30, tzinfo=ZoneInfo("America/New_York"))
assert release.tzname() == "EST"
assert release.utcoffset().total_seconds() == -18000
assert len(DESCRIPTION) <= 160
for key in ("social_mechanism_summary", "social_policy_summary", "social_cross_asset_summary"):
    assert ARTICLE[key] in ARTICLE["substack_body_markdown"]
assert ARTICLE["visual_editorial_decision"] == GOVERNED["visual_editorial_decision"]
for chart in GOVERNED["visual_editorial_decision"]["charts"]:
    assert "## " + chart["placement_after"] in ARTICLE["substack_body_markdown"]
    assert chart["asset_id"] in {a["asset_id"] for a in GOVERNED["editorial_media_plan"]["assets"]}
assert "\ufffd" not in " ".join(ARTICLE[k] for k in ("title", "dek", "search_title", "meta_description", "social_hook", "substack_body_markdown"))
ok, failure_class, _, reason = _validate_worker_text(json.dumps(OUTPUT))
assert ok, (failure_class, reason)
_, validation = _validate_article_against_source_pack(
    OUTPUT, GOVERNED["source_pack"], selected_candidate=GOVERNED["selected_candidate"],
    article_mode=GOVERNED["article_mode"], epistemic_state=GOVERNED["epistemic_state"],
)

observation = json.loads((BASE / "desktop_response_visual-edit.json").read_bytes())["invocation_observation"]
observation["observation_source"] = (
    "Supported native canonical task context /root/native_max_jobs_ed46a179bd88 continued through visual selection, "
    "exact local asset inspection and this corrected writer request in the same context. The actual parent "
    "collaboration assignment supplies the configured role; runtime model/effort telemetry is unavailable."
)
validate_native_configuration(observation, {"model": "gpt-6.1-sol", "reasoning_effort": "max", "speed": "standard"})
response = {"request_sha256": REQUEST["request_sha256"], "output": OUTPUT, "invocation_observation": observation}
response_path = BASE / "desktop_response_write.json"
response_path.write_text(json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
summary = {
    "request_sha256": REQUEST["request_sha256"],
    "response_path": str(response_path), "response_sha256": sha256(response_path.read_bytes()).hexdigest(),
    "title": TITLE, "schema_validation": "PASS", "source_claim_validation": validation["status"],
    "supported_material_claim_count": validation["supported_material_claim_count"],
    "cited_source_count": validation["cited_source_count"], "public_write_attempted": False,
    "body_word_count": len(re.sub(r"\[\[SOURCE:SOURCE_\d+\]\]", "", ARTICLE["substack_body_markdown"]).split()),
    "assembled_render_review": "PENDING", "model_and_effort_observation": "CONFIGURED_NOT_OBSERVED",
}
summary_path = Path(__file__).with_name("writer-local-validation.json")
summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary))
