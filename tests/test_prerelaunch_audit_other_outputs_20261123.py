"""Pre-relaunch audit of the public outputs other than the plan posts (Ops Product Builder, 23 Nov 2026).

Each test names the defect found in a stored output of 19-23 Nov and checks the fix on new copy only;
stored copy keeps its bytes (the gates are a manuscript revision, a board date, a source marker or a
clock). Every fixture here is synthetic; no test reads the production store or a live export.
"""
from datetime import date, datetime, timezone

import pytest

from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_reader_editorial_v1 as editorial


# Plan pages (Substack) ------------------------------------------------------------------

def test_group_thousands_prices_and_counts_but_never_years_dates_clocks_or_names():
    text = ("Forced sellers sit under 57651.78; the jump topped at 3630.94; support at 3568 to 3570; "
            "1888 signals; stop 68450.00; since 2021 and the 2026 floor; on 2026-11-20 at 13:30; "
            "US500 beta 1.35; S&P 500; already 61,940.88; hash 4462cfd99426; -20.2%.")
    assert pages.group_thousands(text) == (
        "Forced sellers sit under 57,651.78; the jump topped at 3,630.94; support at 3,568 to 3,570; "
        "1,888 signals; stop 68,450.00; since 2021 and the 2026 floor; on 2026-11-20 at 13:30; "
        "US500 beta 1.35; S&P 500; already 61,940.88; hash 4462cfd99426; -20.2%.")


@pytest.mark.parametrize("text, cause", [
    ("Capitulation.", "FRAGMENT"),
    ("Claim 4 and its evidence.", "INTERNAL_WORDING"),
    ("The book already holds the same direction in the MID lane.", "INTERNAL_WORDING"),
    ("The Gulf of Oman incident is not officially confirmed in the frozen files, so no premium is assumed.",
     "INTERNAL_WORDING"),
    ("Sized STARTER because Bitcoin's ten-year short rows are near zero.", "INTERNAL_WORDING"),
    ("After entry the broker stop at 3609.00.", "INTERNAL_WORDING"),
    ("DVOL 45.88 on 19 Nov (cc415, one day old) implied a 6.35% week.", "INTERNAL_WORDING"),
    ("The US front end through today's retail sales, and risk appetite.", "RELATIVE_DAY"),
    ("BTCUSD is below 60977.64 at 2026-11-25T03:00Z on the main path.", "UTC_CLOCK"),
])
def test_an_analyst_sentence_that_cannot_stand_alone_in_public_is_named(text, cause):
    assert pages.public_span_problem(text) == cause


def test_a_public_analyst_sentence_passes():
    assert pages.public_span_problem(
        "Forced sellers sit under 57,651.78 and 55,063.63, with short covering above 61,581.46.") is None


def test_a_sentence_cut_after_a_clock_abbreviation_is_rejoined():
    spans = ["The plan holds through the US reports on 25 Nov at 8:30 a.m.",
             "ET and the jobs report on 4 Dec at 8:30 a.m.", "ET, and is closed on 9 Dec.",
             "Prices fell at 9 a.m.", "Gold then rose."]
    assert pages.join_abbreviation_spans(spans) == [
        "The plan holds through the US reports on 25 Nov at 8:30 a.m. ET and the jobs report on 4 Dec "
        "at 8:30 a.m. ET, and is closed on 9 Dec.", "Prices fell at 9 a.m.", "Gold then rose."]


def _case(heading, *support):
    return {"heading": heading, "support": list(support), "refs": []}


def test_revision_8_cases_drop_fragment_drivers_and_group_numbers():
    cases = editorial._public_cases([
        _case("Base case (54%): BTCUSD is below 60977.64 at Tue 24 Nov, 10:00 PM ET.",
              "What would undo the base case: Stop tightening fact.",
              "Base case driver: A 20-session downtrend under a tightening rate backdrop."),
        _case("Bull case (46%): BTCUSD holds the 57,650 floor.", "Bull case driver: Capitulation.",
              "What would undo the bull case: The view is unchanged and this WATCH registers that level."),
    ])
    assert cases[0]["heading"] == "Base case (54%): BTCUSD is below 60,977.64 at Tue 24 Nov, 10:00 PM ET."
    assert cases[0]["support"] == ["Base case driver: A 20-session downtrend under a tightening rate backdrop."]
    assert cases[1]["support"] == []


def test_revision_8_prints_a_case_line_once_even_when_its_short_wording_was_replaced():
    cases = [_case("Bull case (46%): BTCUSD squeezes higher.",
                   "Bull case driver: The rejected break is a spring and trapped traders positioned for losses "
                   "fuel a squeeze through 61,581.46 toward 62,571.63.")]
    repeat = {"text": "The rejected break is a spring and trapped shorts fuel a squeeze through 61,581.46 "
                      "toward 62,571.63.", "refs": [{}]}
    other = {"text": "Funding, open interest and ETF flows were not observed.", "refs": [{}]}
    sections = {"scenarios": {"paragraphs": [repeat], "summary": repeat["text"]},
                "positioning": {"paragraphs": [other], "summary": other["text"]}}
    editorial._drop_case_repeats(sections, cases)
    assert sections["scenarios"] == {"paragraphs": [], "summary": ""}
    assert sections["positioning"]["paragraphs"] == [other]


def test_new_page_revision_is_8_and_older_manuscripts_keep_their_own_revision():
    assert editorial.PAGE_COPY_REVISION == 8 == pages.PUBLIC_COPY_REVISION


def _geometry_run(frozen_at):
    leg = {"entry_bounds": {"minimum": 3508, "maximum": 3546}, "stop_level": 3480, "target_level": 3300}
    native = {"native_synthesis": {"candidates": [{"candidate_id": "cand_macro_gold",
                                                   "directional_entries": {"pullback": leg, "breakout": leg}}]}}
    return {"freeze": {"frozen_at_utc": frozen_at}, "documents": {"analysis-native.json": native}}


def test_an_old_format_page_frozen_after_decision_157_prints_no_target():
    plan = {"asset_id": "XAUUSD", "zone": {"minimum": 3508, "maximum": 3546}}
    before, _ = pages._public_geometry(plan, _geometry_run("2026-11-22T21:09:02Z"))
    after, bindings = pages._public_geometry(plan, _geometry_run("2026-11-22T21:09:03Z"))
    assert all("model objective: 3,300" in line for line in before)  # stored pages keep their bytes
    assert after and not any("objective" in line or "3,300" in line for line in after)
    assert not any(ref["pointer"].endswith("target_level") for b in bindings for ref in b["refs"])


# Market wrap ---------------------------------------------------------------------------------

def test_wrap_lines_use_timeframe_words_grouped_numbers_and_never_the_desks_own_book():
    from live_contentops import market_wrap_editorial_v1 as wrap
    assert wrap.public_line("Zone reason: a completed M15 close below 58630.87 would create a fresh test.") == (
        "Zone reason: a completed 15-minute close below 58,630.87 would create a fresh test.")
    assert wrap.public_line("Base case (50%): keep the incremental USDJPY view flat and do not add to the "
                            "existing short.") is None
    assert wrap.public_line("Main's analysis points to the carry trade.") is None


def test_wrap_stops_line_never_names_main():
    from live_contentops import market_wrap_sources_v1 as sources
    day = date(2026, 11, 20)
    plan = {"asset_id": "XAUUSD", "outcome": {"state": "SCORED", "score": {
        "result": "STOPPED", "resolved_at_utc": "2026-11-20T15:00:00Z", "scored_at_utc": "2026-11-20T15:05:00Z"}}}
    export = {"status": {"scored_call_count": 1, "plans": [plan]}}
    text = sources.prior_stops(export, day, datetime(2026, 11, 21, tzinfo=timezone.utc))
    assert text.startswith("- A ") and "plan was stopped on" in text and "Main" not in text
    assert sources.prior_stops({"status": {"scored_call_count": 0, "plans": []}}, day,
                               datetime(2026, 11, 21, tzinfo=timezone.utc)) == (
        "No plan was stopped in the last completed cash session.")


# Daily trend board ---------------------------------------------------------------------------

def test_board_from_24_nov_names_rules_in_scenario_words_and_earlier_boards_keep_their_copy():
    from test_daily_trend_board_cc537 import at, source
    from live_contentops import daily_trend_board_v1 as board
    old = board.project(source("2026-11-23"), now=at("2026-11-23"))
    new = board.project(source("2026-11-24"), now=at("2026-11-24"))
    assert "public_voice" not in old and new["public_voice"] == "SCENARIO_WORDS_V1"
    old_text = "\n".join(board.compose(old)["blocks"])
    new_text = "\n".join(board.compose(new)["blocks"])
    assert "Short with trend, 20 sessions (short)" in old_text
    assert "Follow a downtrend, 20 sessions (bearish)" in new_text
    assert " short" not in new_text.casefold().replace("(bearish)", "")
    reference = {"canonical_url": "https://capitalchronicle.substack.com/p/method"}
    asset = {"asset_id": "card"}
    assert "Historical model estimates" in board.payloads(old, None, reference, asset)["substack_notes"][0]["text"]
    new_note = board.payloads(new, None, reference, asset)["substack_notes"][0]["text"]
    assert "Historical estimates after costs" in new_note and "model" not in new_note


# X reply drafts ------------------------------------------------------------------------------

def test_reply_fact_prints_its_market_precision_only_on_new_sources():
    from live_contentops import x_reply_fact_sources_v1 as facts
    assert facts.display_value(82.86000061035156, "USOIL", "USD") == "82.86"
    assert facts.display_value(82.19999694824219, "USOIL", "USD") == "82.20"
    assert facts.display_value(103.73400115966797, "DXY", "points") == "103.734"
    assert facts.display_value(4.920000076, "US10Y", "percent") == "4.92"
    observation = {"market": "USOIL", "value": 82.86000061035156, "unit": "USD", "instrument_name": "WTI crude oil",
                   "source": "Yahoo Finance", "observed_at_utc": "2026-11-20T02:50:00+00:00",
                   "known_at_utc": "2026-11-20T02:51:00+00:00", "observation_path": "o.json",
                   "observation_sha256": "0" * 64, "day_change": -0.5300000000000011}
    held = facts._quote_source(observation)
    fresh = facts._quote_source({**observation, "display": facts.DISPLAY})
    assert "82.86000061035156" in held["excerpt"]  # a held fact re-resolves to its exact identity
    assert "WTI crude oil: 82.86 USD, change from prior close -0.53 USD (Yahoo Finance," in fresh["excerpt"]
    assert held["source_id"] != fresh["source_id"]


def test_reply_drafts_from_the_relaunch_week_name_their_day():
    from live_contentops import x_reply_pack_v1 as pack
    text = "If Bitcoin closes down today, a higher next close has a slight historical edge."
    pack._check_dated(text, datetime(2026, 11, 23, 23, 59, tzinfo=timezone.utc))
    with pytest.raises(ValueError, match="REPLY_RELATIVE_DAY_FORBIDDEN"):
        pack._check_dated(text, datetime(2026, 11, 24, tzinfo=timezone.utc))
    pack._check_dated("If Bitcoin closes down on 24 Nov, the next close rose more often.",
                      datetime(2026, 11, 24, tzinfo=timezone.utc))


# Posting desk --------------------------------------------------------------------------------

def test_desk_leaves_out_a_relative_day_line_and_keeps_the_call():
    """The 22 Nov USD/JPY result pack re-quoted its 17 Nov setup: "through today's retail sales"."""
    from live_contentops import manual_desk_v1 as desk
    base = ("USD/JPY: bearish below 158.88.\nMacro: The US front end through today's retail sales.\n"
            "Positioning: Speculators were net long 123,113 yen contracts on 10 Nov.")
    text = desk.compose_text(base, lead="USD/JPY: bearish below 158.88.", link=None, limit=3000, dated=True)
    assert "today" not in text.casefold() and "retail sales" not in text
    assert text.startswith("USD/JPY: bearish below 158.88.") and "123,113 yen contracts on 10 Nov" in text
    parts = desk.compose_x_thread(base, lead="USD/JPY: bearish below 158.88.", link=None, dated=True)
    assert not any("today" in part.casefold() for part in parts)
    # The stored automatic copy itself is not rewritten; only a fresh pack leaves the line out.
    assert "today's retail sales" in desk.compose_text(base, lead="USD/JPY: bearish below 158.88.", link=None,
                                                       limit=3000)


# Corrections ---------------------------------------------------------------------------------

def test_a_new_correction_body_passes_the_public_copy_rules():
    from live_contentops import correction_reply_v1 as correction
    correction.check_body("USD/JPY: a note on the post above. It is the final result of our earlier plan, "
                          "registered on 17 Nov, and it was posted late.")
    with pytest.raises(ValueError):
        correction.check_body("Gold: a note on the post above. The target level: 3,300 was reached.")
    with pytest.raises(ValueError, match="CORRECTION_RELATIVE_DAY_FORBIDDEN"):
        correction.check_body("Gold: a note on the post above. Its result follows today.")
    with pytest.raises(ValueError):
        correction.check_body("Gold: a note on the post above, written by Claude.")


# Scorecard -----------------------------------------------------------------------------------

def test_empty_scorecard_never_names_main():
    from live_contentops import pinned_result_scorecard_v1 as scorecard
    text, shown = scorecard.render([], {"total": 0, "HIT": 0, "STOPPED": 0, "EXPIRED": 0, "NOT_TRIGGERED": 0,
                                        "scored": 0})
    assert "No resolved calls yet." in text and "Main" not in text and shown == 0


# Substack daily Note -------------------------------------------------------------------------

def test_a_note_from_24_nov_refuses_a_relative_day_and_an_earlier_note_keeps_its_rules():
    from live_contentops import substack_daily_note_v1 as note
    first = "Rate futures on 20 Nov priced a December hike near 86% today, a headwind for gold."
    second = "Our base case favours downside below 3,566; a close above 3,609 ends it."
    page = {"manuscript": {"sections": {"macro": {"paragraphs": [{"text": first}]},
                                        "technical": {"paragraphs": [{"text": second}]}}}}
    authored = {"sentences": [
        {"text": first, "section": "macro", "source_excerpt": first, "fact_date": "20 Nov"},
        {"text": second, "section": "technical", "source_excerpt": second}],
        "view": "Our base case favours downside below 3,566", "invalidation": "a close above 3,609 ends it"}
    assert note.validate_copy(authored, page, strict=False)
    with pytest.raises(ValueError, match="NOTE_RELATIVE_DAY_FORBIDDEN"):
        note.validate_copy(authored, page)


def test_plans_that_ended_while_posting_was_paused_are_in_the_scorecard_with_tick_levels():
    """Jim's pause (23 Nov 04:50Z to the relaunch): such results are shown by the pinned scorecard."""
    from datetime import timedelta
    from test_pinned_result_scorecard_cc394 import call
    from live_contentops import pinned_result_scorecard_v1 as scorecard
    now = datetime(2026, 11, 30, 18, tzinfo=timezone.utc)
    older = [call(f"old-{i:02}", "STOPPED", at=f"2026-11-{10 + i // 10:02}T08:{i % 10:02}:00Z") for i in range(30)]
    paused = [call("paused-hit", "HIT", at="2026-11-23T06:00:00Z"),
              call("paused-stop", "STOPPED", at="2026-11-27T15:00:00Z")]
    plans = older + paused
    source = {"status": {"schema": "CapitalChroniclePlanStatusV1", "schema_version": "1.0.0",
              "generated_at_utc": (now - timedelta(seconds=10)).isoformat(), "content_hash": "source-hash",
              "scored_call_count": len(plans), "plans": plans},
              "transitions": {"schema": "CapitalChroniclePlanTransitionsV1", "schema_version": "1.0.0",
              "generated_at_utc": now.isoformat(), "status_content_hash": "source-hash", "transitions": [
                  {"plan_id": p["plan_id"], "status": "EXPIRED", "at_utc": p["expires_at_utc"],
                   "reason_code": "EXPIRED"} for p in plans]}}
    record = scorecard.project(source, now=now)
    shown = record["text"].split("\n\n")[1].splitlines()
    assert shown[0].startswith("2026-11-27 ET") and shown[0].endswith("| STOPPED")
    assert shown[1].startswith("2026-11-23 ET") and shown[1].endswith("| HIT")
    assert "entry zone 6,000.5–6,005.5 (plan levels)" in shown[0]
    assert "model" not in record["text"].casefold() and "Main" not in record["text"]
