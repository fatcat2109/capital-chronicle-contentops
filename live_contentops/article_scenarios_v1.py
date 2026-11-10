"""Decision 93: use Main's scenarios and retain them in every published copy."""
from __future__ import annotations

from hashlib import sha256
import re

from .event_article_guard_v1 import PUBLIC_NOTICE, CONFLICTS_NOTICE

MARKETS = ("XAUUSD", "US500", "EURUSD", "USDJPY", "USOIL", "BTCUSD")
MODEL_LABEL = "Capital Chronicle model estimate"
NOTICES = (PUBLIC_NOTICE, CONFLICTS_NOTICE)
PREPARATION_GUIDANCE = (
    "JIM DECISION 93 PREPARATION: prepare the held full Main reports/dossiers for 2-3 scenarios, "
    "including each supplied probability, confirmation, six-market implications and invalidation. "
    "Retain exact document ids and source spans; never invent or complement a probability. "
    "Search held reports and other lane outputs before naming a missing field. Identify the lead "
    "market for CC-316's fresh TradingView snapshot; event pieces keep a release card first. "
    "Other pieces need their own data chart or an unused lawful photo. The MAX writer owns all "
    "article and social prose. Two articles per existing production day is a ceiling, not a quota."
)
WRITER_GUIDANCE = """JIM DECISION 93 — applies to every new article, including events.
Write a Scenarios section with 2-3 scenarios from the held Main reports. Never invent
or complement a probability. Each has a labelled Capital Chronicle model estimate
probability, confirmation, implications for XAUUSD, US500, EURUSD, USDJPY, USOIL and
BTCUSD, and invalidation. Use the held full dossier/report where the selected excerpt
is too narrow. Search retained Main/desk records before declaring a field absent.
Supply article.scenario_analysis: a list of {name, role: base_case|alternative,
probability: '<exact supplied percentage>', confirmation, market_moves: {<each of
the six asset ids>: '<Main implication>'}, invalidation, source_bindings: {<field>:
{document_id, support_excerpt}}}. Bind probability, confirmation, invalidation and
each market_moves.<asset> to exact Main text in the supplied source documents; each
field's value occurs verbatim in its support_excerpt. Print these fields in the
Scenarios section. Add article.social_scenarios {base_case, alternative}: two short
authored lines beginning 'Base case:' and 'Alternative:', each retaining its exact
scenario probability. The compiler carries both lines to all social destinations.
Keep decision 40's notices, decision 84's ban on alpha/track-record claims and ET times.
Every piece needs a never-published image. Six-market reviews set article.market_asset
to their lead market before registration and use its fresh TradingView snapshot;
event releases keep their release card first and add their market snapshot. Others
use their own data chart or an unused lawful photo. Do not reuse the Fed or Capitol
photos. At most two articles per production day, including event articles.
"""


def _normal(value):
    return " ".join(re.sub(r"[*_`#]", "", str(value)).split()).casefold()


def payload_text(payload):
    if isinstance(payload, str):
        return payload
    if not isinstance(payload, dict):
        return ""
    # Do not count metadata, alt text or an unused summary as delivered copy.
    posts = payload.get("posts") or []
    if posts:
        return "\n".join(str(p.get("text") or "") for p in posts if isinstance(p, dict))
    return "\n".join(str(payload.get(k) or "") for k in ("text", "caption", "body_markdown", "full_text"))


def validate_article_scenarios(article, documents):
    scenarios = article.get("scenario_analysis")
    if not isinstance(scenarios, list) or not 2 <= len(scenarios) <= 3:
        raise ValueError("SCENARIOS_REQUIRED")
    if not all(isinstance(scenario, dict) for scenario in scenarios):
        raise ValueError("SCENARIOS_REQUIRED")
    roles = [s.get("role") for s in scenarios]
    if roles.count("base_case") != 1 or any(r not in {"base_case", "alternative"} for r in roles):
        raise ValueError("SCENARIO_BASE_AND_ALTERNATIVE_REQUIRED")
    body = article.get("substack_body_markdown") or ""
    section = re.search(r"(?im)^#{1,6}\s+[^\n]*scenarios?[^\n]*\n", body)
    if not section:
        raise ValueError("SCENARIOS_SECTION_REQUIRED")
    visible = _normal(body[section.end():])
    docs = {d.get("document_id"): d for d in documents}
    for scenario in scenarios:
        probability = scenario.get("probability")
        if not isinstance(probability, str) or not re.fullmatch(r"(?:100|\d{1,2})(?:\.\d+)?%", probability):
            raise ValueError("SCENARIO_PROBABILITY_REQUIRED")
        if not 0 <= float(probability[:-1]) <= 100:
            raise ValueError("SCENARIO_PROBABILITY_REQUIRED")
        moves = scenario.get("market_moves") or {}
        if set(moves) != set(MARKETS):
            raise ValueError("SCENARIO_SIX_MARKETS_REQUIRED")
        values = {k: scenario.get(k) for k in ("probability", "confirmation", "invalidation")}
        values.update({"market_moves." + market: moves[market] for market in MARKETS})
        if not scenario.get("name") or _normal(scenario["name"]) not in visible:
            raise ValueError("SCENARIO_NOT_IN_ARTICLE")
        for field, value in values.items():
            binding = (scenario.get("source_bindings") or {}).get(field) or {}
            doc = docs.get(binding.get("document_id")) or {}
            text = doc.get("canonical_content_text") or ""
            excerpt = binding.get("support_excerpt") or ""
            main = (doc.get("desk_record_binding") or
                    "capital chronicle" in str(doc.get("publisher") or "").casefold())
            if (not main or not text or not isinstance(value, str) or not value.strip()
                    or not excerpt or excerpt not in text or value not in excerpt
                    or (doc.get("canonical_content_sha256") and
                        sha256(text.encode()).hexdigest() != doc["canonical_content_sha256"])):
                raise ValueError("SCENARIO_MAIN_SOURCE_BINDING_REQUIRED")
            if field == "probability" and not re.search(r"(?<![\d.,])" + re.escape(value) + r"(?![\d%])", excerpt):
                raise ValueError("SCENARIO_MAIN_SOURCE_BINDING_REQUIRED")
            if _normal(value) not in visible:
                raise ValueError("SCENARIO_NOT_IN_ARTICLE")
        if _normal(MODEL_LABEL) not in visible:
            raise ValueError("SCENARIO_MODEL_ESTIMATE_LABEL_REQUIRED")
    if (_normal(PUBLIC_NOTICE) not in _normal(body)
            or _normal(CONFLICTS_NOTICE) not in _normal(body)):
        raise ValueError("SCENARIO_NOTICES_REQUIRED")
    social = article.get("social_scenarios") or {}
    base = next(s for s in scenarios if s["role"] == "base_case")
    alternative = next(s for s in scenarios if s["role"] == "alternative")
    for key, prefix, scenario in (("base_case", "Base case:", base), ("alternative", "Alternative:", alternative)):
        text = social.get(key)
        if (not isinstance(text, str) or not text.startswith(prefix) or "\n" in text
                or scenario["probability"] not in text):
            raise ValueError("SOCIAL_SCENARIOS_REQUIRED")
        from live_contentops.event_article_guard_v1 import NAMED_NUMBER
        source_text = " ".join([scenario["probability"], scenario["confirmation"], scenario["invalidation"],
                                *scenario["market_moves"].values()])
        number = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)*%?")
        if set(number.findall(NAMED_NUMBER.sub(" ", text))) - set(number.findall(NAMED_NUMBER.sub(" ", source_text))):
            raise ValueError("SCENARIO_SOCIAL_NUMBER_UNBOUND")
    return social


def validate_social_scenarios(article, payload):
    social = article.get("social_scenarios") or {}
    copies = [payload_text(payload)]
    if isinstance(payload, dict) and not payload.get("posts"):
        copies = [str(payload[k]) for k in ("text", "caption", "body_markdown", "full_text") if payload.get(k)] or [""]
    for copy in copies:
        visible = _normal(copy)
        if any(not social.get(k) or _normal(social[k]) not in visible for k in ("base_case", "alternative")):
            raise ValueError("SOCIAL_SCENARIOS_REQUIRED")


def include_social_scenarios(payloads, article):
    """Carry authored scenario lines; formatting never invents a scenario or probability."""
    social = article.get("social_scenarios") or {}
    lines = [social.get(k) for k in ("base_case", "alternative")]
    if not all(isinstance(line, str) and line.strip() for line in lines):
        return payloads  # final coordinator check names the absent fields before a write
    for destination, payload in payloads.items():
        if payload.get("posts"):
            missing = [line for line in lines if _normal(line) not in _normal(payload_text(payload))]
            suffix = "\n".join(missing)
            limit = int(payload.get("platform_limit") or (280 if destination == "x" else 500 if destination == "threads" else 0))
            tail = payload["posts"][-1]
            if suffix and (not limit or len(tail["text"] + "\n\n" + suffix) <= limit):
                tail["text"] += "\n\n" + suffix
            elif suffix:
                from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _split_complete_chunks
                chunks = [suffix] if len(suffix) <= limit else _split_complete_chunks(missing, limit=limit)
                payload["posts"].extend({"text": text, "media_asset_ids": [], "role": "reply",
                                         "order": len(payload["posts"]) + index} for index, text in enumerate(chunks))
            payload["full_text"] = "\n\n".join(p["text"] for p in payload["posts"])
        else:
            fields = [k for k in ("text", "full_text", "caption", "root_text") if k in payload] or ["text"]
            for field in fields:
                existing = str(payload.get(field) or "")
                suffix = "\n".join(line for line in lines if _normal(line) not in _normal(existing))
                if suffix:
                    payload[field] = existing + "\n\n" + suffix
    return payloads
