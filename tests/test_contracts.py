import pytest
from live_contentops.contracts import PromptContract, PlaneOwner
from live_contentops.contract_validation import validate_contract_dict, ValidationError

def test_contract_instantiation():
    c = PromptContract(prompt_id="test")
    assert c.plane_owner == PlaneOwner.CONTROL_PLANE
    assert c.network_used is False
    assert c.human_approval_required is True

def test_validator_valid():
    sample = {"human_approval_required": True, "network_used": False, "prompt_id": "test"}
    assert validate_contract_dict(sample) is True

def test_validator_secret():
    sample = {"api_key": "123"}
    with pytest.raises(ValidationError):
        validate_contract_dict(sample)

def test_validator_live_flag():
    sample = {"network_used": True}
    with pytest.raises(ValidationError):
        validate_contract_dict(sample)

def test_validator_approval():
    sample = {"human_approval_required": False}
    with pytest.raises(ValidationError):
        validate_contract_dict(sample)
