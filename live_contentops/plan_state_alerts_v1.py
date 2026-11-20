"""Source-bound state alerts in the existing plan publication path.

Queued interim alerts retain their original scenario text through validation and recovery.
"""
from __future__ import annotations

from decimal import Decimal
import re

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
    thread = row.get("thread_contract") == "CC549_V1"
    if thread:
        from .plan_reader_copy_v1 import thread_terms, check_thread_text
        terms = thread_terms(row["source_plan"], level_contract=row.get("level_contract"))
        if row["kind"] == "setup":
            lead = title + ": new plan."
            if row.get("level_contract") == "CC584_V1" and row.get("state") == "WAITING":
                condition = terms["call"]["condition"].replace("price trades", "price to trade")
                lead = title + ": armed, waiting for " + condition + "."
            calls = [terms["call"]]
            lines = [lead, terms["call_line"]]
            if row.get("state") in {"FILLED", "TRIGGERED"}:
                lines.append("An entry filled; the position is open.")
        else:
            words = {"FILLED": "an entry filled; the position is open", "TRIGGERED": "an entry filled; the position is open",
                     "CANCELLED": "the plan was withdrawn", "VIEW_CHANGED": "the view changed",
                     "INVALIDATED": "the invalidation condition was reached", "CLOSED": "the position closed",
                     "EXPIRED": "the entry window ended"}
            lead = title + ": " + (cards.ending_words(row) if row["kind"] == "result" else words[row["state"]]) + "."
            lines = [lead, "Updated " + at + ".", "Entry condition: " + terms["call"]["condition"] + ".",
                     terms["invalidation"] + ".", *terms["clocks"]]
            value = result_r(row.get("outcome_source_plan") or row.get("source_plan") or {}) if row["kind"] == "result" else None
            if value is not None:
                lines.append(f"Result: {value:+.1f}R.")
        check_thread_text("\n".join(lines))
    elif row["kind"] == "setup":
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
        value = result_r(row.get("outcome_source_plan") or row.get("source_plan") or {}) if row["kind"] == "result" else None
        if value is not None:
            lines.append(f"Result: {value:+.1f}R.")
    if row.get("price_basis") == "plan" and not thread:
        lines.append("Levels use the plan's prices.")
    if plan.get("target"):
        lines.append("Target level: " + "–".join(dict.fromkeys(cards.level(v, plan) for v in plan["target"])) + ".")
    until = row.get("entry_deadline_utc") or plan.get("valid_until_utc")
    if until and not thread:
        lines.append("Entry valid until " + cards._clock(until) + ".")
    if row.get("time_exit_utc") and not thread:
        lines.append("Time exit: " + cards._clock(row["time_exit_utc"]) + ".")
    if row["kind"] == "setup" and row.get("analysis_lines_contract"):
        from . import plan_scenario_lines_v1 as scenario_lines
        if row["analysis_lines_contract"] != scenario_lines.CONTRACT:
            raise posts.PlanPostError("PLAN_ALERT_ANALYSIS_LINES_CONTRACT_UNKNOWN")
        lines.extend(scenario_lines.analysis_lines(row["source_plan"]))
    if row["kind"] == "setup":
        lines.append("Registered " + cards._clock(row["registered_at_utc"]) + ".")
    if row.get("delayed_at_utc"):
        lines.insert(0, "Delayed update as of " + cards._clock(row["delayed_at_utc"]) + ".")
    if row.get("analysis_copy_contract"):
        from .plan_reader_copy_v1 import analysis_scenario_lines, verified_analysis_lines
        raw = row["source_plan"]
        layers = verified_analysis_lines(raw, row["analysis_layer_quotes"])
        scenarios = analysis_scenario_lines(raw) if row["kind"] == "setup" else []
        lines = [*layers, *scenarios, *lines]
        if row.get("analysis_link"):
            lines.append("Full analysis: " + row["analysis_link"])
    text = "\n".join(lines) + "\n\n" + cards.NOTICES
    check_publication_copy({"body": text}, conditional_calls=calls)
    return {"lead": lead, "text": text, "conditional_calls": calls, "detail_lines": lines[1:]}


def analysis_thread_parts(row, body, notices, *, destination, limit):
    """Keep complete source lines and plan sentences on the two short routes."""
    from .plan_reader_copy_v1 import analysis_scenario_lines, verified_analysis_lines

    width = posts._x_length if destination == "x" else len
    link = "Full analysis: " + row["analysis_link"] if row.get("analysis_link") else ""
    layer_lines = verified_analysis_lines(row["source_plan"], row["analysis_layer_quotes"])
    if row["kind"] == "setup":
        layer_lines += analysis_scenario_lines(row["source_plan"])
    detail = body.splitlines()[len(layer_lines):]
    if link and detail[-1:] == [link]:
        detail.pop()

    def pack(lines):
        parts = []
        for line in lines:
            # An exact call can contain several sentences. Sentence boundaries
            # let short destinations carry the full condition and both clocks.
            sentences = [line] if width(line) <= limit else re.split(r"(?<=[.!?])\s+(?=[A-Z])", line)
            for sentence in sentences:
                if width(sentence) > limit:
                    raise posts.PlanPostError("CC688_COMPLETE_SENTENCE_TOO_LONG:" + destination)
                joined = parts[-1] + "\n" + sentence if parts else sentence
                if parts and width(joined) <= limit:
                    parts[-1] = joined
                else:
                    parts.append(sentence)
        return parts

    if destination == "x" and link:
        parts = pack(layer_lines)
        if parts:
            return [parts[0], link + "\n\n" + notices, *parts[1:], *pack(detail)]
        return [detail[0], link + "\n\n" + notices, *pack(detail[1:])]
    # The root holds the chart credit. Keeping the call sentences together
    # avoids interrupting their exact wording with that credit or the notices.
    tail = [*detail, *([link] if link else []), notices]
    return [*pack(layer_lines), *pack(tail)] if layer_lines else [tail[0], *pack(tail[1:])]


def _inherits_target_omission(row, store):
    if (store is None or row["kind"] != "result" or row["levels"].get("target") is not None
            or not row.get("parent_key") or not row.get("source_plan_registration")):
        return False
    try:
        parent = posts._row_payload(store, row["parent_key"])
    except posts.PlanPostError:
        return False
    registration = parent.get("source_plan_registration") or parent.get("source_plan_hash")
    return (parent.get("kind") == "setup" and parent.get("plan_id") == row["plan_id"]
            and parent.get("symbol") == row["symbol"] and registration == row["source_plan_registration"]
            and (parent.get("levels") or {}).get("target") is None)


def validate(row, *, store=None):
    """The public geometry and copy must still equal this frozen Main plan."""
    from .plan_call_cards_v1 import card_plan
    raw = row["source_plan"]
    if posts._sha(raw) != row.get("state_alert_source_sha256"):
        raise posts.PlanPostError("PLAN_ALERT_SOURCE_BYTES_CHANGED")
    if raw.get("registration_hash") != row.get("source_plan_registration"):
        raise posts.PlanPostError("PLAN_ALERT_SOURCE_REGISTRATION_CHANGED")
    outcome_source = row.get("outcome_source_plan")
    if outcome_source is not None:
        if posts._sha(outcome_source) != row.get("outcome_source_sha256"):
            raise posts.PlanPostError("PLAN_ALERT_OUTCOME_SOURCE_BYTES_CHANGED")
        if (outcome_source.get("plan_id") != row["plan_id"] or outcome_source.get("asset_id") != row["symbol"]
                or outcome_source.get("registration_hash") != raw.get("registration_hash")):
            raise posts.PlanPostError("PLAN_ALERT_OUTCOME_SOURCE_REGISTRATION_CHANGED")
    expected = card_plan(raw)
    for field in ("direction", "zone_low", "zone_high", "invalidation_level", "valid_until_utc"):
        if row["levels"].get(field) != expected.get(field):
            raise posts.PlanPostError("PLAN_ALERT_SOURCE_FIELD_CHANGED:" + field)
    # The original post can omit a target. A result can inherit that omission
    # only from the same frozen setup, never from a changed result payload.
    if row["levels"].get("target") != expected.get("target") and not _inherits_target_omission(row, store):
        raise posts.PlanPostError("PLAN_ALERT_SOURCE_FIELD_CHANGED:target")
    if row.get("thread_contract") == "CC549_V1":
        from .plan_reader_copy_v1 import thread_terms
        terms = thread_terms(raw, level_contract=row.get("level_contract"))
        for field, key in (("instrument_title", "market"), ("price_basis", "price_basis"),
                           ("entry_deadline_utc", "entry_deadline_utc"), ("time_exit_utc", "time_exit_utc")):
            if row.get(field) != terms[key]:
                raise posts.PlanPostError("PLAN_ALERT_SOURCE_FIELD_CHANGED:" + field)
    if row.get("analysis_link") and store is not None:
        from .plan_analysis_pages_v1 import confirmed_publication
        publication = confirmed_publication(store, raw) or {}
        if publication.get("canonical_url") != row["analysis_link"]:
            raise posts.PlanPostError("CC688_CANONICAL_PLAN_LINK_CHANGED")
    if row["text"] != compose(row)["text"]:
        raise posts.PlanPostError("PLAN_ALERT_SOURCE_COPY_CHANGED")


def payloads(row, **options):
    from .plan_call_cards_v1 import destination_payloads, destinations_for
    # Reuse the established length, thread, notice, chart-credit and parent
    # handling. The public source fields need no editorial variants.
    parents = options.pop("parents", None) or {}
    compiled = {**row, "state_alert_contract": None, "reader_contract": None}
    if parents.get("discord", {}).get("delivery_mode") == "standalone":
        compiled["discord_delivery"] = "channel"
    replies = {d: route for d, route in parents.items() if route.get("public_object_id")}
    result = destination_payloads(compiled, parents=replies, destinations=destinations_for(row), **options)
    if options.get("carousel") and "instagram_business" in result:
        result["instagram_business"]["media_asset_ids"] = [options["carousel"][0]["asset_id"]]
    return result
