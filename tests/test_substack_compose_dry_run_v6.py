import json
from live_contentops import substack_compose_dry_run_v6 as dry_run

def test_dry_run_orchestrator(tmp_path):
    contract = {
        "canonical_article": {
            "title": "Yield Analysis",
            "subtitle": "Analysis Subtitle",
            "body_markdown": "Body text overview.",
            "citations": ["UNVERIFIED_SAMPLE_SOURCE_REF"]
        }
    }
    contract_file = tmp_path / "contract.json"
    contract_file.write_text(json.dumps(contract), encoding="utf-8")
    
    out_dir = tmp_path / "out"
    dry_run.main([
        "--output-dir", str(out_dir),
        "--contract-packet", str(contract_file)
    ])
    
    packet = json.loads((out_dir / "substack_compose_dry_run_packet.json").read_text(encoding="utf-8"))
    assert packet["substack_compose_dry_run_status"] == "READY_FOR_LOCAL_MOCK_REVIEW_ONLY"
    assert packet["real_substack_opened"] is False
    assert packet["dispatch_allowed_now"] is False
    assert "source_verification_required" in packet["blockers"]
