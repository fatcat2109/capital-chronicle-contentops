"""CC-403: reader prose and source clocks in the existing article lifecycle.

The writer owns words. This module checks them and freezes the source clock;
it does not create a publication, queue, schedule or numerical estimate.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import re

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of

POLICY = "CC403_READER_ARTICLE_V1"
MAX_SENTENCE_WORDS = 35
DAILY_WORDS = 350
DATA_TO_PUBLICATION_MINUTES = 60
FIELDS = ("title", "subtitle", "dek", "search_title", "meta_description", "social_hook",
          "substack_body_markdown")
MARKER = re.compile(r"\[\[SOURCE:(SOURCE_\d+)\]\]")
INTERNAL_PHRASES = ("DATED CAPITAL CHRONICLE REVIEW", "the review records", "capture",
                    "NATIVE_DESKTOP_INPUT_REQUIRED")
NUMBER = re.compile(r"(?<![\w.])[+\-\N{MINUS SIGN}]?\d+(?:,\d{3})*(?:\.\d+)?"
                    r"(?:\s*(?:%|percent\b|bps\b|basis points?\b))?", re.I)
MARKETS = (r"\bgold\b", r"\bS&P\s*500\b", r"\bEUR\s*/?\s*USD\b", r"\bUSD\s*/?\s*JPY\b",
           r"\b(?:WTI|oil)\b", r"\b(?:Bitcoin|BTC)\b")
GUIDANCE = """CC403_READER_ARTICLE_V1: these reader rules supersede older presentation instructions.
Start the first body sentence with our call in first person, for example 'We think ...'.
Use our voice throughout. Keep internal labels in metadata, including DATED CAPITAL
CHRONICLE REVIEW, 'the review records', and 'capture'. Titles are clean editorial titles.
Keep natural attribution, meaningful dates, uncertainty and every substantive source limit.
Use one Scenarios section with the single Main-sourced scenario set, never two clocks or
an invented probability. Include an explicit 'So what:' sentence for the reader.
Every prose sentence is at most 35 words. Every number in public fields must occur in
its bound source text, with the same sign and unit; keep internal SOURCE markers and
claim bindings. Never use source ids, URLs or timestamps as numerical evidence.
A DAILY_NOTE has one six-market Markdown table, at most 350 words outside that table,
and substantive 'What changed since yesterday' and 'What we got wrong' sections.
Reuse the supplied prior reports and outcomes; state an actual comparison gap plainly
when the supplied record cannot establish it. Never invent an error or a success.
A WEEKLY_REVIEW is a long review, not a daily note. Include CC-379's whole scored-call
record exactly once, including losses and unscored expiries, and discuss what we got wrong.
The daily note uses Antigravity's first draft (decision 114) and one Codex light editorial
pass. The weekly review uses the existing Codex strong pass. Record actual calls and
failures. Cards retain their own contract. Keep the original data cutoff: generation,
retrieval, approval and a media refresh never restart the 60-minute publication clock.
"""


def utc(value):
    try:
        clock = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if clock.tzinfo is None:
            raise ValueError()
        return clock.astimezone(timezone.utc)
    except (ValueError, TypeError) as exc:
        raise ValueError("ARTICLE_DATA_CUTOFF_INVALID") from exc


def article_format(governed, run_id=""):
    from live_contentops.weekly_scored_calls_v1 import is_wrap
    candidate = governed.get("selected_candidate") or {}
    explicit = candidate.get("reader_format") or governed.get("reader_format")
    if explicit in {"DAILY_NOTE", "WEEKLY_REVIEW"}:
        return explicit
    if is_wrap(candidate, run_id) or any(d.get("weekly_scored_calls") for d in governed.get("source_pack", [])):
        return "WEEKLY_REVIEW"
    title = " ".join(str(candidate.get(k) or "") for k in ("headline_text", "headline", "title"))
    tags = set(candidate.get("candidate_catalyst_tags") or [])
    if tags & {"DAILY_NOTE", "DAILY_WRAP", "PRE_US_WRAP"} or re.search(
            r"\b(?:daily[ -](?:note|wrap)|pre[ -]US[ -](?:note|wrap)|six[ -]market[ -](?:note|wrap))\b",
            title + " " + run_id, re.I):
        return "DAILY_NOTE"
    return "ARTICLE"


def source_clock(documents, candidate=None):
    """The current source's data clock; dated context cannot refresh that clock."""
    candidate = candidate or {}
    current = [d for d in documents if not d.get("context_only") and not d.get("weekly_scored_calls")]
    primary = next((d for d in current if d.get("document_id") == candidate.get("headline_id")),
                   current[0] if current else {})
    lineage = primary.get("report_lineage") or {}
    value = primary.get("data_cutoff_utc") or lineage.get("data_cutoff_utc") or lineage.get("known_at_cutoff_utc")
    if not value:
        observations = [e["observation_time_utc"] for claim in lineage.get("claims", [])
                        for e in claim.get("evidence", []) if e.get("observation_time_utc")]
        value = max(observations, key=utc) if observations else None
    # A release's own publication is a data clock. A retained report's generation
    # or a fresh read of it is not. The projection adapter supplies its capture.
    if not value and "KNOWN_AT" not in str(primary.get("published_at_source") or ""):
        value = primary.get("published_at_utc")
    return utc(value).isoformat() if value else None


def contract_for(governed, run_id=""):
    documents = governed.get("source_pack", [])
    candidate = governed.get("selected_candidate") or {}
    current = [d for d in documents if not d.get("context_only") and not d.get("weekly_scored_calls")]
    primary = next((d for d in current if d.get("document_id") == candidate.get("headline_id")),
                   current[0] if current else {})
    return {"policy": POLICY, "format": article_format(governed, run_id),
            "source_pack_sha256": sha256_of(documents),
            "primary_document_id": primary.get("document_id"),
            "data_cutoff_utc": source_clock(documents, candidate),
            "max_sentence_words": MAX_SENTENCE_WORDS, "daily_prose_words": DAILY_WORDS,
            "publication_target_minutes": DATA_TO_PUBLICATION_MINUTES}


def visible(text):
    text = MARKER.sub("", str(text or ""))
    text = re.sub(r"\[\[(?:CITE:[^|\]]+\|([^\]]+)|VISUAL:[^\]]+)\]\]", lambda m: m[1] or "", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    return re.sub(r"[*_`]", "", text).strip()


def words(text):
    return re.findall(r"\b[\w]+(?:['\N{RIGHT SINGLE QUOTATION MARK}-][\w]+)*\b", text)


def sentences(text):
    text = re.sub(r"\b(?:U\.S\.|U\.K\.|e\.g\.|i\.e\.)", lambda m: m[0].replace(".", ""), text)
    for line in text.splitlines():
        line = re.sub(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)", "", line)
        if not line.strip() or line.lstrip().startswith(("#", "|")):
            continue
        yield from (s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if s.strip())


def numbers(text):
    text = visible(text)
    # Decision 107's instrument names are identifiers, not newly asserted values.
    text = re.sub(r"\b(?:S&P\s*500|6E|6J)\b", "", text, flags=re.I)
    text = re.sub(r"\b(\d{4})-(\d{2})-(\d{2})(?:T[^\s]+)?", r"\1 \2 \3", text)
    result = set()
    for match in NUMBER.finditer(text):
        value = match[0].replace(",", "").replace("\N{MINUS SIGN}", "-")
        value = re.sub(r"\s+", "", value).casefold()
        value = value.replace("percent", "%").replace("basispoints", "bps").replace("basispoint", "bps")
        value = value.removeprefix("+")
        result.add(value)
    return result


def label_errors(text):
    return ["INTERNAL_EDITORIAL_LABEL:" + phrase for phrase in INTERNAL_PHRASES
            if re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text, re.I)]


def _daily_prose(body):
    blocks = re.split(r"\n\s*\n", body)
    tables = [block for block in blocks if block.lstrip().startswith("|") and all(
        re.search(pattern, block, re.I) for pattern in MARKETS)]
    if len(tables) != 1:
        return body, ["DAILY_SIX_MARKET_TABLE_REQUIRED"]
    return "\n\n".join(b for b in blocks if b != tables[0]), []


def check_article(article, documents, *, contract=None):
    contract = contract or article.get("reader_article_contract")
    if not contract or contract.get("policy") != POLICY:
        return []
    errors = []
    if contract.get("source_pack_sha256") != sha256_of(documents):
        errors.append("ARTICLE_READER_SOURCE_CHANGED")
    if contract.get("data_cutoff_utc") != source_clock(documents, {"headline_id": contract.get("primary_document_id")}):
        errors.append("ARTICLE_DATA_CLOCK_CHANGED")
    body = visible(article.get("substack_body_markdown"))
    text = "\n".join(visible(article.get(k)) for k in FIELDS)
    errors.extend(label_errors(text))
    first = next(iter(sentences(body)), "")
    if not re.match(r"^(?:We\b|Our\b)", first, re.I) or not re.search(
            r"\b(?:think|expect|see|favour|favor|prefer|lean|watch|remain|view|judge|look|would|are|stay|keep)\b", first, re.I):
        errors.append("FIRST_SENTENCE_OUR_CALL_REQUIRED")
    if len(re.findall(r"(?im)^#{1,6}\s+[^\n]*\bscenarios?\b[^\n]*$", body)) != 1:
        errors.append("SINGLE_SCENARIO_SET_REQUIRED")
    if not re.search(r"(?im)^(?:#{1,6}\s*)?So what\s*[:?]?\s*\S", body):
        errors.append("SO_WHAT_LINE_REQUIRED")
    for sentence in sentences(text):
        count = len(words(sentence))
        if count > MAX_SENTENCE_WORDS:
            errors.append("SENTENCE_TOO_LONG:" + str(count) + ":" + sentence[:90])
    docs = {d.get("source_id"): d for d in documents}
    all_numbers = set().union(*(numbers(d.get("canonical_content_text")) for d in documents)) if documents else set()
    for field in FIELDS:
        if field == "substack_body_markdown":
            continue
        errors.extend("NUMBER_NOT_IN_SOURCE:" + number for number in sorted(numbers(article.get(field)) - all_numbers))
    social_scenarios = article.get("social_scenarios") or {}
    if not isinstance(social_scenarios, dict):
        errors.append("SOCIAL_SCENARIOS_OBJECT_REQUIRED")
        social_scenarios = {}
    social = "\n".join(str(v) for k, v in article.items() if k.startswith("social_") and isinstance(v, str))
    social += "\n" + "\n".join(str(v) for v in social_scenarios.values())
    errors.extend(label_errors(social))
    errors.extend("NUMBER_NOT_IN_SOURCE:" + number for number in sorted(numbers(social) - all_numbers))
    for paragraph in re.split(r"\n\s*\n", str(article.get("substack_body_markdown") or "")):
        refs = MARKER.findall(paragraph)
        supported = set().union(*(numbers(docs[r].get("canonical_content_text")) for r in refs if r in docs)) if refs else all_numbers
        errors.extend("NUMBER_NOT_IN_BOUND_SOURCE:" + number for number in sorted(numbers(paragraph) - supported))
    scenario_section = re.search(r"(?im)^#{1,6}\s+[^\n]*\bscenarios?\b[^\n]*$", body)
    if scenario_section:
        scenario_copy = body[scenario_section.end():]
        level = len(re.match(r"#+", scenario_section[0])[0])
        following = re.search(r"(?m)^#{1," + str(level) + r"}\s+", scenario_copy)
        if following:
            scenario_copy = scenario_copy[:following.start()]
        scenarios = article.get("scenario_analysis") or []
        if not isinstance(scenarios, list) or any(not isinstance(s, dict) for s in scenarios):
            errors.append("SCENARIOS_REQUIRED")
            scenarios = []
        expected = Counter(str(s.get("probability") or "") for s in scenarios)
        actual = Counter(re.findall(r"(?<![\w.])\d+(?:\.\d+)?%", scenario_copy))
        for probability, count in expected.items():
            if probability and actual[probability] > count:
                errors.append("SINGLE_SCENARIO_SET_REQUIRED:" + probability)
    if contract.get("format") == "DAILY_NOTE":
        prose, table_errors = _daily_prose(body)
        errors.extend(table_errors)
        if len(words(prose)) > DAILY_WORDS:
            errors.append("DAILY_NOTE_TOO_LONG:" + str(len(words(prose))))
        for heading, reason in (("What changed since yesterday", "DAILY_CHANGE_SECTION_REQUIRED"),
                                ("What we got wrong", "DAILY_ERROR_SECTION_REQUIRED")):
            match = re.search(r"(?im)^#{1,6}\s+" + heading + r"\s*\n+([^#]+)", body)
            if not match or not words(match[1]):
                errors.append(reason)
    if contract.get("format") == "WEEKLY_REVIEW" and not any(d.get("weekly_scored_calls") for d in documents):
        errors.append("WEEKLY_CALL_RECORD_REQUIRED")
    return list(dict.fromkeys(errors))


def validate_article(article, documents):
    errors = check_article(article, documents)
    if errors:
        raise ValueError("; ".join(errors))


def validate_payload(article, payload):
    if (article.get("reader_article_contract") or {}).get("policy") != POLICY:
        return
    from live_contentops.article_scenarios_v1 import payload_text
    text = payload_text(payload)
    if isinstance(payload, dict):
        text += "\n" + str(payload.get("title") or "") + "\n" + str(payload.get("subtitle") or "")
        text += "\n" + str(payload.get("alt_text") or "")
    errors = label_errors(text)
    from live_contentops.v1_simple_gemini_newsroom_v1 import _public_copy
    errors.extend("NUMBER_NOT_IN_ARTICLE:" + value for value in sorted(numbers(text) - numbers(_public_copy(article))))
    if errors:
        raise ValueError("; ".join(errors))


def validate_publication_clock(article, *, now, destination):
    contract = article.get("reader_article_contract") or {}
    if contract.get("policy") != POLICY or destination != "substack":
        return
    cutoff = contract.get("data_cutoff_utc")
    if not cutoff:
        raise ValueError("ARTICLE_DATA_CUTOFF_NOT_SUPPLIED_BY_SOURCE")
    age = now.astimezone(timezone.utc) - utc(cutoff)
    if age < timedelta(0):
        raise ValueError("ARTICLE_DATA_CUTOFF_IN_FUTURE")
    if age > timedelta(minutes=DATA_TO_PUBLICATION_MINUTES):
        raise ValueError("ARTICLE_DATA_CUTOFF_EXPIRED:" + str(int(age.total_seconds())) + "s")


def publication_timing(article, *, published_at_utc):
    """Keep the observed publication separate from the source and dispatch clocks."""
    contract = article.get("reader_article_contract") or {}
    cutoff = contract.get("data_cutoff_utc")
    elapsed = (utc(published_at_utc) - utc(cutoff)).total_seconds() if cutoff and published_at_utc else None
    return {"policy": POLICY, "data_cutoff_utc": cutoff, "published_at_utc": published_at_utc,
            "seconds_from_data": elapsed, "within_60_minutes": 0 <= elapsed <= 3600 if elapsed is not None else None}
