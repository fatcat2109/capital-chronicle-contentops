import json

import pytest

from live_contentops.agy_decision_metrics_v1 import daily_metrics
from live_contentops.day_readback_v1 import check_public_text, report_window, write_decision_checks, write_report
from live_contentops.public_decision_checks_v1 import DecisionChecks, WRAP_ROUTES


def checks(tmp_path, start="2026-11-19T12:15:00Z", end="2026-11-20T12:15:00Z"):
    return DecisionChecks({"since_utc": start, "until_utc": end}, tmp_path)


def published(audit, piece, platform, *, title="", text="", source=None, native=None, intent=None,
              published_at="2026-11-19T12:30:00Z", read_at="2026-11-19T13:30:00Z", media_visible=True, mutations=()):
    history = [(read_at, {"readback": {
        "verified": True, "write_exists": True, "meaningful_media_visible": media_visible,
        "observed_published_at_utc": published_at, "observed_public_object_id": "object-1",
    }})]
    url = "https://capitalchronicle.substack.com/p/" + piece
    return audit.add(piece, platform, url, title, text, {"native_payload": native or {}, **(intent or {})},
                     {"status": "DISPATCH_CONFIRMED", "public_object_id": "object-1", "dispatched_at": published_at},
                     [*history, *mutations], source or {})


def test_trading_wrap_due_before_next_notice_and_all_routes_are_required(tmp_path):
    audit = checks(tmp_path)
    for route in WRAP_ROUTES:
        if route != "linkedin_company":
            published(audit, "the-wrap", route, title="Daily market wrap")
    result = audit.finish({}, {})
    assert [(e["decision"], e["piece_id"], e["platform"], e["first_cause"])
            for e in result["issues"] if e["decision"] == "98"] == [
        ("98", "the-wrap", "linkedin_company", "WRAP_PLATFORM_MISSING")]
    no_due = checks(tmp_path, start="2026-11-26T00:00:00Z", end="2026-11-27T12:15:00Z")
    assert not no_due.finish({}, {})["issues"]  # Thanksgiving and before Friday's deadline
    sunday = checks(tmp_path, start="2026-11-22T12:15:00Z", end="2026-11-23T12:15:00Z")
    assert {e["piece_id"] for e in sunday.finish({}, {})["issues"]} == {"weekend-wrap-2026-11-22"}


def test_plan_quotes_exact_link_chart_discord_and_linkedin_are_checked_per_copy(tmp_path):
    audit = checks(tmp_path)
    source = {"kind": "result", "plan_id": "plan_gold", "symbol": "XAUUSD", "source_plan": {
        "macro": "Rates fell after the policy surprise.",
        "fundamental": "The cost of holding gold fell.",
        "options": "Dealer positioning dampened the early move.",
    }}
    page = "https://capitalchronicle.substack.com/p/gold-analysis"
    wrong = "https://capitalchronicle.substack.com/p/other-plan"
    published(audit, "gold-result", "discord", text=f"Macro: This is new text. {wrong}", source=source,
              native={"discord_thread_parent_id": "parent", "media_asset_ids": ["chart"]},
              intent={"media_assets": [{"asset_id": "chart", "tradingview_snapshot": {"tv_symbol": "FX_IDC:EURUSD"}}]})
    published(audit, "gold-result", "linkedin", text="Gold hit its target.", source=source, media_visible=False)
    output = audit.finish({"copies": [{
        "plan_post": "gold-result", "platform": "x", "status": "WAITING",
        "confirmed": False, "behind_over_ten_minutes": True, "public_url": None,
        "first_cause": "CARD_PARENT_NOT_CONFIRMED",
        "retry_failure_cause": "NEO_RETURN_BINDING_OR_IDENTITY_MISMATCH", "unresolved_write_age_seconds": 3700,
    }]}, {"plan_gold": page})
    problems = {(r["decision"], r["platform"], r["first_cause"]) for r in output["issues"]}
    assert {
        ("82", "discord", "MARKET_TRADINGVIEW_SYMBOL_MISMATCH"),
        ("113", "discord", "PLAN_ANALYSIS_LAYERS_MISSING"),
        ("113", "discord", "FULL_ANALYSIS_LINK_MISSING"),
        ("CC-685", "discord", "DISCORD_FILL_OR_RESULT_THREAD_ONLY"),
        ("CC-684", "linkedin", "LINKEDIN_SUBSTACK_LINK_MISSING"),
        ("CC-684", "linkedin", "LINKEDIN_IMAGE_MISSING"),
        ("CC-684", "linkedin_company", "LINKEDIN_ACCOUNT_COPY_MISSING"),
    } <= problems
    coverage = next(r for r in output["issues"] if r["decision"] == "CC-672")
    assert coverage["delivery_cause"] == "CARD_PARENT_NOT_CONFIRMED"
    assert coverage["retry_failure_cause"] == "NEO_RETURN_BINDING_OR_IDENTITY_MISMATCH"
    assert coverage["unresolved_write_age_seconds"] == 3700


def test_plan_target_and_voice_use_each_platform_and_the_bound_continuation(tmp_path):
    audit = checks(tmp_path)
    piece = "plan-status-post-gold"
    source = {"kind": "setup", "key": piece, "symbol": "XAUUSD", "target_policy": "DECISION_40_NO_TARGET"}
    base = "Base case (55%): Gold steadies.\nMacro: Yields eased.\nFundamentals: ETF demand held."
    levels = "Entry zone: 3,954–3,964. Plan wrong below 3,904."
    good = f"{base}\nBull case: Gold rallies if yields fall further.\n{levels}"
    published(audit, piece, "telegram", text=good, source=source)
    x_copy = published(audit, piece, "x", text=good, source=source)
    x_copy.public_text = base
    continuation = published(audit, piece + "-part-1", "x", source=source,
                             text="Model target level: 4,000.", intent={"plan_status_part": 1})
    continuation.row["public_object_id"] = "x-reply"
    published(audit, piece, "discord", source=source, text=good)
    audit.copies[-1].public_text = ""
    pending = published(audit, piece, "threads", text="Target level: 4,000.", source=source)
    pending.row["status"] = "UNKNOWN_WRITE"
    pending.verified_at = None

    report = audit.finish({}, {})
    issues = [issue for issue in report["issues"] if issue["decision"] in {"157", "158"}]
    assert [(r["piece_id"], r["platform"], r["status"], r["first_cause"])
            for r in issues if r["decision"] == "157"] == [
                (piece, "discord", "UNVERIFIED", "PLAN_COPY_TEXT_UNAVAILABLE"),
                (piece + "-part-1", "x", "FAIL", "PUBLIC_PLAN_TARGET_PRESENT"),
            ]
    assert {r["first_cause"] for r in issues if r["platform"] == "x" and r["status"] == "FLAGGED"} == {
        "SCENARIO_CASES_MISSING", "ENTRY_ZONE_MISSING", "INVALIDATION_LEVEL_MISSING",
    }
    assert not any(r["platform"] in {"telegram", "threads"} for r in issues)
    assert report["scenario_voice"]["posts_reviewed"] == 2
    by_rule = {row["rule"]: row for row in report["scenario_voice"]["rules"]}
    assert by_rule["SCENARIO_CASES_MISSING"]["share_pct"] == 50
    assert by_rule["SCENARIO_FORCES_TOO_FEW"]["share_pct"] == 0
    failed = {row["decision"]: row["failed"] for row in report["checks"]}
    assert (failed["157"], failed["158"]) == (1, 0)


def test_empty_evening_has_no_voice_percentage(tmp_path):
    review = checks(tmp_path).finish({}, {})["scenario_voice"]
    assert review["posts_reviewed"] == 0
    assert all(r["share_pct"] is None and r["flagged"] == 0 for r in review["rules"])


def test_actual_post_body_overrides_intent_and_is_not_serialized(tmp_path):
    audit = checks(tmp_path)
    source = {"kind": "setup", "symbol": "XAUUSD", "plan_id": "plan_gold", "source_plan": {
        "macro": "Rates fell after the policy surprise.", "fundamental": "The cost of holding gold fell.",
        "options": "Dealer positioning dampened the early move.",
    }}
    page = "https://capitalchronicle.substack.com/p/gold-analysis"
    text = ("Macro: Rates fell after the policy surprise.\n"
            "Fundamentals: The cost of holding gold fell.\n"
            "Options and gamma: Dealer positioning dampened the early move.\nFull analysis: " + page)
    copy = published(audit, "gold-setup", "telegram", text=text, source=source,
                     intent={"media_assets": [{"asset_id": "chart", "tradingview_snapshot": {"tv_symbol": "FX_IDC:XAUUSD"}}]})
    layers = audit.finish({}, {"plan_gold": page})["plan_analysis"][0]["layers"]
    assert {name for name, item in layers.items() if item["state"] == "PRINTED"} == {
        "macro", "fundamental", "options_gamma"}

    audit = checks(tmp_path)
    copy = published(audit, "gold-setup", "telegram", text=text, source=source)
    check_public_text("telegram", """<div class="tgme_widget_message_text">Parent text</div>
        <div class="tgme_widget_message_text">Gold is still waiting. Written by AI at 18:12 UTC.</div>""",
        expected_text=text, decision_copy=copy)
    result = audit.finish({}, {"plan_gold": page})
    issue_codes = {e["first_cause"] for e in result["issues"]}
    assert {"FULL_ANALYSIS_LINK_MISSING", "PUBLIC_AI_LABEL_OR_MODEL_NAME",
            "PUBLIC_TIMEZONE_ET_REQUIRED"} <= issue_codes
    artifact = write_decision_checks(tmp_path, result)
    assert "Parent text" not in artifact.read_text(encoding="utf-8")
    assert json.loads(artifact.read_bytes()) == result


@pytest.mark.parametrize("case,expected_gaps", [
    ("complete", {}),
    ("unavailable", {}),
    ("omitted", {"technical": "EXPORTED_LAYER_NOT_PRINTED"}),
    ("incorrect", {"scenarios": "EXPORTED_LAYER_NOT_PRINTED"}),
    ("uncited", {"cross_asset_contagion": "EXPORT_GAP_WITHOUT_CAUSE"}),
])
def test_plan_layers_match_the_frozen_export_per_platform(tmp_path, case, expected_gaps):
    audit = checks(tmp_path)
    page = "https://capitalchronicle.substack.com/p/gold-analysis"
    lines = {
        "macro": "Yields eased as the dollar weakened.",
        "event_and_cause": "Prices rose after the official release.",
        "fundamentals": "Physical demand remained firm through Monday.",
        "priced_in": "Futures already reflected one rate cut.",
        "positioning_and_sentiment": "Speculators maintained their net long exposure.",
        "options_and_gamma": "Dealer hedging slowed the intraday move.",
        "cross_asset_and_contagion": "Treasuries led the recovery in gold.",
        "technical": "Gold held above its previous weekly low.",
    }
    exported = [{"layer": name, "state": "USED", "text": value} for name, value in lines.items()]
    if case in {"unavailable", "uncited"}:
        exported[-2] = {"layer": "cross_asset_and_contagion", "state": "UNAVAILABLE",
                        "first_cause": "NOT_WRITTEN" if case == "unavailable" else None}
        lines.pop("cross_asset_and_contagion")
    if case == "omitted":
        lines.pop("technical")
    text = "\n".join(f"{label.replace('_', ' ')}: {value}" for label, value in lines.items())
    text += f"\nMain scenario (55%). Alternative scenario ({41 if case == 'incorrect' else 40}%).\n{page}"
    source = {"kind": "update", "plan_id": "plan_gold", "symbol": "XAUUSD", "source_plan": {
        "layers": exported, "scenario_analysis": {"base_case": {"probability_pct": 55},
                                                 "main_alternative": {"probability_pct": 40}}}}
    chart = {"asset_id": "chart", "tradingview_snapshot": {"tv_symbol": "FX_IDC:XAUUSD"}}
    published(audit, "gold", "telegram", text=text, source=source,
              native={"media_asset_ids": ["chart"]}, intent={"media_assets": [chart]})
    published(audit, "gold", "linkedin", text="Gold is holding.", source=source,
              native={"media_asset_ids": ["chart"]}, intent={"media_assets": [chart]}, media_visible=None)
    result = audit.finish({}, {"plan_gold": page})
    copies = {row["platform"]: row for row in result["plan_analysis"]}
    layers = copies["telegram"]["layers"]
    assert len(layers) == 9
    assert copies["telegram"]["full_analysis_link"] and not copies["linkedin"]["full_analysis_link"]
    assert {key: layer["cause"] for key, layer in layers.items() if layer["state"] == "MISSING"} == expected_gaps
    assert copies["linkedin"]["layers"]["macro"]["state"] == "MISSING"
    if case == "unavailable":
        assert layers["cross_asset_contagion"] == {"state": "UNAVAILABLE", "cause": "NOT_WRITTEN"}
    assert {(row["platform"], row["first_cause"]) for row in result["issues"] if row["decision"] == "82"} == {
        ("linkedin", "MARKET_TRADINGVIEW_CHART_UNVERIFIED")}


@pytest.mark.parametrize("first_has_link", [True, False])
def test_analysis_link_uses_only_the_first_confirmed_platform_reply(tmp_path, first_has_link):
    audit = checks(tmp_path)
    page = "https://capitalchronicle.substack.com/p/gold-analysis"
    root = published(audit, "gold", "telegram", source={"kind": "setup", "plan_id": "plan_gold"},
                     text="Gold is holding.", native={"full_text": "Gold is holding. " + page,
                                                      "text": "Gold is holding."})
    published(audit, "first", "telegram", text=page if first_has_link else "Earlier reply.",
              native={"reply_to_id": "object-1", "reply_to_url": root.url},
              published_at="2026-11-19T12:31:00Z")
    published(audit, "second", "telegram", text=page,
              native={"reply_to_id": "object-1", "reply_to_url": root.url},
              published_at="2026-11-19T12:32:00Z")
    assert audit.finish({}, {"plan_gold": page})["plan_analysis"][0]["full_analysis_link"] is first_has_link


def test_x_observed_thread_checks_all_layers_but_link_only_in_first_reply(tmp_path):
    audit = checks(tmp_path)
    page = "https://capitalchronicle.substack.com/p/gold-analysis"
    source = {"kind": "setup", "plan_id": "plan_gold", "source_plan": {
        "macro": "Yields eased as the dollar weakened."}}
    copy = published(audit, "gold", "x", source=source, text="Gold is holding.", mutations=[
        ("2026-11-19T14:02:00Z", {"readback": {
            "verified": True, "content_binding_checks": {"thread_match": True},
            "observed_text": "Gold is holding. " + page,
            "observed_thread": [
                {"role": "root", "public_object_url": "https://x.com/Capitalnicle/status/98",
                 "observed_text": "Gold is holding."},
                {"public_object_url": "https://x.com/Capitalnicle/status/99", "observed_text": "First reply."},
                {"public_object_url": "https://x.com/Capitalnicle/status/100",
                 "observed_text": "Macro: Yields eased as the dollar weakened. " + page},
            ],
        }}),
    ])
    copy.url = "https://x.com/Capitalnicle/status/98"
    result = audit.finish({}, {"plan_gold": page})
    assert not result["plan_analysis"][0]["full_analysis_link"]
    assert result["plan_analysis"][0]["layers"]["macro"] == {"state": "PRINTED"}


def test_verified_text_mismatch_cannot_pass_on_the_intended_link(tmp_path):
    audit = checks(tmp_path)
    page = "https://capitalchronicle.substack.com/p/gold-analysis"
    published(audit, "gold", "telegram", source={"kind": "update", "plan_id": "plan_gold"}, text=page,
              mutations=[("2026-11-19T14:02:00Z", {"readback": {
                  "verified": True, "content_binding_checks": {"text_match": False},
              }})])
    assert not audit.finish({}, {"plan_gold": page})["plan_analysis"][0]["full_analysis_link"]


def test_plan_dispatch_with_a_confirmed_object_id_and_no_safe_permalink_is_audited(tmp_path):
    audit = checks(tmp_path)
    copy = published(audit, "gold", "instagram_business", source={"kind": "update"}, text="Gold is holding.")
    copy.url = None
    output = audit.finish({}, {})
    assert output["plan_analysis"][0]["platform"] == "instagram_business"
    assert output["plan_analysis"][0]["public_url"] is None
    assert any(row["first_cause"] == "PLAN_ANALYSIS_LAYERS_MISSING" for row in output["issues"])


def test_late_page_and_edit_require_dated_object_evidence(tmp_path):
    audit = checks(tmp_path)
    source = {"page_id": "late-gold", "source_plan": {"entry_deadline_utc": "2026-11-19T12:20:00Z"}}
    mutations = [
        ("2026-11-19T14:30:00Z", {"action": "EDIT_EXISTING", "readback": {"verified": True}}),
        ("2026-11-20T13:00:00Z", {"action": "DELETE_EXISTING", "result": {"status": "DELETE_CONFIRMED"}}),
        ("2026-11-19T14:30:00Z", {"action": "DELETE_EXISTING", "result": {"status": "UNKNOWN_WRITE"}}),
    ]
    published(audit, "late-gold", "substack", text="Status: waiting for entry.", source=source, mutations=mutations)
    result = audit.finish({}, {})
    assert {e["first_cause"] for e in result["issues"] if e["decision"] in {"136", "CC-584"}} == {
        "LATE_PLAN_PAGE_FINAL_STATUS_OR_LINE_MISSING", "PUBLISHED_OBJECT_EDIT_CONFIRMED"}

    audit = checks(tmp_path)
    source["final_status"] = {"status": "EXPIRED", "status_at_utc": "2026-11-19T12:20:00Z"}
    published(audit, "late-gold", "substack", source=source,
              text="This page was published after the plan ended. Status: expired.")
    assert not any(e["decision"] == "CC-584" for e in audit.finish({}, {})["issues"])


def test_antigravity_code_outcomes_and_fallbacks_come_from_dated_receipts(tmp_path):
    def receipt(folder, name, value):
        path = tmp_path / "daily_app_outputs" / folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    top = "x_reply_pack/bot/20261119T130000-1234"
    rank = top + "/editorial/rank"
    receipt(top, "reply-pack-request-1.json", {})
    receipt(rank + "/light", "light-call.json", {
        "started_at_utc": "2026-11-19T13:00:00Z", "ended_at_utc": "2026-11-19T13:01:00Z",
        "answered_by": "antigravity", "attempts": [{"caller": "antigravity", "status": "RETURNED"}],
    })
    receipt(rank, "call.json", {"status": "RETURNED", "ended_at_utc": "2026-11-19T13:01:00Z"})
    receipt(rank, "response.json", {"ranking": [{"post_id": "12345", "quality_score": 81}]})
    receipt("plan-status-posts/gold/layer-lines-123", "light-call.json", {
        "job": "plan_layer_lines", "started_at_utc": "2026-11-19T15:00:00Z",
        "ended_at_utc": "2026-11-19T15:05:00Z", "fallback": "frozen_plan", "result": "FALLBACK",
        "attempts": [{"caller": "antigravity", "status": "TIMEOUT", "cause": "AGY_TIMEOUT"}],
    })
    receipt("plan-status-posts/gold/layer-lines-456", "light-call.json", {
        "job": "plan_layer_lines", "started_at_utc": "2026-11-20T12:14:00Z",
        "ended_at_utc": "2026-11-20T12:16:00Z", "result": "PASS", "answered_by": "antigravity",
        "attempts": [{"caller": "antigravity", "status": "RETURNED"}],
    })
    result = daily_metrics(tmp_path, checks(tmp_path).window, {"plan_layer_lines": 3})
    by_job = {row["job"]: row for row in result["jobs"]}
    reply = by_job["x_reply_ranking"]
    assert (reply["posts_due"], reply["calls"], reply["code_pass_rate_pct"]) == (1, 1, 100.0)
    layer = by_job["plan_layer_lines"]
    assert (layer["posts_due"], layer["calls"], layer["timeouts"], layer["code_fallbacks"]) == (3, 2, 1, 1)
    assert layer["calls_incomplete_at_cutoff"] == 1
    assert layer["code_pass_rate_meets_90_pct"] is False
    assert layer["hours_idle_without_rate_limit"] is None


def test_x_own_reply_uses_exact_verified_thread_and_resolved_link(tmp_path):
    audit = checks(tmp_path)
    page = "https://capitalchronicle.substack.com/p/gold-analysis"
    copy = published(audit, "gold-setup", "x", text="Gold is holding.", mutations=[
        ("2026-11-19T14:02:00Z", {"readback": {
            "verified": True, "identity_match": True, "observed_public_object_id": "object-1",
            "content_binding_checks": {"thread_match": True},
            "observed_thread": [{"public_object_url": "https://x.com/Capitalnicle/status/99"}],
            "observed_link_resolutions": [{"public_object_url": "https://x.com/Capitalnicle/status/99",
                                           "target_verified": True, "target_url": page}],
        }}),
    ])
    assert copy.has_link(page)
    assert not copy.has_link(page + "-different")


def test_discord_thread_with_a_confirmed_channel_reply_passes(tmp_path):
    audit = checks(tmp_path)
    source = {"kind": "result", "key": "gold-result"}
    published(audit, "gold-result", "discord", source=source, native={"discord_thread_parent_id": "parent"})
    published(audit, "gold-result-part-1", "discord", source=source, native={"discord_channel_reply": True})
    assert not any(issue["decision"] == "CC-685" for issue in audit.finish({}, {})["issues"])


def test_triggered_fills_require_a_confirmed_discord_channel_post(tmp_path):
    audit = checks(tmp_path)
    source = {"kind": "update", "state": "TRIGGERED"}
    published(audit, "thread-only", "discord", source=source,
              native={"discord_thread_parent_id": "parent"})
    published(audit, "missing", "telegram", source=source)
    published(audit, "in-channel", "discord", source=source, native={"discord_channel_reply": True})
    assert {(issue["piece_id"], issue["first_cause"]) for issue in audit.finish({}, {})["issues"]
            if issue["decision"] == "CC-685"} == {
        ("thread-only", "DISCORD_FILL_OR_RESULT_THREAD_ONLY"),
        ("missing", "DISCORD_FILL_OR_RESULT_CHANNEL_COPY_MISSING"),
    }


def test_shared_report_writer_emits_sidecar_for_digest_without_issue(tmp_path):
    run = tmp_path / "20261120T121500Z"
    run.mkdir()
    observed = {"digest_id": "no-articles", "recorded_at_utc": "2026-11-20T12:16:00Z"}
    window, result = report_window(run, since="2026-11-19T12:15:00Z", run_result=observed)
    assert result == observed
    audit = DecisionChecks(window, tmp_path)
    decisions = audit.finish({}, {})
    report = {"window": window, "observed_at_utc": window["until_utc"], "pieces": [],
              "digest": {"state": "NO_CONFIRMED_ARTICLES", "recipients": None, "opens": None, "public_url": None},
              "reply_bot": {"delivered_count": 0, "counts_by_kind_and_status": []},
              "engagement": {"cutoff_utc": window["until_utc"]}, "exception_count": 0, "exceptions": [],
              "decision_checks": decisions}
    paths = write_report(run, report)
    assert len(paths) == 2
    assert "## Decision checks" in paths[1].read_text(encoding="utf-8")
    assert json.loads((run / "decision_checks.json").read_bytes()) == decisions


def test_decision_83_checks_public_links_and_exact_x_thread(tmp_path):
    audit = checks(tmp_path)
    root = published(audit, "gold-setup", "telegram", text="Gold is holding.")
    check_public_text("telegram", """
        <div class="tgme_widget_message_text">Gold is holding.
        <a href="https://capital-chronicle-preview.pages.dev">Read more</a></div>
        """, decision_copy=root)
    published(audit, "gold-setup", "x", mutations=[
        ("2026-11-19T14:02:00Z", {"readback": {
            "verified": True, "identity_match": True, "observed_public_object_id": "object-1",
            "content_binding_checks": {"thread_match": True},
            "observed_thread": [{"public_object_url": "https://x.com/Capitalnicle/status/99"}],
            "observed_link_resolutions": [{"public_object_url": "https://x.com/Capitalnicle/status/99",
                                           "target_verified": True, "target_url": "https://site.github.io"}],
        }}),
    ])
    published(audit, "other-setup", "discord", text="Capital Chronicle offers analysis.")
    results = audit.finish({}, {})
    broken = [issue for issue in results["issues"] if issue["decision"] == "83"]
    assert {(r["platform"], r["first_cause"]) for r in broken} == {
        ("telegram", "PREVIEW_HOST_LINK_FORBIDDEN"), ("x", "PREVIEW_HOST_LINK_FORBIDDEN")}
    assert "pages.dev" not in json.dumps(results) and "github.io" not in json.dumps(results)


def test_interim_first_post_uses_available_analysis_and_flags_internal_copy(tmp_path):
    audit = checks(tmp_path, end="2026-11-20T14:00:00Z")
    source = {"kind": "setup", "decision_source_created_at_utc": "2026-11-20T12:05:00Z",
              "source_plan": {"scenario_analysis": {"mechanism": "Gold gained as near-term yields fell."}}}
    clocks = {"published_at": "2026-11-20T12:30:00Z", "read_at": "2026-11-20T13:30:00Z"}
    published(audit, "gold-setup", "telegram", source=source, text="The setup is MIXED.", **clocks)
    published(audit, "gold-setup", "x", source=source, text="Macro: Gold gained as near-term yields fell.", **clocks)
    published(audit, "other-setup", "telegram", source={
        **source, "source_plan": {"layers": [{"state": "UNAVAILABLE", "text": None}]}}, text="Gold is holding.", **clocks)
    issues = audit.finish({}, {})["issues"]
    interim = {r["piece_id"] + "/" + r["platform"] + "/" + r["first_cause"]
               for r in issues if r["first_cause"].startswith("FIRST_PLAN_POST_")}
    assert interim == {"gold-setup/telegram/FIRST_PLAN_POST_ANALYSIS_LINE_MISSING",
                       "gold-setup/telegram/FIRST_PLAN_POST_INTERNAL_TOKEN"}


def test_coverage_names_a_stall_even_when_routes_all_confirm_together(tmp_path):
    audit = checks(tmp_path)
    rows = [{"plan_post": "gold-setup", "platform": platform, "status": "DISPATCH_CONFIRMED",
             "confirmed": True, "behind_over_ten_minutes": False, "public_url": None,
             "source_at_utc": "2026-11-19T13:00:00Z", "confirmed_dispatch_at_utc": "2026-11-19T21:00:00Z"}
            for platform in ("x", "telegram")]
    issues = [r for r in audit.finish({"copies": rows}, {})["issues"] if r["decision"] == "CC-672"]
    assert [(r["platform"], r["first_cause"], r["seconds_after_source"]) for r in issues] == [
        ("telegram", "PLAN_COPY_OVER_TEN_MINUTES_LATE", 28800),
        ("x", "PLAN_COPY_OVER_TEN_MINUTES_LATE", 28800)]


def test_codex_calls_count_split_by_caller_and_a_blocked_agy_attempt_is_not_a_call(tmp_path):
    # CC-690 after CC-801 (decision 168): Codex runs the light jobs; a terms-blocked agy attempt started nothing.
    def receipt(folder, value):
        path = tmp_path / "daily_app_outputs" / folder / "light-call.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    codex = {"caller": "codex", "status": "RETURNED"}
    receipt("plan-status-posts/gold/layer-lines-801", {
        "job": "plan_layer_lines", "started_at_utc": "2026-11-19T16:00:00Z", "ended_at_utc": "2026-11-19T16:01:00Z",
        "result": "PASS", "answered_by": "codex", "attempts": [codex]})
    receipt("plan-status-posts/oil/layer-lines-802", {
        "job": "plan_layer_lines", "started_at_utc": "2026-11-19T16:02:00Z", "ended_at_utc": "2026-11-19T16:03:00Z",
        "result": "PASS", "answered_by": "codex",
        "attempts": [{"caller": "antigravity", "status": "NOT_STARTED",
                      "cause": "AGY_BLOCKED_TERMS_OF_SERVICE_20261124"}, codex]})
    receipt("plan-status-posts/btc/layer-lines-803", {
        "job": "plan_layer_lines", "started_at_utc": "2026-11-19T16:04:00Z", "ended_at_utc": "2026-11-19T16:05:00Z",
        "result": "FAIL", "answered_by": "codex", "attempts": [codex]})
    receipt("plan-status-posts/eur/layer-lines-804", {
        "job": "plan_layer_lines", "started_at_utc": "2026-11-19T16:06:00Z", "ended_at_utc": "2026-11-19T16:07:00Z",
        "fallback": "frozen_plan", "result": "FALLBACK",
        "attempts": [{"caller": "antigravity", "status": "NOT_STARTED",
                      "cause": "AGY_BLOCKED_TERMS_OF_SERVICE_20261124"}]})
    result = daily_metrics(tmp_path, checks(tmp_path).window, {"plan_layer_lines": 4})
    assert result["callers_counted"] == ["codex", "antigravity"]
    layer = {row["job"]: row for row in result["jobs"]}["plan_layer_lines"]
    assert (layer["calls"], layer["code_passes"], layer["code_rejects"]) == (3, 2, 1)
    assert layer["calls_by_caller"] == {"codex": 3, "antigravity": 0}
    assert (layer["antigravity_refused_by_block"], layer["codex_takeovers"], layer["code_fallbacks"]) == (2, 1, 1)
    assert layer["code_pass_rate_pct"] == 66.67 and layer["code_pass_rate_meets_90_pct"] is False
    assert layer["hours_without_recorded_call"] == pytest.approx(24 - 3 / 60, abs=0.001)


def test_a_failed_codex_daily_note_is_a_code_fallback_not_a_codex_takeover(tmp_path):
    folder = tmp_path / "daily_app_outputs" / "substack-daily-notes" / "run-1" / "daily-note-first-draft" / "a"
    folder.mkdir(parents=True)
    (folder / "result.json").write_text(json.dumps({
        "schema_version": "contentops.daily_note_first_draft.v1", "status": "AGY_UNAVAILABLE", "caller": "codex",
        "provider_call_attempted": True, "cause": "CODEX_LIGHT_TIMEOUT_180S",
        "started_at_utc": "2026-11-19T17:00:00Z", "ended_at_utc": "2026-11-19T17:03:00Z"}), encoding="utf-8")
    result = daily_metrics(tmp_path, checks(tmp_path).window, {"daily_wrap_sections": 1})
    wrap = {row["job"]: row for row in result["jobs"]}["daily_wrap_sections"]
    assert (wrap["calls"], wrap["timeouts"], wrap["code_fallbacks"], wrap["codex_takeovers"]) == (1, 1, 1, 0)
    assert wrap["calls_by_caller"] == {"codex": 1, "antigravity": 0}
