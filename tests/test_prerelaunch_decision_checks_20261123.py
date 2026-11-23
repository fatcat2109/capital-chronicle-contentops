"""Pre-relaunch audit (23 Nov 2026) of the evening decision checks over the stored posts of 19-23 Nov.

Each test is one false or missed failure found on the copied store, or the paused-day report.
"""
import json
import sqlite3

import pytest

from live_contentops import day_readback_v1 as readback
from live_contentops.public_decision_checks_v1 import (DecisionChecks, notice_counts, pause_windows,
                                                      plan_scenario_flags)
from test_day_readback_cc639 import build, recorded  # noqa: F401

NOTICES = ("Capital Chronicle offers analysis only, not financial advice or recommendations. "
           "Capital Chronicle may hold positions in the markets it covers.")
PAGE = "https://capitalchronicle.substack.com/p/bitcoin-bearish-at-6000061400-wrong"


def checks(runtime, start="2026-11-22T12:15:00Z", end="2026-11-23T12:15:00Z"):
    return DecisionChecks({"since_utc": start, "until_utc": end}, runtime)


def posted(audit, piece, platform, *, text, source, native=None, intent=None, object_id="1",
           at="2026-11-22T23:00:00Z", url=None, readback_fields=None):
    proof = {"verified": True, "identity_match": True, "observed_public_object_id": object_id,
             "observed_published_at_utc": at, **(readback_fields or {})}
    return audit.add(piece, platform, url or f"https://t.me/CapitalChronicle/{object_id}", "", text,
                     {"native_payload": {"text": text, **(native or {})}, **(intent or {})},
                     {"status": "DISPATCH_CONFIRMED", "public_object_id": object_id, "dispatched_at": at,
                      "created_at": at},
                     [(at, {"readback": proof})], source)


def by_decision(result, decision):
    return [(row["platform"], row["status"], row["first_cause"]) for row in result["issues"]
            if row["decision"] == decision]


def test_target_fails_only_under_decision_157(tmp_path):
    # 22 Nov 19:27Z BTC setup (t.me/CapitalChronicle/226) printed "Target level: 53,000." before the
    # 22:30Z policy: listed, not failed. A row marked DECISION_40_NO_TARGET with a target still fails.
    audit = checks(tmp_path)
    text = "Bitcoin: armed.\nTarget level: 53,000.\n" + NOTICES
    old = {"kind": "setup", "key": "plan-status-post-old", "decision_source_created_at_utc": "2026-11-22T19:25:00Z"}
    new = {"kind": "setup", "key": "plan-status-post-new", "target_policy": "DECISION_40_NO_TARGET",
           "decision_source_created_at_utc": "2026-11-23T02:47:00Z"}
    late = {"kind": "update", "key": "plan-status-post-late", "decision_source_created_at_utc": "2026-11-23T01:00:00Z"}
    posted(audit, "plan-status-post-old", "telegram", text=text, source=old, object_id="226",
           at="2026-11-22T19:27:13Z")
    posted(audit, "plan-status-post-new", "telegram", text=text, source=new, object_id="229",
           at="2026-11-23T02:48:16Z")
    posted(audit, "plan-status-post-late", "discord", text=text, source=late, object_id="9",
           at="2026-11-23T01:01:00Z", url="https://discord.com/channels/1/2/9")
    result = audit.finish({}, {})
    rows = {row["piece_id"]: row["status"] for row in result["issues"] if row["decision"] == "157"}
    assert rows == {"plan-status-post-old": "BEFORE_POLICY", "plan-status-post-new": "FAIL",
                    "plan-status-post-late": "FAIL"}
    target = next(row for row in result["checks"] if row["decision"] == "157")
    assert (target["failed"], target["before_policy"]) == (2, 1)


@pytest.mark.parametrize(("line", "rule"), [
    ("Cancel if spot price trades at or above 3,609 before entry.", "INVALIDATION_LEVEL_MISSING"),
    ("Bitcoin plan cancelled on high at or above 68,450 before entry.", "INVALIDATION_LEVEL_MISSING"),
    ("We are bearish on Gold if price breaks through 3,566 (breakout).", "ENTRY_ZONE_MISSING"),
])
def test_voice_reads_the_plans_own_cancel_and_breakout_lines(line, rule):
    assert rule in plan_scenario_flags("Gold: waiting.")
    assert rule not in plan_scenario_flags("Gold: waiting. " + line)


def test_net_positioning_is_not_a_position_word():
    text = ("Speculators were net long 123,113 contracts; funds are net-short the euro. Short covering "
            "lifted Bitcoin. We are bearish.")
    assert "POSITION_WORDS_REPEATED" not in plan_scenario_flags(text)
    assert "POSITION_WORDS_REPEATED" in plan_scenario_flags("Go long here, then go long again.")


def test_threads_replies_of_a_confirmed_dispatch_are_read_with_the_root(tmp_path):
    # Threads 20 Nov 08:17Z (USD/JPY): the readback verified only the root; the frozen reply carried the
    # target and the second copy of both notices (the CC-729 Threads double).
    audit = checks(tmp_path, "2026-11-22T22:00:00Z", "2026-11-23T12:15:00Z")
    source = {"kind": "setup", "key": "plan-status-post-usdjpy", "target_policy": "DECISION_40_NO_TARGET"}
    root = "USD/JPY: armed.\n" + NOTICES
    reply = "Target level: 157.95.\n" + NOTICES
    posted(audit, "plan-status-post-usdjpy", "threads", text=root, source=source, object_id="1801",
           url="https://www.threads.com/@official.capitalchronicle/post/abc",
           native={"root_text": root, "reply_texts": [reply]},
           readback_fields={"content_binding_checks": {"text_match": True}})
    result = audit.finish({}, {})
    assert ("threads", "FAIL", "PUBLIC_PLAN_TARGET_PRESENT") in by_decision(result, "157")
    notice = next(row for row in result["issues"] if row["decision"] == "CC-729")
    assert (notice["first_cause"], notice["notice_counts"]) == (
        "PUBLIC_NOTICE_REPEATED", {"analysis_notice": 2, "conflicts_notice": 2})


def test_one_notice_each_passes_and_counts():
    assert notice_counts("Gold.\n" + NOTICES) == {"analysis_notice": 1, "conflicts_notice": 1}


def test_a_dedicated_analysis_link_reply_counts_after_an_update_reply(tmp_path):
    # Telegram 226 (BTC setup): update 227 replied first at 19:29Z; the page link reply 228 followed at 19:58Z.
    audit = checks(tmp_path)
    setup = {"kind": "setup", "key": "plan-status-post-btc", "plan_id": "plan_btc"}
    update = {"kind": "update", "key": "plan-status-post-btc-update", "plan_id": "plan_btc"}
    posted(audit, "plan-status-post-btc", "telegram", text="Bitcoin: armed.\n" + NOTICES, source=setup,
           object_id="226", at="2026-11-22T19:27:13Z")
    posted(audit, "plan-status-post-btc-update", "telegram", text="Bitcoin: still armed.", source=update,
           object_id="227", at="2026-11-22T19:29:43Z",
           native={"reply_to_id": "226", "reply_to_url": "https://t.me/CapitalChronicle/226"})
    posted(audit, "plan-analysis-link-plan_btc-telegram", "telegram", text="Bitcoin | Full analysis: " + PAGE,
           source={}, object_id="228", at="2026-11-22T19:58:03Z", intent={"plan_analysis_link": True},
           native={"reply_to_id": "226", "reply_to_url": "https://t.me/CapitalChronicle/226"})
    result = audit.finish({}, {"plan_btc": PAGE})
    links = {(row["piece_id"], row["platform"]): row["full_analysis_link"] for row in result["plan_analysis"]}
    assert links[("plan-status-post-btc", "telegram")] is True
    assert links[("plan-status-post-btc-update", "telegram")] is False


def chart_copy(audit, platform, symbol):
    from hashlib import sha256

    path = audit.runtime / "gold-chart.png"
    path.write_bytes(b"uploaded chart bytes")
    digest = sha256(path.read_bytes()).hexdigest()
    asset = {"asset_id": "chart", "sha256": digest, "modality": "tradingview_chart_snapshot", "path": str(path),
             "tradingview_snapshot": {"tv_symbol": symbol}}
    chart = {"public_object_id": "229", "observed_at_utc": "2026-11-23T02:48:19Z", "assets": [{
        "asset_id": "chart", "expected_sha256": digest, "observed_sha256": ["b" * 64], "status": "MISMATCH",
        "tradingview_symbol": symbol}]}
    return posted(audit, "plan-status-post-gold", platform, text="Gold: armed.\n" + NOTICES,
                  source={"kind": "setup", "key": "plan-status-post-gold", "symbol": "XAUUSD"}, object_id="229",
                  at="2026-11-23T02:48:16Z", native={"media_asset_ids": ["chart"]},
                  intent={"media_assets": [asset]}, readback_fields={"posted_chart_readback": chart})


@pytest.mark.parametrize(("platform", "symbol", "status", "cause", "replies"), [
    ("telegram", "FX_IDC:XAUUSD", "UNVERIFIED", "POSTED_CHART_RECOMPRESSED_UNVERIFIED", 0),
    ("threads", "FX_IDC:XAUUSD", "UNVERIFIED", "POSTED_CHART_RECOMPRESSED_UNVERIFIED", 0),
    ("telegram", "FX_IDC:EURUSD", "FAIL", "MARKET_TRADINGVIEW_SYMBOL_MISMATCH", 0),
    ("x", "FX_IDC:XAUUSD", "FAIL", "POSTED_CHART_MISMATCH", 1),
])
def test_a_reencoded_chart_is_unverified_not_a_mismatch(tmp_path, platform, symbol, status, cause, replies):
    # Telegram 229 (23 Nov 02:48Z): the public 800x450 JPEG is the uploaded 1600x900 gold chart; the
    # stored pixel rule (rms 7.8, worst tile 19.9) still recorded MISMATCH and prepared a correction reply.
    audit = checks(tmp_path)
    chart_copy(audit, platform, symbol)
    result = audit.finish({}, {})
    assert (platform, status, cause) in by_decision(result, "82")
    assert len(result["chart_correction_replies"]) == replies


def test_hand_posted_and_superseded_copies_are_expected_not_failed(tmp_path):
    audit = checks(tmp_path)
    copies = [
        {"plan_post": "plan-status-post-gold", "platform": "x", "status": "SETTLED", "confirmed": False,
         "behind_over_ten_minutes": False, "public_url": None, "first_cause": "JIM_POSTS_BY_HAND_20261123",
         "source_at_utc": "2026-11-23T02:47:00Z"},
        {"plan_post": "plan-status-post-gold", "platform": "threads", "status": "SUPERSEDED_NOT_POSTED",
         "confirmed": False, "behind_over_ten_minutes": False, "public_url": None,
         "first_cause": "PLAN_ALREADY_FILLED", "source_at_utc": "2026-11-23T02:47:00Z"},
        {"plan_post": "plan-status-post-gold", "platform": "facebook_page", "status": "UNKNOWN_WRITE",
         "confirmed": False, "behind_over_ten_minutes": False, "public_url": None,
         "first_cause": "PUBLISHING_OLDER_THAN_24_HOURS", "source_at_utc": "2026-11-23T02:47:00Z"},
    ]
    result = audit.finish({"copies": copies}, {})
    assert sorted(by_decision(result, "CC-672")) == [
        ("facebook_page", "FAIL", "PLAN_COPY_UNCONFIRMED"),
        ("threads", "EXPECTED", "PLAN_COPY_SUPERSEDED_BY_LATER_STATE"),
        ("x", "EXPECTED", "PLAN_COPY_HANDED_TO_JIM"),
    ]
    coverage = next(row for row in result["checks"] if row["decision"] == "CC-672")
    assert (coverage["failed"], coverage["expected"]) == (1, 2)


def test_hand_routes_excuse_wraps_only_after_jim_took_them(tmp_path):
    control = tmp_path / "control"
    control.mkdir()
    (control / "suspended_routes.json").write_text(json.dumps({
        "x": "JIM_POSTS_BY_HAND_20261123", "substack_notes": "JIM_POSTS_BY_HAND_20261123"}), encoding="utf-8")
    sunday = checks(tmp_path, "2026-11-22T12:15:00Z", "2026-11-23T12:15:00Z").finish({}, {})
    # The Sunday wrap was due at 18:00Z, before the 20:31Z hand-posting start: still a failure.
    assert ("x", "FAIL", "WRAP_PLATFORM_MISSING") in by_decision(sunday, "98")
    monday = checks(tmp_path, "2026-11-23T00:00:00Z", "2026-11-23T14:00:00Z").finish({}, {})
    assert ("x", "EXPECTED", "WRAP_PLATFORM_HANDED_TO_JIM") in by_decision(monday, "98")
    assert ("telegram", "FAIL", "WRAP_PLATFORM_MISSING") in by_decision(monday, "98")


def pause(runtime, restored=None):
    folder = runtime / "control" / "pause-20261123"
    folder.mkdir(parents=True)
    (folder / "manifest.json").write_text(json.dumps({
        "paused_at_utc": "2026-11-23T04:56:22.3575958Z", "resume_at_utc": "2026-11-25T16:00:00Z",
        "cause": "JIM_PAUSE_20261123T0450Z_UNTIL_20261125T1600Z"}), encoding="utf-8")
    if restored:
        (folder / "restored.json").write_text(json.dumps({"started_at_utc": restored}), encoding="utf-8")


def test_pause_record_ends_at_the_restore(tmp_path):
    pause(tmp_path)
    (start, end, cause), = pause_windows(tmp_path)
    assert (start.isoformat()[:19], end, cause) == (
        "2026-11-23T04:56:22", None, "JIM_PAUSE_20261123T0450Z_UNTIL_20261125T1600Z")


def test_a_paused_day_with_no_posts_reports_paused_not_failures(tmp_path):
    pause(tmp_path)
    copies = [{"plan_post": "plan-result-post-gold", "platform": platform, "status": "READY",
               "confirmed": False, "behind_over_ten_minutes": False, "public_url": None,
               "first_cause": "JIM_PAUSE_20261123T0450Z_UNTIL_20261125T1600Z",
               "source_at_utc": "2026-11-23T08:00:00Z"} for platform in ("telegram", "discord")]
    # An X write left unresolved on 22 Nov was reported that evening; nothing can resolve it while paused.
    stuck = {"plan_post": "plan-status-post-old", "platform": "x", "status": "UNKNOWN_WRITE", "confirmed": False,
             "behind_over_ten_minutes": False, "public_url": None,
             "first_cause": "NEO_RETURN_BINDING_OR_IDENTITY_MISMATCH", "source_at_utc": "2026-11-22T10:00:00Z"}
    result = checks(tmp_path, "2026-11-23T12:15:00Z", "2026-11-24T12:15:00Z").finish(
        {"copies": [*copies, stuck]}, {})
    assert result["failure_count"] == 0
    assert result["pause"] == {"state": "PAUSED", "cause": "JIM_PAUSE_20261123T0450Z_UNTIL_20261125T1600Z",
                               "paused_at_utc": "2026-11-23T04:56:22.357595+00:00", "restored_at_utc": None,
                               "public_copies_in_window": 0, "held_checks": 13}
    assert {row["status"] for row in result["issues"]} == {"PAUSED"}
    assert all(row["pause_cause"] == result["pause"]["cause"] for row in result["issues"])
    assert next(row for row in result["issues"]
                if row["decision"] == "CC-672" and row["platform"] == "x")["carried_over"] is True


def test_after_the_restore_missing_copies_fail_again(tmp_path):
    pause(tmp_path, restored="2026-11-30T01:00:00Z")
    stuck = {"plan_post": "plan-status-post-old", "platform": "x", "status": "UNKNOWN_WRITE", "confirmed": False,
             "behind_over_ten_minutes": False, "public_url": None,
             "first_cause": "NEO_RETURN_BINDING_OR_IDENTITY_MISMATCH", "source_at_utc": "2026-11-22T10:00:00Z"}
    result = checks(tmp_path, "2026-11-29T12:15:00Z", "2026-11-30T14:15:00Z").finish({"copies": [stuck]}, {})
    assert result["pause"]["state"] == "PAUSED"  # Nothing went out; the Monday wrap fell due after the restore.
    assert ("telegram", "FAIL", "WRAP_PLATFORM_MISSING") in by_decision(result, "98")
    assert ("x", "FAIL", "PLAN_COPY_UNCONFIRMED") in by_decision(result, "CC-672")  # owners run again
    assert checks(tmp_path, "2026-11-30T12:15:00Z", "2026-12-01T12:15:00Z").finish({}, {})["pause"] is None


def test_a_post_before_the_pause_makes_the_day_partly_paused(tmp_path):
    pause(tmp_path)
    audit = checks(tmp_path)
    posted(audit, "plan-status-post-gold", "telegram", text="Gold: armed.\n" + NOTICES,
           source={"kind": "setup", "key": "plan-status-post-gold"}, at="2026-11-23T02:48:16Z")
    summary = audit.finish({}, {})["pause"]
    assert (summary["state"], summary["public_copies_in_window"]) == ("PARTLY_PAUSED", 1)


@pytest.mark.parametrize(("frame", "text", "cause"), [
    ({"policy": "RESULT_FRAME_V1", "plan_dates": "17–18 Nov", "correction": True},
     "Correction to the 17–18 Nov USD/JPY result: closed at its time exit.", None),
    ({"policy": "RESULT_FRAME_V1", "plan_dates": "17–18 Nov", "correction": True},
     "USD/JPY, plan of 17–18 Nov: closed at its time exit.", "RESULT_FRAME_NOT_PRINTED"),
    (None, "USD/JPY: closed at its time exit.", "RESULT_FRAME_MISSING"),
])
def test_results_from_23_nov_name_their_dates_and_corrections(tmp_path, frame, text, cause):
    audit = checks(tmp_path)
    source = {"kind": "result", "key": "plan-result-post-usdjpy", "result_frame": frame,
              "decision_source_created_at_utc": "2026-11-23T05:00:00Z"}
    posted(audit, "plan-result-post-usdjpy", "telegram", text=text + "\n" + NOTICES, source=source,
           at="2026-11-23T05:01:00Z")
    result = audit.finish({}, {})
    assert [row[2] for row in by_decision(result, "CC-768")] == ([cause] if cause else [])


def test_a_result_queued_before_the_frame_keeps_its_text(tmp_path):
    # t.me/CapitalChronicle/230 was queued at 02:52Z, before RESULT_FRAME_EFFECTIVE (04:00Z).
    audit = checks(tmp_path)
    source = {"kind": "result", "key": "plan-result-post-usdjpy",
              "decision_source_created_at_utc": "2026-11-23T02:52:00Z"}
    posted(audit, "plan-result-post-usdjpy", "telegram", text="USD/JPY: closed.\n" + NOTICES, source=source,
           object_id="230", at="2026-11-23T02:53:15Z")
    assert by_decision(audit.finish({}, {}), "CC-768") == []


@pytest.mark.parametrize(("text", "cause"), [
    ("USD/JPY: a note on the post above. It is the final result of our earlier plan, registered on 17 Nov.", None),
    ("USD/JPY: the result above is final.", "CORRECTION_DATES_OR_LABEL_MISSING"),
])
def test_correction_replies_are_checked_for_their_dates(tmp_path, text, cause):
    audit = checks(tmp_path)
    posted(audit, "correction-reply-usdjpy-230-20261123", "telegram", text=text + "\n" + NOTICES,
           source={"kind": "correction", "key": "correction-reply-usdjpy-230-20261123"},
           object_id="232", at="2026-11-23T04:23:34Z")
    result = audit.finish({}, {})
    assert [row[2] for row in by_decision(result, "CC-768")] == ([cause] if cause else [])
    assert by_decision(result, "CC-729") == []
    assert by_decision(result, "158") == []  # A correction note is not reviewed as a plan call.


def test_evening_file_says_paused_with_its_cause(recorded, tmp_path):  # noqa: F811
    _, store, _, run = recorded
    pause(store.parent)
    report, _ = build(recorded, since="2026-11-23T12:15:00Z", until="2026-11-24T12:15:00Z")
    decisions = report["decision_checks"]
    assert decisions["pause"]["state"] == "PAUSED"
    assert decisions["failure_count"] == 0
    readback.write_report(tmp_path, report)
    evening = (tmp_path / "day_readback.md").read_text(encoding="utf-8")
    assert "Paused: posting paused since 23 Nov 2026 11:56 GMT+7 (JIM_PAUSE_20261123T0450Z_UNTIL_20261125T1600Z)" in evening
    assert json.loads((tmp_path / "decision_checks.json").read_bytes())["pause"]["state"] == "PAUSED"


def test_correction_rows_are_read_as_the_decision_source(recorded):  # noqa: F811
    from live_contentops import plan_status_posts_v1 as posts

    _, store, _, _ = recorded
    key = "correction-reply-usdjpy-230-20261123"
    with sqlite3.connect(store) as conn:
        conn.execute("INSERT INTO outbox_messages VALUES(?,?,?,?,?,?)", (
            key, key, posts.DESTINATION, json.dumps({"key": key, "kind": "correction"}), "PREPARED",
            "2026-11-23T04:20:00Z"))
        conn.row_factory = sqlite3.Row
        assert readback._decision_source(conn, key, "2026-11-23T12:00:00Z")["kind"] == "correction"
