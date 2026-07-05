import pytest
from live_contentops import operator_rollback_drill
from live_contentops import policy_rules

def test_operator_rollback_drill_blocks_live_capabilities():
    res = operator_rollback_drill.run_operator_rollback_drill(operator_id="test_operator_1")
    
    # 1. Native flag verification
    assert res["network_used"] is False
    assert res["provider_call_used"] is False
    assert res["platform_api_used"] is False
    assert res["telegram_api_used"] is False
    assert res["publishing_enabled"] is False
    assert res["safe_for_publish"] is False
    assert res["live_credentials_allowed_now"] is False
    
    # 2. Operator logic verification
    assert res["operator_action"] == "reject"
    assert res["operator_actor_id"] == "test_operator_1"
    assert res["final_queue_status"] == "REJECTED"
    assert res["drill_status"] == "SUCCESSFUL_ROLLBACK"

def test_operator_rollback_drill_audit_trail_secrets():
    res = operator_rollback_drill.run_operator_rollback_drill()
    
    audit_trail = res.get("audit_trail", [])
    assert len(audit_trail) > 0, "Audit trail should not be empty"
    
    operator_event_found = False
    for event in audit_trail:
        # Native verification on audit elements
        assert event["safe_to_log"] is True
        assert event["secrets_redacted"] is True
        assert event["network_used"] is False
        assert event["publishing_enabled"] is False
        
        if event["event_type"] == "ITEM_REJECTED":
            operator_event_found = True
            assert "Action reject" in event["reason"]
            assert "DRILL:" in event["reason"]
            assert event["result"] == "REJECTED_AND_QUARANTINED"
            
    assert operator_event_found, "The operator rejection event must be present in the audit trail"
