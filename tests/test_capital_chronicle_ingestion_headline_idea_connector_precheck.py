from pathlib import Path

import pytest

from live_contentops import capital_chronicle_ingestion_headline_idea_connector_precheck as pre


def make_file(root: Path, rel: str, text: str = "context only") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def assert_false_safety(flags):
    for flag in pre.SAFETY_FALSE_FLAGS:
        assert flags[flag] is False


def test_snapshot_existing_temp_repo_read_only(tmp_path):
    make_file(tmp_path, ".git/HEAD", "ref: refs/heads/main")
    make_file(tmp_path, "docs/headline_surface.md", "headline surface")
    snapshot, candidates = pre.build_read_only_snapshot(tmp_path, branch="main", head="abc", inspected_at_epoch=7)

    assert snapshot.path_exists is True
    assert snapshot.is_git_repo is True
    assert snapshot.branch == "main"
    assert snapshot.head == "abc"
    assert snapshot.repo_mutated is False
    assert candidates
    assert_false_safety(snapshot.safety_flags)


def test_snapshot_missing_path_blocked_deterministic(tmp_path):
    missing = tmp_path / "missing"
    a, ca = pre.build_read_only_snapshot(missing, inspected_at_epoch=1)
    b, cb = pre.build_read_only_snapshot(missing, inspected_at_epoch=1)

    assert a.snapshot_id == b.snapshot_id
    assert ca == cb == ()
    assert a.path_exists is False
    assert "ingestion_repo_path_missing" in a.blocked_reasons


def test_env_and_credential_like_paths_skipped_not_read(tmp_path):
    make_file(tmp_path, ".env.local", "SECRET_SHOULD_NOT_BE_READ")
    make_file(tmp_path, "!important credential related to model call/token.txt", "SECRET_SHOULD_NOT_BE_READ")
    make_file(tmp_path, "docs/headline_surface.md", "headline")

    snapshot, candidates = pre.build_read_only_snapshot(tmp_path)

    assert any(".env.local" in p for p in snapshot.forbidden_paths_skipped)
    assert any("credential" in p for p in snapshot.forbidden_paths_skipped)
    assert snapshot.env_or_credential_read is False
    assert candidates
    assert "SECRET_SHOULD_NOT_BE_READ" not in str(snapshot)
    assert "SECRET_SHOULD_NOT_BE_READ" not in str(candidates)


def test_candidate_classifier_detects_required_surface_classes(tmp_path):
    cases = {
        "headline_surface": "docs/headline_surfaces/today_headlines.md",
        "official_source_catalog": "official_sources/official_source_catalog.json",
        "source_family_manifest": "docs/source_family_manifest.md",
        "freshness_manifest": "docs/freshness_manifest.json",
        "coverage_gap_report": "docs/coverage_gap_report.md",
        "dqr_summary": "docs/dqr_summary.md",
        "data_sufficiency_summary": "docs/data_sufficiency_summary.md",
        "forecast_readiness_summary": "docs/forecast_readiness_summary.md",
        "internal_alpha_readiness_report": "docs/internal_alpha_readiness_report.md",
        "candidate_official_source_surface": "docs/candidate_official_source_surface.md",
    }
    for cls, rel in cases.items():
        path = make_file(tmp_path, rel, cls)
        cand = pre.classify_candidate(tmp_path, path)
        assert cand.candidate_class == cls
        assert cand.may_support_public_claim is False
        assert cand.may_clear_dqr is False
        assert cand.may_clear_readiness is False
        assert cand.may_create_current_truth is False
        assert cand.requires_human_review is True


def test_unknown_files_fail_closed(tmp_path):
    path = make_file(tmp_path, "misc/random_notes.md", "nothing useful")
    cand = pre.classify_candidate(tmp_path, path)

    assert cand.candidate_class == "unknown_context_surface"
    assert cand.contentops_use_class == "forbidden_or_unknown"
    assert cand.may_generate_content_idea is False
    assert "unknown_context_surface_fail_closed" in cand.blocked_reasons


def test_headline_context_packet_is_context_only(tmp_path):
    make_file(tmp_path, "docs/headline_surface.md", "headline")
    snapshot, candidates = pre.build_read_only_snapshot(tmp_path)
    packets = pre.build_headline_context_packets(candidates)

    assert snapshot.repo_mutated is False
    assert len(packets) == 1
    packet = packets[0]
    assert packet.content_lane == "grounded_news_context"
    assert packet.public_postable is False
    assert packet.artifact_backed_claims_allowed is False
    assert packet.can_create_content_idea is True
    assert packet.can_create_editorial_brief_candidate is True
    assert packet.can_create_approval is False
    assert packet.can_dispatch is False
    assert_false_safety(packet.safety_flags)


def test_precheck_report_counts_deterministic(tmp_path):
    make_file(tmp_path, "docs/headline_surface.md", "headline")
    make_file(tmp_path, "docs/random.md", "unknown")
    snapshot, candidates = pre.build_read_only_snapshot(tmp_path)
    packets = pre.build_headline_context_packets(candidates)
    report = pre.build_precheck_report(snapshot, candidates, packets)

    assert report.candidate_count == 2
    assert report.usable_context_candidate_count == 1
    assert report.blocked_candidate_count == 1
    assert report.headline_context_packet_count == 1
    assert report.validation_status == "precheck_valid_context_only"
    assert report.current_truth_blocked is True
    assert report.dqr_clear_blocked is True
    assert report.readiness_clear_blocked is True
    assert report.provider_api_blocked is True
    assert report.network_blocked is True
    assert report.ingestion_repo_mutated is False


def test_no_provider_api_network_env_scheduler_scraping_dm_behavior(tmp_path):
    make_file(tmp_path, "docs/headline_surface.md", "headline")
    packet = pre.build_contract_packet(tmp_path)

    assert packet["snapshot"]["env_or_credential_read"] is False
    assert packet["snapshot"]["repo_mutated"] is False
    for flag in pre.SAFETY_FALSE_FLAGS:
        assert packet["snapshot"]["safety_flags"][flag] is False
    assert packet["precheck_report"]["provider_api_blocked"] is True
    assert packet["precheck_report"]["network_blocked"] is True


def test_artifact_writer_only_docs_automation_0174u7(tmp_path):
    repo = tmp_path / "primary"
    ing = tmp_path / "ingestion"
    repo.mkdir(); ing.mkdir()
    make_file(ing, "docs/headline_surface.md", "headline")

    packet = pre.write_artifacts(repo, ing)
    assert (repo / pre.DOC_REL_DIR / pre.PACKET_FILENAME).exists()
    assert (repo / pre.DOC_REL_DIR / pre.RUNBOOK_FILENAME).exists()
    assert (repo / pre.DOC_REL_DIR / pre.RECON_FILENAME).exists()
    assert packet["precheck_report"]["ingestion_repo_mutated"] is False
    with pytest.raises(ValueError, match="0174U7"):
        pre.write_artifacts(repo, ing, output_dir=tmp_path / "other")


def test_no_ingestion_write_staging_commit_simulation(tmp_path):
    make_file(tmp_path, ".git/HEAD", "ref: refs/heads/main")
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    snapshot, candidates = pre.build_read_only_snapshot(tmp_path)
    after = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))

    assert before == after
    assert snapshot.repo_mutated is False
    assert snapshot.env_or_credential_read is False
    assert all(c.source_repo_path == str(tmp_path.resolve()) for c in candidates)
