from __future__ import annotations

from dataclasses import replace
from hashlib import sha1
import io
import json
import os
from pathlib import Path
import subprocess
import zipfile

import pytest

from live_contentops import adaptive_learning_adapters_v2 as adapters
from live_contentops import content_intelligence_contracts_v2 as contracts
from live_contentops import production_evidence_adapters_batch_v1 as batch
from live_contentops import schema_aware_evidence_extraction_v1 as extraction
from live_contentops.generic_foundation_freeze_v1 import validate_foundation_freeze
from live_contentops.production_adapter_conformance_v1 import (
    PRODUCTION_ADAPTER_BATCH_TREASURY_CFTC_H41_V1,
    run_adapter_conformance,
)


ROOT = Path(__file__).resolve().parents[1]
CUTOFF = "2026-07-22T00:00:00Z"


def _treasury(*, updated: str = "2026-06-06T11:44:25Z", namespace: str = batch.ATOM_NS) -> bytes:
    return f'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="{namespace}" xmlns:d="{batch.ODATA_DATA_NS}" xmlns:m="{batch.ODATA_METADATA_NS}">
  <updated>{updated}</updated>
  <entry><content type="application/xml"><m:properties>
    <d:Id>1887</d:Id><d:NEW_DATE>1991-03-14T00:00:00</d:NEW_DATE>
    <d:BC_3MONTH>5.94</d:BC_3MONTH><d:BC_10YEAR>8.02</d:BC_10YEAR>
  </m:properties></content></entry>
</feed>'''.encode()


def _cftc(*, invalid_date: bool = False, short: bool = False, compact: str = "260602") -> bytes:
    layout = batch.load_cftc_layout_contract(ROOT)
    values = {name: "1" for name in layout["ordered_columns"]}
    values.update({
        "market_and_exchange_names": "WHEAT-SRW - CHICAGO BOARD OF TRADE",
        "as_of_date_in_form_yymmdd": compact,
        "as_of_date_in_form_yyyy_mm_dd": "2026-99-02" if invalid_date else "2026-06-02",
        "cftc_contract_market_code": "001602",
        "cftc_market_code_in_initials": "CBT",
        "cftc_region_code": "00", "cftc_commodity_code": "001",
        "open_interest_all": "482332",
    })
    row = [values[name] for name in layout["ordered_columns"]]
    if short:
        row.pop()
    output = io.StringIO(newline="")
    __import__("csv").writer(output).writerow(row)
    return output.getvalue().encode()


def _h41(
    *, data_xml: bytes | None = None, common_xsd: bytes | None = None,
    extra: tuple[str, bytes] | None = None, duplicate: bool = False,
) -> bytes:
    h41_xsd = f'''<xs:schema xmlns:xs="{batch.XSD_NS}" targetNamespace="{batch.H41_SERIES_NS}">
      <xs:element name="Series"/><xs:attribute name="CATEGORY"/><xs:attribute name="COMPONENT"/>
      <xs:attribute name="DISTRIBUTION"/><xs:attribute name="SERIESTYPE"/><xs:attribute name="SUBCATEGORY"/>
    </xs:schema>'''.encode()
    common_xsd = common_xsd or f'''<xs:schema xmlns:xs="{batch.XSD_NS}" targetNamespace="{batch.H41_COMMON_NS}">
      <xs:element name="DataSet"/><xs:element name="Obs"/><xs:element name="Series"/>
      <xs:attribute name="OBS_STATUS"/><xs:attribute name="OBS_VALUE"/><xs:attribute name="TIME_PERIOD"/>
    </xs:schema>'''.encode()
    structure = f'''<m:Structure xmlns:m="{batch.SDMX_MESSAGE_NS}"><m:Header>
      <m:ID>H41</m:ID><m:Name>Factors Affecting Reserve Balances (H.4.1)</m:Name>
    </m:Header></m:Structure>'''.encode()
    data_xml = data_xml or f'''<m:MessageGroup xmlns:m="{batch.SDMX_MESSAGE_NS}" xmlns:h="{batch.H41_SERIES_NS}" xmlns:c="{batch.H41_COMMON_NS}">
      <c:DataSet><h:Series SERIES_NAME="H0.TEST" FREQ="19" CATEGORY="ASSET" COMPONENT="TEST" UNIT="Currency" UNIT_MULT="1000000">
        <c:Obs OBS_STATUS="A" OBS_VALUE="10450" TIME_PERIOD="2026-06-03"/>
      </h:Series></c:DataSet></m:MessageGroup>'''.encode()
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("H41_H41.xsd", h41_xsd)
        archive.writestr("H41_data.xml", data_xml)
        archive.writestr("H41_struct.xml", structure)
        archive.writestr("frb_common.xsd", common_xsd)
        if extra:
            archive.writestr(*extra)
        if duplicate:
            archive.writestr("H41_data.xml", data_xml)
    return output.getvalue()


ARTIFACTS = {
    batch.TREASURY_EXTRACTOR_ID: (_treasury, batch.TREASURY_PATH, batch.TREASURY_SCHEMA, {"record_date": "1991-03-14", "maturity": "BC_10YEAR"}),
    batch.CFTC_EXTRACTOR_ID: (_cftc, batch.CFTC_PATH, batch.CFTC_SCHEMA, {"contract_market_code": "001602", "report_date": "2026-06-02"}),
    batch.H41_EXTRACTOR_ID: (_h41, batch.H41_PATH, batch.H41_SCHEMA, {"dataset_id": "H41"}),
}


def _receipt(data: bytes, extractor_id: str):
    registry = adapters.load_trusted_verifier_registry(ROOT)
    extractors = extraction.load_extractor_registry(ROOT)
    extractor = extractors.resolve(extractor_id, "v1")
    _, path, schema, _ = ARTIFACTS[extractor_id]
    blob = sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()
    return contracts.build_verified_producer_artifact_receipt_v1(
        data, registry=registry, verifier_id=batch.VERIFIER_ID, verifier_version=batch.VERIFIER_VERSION,
        repository=batch.UPSTREAM_REPOSITORY, branch=batch.UPSTREAM_BRANCH,
        producer_commit="1" * 40, artifact_path=path, expected_git_blob_sha1=blob,
        artifact_schema_version=schema, producer_version=extractor.shape_contract_id,
        artifact_cutoff_utc="2026-06-07T00:00:00Z", evidence_refs=(),
        source_authority_class="official_public_data", resolved_repository=batch.UPSTREAM_REPOSITORY,
        resolved_branch=batch.UPSTREAM_BRANCH, resolved_commit="1" * 40,
        resolved_artifact_path=path, branch_head_observed="1" * 40,
        producer_commit_reachable_from_branch=True, verification_time_utc=CUTOFF,
    )


def _extract(data: bytes, extractor_id: str, **changes):
    _, _, _, selector = ARTIFACTS[extractor_id]
    kwargs = {
        "receipt": _receipt(data, extractor_id), "registry": extraction.load_extractor_registry(ROOT),
        "extractor_id": extractor_id, "extractor_version": "v1", "selector": selector,
        "feature_targets": ("evidence_completeness", "freshness"),
        "decision_cutoff_utc": CUTOFF, "repo_root": ROOT,
    }
    kwargs.update(changes)
    return batch.extract_production_artifact_evidence(data, **kwargs)


@pytest.mark.parametrize("extractor_id", tuple(ARTIFACTS))
def test_valid_extraction_is_context_only_feature_support_with_stale_zero(extractor_id):
    factory, _, _, _ = ARTIFACTS[extractor_id]
    record, features = _extract(factory(), extractor_id)
    assert record.authority_state == "OFFICIAL_VERIFIED"
    assert record.permission_state == "CONTEXT_ONLY"
    assert record.evidence_roles == (contracts.EvidenceRole.FEATURE_SUPPORT,)
    assert record.qualification_status == "NOT_QUALIFYING_GOVERNED"
    assert record.evidence_ref.startswith("extracted:")
    assert next(row for row in features if row.feature_id == "evidence_completeness").value == 1.0
    freshness = next(row for row in features if row.feature_id == "freshness")
    assert freshness.value == 0.0
    assert freshness.availability == contracts.AvailabilityState.EXPLICIT_ZERO


@pytest.mark.parametrize("extractor_id", tuple(ARTIFACTS))
def test_deterministic_replay(extractor_id):
    factory, _, _, _ = ARTIFACTS[extractor_id]
    data = factory()
    assert _extract(data, extractor_id) == _extract(data, extractor_id)


def test_treasury_malformed_xml_and_namespace_rejected():
    with pytest.raises(ValueError, match="treasury_xml_malformed"):
        _extract(b"<feed>", batch.TREASURY_EXTRACTOR_ID)
    wrong = _treasury(namespace="urn:not-atom")
    with pytest.raises(ValueError, match="treasury_atom_feed_namespace_mismatch"):
        _extract(wrong, batch.TREASURY_EXTRACTOR_ID)


def test_treasury_selector_and_point_in_time_rejected():
    data = _treasury()
    with pytest.raises(ValueError, match="treasury_record_selector_not_unique"):
        _extract(data, batch.TREASURY_EXTRACTOR_ID, selector={"record_date": "1991-03-15", "maturity": "BC_10YEAR"})
    future = _treasury(updated="2026-08-01T00:00:00Z")
    with pytest.raises(ValueError, match="internal_future_timestamp:known_at_utc"):
        _extract(future, batch.TREASURY_EXTRACTOR_ID)


def test_cftc_row_width_invalid_date_and_compact_date_rejected():
    with pytest.raises(ValueError, match="cftc_row_width_mismatch"):
        _extract(_cftc(short=True), batch.CFTC_EXTRACTOR_ID)
    with pytest.raises(ValueError, match="cftc_report_date_invalid"):
        _extract(_cftc(invalid_date=True), batch.CFTC_EXTRACTOR_ID)
    with pytest.raises(ValueError, match="cftc_compact_date_mismatch"):
        _extract(_cftc(compact="260601"), batch.CFTC_EXTRACTOR_ID)


def test_cftc_selector_mismatch_rejected():
    data = _cftc()
    with pytest.raises(ValueError, match="cftc_record_selector_not_unique"):
        _extract(data, batch.CFTC_EXTRACTOR_ID, selector={"contract_market_code": "999999", "report_date": "2026-06-02"})


def test_cftc_layout_contract_is_complete_versioned_and_hash_bound():
    layout = batch.load_cftc_layout_contract(ROOT)
    assert len(layout["ordered_columns"]) == layout["field_count"] == 129
    assert layout["source_contract_git_blob_sha1"] == "60587be1fd1386ce22110449ed349b2faf34fa2c"
    assert layout["source_contract_byte_sha256"] == "3159b803d79f8cd7d01914309bd97230647d172b2151351c9a73923b43e6c8aa"


def test_h41_zip_duplicate_zip_slip_and_unknown_member_rejected():
    with pytest.warns(UserWarning):
        duplicate = _h41(duplicate=True)
    with pytest.raises(ValueError, match="h41_zip_duplicate_member"):
        _extract(duplicate, batch.H41_EXTRACTOR_ID)
    for member, reason in [("../H41_data.xml", "unsafe_member_path"), ("unexpected.xml", "member_not_allowlisted")]:
        data = _h41(extra=(member, b"x"))
        with pytest.raises(ValueError, match=reason):
            _extract(data, batch.H41_EXTRACTOR_ID)


def test_h41_bounded_sizes_and_entry_count(monkeypatch):
    data = _h41()
    monkeypatch.setattr(batch, "H41_MAX_COMPRESSED_TOTAL", 1)
    with pytest.raises(ValueError, match="h41_zip_compressed_total_exceeded"):
        _extract(data, batch.H41_EXTRACTOR_ID)


def test_h41_malformed_xml_and_xsd_rejected():
    with pytest.raises(ValueError, match="h41_data_xml_malformed"):
        _extract(_h41(data_xml=b"<broken>"), batch.H41_EXTRACTOR_ID)
    bad_xsd = f'<xs:schema xmlns:xs="{batch.XSD_NS}" targetNamespace="urn:wrong"/>'.encode()
    with pytest.raises(ValueError, match="h41_xsd_namespace_mismatch"):
        _extract(_h41(common_xsd=bad_xsd), batch.H41_EXTRACTOR_ID)


def test_h41_quarantine_preserves_structure_without_numeric_truth():
    record, _, _, _ = batch._extract_h41(_h41(), {"dataset_id": "H41"})
    assert record["numeric_observation_values_quarantined"] is True
    assert record["numeric_truth_granted"] is False
    assert "OBS_VALUE" not in record
    assert record["series_count"] == 1 and record["observation_count"] == 1


def test_exact_consumed_byte_mismatch_rejected():
    data = _treasury()
    receipt = _receipt(data, batch.TREASURY_EXTRACTOR_ID)
    with pytest.raises(ValueError, match="extractor_consumed_bytes_receipt_mismatch"):
        batch.extract_production_artifact_evidence(
            data + b" ", receipt=receipt, registry=extraction.load_extractor_registry(ROOT),
            extractor_id=batch.TREASURY_EXTRACTOR_ID, extractor_version="v1",
            selector={"record_date": "1991-03-14", "maturity": "BC_10YEAR"},
            feature_targets=("freshness",), decision_cutoff_utc=CUTOFF, repo_root=ROOT,
        )


@pytest.mark.parametrize("field,value,reason", [
    ("authority_state", "FIRST_PARTY_VERIFIED", "caller_authority_upgrade_forbidden"),
    ("permission_state", "PUBLIC_CLAIM_ALLOWED", "caller_permission_upgrade_forbidden"),
    ("evidence_roles", (contracts.EvidenceRole.NEW_PHASE,), "caller_evidence_role_addition_forbidden"),
])
def test_caller_authority_permission_and_role_upgrades_rejected(field, value, reason):
    with pytest.raises(ValueError, match=reason):
        _extract(_treasury(), batch.TREASURY_EXTRACTOR_ID, **{field: value})


def _git(repo: Path, *args: str, env=None) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, env=env).stdout.strip()


@pytest.fixture()
def three_adapter_repo(tmp_path: Path):
    repo = tmp_path / "upstream"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Adapter Tests")
    _git(repo, "config", "user.email", "adapter@example.invalid")
    payloads = [_treasury(), _cftc(), _h41()]
    for spec, payload in zip(PRODUCTION_ADAPTER_BATCH_TREASURY_CFTC_H41_V1, payloads, strict=True):
        target = repo / spec.artifact_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    _git(repo, "add", ".")
    env = {**os.environ, "GIT_AUTHOR_DATE": "2026-06-07T00:00:00Z", "GIT_COMMITTER_DATE": "2026-06-07T00:00:00Z"}
    _git(repo, "commit", "-m", "three adapter artifacts", env=env)
    return repo, _git(repo, "rev-parse", "HEAD")


def test_three_adapter_frozen_conformance_and_no_publication(three_adapter_repo):
    repo, commit = three_adapter_repo
    results = []
    for spec in PRODUCTION_ADAPTER_BATCH_TREASURY_CFTC_H41_V1:
        results.append(run_adapter_conformance(
            replace(spec, expected_git_blob_sha1=None, expected_byte_sha256=None),
            repo_root=ROOT, upstream_git_repository=repo, upstream_commit=commit,
            branch_authority_ref="refs/heads/main",
        ))
    assert all(row["status"] == "PASS" for row in results)
    assert all(row["publication_authority_granted"] is False for row in results)
    assert all(row["numeric_truth_granted"] is False for row in results)
    assert all("NO_PUBLICATION" in row["publication_disposition"] for row in results)


def test_portable_git_receipt_rejects_blob_and_byte_pin_mismatch(three_adapter_repo):
    repo, commit = three_adapter_repo
    spec = PRODUCTION_ADAPTER_BATCH_TREASURY_CFTC_H41_V1[0]
    kwargs = dict(
        git_repository=repo, registry=adapters.load_trusted_verifier_registry(ROOT), commit=commit,
        artifact_path=spec.artifact_path, artifact_schema_version=spec.artifact_schema_version,
        producer_version=extraction.load_extractor_registry(ROOT).resolve(spec.extractor_id, "v1").shape_contract_id,
        artifact_cutoff_utc="2026-06-07T00:00:00Z", verification_time_utc=CUTOFF,
        branch_authority_ref="refs/heads/main",
    )
    with pytest.raises(ValueError, match="pinned_git_blob_mismatch"):
        batch.build_production_git_artifact_receipt(**kwargs, expected_git_blob_sha1="0" * 40)
    with pytest.raises(ValueError, match="pinned_byte_sha256_mismatch"):
        batch.build_production_git_artifact_receipt(**kwargs, expected_byte_sha256="0" * 64)


def test_frozen_manifest_integrity_and_append_only_registry_deltas():
    assert not validate_foundation_freeze(ROOT)
    verifiers = adapters.load_trusted_verifier_registry(ROOT)
    extractors = extraction.load_extractor_registry(ROOT)
    assert verifiers.registry_version == "trusted-evidence-registry-1.3.0"
    assert extractors.registry_version == "artifact-evidence-extractor-registry-1.3.0"
    assert verifiers.resolve(batch.VERIFIER_ID, "v1") is not None
    assert all(extractors.resolve(extractor_id, "v1") is not None for extractor_id in ARTIFACTS)


def test_exact_real_artifact_inventory_constants_are_complete():
    assert set(batch.PINNED_ARTIFACTS) == set(ARTIFACTS)
    assert {row["git_blob_sha1"] for row in batch.PINNED_ARTIFACTS.values()} == {
        "4c6cb14c58b3e16422eca115fecb1d883a98d79f",
        "d76fafa828839ce774626ee2654b6477904e5260",
        "fd52a7682725d15aa5d997201c52ebae4e291cce",
    }
