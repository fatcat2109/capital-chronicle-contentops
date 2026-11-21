"""Synthetic source fixtures only; no network, model or production store."""
from copy import deepcopy
from datetime import datetime, timezone
import gzip
import hashlib
import json
from types import SimpleNamespace

import pytest

from live_contentops.official_release_history_v1 import (
    BLS_RIGHTS, SERIES, enrich_source_pack, history_documents, history_for_source_pack,
    load_cc010_history, month_window,
)
from live_contentops.official_primary_evidence_loader_v1 import BoundedOfficialPrimaryEvidenceLoader
from live_contentops.rolling_x_grounded_article_media_builder_v1 import _editorial_data_values, build_editorial_data_chart

CUTOFF = "2026-10-14T12:30:00Z"
NAMES = tuple(n for n in SERIES if n.startswith("CPI_"))


@pytest.fixture
def archive(tmp_path):
    root = tmp_path / "CONTROLLED_CC010_NOT_PRODUCTION"
    (root / "raw").mkdir(parents=True)
    rows, sources = [], []
    for i, period in enumerate(month_window("2026-09")):
        year, month = map(int, period.split("-"))
        following = f"{year+month//12:04d}-{month%12+1:02d}"
        day = "14" if period == "2026-09" else "01"
        released = following + f"-{day}T12:30:00Z"
        url = "https://www.bls.gov/news.release/archives/cpi_" + following[5:] + day + following[:4] + ".htm"
        body = f"CONTROLLED source {period} {i}, no real BLS values".encode()
        sha = hashlib.sha256(body).hexdigest()
        relative = "raw/" + sha + ".bin.gz"
        (root / relative).write_bytes(gzip.compress(body))
        sources.append({"sha256": sha, "url": url, "status": 200})
        for name in NAMES:
            _, unit, sa, _ = SERIES[name]
            missing = period == "2025-10" or period == "2025-11" and name.endswith("MOM")
            rows.append({"family": "cpi", "series": name, "reference_period": period,
                "value": None if missing else round(i/10, 1), "native_value": None if missing else str(round(i/10, 1)),
                "unit": unit, "seasonal_adjustment": sa, "availability": "MISSING" if missing else "OBSERVED",
                "release_datetime_utc": released, "source_url": url, "rights_tag": BLS_RIGHTS,
                "vintage": "FIRST_REFERENCE_MONTH_IN_DATED_RELEASE", "archive_correction_notice": False,
                "source_sha256": sha, "source_relative_artifact": relative, "retrieved_at_utc": "2026-10-30T00:00:00Z"})
    _write_archive(root, rows, sources)
    return root


def _write_archive(root, rows, sources):
    raw = b"\n".join(json.dumps(r).encode() for r in rows) + b"\n"
    (root / "first_release_actuals.jsonl").write_bytes(raw)
    (root / "archive_manifest.json").write_text(json.dumps({"schema": "EventDeskFirstReleaseArchiveV1",
        "dataset_sha256": hashlib.sha256(raw).hexdigest(), "sources": sources}), encoding="utf-8")


def load(root):
    return load_cc010_history(root, series=NAMES, end_period="2026-09", cutoff_utc=CUTOFF)


def test_first_prints_keep_24_calendar_months_dimensions_gaps_and_separate_clocks(archive):
    result = load(archive)
    assert result["window"] == ["2024-10", "2026-09"]
    assert len(result["periods"]) == 24 and len(result["series"]) == 4
    assert result["new_source_requests"] == 0 and not result["historical_possession_proven"]
    for series in result["series"]:
        assert series["official_series_id"] == SERIES[series["name"]][0]
        assert series["observations"][12]["value"] is None
        assert series["observations"][-1]["source_record"]["retrieved_at_utc"] > CUTOFF
        if series["name"].endswith("MOM"):
            assert series["observations"][13]["value"] is None
    docs = history_documents(result)
    assert len(docs) == 4 and all(d["official_release_history"]["window"] == result["window"] for d in docs)


@pytest.mark.parametrize("fault", ["dataset", "capture", "rights", "units", "duplicate", "vintage", "traversal"])
def test_changed_or_ambiguous_owner_evidence_fails_closed(archive, fault):
    rows = [json.loads(x) for x in (archive / "first_release_actuals.jsonl").read_bytes().splitlines()]
    sources = json.loads((archive / "archive_manifest.json").read_bytes())["sources"]
    if fault == "dataset":
        with (archive / "first_release_actuals.jsonl").open("ab") as f:
            f.write(b" ")
    elif fault == "capture":
        (archive / rows[0]["source_relative_artifact"]).write_bytes(gzip.compress(b"changed"))
    else:
        if fault == "rights":
            rows[0]["rights_tag"] = "PRIVATE"
        if fault == "units":
            rows[0]["unit"] = "index"
        if fault == "duplicate":
            rows.append(deepcopy(rows[0]))
        if fault == "vintage":
            rows[0]["vintage"] = "CURRENT_REVISED_HISTORY"
        if fault == "traversal":
            rows[0]["source_relative_artifact"] = "../outside.gz"
        _write_archive(archive, rows, sources)
    with pytest.raises(ValueError, match="HISTORY_"):
        load(archive)


def test_later_release_cannot_enter_older_event_history(archive):
    result = load_cc010_history(archive, series=NAMES, end_period="2026-09", cutoff_utc="2026-09-15T00:00:00Z")
    assert all(s["observations"][-1]["value"] is None for s in result["series"])
    with pytest.raises(ValueError, match="AT_LEAST_24"):
        month_window("2026-09", 23)


def test_retained_bls_summary_routes_keep_the_prior_release_clock(archive):
    history = history_for_source_pack([{"url": "https://www.bls.gov/news.release/cpi.nr0.htm",
        "published_at_utc": CUTOFF}], cutoff_utc="2026-11-05T00:00:00Z", archive_root=archive)
    assert history["window"] == ["2024-10", "2026-09"]
    assert history["cutoff_utc"] == "2026-10-14T12:30:00+00:00"


def test_component_chart_uses_reported_disjoint_effects_instead_of_weight_estimates(archive):
    rows = [json.loads(x) for x in (archive / "first_release_actuals.jsonl").read_bytes().splitlines()]
    manifest = json.loads((archive / "archive_manifest.json").read_bytes())
    body = ("<table id='cpipress6'><caption>Seasonally adjusted effect on All Items</caption>"
        "<tr><td>Food</td><td>10</td><td>5</td><td>0.001</td><td>x</td><td>x</td><td>x</td></tr>"
        "<tr><td>Energy</td><td>20</td><td>5</td><td>0.022</td><td>x</td><td>x</td><td>x</td></tr>"
        "<tr><td>All items less food and energy</td><td>70</td><td>5</td><td>0.333</td><td>x</td><td>x</td><td>x</td></tr></table>").encode()
    sha = hashlib.sha256(body).hexdigest()
    relative = "raw/" + sha + ".bin.gz"
    (archive / relative).write_bytes(gzip.compress(body))
    latest = [r for r in rows if r["reference_period"] == "2026-09"]
    manifest["sources"] = [s for s in manifest["sources"] if s["sha256"] != latest[0]["source_sha256"]]
    for row in latest:
        row.update(source_sha256=sha, source_relative_artifact=relative)
    manifest["sources"].append({"sha256": sha, "url": latest[0]["source_url"], "status": 200})
    _write_archive(archive, rows, manifest["sources"])
    result = load(archive)
    effects = result["components"]["effects"]
    assert [e["value"] for e in effects] == [0.001, 0.022, 0.333]
    assert all(e["unit"] == "percentage points" for e in effects)
    assert history_documents(result)[-1]["release_component_effects"]["capture_sha256"] == sha


def test_source_stage_joins_history_before_freeze_and_preserves_issued_packets(archive, tmp_path):
    pack = [{"source_id": "SOURCE_1", "url": "https://www.bls.gov/news.release/archives/cpi_10142026.htm",
        "published_at_utc": CUTOFF}]
    turn = SimpleNamespace(root=tmp_path / "operation", frozen_request=lambda _: None)
    kwargs = dict(source_pack=pack, article_mode="DATA_OR_DOCUMENT_LENS", cutoff_utc="2026-11-03T00:00:00Z", archive_root=archive)
    joined = enrich_source_pack(turn, **kwargs)
    assert len(joined) == 5 and joined[-1]["source_id"] == "SOURCE_5"
    assert joined[-1]["official_release_history"]["cutoff_utc"] == "2026-10-14T12:30:00+00:00"
    assert enrich_source_pack(turn, **kwargs) == joined
    turn.frozen_request = lambda _: {"already_issued": True}
    assert enrich_source_pack(turn, **kwargs) == joined
    turn.root = tmp_path / "old_operation_without_history"
    assert enrich_source_pack(turn, **kwargs) == pack
    assert enrich_source_pack(turn, **{**kwargs, "article_mode": "BREAKING_BRIEF"}) == pack
    assert history_for_source_pack([{"url": "https://example.org/news"}], cutoff_utc=CUTOFF, archive_root=archive) is None


@pytest.mark.parametrize("url", [
    "https://api.bls.gov/publicAPI/v1/timeseries/data/CUUR0000SA0?startyear=2024&endyear=2026",
    "https://www.bea.gov/sites/default/files/history.csv",
    "https://www.federalreserve.gov/datadownload/history.csv",
    "https://home.treasury.gov/resource-center/data-chart-center/history.csv",
])
def test_exact_official_history_fetch_reuses_shared_budget_without_retry(url):
    calls = []
    def get(url, timeout, size):
        calls.append(url)
        body = json.dumps({"status": "REQUEST_SUCCEEDED", "Results": {"series": [{"seriesID": "CUUR0000SA0", "data": []}]}}).encode()
        return {"status": 200, "final_url": url, "body": body, "content_truncated": False}
    budget = {"used": 0, "limit": 1}
    loader = BoundedOfficialPrimaryEvidenceLoader(evaluation_as_of_utc=CUTOFF, http_get=get,
        shared_request_budget=budget, clock=lambda: datetime(2026, 11, 3, tzinfo=timezone.utc))
    request = {"url": url, "rights_class": "PUBLIC_DOMAIN", "rights_evidence_sha256": "a"*64}
    result = loader.acquire_release_history(request)
    assert result["capture_sha256"] == hashlib.sha256(result["raw_bytes"]).hexdigest()
    assert result["vintage_basis"] == "CURRENT_CAPTURE_NOT_EVENT_TIME_PROOF"
    with pytest.raises(RuntimeError, match="budget_exhausted"):
        loader.acquire_release_history(request)
    assert len(calls) == 1 and budget["used"] == 1
    with pytest.raises(ValueError, match="DATED_ARCHIVE_VINTAGE"):
        loader.acquire_release_history({**request, "retrospective": True})
    assert len(calls) == 1


@pytest.mark.parametrize("chart_type", ["line", "grouped_bar"])
def test_missing_month_is_rendered_as_a_gap_and_cannot_be_filled(archive, tmp_path, chart_type):
    history = load(archive)
    doc = history_documents(history)[0]
    points = []
    for obs in history["series"][0]["observations"]:
        if obs["value"] is None:
            points.append({"period": obs["period"], "value": None, "observation_kind": "MISSING",
                "missing_reason": obs["missing_reason"], "inputs": [], "missing_binding": {
                    "document_id": doc["document_id"], "source_content_sha256": doc["canonical_content_sha256"]}})
        else:
            line = next(line for line in doc["canonical_content_text"].splitlines() if f"; {obs['period']};" in line)
            points.append({"period": obs["period"], "value": obs["value"], "observation_kind": "REPORTED_ACTUAL",
                "inputs": [{"document_id": doc["document_id"], "support_excerpt": line, "value_text": f"{obs['value']:g}",
                    "source_period_text": obs["period"], "source_content_sha256": doc["canonical_content_sha256"],
                    "metric": "CPI_HEADLINE_MOM", "unit": "percent", "prepared_period": obs["period"],
                    "period_basis": {"basis": "CONTROLLED_CC010_OBSERVATION"}}]})
    packet = {"asset_id": "controlled-history-gap", "chart_type": chart_type, "title": "Controlled fixture",
        "question": "Does the missing month remain a gap?", "unit": "percent", "source_caption": "BLS controlled fixture",
        "series": [{"name": "Controlled", "points": points}], "missingness": ["2025-10", "2025-11"]}
    assert _editorial_data_values(packet, [doc])[0][12:14] == [None, None]
    asset = build_editorial_data_chart(packet, [doc], output_dir=tmp_path / "render")
    assert asset["computed_values"][0][12:14] == [None, None]
    if chart_type == "grouped_bar":
        packet["history_point_labels"] = [{"series_index": 0, "period": "2026-09", "decimals": 1}]
        labelled = build_editorial_data_chart(packet, [doc], output_dir=tmp_path / "labelled")
        assert labelled["computed_values"] == asset["computed_values"]
        packet["history_point_labels"] = [{"series_index": 0, "period": "2025-10"}]
        with pytest.raises(ValueError, match="POINT_LABEL_UNBOUND"):
            build_editorial_data_chart(packet, [doc], output_dir=tmp_path / "invalid-label")
        packet.pop("history_point_labels")
    bad = deepcopy(packet)
    bad["series"][0]["points"][12]["missing_reason"] = "invented gap"
    with pytest.raises(ValueError, match="MISSING_POINT_UNBOUND"):
        _editorial_data_values(bad, [doc])


@pytest.fixture
def desk_export(archive, tmp_path, monkeypatch):
    import live_contentops.official_release_history_v1 as owner

    raw = (archive / "first_release_actuals.jsonl").read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    series = []
    for name in NAMES:
        official_id, unit, adjustment, measure = SERIES[name]
        points, gaps = [], []
        for row in rows:
            if row["series"] != name:
                continue
            period = row["reference_period"]
            gap = period == "2025-10"
            if gap:
                gaps.append({"x": period, "state": "MISSING", "value": None})
                continue
            points.append({"x": period, "value": row["value"], "state": row["availability"],
                "missing_reason": "TWO_MONTH_CHANGE_IS_NOT_MOM" if row["value"] is None else None,
                "rights_class": BLS_RIGHTS, "public_eligible": True, "lineage": [{
                    "source_id": "cc010-first-print", "source_series": official_id,
                    "source_url": row["source_url"], "vintage": row["vintage"],
                    "window": {"reference_period": period},
                    "capture_hash_verified": True, "archive_correction_notice": False,
                    "published_at_utc": row["release_datetime_utc"],
                    "captured_at_utc": row["retrieved_at_utc"], "known_at_utc": row["retrieved_at_utc"],
                    "capture_sha256": row["source_sha256"], "input_sha256": hashlib.sha256(raw).hexdigest(),
                }]})
        series.append({"family": "cpi", "series_id": name, "unit": unit, "seasonal_adjustment": adjustment,
            "vintage": owner.FIRST_PRINT, "measure": owner.DESK_MEASURES[measure], "points": points, "gaps": gaps})
    delivery = tmp_path / "producer-deliveries" / "cc-145"
    delivery.mkdir(parents=True)
    export = delivery / "public.json"
    export.write_text(json.dumps({"schema": "NewsroomDeskChartDataV1", "audience": "public",
        "public_export": True, "status": "READY", "series": series}), encoding="utf-8")
    (delivery / "private.json").write_text("THIS_MUST_NEVER_BE_READ", encoding="utf-8")
    config = tmp_path / "official_release_history_v1.json"
    config.write_text(json.dumps({"cc010_archive_root": str(tmp_path / "absent-archive"),
        "newsroom_desk_adapter": {"public_export_path": str(export)}}), encoding="utf-8")
    monkeypatch.setattr(owner, "HISTORY_CONFIG_PATH", config)
    return export


RELEASE_SOURCE = [{"url": "https://www.bls.gov/news.release/archives/cpi_10142026.htm",
                   "published_at_utc": CUTOFF}]


def test_desk_export_drives_native_source_and_release_chart(desk_export, tmp_path):
    from pathlib import Path
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, validate_release_media
    from live_contentops.official_release_history_v1 import history_chart_packet

    turn = SimpleNamespace(root=tmp_path / "operation", frozen_request=lambda _: None)
    kwargs = dict(source_pack=RELEASE_SOURCE, article_mode="STANDARD_NEWS_ANALYSIS", cutoff_utc=CUTOFF)
    docs = NativeDesktopTurn.release_history_sources(turn, **kwargs)
    history_path = turn.root / "official_release_history_v1.json"
    frozen_bytes = history_path.read_bytes()
    history = json.loads(frozen_bytes)
    assert history["producer"] == "CC-145"
    assert history["dataset_sha256"] == hashlib.sha256(desk_export.read_bytes()).hexdigest()
    assert history["window"] == ["2024-10", "2026-09"]
    assert {d["official_release_history"]["series"]["name"] for d in docs[1:]} == set(NAMES)
    yoy = [n for n in NAMES if n.endswith("_YOY")]
    packet = history_chart_packet(history, series_names=yoy, asset_id="cpi-yoy-history",
        title="Headline and core inflation", question="How did inflation change over time?",
        placement_after="Inflation trend")
    assert packet["history_lineage"]["producer"] == "CC-145"
    for series in packet["series"]:
        assert len(series["points"]) == 24
        assert series["points"][12]["value"] is None
        last = series["points"][-1]["inputs"][0]["period_basis"]
        assert last["dataset_sha256"] == history["dataset_sha256"]
        assert last["rights_class"] == BLS_RIGHTS and len(last["capture_sha256"]) == 64
    chart = build_editorial_data_chart(packet, docs, output_dir=tmp_path / "render")
    assert Path(chart["path"]).is_file()
    result = {"article": {"news_item_kind": "ANALYSIS"}, "media_assets": [chart], "evidence": docs}
    assert validate_release_media(result, require_pixel_review=False, prewriter=True)["chart_count"] == 1
    wrong_capture = deepcopy(packet)
    wrong_capture["series"][0]["points"][0]["inputs"][0]["period_basis"]["capture_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="CC145_OBSERVATION_UNBOUND"):
        _editorial_data_values(wrong_capture, docs)
    desk_export.unlink()
    turn.frozen_request = lambda _: {"already_issued": True}
    assert NativeDesktopTurn.release_history_sources(turn, **kwargs) == docs
    assert history_path.read_bytes() == frozen_bytes


@pytest.mark.parametrize("fault, error", [
    ("public_marker", "PUBLIC_PROJECTION"), ("rights", "PUBLIC_POINT_RIGHTS"),
    ("eligibility", "PUBLIC_POINT_RIGHTS"), ("capture", "FIRST_PRINT_LINEAGE"),
    ("dimensions", "SERIES_IDENTITY_OR_DIMENSION"), ("duplicate", "AMBIGUOUS_FIRST_PRINT"),
])
def test_desk_export_rejects_bad_public_bindings(desk_export, fault, error):
    from live_contentops.official_release_history_v1 import load_public_desk_history

    export = json.loads(desk_export.read_bytes())
    series = export["series"][0]
    point = series["points"][-1]
    if fault == "public_marker":
        export["audience"] = "private"
    elif fault == "rights":
        point["rights_class"] = "LICENSE_REQUIRED"
    elif fault == "eligibility":
        point["public_eligible"] = False
    elif fault == "capture":
        point["lineage"][0]["capture_hash_verified"] = False
    elif fault == "dimensions":
        series["unit"] = "index"
    elif fault == "duplicate":
        series["points"].append(deepcopy(point))
    desk_export.write_text(json.dumps(export), encoding="utf-8")
    with pytest.raises(ValueError, match=error):
        load_public_desk_history(desk_export, family="cpi", cutoff_utc=CUTOFF)


def test_desk_history_uses_release_cutoff_and_preserves_reported_missingness(desk_export):
    from live_contentops.official_release_history_v1 import load_public_desk_history

    history = load_public_desk_history(desk_export, family="cpi",
        cutoff_utc="2026-10-14T12:29:59Z", end_period="2026-09")
    for series in history["series"]:
        last = series["observations"][-1]
        assert last["period"] == "2026-09" and last["value"] is None and last["source_record"] is None
        first = next(o for o in series["observations"] if o["value"] is not None)["source_record"]
        assert first["release_datetime_utc"] < CUTOFF < first["known_at_utc"]
        missing = series["observations"][13]
        if series["name"].endswith("_MOM"):
            assert missing["value"] is None
            assert missing["missing_reason"] == "TWO_MONTH_CHANGE_IS_NOT_MOM"
            assert missing["source_record"]["source_sha256"]


def test_desk_export_failure_preserves_verified_archive_chart_source(desk_export, archive):
    from live_contentops.official_release_history_v1 import history_for_source_pack

    desk_export.unlink()
    history = history_for_source_pack(RELEASE_SOURCE, cutoff_utc=CUTOFF, archive_root=archive,
        desk_binding={"public_export_path": str(desk_export)})
    assert history["producer"] == "MAIN_CC010_FIRST_PRINT_ARCHIVE"
    assert history["window"] == ["2024-10", "2026-09"]
