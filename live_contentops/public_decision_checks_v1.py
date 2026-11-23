"""CC-690 decision checks over the evening readback's point-in-time evidence."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import parse_qs, urlsplit

from .preview_link_guard_v1 import REASON as PREVIEW_LINK_REASON, find_forbidden_link
from .public_time_v1 import PUBLIC_ZONE, find_forbidden_public_time
from .tradingview_snapshot_v1 import SYMBOLS
from .x_reply_trading_dates_v1 import trading_date


WRAP_ROUTES = ("substack", "substack_notes", "telegram", "discord", "facebook_page",
               "instagram_business", "threads", "linkedin", "linkedin_company", "x")
DECISIONS = ("98", "113", "82", "CC-672", "CC-685", "CC-684", "90", "109", "136", "CC-584", "83", "CC-732",
             "157", "158", "CC-729", "CC-768")
# Statuses that never count as a failure or an unverified check. BEFORE_POLICY: the copy was frozen before
# the decision it breaks took effect. EXPECTED: a named, deliberate non-send (Jim posts that route by hand,
# or a later plan state replaced the copy). PAUSED: Jim's posting pause held it.
NOT_COUNTED = ("FLAGGED", "BEFORE_POLICY", "EXPECTED", "PAUSED")
# Jim, 23 Nov 03:04 GMT+7: X, Substack Notes and the LinkedIn company page are his by hand, suspended in
# suspended_routes.json from 22 Nov 20:31Z (23 Nov 03:31 GMT+7; BACKLOG CC-731 and CC-748 lines).
HAND_POSTING_FROM = {"JIM_POSTS_BY_HAND_20261123": datetime(2026, 11, 22, 20, 31, tzinfo=timezone.utc)}
# Telegram, Facebook, Instagram and Threads serve a re-encoded, downscaled JPEG of the upload. On 23 Nov the
# public Telegram 229 image (sha 6abae0f1..., 800x450) was the exact chart uploaded (1600x900), yet the pixel
# rule read rms 7.8 / worst tile 19.9 and recorded MISMATCH. Exact or pixel MATCH still passes on these routes.
RECOMPRESSED_IMAGE_ROUTES = frozenset({"telegram", "facebook_page", "instagram_business", "threads"})
PAUSE_RECORD_GLOB = "control/pause-*/manifest.json"
ABSENCE_CAUSES = frozenset({
    "WRAP_PLATFORM_MISSING", "WRAP_PUBLISHED_LATE", "WRAP_PUBLICATION_TIME_UNVERIFIED",
    "PLAN_COPY_UNCONFIRMED", "PLAN_COPY_OVER_TEN_MINUTES_LATE", "BROKER_PLAN_FIRST_POST_MISSING",
    "LINKEDIN_ACCOUNT_COPY_MISSING", "DISCORD_FILL_OR_RESULT_CHANNEL_COPY_MISSING",
})
_MONTH_DATE = re.compile(r"\b\d{1,2}(?:\s*[-–]\s*\d{1,2})?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b")
PLAN_DELIVERY_LIMIT = timedelta(minutes=10)
PLAN_FILL_STATES = {"TRIGGERED", "FILLED"}
PLAN_POST_KINDS = {"setup", "update", "result"}
LATE_LINE = "this page was published after the plan ended"
LAYER_PREFIX = re.compile(
    r"\b(macro|fundamentals?|positioning and sentiment|positioning|sentiment|options and gamma|"
    r"options|gamma|gex|priced in|technical|structure|geopolitics|geopolitical|scenarios?)\s*:\s*", re.I)
LAYER_ALIAS = {
    "fundamentals": "fundamental", "positioning and sentiment": "positioning", "sentiment": "positioning",
    "positioning sentiment": "positioning",
    "gamma": "options", "gex": "options", "options and gamma": "options", "options gamma": "options",
    "structure": "technical",
    "geopolitical": "geopolitics", "scenarios": "scenario",
}
PLAN_LAYERS = {
    "macro": ("macro",),
    "event_cause": ("event and cause", "event cause", "event driven causal analysis", "geopolitics", "geopolitical"),
    "fundamental": ("fundamentals", "fundamental"),
    "priced_in": ("priced in",),
    "positioning_sentiment": ("positioning and sentiment", "positioning sentiment", "positioning", "sentiment"),
    "options_gamma": ("options and gamma", "options gamma", "options", "gamma", "gex"),
    "cross_asset_contagion": ("cross asset and contagion", "cross asset contagion", "contagion cross asset",
                              "cross asset", "contagion"),
    "technical": ("technical", "structure"),
    "scenarios": ("scenarios", "scenario"),
}
PLAN_LAYER_NAMES = {name: key for key, names in PLAN_LAYERS.items() for name in names}
PLAN_LAYER_LABEL = re.compile(r"\b(" + "|".join(map(re.escape,
    sorted(PLAN_LAYER_NAMES, key=len, reverse=True))) + r")\s*:\s*")
SCENARIO_ODDS = re.compile(r"\b(main|base|alternative)(?:\s+(?:case|scenario))?\s*\((\d+(?:\.\d+)?)\s*%\)")
LAYER_CAUSE = re.compile(r"[A-Z][A-Z0-9_]{1,79}\Z")
LEGACY_PLAN_LAYERS = {
    "macro": ("driver",), "event_cause": ("mechanism",), "fundamental": ("fundamental", "fundamentals"),
    "priced_in": ("priced",), "positioning_sentiment": ("positioning", "sentiment"),
    "options_gamma": ("options", "gamma"), "cross_asset_contagion": ("cross_asset_contagion",),
    "technical": ("zone_reason", "acceptance", "confirmations"),
}
AI_LABEL = re.compile(
    r"\b(?:AI|artificial intelligence)[ -]+(?:generated|written|powered|assisted|"
    r"produced|run|agent|disclosure|label)\b|\b(?:generated|written|made) (?:with|by) (?:an? )?AI\b|"
    r"\b(?:ChatGPT|GPT[- ]?\d[\w.-]*|gpt-[\w.-]+|Gemini(?:[ -][\w.-]+)?|"
    r"Claude(?:[ -](?:Opus|Sonnet|Haiku)[\w .-]*)?|grok[- ]?\d[\w.-]*|"
    r"DeepSeek[-\w]*|Antigravity|Codex|OpenAI)\b", re.I)
PUBLIC_CLOCK = re.compile(
    r"\b(?:[01]?\d|2[0-3]):[0-5]\d(?:\:[0-5]\d)?\s*(?:[ap]\.?m\.?\s*)?"
    r"(?:UTC|GMT|EST|EDT|PST|PDT|CST|CDT|MST|MDT|CET|CEST|BST|JST|HKT|ICT|Z)\b", re.I)
DAILY_WRAP = re.compile(
    r"\b(?:(?:pre[- ]?(?:US|open)|daily|six[- ]market|US (?:cash )?open) "
    r"(?:market )?(?:wrap|recap)|market wrap|market recap)\b", re.I)
WEEKEND_WRAP = re.compile(
    r"\b(?:weekend|weekly|week ahead|week in review)\b.{0,46}\b(?:wrap|recap|review|preview)\b"
    r"|\b(?:wrap|recap|review)\b.{0,30}\b(?:weekend|weekly)\b", re.I)


# Look for the plan's target as a price, or an explicit target-level field.
# A macro policy target and a qualitative result are both legitimate copy.
_COPY_LINK = re.compile(r"https?://[^\s<>]+", re.I)
_PRICE = r"(?:USD\s*)?[$€£]?\s*[+-]?\d+(?:,\d{3})*(?:\.\d+)?"
_TARGET_LABEL = re.compile(
    r"^\s*(?:[-*•>#]+\s*)?(?:model\s+)?target\s+level\b|\btarget\s+level\s*[:=]", re.I | re.M)
_TARGET_PRICE = re.compile(
    rf"\b(?:(?:profit|price|model)[ -]+)?(?:targets?|take[ -]+profits?|TP\d*)\b"
    rf"(?:\s+(?:level|price|zone))?\s*(?:[:=@]|\b(?:is\s+)?(?:at|of|near|around|above|below)\b|\bis\b)?"
    rf"\s*(?:[<>]=?\s*)?{_PRICE}(?!\d|[.,:]\d)", re.I)
_TARGET_BEFORE_LABEL = re.compile(
    rf"{_PRICE}\s+(?:(?:(?:profit|price|model)[ -]+)?target|take[ -]+profit)\b", re.I)
_POLICY_TARGET = re.compile(
    r"\b(?:inflation|employment|unemployment|deficit|fed funds|policy rate|interest rate|yield"
    r"|(?:fed|ecb|boj|boe|central bank)'s)"
    r"(?:\s+rate)?\s+$", re.I)
# "Net long", "net short", "short covering" and "short interest" report positioning data, not the desk's call.
_POSITION_WORD = re.compile(
    r"(?<!net )(?<!net-)\b(?:long|short|buy|sell)\b(?![ -](?:term|covering|squeeze|interest)\b)", re.I)
_SCENARIO_FORCES = tuple(re.compile(pattern, re.I) for pattern in (
    r"\bmacro(?:economic)?\b", r"\bfundamentals?\b", r"\b(?:sentiment|positioning)\b",
    r"\b(?:priced[ -]in|priced\s+into|pricing\s+in)\b",
))
_ENTRY_LEVEL = re.compile(
    rf"\b(?:(?:buy|entry|sell|accumulation)[ -]+(?:zone|range|band|area)(?:\s+is)?\s*[:=]?\s*"
    rf"(?:between\s+|around\s+|near\s+|at\s+)?|(?:bullish|bearish)\s+(?:(?:at|around|below|above)\s+)?|"
    rf"(?:trades?|returns?|moves?|holds?|breaks?)\s+(?:into|between|above|below|through)\s+){_PRICE}"
    rf"|{_PRICE}(?:\s*[-–—]\s*{_PRICE})?\s+(?:entry|buy\s+zone)\b", re.I)
# The plan's own cancel line ("Cancel if spot price trades at or above 3,609 before entry", "plan cancelled
# on high at or above 68,450") is its invalidation level.
_INVALIDATION_LEVEL = re.compile(
    rf"\b(?:invalidation(?:\s+level)?|(?:plan\s+)?wrong|invalid(?:ated)?|"
    rf"(?:cancel|stop)[ -](?:level|loss))\s*[:=]?\s*"
    rf"(?:if\s+)?(?:the\s+)?(?:price\s+(?:moves?\s+)?)?(?:(?:is|at|above|below|under|over)\s+)?"
    rf"{_PRICE}|{_PRICE}\s+invalidation\b"
    rf"|\bcancel(?:led|s)?\b[^.\n]{{0,60}}?\b(?:above|below|under|over)\s+{_PRICE}", re.I)
SCENARIO_REVIEW_RULES = (
    "SCENARIO_CASES_MISSING", "POSITION_WORDS_REPEATED", "SCENARIO_FORCES_TOO_FEW",
    "ENTRY_ZONE_MISSING", "INVALIDATION_LEVEL_MISSING",
)


def _plan_copy_text(text):
    return _COPY_LINK.sub("", re.sub(r"\*\*|__|\x60", "", unicodedata.normalize("NFKC", text).replace("’", "'")))


def plan_target_present(text):
    plain = _plan_copy_text(text)
    return bool(_TARGET_LABEL.search(plain) or _TARGET_BEFORE_LABEL.search(plain) or any(
        not _POLICY_TARGET.search(plain[:match.start()])
        for match in _TARGET_PRICE.finditer(plain)
    ))


def plan_scenario_flags(text):
    plain = _plan_copy_text(text)
    checks = (
        re.search(r"\bbase\s+case\b", plain, re.I) and re.search(r"\b(?:bull|bear)\s+case\b", plain, re.I),
        len(_POSITION_WORD.findall(plain)) <= 1,
        sum(bool(force.search(plain)) for force in _SCENARIO_FORCES) >= 2,
        _ENTRY_LEVEL.search(plain),
        _INVALIDATION_LEVEL.search(plain),
    )
    return tuple(rule for rule, passed in zip(SCENARIO_REVIEW_RULES, checks) if not passed)


def notice_counts(text):
    """How often one public copy prints decision 40's analysis notice and its conflicts notice (CC-729)."""
    from .event_article_guard_v1 import CONFLICTS_NOTICE, PUBLIC_NOTICE

    body = normalized(text or "")
    return {"analysis_notice": body.count(normalized(PUBLIC_NOTICE)),
            "conflicts_notice": body.count(normalized(CONFLICTS_NOTICE))}


def pause_windows(runtime):
    """Jim's posting pauses as (start, end or None, cause), read from the pause records under the runtime.

    The pause starts when the routes were suspended (manifest paused_at_utc) and ends when the restore wrote
    restored.json (its started_at_utc). No restored.json means the pause still holds.
    """
    windows = []
    for path in sorted(Path(runtime).glob(PAUSE_RECORD_GLOB)):
        record = object_json(path)
        start = clock(record.get("paused_at_utc"))
        cause = record.get("cause")
        if not start or not (isinstance(cause, str) and LAYER_CAUSE.fullmatch(cause)):
            continue
        end = None
        if path.with_name("restored.json").exists():
            restored = object_json(path.with_name("restored.json"))
            # An unreadable restore record falls back to the planned resume time.
            end = (clock(restored.get("started_at_utc")) or clock(restored.get("ended_at_utc"))
                   or clock(record.get("resume_at_utc")))
        windows.append((start, end, cause))
    return windows


def clock(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except ValueError:
        return None


def object_json(path):
    try:
        value = json.loads(Path(path).read_bytes())
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def normalized(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(text.translate(str.maketrans("‘’“”–—", "''\"\"--")).split())


def wrap_kind(title, kind):
    if kind in {"WEEKEND_WRAP", "WEEKLY_WRAP", "WEEKLY_REVIEW"} or WEEKEND_WRAP.search(title):
        return "weekend"
    if kind in {"PRE_US_WRAP", "DAILY_WRAP", "MARKET_WRAP", "CPI_PPI_PREVIEW"} or DAILY_WRAP.search(title):
        return "daily"
    return None


def public_link(value):
    try:
        parsed = urlsplit(value)
        if (parsed.scheme == "https" and (parsed.hostname or "").endswith(".substack.com")
                and parsed.path.startswith("/p/") and not parsed.username and not parsed.password):
            return parsed.hostname, parsed.path.rstrip("/")
    except (TypeError, ValueError):
        pass
    return None


def contains_link(text, url, links=()):
    target = public_link(url)
    if not target:
        return False
    candidates = (*links, *re.findall(r"https://[^\s<>\"\])]+", text))
    return any(public_link(candidate.rstrip(".,;")) == target for candidate in candidates)


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for part in value.values():
            yield from _strings(part)
    elif isinstance(value, list):
        for part in value:
            yield from _strings(part)


def quoted_layer_count(text, source):
    body = normalized(re.sub(r"(?:\*\*|__)", "", text))
    raw = tuple(normalized(part) for part in _strings(source) if len(part.strip()) > 18)
    # Use the publisher's source selector as soon as CC-688 is integrated. Its
    # validation admits only the exact same frozen quotes as the writer.
    from . import plan_reader_copy_v1 as reader

    selector = getattr(reader, "analysis_layer_options", None)
    options = selector(source) if selector and source.get("asset_id") else {}
    allowed = defaultdict(set)
    for key, entries in options.items():
        layer = LAYER_ALIAS.get(key.replace("_", " "), key.replace("_", " "))
        allowed[layer].update(normalized(entry["text"]).rstrip(".!?") for entry in entries)
    matches = list(LAYER_PREFIX.finditer(body))
    counted, quotes = set(), set()
    for index, match in enumerate(matches):
        layer = LAYER_ALIAS.get(match[1], match[1])
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        clause = body[match.end():end]
        if allowed:
            candidates = sorted(allowed[layer], key=lambda item: (-len(item), item))
            quote = next((q for q in candidates if clause == q or clause.startswith(q + ".")
                          or clause.startswith(q + " ") or clause.startswith(q + "!")
                          or clause.startswith(q + "?")), "")
        else:
            quote = re.split(r"(?<=[.!?])\s+", clause, maxsplit=1)[0].rstrip(" .!?")
            if len(quote.split()) < 4 or not any(quote in part for part in raw):
                continue
        if quote and quote not in quotes:
            quotes.add(quote)
            counted.add(layer)
    return len(counted)


def _layer_name(name):
    return PLAN_LAYER_NAMES.get(re.sub(r"[_-]+", " ", normalized(str(name))))


def _layer_entries(record):
    if isinstance(record, dict):
        entries = record.items()
    elif isinstance(record, list):
        entries = ((item.get("layer"), item) for item in record if isinstance(item, dict))
    else:
        return {}
    return {key: value for name, value in entries if (key := _layer_name(name))}


def _safe_cause(value):
    return value if isinstance(value, str) and LAYER_CAUSE.fullmatch(value) else None


def _layer_text(text):
    return re.sub(r"(?<=[a-z])-(?=[a-z])", " ", normalized(re.sub(r"\*\*|__|\x60", "", text)))


def _quoted(clause, candidates):
    for raw in candidates:
        if not isinstance(raw, str):
            continue
        for line in re.split(r"(?<=[.!?])\s+|[;\n]", raw):
            quote = _layer_text(line).strip(" ,;:.!?")
            if quote and re.match(re.escape(quote) + r"(?=\s*$|[.!?](?:\s|$))", clause):
                return True
    return False


def _scenario_odds(scenario, text):
    expected = {}
    for key, label in (("base_case", "main"), ("main_alternative", "alternative")):
        branch = scenario.get(key) or {}
        value = branch.get("probability_pct")
        if type(value) in (float, int) and 0 <= value <= 100:
            expected[label] = value
    actual = defaultdict(set)
    for label, value in SCENARIO_ODDS.findall(text):
        actual["main" if label == "base" else label].add(float(value))
    return bool(expected and actual == {label: {value} for label, value in expected.items()})


def plan_layer_checks(text, plan, missing):
    body = _layer_text(text)
    labels = list(PLAN_LAYER_LABEL.finditer(body))
    clauses = defaultdict(list)
    for index, label in enumerate(labels):
        end = labels[index + 1].start() if index + 1 < len(labels) else len(body)
        clauses[PLAN_LAYER_NAMES[label[1]]].append(body[label.end():end])

    exported = _layer_entries(plan.get("analysis_layers"))
    exported.update(_layer_entries(plan.get("layers")))
    scenario = plan.get("scenario_analysis") or {}
    result = {}
    for key in PLAN_LAYERS:
        entry = exported.get(key)
        if isinstance(entry, dict):
            state = str(entry.get("state") or entry.get("status") or "").upper()
            unavailable = state in {"UNAVAILABLE", "MISSING", "STALE", "NOT_USED", "NOT_AVAILABLE"} or (
                entry.get("used") is False or entry.get("available") is False)
            if unavailable:
                cause = _safe_cause(entry.get("first_cause") or entry.get("cause") or missing.get(key))
                if clauses[key]:
                    result[key] = {"state": "MISSING", "cause": "LAYER_TEXT_NOT_BOUND_TO_EXPORT"}
                elif cause:
                    result[key] = {"state": "UNAVAILABLE", "cause": cause}
                else:
                    result[key] = {"state": "MISSING", "cause": "EXPORT_GAP_WITHOUT_CAUSE"}
                continue
            entry = entry.get("text") or entry.get("line")
        legacy = [scenario.get(field) for field in LEGACY_PLAN_LAYERS.get(key, ())]
        candidates = [entry] if entry else [*(plan.get(name.replace(" ", "_")) for name in PLAN_LAYERS[key]), *legacy]
        sourced = any(isinstance(line, str) and line.strip() for line in candidates)
        if key == "scenarios":
            # A prose line cannot substitute for the odds that the frozen plan holds.
            odds_present = any((scenario.get(branch) or {}).get("probability_pct") is not None
                               for branch in ("base_case", "main_alternative"))
            printed = _scenario_odds(scenario, body) if odds_present else any(
                _quoted(clause, candidates) for clause in clauses[key])
            sourced = sourced or odds_present
        else:
            printed = any(_quoted(clause, candidates) for clause in clauses[key])
        if printed:
            result[key] = {"state": "PRINTED"}
        elif not sourced and not clauses[key] and (cause := _safe_cause(missing.get(key))):
            result[key] = {"state": "UNAVAILABLE", "cause": cause}
        else:
            result[key] = {"state": "MISSING", "cause": "EXPORTED_LAYER_NOT_PRINTED" if sourced else (
                "LAYER_TEXT_NOT_BOUND_TO_EXPORT" if clauses[key] else "EXPORT_GAP_NOT_RECORDED")}
    return result


def _observations(history, row, end):
    """Only dated observations of this dispatch can establish publication."""
    verified_at = published_at = None
    proof = {}
    for read_at, record in history:
        seen = clock(read_at)
        if not seen or seen > end:
            continue
        current = record.get("readback", record)
        if (current.get("verified") is not True or current.get("write_absent") is True
                or current.get("identity_match") is False
                or current.get("observed_public_object_id") not in (None, row.get("public_object_id"))):
            continue
        proof = {**proof, **current}
        verified_at = min(verified_at, seen) if verified_at else seen
        seen_at = clock(current.get("observed_published_at_utc"))
        if seen_at and seen_at <= seen:
            published_at = min(published_at, seen_at) if published_at else seen_at
    return proof, verified_at, published_at


def _media_symbol(asset):
    snapshot = asset.get("tradingview_snapshot") or {}
    if snapshot.get("tv_symbol"):
        return snapshot["tv_symbol"]
    provenance = asset.get("source_provenance") or {}
    url = provenance.get("source_page_url") or snapshot.get("chart_url")
    if url:
        try:
            parsed = urlsplit(url)
            if parsed.hostname in {"tradingview.com", "www.tradingview.com"}:
                return next(iter(parse_qs(parsed.query).get("symbol", [])), None)
        except ValueError:
            return None
    return None


@dataclass
class PublicCopy:
    piece: str
    platform: str
    url: str | None
    title: str
    text: str
    intent: dict
    row: dict
    history: list
    source: dict
    end: datetime
    public_text: str | None = None
    public_links: tuple = ()
    image_visible: bool | None = None
    public_http_status: int | None = None
    manual_posted: bool = False
    proof: dict = field(init=False)
    verified_at: datetime | None = field(init=False)
    published_at: datetime | None = field(init=False)
    dispatched_at: datetime | None = field(init=False)

    def __post_init__(self):
        self.proof, self.verified_at, self.published_at = _observations(self.history, self.row, self.end)
        dispatched = clock(self.row.get("dispatched_at"))
        self.dispatched_at = dispatched if dispatched and dispatched <= self.end else None

    @property
    def confirmed(self):
        has_identity = self.url or (self.source.get("kind") in PLAN_POST_KINDS
                                    and self.row.get("public_object_id"))
        return bool(has_identity and (self.verified_at or (
            self.dispatched_at and self.row.get("status") == "DISPATCH_CONFIRMED")))

    @property
    def native(self):
        return self.intent.get("native_payload") or {}

    @property
    def visible_text(self):
        if self.public_text is not None:
            return self.public_text
        observed = self.proof.get("observed_public_text", self.proof.get("observed_text",
                                  self.proof.get("visible_body_text")))
        return observed if isinstance(observed, str) else self.text

    @property
    def evidence(self):
        return "public_http" if self.public_text is not None else (
            "manual_desk_mark" if self.manual_posted else
            "stored_readback" if self.verified_at else "confirmed_dispatch")

    @property
    def observed_image(self):
        delivery = self.proof.get("image_delivery")
        if delivery in {"TEXT_ONLY", "TEXT_FALLBACK", "IMAGE_ATTACHED"}:
            observed = delivery == "IMAGE_ATTACHED"
        else:
            observed = self.proof.get("meaningful_media_visible", self.proof.get("image_visible"))
        if self.image_visible is False or observed is False:
            return False
        return self.image_visible if self.image_visible is not None else observed

    def verified_thread(self):
        if self.verified_at and (self.proof.get("content_binding_checks") or {}).get("thread_match") is True:
            return self.proof.get("observed_thread") or self.proof.get("thread_posts") or []
        return []

    def root_text(self):
        if self.public_text is not None:
            return self.public_text
        thread = self.verified_thread()
        if root := next((post for post in thread if post.get("public_object_url") == self.url), None):
            return str(root.get("observed_text") or "")
        observed = self.proof.get("observed_public_text", self.proof.get("observed_text",
                                  self.proof.get("visible_body_text")))
        if not thread and isinstance(observed, str):
            return observed
        if (self.proof.get("content_binding_checks") or {}).get("text_match") is False:
            return ""
        return self.native.get("root_text") or self.native.get("text") or self.text

    def resolved_links(self, thread, *, include_root=True):
        urls = {post.get("public_object_url") for post in thread} - {None}
        if include_root and self.url:
            urls.add(self.url)
        return [link["target_url"] for link in self.proof.get("observed_link_resolutions") or []
                if link.get("target_url") and link.get("target_verified") is True and link.get("public_object_url") in urls]

    def has_link(self, canonical, replies=()):
        if contains_link(self.root_text(), canonical, self.public_links):
            return True
        if self.public_text is None and contains_link("", canonical, self.resolved_links([])):
            return True
        first = next(iter(self.thread_replies()), None)
        if first:
            links = self.resolved_links([first], include_root=False)
            return contains_link(str(first.get("observed_text") or ""), canonical, links)
        if parts := self.bound_reply_texts():
            return contains_link(parts[0], canonical)
        if not replies:
            return False
        first = replies[0]
        links = first.public_links if first.public_text is not None else (*first.public_links, *first.resolved_links([]))
        return contains_link(first.root_text(), canonical, links)

    def thread_replies(self):
        return [post for post in self.verified_thread() if post.get("role") != "root"
                and post.get("public_object_url") and post["public_object_url"] != self.url]

    def bound_reply_texts(self):
        # Some verified receipts retained the match flag, but no observed text.
        if self.verified_thread():
            return []
        matched = (self.proof.get("content_binding_checks") or {}).get("thread_match")
        if self.verified_at and matched is True:
            return self.native.get("reply_texts") or []
        # A Threads or X readback that verified only the root still sent the frozen replies in the same
        # confirmed dispatch (the Threads splitter's second notice and the X target reply live there).
        if matched is None and self.confirmed and self.row.get("status") == "DISPATCH_CONFIRMED":
            return [text for text in self.native.get("reply_texts") or [] if isinstance(text, str)]
        return []

    def reply_parent(self):
        expected = self.native.get("reply_to_id")
        observed = self.proof.get("observed_reply_parent_id")
        if (self.proof.get("content_binding_checks") or {}).get("reply_parent_match") is False:
            return None
        if observed is not None and expected is not None and str(observed) != str(expected):
            return None
        parent = observed if observed is not None else expected
        return str(parent) if parent is not None else None

    def media(self, runtime):
        ids = self.native.get("media_asset_ids")
        assets = self.intent.get("media_assets") or self.source.get("media_assets") or []
        folder = self.intent.get("output_dir")
        if folder:
            # Only the existing delivery artifact under this runtime is read.
            root = Path(folder).resolve()
            if root.is_relative_to(runtime):
                assets = [*assets, *object_json(root / "delivery_media_manifest_v1.json").get("assets", [])]
                if self.intent.get("plan_status_post") and ids:
                    context = object_json(root / "run_context_v1.json")
                    assets = [*assets, *((context.get("media") or {}).get("assets") or [])]
        if ids is not None:
            return [asset for asset in assets if (asset.get("media_asset_id") or asset.get("asset_id")) in ids]
        return [asset for asset in assets if asset.get("article_inclusion") is not False]


class DecisionChecks:
    def __init__(self, window, runtime):
        self.window = window
        self.start = clock(window["since_utc"])
        self.end = clock(window["until_utc"])
        self.runtime = Path(runtime).resolve()
        self.copies = []
        self.counts = Counter()
        self.layer_gaps = Counter()
        self.wraps_due = Counter()
        self.issues = []
        self.seen = set()
        self.plan_analysis = []
        self.chart_readbacks = []
        self.chart_replies = {}
        self.pauses = pause_windows(self.runtime)
        self.posted = []

    def paused_at(self, at):
        """The cause of Jim's posting pause holding at this moment, or None."""
        if at is None:
            return None
        return next((cause for start, end, cause in self.pauses if start <= at and (end is None or at < end)), None)

    def paused_through_window(self):
        """The pause cause when Jim's pause holds for the whole report window, or None."""
        return next((cause for start, end, cause in self.pauses
                     if start <= self.start and (end is None or end >= self.end)), None)

    def add(self, piece, platform, url, title, text, intent, row, history, source):
        copy = PublicCopy(piece, platform, url, title, text, intent, row, history, source, self.end)
        self.copies.append(copy)
        return copy

    def issue(self, decision, piece, platform, cause, *, url=None, evidence=None,
              status="FAIL", held_at=None, **details):
        key = (decision, piece, platform, cause, url, details.get("public_object_id"))
        if cause in ABSENCE_CAUSES and status in {"FAIL", "UNVERIFIED"} and (pause := self.paused_at(held_at)):
            # A copy due while Jim's pause held every route is the pause's result, not a delivery failure.
            status, details = "PAUSED", {**details, "pause_cause": pause, "due_at_utc": held_at.isoformat()}
        elif (cause in ABSENCE_CAUSES and status == "FAIL" and held_at and held_at <= self.start
              and (pause := self.paused_through_window())):
            # An older unresolved copy, already reported on the day it fell due. Its owners are stopped for
            # the whole window, so it cannot change today: carried over, not a new failure of a paused day.
            status, details = "PAUSED", {**details, "pause_cause": pause, "carried_over": True,
                                         "due_at_utc": held_at.isoformat()}
        if key not in self.seen:
            self.seen.add(key)
            self.issues.append({"decision": decision, "piece_id": piece, "platform": platform,
                                "first_cause": cause, "status": status, "public_url": url,
                                "evidence": evidence, **details})

    def check(self, decision, copy, cause=None, *, status="FAIL", **details):
        self.counts[decision] += 1
        if cause:
            self.issue(decision, copy.piece, copy.platform, cause, url=copy.url,
                       evidence=copy.evidence, status=status, **details)

    def plan_queue(self, events):
        from .plan_queue_clock_v1 import DECISION

        self.counts[DECISION] = len({event.get("source_transition_id") or event["key"] for event in events})
        for event in events:
            if event["alarm"]:
                self.issue(DECISION, event.get("source_transition_id") or event["key"], "internal",
                           event["first_cause"], evidence=event,
                           plan_id=event["plan_id"], state=event["state"], gap_seconds=event["gap_seconds"])

    def _wraps(self):
        by_kind = defaultdict(list)
        for copy in self.copies:
            features = copy.intent.get("editorial_features") or {}
            kind = wrap_kind(copy.title, features.get("reader_format") or copy.intent.get("reader_format"))
            if kind:
                by_kind[kind].append(copy)

        day = self.start.date()
        while day <= self.end.date():
            weekend = day.weekday() == 6
            deadline = datetime.combine(day, time(18) if weekend else time(13, 45), timezone.utc)
            if self.start < deadline <= self.end and (weekend or trading_date(day, {"EQUITIES"})):
                first_day = day - timedelta(days=int(weekend))
                kind = "weekend" if weekend else "daily"
                self.wraps_due[kind] += 1
                self._wrap_deadline(by_kind[kind], first_day, day, deadline)
            day += timedelta(days=1)

    def _wrap_deadline(self, copies, first_day, day, deadline):
        canonical = [(ts, copy) for copy in copies if copy.platform == "substack"
                     and (ts := copy.published_at or copy.dispatched_at or clock(copy.row.get("created_at")))
                     and first_day <= ts.astimezone(PUBLIC_ZONE).date() <= day]
        latest_fallback = datetime.max.replace(tzinfo=timezone.utc)
        timely = defaultdict(set)
        for copy in copies:
            if copy.confirmed and (copy.published_at or copy.verified_at or latest_fallback) <= deadline:
                timely[copy.piece].add(copy.platform)
        chosen = min(canonical, key=lambda item: ("substack" not in timely[item[1].piece],
                     -len(timely[item[1].piece]), not item[1].confirmed, item[0], item[1].piece), default=None)
        label = (("weekend-wrap-" if first_day != day else "pre-us-wrap-") + day.isoformat()
                 if chosen is None else chosen[1].piece)
        for platform in WRAP_ROUTES:
            self.counts["98"] += 1
            candidates = [copy for copy in copies if copy.piece == label and copy.platform == platform]
            confirmed = [copy for copy in candidates if copy.confirmed]
            if platform in timely[label]:
                continue
            picked = next(iter(confirmed or candidates), None)
            if confirmed:
                cause = "WRAP_PUBLISHED_LATE" if all(copy.published_at for copy in confirmed) else "WRAP_PUBLICATION_TIME_UNVERIFIED"
            else:
                cause = "WRAP_PLATFORM_MISSING"
            hand = self._hand_posted(platform, deadline)
            self.issue("98", label, platform, "WRAP_PLATFORM_HANDED_TO_JIM" if hand and not confirmed else cause,
                       url=picked.url if picked else None,
                       status="EXPECTED" if hand and not confirmed else
                       "UNVERIFIED" if cause.endswith("_UNVERIFIED") else "FAIL",
                       deadline_utc=deadline.isoformat(), held_at=deadline,
                       **({"hand_cause": hand} if hand else {}))

    def _hand_posted(self, platform, at):
        """Jim's hand-posting cause for this route at this moment, from the suspension he set (CC-731)."""
        routes = object_json(self.runtime / "control" / "suspended_routes.json")
        for path in sorted(self.runtime.glob("control/pause-*/suspended_routes_before.json")):
            # During a pause every route carries the pause cause; the hand routes are in the saved file.
            routes = {**object_json(path), **{key: value for key, value in routes.items()
                                              if value in HAND_POSTING_FROM}}
        cause = routes.get(platform)
        start = HAND_POSTING_FROM.get(cause)
        return cause if start and at and at >= start else None

    def _current_layers(self, copy, text):
        from .plan_reader_copy_v1 import PLAN_LAYER_ORDER
        from .plan_state_alerts_v1 import analysis_lines

        try:
            expected = analysis_lines(copy.source)
        except (KeyError, TypeError, ValueError):
            return {key: {"state": "MISSING", "cause": "PLAN_LAYER_RECORD_INVALID"}
                    for key, _ in PLAN_LAYER_ORDER}

        if copy.platform in {"linkedin", "linkedin_company"}:
            official = (copy.native.get("text") or "").splitlines()
            prefixes = tuple(label + ": " for _, label in PLAN_LAYER_ORDER)
            excerpts = [line for line in official if line.startswith(prefixes)]
            if [line.split(":", 1)[0] for line in excerpts] == [line.split(":", 1)[0] for line in expected]:
                # The frozen destination payload carries the reviewed excerpts for both accounts.
                expected = excerpts

        expected_by_label = {line.split(":", 1)[0]: _layer_text(line) for line in expected}
        body = _layer_text(text)
        gaps = copy.source.get("analysis_layer_gaps") or {}
        layers = {}
        for key, label in PLAN_LAYER_ORDER:
            line = expected_by_label.get(label)
            if line and re.search(r"(?<!\w)" + re.escape(line) + r"(?!\w)", body):
                layers[key] = {"state": "PRINTED"}
            elif line:
                layers[key] = {"state": "MISSING", "cause": "EXPORTED_LAYER_NOT_PRINTED"}
            elif re.search(r"(?<!\w)" + re.escape(_layer_text(label)) + r"\s*:", body):
                layers[key] = {"state": "MISSING", "cause": "LAYER_TEXT_NOT_BOUND_TO_EXPORT"}
            elif cause := _safe_cause(gaps.get(key)):
                layers[key] = {"state": "UNAVAILABLE", "cause": cause}
            else:
                layers[key] = {"state": "MISSING", "cause": "EXPORT_GAP_NOT_RECORDED"}
        return layers

    @staticmethod
    def _plan_copy_body(copy, continuations=()):
        return "\n".join(filter(None, (
            copy.root_text(),
            *(str(post.get("observed_text") or "") for post in copy.thread_replies()),
            *copy.bound_reply_texts(),
            *(item.root_text() for item in continuations),
        )))

    def review_manual_plan_copy(self, piece, platform, url, read_public, posted_at=None):
        # Jim's Posted mark is the copy's public clock (decision 157 binds from 22 Nov 22:30Z).
        row = {"dispatched_at": posted_at} if posted_at else {}
        copy = PublicCopy(piece, platform, url, "", "", {}, row, [], {}, self.end, manual_posted=True)
        read_public(platform, url, decision_copy=copy)
        text = copy.root_text()
        self._plan_target(copy, text)
        self._scenario_voice(copy, text)

    def _frozen_at(self, copy):
        """When the copy's text was frozen: its plan row's creation, else its own first public clock."""
        return (clock(copy.source.get("decision_source_created_at_utc"))
                or copy.published_at or copy.dispatched_at or clock(copy.row.get("created_at")))

    def _target_policy(self, copy):
        """Decision 157 binds rows marked DECISION_40_NO_TARGET and any copy frozen from 22 Nov 22:30Z."""
        from .plan_call_cards_v1 import NO_TARGET_EFFECTIVE, NO_TARGET_POLICY

        if copy.source.get("target_policy") == NO_TARGET_POLICY:
            return True
        frozen = self._frozen_at(copy)
        return bool(frozen and frozen >= NO_TARGET_EFFECTIVE) or (frozen is None and self.end >= NO_TARGET_EFFECTIVE
                                                                     and copy.manual_posted)

    def _plan_target(self, copy, text):
        details = {"public_object_id": copy.row.get("public_object_id")}
        if plan_target_present(text) and not self._target_policy(copy):
            # Frozen before Jim's "Keep targets off" took effect: listed, never a decision 157 failure.
            self.check("157", copy, "PUBLIC_PLAN_TARGET_PRESENT", status="BEFORE_POLICY", **details)
        elif plan_target_present(text):
            self.check("157", copy, "PUBLIC_PLAN_TARGET_PRESENT", **details)
        elif not text.strip():
            self.check("157", copy, "PLAN_COPY_TEXT_UNAVAILABLE", status="UNVERIFIED", **details)
        else:
            self.check("157", copy)

    def _scenario_voice(self, copy, text, *, rules=SCENARIO_REVIEW_RULES):
        details = {"public_object_id": copy.row.get("public_object_id")}
        if not text.strip():
            self.check("158", copy, "PLAN_COPY_TEXT_UNAVAILABLE", status="UNVERIFIED", **details)
            return
        self.check("158", copy)
        for flag in (flag for flag in plan_scenario_flags(text) if flag in rules):
            self.issue("158", copy.piece, copy.platform, flag, url=copy.url,
                       evidence=copy.evidence, status="FLAGGED", **details)

    def _notices(self, copy, text):
        """CC-729: one platform copy (its root, thread replies and parts) prints each notice once."""
        details = {"public_object_id": copy.row.get("public_object_id")}
        if not text.strip():
            self.check("CC-729", copy, "PLAN_COPY_TEXT_UNAVAILABLE", status="UNVERIFIED", **details)
            return
        counts = notice_counts(text)
        repeated = {name: count for name, count in counts.items() if count > 1}
        self.check("CC-729", copy, "PUBLIC_NOTICE_REPEATED" if repeated else None,
                   **({"notice_counts": counts, **details} if repeated else {}))

    def _result_frame(self, copy, text, *, correction):
        """CC-768: a result queued from 23 Nov 04:00Z names its plan's dates; a corrected outcome says so."""
        from .plan_call_cards_v1 import RESULT_FRAME_EFFECTIVE

        details = {"public_object_id": copy.row.get("public_object_id")}
        frame = copy.source.get("result_frame")
        plain = normalized(re.sub(r"\*\*|__", "", text))
        frozen = self._frozen_at(copy)
        if not text.strip():
            if frame or correction or (frozen and frozen >= RESULT_FRAME_EFFECTIVE):
                self.check("CC-768", copy, "PLAN_COPY_TEXT_UNAVAILABLE", status="UNVERIFIED", **details)
            return
        if isinstance(frame, dict) and frame.get("plan_dates"):
            missing = [part for part, present in (
                ("plan_dates", normalized(frame["plan_dates"]) in plain),
                ("correction_label", not frame.get("correction") or "correction to the" in plain),
            ) if not present]
            self.check("CC-768", copy, "RESULT_FRAME_NOT_PRINTED" if missing else None,
                       **({"missing": missing, "plan_dates": frame["plan_dates"], **details} if missing else {}))
        elif correction:
            # A correction names what it corrects and the plan's dates.
            labelled = re.search(r"\bcorrect(?:ion|ed|s)\b|\bnote on\b", plain)
            missing = [part for part, present in (("correction_label", bool(labelled)),
                                                  ("plan_dates", bool(_MONTH_DATE.search(text)))) if not present]
            self.check("CC-768", copy, "CORRECTION_DATES_OR_LABEL_MISSING" if missing else None,
                       **({"missing": missing, **details} if missing else {}))
        elif frozen and frozen >= RESULT_FRAME_EFFECTIVE:
            self.check("CC-768", copy, "RESULT_FRAME_MISSING", **details)

    def _analysis(self, copy, analysis_urls, parts, replies):
        from .plan_reader_copy_v1 import NINE_LAYER_COPY

        source = copy.source.get("source_plan") or {}
        plan_id = copy.source.get("plan_id")
        canonical = analysis_urls.get(plan_id)
        continuations = (*parts, *(reply for reply in replies if reply.intent.get("plan_analysis_link")))
        text = self._plan_copy_body(copy, continuations)
        missing = {**_layer_entries(copy.source.get("missing_layers")),
                   **_layer_entries(copy.intent.get("missing_layers"))}
        missing = {key: (value.get("first_cause") or value.get("cause")) if isinstance(value, dict)
                   else value for key, value in missing.items()}
        current = copy.source.get("analysis_copy_contract") == NINE_LAYER_COPY
        layers = self._current_layers(copy, text) if current else plan_layer_checks(text, source, missing)
        # The page is often confirmed after the post; its dedicated link reply then lands under the post,
        # sometimes after an update reply. That reply is the post's analysis link wherever it sits.
        has_link = copy.has_link(canonical, replies) or any(
            reply.intent.get("plan_analysis_link") and reply.has_link(canonical) for reply in replies)
        self.plan_analysis.append({"piece_id": copy.piece, "platform": copy.platform, "public_url": copy.url,
                                   "evidence": copy.evidence, "layers": layers, "full_analysis_link": has_link})
        gaps = {key: item["cause"] for key, item in layers.items() if item["state"] == "MISSING"}
        if gaps:
            self.check("113", copy, "PLAN_ANALYSIS_LAYERS_MISSING", missing_layers=gaps)
        elif current and copy.public_text is None and not copy.verified_at:
            self.check("113", copy, "PLAN_LAYER_READBACK_UNAVAILABLE", status="UNVERIFIED")
        else:
            self.check("113", copy)
        if not has_link:
            self.issue("113", copy.piece, copy.platform, "FULL_ANALYSIS_LINK_MISSING" if canonical
                       else "CONFIRMED_FULL_ANALYSIS_PAGE_UNAVAILABLE", url=copy.url, evidence=copy.evidence)
        return text

    def _first_analysis(self, copy, text):
        from . import plan_scenario_lines_v1 as scenario

        created = clock(copy.source.get("decision_source_created_at_utc")) or clock(copy.row.get("created_at"))
        if (not copy.source.get("analysis_lines_contract")
                and (not created or created < scenario.EFFECTIVE)):
            return
        plan = copy.source.get("source_plan") or {}
        quotes = scenario.analysis_lines(plan)
        public_layers = plan.get("layers") or plan.get("analysis_layers") or []
        if isinstance(public_layers, dict):
            public_layers = public_layers.values()
        analyst_line_available = bool(quotes) or any(
            isinstance(line, dict) and line.get("state") == "USED"
            and isinstance(line.get("text"), str) and line["text"].strip()
            for line in public_layers)
        body = normalized(re.sub(r"\*\*|__", "", text))
        if (analyst_line_available and not quoted_layer_count(text, plan)
                and not any(normalized(quote) in body for quote in quotes)):
            self.check("113", copy, "FIRST_PLAN_POST_ANALYSIS_LINE_MISSING")
        else:
            self.check("113", copy)
        public_text = re.sub(r"https?://\S+", "", text)
        if (scenario.BARE_UTC.search(public_text) or scenario.INTERNAL_CAPS.search(public_text)
                or scenario.INTERNAL_WORDS.search(public_text)):
            self.issue("113", copy.piece, copy.platform, "FIRST_PLAN_POST_INTERNAL_TOKEN",
                       url=copy.url, evidence=copy.evidence)

    def _preview_link(self, copy):
        thread = copy.verified_thread()
        values = (copy.visible_text, copy.title, copy.public_links, copy.resolved_links(thread),
                  [post.get("observed_text") for post in thread])
        self.check("83", copy, PREVIEW_LINK_REASON if find_forbidden_link(*values) else None)

    def _chart(self, copy, market, *, plan_post=False):
        from .posted_chart_readback_v1 import report_copy

        market = market.upper() if isinstance(market, str) else None
        expected = SYMBOLS.get(market)
        chart, reply = report_copy(copy, self.runtime, market, expected)
        if (chart is not None and chart["first_cause"] == "POSTED_CHART_MISMATCH"
                and copy.platform in RECOMPRESSED_IMAGE_ROUTES
                and (not expected or all(asset.get("tradingview_symbol") in ("", expected) for asset in chart["assets"]))):
            # The platform re-encodes the upload; the stored pixel rule cannot tell that from a wrong chart.
            # Never send a "here is the chart" correction on that evidence alone.
            chart = {**chart, "status": "UNVERIFIED", "first_cause": "POSTED_CHART_RECOMPRESSED_UNVERIFIED"}
            reply = None
        assets = copy.media(self.runtime) if market else []
        chart_causes = sorted({cause for asset in assets if (cause :=
            (asset.get("plan_chart_fallback") or {}).get("cause")
            or (asset.get("tradingview_snapshot") or {}).get("plain_price_scale_cause"))})
        if chart is not None:
            self.chart_readbacks.append(chart)
            if reply:
                key = reply["correction_id"]
                previous = self.chart_replies.get(key)
                if previous:
                    media = {asset["sha256"]: asset for asset in [*previous["media_assets"], *reply["media_assets"]]}
                    previous["media_assets"] = list(media.values())
                else:
                    self.chart_replies[key] = reply
            self.check("82", copy, chart["first_cause"], chart_readback=True,
                       status="UNVERIFIED" if chart["status"] == "UNVERIFIED" else "FAIL",
                       public_object_id=chart["public_object_id"])
            if chart["status"] == "MATCH" and chart_causes:
                self.issue("82", copy.piece, copy.platform, "MARKET_TRADINGVIEW_PRICE_SCALE_REFUSED",
                           url=copy.url, evidence=copy.evidence, chart_causes=chart_causes,
                           market=market, expected_symbol=expected)
            return
        if not isinstance(market, str) or not market:
            if plan_post:
                self.check("82", copy, "PLAN_MARKET_UNAVAILABLE", status="UNVERIFIED")
            return
        if not expected:
            self.check("82", copy, "MARKET_TRADINGVIEW_SYMBOL_UNMAPPED", status="UNVERIFIED", market=market)
            return
        symbols = sorted({symbol for asset in assets if (symbol := _media_symbol(asset))})
        cause = ("MARKET_TRADINGVIEW_CHART_MISSING" if not symbols or copy.observed_image is False
                 else "MARKET_TRADINGVIEW_SYMBOL_MISMATCH" if expected not in symbols
                 else "MARKET_TRADINGVIEW_PRICE_SCALE_REFUSED" if chart_causes else None)
        if not cause and plan_post and copy.observed_image is not True:
            self.check("82", copy, "MARKET_TRADINGVIEW_CHART_UNVERIFIED", status="UNVERIFIED", market=market,
                       expected_symbol=expected)
        else:
            self.check("82", copy, cause, market=market, expected_symbol=expected, observed_symbols=symbols,
                       **({"chart_causes": chart_causes} if chart_causes else {}))

    def _coverage(self, delivery):
        for copy in delivery.get("copies", []):
            self.counts["CC-672"] += 1
            source = clock(copy.get("source_at_utc"))
            delivered = next((at for field in ("observed_published_at_utc", "first_verified_readback_at_utc",
                                               "confirmed_dispatch_at_utc") if (at := clock(copy.get(field)))), None)
            source_lag = delivered - source if source and delivered else None
            waited = copy["behind_over_ten_minutes"] or bool(source and self.end - source > PLAN_DELIVERY_LIMIT)
            late = copy["behind_over_ten_minutes"] or bool(source_lag and source_lag > PLAN_DELIVERY_LIMIT)
            status = "FAIL"
            if copy["confirmed"]:
                if not late:
                    continue
                cause = "PLAN_COPY_OVER_TEN_MINUTES_LATE"
            elif waited or copy.get("x_ready_over_five_minutes"):
                cause = "PLAN_COPY_UNCONFIRMED"
                delivery_cause = str(copy.get("first_cause") or "")
                if delivery_cause in HAND_POSTING_FROM:
                    # A route Jim posts by hand is expected to have no automated copy (CC-731, 23 Nov).
                    status, cause = "EXPECTED", "PLAN_COPY_HANDED_TO_JIM"
                elif copy.get("status") == "SUPERSEDED_NOT_POSTED":
                    # The composer replaced this state with a later one (filled or cancelled) by design.
                    status, cause = "EXPECTED", "PLAN_COPY_SUPERSEDED_BY_LATER_STATE"
            else:
                continue
            due = source + PLAN_DELIVERY_LIMIT if source else self.end
            self.issue("CC-672", copy["plan_post"], copy["platform"], cause, url=copy["public_url"],
                       status=status, held_at=due,
                       delivery_cause=copy.get("first_cause"), delivery_state=copy["status"],
                       retry_failure_cause=copy.get("retry_failure_cause"),
                       unresolved_write_age_seconds=copy.get("unresolved_write_age_seconds"),
                       seconds_after_source=source_lag.total_seconds() if source_lag is not None else None,
                       seconds_after_first_confirmed=copy.get("seconds_after_first_confirmed"))

    def _first_posts(self, export, announced, source_error, cutoff):
        if source_error:
            self.issue("CC-672", "plan-status", "all", source_error, status="UNVERIFIED",
                       evidence="main_public_plan_export")
        if not export:
            return

        from .plan_status_posts_v1 import ACTIVE

        snapshot = export["status"]
        observed = clock(snapshot["generated_at_utc"])
        if observed > cutoff or cutoff - observed > PLAN_DELIVERY_LIMIT:
            cause = "MAIN_PLAN_EXPORT_POSTDATES_CUTOFF" if observed > cutoff else "MAIN_PLAN_EXPORT_STALE"
            self.issue("CC-672", "plan-status", "all", cause, status="UNVERIFIED",
                       evidence="main_public_plan_export", observed_at_utc=observed.isoformat())
        # Dated fills are usable even when the snapshot was generated just after the cutoff.
        filled = {transition["plan_id"] for transition in export["transitions"]["transitions"]
                  if transition["status"] == "FILLED" and self.start < clock(transition["at_utc"]) <= cutoff}

        for plan in snapshot["plans"]:
            registered = clock(plan.get("registered_at_utc"))
            if not registered or registered > cutoff or not plan.get("asset_id"):
                continue
            state = plan.get("status")
            status_at = clock(plan.get("status_at_utc"))
            if plan["plan_id"] in filled or (state == "FILLED" and status_at and status_at <= cutoff):
                basis = "recorded_fill"
            elif observed <= cutoff:
                instrument = plan.get("public_instrument") or {}
                # Main supplies these levels only from a joined submitted IBKR ticket.
                submitted = (instrument.get("levels_first_cause") is None
                             and instrument.get("direction") in {"BULLISH", "BEARISH"}
                             and all(instrument.get(key) is not None for key in
                                     ("zone_low", "zone_high", "invalidation_level")))
                if submitted and (registered > self.start or state in ACTIVE):
                    basis = "submitted_ibkr_ticket"
                elif state in ACTIVE and plan.get("kind") == "OPEN_ARM":
                    basis = "active_main_arm"
                else:
                    continue
            else:
                continue
            self.counts["CC-672"] += 1
            if plan["plan_id"] not in announced:
                self.issue("CC-672", plan["plan_id"], "all", "BROKER_PLAN_FIRST_POST_MISSING",
                           held_at=registered + PLAN_DELIVERY_LIMIT,
                           evidence="main_public_plan_export", broker_evidence=basis,
                           market=plan["asset_id"], plan_status=state,
                           registered_at_utc=registered.isoformat(), observed_at_utc=observed.isoformat(),
                           checked_as_of_utc=cutoff.isoformat())

    def _discord(self, copy, channel_arrivals):
        source = copy.source
        if source.get("kind") != "result" and source.get("state") not in PLAN_FILL_STATES:
            return
        channel_reply = copy.native.get("discord_channel_reply") or copy.native.get("discord_channel_post")
        if (channel_reply or (source.get("key") or copy.piece) in channel_arrivals
                or copy.proof.get("discord_channel_reply_verified") is True):
            self.check("CC-685", copy)
        elif copy.native.get("discord_thread_parent_id"):
            self.check("CC-685", copy, "DISCORD_FILL_OR_RESULT_THREAD_ONLY")
        else:
            self.check("CC-685", copy, "DISCORD_CHANNEL_PLACEMENT_UNVERIFIED", status="UNVERIFIED")

    def _linkedin(self, piece, copies, canonical):
        by_platform = defaultdict(list)
        for copy in copies:
            by_platform[copy.platform].append(copy)
        first = min((at for copy in copies for at in (copy.published_at, copy.dispatched_at, copy.verified_at)
                     if at), default=None)
        due = first + PLAN_DELIVERY_LIMIT if first else None
        for platform in ("linkedin", "linkedin_company"):
            available = [copy for copy in by_platform[platform] if copy.confirmed]
            if not available:
                self.counts["CC-684"] += 1
                if hand := self._hand_posted(platform, due):
                    self.issue("CC-684", piece, platform, "LINKEDIN_COPY_HANDED_TO_JIM", status="EXPECTED",
                               hand_cause=hand)
                else:
                    self.issue("CC-684", piece, platform, "LINKEDIN_ACCOUNT_COPY_MISSING", held_at=due)
            for copy in available:
                self.check("CC-684", copy, "LINKEDIN_SUBSTACK_LINK_MISSING"
                           if not copy.has_link(canonical) else None)
                image = copy.observed_image
                if image is not True:
                    cause = ("LINKEDIN_IMAGE_MISSING" if image is False or not copy.media(self.runtime)
                             else "LINKEDIN_IMAGE_UNVERIFIED")
                    self.issue("CC-684", piece, platform, cause, url=copy.url, evidence=copy.evidence,
                               status="UNVERIFIED" if cause.endswith("_UNVERIFIED") else "FAIL")

    def _late(self, copy):
        from .plan_analysis_pages_v1 import FINAL_STATES, entry_deadline

        plan = copy.source.get("source_plan") or {}
        deadline = clock(entry_deadline(plan))
        if not deadline:
            return
        at = copy.published_at
        if not at and copy.verified_at and copy.verified_at <= deadline:
            return
        if not at and copy.dispatched_at and copy.dispatched_at >= deadline:
            at = copy.dispatched_at  # the frozen write was dispatched after entry closed
        if not at:
            self.check("CC-584", copy, "PLAN_PAGE_PUBLICATION_CLOCK_UNVERIFIED", status="UNVERIFIED")
        elif at >= deadline:
            text = normalized(copy.visible_text)
            final = copy.source.get("final_status") or {}
            status = FINAL_STATES.get(final.get("status"))
            status_at = clock(final.get("status_at_utc"))
            waiting = re.search(r"\b(?:status\s*:\s*)?waiting for entry\b", text)
            if (waiting or LATE_LINE not in text or not status or not status_at or status_at > at
                    or "status: " + normalized(status) not in text):
                self.check("CC-584", copy, "LATE_PLAN_PAGE_FINAL_STATUS_OR_LINE_MISSING",
                           entry_deadline_utc=deadline.isoformat())
            else:
                self.check("CC-584", copy)
        else:
            self.check("CC-584", copy)

    def _immutable(self, copy):
        self.counts["136"] += 1
        if copy.public_http_status in {404, 410}:
            self.issue("136", copy.piece, copy.platform, "PREVIOUSLY_CONFIRMED_OBJECT_UNAVAILABLE",
                       url=copy.url, evidence="public_http", status="UNVERIFIED")
        for read_at, record in copy.history:
            seen = clock(read_at)
            if not seen or not self.start < seen <= self.end:
                continue
            proof = record.get("readback", record)
            result = record.get("result") or {}
            action = record.get("action")
            if (action in {"EDIT_EXISTING", "EDIT_EXISTING_PHOTO_ATTRIBUTION"}
                    and (proof.get("verified") is True or result.get("status") == "PRESENTATION_EDIT_CONFIRMED")
                    and proof.get("write_absent") is not True and result.get("public_write_performed") is not False
                    and proof.get("identity_match") is not False
                    and proof.get("observed_public_object_id") in (None, copy.row.get("public_object_id"))):
                self.issue("136", copy.piece, copy.platform, "PUBLISHED_OBJECT_EDIT_CONFIRMED",
                           url=copy.url, evidence="stored_readback", observed_at_utc=read_at)
            elif (action in {"DELETE_EXISTING", "DELETE_POST"}
                    and (result.get("status") in {"DELETED", "DELETE_CONFIRMED"}
                         or proof.get("write_absent") is True)):
                self.issue("136", copy.piece, copy.platform, "PUBLISHED_OBJECT_DELETE_CONFIRMED",
                           url=copy.url, evidence="stored_readback", observed_at_utc=read_at)

    def finish(self, delivery, analysis_urls, *, plan_export=None, announced=(), plan_source_error=None,
               plan_cutoff=None):
        from .plan_call_cards_v1 import DISCORD_CHANNEL_PART, LATE_CHART_PART
        from .plan_reader_copy_v1 import NINE_LAYER_COPY

        self._wraps()
        self._coverage(delivery)
        self._first_posts(plan_export, announced, plan_source_error, plan_cutoff or self.end)
        groups = defaultdict(list)
        discord = defaultdict(list)
        parts = defaultdict(list)
        replies = defaultdict(list)
        for copy in self.copies:
            source = copy.source
            plan = source.get("source_plan") or {}
            market = plan.get("asset_id") or source.get("symbol") or copy.intent.get("market_asset")
            if not copy.confirmed:
                # Some confirmed comments return an object ID without a permalink.
                if (copy.row.get("status") == "DISPATCH_CONFIRMED" and copy.row.get("public_object_id")
                        and copy.dispatched_at and self.start < copy.dispatched_at <= self.end):
                    self._chart(copy, market)
                continue
            if copy.platform == "discord":
                discord[copy.source.get("key") or copy.piece].append(copy)
            part = copy.intent.get("plan_status_part")
            key = copy.source.get("key")
            if (key and type(part) is int and part > 0 and part != LATE_CHART_PART
                    and copy.piece == f"{key}-part-{part}"
                    and not (copy.platform == "discord" and part == DISCORD_CHANNEL_PART
                             and (copy.native.get("discord_channel_reply") or copy.native.get("discord_channel_post")))):
                parts[(key, copy.platform)].append((part, copy))
            if parent := copy.reply_parent():
                replies[(copy.platform, parent)].append(copy)
        for chain in replies.values():
            chain.sort(key=lambda copy: (copy.published_at or copy.dispatched_at or copy.verified_at, copy.piece))
        channel_arrivals = {key for key, copies in discord.items()
                            if any(copy.intent.get("plan_status_part") != LATE_CHART_PART
                                   and (copy.native.get("discord_channel_reply") or copy.native.get("discord_channel_post"))
                                   for copy in copies)}
        fills_and_results = set()
        counted_gaps = set()
        for copy in self.copies:
            if not copy.confirmed:
                continue
            chain = [part for _, part in sorted(parts.get((copy.piece, copy.platform), []),
                                                key=lambda pair: pair[0])]
            times = (at for item in (copy, *chain) for at in (item.published_at, item.verified_at, item.dispatched_at))
            if not any(at and self.start < at <= self.end for at in times):
                # Old posts can still acquire an edit/delete readback this evening.
                if any(self.start < clock(at) <= self.end for at, _ in copy.history):
                    self._immutable(copy)
                continue
            source = copy.source
            plan = source.get("source_plan") or {}
            plan_post = source.get("kind") in PLAN_POST_KINDS
            late_chart = plan_post and copy.intent.get("plan_status_part") == LATE_CHART_PART
            channel_copy = copy.platform == "discord" and not late_chart and (
                copy.native.get("discord_channel_reply") or copy.native.get("discord_channel_post"))
            plan_part = plan_post and bool(copy.intent.get("plan_status_part")) and not channel_copy
            plan_page = copy.platform == "substack" and bool(copy.intent.get("plan_analysis_page") or source.get("page_id"))
            correction = source.get("kind") == "correction" or copy.piece.startswith("correction-")
            self.posted.append(copy)
            if (plan_post and not plan_part) or correction:
                self._notices(copy, self._plan_copy_body(copy, chain))
                if source.get("kind") == "result" or correction:
                    self._result_frame(copy, self._plan_copy_body(copy, chain), correction=correction)
            if plan_post or plan_page or correction:
                body = self._plan_copy_body(copy)
                # A continuation is a public object with its own target check. Use
                # the whole platform copy for the scenario review below.
                target_text = f"{copy.title}\n{body}" if body and copy.public_text is None else body
                self._plan_target(copy, target_text)
                if plan_page:
                    self._scenario_voice(copy, body)
                elif correction:
                    # A correction note is no plan call: no cases, zone or invalidation to look for.
                    self._scenario_voice(copy, body, rules=("POSITION_WORDS_REPEATED",))
            if plan_post and not plan_part:
                key = source.get("key") or copy.piece
                if key not in counted_gaps:
                    counted_gaps.add(key)
                    self.layer_gaps.update((layer, cause) for layer, cause in
                                           (source.get("analysis_layer_gaps") or {}).items() if _safe_cause(cause))
                own_replies = [reply for reply in replies[(copy.platform, str(copy.row.get("public_object_id")))]
                               if reply is not copy and reply.native.get("reply_to_url") in (None, copy.url)]
                text = self._analysis(copy, analysis_urls, chain, own_replies)
                self._scenario_voice(copy, text)
                if source.get("kind") == "setup" and source.get("analysis_copy_contract") != NINE_LAYER_COPY:
                    self._first_analysis(copy, text)
                if source.get("kind") == "result" or source.get("state") in PLAN_FILL_STATES:
                    fills_and_results.add(source.get("key") or copy.piece)
                if copy.platform == "discord":
                    self._discord(copy, channel_arrivals)
            market = plan.get("asset_id") or source.get("symbol") or copy.intent.get("market_asset")
            if not plan_part or late_chart:
                self._chart(copy, market, plan_post=plan_post)
            text = copy.visible_text + "\n" + copy.title
            self.check("90", copy, "PUBLIC_TIMEZONE_ET_REQUIRED"
                       if find_forbidden_public_time(text) or PUBLIC_CLOCK.search(text) else None)
            self.check("109", copy, "PUBLIC_AI_LABEL_OR_MODEL_NAME" if AI_LABEL.search(text) else None)
            self._preview_link(copy)
            self._immutable(copy)
            if plan_page:
                self._late(copy)
            if not plan_part and (plan_post or copy.intent.get("full_v1_distribution_required") or copy.intent.get("resolved_article_mode")
                    or wrap_kind(copy.title, None) or copy.platform in {"linkedin", "linkedin_company"}):
                groups[source.get("key") or copy.piece].append(copy)
        for piece in sorted(fills_and_results - discord.keys()):
            self.counts["CC-685"] += 1
            first = min((at for copy in self.posted if (copy.source.get("key") or copy.piece) == piece
                         for at in (copy.published_at, copy.dispatched_at, copy.verified_at) if at), default=None)
            self.issue("CC-685", piece, "discord", "DISCORD_FILL_OR_RESULT_CHANNEL_COPY_MISSING",
                       held_at=first + PLAN_DELIVERY_LIMIT if first else None)
        for piece, copies in groups.items():
            first = copies[0]
            canonical = (analysis_urls.get(first.source.get("plan_id"))
                         or next((copy.url for copy in self.copies if copy.piece == piece and copy.platform == "substack"
                                  and copy.confirmed), None)
                         or first.intent.get("canonical_url"))
            self._linkedin(piece, copies, canonical)
        return self.result()

    def result(self):
        issues = sorted(self.issues, key=lambda row: (DECISIONS.index(row["decision"]), row["piece_id"],
                                                     row["platform"], row["first_cause"], row["public_url"] or ""))
        voice = Counter(row["first_cause"] for row in issues if row["status"] == "FLAGGED")
        voice_reviewed = self.counts["158"] - sum(row["decision"] == "158" and row["status"] == "UNVERIFIED"
                                                for row in issues)
        scenario_voice = {
            "posts_reviewed": voice_reviewed,
            "rules": [{"rule": rule, "flagged": voice[rule],
                       "share_pct": round(100 * voice[rule] / voice_reviewed, 2) if voice_reviewed else None}
                      for rule in SCENARIO_REVIEW_RULES],
        }
        return {"schema_version": "contentops.decision_checks.v1", "window": self.window,
                "pause": self.pause_summary(issues),
                "scenario_voice": scenario_voice,
                "plan_analysis": sorted(self.plan_analysis, key=lambda row: (
                    row["piece_id"], row["platform"], row["public_url"] or "")),
                "checks": [{"decision": decision, "checked": self.counts[decision],
                            "failed": sum(row["decision"] == decision and row["status"] == "FAIL" for row in issues),
                            "unverified": sum(row["decision"] == decision and row["status"] == "UNVERIFIED" for row in issues),
                            **{status.lower(): count for status in NOT_COUNTED[1:] if (count := sum(
                                row["decision"] == decision and row["status"] == status for row in issues))}}
                           for decision in DECISIONS],
                "failure_count": sum(row["status"] == "FAIL" for row in issues),
                "unverified_count": sum(row["status"] == "UNVERIFIED" for row in issues),
                "analysis_layer_gaps": [{"layer": layer, "first_cause": cause, "count": count}
                                        for (layer, cause), count in sorted(self.layer_gaps.items())],
                "posted_chart_readbacks": self.chart_readbacks,
                "chart_correction_replies": list(self.chart_replies.values()),
                "issues": issues}

    def pause_summary(self, issues):
        """None when no posting pause touches the window; otherwise its cause, clocks and what it held.

        PAUSED: no public copy went out in the window, so the day reports the pause, not failures.
        PARTLY_PAUSED: copies went out before or after the pause; only copies due inside it are held.
        """
        overlapping = [(start, end, cause) for start, end, cause in self.pauses
                       if start < self.end and (end is None or end > self.start)]
        if not overlapping:
            return None
        start, end, cause = overlapping[-1]
        published = sum(1 for copy in self.posted if any(
            at and self.start < at <= self.end for at in (copy.published_at, copy.dispatched_at)))
        return {"state": "PARTLY_PAUSED" if published else "PAUSED", "cause": cause,
                "paused_at_utc": start.isoformat(), "restored_at_utc": end.isoformat() if end else None,
                "public_copies_in_window": published,
                "held_checks": sum(row["status"] == "PAUSED" for row in issues)}

    def estimated_jobs(self, delivery):
        new_plans = {copy.source.get("plan_id") for copy in self.copies
                     if copy.source.get("kind") == "setup"
                     and self.start < (clock(copy.row.get("created_at")) or self.start) <= self.end}
        articles = {copy.piece for copy in self.copies if copy.platform == "substack"
                    and (copy.intent.get("full_v1_distribution_required")
                         or copy.intent.get("resolved_article_mode"))
                    and self.start < (clock(copy.row.get("created_at")) or self.start) <= self.end}
        return {"plan_layer_lines": delivery.get("plan_posts", 0),
                "plan_analysis_page": len(new_plans - {None}),
                "daily_wrap_sections": self.wraps_due["daily"],
                "weekend_wrap_sections": self.wraps_due["weekend"],
                "article_claim_check": len(articles)}
