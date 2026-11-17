"""Present CC-441's held computed cells; never rebuild or infer a price move."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN
import gzip
from hashlib import sha256
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from .capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from .cpi_reaction_page_v1 import EVENT_PAGES, LABELS

MARKETS = ("XAUUSD", "EURUSD", "USDJPY", "US500", "USOIL", "BTCUSD")
FAMILIES = {"NFP": ("NFP",), "FOMC": ("FOMC_DECISION", "FOMC_PRESS_CONFERENCE"), "PPI": ("PPI",)}
HORIZONS = ("1m", "15m", "60m", "session_close", "+1_session", "+3_sessions")
NAMES = {"FOMC_DECISION": "Fed statement", "FOMC_PRESS_CONFERENCE": "Fed press conference",
         "NFP": "Payrolls", "PPI": "Producer prices"}
SERIES = {**LABELS, "YAHOO_FINANCE:GC=F": "Yahoo Finance gold futures",
          "YAHOO_FINANCE:EURUSD=X": "Yahoo Finance EUR/USD", "YAHOO_FINANCE:JPY=X": "Yahoo Finance USD/JPY",
          "DUKASCOPY:LIGHT.CMD/USD": "Dukascopy WTI oil", "IBKR:MCL": "WTI micro futures",
          "CC_HELD_CFD:BTCUSD": "Capital Chronicle held Bitcoin price proxy",
          **{"mt5_demo_capture:" + key: "Capital Chronicle broker-price proxy for " + LABELS[key] for key in MARKETS}}


def display(value):
    if value is None:
        return "—"
    number = Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)
    return format(abs(number) if number == 0 else number, ".4f")


def project(table, family):
    """Exact row/cell locators; raw prices and consensus tables never enter."""
    events = {e["event_id"]: e for e in table["events"]}
    bindings, blocks, gaps, observed = [], [], {}, 0
    selected = [(i, r) for i, r in enumerate(table["rows"])
                if r["family"] in FAMILIES[family] and r["symbol"] in MARKETS]
    for subtype in FAMILIES[family]:
        for market in MARKETS:
            rows = [(i, r) for i, r in selected if r["family"] == subtype and r["symbol"] == market]
            if not rows:
                continue
            lines = ["| Release (ET) | Price series | +1m | +15m | +60m | Close | Next session | Third session |",
                     "|---|---|---:|---:|---:|---:|---:|---:|"]
            for index, row in rows:
                event = events[row["event_id"]]
                when = row.get("released_at_utc")
                if when:
                    at = datetime.fromisoformat(when.replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York"))
                    stamp = at.strftime("%d %b %Y, %I:%M %p ET").lstrip("0")
                else:
                    stamp = event["event_date"]
                series = row.get("series_id")
                label = SERIES.get(series, str(series).replace("|", "/")) if series else "No price series"
                basis = row.get("price_basis") or ""
                if basis == "BID":
                    label += "; bid quotes"
                elif basis == "SPOT_TRADE":
                    label += "; spot trades"
                elif basis.startswith("YAHOO_UNADJUSTED_CHART_OHLC:"):
                    label += "; unadjusted chart close"
                elif basis == "NATIVE_BROKER_OHLC_UNADJUSTED_BASIS_NOT_EXCHANGE_LAST_OR_MID":
                    label += "; broker chart close"
                cells = []
                for horizon in HORIZONS:
                    window = row["windows"][horizon]
                    value = window.get("move_bps")
                    cell = display(value)
                    observed += value is not None
                    if value is None:
                        reason = window.get("missing_reason") or "SOURCE_VALUE_ABSENT"
                        gaps[reason] = gaps.get(reason, 0) + 1
                    bindings.append({"event_id": row["event_id"], "market": market, "series_id": series,
                        "price_basis": row.get("price_basis"), "source_pointer": f"/rows/{index}/windows/{horizon}/move_bps",
                        "source_value": value, "display": cell, "unit": "basis_points",
                        "transformation": "ROUND_HALF_EVEN_4DP" if value is not None else "MISSING_PRESERVED",
                        "endpoint_utc": window.get("endpoint_utc"), "missing_reason": window.get("missing_reason")})
                    cells.append(cell)
                lines.append("| " + " | ".join([stamp, label, *cells]) + " |")
            blocks.append("## " + NAMES[subtype] + ": " + LABELS[market] + "\n\n" + "\n".join(lines))
    body = ("Computed price changes in basis points, displayed to four decimal places. "
            "These are observed co-movements, not an isolated release effect, a forecast or a trading result. "
            "Source series and their price bases remain separate. A dash means no exact source window. "
            "Close and session horizons use the producer's weekday New York close benchmark; "
            "Bitcoin uses its original day convention. Holidays without an exact endpoint stay absent.\n\n"
            + "\n\n".join(blocks))
    body += ("\n\n## Coverage\n\n| Market rows | Observed windows | Unavailable windows |\n"
             "|---:|---:|---:|\n| " + str(len(selected)) + " | " + str(observed) + " | "
             + str(len(bindings) - observed) + " |")
    if family == "FOMC" and observed == 0:
        body += ("\n\nThe retained Fed rows hold meeting dates but no exact statement or press-conference "
                 "release times. Their measured price changes are unavailable, not zero.")
    return {"body_markdown": body, "cell_bindings": bindings, "market_rows": len(selected),
            "observed_moves": observed, "gaps": gaps, "source_data_cutoff_utc": table["as_of_utc"]}


def prepare(table_path, output_root, *, generated_at_utc, producer_commit):
    """Write the requested output folder; leave the Data job and stores alone."""
    path = Path(table_path)
    raw = path.read_bytes()
    table = json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)
    if table.get("schema") != "EventWeightDecayTableV1":
        raise ValueError("CC441_EVENT_TABLE_REQUIRED")
    table_hash = sha256(raw).hexdigest()
    projections = {family: project(table, family) for family in FAMILIES}
    root = Path(output_root).resolve() / ("source-" + table_hash[:16]) / ("presentation-" + sha256_of(projections)[:16])
    root.mkdir(parents=True, exist_ok=True)
    results = []
    for family in FAMILIES:
        spec = EVENT_PAGES[family]
        projection = projections[family]
        folder = root / family.lower()
        folder.mkdir(exist_ok=True)
        target = folder / "desk-export.json"
        generated = json.loads(target.read_bytes())["generated_at_utc"] if target.is_file() else generated_at_utc
        instant = datetime.fromisoformat(generated.replace("Z", "+00:00"))
        if instant.tzinfo is None:
            raise ValueError("EVENT_PROJECTION_CLOCK_TIMEZONE_REQUIRED")
        generated = instant.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        sid = "src:cc:cc441-" + family.lower()
        def field(value):
            return {"value": value, "rights_class": "CC_OWN_ANALYSIS", "visibility": "public",
                    "use_label": "PUBLIC_OWN_ANALYSIS_NOT_ADVICE", "source_ids": [sid]}
        # This is a Publisher presentation projection, never a new Main report
        # or a freshly captured market observation.
        export = {"schema": "CapitalChronicleDeskRecordExportV1", "schema_version": "1.4.0",
            "export_id": "cc468-" + family.lower() + "-" + table_hash[:16],
            "generated_at_utc": generated, "fixture": False,
            "producer": {"name": "contentops_cc468_held_data_projection", "version": "1", "commit": producer_commit,
                         "inputs": ["CC-441 EventWeightDecayTableV1 " + table_hash]},
            "entitlement_map_version": "draft_v1",
            "sources": [{"source_id": sid, "provider": "Capital Chronicle", "dataset": "CC441_EVENT_WEIGHT_DECAY_V1",
                "title": spec["title"], "url": None, "retrieved_at_utc": generated,
                "known_at_utc": None, "clock_missing_cause": "CC441_TABLE_FIRST_KNOWN_CLOCK_NOT_SUPPLIED",
                "raw_sha256": table_hash, "rights_class": "CC_OWN_ANALYSIS",
                "attribution": "Capital Chronicle calculations; source price series as labelled",
                "disclaimer": "Computed changes only; no raw prices, consensus tables or private execution data."}],
            "asset_dossiers": [], "event_cards": [], "decision_records": [], "calendar_entries": [], "data_series": [],
            "reports": [{"record_type": "report", "record_id": spec["record_id"], "report_type": "POST_RELEASE_NOTE",
                "for_date": table["as_of_utc"][:10], "generated_at_utc": generated, "title": field(spec["title"]),
                "sections": [{"section_id": "reaction-tables", "heading": field(spec["title"]),
                              "body_markdown": field(projection["body_markdown"]), "cites": []},
                             {"section_id": "source-data-cutoff", "heading": field("Data coverage cutoff"),
                              "body_markdown": field(table["as_of_utc"]), "cites": []}]}]}
        export["integrity"] = {"canonicalization": "JSON_SORTED_KEYS_COMPACT_UTF8_WITHOUT_INTEGRITY",
                               "content_sha256": sha256_of(export)}
        target.write_bytes(canonical_bytes(export))
        binding = {"schema_version": "contentops.main_report_feed_pointer.v1",
            "producer_repository": "https://github.com/fatcat2109/capital-chronicle-contentops",
            "producer_commit": producer_commit, "desk_record_exports": [{"path": str(target),
                "sha256": sha256(target.read_bytes()).hexdigest()}]}
        (folder / "feed-binding.json").write_bytes(canonical_bytes(binding))
        (folder / "cell-bindings.json").write_bytes(canonical_bytes({"source_path": str(path.resolve()),
            "source_sha256": table_hash, "source_data_cutoff_utc": table["as_of_utc"],
            "generated_at_utc": generated, "cells": projection["cell_bindings"]}))
        (folder / "reader-tables.md").write_text(projection["body_markdown"], encoding="utf-8")
        results.append({"family": family, "binding_path": str(folder / "feed-binding.json"),
            "record_id": spec["record_id"], "source_sha256": table_hash, "source_data_cutoff_utc": table["as_of_utc"],
            "generated_at_utc": generated, "market_rows": projection["market_rows"],
            "observed_moves": projection["observed_moves"], "gaps": projection["gaps"]})
    return results
