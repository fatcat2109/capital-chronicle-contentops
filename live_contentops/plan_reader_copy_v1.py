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

from .event_article_guard_v1 import PUBLIC_NOTICE, CONFLICTS_NOTICE, check_publication_copy

CONTRACT = "CC466_V1"
THREAD_CONTRACT = "CC549_V1"
LEVEL_CONTRACT = "CC584_V1"
LEVEL_EFFECTIVE = datetime(2026, 11, 14, tzinfo=timezone.utc)
EFFECTIVE = datetime(2026, 11, 11, 16, 30, tzinfo=timezone.utc)
ANALYSIS_COPY = "CC688_V1"
NINE_LAYER_COPY = "CC730_V1"
STATUS_ANALYSIS_CONTRACTS = (ANALYSIS_COPY, NINE_LAYER_COPY)
ANALYSIS_LAYERS = (
    ("macro", "Macro"), ("fundamental", "Fundamentals"), ("positioning_sentiment", "Positioning and sentiment"),
    ("options_gamma", "Options and gamma"), ("priced_in", "Priced in"), ("technical", "Technical"),
)
PLAN_LAYER_ORDER = (
    ("macro", "Macro"),
    ("event_and_cause", "Event and cause"),
    ("fundamental", "Fundamentals"),
    ("priced_in", "Priced in"),
    ("positioning_sentiment", "Positioning and sentiment"),
    ("options_gamma", "Options and gamma"),
    ("cross_asset_and_contagion", "Cross-asset and contagion"),
    ("technical", "Technical"),
    ("scenarios", "Scenarios"),
)
_SCENARIO_CASES = (("base_case", "Main"), ("main_alternative", "Alternative"))
_PLAN_CLOCK_FIELDS = ("registered_at_utc", "not_before_utc", "entry_deadline_utc", "expires_at_utc",
                      "time_exit_utc", "horizon_end_utc")
_EVENT_CAUSE = re.compile(r"\b(?:after|because|following|prompted|triggered|drove|led to)\b", re.I)
_PLAN_INTERNAL_REF = re.compile(r"\b[a-z0-9]+_[a-z0-9_]+\b|\bCC[- ]?\d+\b|\bKB:|\.md\b|"
                                r"@[0-9a-f]{7,}\b|\b[0-9a-f]{12,}\b|\b[A-Z]:\\", re.I)
_LAYER_ALIASES = {
    "fundamentals": "fundamental",
    "positioning_and_sentiment": "positioning_sentiment",
    "positioning": "positioning_sentiment",
    "sentiment": "positioning_sentiment",
    "options_and_gamma": "options_gamma",
    "options": "options_gamma",
    "gamma": "options_gamma",
}
_UNAVAILABLE_LAYER_STATES = {"unavailable", "missing", "stale", "not_used", "not_available"}
_FUNDAMENTAL = re.compile(r"\b(?:earnings|revenue|valuations?|inventor(?:y|ies)|stockpiles?|barrels|"
                          r"supply|demand|production|output|shipments?|rate differential|net inflows?)\b", re.I)
_OPTIONS = re.compile(r"\b(?:options?|gamma|gex|implied volatility|strikes?|skew)\b", re.I)
_STRUCTURE = re.compile(r"\b(?:highs?|lows?|trend|brea(?:k|ch)\w*|levels?|shelf|"
                         r"close[ds]?|entry|support|resistance|price|band)\b", re.I)
_UNAVAILABLE_LAYER = re.compile(r"\b(?:unavailable|stale|not (?:read|used|available|consulted)|"
                                r"no (?:usable|fresh|current|reliable) (?:input|data|read|options|gamma))\b", re.I)
_LAYER_SPAN = re.compile(r"(?<=[.!?])\s+|\s*[;\n]\s*")
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


def thread_terms(raw, *, level_contract=None, original_stop=None):
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
    stop = (levels["invalidation_level"], {"file": "plan-export", "pointer": "/public_instrument/invalidation_level",
                                         "transform": "PUBLIC_TICK"}) if mapped else original_stop
    stop_text = None
    if stop:
        value, ref = stop
        side = "below" if Decimal(str(value)) < Decimal(str(levels["zone_low"])) else "above"
        price = cards.level(value, levels) if mapped else posts._level(value)
        stop_text = f"{side} {price}"
        conditions.append(f"{name} " + ("plan wrong " if level_contract == LEVEL_CONTRACT else "invalidation ")
            + stop_text + (" after entry" if level_contract == LEVEL_CONTRACT else ""))
        refs.append(ref)
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
    title = posts.TITLES[raw["asset_id"]] + ": " + invalidation
    if level_contract == LEVEL_CONTRACT:
        entries = levels.get("entries") or []
        limit = next((entry for entry in entries if entry["kind"] == "LIMIT"), None)
        if entries and limit is None:
            side = "below" if levels["direction"] == "bearish" else "above"
            entry_text = f"{side} {cards.level(entries[0]['level'], levels)}"
        else:
            zone = limit or levels
            low, high = (cards.level(zone[key], levels) for key in ("zone_low", "zone_high"))
            entry_text = f"at {low}" if low == high else f"at {low}–{high}"
        title = f"{posts.TITLES[raw['asset_id']]}: {levels['direction']} {entry_text}"
        if stop_text:
            title += f", wrong {stop_text}"
    from .event_article_guard_v1 import thread_reader_conditional_call_text
    return {"contract": THREAD_CONTRACT, "market": market, "price_basis": "instrument" if mapped else "plan",
            "title": title, "invalidation": invalidation,
            "entry_deadline_utc": deadline, "time_exit_utc": end, "clocks": clocks,
            "call": call, "call_line": thread_reader_conditional_call_text(call), "refs": refs}


def page_thread_terms(plan, run, *, level_contract):
    from .plan_analysis_pages_v1 import _owner_candidate

    original_stop = None
    if level_contract == LEVEL_CONTRACT:
        try:
            candidate, filename, pointer = _owner_candidate(plan, run)
        except (KeyError, StopIteration):
            candidate = {}
        direction = {"LONG": "BULLISH", "SHORT": "BEARISH"}.get(candidate.get("direction"), candidate.get("direction"))
        if (direction == plan["direction"] and candidate.get("entry_bounds") == plan["zone"]
                and candidate.get("stop_loss") is not None):
            original_stop = candidate["stop_loss"], {"file": filename, "pointer": pointer + "/stop_loss"}
    return thread_terms(plan, level_contract=level_contract, original_stop=original_stop)


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


def verbatim_analysis_spans(value):
    for span in _LAYER_SPAN.split(value.strip()):
        span = " ".join(span.split()).strip(" ,;:")
        span = re.sub(r"^(?:ACCEPTED|AMBIGUOUS|REJECTED)[,: ]+\s*", "", span)
        if span:
            text = span[0].upper() + span[1:]
            yield text if text[-1] in ".?!" else text + "."


def analysis_layer_options(plan):
    """Public, directly quotable sentences and source pointers from the frozen export."""
    from .plan_analysis_pages_v1 import check_reader_claim

    name_by_layer = dict(ANALYSIS_LAYERS)
    sources = {layer: [] for layer in name_by_layer}

    def add(layer, value, pointer, *, match=None):
        if not isinstance(value, str):
            return
        for text in verbatim_analysis_spans(value):
            if (_UNAVAILABLE_LAYER.search(text) or (match and not match.search(text))
                    or re.search(r"\b(?:bullish|bearish)\b", text, re.I)):
                continue
            if len(text) > 220 or any(item["text"] == text for item in sources[layer]):
                continue
            try:
                check_text(text, source=value, prose=False)
                check_thread_text(text, force=True)
                check_reader_claim(text, source=text)
                check_publication_copy({"body": text}, require_notice=False)
            except ValueError:
                continue
            sources[layer].append({"text": text, "ref": {"file": "plan-export", "pointer": pointer}})

    explicit = plan.get("analysis_layers")
    if isinstance(explicit, (dict, list)):
        entries = (explicit.items() if isinstance(explicit, dict)
                   else ((str(index), value) for index, value in enumerate(explicit)))
        for key, value in entries:
            label = key if isinstance(explicit, dict) else value.get("layer") if isinstance(value, dict) else None
            label = str(label).lower().replace("-", "_").replace(" ", "_")
            layer = _LAYER_ALIASES.get(label, label)
            if layer not in sources:
                continue
            pointer = "/analysis_layers/" + key.replace("~", "~0").replace("/", "~1")
            if isinstance(value, dict):
                state = str(value.get("state") or value.get("status") or "").lower()
                if value.get("used") is False or value.get("available") is False or state in _UNAVAILABLE_LAYER_STATES:
                    continue
                field = "text" if "text" in value else "line"
                add(layer, value.get(field), pointer + "/" + field)
            else:
                add(layer, value, pointer)
    else:
        # Older exports bundled the analyst's actual observations in the
        # scenario fields. A named input alone is not an analyst observation.
        scenario = plan.get("scenario_analysis") or {}

        def legacy(layer, fields, pattern=None):
            for field in fields:
                add(layer, scenario.get(field), "/scenario_analysis/" + field, match=pattern)

        legacy("macro", ("driver",))
        legacy("fundamental", ("fundamental", "fundamentals", "mechanism", "driver", "positioning"), _FUNDAMENTAL)
        legacy("positioning_sentiment", ("positioning", "sentiment"))
        legacy("options_gamma", ("options", "gamma", "priced", "mechanism", "positioning"), _OPTIONS)
        legacy("priced_in", ("priced",))
        legacy("technical", ("acceptance", "confirmations", "mechanism", "zone_reason"), _STRUCTURE)
    # A five-layer plan gets all five. Keep the extra legacy priced-in line
    # where it adds depth without displacing an explicitly used layer.
    if sum(bool(sources[key]) for key in sources if key != "priced_in") == 5:
        sources["priced_in"] = []
    return {key: options for key, options in sources.items() if options}


def validate_analysis_line(options, layer, text):
    if not isinstance(text, str) or not any(text == item["text"] for item in options.get(layer, ())):
        raise ValueError("CC688_LAYER_NOT_QUOTED_FROM_PLAN:" + str(layer))


def _public_plan_quote(span, plan):
    """Translate only source notation whose meaning the code can verify."""
    from .plan_analysis_pages_v1 import check_reader_claim, public_filter
    from .plan_scenario_lines_v1 import BARE_UTC, INTERNAL_CAPS, ISO_TIME

    # Check before removing notation so a rewrite cannot hide a restricted input.
    public_filter(span)
    check_reader_claim(span, source=span)
    converted_clocks = []

    def instant(match):
        value = et(match[0])
        converted_clocks.append(value)
        return value

    text = ISO_TIME.sub(lambda match: instant(match) if match[0].endswith(("Z", "+00:00")) else match[0], span)

    def utc_clock(match):
        hour, minute = map(int, match[1].split(":"))
        dates = set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", span))
        if not dates:
            fields = [plan.get(key) for key in _PLAN_CLOCK_FIELDS]
            fields.extend(value.get("horizon_end_utc") for key in ("scenario_analysis", "forecast_probabilities")
                          if isinstance(value := plan.get(key), dict))
            for field in fields:
                if not isinstance(field, str):
                    continue
                try:
                    clock = datetime.fromisoformat(field.replace("Z", "+00:00"))
                except ValueError:
                    continue
                if clock.tzinfo is None:
                    continue
                clock = clock.astimezone(timezone.utc)
                if (clock.hour, clock.minute) == (hour, minute):
                    dates.add(clock.date().isoformat())
        if len(dates) != 1:
            raise ValueError("LAYER_CLOCK_DATE_UNAVAILABLE")
        value = et(f"{dates.pop()}T{hour:02d}:{minute:02d}:00Z")
        converted_clocks.append(value)
        return value

    text = re.sub(r"(?<![\d:\-–])\b(\d{1,2}:\d{2})(?:Z|\s+UTC)\b", utc_clock, text)
    text = re.sub(r"\bchannel(?:\s*[:=]\s*|\s+)(MIXED|CLEAR)\b",
                  lambda match: "signals are " + match[1].lower(), text, flags=re.I)
    text = re.sub(r"\bjim_weekly_minimum_\d+\s+starter\b", "initial entry", text, flags=re.I)
    text = re.sub(r"^CC-\d+\s*[:–-]\s*|\s*\((?:see\s+)?CC-\d+\)|"
                  r"\s+(?:per|under|see)\s+CC-\d+\b", "", text, flags=re.I)
    text = re.sub(r"^(long|short) positions\b", r"\1s", text, flags=re.I)
    text = text.strip()
    text = text[0].upper() + text[1:] if text else text
    if not text or BARE_UTC.search(text) or INTERNAL_CAPS.search(text) or _PLAN_INTERNAL_REF.search(text):
        raise ValueError("LAYER_INTERNAL_TOKEN_HAS_NO_PUBLIC_EQUIVALENT")
    check_text(text, source="\n".join([span, *converted_clocks]), prose=False)
    check_thread_text(text, force=True)
    check_publication_copy({"body": text}, require_notice=False)
    return text


def _scenario_probability(branch):
    value = branch.get("probability_pct")
    return value if type(value) in (int, float) and 0 <= value <= 100 else None


def _exported_scenarios(plan):
    scenario = plan.get("scenario_analysis")
    return scenario if isinstance(scenario, dict) else {}


def plan_layer_candidates(plan):
    """Read the CC-717 ordered export, its CC-687 bridge and earlier rationale fields."""
    sources = {layer: [] for layer, _ in PLAN_LAYER_ORDER}
    causes = dict.fromkeys(sources, "EXPORT_FIELD_ABSENT")
    explicit = set()

    def add(layer, value, *, pattern=None, status=None):
        if not isinstance(value, str) or not value.strip():
            return
        for quote in verbatim_analysis_spans(value):
            if pattern and not pattern.search(quote):
                continue
            if status != "used" and _UNAVAILABLE_LAYER.search(quote):
                causes[layer] = "ANALYST_REPORTED_UNAVAILABLE"
                continue
            try:
                text = _public_plan_quote(quote, plan)
            except ValueError as exc:
                causes[layer] = str(exc).split(":", 1)[0]
                continue
            if all(candidate["text"] != text for candidate in sources[layer]):
                sources[layer].append({"quote": quote, "text": text})

    for field in ("layers", "analysis_layers"):
        block = plan.get(field)
        if isinstance(block, list):
            entries = ((row.get("layer"), row) for row in block if isinstance(row, dict))
        elif isinstance(block, dict):
            entries = block.items()
        else:
            continue
        for name, row in entries:
            if not isinstance(name, str):
                continue
            name = name.lower().replace("-", "_").replace(" ", "_")
            layer = _LAYER_ALIASES.get(name, name)
            if layer not in sources or layer in explicit:
                continue
            explicit.add(layer)
            if isinstance(row, dict):
                state = str(row.get("state") or row.get("status") or "").lower()
                if row.get("used") is False or row.get("available") is False or state in _UNAVAILABLE_LAYER_STATES:
                    cause = row.get("first_cause")
                    causes[layer] = str(cause) if cause else "ANALYST_REPORTED_UNAVAILABLE"
                    continue
                add(layer, row.get("text", row.get("line")), status=state)
            else:
                add(layer, row)

    scenario = _exported_scenarios(plan)
    legacy = (
        ("macro", ("driver",), None),
        ("event_and_cause", ("event_and_cause",), None),
        ("fundamental", ("fundamental", "fundamentals", "mechanism", "driver", "positioning"), _FUNDAMENTAL),
        ("priced_in", ("priced", "priced_in"), None),
        ("positioning_sentiment", ("positioning", "sentiment"), None),
        ("options_gamma", ("options", "gamma", "priced", "mechanism", "positioning"), _OPTIONS),
        ("cross_asset_and_contagion", ("cross_asset_and_contagion",), None),
        ("technical", ("acceptance", "confirmations", "mechanism", "zone_reason"), _STRUCTURE),
    )
    for layer, fields, pattern in legacy:
        if layer not in explicit:
            for field in fields:
                add(layer, scenario.get(field), pattern=pattern)
    if "event_and_cause" not in explicit and not sources["event_and_cause"]:
        add("event_and_cause", scenario.get("mechanism"), pattern=_EVENT_CAUSE)

    for case, _ in _SCENARIO_CASES:
        sources[case] = []
        branch = scenario.get(case)
        if not isinstance(branch, dict):
            continue
        add(case, branch.get("market_move"))
        if _scenario_probability(branch) is not None and not sources[case]:
            # The probability itself is useful even if the case has no quotable prose.
            sources[case].append({"quote": "", "text": ""})
    if any(sources[case] for case, _ in _SCENARIO_CASES):
        causes.pop("scenarios")
    elif not sources["scenarios"]:
        causes["scenarios"] = next((causes[case] for case, _ in _SCENARIO_CASES if case in causes),
                                   causes["scenarios"])
    return ({key: options for key, options in sources.items() if options},
            {key: causes[key] for key, _ in PLAN_LAYER_ORDER if key in causes and not sources.get(key)})


def verified_analysis_lines(plan, quotes, *, contract=ANALYSIS_COPY):
    options = plan_layer_candidates(plan)[0] if contract == NINE_LAYER_COPY else analysis_layer_options(plan)
    if not isinstance(quotes, dict) or set(quotes) != set(options):
        raise ValueError("CC688_LAYER_SET_CHANGED")
    for layer, text in quotes.items():
        validate_analysis_line(options, layer, text)
    order = PLAN_LAYER_ORDER if contract == NINE_LAYER_COPY else ANALYSIS_LAYERS
    lines = [f"{label}: {quotes[layer]}" for layer, label in order if layer in quotes and layer != "scenarios"]
    cases = [quotes["scenarios"]] if "scenarios" in quotes else []
    for key, label in _SCENARIO_CASES:
        if key not in quotes:
            continue
        probability = _scenario_probability(plan["scenario_analysis"][key])
        if probability is not None:
            label += f" ({probability:g}%)"
        cases.append(f"{label}: {quotes[key]}" if quotes[key] else label + ".")
    if cases:
        lines.append("Scenarios: " + " ".join(cases))
    return lines


def analysis_scenario_lines(plan):
    from .plan_analysis_pages_v1 import check_reader_claim

    scenario = plan.get("scenario_analysis") or {}
    lines = []
    for key, label in (("base_case", "Main"), ("main_alternative", "Alternative")):
        branch = scenario.get(key) or {}
        probability = branch.get("probability_pct")
        if isinstance(probability, bool) or not isinstance(probability, (int, float)) or not 0 <= probability <= 100:
            continue
        summary = branch.get("market_move", "")
        try:
            if (not isinstance(summary, str) or not summary.strip()
                    or re.search(r"\b(?:bullish|bearish)\b", summary, re.I)):
                raise ValueError("SCENARIO_PROSE_NOT_PUBLIC")
            check_text(summary, source=summary, max_chars=175, prose=False)
            check_reader_claim(summary, source=summary)
            check_publication_copy({"body": summary}, require_notice=False)
        except ValueError:
            summary = ""
        odds = f"{label} scenario ({probability:g}%)"
        lines.append((odds + ": " + summary.strip()).rstrip(".") + "." if summary else odds + ".")
    return lines


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
        terms = page_thread_terms(plan, run, level_contract=level_contract)
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


def payloads(row, card_id, *, chart_credit=False, parents=None, portrait_id=None, destinations=None):
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
        facts = re.split(r"(?<=\.)\s+(?=[A-Z])", call_line)
        # The analysis thread's second reply is reserved for the market forces.
        own_thread = row.get("x_analysis_thread")
        if not own_thread:
            facts = [*points[:3], *facts]
        if chart_credit:
            facts.append(posts.CHART_CREDIT)
        continuations, current = (["\n".join(points[:3])] if own_thread and points else []), ""
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
    destinations = destinations or ("telegram", "discord", "threads", "facebook_page", "instagram_business", "x", "substack_notes")
    if "x" in destinations and any(posts._x_length(part) > 280 for part in x_parts):
        raise ValueError("CC466_X_FIELD_SET_TOO_LONG_REWRITE_REQUIRED")
    threads_root = "\n\n".join([root, "Full analysis: " + url, NOTICES])
    thread_parts = [threads_root, reasons + credit]
    if "threads" in destinations and any(len(part) > 500 for part in thread_parts):
        raise ValueError("CC466_THREADS_FIELD_SET_TOO_LONG_REWRITE_REQUIRED")
    result = {}
    for destination in destinations:
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
