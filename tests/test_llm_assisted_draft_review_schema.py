
import pytest
import os
import json
from live_contentops.llm_assisted_draft_review import validate_review_packet_file

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "llm_assisted_draft_reviews")

def _fixt(name):
    return os.path.join(FIX_DIR, name)

def test_schema_valid_packet():
    res = validate_review_packet_file(_fixt("valid_review_only_grounded_news_draft.json"))
    assert res["valid"] is True
