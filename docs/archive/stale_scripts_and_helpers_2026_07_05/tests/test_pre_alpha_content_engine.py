"""Tests for the local-only pre-alpha content engine (Task 0095).

Deterministic, offline. No network/provider/LLM/platform/credential access.
"""

import os
import json

import pytest

from live_contentops import pre_alpha_content_engine as engine

FIXTURE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "pre_alpha_content_engine"
)


def _fx(name):
    return os.path.join(FIXTURE_DIR, name)


def _load(name):
    with open(_fx(name), "r", encoding="utf-8") as f:
        return json.load(f)


# --- schema presence ---------------------------------------------------------

def test_schemas_exist_and_load():
    assert isinstance(engine.load_seed_schema(), dict)
    assert isinstance(engine.load_draft_schema(), dict)
    assert isinstance(engine.load_packet_schema(), dict)


# --- valid seeds -------------------------------------------------------------

@pytest.mark.parametrize("name", [
    "valid_build_in_public_seed.json",
    "valid_macro_education_seed.json",
    "valid_data_sufficiency_seed.json",
])
def test_valid_seeds_pass(name):
    result = engine.validate_seed_file(_fx(name))
    assert result["valid"] is True, result["errors"]
    assert result["errors"] == []


# --- invalid seeds -----------------------------------------------------------

def test_invalid_fake_alpha_market_note_blocks():
    result = engine.validate_seed_file(_fx("invalid_fake_alpha_market_note.json"))
    assert result["valid"] is False
    assert "seed_implies_alpha_output" in result["errors"]
    assert "market_note_must_be_general_process" in result["errors"]


def test_invalid_financial_advice_language_blocks():
    result = engine.validate_seed_file(_fx("invalid_financial_advice_language.json"))
    assert result["valid"] is False
    assert "seed_forbidden_language" in result["errors"]


def test_invalid_unverified_numeric_claim_blocks():
    result = engine.validate_seed_file(_fx("invalid_unverified_numeric_claim.json"))
    assert result["valid"] is False
    assert "seed_unverified_numeric_market_claim" in result["errors"]
