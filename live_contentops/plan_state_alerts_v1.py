"""CC-543: deterministic state alerts in the existing plan publication path.

Analysis retains its own page and reply. Neither is an input to these alerts.
"""
from __future__ import annotations

from decimal import Decimal

from . import plan_status_posts_v1 as posts
from .event_article_guard_v1 import check_publication_copy, conditional_call_text

CONTRACT = "CC543_V1"
IMMEDIATE_DESTINATIONS = ("telegram", "discord")


def compose(row):
    from . import plan_call_cards_v1 as cards
    from .plan_reader_copy_v1 import result_r
    plan = row["levels"]
    title = row["instrument_title"]
    at = cards._clock(row["at_utc"])
    calls = []
    if row["kind"] == "setup":
        lead = title + ": new plan."
        horizon = row.get("time_exit_utc") or plan["valid_until_utc"]
        side = "below" if Decimal(str(plan["invalidation_level"])) < Decimal(str(plan["zone_low"])) else "above"
        call = {"condition": posts._entry_condition(plan), "direction": plan["direction"],
                "market": title, "horizon": "the period to " + cards._clock(horizon),
                "invalidation": "price moves " + side + " " + cards.level(plan["invalidation_level"], plan)}
        calls = [call]
        lines = [lead, conditional_call_text(call)]
        if row.get("state") in {"FILLED", "TRIGGERED"}:
            lines.append("An entry filled; the position is open.")
        opens = (row.get("source_plan") or {}).get("not_before_utc")
        if opens and posts._utc(opens) > posts._utc(row["registered_at_utc"]):
            lines.append("Entry opens: " + cards._clock(opens) + ".")
    else:
        state = row["state"]
        words = {"FILLED": "an entry filled; the position is open",
                 "TRIGGERED": "an entry filled; the position is open",
                 "CANCELLED": "the plan was withdrawn", "VIEW_CHANGED": "the view changed",
                 "INVALIDATED": "the invalidation condition was reached",
                 "CLOSED": "the position closed", "EXPIRED": "the entry window ended"}
        if row["kind"] == "result":
            words_for_state = cards.ending_words(row)
        else:
            words_for_state = words[state]
        lead = title + ": " + words_for_state + "."
        lines = [lead, "Updated " + at + ".",
                 "Entry zone: " + cards.level(plan["zone_low"], plan) + "–" + cards.level(plan["zone_high"], plan) + ".",
                 "Invalidation: " + cards.level(plan["invalidation_level"], plan) + "."]
        value = result_r(row.get("source_plan") or {}) if row["kind"] == "result" else None
        if value is not None:
            lines.append(f"Result: {value:+.1f}R.")
    if row.get("price_basis") == "plan":
        lines.append("Levels use the plan's prices.")
    if plan.get("target"):
        lines.append("Target level: " + "–".join(dict.fromkeys(cards.level(v, plan) for v in plan["target"])) + ".")
    until = row.get("entry_deadline_utc") or plan.get("valid_until_utc")
    if until:
        lines.append("Entry valid until " + cards._clock(until) + ".")
    if row.get("time_exit_utc"):
        lines.append("Time exit: " + cards._clock(row["time_exit_utc"]) + ".")
    if row["kind"] == "setup":
        lines.append("Registered " + cards._clock(row["registered_at_utc"]) + ".")
    if row.get("delayed_at_utc"):
        lines.insert(0, "Delayed update as of " + cards._clock(row["delayed_at_utc"]) + ".")
    text = "\n".join(lines) + "\n\n" + cards.NOTICES
    check_publication_copy({"body": text}, conditional_calls=calls)
    return {"lead": lead, "text": text, "conditional_calls": calls, "detail_lines": lines[1:]}


def validate(row):
    """The public geometry and copy must still equal this frozen Main plan."""
    from .plan_call_cards_v1 import card_plan
    raw = row["source_plan"]
    if posts._sha(raw) != row.get("state_alert_source_sha256"):
        raise posts.PlanPostError("PLAN_ALERT_SOURCE_BYTES_CHANGED")
    if raw.get("registration_hash") != row.get("source_plan_registration"):
        raise posts.PlanPostError("PLAN_ALERT_SOURCE_REGISTRATION_CHANGED")
    expected = card_plan(raw)
    for field in ("direction", "zone_low", "zone_high", "invalidation_level", "target", "valid_until_utc"):
        if row["levels"].get(field) != expected.get(field):
            raise posts.PlanPostError("PLAN_ALERT_SOURCE_FIELD_CHANGED:" + field)
    if row["text"] != compose(row)["text"]:
        raise posts.PlanPostError("PLAN_ALERT_SOURCE_COPY_CHANGED")


def payloads(row, **options):
    from .plan_call_cards_v1 import destination_payloads
    # Reuse the established length, thread, notice, chart-credit and parent
    # handling. The public source fields need no editorial variants.
    result = destination_payloads({**row, "state_alert_contract": None, "reader_contract": None}, **options)
    if options.get("carousel") and "instagram_business" in result:
        result["instagram_business"]["media_asset_ids"] = [options["carousel"][0]["asset_id"]]
    return result
