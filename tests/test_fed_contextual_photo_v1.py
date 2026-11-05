"""Board photographs retain their specific public licence and Reserve Bank exclusion."""
from hashlib import sha256
import json

import pytest

from live_contentops.visual_asset_discovery_v1 import _contextual_license_url


@pytest.fixture
def board_licence(tmp_path):
    url = "https://commons.wikimedia.org/wiki/Template:PD-USGov-Federal_Reserve"
    terms = ("This work is in the public domain in the United States because it is a work of the "
        "Board of Governors of the Federal Reserve System. This does not apply to any other entity "
        "within the Federal Reserve System, including the regional Federal Reserve Banks.")
    path = tmp_path / "board-policy.json"
    path.write_text(json.dumps({"status": "PASS", "final_url": url,
        "retrieval_method": "READ_ONLY_BROWSEROS_NEO_PUBLIC_LICENSE", "canonical_content_text": terms,
        "credential_or_session_material_read": False, "public_write_performed": False}))
    receipt = {"creator_publisher": "Federalreserve", "license_text": terms,
        "public_domain_basis": {"policy_url": url, "policy_capture_path": str(path),
            "policy_capture_sha256": sha256(path.read_bytes()).hexdigest()}}
    provider = {"page": {"license_wikitext": "{{PD-USGov-Federal Reserve}}"}}
    metadata = {"License": {"value": "pd"}, "LicenseShortName": {"value": "Public domain"},
        "Copyrighted": {"value": "False"}}
    return receipt, provider, metadata, path


def test_board_public_domain_photo_reaches_existing_media_licence_owner(board_licence):
    receipt, provider, metadata, _ = board_licence
    assert _contextual_license_url(receipt, provider, metadata) == receipt["public_domain_basis"]["policy_url"]


@pytest.mark.parametrize("fault", ["reserve_bank", "missing_exclusion", "copyrighted", "unknown_template", "changed_policy"])
def test_board_photo_does_not_grant_other_entities_or_unverified_bytes(board_licence, fault):
    receipt, provider, metadata, path = board_licence
    if fault == "reserve_bank":
        receipt["creator_publisher"] = "Federal Reserve Bank of New York"
    elif fault == "missing_exclusion":
        receipt["license_text"] = "Board of Governors of the Federal Reserve System public domain"
    elif fault == "copyrighted":
        metadata["Copyrighted"]["value"] = "True"
    elif fault == "unknown_template":
        provider["page"]["license_wikitext"] = "{{UNKNOWN_FREE_IMAGE}}"
    elif fault == "changed_policy":
        path.write_text("changed policy")
    with pytest.raises((ValueError, json.JSONDecodeError)):
        _contextual_license_url(receipt, provider, metadata)
