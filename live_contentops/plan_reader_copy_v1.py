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
THREAD_CONTRACT = "CC549_V1"
LEVEL_CONTRACT = "CC584_V1"
LEVEL_EFFECTIVE = datetime(2026, 11, 14, tzinfo=timezone.utc)
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


def thread_terms(raw, *, level_contract=None):
    """One explicit price basis and two distinct clocks from this Main export."""
    from . import plan_call_cards_v1 as cards, plan_status_posts_v1 as posts
    levels = cards.card_plan(raw)
    mapped = levels.get("price_basis") == "instrument"
    instrument = raw.get("public_instrument") or {}
    market = posts._instrument_title(raw["asset_id"], levels) if mapped else posts.TITLES[raw["asset_id"]]
    name = instrument["symbol"] if mapped else posts.TITLES[raw["asset_id"]]
    price_name = "Spot" if raw["asset_id"] in {"XAUUSD", "EURUSD", "USDJPY"} else posts.TITLES[raw["asset_id"]]
    operators = {"GT": "above ", "GTE": "at or above ", "LT": "below ", "LTE": "at or below "}
    conditions, refs = [], []
    if mapped and instrument.get("contract_month"):
        refs.append({"file": "plan-export", "pointer": "/public_instrument/contract_month"})
    for index, condition in enumerate(raw.get("invalidation_conditions") or []):
        if condition.get("field") not in {"close", "low", "high", "bid", "ask", "mid"} or condition.get("operator") not in operators:
            continue
        before = level_contract == LEVEL_CONTRACT
        conditions.append(f"{price_name} " + ("plan cancelled on " if before else "")
            + f"{condition['field']} {operators[condition['operator']]}{posts._level(condition['threshold'])}"
            + (" before entry" if before else ""))
        refs.append({"file": "plan-export", "pointer": f"/invalidation_conditions/{index}/threshold"})
    if mapped:
        side = "below " if Decimal(str(levels["invalidation_level"])) < Decimal(str(levels["zone_low"])) else "above "
        conditions.append(f"{name} " + ("plan wrong " if level_contract == LEVEL_CONTRACT else "invalidation ")
            + f"{side}{cards.level(levels['invalidation_level'], levels)}"
            + (" after entry" if level_contract == LEVEL_CONTRACT else ""))
        refs.append({"file": "plan-export", "pointer": "/public_instrument/invalidation_level", "transform": "PUBLIC_TICK"})
    if not conditions:
        raise ValueError("CC549_INVALIDATION_NOT_EXPORTED")
    display = dict(levels)
    for key in ("zone_low", "zone_high"):
        display[key] = cards.level(levels[key], levels).replace(",", "")
    display["entries"] = [{key: cards.level(value, levels).replace(",", "") if key != "kind" else value
                           for key, value in entry.items()} for entry in levels.get("entries") or []]
    prefix = "/public_instrument" if mapped else ""
    for index, entry in enumerate(levels.get("entries") or []):
        for key in entry:
            if key != "kind":
                refs.append({"file": "plan-export", "pointer": f"{prefix}/entries/{index}/{key}",
                             **({"transform": "PUBLIC_TICK"} if mapped else {})})
    if not levels.get("entries"):
        for key in ("zone_low", "zone_high") if mapped else ("minimum", "maximum"):
            refs.append({"file": "plan-export", "pointer": prefix + "/" + key if mapped else "/zone/" + key,
                         **({"transform": "PUBLIC_TICK"} if mapped else {})})
    deadlines = [(key, raw[key]) for key in ("entry_deadline_utc", "expires_at_utc") if raw.get(key)]
    deadline_key, deadline = min(deadlines, key=lambda pair: posts._utc(pair[1])) if deadlines else (None, None)
    forecast = raw.get("forecast_probabilities") or {}
    scenario = raw.get("scenario_analysis") or {}
    end_ref, end = next(((pointer, value) for pointer, value in (
        ("/time_exit_utc", raw.get("time_exit_utc")), ("/horizon_end_utc", raw.get("horizon_end_utc")),
        ("/forecast_probabilities/horizon_end_utc", forecast.get("horizon_end_utc")),
        ("/scenario_analysis/horizon_end_utc", scenario.get("horizon_end_utc"))) if value), (None, None))
    clocks = []
    opens = raw.get("not_before_utc")
    if opens and raw.get("registered_at_utc") and posts._utc(opens) > posts._utc(raw["registered_at_utc"]):
        clocks.append("Entry opens " + et(opens) + ".")
        refs.append({"file": "plan-export", "pointer": "/not_before_utc", "transform": "ET12"})
    if deadline:
        clocks.append("Entry can start until " + et(deadline) + ".")
        refs.append({"file": "plan-export", "pointer": "/" + deadline_key, "transform": "ET12"})
    if end:
        clocks.append("Filled positions close by " + et(end) + ".")
        refs.append({"file": "plan-export", "pointer": end_ref, "transform": "ET12"})
    invalidation = "; ".join(conditions)
    call = {"market": market, "direction": levels["direction"], "condition": posts._entry_condition(display),
            "horizon": " ".join(clocks).rstrip("."), "invalidation": invalidation}
    from .event_article_guard_v1 import thread_reader_conditional_call_text
    return {"contract": THREAD_CONTRACT, "market": market, "price_basis": "instrument" if mapped else "plan",
            "title": posts.TITLES[raw["asset_id"]] + ": " + invalidation, "invalidation": invalidation,
            "entry_deadline_utc": deadline, "time_exit_utc": end, "clocks": clocks,
            "call": call, "call_line": thread_reader_conditional_call_text(call), "refs": refs}


def check_thread_text(text, *, force=False):
    """CC-549's observed copy defects, only for newly authored thread packets."""
    if re.search(r"\b(?:I|I'm|I've|I'd|I'll|me|my|mine)\b", text, re.I):
        raise ValueError("CC549_DESK_VOICE_MUST_BE_WE")
    if re.search(r"\b(?:supplied|provided|the pack|the review given)\b", text, re.I):
        raise ValueError("CC549_WRITER_INPUT_LANGUAGE")
    if force and re.search(r"\bwe\s+(?:watch|track|monitor|look for|focus on)\b", text, re.I) and not re.search(
            r"\d|\b(?:rose|fell|risen|fallen|since|increased|decreased|widened|narrowed)\b", text, re.I):
        raise ValueError("CC549_FORCE_HAS_NO_FINDING")
    return {"status": "PASS"}


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


def source_packet(plan, run, *, original_probabilities=False, thread=False, level_contract=None):
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

    scenario = json.loads(json.dumps(plan.get("scenario_analysis") or {}))
    original_probability = None
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
    if original_probabilities and (scenario.get("base_case") or {}).get("probability_pct") is None:
        # Some Main exports omit an odds field that the bound original owner
        # explicitly wrote. Use only that directional statement, never 100-p,
        # a touch probability, a target-first probability or a base rate.
        direction = str(plan.get("direction") or "").upper()
        movement = "lower" if direction in {"BEARISH", "SHORT"} else "higher" if direction in {"BULLISH", "LONG"} else None
        rationale = next((s for s in lines if s["ref"] == {"file": filename, "pointer": pointer + "/rationale"}), None) if candidate else None
        matches = list(re.finditer(r"(?<![\d.])(\d{1,3}(?:\.\d+)?)%\s+" + movement + r"\s+at\s+(?:the\s+)?exit\b",
                                  rationale["text"], re.I)) if movement and rationale else []
        if len(matches) == 1 and 0 <= Decimal(matches[0][1]) <= 100:
            value = float(matches[0][1])
            probability = int(value) if value.is_integer() else value
            scenario["base_case"] = {**(scenario.get("base_case") or {}), "probability_pct": probability}
            original_probability = {"probability_pct": probability, "direction": movement,
                "statement": matches[0][0], "ref": rationale["ref"], "source_id": rationale["id"]}
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
    if thread:
        terms = thread_terms(plan, level_contract=level_contract)
        for ref in terms["refs"]:
            lines.append({"id": "s" + str(len(lines)), "layer": "plan",
                          "text": pages._source_text(run, ref), "ref": ref})
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
            "missing_export_fields": ["scenario_analysis." + k for k in mapping if not scenario.get(k)],
            **({"thread_contract": THREAD_CONTRACT, "thread_terms": terms} if thread else {}),
            **({"level_contract": level_contract} if level_contract else {}),
            **({"source_contract": "CC432_ORIGINAL_PROBABILITY_V1", "original_probability_binding": original_probability}
               if original_probability else {})}


def validate_fields(fields, source):
    """Validate each number against its declared source lines, not another plan."""
    sources = {s["id"]: s for s in source["sources"]}
    checks = []

    def field(value, limit=None):
        if not isinstance(value, dict) or not value.get("source_ids"):
            raise ValueError("CC466_FIELD_SOURCE_REQUIRED")
        refs = [sources[k] for k in value["source_ids"]]
        if source.get("thread_contract") == THREAD_CONTRACT:
            check_thread_text(value["text"])
        if source.get("level_contract") == LEVEL_CONTRACT:
            from .plan_analysis_pages_v1 import check_reader_claim
            check_reader_claim(value["text"], source="\n".join(s["text"] for s in refs),
                source_name=value.get("source_name", ""), pricing_source=value.get("pricing_source"))
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
    minimum = 0 if source.get("thread_contract") == THREAD_CONTRACT else 1
    if not isinstance(points, list) or not minimum <= len(points) <= 5:
        raise ValueError("CC466_ONE_TO_FIVE_SOURCED_LAYERS_REQUIRED")
    order = [key for key, _ in LAYERS]
    layer_keys = [p["layer"] for p in points]
    if len(set(layer_keys)) != len(layer_keys) or layer_keys != sorted(layer_keys, key=order.index):
        raise ValueError("CC466_FORCE_ORDER_REQUIRED")
    if sum(p["layer"] == "technical" for p in points) > 1:
        raise ValueError("CC466_ONE_TECHNICAL_LINE_MAXIMUM")
    if points and any(p["layer"] != "technical" for p in source["sources"] if p["layer"] in order) and all(
            p["layer"] == "technical" for p in points):
        raise ValueError("CC466_HELD_MARKET_FORCES_OMITTED")
    for point in points:
        field(point, 90)
        if source.get("thread_contract") == THREAD_CONTRACT:
            check_thread_text(point["text"], force=True)
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
    if row.get("thread_contract") == THREAD_CONTRACT:
        terms = thread_terms(row["source_plan"], level_contract=row.get("level_contract"))
        return {"reader_call_line": terms["call_line"], "conditional_calls": [terms["call"]]}
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
    if source.get("level_contract") == LEVEL_CONTRACT and call_line:
        # The two exact phase conditions and clocks may exceed a single post.
        # Keep the link first and the points second; continue with complete
        # sentences rather than asking a writer to shorten frozen plan facts.
        facts = [*points[:3], *re.split(r"(?<=\.)\s+(?=[A-Z])", call_line)]
        if chart_credit:
            facts.append(posts.CHART_CREDIT)
        continuations, current = [], ""
        for fact in facts:
            if posts._x_length(fact) > 280:
                raise ValueError("CC466_X_BOUND_SENTENCE_TOO_LONG")
            joined = (current + "\n" + fact).strip()
            if current and posts._x_length(joined) > 280:
                continuations.append(current)
                current = fact
            else:
                current = joined
        if current:
            continuations.append(current)
        x_parts = [root, link_reply, *continuations]
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
