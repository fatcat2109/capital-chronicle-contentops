"""CC-425: carry Data's CPI tables through the existing article consumer.

The writer supplies the argument. Structured tables retain the producer's cells;
this module computes no return, surprise, forecast or outcome and sends no post.
"""
from __future__ import annotations

import hashlib
import re
from collections import Counter

RECORD_ID = "report:cc-cpi-reactions-since-2024"
TOKEN = "[[CPI_REACTION_TABLES]]"
POLICY = "CC425_CPI_REACTION_PAGE_V1"
TITLE = "What gold, the euro and the S&P did after each CPI since 2024"

# CC-468 extends the same table consumer. CPI's issued projection and policy
# retain their exact shape; new families carry their own source identity.
EVENT_PAGES = {
    "CPI": {"record_id": RECORD_ID, "title": TITLE},
    "NFP": {"record_id": "report:cc-nfp-reactions-since-2024",
            "title": "What gold, the euro and the S&P did after each payrolls release"},
    "FOMC": {"record_id": "report:cc-fomc-reactions-since-2024",
             "title": "What gold, the euro and the S&P did after each Fed decision"},
    "PPI": {"record_id": "report:cc-ppi-reactions-since-2024",
            "title": "What gold, the euro and the S&P did after each PPI release"},
}


def event_family(record_id):
    return next((family for family, spec in EVENT_PAGES.items()
                 if spec["record_id"] == record_id), None)

# Reader names only. Exact vendor instruments remain in the source binding.
LABELS = {
    "YAHOO_FINANCE:BTC-USD": "Yahoo Finance Bitcoin/USD",
    "YAHOO_FINANCE:ES=F": "Yahoo Finance S&P 500 futures",
    "YAHOO_FINANCE:CL=F": "Yahoo Finance WTI futures",
    "DUKASCOPY:USA500.IDX/USD": "Dukascopy S&P 500 index",
    "DUKASCOPY:EUR/USD": "Dukascopy EUR/USD",
    "DUKASCOPY:USD/JPY": "Dukascopy USD/JPY",
    "DUKASCOPY:XAU/USD": "Dukascopy gold/USD",
    "HISTDATA:SPXUSD": "HistData S&P 500 index",
    "HISTDATA:USDJPY": "HistData USD/JPY",
    "HISTDATA:XAUUSD": "HistData gold/USD",
    "BINANCE:BTCUSDT": "Binance Bitcoin/USDT",
    "CPI_HEADLINE_MOM": "Headline CPI, monthly",
    "CPI_CORE_MOM": "Core CPI, monthly",
    "FEWER_THAN_12_PRIOR_SURPRISES": "too few earlier forecast errors",
    "ZERO_DISPERSION": "no earlier error dispersion",
    "CONSENSUS_NOT_HELD_FOR_RELEASE": "forecast unavailable",
    "ACTUAL_NOT_HELD_FOR_RELEASE": "first print unavailable",
    "PRE_RELEASE_ENDPOINT_ABSENT": "release baseline unavailable",
    "EXACT_ENDPOINT_ABSENT": "exact endpoint unavailable",
    "next_session_close": "Next close",
    "session_close": "Close",
    "UNCLASSIFIED": "Unclassified",
    "IN_LINE": "In line",
    "HOT": "Hot",
    "COOL": "Cool",
    "XAUUSD": "Gold",
    "US500": "S&P 500",
    "EURUSD": "EUR/USD",
    "USDJPY": "USD/JPY",
    "USOIL": "WTI oil",
    "BTCUSD": "Bitcoin",
}
PUBLIC_LABELS = {
    "PRE_RELEASE_CAPTURE": "forecast saved before release",
    "RETAINED_LATER_OBSERVATION": "forecast retrieved later",
    "UNAVAILABLE": "Unavailable",
}


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tables(text):
    """Contiguous Markdown tables, with no interpretation of numeric cells."""
    return re.findall(r"(?m)^\|[^\n]*(?:\n\|[^\n]*)+", text)


def reader_names(text, *, final_copy=False):
    for old, new in {**LABELS, **(PUBLIC_LABELS if final_copy else {})}.items():
        text = re.sub(r"(?<![\w])" + re.escape(old) + r"(?![\w])", lambda _: new, text)
    return text


def record_projection(record):
    family = event_family(record["binding"]["record_id"])
    if family is None:
        return None
    field = next((f for f in record["binding"]["fields"]
                  if f["field_path"] == "/sections/reaction-tables/body_markdown"), None)
    if not field or not isinstance(field.get("value"), str):
        raise ValueError("CPI_REACTION_SOURCE_TABLE_REQUIRED")
    body = field["value"]
    blocks = []
    heading = "Market reactions"
    for part in re.split(r"(?m)(^## [^\n]+$)", body):
        if part.startswith("## "):
            heading = part[3:]
        else:
            blocks.extend({"heading": heading, "markdown": reader_names(t),
                           "source_table_sha256": digest(t)} for t in tables(part))
    if not blocks:
        raise ValueError("CPI_REACTION_SOURCE_TABLE_REQUIRED")
    result = {"policy": POLICY, "record_id": record["binding"]["record_id"],
            "export_bytes_sha256": record["binding"]["export_bytes_sha256"],
            "source_field_citation": field["citation"],
            "source_body_sha256": digest(body), "tables": blocks}
    if family != "CPI":
        clock = next((f for f in record["binding"]["fields"]
                      if f["field_path"] == "/sections/source-data-cutoff/body_markdown"), None)
        result["data_cutoff_utc"] = clock["value"] if clock else None
        result["data_clock_binding"] = ({"citation": clock["citation"], "value": clock["value"]}
                                       if clock else None)
    return result


def writer_guidance(documents):
    if not any(d.get("cpi_reaction_page") for d in documents):
        return ""
    projections = [d["cpi_reaction_page"] for d in documents if d.get("cpi_reaction_page")]
    titles = [EVENT_PAGES[event_family(p["record_id"])]["title"] for p in projections]
    return ("\nCC425_CPI_REACTION_PAGE_V1: Write the source-bound reader argument under "
            f"the title '{titles[0]}'. Place {TOKEN} once where the historical tables belong. "
            "Code inserts the exact structured source tables before source validation; "
            "do not copy, round, reorder or invent their cells. Write all prose yourself. "
            "Distinguish monthly first prints or policy decisions, source-specific surprise buckets, the desk's "
            "normal-spread yardstick and descriptive price changes. Preserve series and proxy "
            "labels, sample counts, eligible denominators and gaps. Do not pool sources or "
            "infer causation, a trading edge or a forecast from a sample mean. A dash is not zero. "
            "Keep the source-data-cutoff field in metadata; never paste that internal clock into the article. "
            "State the actual last release covered. The old map/result description retains "
            "its original clock: never call a past release upcoming or its result not yet due. "
            "Use only a supplied Main map, result and scenario set; never invent absent ones. "
            + ("Ops Product's table review precedes the first CPI post under CC-417. "
               if any(p["record_id"] == RECORD_ID for p in projections) else
               "Keep the FOMC statement and press conference distinct; do not combine overlapping windows. ")
            + "Retain CC-403, "
            "rights, media, identity and readback rules. A refreshed source requires the "
            "existing editorial revision and coordinator, not a second post or scheduler.\n")


def bind_tables(article, documents):
    """Expand a writer-chosen placement, then bind the exact structured output."""
    article = dict(article)
    article.pop("cpi_reaction_page", None)
    sources = [d for d in documents if d.get("cpi_reaction_page")]
    if not sources:
        return article
    if len(sources) != 1:
        raise ValueError("CPI_REACTION_SOURCE_AMBIGUOUS")
    source = sources[0]
    projection = source["cpi_reaction_page"]
    # Presentation labels can improve while an immutable source packet remains
    # frozen. Original table/body hashes retain the producer's exact bytes.
    projected_tables = [{**t, "markdown": reader_names(t["markdown"], final_copy=True)} for t in projection["tables"]]
    body = str(article.get("substack_body_markdown") or "")
    if body.count(TOKEN) > 1:
        raise ValueError("CPI_REACTION_TABLES_DUPLICATED")
    if TOKEN in body:
        sid = source["source_id"]
        assembled = "\n\n".join("## " + t["heading"] + "\n\n" + t["markdown"]
                                  + f"\n[[SOURCE:{sid}]]" for t in projected_tables)
        body = body.replace(TOKEN, assembled)
        article["substack_body_markdown"] = body
    expected = [digest(t["markdown"]) for t in projected_tables]
    actual = [digest(t) for t in tables(body)]
    if any(actual.count(h) != count for h, count in Counter(expected).items()):
        raise ValueError("CPI_REACTION_TABLE_CHANGED_OR_MISSING")
    article["cpi_reaction_page"] = {k: projection[k] for k in (
        "policy", "record_id", "export_bytes_sha256", "source_field_citation", "source_body_sha256")}
    article["cpi_reaction_page"]["table_sha256"] = expected
    field = next(f for f in source["desk_record_binding"]["fields"]
                 if f["field_path"] == "/sections/reaction-tables/body_markdown")
    citation = {k: field.get(k) for k in ("citation", "value", "display", "decimals", "unit")}
    article["desk_record_citations"] = [c for c in article.get("desk_record_citations", [])
                                         if c.get("citation") != citation["citation"]] + [citation]
    return article


def validate_bound_tables(article):
    binding = article.get("cpi_reaction_page")
    if not binding:
        return
    actual = [digest(t) for t in tables(str(article.get("substack_body_markdown") or ""))]
    if (binding.get("policy") != POLICY or not binding.get("table_sha256")
            or any(actual.count(h) != count for h, count in Counter(binding["table_sha256"]).items())):
        raise ValueError("CPI_REACTION_TABLE_CHANGED_OR_MISSING")


def validate_chart_cell(packet, point, operand, document):
    """Admit an unchanged public report cell to the existing chart renderer."""
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of

    binding = document["desk_record_binding"]
    if (event_family(binding.get("record_id")) is None
            or document.get("url") != "urn:cc-public-report:desk:" + sha256_of(binding)):
        raise ValueError("CPI_REACTION_CHART_SOURCE_CHANGED")
    projection = record_projection({"binding": binding})
    basis = operand.get("period_basis") or {}
    source = next((t for t in projection["tables"]
                   if t["source_table_sha256"] == basis.get("source_table_sha256")), None)
    # Locate the original row, before reader-name substitutions.
    field = next(f for f in binding["fields"]
                 if f["field_path"] == "/sections/reaction-tables/body_markdown")
    original = next((t for t in tables(field["value"])
                     if digest(t) == basis.get("source_table_sha256")), None)
    if not source or not original or basis.get("basis") != "CC425_EXACT_TABLE_CELL":
        raise ValueError("CPI_REACTION_CHART_CELL_UNBOUND")
    lines = original.splitlines()
    row_index, column = basis.get("row_index"), basis.get("column_index")
    if (type(row_index) is not int or not 0 <= row_index < len(lines) - 2
            or type(column) is not int):
        raise ValueError("CPI_REACTION_CHART_CELL_UNBOUND")
    row = lines[row_index + 2]
    cells = [v.strip() for v in row.strip().strip("|").split("|")]
    headers = [v.strip() for v in lines[0].strip().strip("|").split("|")]
    if not 0 <= column < min(len(cells), len(headers)):
        raise ValueError("CPI_REACTION_CHART_CELL_UNBOUND")
    token = cells[column]
    if (not re.fullmatch(r"[+-]?\d+(?:\.\d+)?%", token)
            or operand.get("value_text") != token
            or operand.get("support_excerpt") != row
            or operand.get("metric") != headers[column]
            or not operand.get("source_period_text")
            or operand["source_period_text"] not in row
            or operand.get("prepared_period") != point.get("period")
            or operand.get("source_content_sha256") != digest(document["canonical_content_text"])
            or operand.get("unit") != "percent" or packet.get("unit") != "percent"
            or point.get("transform", "IDENTITY") != "IDENTITY" or point.get("scale", 1) != 1
            or len(point.get("inputs", [])) != 1
            or point.get("observation_kind") != "REPORTED_ACTUAL"
            or type(point.get("value")) not in (float, int)
            or point["value"] != float(token[:-1])):
        raise ValueError("CPI_REACTION_CHART_EXACT_CELL_REQUIRED")
    expected = {k: projection[k] for k in ("record_id", "export_bytes_sha256", "source_body_sha256")}
    if packet.get("cpi_reaction_source") != expected:
        raise ValueError("CPI_REACTION_CHART_SOURCE_CHANGED")
