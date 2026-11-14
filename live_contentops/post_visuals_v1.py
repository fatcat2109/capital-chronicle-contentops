"""CC-144 deterministic post visuals, inside the existing media/review owners.

No acquisition, model call, publisher, store or schedule lives here. Cards project
already validated article claims; the native final review still inspects the pixels.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import re

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of

POLICY = "CC144_EVERY_POST_VISUAL_V1"
# CC-267: the one card of a NEWS/POLICY post that has no admitted public fact to show.
TITLE_CARD = "CC267_TITLE_ONLY_NO_PUBLIC_FACT_V1"
DESTINATIONS = ("telegram", "discord", "x", "linkedin", "facebook_page",
                "instagram_business", "threads", "youtube")
_NUMBERS = re.compile(r"(?<!\w)[+-]?\d+(?:,\d{3})*(?:\.\d+)?%?")
_SURVEYS = re.compile(r"\b(?:ism|ismworld|s&p global|spglobal|pmi|conference[ -]board|umich|university of michigan|adp)\b", re.I)
# A title card shows no figures (decision 44 keeps private-survey figures off cards). Dates,
# period labels, maturities, times, ordinals and names that carry a number are not figures.
_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
_TITLE_KEEP = re.compile(
    r"\b(?:" + _MONTHS + r")(?:\s+\d{1,2}(?:st|nd|rd|th)?)?(?:,?\s+(?:19|20)\d{2})?(?!\w)"
    r"|\b(?:in|since|of|for|from|to|by|until|through|before|after)\s+(?:19|20)\d{2}(?![\w%]|[.,]\d)"
    r"|\b[QH][1-4](?:\s+(?:19|20)\d{2})?(?!\w)|\b\d{1,2}-(?:year|month|week|day)s?\b"
    r"|\b\d{1,2}:\d{2}(?:\s?[ap]\.?m\.?)?|\b\d+(?:st|nd|rd|th)\b|\b[A-Za-z]+-\d+\b"
    r"|\b(?:S&P|Nasdaq|Russell|FTSE|DAX|Nikkei|Stoxx|CAC|Hang Seng|ASX|KOSPI|Sensex|Nifty|Section|Title"
    r"|Article|Chapter|Rule|Form|Regulation|Executive Order)\s+\d+\b", re.I)
_FIGURE = (
    r"(?<![\w.])[-+−]?[$€£¥]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:bn|mn|tn|bps?|pp|pts?|[kmbx])?(?!\w)"
    r"(?:\s?(?:%|percent(?:age)?(?:\s+points?)?|pp|bps?|basis\s+points?|points?|pts|million|billion"
    r"|trillion|thousand)(?!\w))?"
    r"(?:\s+(?:annuali[sz]ed|year[- ]on[- ]year|y/y|m/m|month[- ]on[- ]month|a year (?:earlier|ago))(?!\w))?")
_QUALIFIER = r"(?:expected|forecasts?|consensus|est\.?|estimates?|estimated)"
# "54.8 vs 55.2 expected": the comparison goes whole, or "PMI expected" would change the meaning.
_TITLE_VERSUS = re.compile(r"\s*\b(?:vs\.?|versus|against|compared with)\s+" + _FIGURE
                           + r"(?:\s+" + _QUALIFIER + r"(?!\w))?", re.I)
_TITLE_FIGURE = re.compile(
    r"(?P<lead>\b(?:to|at|by|from|of|near|around|about|above|below|over|under|than)\s+)?" + _FIGURE, re.I)
# A figure that was the object of one of these verbs leaves the verb without its object.
_TRANSITIVE = frozenset((
    "hit hits reach reaches reached top tops topped total totals totaled totalled exceed exceeds exceeded "
    "surpass surpasses surpassed cross crosses crossed post posts posted add adds added shed sheds cut cuts "
    "lose loses lost record records recorded see sees saw show shows showed register registers registered "
    "print prints printed log logs logged notch notches notched mark marks marked approach approaches "
    "approached near nears neared eclipse eclipses eclipsed match matches matched beat beats miss misses missed"
).split())
_PREPOSITIONS = frozenset((
    "in on for during after amid as while with since from to at by of before despite under over through "
    "into ahead following"
).split())
_DANGLING = re.compile(r"\b(?:since|vs\.?|versus|than|from|to|at|by|of|above|below|near|around|about|over|under"
                       r"|between|and|or|with|as|the|a|an)\s*(?:[,.;:!?)]|$)", re.I)
_QUALIFIER_WORD = re.compile(r"\b(?:expected|forecasts?|consensus|estimates?)\b", re.I)
_QUALIFIER_OK_AFTER = frozenset((
    "than beat beats beating beaten miss misses missing missed above below top tops topping topped exceed "
    "exceeds exceeding exceeded over under with vs versus against of line ahead"
).split())
# The neutral title when no clean title or dek remains: "Challenger job cuts: October report".
_RELEASES = (
    (re.compile(r"\bChallenger\b", re.I), "Challenger job cuts"),
    (re.compile(r"\bADP\b"), "ADP private payrolls"),
    (re.compile(r"\bISM\b(?=.*\bservices\b)|\bservices\b(?=.*\bISM\b)", re.I), "ISM services PMI"),
    (re.compile(r"\bISM\b(?=.*\bmanufacturing\b)|\bmanufacturing\b(?=.*\bISM\b)", re.I), "ISM manufacturing PMI"),
    (re.compile(r"\bISM\b"), "ISM report"),
    (re.compile(r"\bS&P Global\b(?=.*\bservices\b)", re.I), "S&P Global services PMI"),
    (re.compile(r"\bS&P Global\b(?=.*\bmanufacturing\b)", re.I), "S&P Global manufacturing PMI"),
    (re.compile(r"\bS&P Global\b", re.I), "S&P Global PMI"),
    (re.compile(r"\bUMich\b|\bUniversity of Michigan\b|\bMichigan\b.*\bsentiment\b", re.I), "UMich consumer sentiment"),
    (re.compile(r"\bConference Board\b", re.I), "Conference Board consumer confidence"),
)


def _normal(value):
    return " ".join(str(value or "").split())


def reject_private_survey_visual(document, context=""):
    """Decision 44 applies even when another receipt admits factual paraphrase."""
    identity = " ".join(str(document.get(k) or "") for k in (
        "publisher", "source_url", "url", "source_adapter_family", "title"))
    if _SURVEYS.search(identity + " " + context) or document.get("private_survey") is True:
        raise ValueError("PRIVATE_SURVEY_HEADLINE_ONLY_NO_VISUAL")


def public_visual_source(document):
    reject_private_survey_visual(document)
    from live_contentops.event_public_record_v1 import verified_main_research_excerpts
    if verified_main_research_excerpts(document):
        return "capital_chronicle_own_report"
    desk = document.get("desk_record_binding") or {}
    sources = desk.get("sources") or []
    if (sources and all(s.get("rights_class") == "BLS_OFFICIAL_PUBLIC_DERIVED"
            and str(s.get("url") or "").startswith("https://www.bls.gov/")
            and re.fullmatch(r"[a-f0-9]{64}", str(s.get("raw_sha256") or "")) for s in sources)):
        return "public_domain"
    constraints = document.get("source_reuse_constraints") or {}
    lineage = document.get("report_lineage") or {}
    digest = lineage.get("report_projection_sha256")
    if (constraints.get("scope") == "CAPITAL_CHRONICLE_OWN_REPORT_PUBLIC_EXCERPTS"
            and constraints.get("authority_ref") == "JIM_DECISION_89"
            and document.get("source_authority_class") == "governed_capital_chronicle_report_only"
            and re.fullmatch(r"[a-f0-9]{64}", str(digest or ""))
            and constraints.get("source_capture_sha256") == digest
            and (document.get("url") or document.get("source_url")) == "urn:cc-public-report:main-retained:" + digest):
        return "capital_chronicle_own_report"
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _underlying_source_rights
    rights, _ = _underlying_source_rights(document)
    if rights == "public_domain" and document.get("rights_evidence_sha256"):
        return "public_domain"
    if (constraints.get("scope") in {"ATTRIBUTED_REPORTED_FACTS_ONLY_INDEPENDENT_PUBLIC_PARAPHRASE",
            "ATTRIBUTED_ORIGINAL_FACTS_ONLY_INDEPENDENT_PUBLIC_PARAPHRASE",
            "ATTRIBUTED_FILING_FACTS_ONLY_INDEPENDENT_PUBLIC_PARAPHRASE"}
            and constraints.get("attribution_required") is True
            and constraints.get("policy_capture_sha256") and constraints.get("source_capture_sha256")):
        return "attributed_facts_independent_chart"
    raise ValueError("DATA_CARD_PUBLIC_RIGHTS_REQUIRED")


def _bound_fact(claim, article, documents):
    source = next((d for d in documents if d.get("source_id") == claim.get("source_id")), None)
    if not source or not claim.get("source_id"):
        raise ValueError("DATA_CARD_FACT_SOURCE_REQUIRED")
    rights = public_visual_source(source)
    text, excerpt = _normal(claim.get("claim_text")), _normal(claim.get("support_excerpt"))
    reject_private_survey_visual(source, text + " " + excerpt)
    body = _normal(" ".join(str(article.get(k) or "") for k in (
        "title", "dek", "substack_body_markdown", "social_hook", "search_title", "seo_title", "meta_description")))
    canonical = str(source.get("canonical_content_text") or "")
    allowed_numbers = set(_NUMBERS.findall(_normal(canonical)))
    for field in (source.get("desk_record_binding") or {}).get("fields", []):
        value = str(field.get("value") or "")
        if field.get("citation") in excerpt and value in canonical and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", value):
            from live_contentops.public_time_v1 import public_timestamp
            allowed_numbers.update(_NUMBERS.findall(public_timestamp(value)))
    if (not text or not excerpt or text not in body or excerpt not in _normal(canonical)
            or not set(_NUMBERS.findall(text)) <= allowed_numbers):
        raise ValueError("DATA_CARD_FACT_OR_NUMBER_NOT_IN_POST_AND_SOURCE")
    url = source.get("url") or source.get("source_url")
    publisher = source.get("publisher")
    desk_sources = (source.get("desk_record_binding") or {}).get("sources") or []
    if rights == "public_domain" and not str(url or "").startswith("https://") and desk_sources:
        url, publisher = desk_sources[0]["url"], desk_sources[0]["provider"]
    if (not str(url or "").startswith("https://") and rights != "capital_chronicle_own_report") or not source.get("publisher"):
        raise ValueError("DATA_CARD_PUBLIC_ATTRIBUTION_REQUIRED")
    return {"claim_id": claim.get("claim_id"), "text": text, "source_id": claim["source_id"],
        "document_id": source["document_id"], "support_excerpt": claim["support_excerpt"],
        "source_content_sha256": sha256(canonical.encode()).hexdigest(), "rights_class": rights,
        "rights_binding_sha256": sha256_of({k: source.get(k) for k in (
            "underlying_reuse_classification", "rights_evidence_sha256", "source_reuse_constraints")}),
        "publisher": publisher, "url": url}


def _render_card(packet, path, mini_chart=None):
    """CC-245: the data card in the site design, Instagram's 1080x1350 portrait size.

    The facts stay verbatim with their publishers; the key figure is an exact substring
    of a fact. A card that cannot show every fact whole raises the layout error, so the
    builder drops the last fact and renders again (no cut claim is ever posted).
    """
    from live_contentops.fact_card_design_v1 import CardSpec, INSTAGRAM_SIZE, key_from_facts, render_fact_card
    display = packet.get("editorial_display") or {}
    labels = display.get("fact_labels") or []
    facts = [(labels[i] if i < len(labels) else
              "From the dated review" if fact.get("rights_class") == "capital_chronicle_own_report" else "Reported fact",
              re.sub(r"\*\*([^*]+)\*\*", r"\1", fact["text"]))
        for i, fact in enumerate(packet["facts"])]
    publishers = list(dict.fromkeys(fact["publisher"] for fact in packet["facts"]))
    key_label, key_value = ("", "") if mini_chart else key_from_facts(facts)
    if display:
        key_label, key_value = display["key_label"], display["key_value"]
    if all(fact.get("rights_class") == "capital_chronicle_own_report" for fact in packet["facts"]):
        from live_contentops.fact_card_design_v1 import full_number_text, main_review_figure
        # Display formatting only: the packet retains the admitted source words.
        # A Main review leads with its count, rather than a period or compact suffix.
        figure_label, figure_value = main_review_figure(facts)
        if figure_value:
            key_label, key_value = figure_label, full_number_text(figure_value)
        else:
            key_value = full_number_text(key_value)
        facts = [(label, full_number_text(text)) for label, text in facts]
    spec = CardSpec(title=display.get("title") or packet.get("title") or "Key facts", facts=facts,
        kicker=display.get("kicker") or " · ".join(publishers),
        key_label=key_label, key_value=key_value,
        source_line=packet.get("source_line") or "Source: " + ", ".join(publishers),
        dated_line=packet.get("dated_line") or "Capital Chronicle", image_path=str(mini_chart or ""),
        chart=packet.get("series_asset") if mini_chart else None)  # CC-290: drawn for its slot, legible
    result = render_fact_card(path, spec, size=INSTAGRAM_SIZE)
    # Readable on a phone: every fact whole, at 28px or more on the 1080px card.
    if result["facts_shown"] < result["facts_given"] or (result["facts_size"] or 0) < 28:
        raise ValueError("DATA_CARD_CONTENT_EXCEEDS_READABLE_LAYOUT")
    return INSTAGRAM_SIZE


def _validate_card_series(packet, article, documents):
    ids = {v["document_id"] for s in packet["series"] for p in s["points"] for v in p["inputs"]}
    if not ids <= {d.get("document_id") for d in documents}:
        raise ValueError("DATA_CARD_SERIES_SOURCE_REQUIRED")
    for document in documents:
        if document.get("document_id") in ids and public_visual_source(document) != "public_domain":
            raise ValueError("DATA_CARD_HISTORY_REQUIRES_PUBLIC_DOMAIN_SERIES")
    body_numbers = set(_NUMBERS.findall(_normal(article.get("substack_body_markdown"))))
    for series in packet["series"]:
        for point in series["points"]:
            if not set(_NUMBERS.findall(str(point["value"]))) <= body_numbers:
                raise ValueError("DATA_CARD_SERIES_NUMBER_NOT_IN_POST")


def _prose_sentences(article, claim):
    """The post's own sentences that state every figure of ``claim``, in reading order.

    A card fact worded apart from the post binds to the post's sentence carrying the same
    figures, so a card is built only from the canonical prose (CC-290, IBM 5 Nov)."""
    figures = set(_NUMBERS.findall(_normal(claim.get("claim_text"))))
    if not figures:
        return []
    prose = re.sub(r"\[\[[A-Z_]+:[^\]]*\]\]", " ", str(article.get("substack_body_markdown") or ""))
    found = []
    for paragraph in re.split(r"\n\s*\n", prose):
        if paragraph.lstrip().startswith(("#", "![")):
            continue
        for sentence in re.split(r"(?<=[a-z0-9%)\"\u201d\u2019]{2}[.!?])\s+(?=[A-Z0-9\"\u201c(])", _normal(paragraph)):
            if figures <= set(_NUMBERS.findall(sentence)):
                found.append(sentence)
    return found


def build_post_data_card(article, claims, documents, *, output_dir, series_packet=None):
    """Render only admitted claims present in this post. No number extraction guesses."""
    facts, seen = [], set()
    body = _normal(article.get("substack_body_markdown"))
    for claim in claims:
        text = _normal(claim.get("claim_text"))
        if not text or text in seen or len(text) > 280:
            continue
        # CC-290 (IBM, 5 Nov): the claim's own words if the post contains them, else the
        # post's own sentence stating its figures; post_image_view admits exactly these.
        fact, candidates = None, [text]
        while candidates:
            candidate = candidates.pop(0)
            try:
                fact = _bound_fact({**claim, "claim_text": candidate}, article, documents)
                break
            except ValueError as exc:
                if str(exc) in {"PRIVATE_SURVEY_HEADLINE_ONLY_NO_VISUAL", "DATA_CARD_PUBLIC_RIGHTS_REQUIRED"}:
                    break
                if str(exc) != "DATA_CARD_FACT_OR_NUMBER_NOT_IN_POST_AND_SOURCE":
                    raise
                if candidate == text:
                    candidates = [s for s in _prose_sentences(article, claim)
                                  if s != text and s not in seen and len(s) <= 280]
        if fact:
            facts.append(fact)
            seen.add(fact["text"])
    # Validate every candidate before selection. Prefer the article's actual
    # paragraphs to SEO/title variants that would repeat the same fact.
    body_facts = [f for f in facts if f["text"] in body]
    facts = (body_facts or facts)[:1 if series_packet else 3]
    if not facts:
        raise ValueError("DATA_CARD_NO_ADMITTED_PUBLIC_VISUAL_FACTS")
    from live_contentops.fact_card_design_v1 import DESIGN, piece_dated_line
    # The design, title and piece date are part of the packet, so a new render never
    # reuses the path of a card already sent in the older layout.
    packet = {"policy": POLICY, "facts": facts, "design": DESIGN,
              "text_presentation": "PLAIN_EMPHASIS_AND_DATED_REVIEW_ATTRIBUTION_V1",
              "title": str(article.get("title") or "Key facts"), "dated_line": piece_dated_line(article)}
    if all(f["rights_class"] == "capital_chronicle_own_report" for f in facts):
        packet["text_presentation"] = "CC333_MAIN_REVIEW_FULL_FIGURE_V1"
        from live_contentops.public_time_v1 import public_date
        source_ids = {f["document_id"] for f in facts}
        dates = {public_date(d["published_at_utc"]) for d in documents
                 if d.get("document_id") in source_ids and d.get("published_at_utc")}
        if len(dates) == 1:
            packet["source_line"] = "Source: Capital Chronicle review, " + dates.pop() + " (ET)."
        event = article.get("event_article_packet") or {}
        if article.get("article_type") == "EVENT_REVIEW" and event.get("event_time_utc"):
            packet["source_line"] = "Source: Capital Chronicle; event dated " + public_date(event["event_time_utc"]) + " (ET)."
    display = (article.get("visual_editorial_decision") or {}).get("post_data_card_plan") or {}
    if display and [f.get("text") for f in display.get("facts", [])] == [f["text"] for f in facts]:
        packet["editorial_display"] = {k: str(display.get(k) or "") for k in (
            "title", "kicker", "key_label", "key_value")}
        packet["editorial_display"]["fact_labels"] = [str(f.get("label") or "Reported fact") for f in display["facts"]]
    mini = None
    if series_packet:
        from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_editorial_data_chart
        _validate_card_series(series_packet, article, documents)
        mini = build_editorial_data_chart(series_packet, documents, output_dir=output_dir)
        packet["series_asset"] = mini
    while True:
        digest = sha256_of(packet)
        asset_id = "post-facts-" + digest[:20]
        path = Path(output_dir).resolve() / "media_assets" / (asset_id + ".png")
        try:
            width, height = _render_card(packet, path, mini["path"] if mini else None)
            break
        except ValueError as exc:
            if str(exc) != "DATA_CARD_CONTENT_EXCEEDS_READABLE_LAYOUT" or len(facts) == 1:
                raise
            facts.pop()  # Keep complete claims and readable type inside Instagram's 4:5 limit.
    path.with_suffix(".json").write_bytes(canonical_bytes(packet))
    return {"asset_id": asset_id, "path": str(path), "sha256": sha256(path.read_bytes()).hexdigest(),
        "width": width, "height": height, "modality": "source_bound_data_card",
        "role": "supporting_fact_context", "media_role": "post_key_facts", "caption": "Key facts from the article.",
        "alt_text": " ".join(f["text"] for f in facts),
        "attribution": "Source: " + ", ".join(dict.fromkeys(f["publisher"] for f in facts)),
        "source_page_url": facts[0]["url"],
        "source_links": [{"document_id": f["document_id"], "url": f["url"], "label": f["publisher"]} for f in facts],
        "source_lineage": [{"document_id": f["document_id"], "source_url": f["url"]} for f in facts],
        "underlying_source_rights_status": "attributed_facts_independent_chart",
        "data_card_packet": packet, "transform_sha256": digest,
        "publication_authority": False}


def _protect(text):
    kept = []

    def keep(match):
        kept.append(match.group(0))
        return chr(0xE000 + len(kept) - 1)

    return _TITLE_KEEP.sub(keep, _normal(text)), kept


def _restore(value, kept):
    for index, original in enumerate(kept):
        value = value.replace(chr(0xE000 + index), original)
    return value


def _tidy(value):
    value = re.sub(r"\(\s*(?:expected|forecasts?|consensus|est\.?|estimates?|prior|previous)?\s*\)", "", value, flags=re.I)
    value = re.sub(r"\s+([,.;:!?])", r"\1", value)
    value = re.sub(r"([,;:])(?=\s*(?:[,;:.!?]|$))", "", value)
    value = re.sub(r"\s{2,}", " ", value).strip(" ,;:-–—")
    value = re.sub(r"(?:\s+(?:to|at|by|from|of|and|or|vs\.?|versus|with|than|as))+$", "", value, flags=re.I)
    return value.strip(" ,;:-–—")


def _capital(value):
    return value[:1].upper() + value[1:]


def _lone_qualifier(value):
    """'PMI expected' changed the meaning; 'beating forecast' or 'than expected' did not."""
    for match in _QUALIFIER_WORD.finditer(value):
        before = value[:match.start()].split()
        if not before or before[-1].casefold().strip(",;:(") not in _QUALIFIER_OK_AFTER:
            return True
    return False


def _reads_cleanly(value):
    return len(value.split()) >= 3 and not _DANGLING.search(value) and not _lone_qualifier(value)


def _strip_title_figures(text):
    """(text without figures, whether it still reads cleanly). Unchanged text is clean."""
    original = _normal(text)
    value, kept = _protect(original)
    value = _TITLE_VERSUS.sub("", value)
    broken = []

    def drop(match):
        if not match.group("lead"):
            clause = re.split(r"[,;:(]", match.string[:match.start()])[-1].split()
            after = match.string[match.end():].lstrip()
            following = re.match(r"[A-Za-z']+|[,.;:!?)]|$", after).group(0).casefold()
            ends_clause = not following.isalpha()
            if clause and clause[-1].casefold() in _TRANSITIVE and (ends_clause or following in _PREPOSITIONS):
                broken.append("VERB_LOST_ITS_OBJECT")
            if len(clause) == 1 and ends_clause:
                broken.append("ONE_WORD_CLAUSE")
        return ""

    value = _capital(_restore(_tidy(_TITLE_FIGURE.sub(drop, value)), kept))
    if value == original:
        return value, True
    return value, not broken and _reads_cleanly(value)


def _leading_clause(text):
    """The title before its first figure, when that part reads cleanly on its own."""
    value, kept = _protect(text)
    first = min((m.start() for m in (_TITLE_VERSUS.search(value), _TITLE_FIGURE.search(value)) if m), default=None)
    if first is None:
        return None
    head = _capital(_restore(_tidy(value[:first]), kept))
    # 'US layoffs hit' ends on a verb whose object was the figure.
    if not _reads_cleanly(head) or head.split()[-1].casefold().strip(",;:.") in _TRANSITIVE:
        return None
    return head


def _neutral_release_title(article):
    text = " ".join(_normal(article.get(k)) for k in ("title", "dek"))
    name = next((label for pattern, label in _RELEASES if pattern.search(text)), None)
    month = re.search(r"\bin (" + _MONTHS + r")\b", text) or re.search(r"\b(" + _MONTHS + r")\b", text)
    if not name:
        return "Capital Chronicle news brief"
    return f"{name}: {month.group(1)} report" if month else f"{name}: latest report"


def card_title(article):
    """CC-267: the card's title, never a phrase whose meaning changed or whose grammar broke.

    The published title without its figures when it still reads cleanly ('ISM services index
    rises to 52.4 as prices paid climb' -> 'ISM services index rises as prices paid climb');
    otherwise the clean leading clause, the dek without figures, or a neutral release title
    such as 'Challenger job cuts: October report'. Dates and named numbers stay.
    """
    title, clean = _strip_title_figures(article.get("title"))
    if title and clean:
        return title
    lead = _leading_clause(article.get("title"))
    if lead:
        return lead
    dek, clean = _strip_title_figures(article.get("dek"))
    if clean and len(dek.split()) >= 3:
        return dek
    return _neutral_release_title(article)


def title_card_packet(article):
    """The packet a title card renders: the card title (no figures) and the piece's date only."""
    from live_contentops.fact_card_design_v1 import DESIGN, piece_dated_line
    return {"policy": POLICY, "kind": TITLE_CARD, "facts": [], "design": DESIGN, "title": card_title(article),
            "dated_line": piece_dated_line(article)}


def build_post_title_card(article, claims, documents, *, output_dir, reason=""):
    """CC-267: a NEWS/POLICY post with no admitted public fact still carries one card.

    The CC-245 design with the piece's title, figures removed, and its dated line. It draws
    no fact, figure or source text, so decisions 42 (an image on every post) and 44 (no
    private-survey figure on a card) both hold. The lineage names the post's own sources.
    """
    from live_contentops.fact_card_design_v1 import CardSpec, INSTAGRAM_SIZE, render_fact_card
    packet = title_card_packet(article)
    digest = sha256_of(packet)
    asset_id = "post-title-" + digest[:20]
    path = Path(output_dir).resolve() / "media_assets" / (asset_id + ".png")
    render_fact_card(path, CardSpec(title=packet["title"], dated_line=packet["dated_line"]), size=INSTAGRAM_SIZE)
    path.with_suffix(".json").write_bytes(canonical_bytes(packet))
    cited = {c.get("source_id") for c in claims or []}
    sources = [d for d in documents or [] if str(d.get("url") or d.get("source_url") or "").startswith("https://")]
    sources = [d for d in sources if d.get("source_id") in cited] or sources
    lineage = [{"document_id": d.get("document_id"), "source_url": d.get("url") or d.get("source_url")}
               for d in sources]
    width, height = INSTAGRAM_SIZE
    return {"asset_id": asset_id, "path": str(path), "sha256": sha256(path.read_bytes()).hexdigest(),
        "width": width, "height": height, "modality": "source_bound_data_card", "card_kind": "TITLE_ONLY",
        "role": "supporting_fact_context", "media_role": "post_key_facts", "caption": packet["title"],
        "alt_text": packet["title"] + ". " + packet["dated_line"], "attribution": "Capital Chronicle",
        "source_page_url": (lineage[0]["source_url"] if lineage
                            else str(article.get("canonical_url") or "https://capitalchronicle.substack.com/")),
        "source_links": [], "source_lineage": lineage,
        "underlying_source_rights_status": "attributed_facts_independent_chart",
        "data_card_packet": packet, "transform_sha256": digest, "title_card_reason": str(reason or ""),
        "publication_authority": False}


def validate_post_data_card(asset, article, documents):
    packet = asset.get("data_card_packet") or {}
    if packet.get("kind") == TITLE_CARD:
        # CC-267: no fact to recheck; the card must show this article's title, figure-free.
        expected = title_card_packet(article)
        if ({k: v for k, v in packet.items() if k != "dated_line"} != {k: v for k, v in expected.items() if k != "dated_line"}
                or not str(packet.get("dated_line") or "").startswith("Capital Chronicle")):
            raise ValueError("DATA_CARD_TITLE_CARD_CHANGED")
        if (sha256_of(packet) != asset.get("transform_sha256")
                or sha256(Path(asset["path"]).read_bytes()).hexdigest() != asset.get("sha256")):
            raise ValueError("DATA_CARD_PACKET_OR_BYTES_CHANGED")
        return
    if packet.get("policy") != POLICY or not 1 <= len(packet.get("facts", [])) <= 3:
        raise ValueError("DATA_CARD_PACKET_REQUIRED")
    for fact in packet["facts"]:
        rebound = _bound_fact({"claim_id": fact["claim_id"], "claim_text": fact["text"],
            "source_id": fact["source_id"], "support_excerpt": fact["support_excerpt"]}, article, documents)
        if fact != rebound:
            raise ValueError("DATA_CARD_SOURCE_OR_RIGHTS_CHANGED")
    if packet.get("series_asset"):
        from live_contentops.rolling_x_grounded_article_media_builder_v1 import validate_editorial_data_chart
        _validate_card_series(packet["series_asset"]["editorial_data_packet"], article, documents)
        validate_editorial_data_chart(packet["series_asset"], documents)
    if (sha256_of(packet) != asset.get("transform_sha256")
            or sha256(Path(asset["path"]).read_bytes()).hexdigest() != asset.get("sha256")):
        raise ValueError("DATA_CARD_PACKET_OR_BYTES_CHANGED")


def complete_post_visuals(article, claims, documents, assets, *, output_dir):
    """Run before previews/review; never mutate a prepared or sent package."""
    article = dict(article)
    assets = list(assets)
    decision = article.get("visual_editorial_decision") or {}
    if decision.get("story_kind") != "ANALYSIS":
        series = decision.get("data_card_series")
        try:
            card = build_post_data_card(article, claims, documents, output_dir=output_dir, series_packet=series)
        except ValueError as exc:
            # CC-267: a missing card never stops the run. A rejected series falls back to the
            # facts alone; no admitted public fact (e.g. private surveys) gives the title card.
            card = None
            if series:
                try:
                    card = build_post_data_card(article, claims, documents, output_dir=output_dir)
                    card["series_dropped_reason"] = str(exc)
                except ValueError:
                    card = None
            if card is None:
                card = build_post_title_card(article, claims, documents, output_dir=output_dir, reason=str(exc))
        assets.append(card)
    if not assets:
        raise ValueError("EVERY_POST_IMAGE_REQUIRED")
    fallback = next((a["asset_id"] for a in assets if a.get("modality") == "source_bound_data_card"), assets[0]["asset_id"])
    choices = decision.get("channel_media") or {}
    article["post_visual_policy"] = POLICY
    article["post_visual_destination_media"] = {d: list(choices.get(d) or [fallback]) for d in DESTINATIONS}
    return article, assets


def require_publication_image(destination, data):
    """One pre-send check across Neo and API transports. Readback never calls it."""
    assets = data.get("media_assets") or []
    if destination != "substack":
        payload = data.get("payloads", {}).get(destination) or {}
        selected = set(payload.get("media_asset_ids") or [])
        selected.update(a for post in payload.get("posts") or [] for a in post.get("media_asset_ids") or [])
        assets = [a for a in assets if a.get("asset_id") in selected]
    if not assets:
        from .publication_image_contract_v1 import bounded_text_fallback
        if destination != "instagram_business" and bounded_text_fallback(
                data.get("article") or {}, data.get("output_dir") or ""):
            return
        raise ValueError("EVERY_POST_IMAGE_REQUIRED:" + destination)
    from PIL import Image
    for asset in assets:
        path = Path(asset.get("path") or asset.get("absolute_local_source_path") or "")
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != asset.get("sha256"):
            raise ValueError("PUBLICATION_IMAGE_BYTES_CHANGED:" + destination)
        with Image.open(path) as pixels:
            if pixels.format not in {"PNG", "JPEG", "WEBP"}:
                raise ValueError("PUBLICATION_IMAGE_FORMAT_UNSUPPORTED:" + destination)
            pixels.verify()
    if destination in {"facebook_page", "instagram_business", "threads"}:
        primary = data.get("primary_media") or {}
        if (not str(data.get("public_image_url") or "").startswith("https://")
                or primary.get("sha256") not in {a["sha256"] for a in assets}
                or primary.get("local_public_hash_continuity") is not True
                or primary.get("public_delivery_sha256") != primary.get("sha256")):
            raise ValueError("SELECTED_IMAGE_PUBLIC_DELIVERY_REQUIRED:" + destination)
