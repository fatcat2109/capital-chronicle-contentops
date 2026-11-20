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

from .public_time_v1 import PUBLIC_ZONE, find_forbidden_public_time
from .tradingview_snapshot_v1 import SYMBOLS
from .x_reply_trading_dates_v1 import trading_date


WRAP_ROUTES = ("substack", "substack_notes", "telegram", "discord", "facebook_page",
               "instagram_business", "threads", "linkedin", "linkedin_company", "x")
DECISIONS = ("98", "113", "82", "CC-672", "CC-685", "CC-684", "90", "109", "136", "CC-584")
LATE_LINE = "this page was published after the plan ended"
LAYER_PREFIX = re.compile(
    r"\b(macro|fundamentals?|positioning and sentiment|positioning|sentiment|options and gamma|"
    r"options|gamma|gex|priced in|technical|structure|geopolitics|geopolitical|scenarios?)\s*:\s*", re.I)
LAYER_ALIAS = {
    "fundamentals": "fundamental", "positioning and sentiment": "positioning", "sentiment": "positioning",
    "gamma": "options", "gex": "options", "options and gamma": "options", "structure": "technical",
    "geopolitical": "geopolitics", "scenarios": "scenario",
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


def _observations(history, row):
    """Only dated observations of this dispatch can establish publication."""
    verified_at = published_at = None
    proof = {}
    for read_at, record in history:
        current = record.get("readback", record)
        if (current.get("verified") is not True or current.get("write_absent") is True
                or current.get("identity_match") is False
                or current.get("observed_public_object_id") not in (None, row.get("public_object_id"))):
            continue
        proof = {**proof, **current}
        verified_at = verified_at or clock(read_at)
        seen_at = clock(current.get("observed_published_at_utc"))
        if seen_at and seen_at <= clock(read_at):
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
    proof: dict = field(init=False)
    verified_at: datetime | None = field(init=False)
    published_at: datetime | None = field(init=False)
    dispatched_at: datetime | None = field(init=False)

    def __post_init__(self):
        self.proof, self.verified_at, self.published_at = _observations(self.history, self.row)
        dispatched = clock(self.row.get("dispatched_at"))
        self.dispatched_at = dispatched if dispatched and dispatched <= self.end else None

    @property
    def confirmed(self):
        return bool(self.url and (self.verified_at or (
            self.dispatched_at and self.row.get("status") == "DISPATCH_CONFIRMED")))

    @property
    def native(self):
        return self.intent.get("native_payload") or {}

    @property
    def visible_text(self):
        return self.public_text if self.public_text is not None else self.text

    @property
    def evidence(self):
        return "public_http" if self.public_text is not None else (
            "stored_readback" if self.verified_at else "confirmed_dispatch")

    def media(self, runtime):
        ids = self.native.get("media_asset_ids")
        assets = self.intent.get("media_assets") or self.source.get("media_assets") or []
        folder = self.intent.get("output_dir")
        if folder:
            # Only the existing delivery artifact under this runtime is read.
            root = Path(folder).resolve()
            if root.is_relative_to(runtime):
                assets = [*assets, *object_json(root / "delivery_media_manifest_v1.json").get("assets", [])]
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
        self.wraps_due = Counter()
        self.issues = []
        self.seen = set()

    def add(self, piece, platform, url, title, text, intent, row, history, source):
        copy = PublicCopy(piece, platform, url, title, text, intent, row, history, source, self.end)
        self.copies.append(copy)
        return copy

    def issue(self, decision, piece, platform, cause, *, url=None, evidence=None,
              status="FAIL", **details):
        key = (decision, piece, platform, cause, url)
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
        candidate_pieces = {
            copy.piece for copy in copies if copy.platform == "substack"
            and (ts := copy.published_at or copy.dispatched_at or clock(copy.row.get("created_at")))
            and first_day <= ts.astimezone(PUBLIC_ZONE).date() <= day
        }
        for platform in WRAP_ROUTES:
            self.counts["98"] += 1
            candidates = [copy for copy in copies if copy.piece in candidate_pieces and copy.platform == platform]
            confirmed = [copy for copy in candidates if copy.confirmed]
            if any((copy.published_at or copy.verified_at or datetime.max.replace(tzinfo=timezone.utc)) <= deadline
                   for copy in confirmed):
                continue
            picked = next(iter(confirmed or candidates), None)
            if confirmed:
                cause = "WRAP_PUBLISHED_LATE" if all(copy.published_at for copy in confirmed) else "WRAP_PUBLICATION_TIME_UNVERIFIED"
            else:
                cause = "WRAP_PLATFORM_MISSING"
            label = ("weekend-wrap-" if first_day != day else "pre-us-wrap-") + day.isoformat()
            self.issue("98", picked.piece if picked else next(iter(sorted(candidate_pieces)), label),
                       platform, cause, url=picked.url if picked else None,
                       status="UNVERIFIED" if cause.endswith("_UNVERIFIED") else "FAIL",
                       deadline_utc=deadline.isoformat())

    def _analysis(self, copy, analysis_urls):
        source = copy.source.get("source_plan") or {}
        plan_id = copy.source.get("plan_id")
        canonical = analysis_urls.get(plan_id)
        linked = contains_link(copy.visible_text, canonical, copy.public_links)
        if not linked and copy.platform == "x" and copy.proof.get("thread_verified") is True:
            linked = contains_link("\n".join(_strings(copy.native.get("reply_texts"))), canonical)
        layers = quoted_layer_count(copy.visible_text, source)
        self.check("113", copy, "PLAN_LAYER_QUOTES_BELOW_THREE" if layers < 3 else None,
                   quoted_layers=layers)
        if not linked:
            self.issue("113", copy.piece, copy.platform, "FULL_ANALYSIS_LINK_MISSING" if canonical
                       else "CONFIRMED_FULL_ANALYSIS_PAGE_UNAVAILABLE", url=copy.url, evidence=copy.evidence)

    def _chart(self, copy, market):
        if not market:
            return
        market = market.upper()
        expected = SYMBOLS.get(market)
        if not expected:
            self.check("82", copy, "MARKET_TRADINGVIEW_SYMBOL_UNMAPPED", status="UNVERIFIED", market=market)
            return
        symbols = sorted({symbol for asset in copy.media(self.runtime) if (symbol := _media_symbol(asset))})
        cause = ("MARKET_TRADINGVIEW_CHART_MISSING" if not symbols or copy.image_visible is False
                 else "MARKET_TRADINGVIEW_SYMBOL_MISMATCH" if expected not in symbols else None)
        self.check("82", copy, cause, market=market, expected_symbol=expected, observed_symbols=symbols)

    def _coverage(self, delivery):
        for copy in delivery.get("copies", []):
            self.counts["CC-672"] += 1
            if copy["confirmed"] and not copy["behind_over_ten_minutes"]:
                continue
            first = clock(copy.get("source_at_utc"))
            if (not copy["behind_over_ten_minutes"] and not copy.get("x_ready_over_five_minutes")
                    and (not first or (self.end - first).total_seconds() <= 600)):
                continue
            cause = "PLAN_COPY_OVER_TEN_MINUTES_LATE" if copy["confirmed"] else "PLAN_COPY_UNCONFIRMED"
            self.issue("CC-672", copy["plan_post"], copy["platform"], cause, url=copy["public_url"],
                       delivery_cause=copy.get("first_cause"), delivery_state=copy["status"],
                       seconds_after_first_confirmed=copy.get("seconds_after_first_confirmed"))

    def _discord(self, copy, channel_arrivals):
        source = copy.source
        if source.get("kind") != "result" and str(source.get("state")).upper() != "FILLED":
            return
        channel_reply = copy.native.get("discord_channel_reply")
        if channel_reply or copy.piece in channel_arrivals or copy.proof.get("discord_channel_reply_verified") is True:
            self.check("CC-685", copy)
        elif copy.native.get("discord_thread_parent_id"):
            self.check("CC-685", copy, "DISCORD_FILL_OR_RESULT_THREAD_ONLY")
        else:
            self.check("CC-685", copy, "DISCORD_CHANNEL_PLACEMENT_UNVERIFIED", status="UNVERIFIED")

    def _linkedin(self, piece, copies, canonical):
        by_platform = defaultdict(list)
        for copy in copies:
            by_platform[copy.platform].append(copy)
        for platform in ("linkedin", "linkedin_company"):
            available = [copy for copy in by_platform[platform] if copy.confirmed]
            if not available:
                self.counts["CC-684"] += 1
                self.issue("CC-684", piece, platform, "LINKEDIN_ACCOUNT_COPY_MISSING")
            for copy in available:
                self.check("CC-684", copy, "LINKEDIN_SUBSTACK_LINK_MISSING"
                           if not contains_link(copy.visible_text, canonical, copy.public_links) else None)
                image = copy.image_visible
                if image is None:
                    image = copy.proof.get("meaningful_media_visible", copy.proof.get("image_visible"))
                if image is not True:
                    cause = "LINKEDIN_IMAGE_MISSING" if image is False or not copy.native.get("media_asset_ids") else "LINKEDIN_IMAGE_UNVERIFIED"
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
        for read_at, record in copy.history:
            if not self.start < clock(read_at) <= self.end:
                continue
            proof = record.get("readback", record)
            result = record.get("result") or {}
            action = record.get("action")
            if action == "EDIT_EXISTING" and proof.get("verified") is True and proof.get("write_absent") is not True:
                self.issue("136", copy.piece, copy.platform, "PUBLISHED_OBJECT_EDIT_CONFIRMED",
                           url=copy.url, evidence="stored_readback", observed_at_utc=read_at)
            elif (action in {"DELETE_EXISTING", "DELETE_POST"}
                    and (result.get("status") in {"DELETED", "DELETE_CONFIRMED"}
                         or proof.get("write_absent") is True)):
                self.issue("136", copy.piece, copy.platform, "PUBLISHED_OBJECT_DELETE_CONFIRMED",
                           url=copy.url, evidence="stored_readback", observed_at_utc=read_at)

    def finish(self, delivery, analysis_urls):
        self._wraps()
        self._coverage(delivery)
        groups = defaultdict(list)
        channel_arrivals = {c.piece.rsplit("-part-", 1)[0] for c in self.copies
                            if c.confirmed and c.platform == "discord" and c.native.get("discord_channel_reply")}
        for copy in self.copies:
            if not copy.confirmed:
                continue
            times = (copy.published_at, copy.verified_at, copy.dispatched_at)
            if not any(at and self.start < at <= self.end for at in times):
                # Old posts can still acquire an edit/delete readback this evening.
                if any(self.start < clock(at) <= self.end for at, _ in copy.history):
                    self._immutable(copy)
                continue
            source = copy.source
            plan = source.get("source_plan") or {}
            plan_post = source.get("kind") in {"setup", "update", "result"}
            plan_page = copy.platform == "substack" and bool(copy.intent.get("plan_analysis_page") or source.get("page_id"))
            if plan_post:
                self._analysis(copy, analysis_urls)
                if copy.platform == "discord":
                    self._discord(copy, channel_arrivals)
            market = plan.get("asset_id") or source.get("symbol") or copy.intent.get("market_asset")
            self._chart(copy, market)
            text = copy.visible_text + "\n" + copy.title
            self.check("90", copy, "PUBLIC_TIMEZONE_ET_REQUIRED"
                       if find_forbidden_public_time(text) or PUBLIC_CLOCK.search(text) else None)
            self.check("109", copy, "PUBLIC_AI_LABEL_OR_MODEL_NAME" if AI_LABEL.search(text) else None)
            self._immutable(copy)
            if plan_page:
                self._late(copy)
            if plan_post or copy.intent.get("full_v1_distribution_required") or copy.platform in {"linkedin", "linkedin_company"}:
                groups[copy.piece].append(copy)
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
        return {"schema_version": "contentops.decision_checks.v1", "window": self.window,
                "checks": [{"decision": decision, "checked": self.counts[decision],
                            "failed": sum(row["decision"] == decision and row["status"] == "FAIL" for row in issues),
                            "unverified": sum(row["decision"] == decision and row["status"] == "UNVERIFIED" for row in issues)}
                           for decision in DECISIONS],
                "failure_count": sum(row["status"] == "FAIL" for row in issues),
                "unverified_count": sum(row["status"] == "UNVERIFIED" for row in issues),
                "issues": issues}

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
