"""CC-466: source-bound reader fields. Formatting never writes new analysis.

Only newly authored packets opt in. Issued packets retain their bytes and their
existing recovery path. Acronym findings are a one-pass writing hint, never a veto.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re

from .event_article_guard_v1 import PUBLIC_NOTICE, CONFLICTS_NOTICE

CONTRACT = "CC466_V1"
EFFECTIVE = datetime(2026, 11, 11, 16, 30, tzinfo=timezone.utc)
LAYERS = (("macro", "Macro"), ("priced_in", "Priced in"),
          ("positioning", "Positioning"), ("fundamental", "Fundamentals"),
          ("geopolitical", "Geopolitics"), ("technical", "Structure"))
NOTICES = PUBLIC_NOTICE + "\n" + CONFLICTS_NOTICE
ACRONYMS = Path(__file__).resolve().parents[1] / "config/plan_reader_acronyms_v1.json"
BANNED = """
model estimate | base-case chance | the model | our model | model position | demo account | demo | paper account | paper trading
AI-run | AI-generated | as an AI | language model | LLM | GPT | Claude | Fable | Opus | Gemini | Codex | Antigravity | Anthropic | OpenAI | system prompt | the prompt | AI agent | subagent
vol-normalised | volatility-normalised | z-score | sd over | ATR | SMA | EFFR | USD leg | front-end gap | context about | clear by D1 sign
calls judged | time exits | not triggered | Levels use the plan's prices | over the period to | the desk is bullish on | the desk is bearish on | from our | ET run | analysis run
frozen call | freeze id | known-at | cost admission | admission check | armed plan | arming run | Guardian pass | kernel | our ledger | shadow call | short-term lane | mid-term lane | long-term lane | role pack | reply pack
our account | trading account | account balance | account size | our balance | equity curve | lot size | position size | our leverage | CFD | Exness | MT5 | IBKR | Interactive Brokers
buy now | sell now | you should | we recommend | guaranteed | risk-free | will definitely
Jim | GMT+7 | UTC
"""
TERMS = tuple(term.strip() for line in BANNED.splitlines() for term in line.split("|") if term.strip())
PATTERNS = (r"#[0-9a-f]{6,}", r"…|\.\.\.", r"\b[A-Z]{2,}(_[A-Z0-9]+)+\b",
            r"\b(M1|M5|M15|M30|H1|H4|D1|W1)\b", r"\b(US|JP|DE|UK)\d{1,2}Y\b",
            r"\bz ?[+\-−]\d", r"\b\d+(\.\d+)? lots?\b", r"\b(?:SMA|ATR)\d+\b")


def et(value):
    from .public_time_v1 import public_datetime
    local = public_datetime(value)
    return f"{local:%a} {local.day} {local:%b}, {local:%I:%M %p}".replace(", 0", ", ") + " ET"


def numbers(text):
    from .plan_analysis_pages_v1 import _numbers
    return _numbers(text)


def check_text(text, *, source, max_chars=None, check_numbers=True, prose=True, allowed=()):
    """Raise only for an actual copy/source defect; return soft acronym findings."""
    from .plan_analysis_pages_v1 import public_filter
    public_filter(text)
    clean = text.replace(PUBLIC_NOTICE, "").replace(CONFLICTS_NOTICE, "")
    clean = re.sub(r"https://[^\s]+", "", clean)
    if any(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", clean, re.I) for term in TERMS):
        raise ValueError("CC466_INTERNAL_OR_BANNED_TERM")
    if any(re.search(pattern, clean) for pattern in PATTERNS) or re.search(r"[{}]", clean):
        raise ValueError("CC466_CUT_SENTENCE_OR_INTERNAL_PATTERN")
    if max_chars is not None and len(text) > max_chars:
        raise ValueError("CC466_FIELD_TOO_LONG:" + str(max_chars))
    if check_numbers and numbers(clean) - numbers(source):
        raise ValueError("CC466_NUMBER_NOT_IN_BOUND_SOURCE:" + ",".join(sorted(numbers(clean) - numbers(source))))
    if prose:
        for line in clean.splitlines():
            line = line.strip().removeprefix("• ")
            if not line:
                continue
            if not re.search(r"[.!?\d]$", line):
                raise ValueError("CC466_UNFINISHED_SENTENCE")
            for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z])", line):
                if len(sentence.split()) > 22:
                    raise ValueError("CC466_SENTENCE_OVER_22_WORDS")
    base = set(json.loads(ACRONYMS.read_bytes())) | set(allowed)
    capitals = set(re.findall(r"\b[A-Z]{4,}\b", clean))
    sourced = {word for word in capitals if re.search(r"\b" + word + r"\b", source)}
    return {"status": "PASS", "automatic_acronyms": sorted(sourced - base),
            "unknown_acronyms": sorted(capitals - base - sourced)}


def page_footer(plan, freeze, *, legacy=False):
    states = {"WAITING": "waiting for entry", "TRIGGERED": "in position", "FILLED": "in position"}
    state=states.get(plan.get("status"))
    if legacy and state is None:
        state="closed"
    if plan.get("status") in {"CANCELLED","INVALIDATED","EXPIRED","VIEW_CHANGED","CLOSED","RESULT"}:
        state="closed"
    status=("Status: "+state if state else "Current entry status is unavailable") + " (updated " + et(
        plan.get("status_at_utc") or plan.get("registered_at_utc") or freeze["frozen_at_utc"]) + ")."
    return ["How this view was built: a main case, a written case against it, then a final decision. "
            "The plan was fixed at " + et(freeze["frozen_at_utc"]) + ", before this page was published.",
            status]


def source_packet(plan, run):
    """Whitelisted original analysis, not accounts, execution or raw input tables."""
    from . import plan_analysis_pages_v1 as pages
    lines = []

    def add(layer, filename, pointer, text):
        if not isinstance(text, (str, int, float)) or isinstance(text, bool):
            return
        text = str(text)
        if not text.strip():
            return
        # Retained role prose can mix private execution and public analysis.
        # Include complete safe sentences only. Final copy is checked again.
        safe = []
        for sentence in re.split(r"(?<=[.!?;])\s+", text):
            try:
                pages.public_filter(sentence)
            except ValueError:
                continue
            safe.append(sentence)
        if safe:
            lines.append({"id": "s" + str(len(lines)), "layer": layer, "text": " ".join(safe),
                          "ref": {"file": filename, "pointer": pointer}})

    scenario = plan.get("scenario_analysis") or {}
    mapping = {"mechanism": "macro", "driver": "macro", "priced": "priced_in", "positioning": "positioning",
               "acceptance": "story", "confirmations": "macro", "zone_reason": "technical",
               "invalidation_text": "invalidation", "invalidation_reason": "invalidation",
               "opposite_mechanism": "scenarios"}
    for key, layer in mapping.items():
        add(layer, "plan-export", "/scenario_analysis/" + key, scenario.get(key))
    for branch in ("base_case", "main_alternative"):
        for key in ("market_move", "probability_pct"):
            add("scenarios", "plan-export", "/scenario_analysis/" + branch + "/" + key,
                (scenario.get(branch) or {}).get(key))
    try:
        candidate, filename, pointer = pages._owner_candidate(plan, run)
        for key in ("rationale", "invalidation"):
            add("analysis", filename, pointer + "/" + key, candidate.get(key))
    except (KeyError, StopIteration, ValueError):
        candidate = {}
    primary = run["documents"].get("primary-native.json", {})
    for index, value in enumerate(primary.get("candidate_evaluations", [])):
        if value.get("candidate_id") != candidate.get("candidate_id"):
            continue
        for key in ("directional_thesis", "mechanism_and_transmission", "material_counterevidence", "invalidation"):
            add("analysis", "primary-native.json", f"/candidate_evaluations/{index}/{key}", value.get(key))
    # Exact public plan scalars support the plan table, not a copied private book.
    def scalars(value, pointer=""):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"zone", "invalidation_level", "direction", "entry_deadline_utc", "horizon_end_utc",
                           "time_exit_utc", "registered_at_utc", "status", "low", "high", "lower", "upper",
                           "minimum", "maximum", "zone_low", "zone_high", "invalidation_conditions",
                           "level", "price", "horizon_end_utc", "scenario_analysis"}:
                    scalars(child, pointer + "/" + key)
        elif isinstance(value, (str, int, float)):
            add("plan", "plan-export", pointer, value)
    scalars(plan)
    for key in ("registered_at_utc", "entry_deadline_utc", "status_at_utc"):
        if plan.get(key):
            lines.append({"id":"s"+str(len(lines)), "layer":"plan", "text":et(plan[key]),
                "ref":{"file":"plan-export", "pointer":"/"+key, "transform":"ET12"}})
    if scenario.get("horizon_end_utc"):
        lines.append({"id":"s"+str(len(lines)), "layer":"plan", "text":et(scenario["horizon_end_utc"]),
            "ref":{"file":"plan-export", "pointer":"/scenario_analysis/horizon_end_utc", "transform":"ET12"}})
    for parent,pointer in ((plan.get("outcome") or {},"/outcome"),
                           ((plan.get("outcome") or {}).get("score") or {},"/outcome/score")):
        for key in ("result_r","realized_r","r_multiple","resolved_at_utc","result"):
            if parent.get(key) is not None:
                add("result","plan-export",pointer+"/"+key,parent[key])
    return {"plan_id": plan["plan_id"], "registration_hash": plan["registration_hash"],
            "asset_id": plan["asset_id"], "sources": lines,
            "scenario_analysis": scenario,
            "result_r": str(result_r(plan)) if result_r(plan) is not None else None,
            "source_manifest": run["manifest"], "frozen_at_utc": run["freeze"]["frozen_at_utc"],
            "missing_export_fields": ["scenario_analysis." + k for k in mapping if not scenario.get(k)]}


def validate_fields(fields, source):
    """Validate each number against its declared source lines, not another plan."""
    sources = {s["id"]: s for s in source["sources"]}
    checks = []

    def field(value, limit=None):
        if not isinstance(value, dict) or not value.get("source_ids"):
            raise ValueError("CC466_FIELD_SOURCE_REQUIRED")
        refs = [sources[k] for k in value["source_ids"]]
        checks.append(check_text(value["text"], source="\n".join(s["text"] for s in refs), max_chars=limit))
        return value["text"]

    field(fields["hook"], 96)
    points = fields["points"]
    if fields.get("result_line"):
        text=field(fields["result_line"])
        match=re.search(r"Result: ([+−-]\d+\.\d)R\.",text)
        if not match:
            raise ValueError("CC466_SIGNED_R_RESULT_REQUIRED")
        if source.get("result_r") is None or Decimal(match[1].replace("−","-")) != Decimal(source["result_r"]):
            raise ValueError("CC466_R_RESULT_NOT_IN_EXPORT")
        if not isinstance(points,list) or len(points)>2:
            raise ValueError("CC466_TWO_RESULT_REVIEW_LINES_MAXIMUM")
        for point in points:
            field(point,90)
        return checks
    if not isinstance(points, list) or not 1 <= len(points) <= 5:
        raise ValueError("CC466_ONE_TO_FIVE_SOURCED_LAYERS_REQUIRED")
    order = [key for key, _ in LAYERS]
    layer_keys = [p["layer"] for p in points]
    if len(set(layer_keys)) != len(layer_keys) or layer_keys != sorted(layer_keys, key=order.index):
        raise ValueError("CC466_FORCE_ORDER_REQUIRED")
    if sum(p["layer"] == "technical" for p in points) > 1:
        raise ValueError("CC466_ONE_TECHNICAL_LINE_MAXIMUM")
    if any(p["layer"] != "technical" for p in source["sources"] if p["layer"] in order) and all(
            p["layer"] == "technical" for p in points):
        raise ValueError("CC466_HELD_MARKET_FORCES_OMITTED")
    for point in points:
        field(point, 90)
    main = field(fields["scenario_main"], 90)
    alt = field(fields["scenario_alt"], 90) if fields.get("scenario_alt") else None
    if not re.match(r"Main \(\d+%\): .+[.]$", main):
        raise ValueError("CC466_MAIN_ODDS_REQUIRED")
    # Exact explicit odds only. An absent alternative never becomes a complement.
    for key, text in (("base_case", main), ("main_alternative", alt)):
        branch = source.get("scenario_analysis", {}).get(key) or {}
        probability = branch.get("probability_pct")
        if text and not re.match(("Main" if key == "base_case" else "Alternative") + r" \(\d+%\): .+[.]$", text):
            raise ValueError("CC466_SCENARIO_LABEL_REQUIRED")
        if text and probability is None:
            raise ValueError("CC466_SCENARIO_ODDS_NOT_SUPPLIED")
        if text and Decimal(re.search(r"\((\d+)%\)", text)[1]) != Decimal(str(probability)):
            raise ValueError("CC466_SCENARIO_ODDS_CHANGED")
    if (source.get("scenario_analysis", {}).get("main_alternative") or {}).get("probability_pct") is not None and not alt:
        raise ValueError("CC466_HELD_ALTERNATIVE_ODDS_OMITTED")
    for key in ("window", "alt_text"):
        if fields.get(key):
            field(fields[key])
    return checks


def attach_call(row):
    """The concise call still states every field Jim decision 40 requires."""
    from . import plan_status_posts_v1 as posts
    from .event_article_guard_v1 import compact_reader_conditional_call_text
    plan = row["levels"]
    low, high, invalid = (plan[k] for k in ("zone_low", "zone_high", "invalidation_level"))
    side = "below" if Decimal(str(invalid)) < Decimal(str(low)) else "above"
    call = {"market": row["symbol"] if row["symbol"] in {"EURUSD", "USDJPY"} else row["instrument_title"],
            "condition": "price reaches " + posts._level(low) + "–" + posts._level(high),
            "direction": plan["direction"], "horizon": et(row.get("time_exit_utc") or plan["valid_until_utc"]),
            "invalidation": side + " " + posts._level(invalid)}
    call["market"] = {"EURUSD":"EUR/USD", "USDJPY":"USD/JPY"}.get(call["market"], call["market"])
    return {"reader_call_line":compact_reader_conditional_call_text(call), "conditional_calls":[call]}


def result_r(plan):
    """Only an explicitly exported R result; STOPPED does not imply -1R."""
    outcome=plan.get("outcome") or {}
    score=outcome.get("score") or {}
    for parent in (score,outcome):
        for key in ("result_r", "realized_r", "r_multiple"):
            value=parent.get(key)
            if isinstance(value,(int,float)) and not isinstance(value,bool):
                number=Decimal(str(value))
                if number.is_finite():
                    return number
    return None


def payloads(row, card_id, *, chart_credit=False, parents=None, portrait_id=None):
    from . import plan_status_posts_v1 as posts
    fields, source = row["reader_fields"], row["reader_source"]
    validate_fields(fields, source)
    url = row["analysis_publication"]["canonical_url"]
    if not re.fullmatch(r"https://capitalchronicle\.substack\.com/p/[a-z0-9-]+", url):
        raise ValueError("CC466_CONFIRMED_PLAN_PAGE_REQUIRED")
    hook = fields["hook"]["text"]
    scenarios = [fields["scenario_main"]["text"]] if fields.get("scenario_main") else []
    if fields.get("scenario_alt"):
        scenarios.append(fields["scenario_alt"]["text"])
    labels = dict(LAYERS)
    points = [labels.get(p["layer"],"Review") + ": " + p["text"] for p in fields["points"]]
    window = fields.get("window", {}).get("text", "")
    call_line = row.get("reader_call_line", "")
    credit = "\n\n" + posts.CHART_CREDIT if chart_credit else ""
    long = "\n\n".join(filter(None, [hook, "\n".join(points), "\n".join(scenarios), window,
                                          call_line, "Full analysis: " + url, NOTICES])) + credit
    result_line=fields.get("result_line",{}).get("text","")
    if result_line:
        long="\n\n".join([result_line,"\n".join(points),"R is the risk planned at entry.",
            "Every call and its result: "+url,NOTICES])+credit
    root = (result_line if result_line else hook + "\n\n" + "\n".join(scenarios))
    link_reply = "Full analysis, and what would change our mind: " + url + "\n\n" + NOTICES
    reasons = "\n".join(points[:3]) + ("\n" + call_line if call_line else "")
    x_parts = [root, link_reply, reasons]
    # Attribution stays with the chart. It does not push the root's link back in.
    if credit:
        x_parts[2] += credit
    x_parts=[part for part in x_parts if part.strip()]
    if any(posts._x_length(part) > 280 for part in x_parts):
        raise ValueError("CC466_X_FIELD_SET_TOO_LONG_REWRITE_REQUIRED")
    threads_root = "\n\n".join([root, "Full analysis: " + url, NOTICES])
    thread_parts = [threads_root, reasons + credit]
    if any(len(part) > 500 for part in thread_parts):
        raise ValueError("CC466_THREADS_FIELD_SET_TOO_LONG_REWRITE_REQUIRED")
    result = {}
    for destination in ("telegram", "discord", "threads", "facebook_page", "instagram_business", "x", "substack_notes"):
        media_id = portrait_id if portrait_id and destination in {"threads", "instagram_business"} else card_id
        parts = x_parts if destination == "x" else thread_parts if destination == "threads" else [long]
        maximum = {"telegram": 4096, "discord": 2000, "instagram_business": 2200}.get(destination, 60000)
        if destination not in {"x", "threads"} and len(parts[0]) > maximum:
            raise ValueError("CC466_DESTINATION_COPY_TOO_LONG:" + destination)
        payload = {"destination": destination, "text": parts[0], "full_text": "\n\n".join(parts),
                   "media_asset_ids": [media_id] if media_id else []}
        if len(parts) > 1:
            payload.update(root_text=parts[0], reply_texts=parts[1:], posts=[{
                "text": text, "order": index, "role": "root" if index == 0 else "reply",
                "media_asset_ids": [media_id] if media_id and index == 0 else []} for index, text in enumerate(parts)])
        parent = (parents or {}).get(destination)
        if parent and parent.get("public_object_id"):
            payload.update(reply_to_id=str(parent["public_object_id"]), reply_to_url=parent["public_object_url"])
        if destination == "discord" and row.get("discord_delivery") == "channel":
            payload["discord_channel_post"] = True
        if destination == "telegram":
            payload["telegram_text_with_card_preview"] = bool(card_id)
        result[destination] = payload
    return result
