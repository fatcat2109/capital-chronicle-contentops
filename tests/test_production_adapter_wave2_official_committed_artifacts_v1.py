from __future__ import annotations

from dataclasses import replace
from hashlib import sha1
import json
import os
from pathlib import Path
import subprocess

import pytest

from live_contentops import adaptive_learning_adapters_v2 as adapters
from live_contentops import content_intelligence_contracts_v2 as contracts
from live_contentops import production_evidence_adapters_wave2_v1 as wave2
from live_contentops import schema_aware_evidence_extraction_v1 as extraction
from live_contentops.generic_foundation_freeze_v1 import validate_foundation_freeze
from live_contentops.production_adapter_conformance_v1 import (
    PRODUCTION_ADAPTER_WAVE2_V1,
    run_adapter_conformance,
)


ROOT = Path(__file__).resolve().parents[1]
CUTOFF = "2026-07-22T00:00:00Z"


def _treasury(*, record_date: str = "2026-06-01", public_debt: str = "0") -> bytes:
    row = {
        "record_date": record_date, "debt_held_public_amt": public_debt,
        "intragov_hold_amt": "7614128912261.16", "tot_pub_debt_out_amt": "39195502287422.08",
        "src_line_nbr": "1", "record_fiscal_year": "2026", "record_fiscal_quarter": "3",
        "record_calendar_year": "2026", "record_calendar_quarter": "2",
        "record_calendar_month": "06", "record_calendar_day": "01",
    }
    data_types = {
        "record_date": "DATE", "debt_held_public_amt": "CURRENCY",
        "intragov_hold_amt": "CURRENCY", "tot_pub_debt_out_amt": "CURRENCY",
        "src_line_nbr": "INTEGER", "record_fiscal_year": "YEAR",
        "record_fiscal_quarter": "QUARTER", "record_calendar_year": "YEAR",
        "record_calendar_quarter": "QUARTER", "record_calendar_month": "MONTH",
        "record_calendar_day": "DAY",
    }
    links = {"self": "local:self", "first": "local:first", "prev": None, "next": None, "last": "local:last"}
    return json.dumps({"data": [row], "meta": {"count": 1, "dataTypes": data_types}, "links": links}, separators=(",", ":")).encode()


def _bls(*, year: str = "2026", period: str = "M05", period_name: str = "May", value: str = "0") -> bytes:
    return json.dumps({
        "status": "REQUEST_SUCCEEDED", "responseTime": 1, "message": [],
        "Results": {"series": [{"seriesID": "LNS14000000", "data": [{
            "year": year, "period": period, "periodName": period_name,
            "latest": "true", "value": value, "footnotes": [{}],
        }]}]},
    }, separators=(",", ":")).encode()


def _fomc(*, official: bool = True, year: str = "2026", month: str = "January", dates: str = "27-28") -> bytes:
    url = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm" if official else "https://example.invalid/"
    return f'''<!doctype html><html><head><meta property="og:url" content="{url}" /></head><body>
<h4><a id="42828">{year} FOMC Meetings</a></h4>
<div class="row fomc-meeting" "><div class="fomc-meeting__month"><strong>{month}</strong></div>
<div class="fomc-meeting__date">{dates}</div><a href="/newsevents/pressreleases/monetary20260128a.htm">HTML</a></div>
<h4><a id="42827">2025 FOMC Meetings</a></h4></body></html>'''.encode()


ARTIFACTS = {
    wave2.TREASURY_EXTRACTOR_ID: (_treasury, wave2.TREASURY_PATH, wave2.TREASURY_SCHEMA, {"record_date": "2026-06-01"}),
    wave2.BLS_EXTRACTOR_ID: (_bls, wave2.BLS_PATH, wave2.BLS_SCHEMA, {"series_id": "LNS14000000", "year": "2026", "period": "M05"}),
    wave2.FOMC_EXTRACTOR_ID: (_fomc, wave2.FOMC_PATH, wave2.FOMC_SCHEMA, {"year": "2026", "month": "January", "meeting_dates": "27-28"}),
}


def _receipt(data: bytes, extractor_id: str):
    registry = adapters.load_trusted_verifier_registry(ROOT)
    extractor = extraction.load_extractor_registry(ROOT).resolve(extractor_id, wave2.EXTRACTOR_VERSION)
    _, path, schema, _ = ARTIFACTS[extractor_id]
    blob = sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
    return contracts.build_verified_producer_artifact_receipt_v1(
        data, registry=registry, verifier_id=wave2.VERIFIER_ID, verifier_version="v1",
        repository=wave2.UPSTREAM_REPOSITORY, branch=wave2.UPSTREAM_BRANCH,
        producer_commit="1" * 40, artifact_path=path, expected_git_blob_sha1=blob,
        artifact_schema_version=schema, producer_version=extractor.shape_contract_id,
        artifact_cutoff_utc="2026-06-10T00:00:00Z", evidence_refs=(),
        source_authority_class="official_public_data", resolved_repository=wave2.UPSTREAM_REPOSITORY,
        resolved_branch=wave2.UPSTREAM_BRANCH, resolved_commit="1" * 40,
        resolved_artifact_path=path, branch_head_observed="2" * 40,
        producer_commit_reachable_from_branch=True, verification_time_utc=CUTOFF,
    )


def _extract(data: bytes, extractor_id: str, **changes):
    _, _, _, selector = ARTIFACTS[extractor_id]
    kwargs = {
        "receipt": _receipt(data, extractor_id), "registry": extraction.load_extractor_registry(ROOT),
        "extractor_id": extractor_id, "extractor_version": wave2.EXTRACTOR_VERSION, "selector": selector,
        "feature_targets": ("evidence_completeness", "freshness"), "decision_cutoff_utc": CUTOFF,
    }
    kwargs.update(changes)
    return wave2.extract_wave2_artifact_evidence(data, **kwargs)


@pytest.mark.parametrize("extractor_id", tuple(ARTIFACTS))
def test_valid_wave2_extraction_is_bounded_and_deterministic(extractor_id):
    factory, _, _, _ = ARTIFACTS[extractor_id]
    data = factory()
    first = _extract(data, extractor_id)
    assert first == _extract(data, extractor_id)
    record, features = first
    assert record.authority_state == "OFFICIAL_VERIFIED"
    assert record.permission_state == "CONTEXT_ONLY"
    assert record.evidence_roles == (contracts.EvidenceRole.FEATURE_SUPPORT,)
    assert record.qualification_status == "NOT_QUALIFYING_GOVERNED"
    assert record.observed_at_utc is not None
    assert record.known_at_utc == "2026-06-10T00:00:00Z"
    assert next(row for row in features if row.feature_id == "evidence_completeness").value == 1.0
    freshness = next(row for row in features if row.feature_id == "freshness")
    assert freshness.value == 0.0 and freshness.availability == contracts.AvailabilityState.EXPLICIT_ZERO


def test_explicit_numeric_zero_is_preserved_as_present_evidence():
    zero_record, zero_features = _extract(_treasury(public_debt="0"), wave2.TREASURY_EXTRACTOR_ID)
    nonzero_record, _ = _extract(_treasury(public_debt="1"), wave2.TREASURY_EXTRACTOR_ID)
    assert zero_record.extracted_record_hash != nonzero_record.extracted_record_hash
    assert zero_features[0].value == 1.0
    bls_zero, _ = _extract(_bls(value="0"), wave2.BLS_EXTRACTOR_ID)
    bls_nonzero, _ = _extract(_bls(value="4.3"), wave2.BLS_EXTRACTOR_ID)
    assert bls_zero.extracted_record_hash != bls_nonzero.extracted_record_hash


def test_treasury_malformed_shape_count_date_numeric_and_selector_rejected():
    with pytest.raises(ValueError, match="treasury_debt_json_malformed"):
        _extract(b"{", wave2.TREASURY_EXTRACTOR_ID)
    bad_count = json.loads(_treasury())
    bad_count["meta"]["count"] = 2
    with pytest.raises(ValueError, match="treasury_debt_count_mismatch"):
        _extract(json.dumps(bad_count).encode(), wave2.TREASURY_EXTRACTOR_ID)
    missing_type = json.loads(_treasury())
    del missing_type["meta"]["dataTypes"]["debt_held_public_amt"]
    with pytest.raises(ValueError, match="datatype_contract_mismatch"):
        _extract(json.dumps(missing_type).encode(), wave2.TREASURY_EXTRACTOR_ID)
    wrong_type = json.loads(_treasury())
    wrong_type["meta"]["dataTypes"]["record_date"] = "STRING"
    with pytest.raises(ValueError, match="datatype_contract_mismatch"):
        _extract(json.dumps(wrong_type).encode(), wave2.TREASURY_EXTRACTOR_ID)
    wrong_numeric_type = json.loads(_treasury())
    wrong_numeric_type["meta"]["dataTypes"]["debt_held_public_amt"] = "NUMBER"
    with pytest.raises(ValueError, match="datatype_contract_mismatch"):
        _extract(json.dumps(wrong_numeric_type).encode(), wave2.TREASURY_EXTRACTOR_ID)
    missing_selected_field = json.loads(_treasury())
    del missing_selected_field["data"][0]["tot_pub_debt_out_amt"]
    with pytest.raises(ValueError, match="required_field_missing"):
        _extract(json.dumps(missing_selected_field).encode(), wave2.TREASURY_EXTRACTOR_ID)
    bad_links = json.loads(_treasury())
    del bad_links["links"]["last"]
    with pytest.raises(ValueError, match="links_shape_mismatch"):
        _extract(json.dumps(bad_links).encode(), wave2.TREASURY_EXTRACTOR_ID)
    with pytest.raises(ValueError, match="record_date_invalid"):
        _extract(_treasury(record_date="2026-99-01"), wave2.TREASURY_EXTRACTOR_ID, selector={"record_date": "2026-99-01"})
    with pytest.raises(ValueError, match="numeric_value_invalid"):
        _extract(_treasury(public_debt="not-a-number"), wave2.TREASURY_EXTRACTOR_ID)
    with pytest.raises(ValueError, match="record_selector_not_unique"):
        _extract(_treasury(), wave2.TREASURY_EXTRACTOR_ID, selector={"record_date": "2026-06-02"})


def test_bls_malformed_period_shape_value_and_selector_rejected():
    with pytest.raises(ValueError, match="bls_unemployment_json_malformed"):
        _extract(b"[]", wave2.BLS_EXTRACTOR_ID)
    with pytest.raises(ValueError, match="period_invalid"):
        _extract(_bls(period="M13", period_name="Unknown"), wave2.BLS_EXTRACTOR_ID, selector={"series_id": "LNS14000000", "year": "2026", "period": "M13"})
    with pytest.raises(ValueError, match="period_name_mismatch"):
        _extract(_bls(period_name="June"), wave2.BLS_EXTRACTOR_ID)
    with pytest.raises(ValueError, match="value_invalid"):
        _extract(_bls(value="-"), wave2.BLS_EXTRACTOR_ID)
    with pytest.raises(ValueError, match="series_selector_not_unique"):
        _extract(_bls(), wave2.BLS_EXTRACTOR_ID, selector={"series_id": "OTHER", "year": "2026", "period": "M05"})


def test_fomc_official_shape_selector_link_and_future_timestamp_rejected():
    with pytest.raises(ValueError, match="official_shape_mismatch"):
        _extract(_fomc(official=False), wave2.FOMC_EXTRACTOR_ID)
    with pytest.raises(ValueError, match="meeting_selector_not_unique"):
        _extract(_fomc(), wave2.FOMC_EXTRACTOR_ID, selector={"year": "2026", "month": "March", "meeting_dates": "17-18"})
    with pytest.raises(ValueError, match="dated_document_link_missing"):
        _extract(_fomc().replace(b"monetary20260128", b"monetary20260127"), wave2.FOMC_EXTRACTOR_ID)
    with pytest.raises(ValueError, match="internal_future_timestamp"):
        _extract(_fomc(), wave2.FOMC_EXTRACTOR_ID, decision_cutoff_utc="2026-01-01T00:00:00Z")


def test_fomc_exact_container_selects_statement_among_sibling_documents():
    meeting = _fomc().replace(
        b'</a></div>',
        b'</a><a href="/newsevents/pressreleases/monetary20260128a1.htm">Implementation Note</a>'
        b'<a href="/monetarypolicy/fomcpressconf20260128.htm">Press Conference</a></div>',
        1,
    )
    record, _ = _extract(meeting, wave2.FOMC_EXTRACTOR_ID)
    baseline, _ = _extract(_fomc(), wave2.FOMC_EXTRACTOR_ID)
    assert record.extracted_record_hash == baseline.extracted_record_hash
    assert record.published_at_utc == "2026-01-28T00:00:00Z"
    assert record.source_fields_used == (
        "official_url", "year", "month", "meeting_dates", "decision_date", "dated_document_href",
    )


def test_fomc_does_not_cross_into_next_meeting_container_for_statement():
    first = _fomc().replace(b"monetary20260128", b"monetary20260127")
    next_meeting = b'''<div class="row fomc-meeting"><div class="fomc-meeting__month"><strong>March</strong></div>
<div class="fomc-meeting__date">17-18</div><a href="/newsevents/pressreleases/monetary20260128a.htm">wrong meeting</a></div>'''
    artifact = first.replace(b'<h4><a id="42827">', next_meeting + b'<h4><a id="42827">')
    with pytest.raises(ValueError, match="dated_document_link_missing"):
        _extract(artifact, wave2.FOMC_EXTRACTOR_ID)


def test_timestamp_classes_do_not_masquerade_observation_as_release():
    treasury, _ = _extract(_treasury(), wave2.TREASURY_EXTRACTOR_ID)
    bls, _ = _extract(_bls(), wave2.BLS_EXTRACTOR_ID)
    fomc, _ = _extract(_fomc(), wave2.FOMC_EXTRACTOR_ID)
    assert treasury.observed_at_utc == "2026-06-01T00:00:00Z" and treasury.published_at_utc is None
    assert bls.observed_at_utc == "2026-05-01T00:00:00Z" and bls.published_at_utc is None
    assert fomc.observed_at_utc == "2026-01-28T00:00:00Z"
    assert fomc.published_at_utc == "2026-01-28T00:00:00Z"
    assert {treasury.known_at_utc, bls.known_at_utc, fomc.known_at_utc} == {"2026-06-10T00:00:00Z"}


def test_byte_mismatch_and_caller_upgrades_rejected():
    data = _treasury()
    with pytest.raises(ValueError, match="consumed_bytes_receipt_mismatch"):
        wave2.extract_wave2_artifact_evidence(
            data + b" ", receipt=_receipt(data, wave2.TREASURY_EXTRACTOR_ID),
            registry=extraction.load_extractor_registry(ROOT), extractor_id=wave2.TREASURY_EXTRACTOR_ID,
            extractor_version=wave2.EXTRACTOR_VERSION, selector={"record_date": "2026-06-01"},
            feature_targets=("freshness",), decision_cutoff_utc=CUTOFF,
        )
    for field, value, reason in [
        ("authority_state", "FIRST_PARTY_VERIFIED", "caller_authority_upgrade_forbidden"),
        ("permission_state", "PUBLIC_CLAIM_ALLOWED", "caller_permission_upgrade_forbidden"),
        ("evidence_roles", (contracts.EvidenceRole.NEW_PHASE,), "caller_evidence_role_addition_forbidden"),
    ]:
        with pytest.raises(ValueError, match=reason):
            _extract(data, wave2.TREASURY_EXTRACTOR_ID, **{field: value})


def _git(repo: Path, *args: str, env=None) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, env=env).stdout.strip()


@pytest.fixture()
def advanced_branch_repo(tmp_path: Path):
    repo = tmp_path / "upstream"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Wave Tests")
    _git(repo, "config", "user.email", "wave@example.invalid")
    for spec, factory in zip(PRODUCTION_ADAPTER_WAVE2_V1, (_treasury, _bls, _fomc), strict=True):
        target = repo / spec.artifact_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(factory())
    env = {**os.environ, "GIT_AUTHOR_DATE": "2026-06-10T00:00:00Z", "GIT_COMMITTER_DATE": "2026-06-10T00:00:00Z"}
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "pinned artifacts", env=env)
    pinned = _git(repo, "rev-parse", "HEAD")
    (repo / "unrelated.txt").write_text("branch advanced\n", encoding="utf-8")
    _git(repo, "add", "unrelated.txt")
    _git(repo, "commit", "-m", "advance branch", env=env)
    return repo, pinned, _git(repo, "rev-parse", "HEAD")


def test_branch_advancement_keeps_pinned_commit_separate_from_observed_head(advanced_branch_repo):
    repo, pinned, observed = advanced_branch_repo
    for spec in PRODUCTION_ADAPTER_WAVE2_V1:
        result = run_adapter_conformance(
            replace(spec, expected_git_blob_sha1=None, expected_byte_sha256=None),
            repo_root=ROOT, upstream_git_repository=repo, upstream_commit=pinned,
            branch_authority_ref="refs/heads/main",
        )
        assert result["status"] == "PASS"
        assert result["upstream"]["producer_commit"] == pinned
        assert result["upstream"]["branch_head_observed"] == observed
        assert pinned != observed and result["upstream"]["commit_reachable_from_branch"] is True


def test_unreachable_pinned_commit_is_rejected(advanced_branch_repo, tmp_path):
    repo, _, _ = advanced_branch_repo
    other = tmp_path / "other"
    other.mkdir()
    _git(other, "init", "-b", "other")
    _git(other, "config", "user.name", "Other")
    _git(other, "config", "user.email", "other@example.invalid")
    (other / "x").write_text("x", encoding="utf-8")
    _git(other, "add", "x")
    _git(other, "commit", "-m", "unrelated")
    foreign = _git(other, "rev-parse", "HEAD")
    _git(repo, "fetch", str(other), foreign)
    spec = replace(PRODUCTION_ADAPTER_WAVE2_V1[0], expected_git_blob_sha1=None, expected_byte_sha256=None)
    with pytest.raises(ValueError, match="not_reachable_from_observed_branch"):
        run_adapter_conformance(spec, repo_root=ROOT, upstream_git_repository=repo, upstream_commit=foreign, branch_authority_ref="refs/heads/main")


def test_append_only_registries_and_frozen_manifest_integrity():
    assert not validate_foundation_freeze(ROOT)
    verifiers = adapters.load_trusted_verifier_registry(ROOT)
    extractors = extraction.load_extractor_registry(ROOT)
    assert verifiers.registry_version == "trusted-evidence-registry-1.3.0"
    assert extractors.registry_version == "artifact-evidence-extractor-registry-1.3.0"
    assert verifiers.resolve(wave2.VERIFIER_ID, "v1") is not None
    assert all(extractors.resolve(extractor_id, wave2.EXTRACTOR_VERSION) is not None for extractor_id in ARTIFACTS)


def test_exact_inventory_pins_are_complete():
    assert set(wave2.PINNED_ARTIFACTS) == set(ARTIFACTS)
    assert all(row["producer_commit"] != wave2.OBSERVED_UPSTREAM_HEAD for row in wave2.PINNED_ARTIFACTS.values())
    assert all(len(row["git_blob_sha1"]) == 40 and len(row["byte_sha256"]) == 64 for row in wave2.PINNED_ARTIFACTS.values())
