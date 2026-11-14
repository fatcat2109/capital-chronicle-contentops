"""Prepare CC-107's dated review through the existing verified source adapter."""
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from live_contentops.main_report_projection_source_v1 import _event_output_text, verify_projection

HERE = Path(__file__).resolve().parent
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
LIVE_HERE = LIVE / "docs/publisher/CC-107/run-20261114"
RESEARCH = Path(r"A:\Capital Chronicle\ResearchRuns")


def save(name, value):
    path = HERE / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def computed(path, pointer):
    passage = {"source_path": str(path), "source_sha256": sha256(path.read_bytes()).hexdigest(),
        "source_json_pointer": pointer, "event_id": "US_NFP_20261106"}
    text = _event_output_text(path.resolve(), passage, path.read_bytes())
    passage["fragments"] = [{"start": 0, "end": len(text)}]
    return passage


arrival = json.loads((ROOT / "docs/publisher/CC-107/run-20261106/nfp-review-held-arrival.json").read_bytes())["source_spec"]
preview = json.loads((ROOT / "docs/publisher/CC-107/run-20261106/source/index.json").read_bytes())["records"][0]
reaction = RESEARCH / "main-event-reaction-tables/tables/20261109T091537Z/US_NFP_20261106/20261106T133000Z.json"
scores = RESEARCH / "main-event-forecast-scores/event-scores-US_NFP_20261106-20261109T091537Z.json"
spec = {"authorship_class": "CAPITAL_CHRONICLE_MAIN_REPORT_PROJECTION", "authority_ref": "JIM_DECISION_89",
    "headline_id": "cc107-nfp-dated-review-20261114",
    "headline_text": "Capital Chronicle NFP review: the Strong branch and the measured market response",
    "source_url": "urn:cc-public-report:cc107:nfp-review:20261114",
    "known_at_utc": "2026-11-09T09:15:37.302916Z",
    "revision_at_utc": "2026-11-09T09:15:37.302916Z",
    "candidate_catalyst_tags": ["EVENT_REVIEW", "bls-emsit-20261106", "NFP"],
    "passages": [*arrival["passages"], *preview["passages"],
        *[computed(reaction, f"/intraday_reaction/markets/{market}/returns_pct")
            for market in ["EURUSD", "USDJPY", "XAUUSD", "US500", "USOIL"]],
        computed(scores, "/scores/36")],
    "supporting_headline_ids": ["bls-october-release", "bls-october-sectors"]}
record = verify_projection(spec)
save("source/index.json", {"schema_version": "contentops.retained_source_research.v1", "records": [spec]})
save("source-verification.json", {"headline_id": record["headline_id"],
    "source_hashes": record["research_metadata"]["source_hashes"],
    "document_sha256": record["document"]["canonical_content_sha256"],
    "known_at_utc": record["known_at_utc"], "original_preview_unchanged": True,
    "computed_reuse_authority": "JIM_DECISION_72_B", "raw_price_and_consensus_inputs_projected": False})
pointer = json.loads((LIVE / "config/native_desktop_main_feed_binding_v1.json").read_bytes())
pointer.pop("public_export_root", None)
pointer.update(research_root=str(LIVE / "docs/publisher/CC-124/run-20261106-2050/source"),
    research_editions_root=[str(LIVE_HERE / "source")], review_event_id="bls-emsit-20261106")
save("feed-pointer.json", pointer)
profile = json.loads((LIVE / "config/native_desktop_operator_profile_v1.json").read_bytes())
profile.update(feed_pointer_path=str(LIVE_HERE / "feed-pointer.json"), research_editions_root=[])
save("operator-profile.json", profile)
request = """Complete CC-107's EVENT_REVIEW of the 6 November NFP release, written now as a dated retrospective, through the existing native article route. Select cc107-nfp-dated-review-20261114. The November 6 NFP preview and November 10 CPI preview already exist; never rewrite or repost them. The current writing date is 14 November 2026 ET; source, observation, score-generation and publication clocks stay separate.

Use the supplied Main frozen Strong/Weak conditions, exact arrival outcome, current-release official BLS sources, prior official 24-month histories and Main's computed reaction timeline. The Strong release combination held. Main's computed intraday market returns describe co-movement only, not a causal proof, a fill or a profit. Explain the first observed five-minute and sixty-minute windows in ET without inventing a first-day observation, a pre-event range break, a bond-yield move or a sector return. Missing first-day/rates/sector measurements limit those claims, never the supported review.

CC-106 supplies a separate historical-frequency categorical comparison, PIT_CLEAN with RESEARCH_PREPARATION evidence: the observed category is IN_LINE; the matrix Brier score is 0.02 and the consensus-only Brier is 0 for Investing's baseline (the source adapter formats Main's pinned score to twelve significant digits). Lower is better. This is one event, not two independent successes and not a score of the published preview's Strong/Weak conditions. The prediction-market-only comparison is unavailable; do not invent it or print numerical prediction-market odds. Label our computed outputs Capital Chronicle model estimate, including measured derived market changes, and retain all provenance privately. An old source public_eligible flag does not hide our computed outputs under decision 72 b; raw broker prices, third-party tables and account/execution details remain private.

Lead in first person with the call and the lesson. Keep the supplied event-resolution frame and exact article.event_article_packet. Use the frozen supported scenarios, confirmation and invalidation without inventing odds or complements. Use natural attribution and a So what line, source-bound public numbers and ET public times. This is a retrospective report, never current market guidance. No entries, stops, targets, sizes, trade advice, invented market reaction or performance/alpha claim. Source facts and computed values come from the admitted documents; prose never recalculates them.

The MAX writer chooses useful official-history and latest-month/components charts under CC-142 and may reuse the reviewed CC-216 background as source context. Use fresh image bytes for this piece through the existing media owner, retain lineage and any lawful photo credits, and follow the existing review and sole canonical-first coordinator. No new schedule, chat message, Claude call or second publisher. Notices: Capital Chronicle offers analysis only, not financial advice or recommendations. Capital Chronicle may hold positions in the markets it covers.
"""
(HERE / "editorial-request.txt").write_text(request, encoding="utf-8")
print(json.dumps({"source_verified": record["headline_id"], "public_text_characters": len(record["permitted_source_text"]),
    "source_paths": len(record["research_metadata"]["source_hashes"]), "profile": str(LIVE_HERE / "operator-profile.json")}))
