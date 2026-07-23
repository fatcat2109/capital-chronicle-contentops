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
from live_contentops import production_adapter_contract_coverage_v1 as coverage
from live_contentops import production_evidence_adapters_wave3_v1 as wave3
from live_contentops import schema_aware_evidence_extraction_v1 as extraction
from live_contentops.generic_foundation_freeze_v1 import validate_foundation_freeze
from live_contentops.production_adapter_conformance_v1 import PRODUCTION_ADAPTER_WAVE3_V1, run_adapter_conformance


ROOT = Path(__file__).resolve().parents[1]
CUTOFF = "2026-07-22T00:00:00Z"


def _tic(*, updated: str = "2026-06-15", duplicate_canonical: bool = False) -> bytes:
    canonical = "https://home.treasury.gov/data/treasury-international-capital-tic-system"
    extra = f'<link rel="canonical" href="{canonical}" />' if duplicate_canonical else ""
    return f'''<!DOCTYPE html><html><head><link rel="canonical" href="{canonical}" />{extra}<meta property="og:site_name" content="U.S. Department of the Treasury"/><meta property="og:url" content="{canonical}"/><meta property="og:updated_time" content="{updated}"/><title>Treasury International Capital (TIC) System | U.S. Department of the Treasury</title></head><body></body></html>'''.encode()


def _usgs(*, magnitude: float = 0.0, event_time: int = 1783633608405, updated: int = 1783633705342, generated: int = 1783633997000) -> bytes:
    return json.dumps({
        "type": "FeatureCollection",
        "metadata": {"generated": generated, "url": "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=1", "title": "USGS Earthquakes", "status": 200, "api": "2.7.0", "limit": 1, "offset": 1},
        "features": [{"type": "Feature", "properties": {"mag": magnitude, "place": "79 km SE of Kokhanok, Alaska", "time": event_time, "updated": updated, "status": "automatic", "tsunami": 0}, "geometry": {"type": "Point", "coordinates": [-153.978, 58.854, 99.1]}, "id": "aka2026nmtsmu"}],
    }, separators=(",", ":")).encode()


def _fhfa(*, modified: str = "2026-06-30", duplicate_canonical: bool = False) -> bytes:
    extra = '<link rel="canonical" href="https://www.fhfa.gov/data/hpi" />' if duplicate_canonical else ""
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"/><link rel="canonical" href="https://www.fhfa.gov/data/hpi" />{extra}<meta name="author" content="FHFA"/><meta property="article:modified_time" content="{modified}"/><title>FHFA House Price Index® | FHFA</title></head><body></body></html>'''.encode()


ARTIFACTS = {
    wave3.TIC_EXTRACTOR_ID: (_tic, wave3.TIC_PATH, wave3.TIC_SCHEMA, {"canonical_url": "https://home.treasury.gov/data/treasury-international-capital-tic-system"}),
    wave3.USGS_EXTRACTOR_ID: (_usgs, wave3.USGS_PATH, wave3.USGS_SCHEMA, {"event_id": "aka2026nmtsmu"}),
    wave3.FHFA_EXTRACTOR_ID: (_fhfa, wave3.FHFA_PATH, wave3.FHFA_SCHEMA, {"canonical_url": "https://www.fhfa.gov/data/hpi"}),
}


def _receipt(data: bytes, extractor_id: str):
    verifier_registry = adapters.load_trusted_verifier_registry(ROOT)
    extractor = extraction.load_extractor_registry(ROOT).resolve(extractor_id, wave3.EXTRACTOR_VERSION)
    _, path, schema, _ = ARTIFACTS[extractor_id]
    blob = sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
    return contracts.build_verified_producer_artifact_receipt_v1(
        data, registry=verifier_registry, verifier_id=wave3.VERIFIER_ID, verifier_version=wave3.VERIFIER_VERSION,
        repository=wave3.UPSTREAM_REPOSITORY, branch=wave3.UPSTREAM_BRANCH, producer_commit="1" * 40,
        artifact_path=path, expected_git_blob_sha1=blob, artifact_schema_version=schema,
        producer_version=extractor.shape_contract_id, artifact_cutoff_utc="2026-07-10T00:00:00Z",
        evidence_refs=(), source_authority_class="official_public_data", resolved_repository=wave3.UPSTREAM_REPOSITORY,
        resolved_branch=wave3.UPSTREAM_BRANCH, resolved_commit="1" * 40, resolved_artifact_path=path,
        branch_head_observed="2" * 40, producer_commit_reachable_from_branch=True, verification_time_utc=CUTOFF,
    )


def _extract(data: bytes, extractor_id: str, **changes):
    _, _, _, selector = ARTIFACTS[extractor_id]
    kwargs = {
        "receipt": _receipt(data, extractor_id), "registry": extraction.load_extractor_registry(ROOT),
        "extractor_id": extractor_id, "extractor_version": wave3.EXTRACTOR_VERSION,
        "selector": selector, "feature_targets": ("evidence_completeness", "freshness"),
        "decision_cutoff_utc": CUTOFF,
    }
    kwargs.update(changes)
    return wave3.extract_wave3_artifact_evidence(data, **kwargs)


def test_registry_contract_coverage_is_complete_and_deterministic():
    registry = extraction.load_extractor_registry(ROOT)
    first = coverage.validate_registry_contract_coverage(registry, repo_root=ROOT)
    assert first == coverage.validate_registry_contract_coverage(registry, repo_root=ROOT)
    assert first["status"] == "PASS" and first["record_count"] == len(registry.records)
    runtime = [row for row in first["rows"] if row["classification"] == "RUNTIME_IMPLEMENTED_IMMUTABLY_BOUND"]
    assert len(runtime) == 16
    assert all(row["record_hash_verified"] and row["accepted_evidence_verified"] for row in runtime)
    assert all(row["shape_contract_id"] and row["required_fields"] and row["timestamp_extraction_rules"] for row in runtime)
    assert all(row["authority_derivation_rule"] and row["permission_derivation_rule"] and row["role_derivation_rule"] for row in runtime)
    assert all(row["supported_evidence_roles"] and row["supported_feature_ids"] and row["implementation_contract_id"] and row["runtime_callable"] for row in runtime)
    assert all(row["classification"].startswith("RUNTIME_IMPLEMENTED") for row in first["rows"] if row["extractor_id"] != "contentops.disabled_legacy_extractor")
    assert next(row for row in first["rows"] if row["extractor_id"] == "contentops.disabled_legacy_extractor")["classification"] == "EXPLICIT_DOCUMENTARY_NON_RUNTIME"


def test_registry_contract_coverage_rejects_declared_runtime_drift():
    registry = extraction.load_extractor_registry(ROOT)
    records = list(registry.records)
    index = next(i for i, row in enumerate(records) if (row.extractor_id, row.extractor_version) == (wave3.USGS_EXTRACTOR_ID, "v1"))
    records[index] = replace(records[index], required_fields=records[index].required_fields[:-1])
    report = coverage.validate_registry_contract_coverage(replace(registry, records=tuple(records)))
    assert report["status"] == "FAIL"
    assert report["blockers"] == [f"registry_immutable_record_hash_mismatch:{wave3.USGS_EXTRACTOR_ID}:v1"]


def test_registry_contract_coverage_rejects_missing_field_wrong_shape_and_timestamp_rule():
    registry = extraction.load_extractor_registry(ROOT)
    index = next(index for index, row in enumerate(registry.records) if row.extractor_id == wave3.USGS_EXTRACTOR_ID)
    original = registry.records[index]
    mutations = (
        replace(original, required_fields=original.required_fields[:-1]),
        replace(original, shape_contract_id="wrong.shape.contract"),
        replace(original, timestamp_extraction_rules={**original.timestamp_extraction_rules, "known_at_utc": "WRONG_RULE"}),
    )
    for mutated in mutations:
        records = (*registry.records[:index], mutated, *registry.records[index + 1:])
        result = coverage.validate_registry_contract_coverage(replace(registry, records=records))
        assert result["status"] == "FAIL"
        assert result["blockers"] == [f"registry_immutable_record_hash_mismatch:{wave3.USGS_EXTRACTOR_ID}:v1"]


@pytest.mark.parametrize("extractor_id", tuple(ARTIFACTS))
def test_valid_wave3_extraction_is_deterministic_bounded_and_no_publication(extractor_id):
    data = ARTIFACTS[extractor_id][0]()
    first = _extract(data, extractor_id)
    assert first == _extract(data, extractor_id)
    record, features = first
    assert record.authority_state == "OFFICIAL_VERIFIED"
    assert record.permission_state == "CONTEXT_ONLY"
    assert record.evidence_roles == (contracts.EvidenceRole.FEATURE_SUPPORT,)
    assert record.qualification_status == "NOT_QUALIFYING_GOVERNED"
    assert record.known_at_utc is not None
    assert next(row for row in features if row.feature_id == "evidence_completeness").value == 1.0
    freshness = next(row for row in features if row.feature_id == "freshness")
    assert freshness.value == 0.0 and freshness.availability == contracts.AvailabilityState.EXPLICIT_ZERO


def test_treasury_tic_exact_official_head_shape_revision_and_selector_fail_closed():
    record, _ = _extract(_tic(), wave3.TIC_EXTRACTOR_ID)
    assert record.observed_at_utc is None and record.published_at_utc is None
    assert record.revision_at_utc == "2026-06-15T00:00:00Z"
    with pytest.raises(ValueError, match="official_shape_mismatch"):
        _extract(_tic(duplicate_canonical=True), wave3.TIC_EXTRACTOR_ID)
    with pytest.raises(ValueError, match="updated_date_invalid"):
        _extract(_tic(updated="not-a-date"), wave3.TIC_EXTRACTOR_ID)
    with pytest.raises(ValueError, match="selector_mismatch"):
        _extract(_tic(), wave3.TIC_EXTRACTOR_ID, selector={"canonical_url": "https://example.invalid"})


def test_usgs_shape_numeric_timestamp_selector_and_explicit_zero_semantics():
    zero, _ = _extract(_usgs(magnitude=0.0), wave3.USGS_EXTRACTOR_ID)
    nonzero, _ = _extract(_usgs(magnitude=1.7), wave3.USGS_EXTRACTOR_ID)
    assert zero.extracted_record_hash != nonzero.extracted_record_hash
    with pytest.raises(ValueError, match="geojson_malformed"):
        _extract(b"{", wave3.USGS_EXTRACTOR_ID)
    bad = json.loads(_usgs())
    bad["features"][0]["geometry"]["coordinates"] = [1, 2]
    with pytest.raises(ValueError, match="coordinates_invalid"):
        _extract(json.dumps(bad).encode(), wave3.USGS_EXTRACTOR_ID)
    with pytest.raises(ValueError, match="timestamp_order_invalid"):
        _extract(_usgs(updated=1783633000000), wave3.USGS_EXTRACTOR_ID)
    with pytest.raises(ValueError, match="selector_not_unique"):
        _extract(_usgs(), wave3.USGS_EXTRACTOR_ID, selector={"event_id": "missing"})
    with pytest.raises(ValueError, match="internal_future_timestamp"):
        _extract(_usgs(), wave3.USGS_EXTRACTOR_ID, decision_cutoff_utc="2026-07-01T00:00:00Z")


def test_fhfa_exact_official_head_shape_revision_and_selector_fail_closed():
    record, _ = _extract(_fhfa(), wave3.FHFA_EXTRACTOR_ID)
    assert record.observed_at_utc is None and record.published_at_utc is None
    assert record.revision_at_utc == "2026-06-30T00:00:00Z"
    with pytest.raises(ValueError, match="official_shape_mismatch"):
        _extract(_fhfa(duplicate_canonical=True), wave3.FHFA_EXTRACTOR_ID)
    with pytest.raises(ValueError, match="modified_date_invalid"):
        _extract(_fhfa(modified="not-a-date"), wave3.FHFA_EXTRACTOR_ID)
    with pytest.raises(ValueError, match="selector_mismatch"):
        _extract(_fhfa(), wave3.FHFA_EXTRACTOR_ID, selector={"canonical_url": "https://example.invalid"})


def test_exact_byte_mismatch_and_caller_upgrades_are_rejected():
    data = _usgs()
    with pytest.raises(ValueError, match="consumed_bytes_receipt_mismatch"):
        wave3.extract_wave3_artifact_evidence(
            data + b" ", receipt=_receipt(data, wave3.USGS_EXTRACTOR_ID),
            registry=extraction.load_extractor_registry(ROOT), extractor_id=wave3.USGS_EXTRACTOR_ID,
            extractor_version="v1", selector={"event_id": "aka2026nmtsmu"},
            feature_targets=("freshness",), decision_cutoff_utc=CUTOFF,
        )
    for field, value, reason in [
        ("authority_state", "FIRST_PARTY_VERIFIED", "caller_authority_upgrade_forbidden"),
        ("permission_state", "PUBLIC_CLAIM_ALLOWED", "caller_permission_upgrade_forbidden"),
        ("evidence_roles", (contracts.EvidenceRole.NEW_PHASE,), "caller_evidence_role_addition_forbidden"),
    ]:
        with pytest.raises(ValueError, match=reason):
            _extract(data, wave3.USGS_EXTRACTOR_ID, **{field: value})


def _git(repo: Path, *args: str, env=None) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, env=env).stdout.strip()


def _single_artifact_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "single-upstream"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Wave 3 Tests")
    _git(repo, "config", "user.email", "wave3@example.invalid")
    target = repo / wave3.USGS_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(_usgs())
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "USGS artifact")
    return repo, _git(repo, "rev-parse", "HEAD")


def test_wave3_git_receipt_rejects_exact_blob_and_byte_mismatch(tmp_path: Path):
    repo, commit = _single_artifact_repo(tmp_path)
    registry = adapters.load_trusted_verifier_registry(ROOT)
    extractor = extraction.load_extractor_registry(ROOT).resolve(wave3.USGS_EXTRACTOR_ID, "v1")
    kwargs = {
        "git_repository": repo, "registry": registry, "commit": commit,
        "artifact_path": wave3.USGS_PATH, "artifact_schema_version": wave3.USGS_SCHEMA,
        "producer_version": extractor.shape_contract_id,
        "artifact_cutoff_utc": "2026-07-10T00:00:00Z",
        "verification_time_utc": CUTOFF, "branch_authority_ref": "refs/heads/main",
    }
    with pytest.raises(ValueError, match="pinned_git_blob_mismatch"):
        wave3.build_wave3_git_artifact_receipt(**kwargs, expected_git_blob_sha1="0" * 40)
    with pytest.raises(ValueError, match="pinned_byte_sha256_mismatch"):
        wave3.build_wave3_git_artifact_receipt(**kwargs, expected_byte_sha256="0" * 64)


def test_wave3_git_receipt_rejects_unrelated_history(tmp_path: Path):
    repo, _ = _single_artifact_repo(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    _git(other, "init", "-b", "other")
    _git(other, "config", "user.name", "Other")
    _git(other, "config", "user.email", "other@example.invalid")
    (other / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")
    _git(other, "add", ".")
    _git(other, "commit", "-m", "unrelated")
    foreign = _git(other, "rev-parse", "HEAD")
    _git(repo, "fetch", str(other), foreign)
    registry = adapters.load_trusted_verifier_registry(ROOT)
    extractor = extraction.load_extractor_registry(ROOT).resolve(wave3.USGS_EXTRACTOR_ID, "v1")
    with pytest.raises(ValueError, match="not_reachable_from_observed_branch"):
        wave3.build_wave3_git_artifact_receipt(
            git_repository=repo, registry=registry, commit=foreign,
            artifact_path=wave3.USGS_PATH, artifact_schema_version=wave3.USGS_SCHEMA,
            producer_version=extractor.shape_contract_id,
            artifact_cutoff_utc="2026-07-10T00:00:00Z", verification_time_utc=CUTOFF,
            branch_authority_ref="refs/heads/main",
        )


def test_three_adapter_conformance_and_branch_advancement_are_deterministic(tmp_path: Path):
    repo = tmp_path / "upstream"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Wave 3 Tests")
    _git(repo, "config", "user.email", "wave3@example.invalid")
    for spec, (factory, _, _, _) in zip(PRODUCTION_ADAPTER_WAVE3_V1, ARTIFACTS.values(), strict=True):
        target = repo / spec.artifact_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(factory())
    env = {**os.environ, "GIT_AUTHOR_DATE": "2026-07-10T00:00:00Z", "GIT_COMMITTER_DATE": "2026-07-10T00:00:00Z"}
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "wave3 fixtures", env=env)
    pinned = _git(repo, "rev-parse", "HEAD")
    (repo / "advanced.txt").write_text("advanced\n", encoding="utf-8")
    _git(repo, "add", "advanced.txt")
    _git(repo, "commit", "-m", "advance branch", env=env)
    observed = _git(repo, "rev-parse", "HEAD")
    specs = [replace(spec, expected_git_blob_sha1=None, expected_byte_sha256=None) for spec in PRODUCTION_ADAPTER_WAVE3_V1]
    first = [run_adapter_conformance(spec, repo_root=ROOT, upstream_git_repository=repo, upstream_commit=pinned, branch_authority_ref="refs/heads/main") for spec in specs]
    second = [run_adapter_conformance(spec, repo_root=ROOT, upstream_git_repository=repo, upstream_commit=pinned, branch_authority_ref="refs/heads/main") for spec in specs]
    assert first == second and all(row["status"] == "PASS" for row in first)
    assert all(row["upstream"]["producer_commit"] == pinned and row["upstream"]["branch_head_observed"] == observed for row in first)
    assert all("NO_PUBLICATION" in row["publication_disposition"] and row["writes_performed"] == 0 for row in first)


def test_append_only_registries_pins_and_frozen_manifest_integrity():
    assert not validate_foundation_freeze(ROOT)
    assert adapters.load_trusted_verifier_registry(ROOT).registry_version == "trusted-evidence-registry-1.3.0"
    registry = extraction.load_extractor_registry(ROOT)
    assert registry.registry_version == "artifact-evidence-extractor-registry-1.3.0"
    for path in (
        "live_contentops/trusted_evidence_verifier_registry_v1.json",
        "live_contentops/artifact_evidence_extractor_registry_v1.json",
    ):
        baseline = json.loads(_git(ROOT, "show", f"{coverage.STARTING_AUTHORITY_SHA}:{path}"))
        current = json.loads((ROOT / path).read_text(encoding="utf-8"))
        assert current["records"][:len(baseline["records"])] == baseline["records"]
    assert set(wave3.PINNED_ARTIFACTS) == set(ARTIFACTS)
    assert all(row["producer_commit"] != wave3.OBSERVED_UPSTREAM_HEAD and len(row["git_blob_sha1"]) == 40 and len(row["byte_sha256"]) == 64 for row in wave3.PINNED_ARTIFACTS.values())
