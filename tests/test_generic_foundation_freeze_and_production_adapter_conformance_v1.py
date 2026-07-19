from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess

import pytest

from live_contentops import content_intelligence_contracts_v2 as contracts
from live_contentops.generic_foundation_freeze_v1 import (
    calculated_manifest_hash,
    load_freeze_manifest,
    validate_append_only_registry,
    validate_foundation_freeze,
)
from live_contentops.production_adapter_conformance_v1 import (
    PRODUCTION_ADAPTERS_V1,
    run_adapter_conformance,
    run_four_adapter_conformance,
)


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_COMMIT = "85fc4ac3ab0d4d61692492558e6abb854a7a0639"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture()
def four_adapter_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "read-only-upstream"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Conformance Tests")
    _git(repo, "config", "user.email", "tests@example.invalid")
    artifacts = {
        PRODUCTION_ADAPTERS_V1[0].artifact_path: {
            "status": "REQUEST_SUCCEEDED", "Results": {"series": [{
                "seriesID": "CUUR0000SA0", "data": [{
                    "year": "2026", "period": "M04", "periodName": "April", "value": "321.5",
                }],
            }]},
        },
        PRODUCTION_ADAPTERS_V1[1].artifact_path: {
            "data": [{
                "cusip": "912810UU0", "announcemt_date": "2026-06-04", "auction_date": "2026-06-12",
                "security_type": "Bond", "security_term": "30-Year", "auction_format": "Single-Price",
                "offering_amt": "22000000000", "reopening": "Yes",
            }], "meta": {"count": 1},
        },
        PRODUCTION_ADAPTERS_V1[2].artifact_path: {
            "refRates": [{
                "effectiveDate": "2026-06-04", "type": "SOFR", "percentRate": 4.33,
                "volumeInBillions": 2145, "revisionIndicator": "",
            }],
        },
    }
    candidate = {
        "candidate_id": "cc-candidate-120438cc800db7f941be", "evidence_hash": "a" * 64,
        "authority": {"story_decision": "ALLOW"},
        "claim_permissions": {"decision": "ALLOW", "reporting_allowed": True},
        "event_time_utc": "2026-07-13T00:00:00Z", "known_at_utc": "2026-07-13T22:27:31Z",
        "source_packet_id": "packet:conformance", "source_packet_logical_hash": "b" * 64,
        "relationship": "initial_event", "eligible": True, "blockers": [],
        "numeric_claims": [], "source_documents": [],
    }
    newsroom = {
        "schema_version": "capital_chronicle.newsroom_candidate_pool.v1",
        "producer_version": "newsroom_candidate_pool_v1.1.0", "pool_id": "pool:conformance",
        "cutoff_time_utc": "2026-07-14T00:00:00Z", "eligible_candidates": [candidate],
        "rejected_candidates": [],
    }
    newsroom["logical_hash"] = contracts.logical_hash({
        key: value for key, value in newsroom.items() if key not in {"logical_hash", "pool_id"}
    })
    artifacts[PRODUCTION_ADAPTERS_V1[3].artifact_path] = newsroom
    for relative, payload in artifacts.items():
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    _git(repo, "add", ".")
    env = {"GIT_AUTHOR_DATE": "2026-07-19T01:00:00Z", "GIT_COMMITTER_DATE": "2026-07-19T01:00:00Z"}
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", "committed adapter artifacts"],
        check=True, capture_output=True, text=True, env={**__import__("os").environ, **env},
    )
    return repo, _git(repo, "rev-parse", "HEAD")


def test_freeze_manifest_integrity_and_interface_classification():
    manifest = load_freeze_manifest()
    assert manifest["manifest_logical_hash"] == calculated_manifest_hash(manifest)
    assert not validate_foundation_freeze(ROOT, manifest)
    classes = manifest["interface_classification"]
    assert set(classes) == {"FROZEN_SEMANTICS", "VERSIONED_APPEND_ONLY_EXTENSION", "ADAPTER_OWNED"}
    assert "exact_set_feature_aggregation" in classes["FROZEN_SEMANTICS"]
    assert "new_extractor_records" in classes["VERSIONED_APPEND_ONLY_EXTENSION"]
    assert "selectors" in classes["ADAPTER_OWNED"]
    assert manifest["exact_source_counts_frozen"] is False
    assert manifest["scenario_fixtures_frozen"] is False


def test_prohibited_silent_semantic_mutation_is_detected():
    manifest = deepcopy(load_freeze_manifest())
    manifest["exact_semantic_files"][0]["sha256"] = "0" * 64
    manifest["manifest_logical_hash"] = calculated_manifest_hash(manifest)
    assert any(reason.startswith("frozen_semantic_file_mutated:") for reason in validate_foundation_freeze(ROOT, manifest))


def test_versioned_append_only_registry_extension_is_allowed_but_in_place_change_is_not():
    manifest = load_freeze_manifest()
    baseline = manifest["registry_baselines"][0]
    registry = json.loads((ROOT / baseline["path"]).read_text(encoding="utf-8"))
    extended = deepcopy(registry)
    new_row = deepcopy(extended["records"][0])
    new_row["verifier_id"] = "contentops.future_adapter_verifier"
    extended["records"].append(new_row)
    extended["registry_version"] = "trusted-evidence-registry-1.1.0"
    extended["registry_logical_hash"] = "1" * 64
    assert not validate_append_only_registry(baseline, extended)
    mutated = deepcopy(extended)
    mutated["records"][0]["enabled"] = False
    assert any(reason.startswith("baseline_registry_record_mutated:") for reason in validate_append_only_registry(baseline, mutated))


def test_all_four_existing_adapters_pass_and_replay_deterministically(four_adapter_repo):
    repo, commit = four_adapter_repo
    first = run_four_adapter_conformance(
        repo_root=ROOT, upstream_git_repository=repo, upstream_commit=commit,
        branch_authority_ref="refs/heads/main",
    )
    second = run_four_adapter_conformance(
        repo_root=ROOT, upstream_git_repository=repo, upstream_commit=commit,
        branch_authority_ref="refs/heads/main",
    )
    assert first == second
    assert first["status"] == "PASS"
    assert [row["adapter_id"] for row in first["results"]] == [row.adapter_id for row in PRODUCTION_ADAPTERS_V1]
    assert all("NO_PUBLICATION" in row["publication_disposition"] for row in first["results"])
    assert all(row["writes_performed"] == 0 for row in first["results"])
    assert str(repo.resolve()) not in json.dumps(first)


def test_authority_permission_and_role_upgrade_are_rejected(four_adapter_repo):
    repo, commit = four_adapter_repo
    result = run_adapter_conformance(
        PRODUCTION_ADAPTERS_V1[0], repo_root=ROOT, upstream_git_repository=repo,
        upstream_commit=commit, branch_authority_ref="refs/heads/main",
        claimed_authority_state="FIRST_PARTY_VERIFIED",
        claimed_permission_state="PUBLIC_CLAIM_ALLOWED",
        claimed_roles=(contracts.EvidenceRole.NEW_PHASE,),
    )
    assert result["status"] == "REJECTED"
    assert set(result["reason_codes"]) == {
        "caller_authority_upgrade_forbidden", "caller_permission_upgrade_forbidden",
        "caller_evidence_role_addition_forbidden",
    }


def test_point_in_time_future_evidence_is_rejected(four_adapter_repo):
    repo, commit = four_adapter_repo
    with pytest.raises(ValueError, match="internal_future_timestamp"):
        run_adapter_conformance(
            PRODUCTION_ADAPTERS_V1[1], repo_root=ROOT, upstream_git_repository=repo,
            upstream_commit=commit, branch_authority_ref="refs/heads/main",
            decision_cutoff_utc="2026-06-03T00:00:00Z",
        )


@pytest.mark.parametrize("field,value,reason", [
    ("expected_evidence_refs", ("caller:arbitrary",), "arbitrary_or_incomplete_evidence_ref_set"),
    ("aggregation_input_refs", ("caller:other",), "feature_aggregation_exact_set_mismatch"),
])
def test_arbitrary_ref_and_aggregation_mismatch_are_rejected(four_adapter_repo, field, value, reason):
    repo, commit = four_adapter_repo
    result = run_adapter_conformance(
        PRODUCTION_ADAPTERS_V1[0], repo_root=ROOT, upstream_git_repository=repo,
        upstream_commit=commit, branch_authority_ref="refs/heads/main", **{field: value},
    )
    assert result["status"] == "REJECTED"
    assert reason in result["reason_codes"]


def test_release_and_prior_foundation_evidence_are_unchanged():
    manifest = load_freeze_manifest()
    assert _git(ROOT, "rev-parse", "v1.0") == manifest["release"]["tag_object"]
    assert _git(ROOT, "rev-parse", "v1.0^{commit}") == manifest["release"]["release_commit"]
    protected = [
        "docs/automation/CONTENTOPS_GENERIC_FOUNDATION_V2_ENFORCEMENT_HARDENING",
        "docs/automation/CONTENTOPS_GENERIC_FOUNDATION_V2_AUTHORITY_AND_EVIDENCE_INTEGRITY_REPAIR",
        "docs/automation/CONTENTOPS_GENERIC_FOUNDATION_V2_GOVERNED_EVIDENCE_PROVENANCE_AND_ROLE_BINDING",
        "docs/automation/CONTENTOPS_EXTRACTED_AUTHORITY_PERMISSION_ROLE_AND_AGGREGATION_BINDING_V1",
    ]
    assert not _git(ROOT, "diff", "--name-only", manifest["accepted_foundation_commit"], "--", *protected)
