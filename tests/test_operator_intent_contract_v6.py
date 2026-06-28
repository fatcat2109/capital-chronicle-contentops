from live_contentops import operator_intent_contract_v6 as intent_contract

def test_operator_intent_is_not_approval_by_default():
    req = {
        "intent_class": "create_canonical_article",
        "intent_text": "Jim wants to draft a new post about Treasury bills"
    }
    res = intent_contract.validate_operator_intent(req)
    assert res["is_valid"] is True
    assert "operator_signature_missing" not in res["blockers"]

def test_approval_intent_requires_exact_payload_hash():
    req = {
        "intent_class": "approve_payload",
        "intent_text": "Jim signs this draft"
    }
    res = intent_contract.validate_operator_intent(req)
    assert res["is_valid"] is False
    assert "operator_signature_missing" in res["blockers"]
    
    # Passing valid hash should validate
    req["payload_hash"] = "a" * 64
    res2 = intent_contract.validate_operator_intent(req)
    assert "operator_signature_missing" not in res2["blockers"]

def test_ambiguous_live_write_language_is_blocked():
    req = {
        "intent_class": "create_canonical_article",
        "intent_text": "Jim wants to publish to live channel now"
    }
    res = intent_contract.validate_operator_intent(req)
    assert res["is_valid"] is False
    assert "ambiguous_live_write_language" in res["blockers"]

def test_unsafe_financial_signals_are_rewritten_safely():
    req = {
        "intent_class": "create_canonical_article",
        "intent_text": "Jim wants to know if this yield curve inversion is a buy signal",
        "allow_rewrite": True
    }
    res = intent_contract.validate_operator_intent(req)
    assert res["is_valid"] is True
    assert "historical educational context of the asset" in res["validated_intent_text"]
    assert "buy signal" not in res["validated_intent_text"]

def test_unsafe_financial_signals_block_if_no_rewrite():
    req = {
        "intent_class": "create_canonical_article",
        "intent_text": "Jim wants to know if this yield curve inversion is a buy signal",
        "allow_rewrite": False
    }
    res = intent_contract.validate_operator_intent(req)
    assert res["is_valid"] is False
    assert "unsafe_financial_signal_requested" in res["blockers"]
