"""Official history for the existing source stage and editorial chart owner.

CC-010 remains the first-print producer. This adapter verifies its bytes, keeps
missing months and release vintages, and projects exact observations for charts.
It owns no publisher, scheduler, store, model or independent acquisition budget.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import re
import calendar
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of

SCHEMA = "contentops.official_release_history.v1"
BLS_RIGHTS = "BLS_US_FEDERAL_PUBLIC_DOMAIN_DATA_WITH_ATTRIBUTION"
SERIES = {
    "CPI_HEADLINE_MOM": ("CUSR0000SA0", "percent", "SA", "MONTH_ON_MONTH"),
    "CPI_CORE_MOM": ("CUSR0000SA0L1E", "percent", "SA", "MONTH_ON_MONTH"),
    "CPI_HEADLINE_YOY": ("CUUR0000SA0", "percent", "NSA", "TWELVE_MONTH_CHANGE"),
    "CPI_CORE_YOY": ("CUUR0000SA0L1E", "percent", "NSA", "TWELVE_MONTH_CHANGE"),
    "NFP_PAYROLL_CHANGE": ("CES0000000001", "persons", "SA", "MONTHLY_LEVEL_DIFFERENCE"),
    "UNEMPLOYMENT_RATE": ("LNS14000000", "percent", "SA", "LEVEL"),
    "AHE_MOM": ("CES0500000003", "percent", "SA", "MONTH_ON_MONTH"),
    "PPI_FINAL_DEMAND_MOM": ("WPSFD4", "percent", "SA", "MONTH_ON_MONTH"),
}
FAMILIES = {
    "cpi": tuple(k for k in SERIES if k.startswith("CPI_")),
    "empsit": ("NFP_PAYROLL_CHANGE", "UNEMPLOYMENT_RATE", "AHE_MOM"),
    "ppi": ("PPI_FINAL_DEMAND_MOM",),
}


def _time(value):
    t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if t.utcoffset() is None:
        raise ValueError("HISTORY_EXPLICIT_TIMEZONE_REQUIRED")
    return t


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def month_window(end, count=24):
    if not re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", end) or not 24 <= count <= 120:
        raise ValueError("HISTORY_AT_LEAST_24_CALENDAR_MONTHS_REQUIRED")
    year, month = map(int, end.split("-"))
    ordinal = year * 12 + month - 1
    return [f"{n // 12:04d}-{n % 12 + 1:02d}" for n in range(ordinal-count+1, ordinal+1)]


def _source_bytes(root, row):
    relative = row.get("source_relative_artifact")
    if not relative:
        raise ValueError("HISTORY_RETAINED_CAPTURE_REQUIRED")
    path = (root / relative).resolve()
    if root.resolve() not in path.parents:
        raise ValueError("HISTORY_CAPTURE_OUTSIDE_ARCHIVE")
    raw = path.read_bytes()
    if path.suffix == ".gz":
        raw = gzip.decompress(raw)
    if _digest(raw) != row.get("source_sha256"):
        raise ValueError("HISTORY_SOURCE_CAPTURE_HASH_CHANGED")
    return raw


def _ppi_sentence_change(text, period, *, core=False):
    """Read the requested month's change, never the next number in the paragraph."""
    month = calendar.month_name[int(period[5:])]
    subject = (r"(?:The index|Prices|The price index) for final demand less foods, energy, and trade services"
        if core else r"(?:The Producer Price Index for final demand|Final demand prices)")
    starts = list(re.finditer(subject, text, re.I))
    for start in starts:
        span = re.split(r"(?<=[a-z])\.\s", text[start.start():start.start()+650], maxsplit=1)[0]
        token = re.search(r"(?P<verb>were unchanged|was unchanged|remained unchanged|"
            r"increased|rose|advanced|moved up|inched up|edged up|rising|moving up|"
            r"decreased|fell|declined|moved down|edged down|falling|declining)"
            r"(?:\s+(?P<value>\d+(?:\.\d+)?)\s+percent)?\s+in\s+" + month + r"\b", span, re.I)
        if token:
            verb = token["verb"].lower()
            if "unchanged" in verb:
                value = 0.0
            elif token["value"]:
                value = float(token["value"]) * (-1 if any(x in verb for x in
                    ("decreased", "fell", "declin", "down", "falling")) else 1)
            else:
                continue
            return value, span
    return None


def reconcile_ppi_history(history):
    """Correct our chart projection from the held release; preserve producer rows.

    CC-216 measured a parser taking a later month's number after 'unchanged'.
    This changes no Main archive. It also uses the held core series instead of
    treating an unexported series as absent data.
    """
    from copy import deepcopy
    from bs4 import BeautifulSoup
    headline = next((s for s in history["series"] if s["name"] == "PPI_FINAL_DEMAND_MOM"), None)
    if headline is None:
        return history
    result = deepcopy(history)
    headline = next(s for s in result["series"] if s["name"] == "PPI_FINAL_DEMAND_MOM")
    core_points, corrections = [], []
    for point in headline["observations"]:
        record = point.get("source_record")
        if not record:
            core_points.append({**point, "value": None, "availability": "MISSING"})
            continue
        soup = BeautifulSoup(_source_bytes(Path(history["archive_root"]), record), "html.parser")
        pre = soup.find("pre")
        text = " ".join((pre.get_text(" ") if pre else soup.get_text(" ")).split())
        reported = _ppi_sentence_change(text, point["period"])
        if reported and reported[0] != point["value"]:
            correction = {"period": point["period"], "producer_value": point["value"],
                "reported_value": reported[0], "exact_source_span": reported[1],
                "source_sha256": record["source_sha256"], "reason": "CURRENT_MONTH_UNCHANGED_NOT_LATER_MONTH_NUMBER"}
            corrections.append(correction)
            point.update(value=reported[0], source_record={**record, "value": reported[0],
                "native_value": "0.0" if reported[0] == 0 else str(reported[0]),
                "producer_record_preserved": record, "source_projection_correction": correction})
        core = _ppi_sentence_change(text, point["period"], core=True)
        core_points.append({"period": point["period"], "value": core[0] if core else None,
            "availability": "OBSERVED" if core else "MISSING",
            "missing_reason": None if core else "EXACT_CURRENT_MONTH_CORE_PASSAGE_NOT_FOUND",
            "source_record": {**record, "series": "PPI_CORE_EX_FOOD_ENERGY_TRADE_MOM",
                "value": core[0], "native_value": str(core[0]), "exact_source_span": core[1],
                "availability": "OBSERVED", "measure": "MONTH_ON_MONTH",
                "metric": "Final demand less foods, energy, and trade services"} if core else None})
    result["projection_corrections"] = corrections
    if any(o["value"] is not None for o in core_points):
        result["series"].append({"name": "PPI_CORE_EX_FOOD_ENERGY_TRADE_MOM",
            "official_series_id": "BLS_PPI_TABLE_A_FINAL_DEMAND_LESS_FOODS_ENERGY_TRADE_SERVICES",
            "series_identity_basis": "EXACT_OFFICIAL_TABLE_ROW_LABEL_NOT_API_SERIES_CODE",
            "measure": "MONTH_ON_MONTH", "unit": "percent", "seasonal_adjustment": "SA",
            "observations": core_points})
    return result


def load_cc010_history(archive_root, *, series, end_period, cutoff_utc, months=24):
    """Read the accepted producer; acquisition clocks never become event clocks."""
    root = Path(archive_root)
    manifest_raw = (root / "archive_manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    raw = (root / "first_release_actuals.jsonl").read_bytes()
    if manifest.get("schema") != "EventDeskFirstReleaseArchiveV1" or _digest(raw) != manifest.get("dataset_sha256"):
        raise ValueError("HISTORY_CC010_DATASET_HASH_CHANGED")
    if not series or len(set(series)) != len(series) or not set(series) <= set(SERIES):
        raise ValueError("HISTORY_EXACT_SUPPORTED_SERIES_REQUIRED")
    periods, cutoff = month_window(end_period, months), _time(cutoff_utc)
    if end_period > cutoff.strftime("%Y-%m"):
        raise ValueError("HISTORY_PERIOD_AFTER_EVENT")
    sources = {s["sha256"]: s for s in manifest.get("sources", [])}
    selected, verified = {}, {}
    for line in raw.splitlines():
        row = json.loads(line)
        key = (row.get("series"), row.get("reference_period"))
        if key[0] not in series or key[1] not in periods:
            continue
        # Later releases are unavailable, even when they describe an older month.
        if _time(row["release_datetime_utc"]) > cutoff:
            continue
        if key in selected:
            raise ValueError("HISTORY_AMBIGUOUS_FIRST_PRINT")
        official = urlsplit(row.get("source_url", ""))
        if (official.scheme != "https" or official.netloc != "www.bls.gov"
                or not re.fullmatch(r"/news.release/archives/(?:cpi|empsit|ppi)_\d{8}\.htm", official.path)
                or row.get("rights_tag") != BLS_RIGHTS
                or row.get("vintage") != "FIRST_REFERENCE_MONTH_IN_DATED_RELEASE"
                or row.get("archive_correction_notice") is not False):
            raise ValueError("HISTORY_PUBLIC_DATED_FIRST_PRINT_REQUIRED")
        _, unit, adjustment, _ = SERIES[key[0]]
        if row.get("unit") != unit or row.get("seasonal_adjustment") != adjustment:
            raise ValueError("HISTORY_SERIES_DIMENSION_CHANGED")
        digest = row.get("source_sha256")
        source = sources.get(digest)
        if not source or source.get("url") != row["source_url"] or source.get("status") != 200:
            raise ValueError("HISTORY_SOURCE_MANIFEST_BINDING_REQUIRED")
        if digest not in verified:
            _source_bytes(root, row)
            verified[digest] = {"url": row["source_url"], "capture_sha256": digest,
                "retrieved_at_utc": row["retrieved_at_utc"], "relative_capture": row["source_relative_artifact"]}
        if row["value"] is not None and (isinstance(row["value"], bool)
                or not isinstance(row["value"], (int, float)) or not math.isfinite(row["value"])
                or row.get("availability") not in {"OBSERVED", "DERIVED"}):
            raise ValueError("HISTORY_TYPED_OBSERVATION_REQUIRED")
        selected[key] = row
    result = []
    for name in series:
        official_id, unit, adjustment, measure = SERIES[name]
        observations = []
        for period in periods:
            row = selected.get((name, period))
            observations.append({"period": period, "value": row["value"] if row else None,
                "availability": row["availability"] if row else "MISSING",
                "missing_reason": ((row or {}).get("missing_reason") or "NOT_PUBLISHED_OR_NOT_AVAILABLE_AT_EVENT")
                    if not row or row["value"] is None else None,
                "source_record": row})
        if not any(o["value"] is not None for o in observations):
            raise ValueError("HISTORY_SERIES_HAS_NO_ADMISSIBLE_OBSERVATIONS:" + name)
        result.append({"name": name, "official_series_id": official_id, "measure": measure,
            "unit": unit, "seasonal_adjustment": adjustment, "observations": observations})
    components = None
    current = next((selected.get((name, end_period)) for name in series
        if name.startswith("CPI_") and selected.get((name, end_period))), None)
    if current:
        from bs4 import BeautifulSoup
        table = BeautifulSoup(_source_bytes(root, current), "html.parser").find("table", id="cpipress6")
        if table and "Seasonally adjusted effect on All Items" in table.get_text(" ", strip=True):
            effects = []
            categories = {"Food": "CUSR0000SAF1", "Energy": "CUSR0000SA0E",
                "All items less food and energy": "CUSR0000SA0L1E"}
            for row in table.find_all("tr"):
                cells = [c.get_text(" ", strip=True) for c in row.find_all(["th", "td"])]
                if cells and cells[0] in categories and len(cells) == 7:
                    token = cells[3]
                    if not re.fullmatch(r"-?\d+\.\d+", token):
                        raise ValueError("HISTORY_COMPONENT_EFFECT_MISSING")
                    effects.append({"name": cells[0], "official_series_id": categories[cells[0]],
                        "period": end_period, "value": float(token), "native_value": token,
                        "unit": "percentage points", "seasonal_adjustment": "SA",
                        "source_row": " | ".join(cells)})
            if set(e["name"] for e in effects) != set(categories):
                raise ValueError("HISTORY_EXACT_COMPONENT_EFFECT_ROWS_REQUIRED")
            components = {"table_id": "cpipress6", "source_url": current["source_url"] + "#cpipress6",
                "capture_sha256": current["source_sha256"], "release_datetime_utc": current["release_datetime_utc"],
                "period": end_period, "effects": effects,
                "measure": "BLS_REPORTED_SEASONALLY_ADJUSTED_EFFECT_ON_ALL_ITEMS",
                "aggregation": "FOOD_ENERGY_CORE_DISJOINT_CATEGORIES_NOT_WEIGHTS_TIMES_CHANGES"}
    history = {"schema_version": SCHEMA, "producer": "MAIN_CC010_FIRST_PRINT_ARCHIVE",
        "dataset_sha256": _digest(raw), "archive_manifest_sha256": _digest(manifest_raw),
        "archive_root": str(root.resolve()), "cutoff_utc": cutoff_utc,
        "window": [periods[0], periods[-1]], "periods": periods, "series": result,
        "captures": list(verified.values()), "components": components, "new_source_requests": 0,
        "historical_possession_proven": False,
        "vintage_basis": "DATED_RELEASE_FIRST_PRINTS_NOT_CURRENT_REVISED_HISTORY"}
    return reconcile_ppi_history(history)


def history_documents(history):
    """Compact typed producer projections; every point retains its release/capture."""
    docs = []
    for series in history["series"]:
        rows = [o for o in series["observations"] if o["value"] is not None]
        records = [o["source_record"] for o in rows]
        lines = [f"BLS {series['official_series_id']} {series['name']}; {o['period']}; "
            f"{o['value']:g} {series['unit']}; {series['seasonal_adjustment']}; "
            f"{o['source_record']['availability']}; release {o['source_record']['release_datetime_utc']}"
            for o in rows]
        text = "\n".join(lines)
        docs.append({"document_id": "official-history-" + sha256_of([history["dataset_sha256"], series])[:24],
            "url": records[-1]["source_url"], "source_url": records[-1]["source_url"],
            "publisher": "U.S. Bureau of Labor Statistics (CC-010 first-print projection)",
            "published_at_utc": records[-1]["release_datetime_utc"],
            "source_authority_class": "official_release_history_from_cc010",
            "retrieval_method": "READ_ONLY_HASH_VERIFIED_CC010_PROJECTION",
            "canonical_content_text": text, "canonical_content_sha256": _digest(text.encode()),
            "raw_sha256": history["dataset_sha256"],
            "source_reuse_constraints": {"attribution_required": True,
                "scope": "ATTRIBUTED_ORIGINAL_FACTS_ONLY_INDEPENDENT_PUBLIC_PARAPHRASE",
                "policy_capture_sha256": history["dataset_sha256"],
                "policy_capture_basis": "CC010_EXPLICIT_PUBLIC_DOMAIN_RIGHTS_TAGS_IN_VERIFIED_DATASET",
                "source_capture_sha256": history["dataset_sha256"]},
            "official_release_history": {"dataset_sha256": history["dataset_sha256"],
                "series": series, "window": history["window"], "cutoff_utc": history["cutoff_utc"],
                "historical_possession_proven": False}})
    if components := history.get("components"):
        lines = [f"BLS {e['official_series_id']} {e['name']}; {e['period']}; "
            f"{e['native_value']} percentage points; SA; Table 6 reported effect on All Items" for e in components["effects"]]
        text = "\n".join(lines)
        docs.append({"document_id": "official-components-" + components["capture_sha256"][:24],
            "url": components["source_url"], "source_url": components["source_url"],
            "publisher": "U.S. Bureau of Labor Statistics", "published_at_utc": components["release_datetime_utc"],
            "source_authority_class": "official_release_history_from_cc010",
            "retrieval_method": "READ_ONLY_HASH_VERIFIED_BLS_TABLE_6",
            "canonical_content_text": text, "canonical_content_sha256": _digest(text.encode()),
            "raw_sha256": components["capture_sha256"], "release_component_effects": components,
            "source_reuse_constraints": {"attribution_required": True,
                "scope": "ATTRIBUTED_ORIGINAL_FACTS_ONLY_INDEPENDENT_PUBLIC_PARAPHRASE",
                "policy_capture_sha256": history["dataset_sha256"],
                "policy_capture_basis": "CC010_EXPLICIT_PUBLIC_DOMAIN_RIGHTS_TAGS_IN_VERIFIED_DATASET",
                "source_capture_sha256": components["capture_sha256"]}})
    return docs


def history_chart_packet(history, *, series_names, asset_id, title, question, placement_after):
    """Bind the editor's chosen series/argument to existing deterministic charts."""
    docs = history_documents(history)
    packets = []
    for name in series_names:
        doc = next(d for d in docs if (d.get("official_release_history") or {}).get("series", {}).get("name") == name)
        series = doc["official_release_history"]["series"]
        points = []
        for observation in series["observations"]:
            point = {"period": observation["period"], "value": observation["value"]}
            if observation["value"] is None:
                point.update(observation_kind="MISSING", missing_reason=observation["missing_reason"], inputs=[],
                    missing_binding={"document_id": doc["document_id"], "source_content_sha256": doc["canonical_content_sha256"]})
            else:
                line = next(line for line in doc["canonical_content_text"].splitlines() if f"; {observation['period']};" in line)
                point.update(observation_kind="REPORTED_ACTUAL" if observation["availability"] == "OBSERVED" else "ACTUAL",
                    inputs=[{"document_id": doc["document_id"], "support_excerpt": line,
                        "value_text": f"{observation['value']:g}", "source_period_text": observation["period"],
                        "source_content_sha256": doc["canonical_content_sha256"], "metric": name,
                        "unit": series["unit"], "prepared_period": observation["period"],
                        "period_basis": {"basis": "HASH_VERIFIED_CC010_FIRST_PRINT_OBSERVATION",
                            "official_series_id": series["official_series_id"],
                            "capture_sha256": observation["source_record"]["source_sha256"],
                            "release_datetime_utc": observation["source_record"]["release_datetime_utc"]}}])
            points.append(point)
        packets.append({"name": name, "points": points})
    units = {SERIES[name][1] for name in series_names}
    if len(units) != 1:
        raise ValueError("HISTORY_CHART_COMPARABLE_UNITS_REQUIRED")
    return {"asset_id": asset_id, "chart_type": "line", "title": title, "question": question,
        "placement_after": placement_after, "unit": next(iter(units)), "series": packets,
        "source_caption": "Source: BLS dated first releases (CC-010 archive). Missing months are gaps; no interpolation.",
        "missingness": [{"series": s["name"], "period": o["period"], "reason": o["missing_reason"]}
            for s in history["series"] if s["name"] in series_names for o in s["observations"] if o["value"] is None],
        "history_lineage": {"dataset_sha256": history["dataset_sha256"], "window": history["window"],
            "cutoff_utc": history["cutoff_utc"], "vintage_basis": history["vintage_basis"],
            "series": [{"name": s["name"], "official_series_id": s["official_series_id"],
                "seasonal_adjustment": s["seasonal_adjustment"], "observations": s["observations"]}
                for s in history["series"] if s["name"] in series_names]}}


def history_for_source_pack(source_pack, *, cutoff_utc, archive_root):
    """Recognize supported release families from exact official source identities."""
    families, releases = set(), []
    for doc in source_pack:
        url = urlsplit(doc.get("url") or doc.get("source_url") or "")
        match = re.fullmatch(r"/news.release/(?:archives/)?(cpi|empsit|ppi)(?:_\d{8}|\.nr0)?\.htm", url.path)
        if url.scheme == "https" and url.netloc == "www.bls.gov" and match:
            families.add(match[1])
            if not doc.get("published_at_utc"):
                raise ValueError("HISTORY_EXACT_RELEASE_CLOCK_REQUIRED")
            releases.append(_time(doc["published_at_utc"]))
    if not families:
        return None
    if len(families) != 1:
        raise ValueError("HISTORY_EXACT_RELEASE_FAMILY_REQUIRED")
    family = next(iter(families))
    cutoff_utc = min(_time(cutoff_utc), max(releases)).isoformat()
    manifest = json.loads((Path(archive_root) / "archive_manifest.json").read_bytes())
    dataset = (Path(archive_root) / "first_release_actuals.jsonl").read_bytes()
    if _digest(dataset) != manifest.get("dataset_sha256"):
        raise ValueError("HISTORY_CC010_DATASET_HASH_CHANGED")
    periods = [r["reference_period"] for line in dataset.splitlines()
        if (r := json.loads(line)).get("family") == family and _time(r["release_datetime_utc"]) <= _time(cutoff_utc)]
    if not periods:
        raise ValueError("HISTORY_RELEASE_NOT_AVAILABLE_AT_CUTOFF")
    return load_cc010_history(archive_root, series=FAMILIES[family], end_period=max(periods), cutoff_utc=cutoff_utc)


def newsroom_desk_projection(history, *, archive_root, config_path=None):
    """Use CC-145's existing delivered adapter, without copying its data engine."""
    import importlib.util
    config_path = Path(config_path or Path(__file__).resolve().parents[1] / "config/official_release_history_v1.json")
    config = json.loads(config_path.read_bytes())
    binding = config.get("newsroom_desk_adapter")
    if not binding:
        return None
    catalog = Path(binding["catalog_path"])
    catalog_value = json.loads(catalog.read_bytes())
    # A relocated/test archive must not accidentally consume the host's data.
    if not any(row.get("kind") == "first_print" and Path(row["root"]).resolve() == Path(archive_root).resolve()
               for row in catalog_value.get("sources", [])):
        return None
    module_path = Path(binding["module_path"])
    spec = importlib.util.spec_from_file_location("contentops_cc145_delivered_adapter", module_path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    names = [row["name"] for row in history["series"]]
    family = "cpi" if names[0].startswith("CPI_") else "ppi" if names[0].startswith("PPI_") else "nfp"
    value = adapter.project(catalog, family=family, series=tuple(names), audience="public",
        start=history["window"][0], end=history["window"][1], event_cutoff_utc=history["cutoff_utc"])
    if value.get("schema") != "NewsroomDeskChartDataV1" or value.get("audience") != "public" or value.get("public_export") is not True:
        raise ValueError("DESK_ADAPTER_PUBLIC_PROJECTION_REQUIRED")
    if any(point.get("public_eligible") is not True for series in value.get("series", []) for point in series.get("points", [])):
        raise ValueError("DESK_ADAPTER_PUBLIC_POINT_RIGHTS_REQUIRED")
    return {"producer": "CC-145", "module_path": str(module_path),
        "module_sha256": _digest(module_path.read_bytes()), "catalog_path": str(catalog), "data": value}


def enrich_source_pack(turn, *, source_pack, article_mode, cutoff_utc, archive_root=None):
    """Join public history before the existing evidence artifact/writer is frozen."""
    if article_mode in {"BREAKING_BRIEF", "FOLLOW_UP_UPDATE"}:
        return source_pack
    path = turn.root / "official_release_history_v1.json"
    if turn.frozen_request("write") and not path.is_file():
        return source_pack  # Preserve an already issued packet, including old policy.
    if archive_root is None:
        config_path = Path(__file__).resolve().parents[1] / "config/official_release_history_v1.json"
        archive_root = json.loads(config_path.read_bytes())["cc010_archive_root"]
    history = history_for_source_pack(source_pack, cutoff_utc=cutoff_utc, archive_root=archive_root)
    if history is None:
        return source_pack
    if path.is_file():
        retained = json.loads(path.read_bytes())
        for key in ("newsroom_desk_projection", "newsroom_desk_projection_error", "supersedes_projection_sha256"):
            if key in retained:
                history[key] = retained[key]
        if retained != history:
            if (turn.frozen_request("write") or not history.get("projection_corrections")
                    or retained["dataset_sha256"] != history["dataset_sha256"]
                    or retained["cutoff_utc"] != history["cutoff_utc"]):
                raise ValueError("HISTORY_FROZEN_SOURCE_PROJECTION_CHANGED")
            # An exact held-source correction before writing preserves the issued
            # Light request and old projection, and supplies corrected facts to MAX.
            old_raw = path.read_bytes()
            old_hash = _digest(old_raw)
            original = path.with_name("official_release_history_before_cc216_" + old_hash[:12] + ".json")
            if original.exists() and original.read_bytes() != old_raw:
                raise ValueError("HISTORY_RETAINED_CORRECTION_IDENTITY_CONFLICT")
            original.write_bytes(old_raw)
            history["supersedes_projection_sha256"] = old_hash
            path.write_bytes(canonical_bytes(history))
    else:
        try:
            if projection := newsroom_desk_projection(history, archive_root=archive_root):
                history["newsroom_desk_projection"] = projection
        except (OSError, ValueError) as exc:
            # The existing verified CC-010 history is still usable. An optional
            # projection failure never walls it off or admits failed/private data.
            history["newsroom_desk_projection_error"] = str(exc)
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_bytes(history))
    docs = history_documents(history)
    if projection := history.get("newsroom_desk_projection"):
        for doc in docs:
            name = doc.get("official_release_history", {}).get("series", {}).get("name")
            selected = [row for row in projection["data"]["series"] if row["series_id"] == name]
            if selected:
                from copy import deepcopy
                selected = deepcopy(selected)
                corrections = {r["period"]: r for r in history.get("projection_corrections", [])}
                for series in selected:
                    for point in series.get("points", []):
                        if point["x"] in corrections:
                            correction = corrections[point["x"]]
                            point.update(producer_value_preserved=point["value"], value=correction["reported_value"],
                                source_projection_correction=correction)
                doc["newsroom_desk_projection"] = {**projection, "data": {**projection["data"], "series": selected}}
    if len(source_pack) + len(docs) > 10:
        raise ValueError("HISTORY_BOUNDED_SOURCE_PACK_REQUIRED")
    return [*source_pack, *[{**d, "source_id": f"SOURCE_{len(source_pack)+i+1}"} for i,d in enumerate(docs)]]


def acquire_official_history(loader, request):
    """Use the existing bounded loader's GET and shared budget for exact history.

The caller names a keyless official URL and separately admits its public rights.
Current API/flat-file captures cannot claim a historical vintage merely by
filtering their observation dates. BEA/Fed/Treasury native bytes are retained for
their existing parsers; arbitrary response text is never numeric chart authority.
"""
    from live_contentops.official_primary_evidence_loader_v1 import _safe_url
    hosts = {"api.bls.gov", "download.bls.gov", "www.bls.gov", "www.bea.gov",
        "apps.bea.gov", "www.federalreserve.gov", "home.treasury.gov", "api.fiscaldata.treasury.gov"}
    url, _ = _safe_url(request["url"], hosts)
    if request.get("retrospective"):
        raise ValueError("HISTORY_RETROSPECTIVE_REQUIRES_DATED_ARCHIVE_VINTAGE")
    if request.get("rights_class") not in {"PUBLIC", "PUBLIC_DOMAIN"} or not re.fullmatch(
            r"[a-f0-9]{64}", request.get("rights_evidence_sha256", "")):
        raise ValueError("HISTORY_EXPLICIT_PUBLIC_RIGHTS_REQUIRED")
    loader._consume_request()
    response = loader._http_get(url, loader._timeout_seconds, loader._max_response_bytes)
    body = response.get("body")
    if (response.get("status") != 200 or response.get("final_url") != url
            or response.get("content_truncated") or not isinstance(body, bytes) or not body
            or len(body) > loader._max_response_bytes):
        raise ValueError("HISTORY_COMPLETE_EXACT_OFFICIAL_RESPONSE_REQUIRED")
    result = {"source_url": url, "capture_sha256": _digest(body), "raw_bytes": body,
        "retrieved_at_utc": loader._clock().isoformat(), "rights_class": request["rights_class"],
        "rights_evidence_sha256": request["rights_evidence_sha256"],
        "vintage_basis": "CURRENT_CAPTURE_NOT_EVENT_TIME_PROOF", "request_count_for_call": 1}
    if urlsplit(url).hostname == "api.bls.gov":
        parsed = json.loads(body)
        if parsed.get("status") != "REQUEST_SUCCEEDED":
            raise ValueError("HISTORY_BLS_API_REQUEST_FAILED")
        result["official_series"] = parsed.get("Results", {}).get("series", [])
        if not result["official_series"]:
            raise ValueError("HISTORY_BLS_API_SERIES_MISSING")
    return result
