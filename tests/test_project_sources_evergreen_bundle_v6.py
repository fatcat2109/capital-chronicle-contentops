import json
from pathlib import Path


def test_evergreen_authority_index():
    index_path = Path("docs/automation/V6_PROJECT_SOURCES_EVERGREEN/CONTENTOPS_V6_CURRENT_AUTHORITY_INDEX.md")
    assert index_path.exists()
    content = index_path.read_text(encoding="utf-8").lower()
    
    # Assert GitHub remote evidence outranks Project Sources
    assert "github remote" in content
    assert "project sources" in content
    assert "never" in content and "final" in content
    
    # Assert Fast Ship profile is execution posture authority
    assert "fast ship operating profile" in content
    assert "execution posture" in content

    # Assert no hardcoded static HEAD claims as final permanent authority
    assert "latest accepted head" not in content
    assert "final head" not in content
    assert "current generation head" not in content


def test_dynamic_pointer_policy():
    policy_path = Path("docs/automation/V6_PROJECT_SOURCES_EVERGREEN/CONTENTOPS_V6_DYNAMIC_POINTER_POLICY.md")
    assert policy_path.exists()
    content = policy_path.read_text(encoding="utf-8").lower()
    
    # Ephemeral pointer policy
    assert "ephemeral" in content
    assert "verify" in content or "verification" in content
    assert "recommended next task at time of bundle generation" in content


def test_lean_upload_bundle_policy():
    lean_path = Path("docs/automation/V6_PROJECT_SOURCES_EVERGREEN/CONTENTOPS_V6_LEAN_UPLOAD_BUNDLE.md")
    assert lean_path.exists()
    content = lean_path.read_text(encoding="utf-8").lower()
    
    # Recommends 10-13 Project Sources
    assert "10" in content and "13" in content
    
    # Says not to delete V6 master plan or 25-task plan
    assert "master plan" in content
    assert "25-task" in content or "task sequence" in content
    assert "do not delete" in content


def test_source_retention_matrix():
    matrix_path = Path("docs/automation/V6_PROJECT_SOURCES_EVERGREEN/CONTENTOPS_V6_SOURCE_RETENTION_MATRIX.json")
    assert matrix_path.exists()
    
    with open(matrix_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    matrix = data.get("matrix", [])
    assert len(matrix) > 0
    
    # Classifies implementation_report/upload_file_list/replacement_guide as not kept
    not_kept_types = ["implementation_report", "upload_file_list", "replacement_guide"]
    for row in matrix:
        t = row.get("source_type")
        if t in not_kept_types:
            assert row.get("keep_policy") in ["do_not_keep_as_project_source", "do_not_keep_after_upload"]
            assert row.get("upload_default") is False
            
        if t == "ingestion_recon_notes":
            assert "optional_only_for_ingestion_connector_tasks" in row.get("keep_policy")
            assert row.get("upload_default") is False


def test_evergreen_bundle_packet():
    packet_path = Path("docs/automation/V6_PROJECT_SOURCES_EVERGREEN/CONTENTOPS_V6_EVERGREEN_BUNDLE_PACKET.json")
    assert packet_path.exists()
    
    with open(packet_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data.get("fast_ship_profile_active") is True
    assert data.get("project_sources_are_not_repo_authority") is True
    assert data.get("dynamic_pointer_policy_active") is True
    assert "accepted_head" in data.get("stale_fields_banned_in_evergreen_docs", [])


def test_hygiene_and_ceremony_absence():
    docs_to_scan = [
        "docs/automation/V6_PROJECT_SOURCES_EVERGREEN/CONTENTOPS_V6_CURRENT_AUTHORITY_INDEX.md",
        "docs/automation/V6_PROJECT_SOURCES_EVERGREEN/CONTENTOPS_V6_PROJECT_SOURCES_MINIMAL_HANDOFF.md",
        "docs/automation/V6_PROJECT_SOURCES_EVERGREEN/CONTENTOPS_V6_DYNAMIC_POINTER_POLICY.md",
        "docs/automation/V6_PROJECT_SOURCES_EVERGREEN/CONTENTOPS_V6_LEAN_UPLOAD_BUNDLE.md",
        "docs/automation/V6_PROJECT_SOURCES_EVERGREEN/CONTENTOPS_V6_SOURCE_RETENTION_MATRIX.json",
        "docs/automation/V6_PROJECT_SOURCES_EVERGREEN/CONTENTOPS_V6_EVERGREEN_BUNDLE_PACKET.json"
    ]
    
    for path in docs_to_scan:
        content = Path(path).read_text(encoding="utf-8").lower()
        
        # Hygiene checks: no credentials
        assert "discord.com/api/webhooks" not in content
        assert "token_value" not in content
        assert "cookie_value" not in content
        assert "secret_key" not in content
        
        # Ceremony absence checks
        assert "no live" not in content
        assert "no env" not in content
        assert "no provider" not in content
        assert "no browser" not in content
        assert "no network" not in content
        assert "local-only" not in content
