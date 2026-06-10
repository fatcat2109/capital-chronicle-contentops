import os
import json
from live_contentops.seo_newsletter_architecture import validate_seo_newsletter_architecture_packet, validate_newsletter_issue_blueprint_packet

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "seo_newsletter_architecture")

def test_schemas_are_valid():
    res1 = validate_seo_newsletter_architecture_packet(json.load(open(os.path.join(FIX_DIR, "valid_content_architecture_spec.json"))))
    assert res1["valid"] is True

    res2 = validate_newsletter_issue_blueprint_packet(json.load(open(os.path.join(FIX_DIR, "valid_newsletter_issue_blueprint.json"))))
    assert res2["valid"] is True
