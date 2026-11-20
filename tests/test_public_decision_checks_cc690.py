import json

from live_contentops.day_readback_v1 import check_public_text, write_decision_checks
from live_contentops.public_decision_checks_v1 import DecisionChecks, WRAP_ROUTES


def checks(tmp_path, start="2026-11-19T12:15:00Z", end="2026-11-20T12:15:00Z"):
    return DecisionChecks({"since_utc": start, "until_utc": end}, tmp_path)


def published(audit, piece, platform, *, title="", text="", source=None, native=None, intent=None,
              published_at="2026-11-19T12:30:00Z", media_visible=True, mutations=()):
    history = [("2026-11-19T13:30:00Z", {"readback": {
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
    }]}, {"plan_gold": page})
    problems = {(r["decision"], r["platform"], r["first_cause"]) for r in output["issues"]}
    assert {
        ("82", "discord", "MARKET_TRADINGVIEW_SYMBOL_MISMATCH"),
        ("113", "discord", "PLAN_LAYER_QUOTES_BELOW_THREE"),
        ("113", "discord", "FULL_ANALYSIS_LINK_MISSING"),
        ("CC-685", "discord", "DISCORD_FILL_OR_RESULT_THREAD_ONLY"),
        ("CC-684", "linkedin", "LINKEDIN_SUBSTACK_LINK_MISSING"),
        ("CC-684", "linkedin", "LINKEDIN_IMAGE_MISSING"),
        ("CC-684", "linkedin_company", "LINKEDIN_ACCOUNT_COPY_MISSING"),
    } <= problems
    coverage = next(r for r in output["issues"] if r["decision"] == "CC-672")
    assert coverage["delivery_cause"] == "CARD_PARENT_NOT_CONFIRMED"


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
    assert not any(e["decision"] == "113" for e in audit.finish({}, {"plan_gold": page})["issues"])

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
