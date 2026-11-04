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


def test_missing_month_is_rendered_as_a_gap_and_cannot_be_filled(archive, tmp_path):
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
    packet = {"asset_id": "controlled-history-gap", "chart_type": "line", "title": "Controlled fixture",
        "question": "Does the missing month remain a gap?", "unit": "percent", "source_caption": "BLS controlled fixture",
        "series": [{"name": "Controlled", "points": points}], "missingness": ["2025-10", "2025-11"]}
    assert _editorial_data_values(packet, [doc])[0][12:14] == [None, None]
    asset = build_editorial_data_chart(packet, [doc], output_dir=tmp_path / "render")
    assert asset["computed_values"][0][12:14] == [None, None]
    bad = deepcopy(packet)
    bad["series"][0]["points"][12]["missing_reason"] = "invented gap"
    with pytest.raises(ValueError, match="MISSING_POINT_UNBOUND"):
        _editorial_data_values(bad, [doc])


def test_source_stage_feeds_delivered_desk_series_to_writer_and_preserves_frozen_packet(archive, tmp_path, monkeypatch):
    import live_contentops.official_release_history_v1 as owner
    captured = {}
    projection = {"producer": "CC-145", "module_sha256": "a" * 64,
        "data": {"schema": "NewsroomDeskChartDataV1", "audience": "public", "public_export": True,
                 "series": [{"series_id": name, "points": [{"x": "2026-09", "value": 2.3,
                             "public_eligible": True}], "gaps": []} for name in NAMES]}}
    def query(history, *, archive_root):
        captured.update(window=history["window"], root=archive_root)
        return deepcopy(projection)
    monkeypatch.setattr(owner, "newsroom_desk_projection", query)
    turn = SimpleNamespace(root=tmp_path / "operation", frozen_request=lambda stage: None)
    source = [{"url": "https://www.bls.gov/news.release/archives/cpi_10142026.htm", "published_at_utc": CUTOFF}]
    docs = enrich_source_pack(turn, source_pack=source, article_mode="STANDARD_NEWS_ANALYSIS",
                             cutoff_utc=CUTOFF, archive_root=archive)
    joined = [d for d in docs if d.get("newsroom_desk_projection")]
    assert len(joined) == 4 and captured["window"] == ["2024-10", "2026-09"]
    assert {d["newsroom_desk_projection"]["data"]["series"][0]["series_id"] for d in joined} == set(NAMES)
    assert all(len(d["newsroom_desk_projection"]["data"]["series"]) == 1 for d in joined)
    before = (turn.root / "official_release_history_v1.json").read_bytes()
    monkeypatch.setattr(owner, "newsroom_desk_projection", lambda *a, **k: pytest.fail("Frozen source must not requery"))
    assert enrich_source_pack(turn, source_pack=source, article_mode="STANDARD_NEWS_ANALYSIS",
                              cutoff_utc=CUTOFF, archive_root=archive) == docs
    assert (turn.root / "official_release_history_v1.json").read_bytes() == before


def test_desk_adapter_is_reused_and_only_its_public_projection_enters(archive, tmp_path):
    from live_contentops.official_release_history_v1 import newsroom_desk_projection
    module = tmp_path / "delivered_adapter.py"
    module.write_text("def project(catalog, **kwargs):\n"
        "    assert kwargs['audience'] == 'public' and kwargs['event_cutoff_utc']\n"
        "    assert kwargs['start'] == '2024-10' and kwargs['end'] == '2026-09'\n"
        "    return {'schema':'NewsroomDeskChartDataV1','audience':'public','public_export':True,"
        "'series':[{'series_id':'CPI_HEADLINE_YOY','points':[{'public_eligible':True,'value':2.3}]}]}\n")
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps({"sources": [{"kind": "first_print", "root": str(archive)}]}))
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"newsroom_desk_adapter": {"module_path": str(module), "catalog_path": str(catalog)}}))
    value = newsroom_desk_projection(load(archive), archive_root=archive, config_path=config)
    assert value["data"]["series"][0]["points"][0]["value"] == 2.3
    assert value["module_sha256"] == hashlib.sha256(module.read_bytes()).hexdigest()
    module.write_text(module.read_text().replace("'public_eligible':True", "'public_eligible':False"))
    with pytest.raises(ValueError, match="PUBLIC_POINT_RIGHTS"):
        newsroom_desk_projection(load(archive), archive_root=archive, config_path=config)


def test_unavailable_desk_adapter_keeps_existing_verified_history_in_live_source_stage(archive, tmp_path, monkeypatch):
    import live_contentops.official_release_history_v1 as owner
    def unavailable(*args, **kwargs):
        raise FileNotFoundError("CC145_DELIVERED_MODULE_UNAVAILABLE")
    monkeypatch.setattr(owner, "newsroom_desk_projection", unavailable)
    turn = SimpleNamespace(root=tmp_path / "operation", frozen_request=lambda stage: None)
    source = [{"url": "https://www.bls.gov/news.release/archives/cpi_10142026.htm", "published_at_utc": CUTOFF}]
    docs = enrich_source_pack(turn, source_pack=source, article_mode="STANDARD_NEWS_ANALYSIS",
                             cutoff_utc=CUTOFF, archive_root=archive)
    assert len([d for d in docs if d.get("official_release_history")]) == 4
    saved = json.loads((turn.root / "official_release_history_v1.json").read_bytes())
    assert saved["newsroom_desk_projection_error"] == "CC145_DELIVERED_MODULE_UNAVAILABLE"
    assert all(not d.get("newsroom_desk_projection") for d in docs)
