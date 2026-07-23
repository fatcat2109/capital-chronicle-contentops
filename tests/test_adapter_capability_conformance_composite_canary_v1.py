from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess

from live_contentops import content_intelligence_contracts_v2 as contracts
from live_contentops import production_adapter_contract_coverage_v1 as coverage
from live_contentops import schema_aware_evidence_extraction_v1 as extraction
from live_contentops.production_adapter_conformance_v1 import (
    PRODUCTION_ADAPTERS_V1,
    PRODUCTION_ADAPTER_BATCH_TREASURY_CFTC_H41_V1,
    PRODUCTION_ADAPTER_WAVE2_V1,
    PRODUCTION_ADAPTER_WAVE3_V1,
    run_composite_adapter_canary,
)


ROOT = Path(__file__).resolve().parents[1]
ALL_SPECS = (
    PRODUCTION_ADAPTERS_V1
    + PRODUCTION_ADAPTER_BATCH_TREASURY_CFTC_H41_V1
    + PRODUCTION_ADAPTER_WAVE2_V1
    + PRODUCTION_ADAPTER_WAVE3_V1
)


def _spec(adapter_id: str):
    return next(row for row in ALL_SPECS if row.adapter_id == adapter_id)


def test_all_accepted_adapters_have_complete_versioned_capability_bindings():
    assert len(ALL_SPECS) == 13
    assert len({row.adapter_id for row in ALL_SPECS}) == len(ALL_SPECS)
    for spec in ALL_SPECS:
        binding = spec.capability_binding
        assert binding.adapter_id == spec.adapter_id
        assert not binding.validate()
        assert binding.schema_version == "contentops.production_adapter_capability_binding.v1"
        assert binding.contract_version == "contentops.production_adapter_capabilities.v1.0.0"
        assert binding.dimensions.scheduled_event_state is not None
        assert binding.dimensions.source_authority_classes


def test_required_capability_semantics_are_truthful_and_not_hardcoded():
    usgs = _spec("usgs_earthquake_geojson_v1").capability_binding
    assert usgs.dimensions.evidence_modalities == (contracts.EvidenceModality.GEOSPATIAL_OR_PHYSICAL_OBSERVATION,)
    assert contracts.TemporalCharacter.UNSCHEDULED in usgs.dimensions.temporal_characters
    assert contracts.EvidenceModality.NUMERIC_TIME_SERIES not in usgs.dimensions.evidence_modalities
    assert usgs.physical_geographic_capability and usgs.dimensions.geography_ids == ("alaska",)

    fomc = _spec("federal_reserve_fomc_calendar_html_v1").capability_binding.dimensions
    assert contracts.EvidenceModality.EVENT_CALENDAR in fomc.evidence_modalities
    assert contracts.TemporalCharacter.SCHEDULED in fomc.temporal_characters
    assert fomc.story_modes == (contracts.StoryMode.POLICY_DECISION,)

    for adapter_id in ("bls_series_observation_v1", "bls_unemployment_series_v1"):
        dims = _spec(adapter_id).capability_binding.dimensions
        assert contracts.EvidenceModality.NUMERIC_TIME_SERIES in dims.evidence_modalities
        assert contracts.TemporalCharacter.PERIOD_OBSERVATION in dims.temporal_characters
        assert contracts.StoryMode.DATA_RELEASE in dims.story_modes

    cftc = _spec("cftc_legacy_futures_only_cot_v1").capability_binding.dimensions
    assert contracts.EvidenceModality.OFFICIAL_TABLE in cftc.evidence_modalities
    assert contracts.TemporalCharacter.PERIOD_OBSERVATION in cftc.temporal_characters

    h41 = _spec("federal_reserve_h41_zip_structure_v1").capability_binding
    assert contracts.TemporalCharacter.REVISED_RELEASE in h41.dimensions.temporal_characters
    assert h41.numeric_truth_quarantined and h41.dimensions.numeric_evidence_present is False

    for adapter_id in ("us_treasury_tic_official_html_v1", "fhfa_hpi_official_html_v1"):
        dims = _spec(adapter_id).capability_binding.dimensions
        assert contracts.EvidenceModality.QUALITATIVE_CONTEXT in dims.evidence_modalities
        assert contracts.StoryMode.DATA_RELEASE not in dims.story_modes


def test_every_enabled_extractor_has_exact_immutable_runtime_and_evidence_proof():
    registry = extraction.load_extractor_registry(ROOT)
    report = coverage.validate_registry_contract_coverage(registry, repo_root=ROOT)
    assert report["status"] == "PASS"
    assert report["starting_authority_sha"] == "a00a702dc97c2485852ab82a70707940ed8b2083"
    runtime = [row for row in report["rows"] if row["classification"] == "RUNTIME_IMPLEMENTED_IMMUTABLY_BOUND"]
    assert len(runtime) == 16
    assert all(row["record_hash_verified"] and row["accepted_evidence_verified"] for row in runtime)
    assert all(row["accepted_evidence_binding"]["accepted_commit"] != "HEAD" for row in runtime)


def _git(repo: Path, *args: str, env=None) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, env=env).stdout.strip()


def _bls() -> bytes:
    return json.dumps({
        "status": "REQUEST_SUCCEEDED", "responseTime": 1, "message": [],
        "Results": {"series": [{"seriesID": "LNS14000000", "data": [{
            "year": "2026", "period": "M05", "periodName": "May", "latest": "true",
            "value": "0", "footnotes": [{}],
        }]}]},
    }, separators=(",", ":")).encode()


def _fomc() -> bytes:
    return b'''<!doctype html><html><head><meta property="og:url" content="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm" /></head><body>
<h4><a id="42828">2026 FOMC Meetings</a></h4><div class="row fomc-meeting" "><div class="fomc-meeting__month"><strong>January</strong></div>
<div class="fomc-meeting__date">27-28</div><a href="/newsevents/pressreleases/monetary20260128a.htm">HTML</a></div>
<h4><a id="42827">2025 FOMC Meetings</a></h4></body></html>'''


def _usgs() -> bytes:
    return json.dumps({
        "type": "FeatureCollection",
        "metadata": {"generated": 1783633997000, "url": "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=1", "title": "USGS Earthquakes", "status": 200, "api": "2.7.0", "limit": 1, "offset": 1},
        "features": [{"type": "Feature", "properties": {"mag": 0.0, "place": "79 km SE of Kokhanok, Alaska", "time": 1783633608405, "updated": 1783633705342, "status": "automatic", "tsunami": 0}, "geometry": {"type": "Point", "coordinates": [-153.978, 58.854, 99.1]}, "id": "aka2026nmtsmu"}],
    }, separators=(",", ":")).encode()


def _tic() -> bytes:
    canonical = "https://home.treasury.gov/data/treasury-international-capital-tic-system"
    return f'''<!DOCTYPE html><html><head><link rel="canonical" href="{canonical}" /><meta property="og:site_name" content="U.S. Department of the Treasury"/><meta property="og:url" content="{canonical}"/><meta property="og:updated_time" content="2026-06-15"/><title>Treasury International Capital (TIC) System | U.S. Department of the Treasury</title></head><body></body></html>'''.encode()


def test_composite_canary_is_portable_deterministic_distinct_and_no_publication(tmp_path: Path):
    repo = tmp_path / "upstream"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Composite Tests")
    _git(repo, "config", "user.email", "composite@example.invalid")
    base_specs = (PRODUCTION_ADAPTER_WAVE2_V1[1], PRODUCTION_ADAPTER_WAVE2_V1[2], PRODUCTION_ADAPTER_WAVE3_V1[1], PRODUCTION_ADAPTER_WAVE3_V1[0])
    for spec, payload in zip(base_specs, (_bls(), _fomc(), _usgs(), _tic()), strict=True):
        target = repo / spec.artifact_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    env = {**os.environ, "GIT_AUTHOR_DATE": "2026-07-10T00:00:00Z", "GIT_COMMITTER_DATE": "2026-07-10T00:00:00Z"}
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "composite fixtures", env=env)
    pinned = _git(repo, "rev-parse", "HEAD")
    (repo / "branch-advance.txt").write_text("advance\n", encoding="utf-8")
    _git(repo, "add", "branch-advance.txt")
    _git(repo, "commit", "-m", "advance branch", env=env)
    specs = tuple(replace(
        spec, pinned_producer_commit=pinned,
        expected_git_blob_sha1=None, expected_byte_sha256=None,
    ) for spec in base_specs)
    kwargs = {
        "repo_root": ROOT, "upstream_git_repository": repo,
        "branch_authority_ref": "refs/heads/main", "adapter_specs": specs,
    }
    first = run_composite_adapter_canary(**kwargs)
    assert first == run_composite_adapter_canary(**kwargs)
    assert first["status"] == "PASS" and all(first["checks"].values())
    assert first["adapter_count"] == 4 and len(set(first["evidence_refs"])) == 4
    assert first["aggregation_disposition"] == "NO_CROSS_ADAPTER_AGGREGATION_EXACT_SINGLETON_FEATURE_SETS"
    assert first["publication_authority_granted"] is False and first["writes_performed"] == 0
    assert all(row["upstream"]["producer_commit"] == pinned for row in first["results"])
