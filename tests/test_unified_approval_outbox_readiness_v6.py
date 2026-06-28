from live_contentops import unified_approval_outbox_readiness_v6 as readiness

def test_readiness_reports_contain_expected_blockers(tmp_path):
    contract = {
        "draft_inspector": {
            "blockers": ["source_verification_required", "publication_blocked_until_source_verification"]
        }
    }
    readiness.generate_readiness_reports(tmp_path, contract, {})
    
    import json
    report = json.loads((tmp_path / "unified_approval_readiness_report.json").read_text(encoding="utf-8"))
    assert "source_verification_required" in report["blockers"]
    assert report["unified_payload_status"] == "READY_FOR_REVIEW_ONLY_HASHED_PAYLOADS"
    assert report["allowed_for_publication"] is False
    assert report["public_postable"] is False
