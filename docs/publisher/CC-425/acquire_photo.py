"""Acquire the exact Neo-discovered USDA image and validate retained reuse evidence."""
from pathlib import Path
import hashlib
import json
import re
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from live_contentops.visual_asset_discovery_v1 import (
    _default_json_fetcher, validate_contextual_photo,
)
from live_contentops.browser_rendered_source_recovery_v1 import _extract_rendered_page, _canonical_rendered_text
from live_contentops.article_rich_text_v1 import sanitize_source_text
from PIL import Image

ROOT = Path(__file__).resolve().parent / "media"
TITLE = "File:WIC Environments in Michigan (20230621-USDA-FNS-UNK-0052).jpg"


def main():
    ROOT.mkdir(exist_ok=True)
    query = {"action": "query", "format": "json", "formatversion": "2", "titles": TITLE,
             "prop": "imageinfo", "iiprop": "url|size|mime|sha1|extmetadata"}
    provider = _default_json_fetcher("https://commons.wikimedia.org/w/api.php?" + urlencode(query))
    page = provider["query"]["pages"][0]
    raw = _default_json_fetcher("https://commons.wikimedia.org/w/api.php?" + urlencode(
        {"action": "parse", "format": "json", "page": TITLE, "prop": "wikitext"}))
    page["license_wikitext"] = raw["parse"]["wikitext"]["*"]
    info = page["imageinfo"][0]
    meta = info["extmetadata"]
    path = ROOT / "usda-grocery-dearborn-20230622-original.jpg"
    # The discovery helper is deliberately thumbnail-sized. This is the exact
    # original already identified in Neo, bounded separately as delivery media.
    if path.exists():
        image = path.read_bytes()
    else:
        with urlopen(Request(info["url"], headers={"User-Agent": "CapitalChronicle/1.0"}), timeout=20) as response:
            image = response.read(20_000_001)
    if not image or len(image) > 20_000_000:
        raise ValueError("ORIGINAL_PHOTO_SIZE_OUT_OF_BOUNDS")
    if hashlib.sha1(image).hexdigest() != info["sha1"]:
        raise ValueError("ORIGINAL_PHOTO_PROVIDER_BYTES_CHANGED")
    path.write_bytes(image)
    digest = hashlib.sha256(image).hexdigest()
    policy_url, text, truncated = _extract_rendered_page((ROOT / "public-domain-policy-neo.md").read_text(encoding="utf-8"))
    assert not truncated
    plain = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text).replace("**", "")
    policy = {"status": "PASS", "final_url": policy_url,
        "retrieval_method": "READ_ONLY_BROWSEROS_NEO_PUBLIC_LICENSE",
        "canonical_content_text": _canonical_rendered_text(plain), "public_write_performed": False,
        "credential_or_session_material_read": False}
    policy_path = ROOT / "public-domain-policy.json"
    policy_path.write_bytes((json.dumps(policy, indent=2) + "\n").encode("utf-8"))
    asset = {"asset_id": "cc425-usda-grocery-20230622", "path": str(path), "sha256": digest,
        "modality": "documentary_photo", "media_role": "context_photo", "source_page_url": info["descriptionurl"],
        "original_asset_url": info["url"].split("?", 1)[0], "creator_publisher": "USDAgov",
        "license_name": "Public domain (USDA official-duty work)", "license_url": policy_url,
        "rights_status": "PUBLIC_DOMAIN", "depicted_date": sanitize_source_text(meta["DateTimeOriginal"]["value"]).strip(),
        "source_reuse_basis": "The retained Commons file has PD-USGov-USDA and identifies an official-duty USDA work; its exact metadata and federal-work policy are retained.",
        "context_only": True, "corroborates_article_facts": False, "is_archive_context": True,
        "supports_headline": False, "is_logo": False, "is_thumbnail": False,
        "is_synthetic": False, "ai_generated_image": False,
        "relevance_rationale": "Archive grocery-shopping context for consumer prices; it depicts neither a CPI release nor a market reaction.",
        "caption": "Archive context: grocery shopping at the Papaya Supermarket in Dearborn, Michigan, June 2023. Photo: USDAgov / Wikimedia Commons; public domain.",
        "alt_text": "A shopper selects fresh produce inside a supermarket, photographed in Michigan in June 2023.",
        "attribution": "USDAgov / Wikimedia Commons / public domain", "placement_after": "introduction"}
    with Image.open(path) as im:
        asset.update(width=im.width, height=im.height)
    receipt = {k: asset[k] for k in ("source_page_url", "original_asset_url", "creator_publisher",
        "license_url", "rights_status", "depicted_date")}
    receipt.update(original_sha256=digest, license_text=policy["canonical_content_text"],
        provider_metadata={"provider_id": "WIKIMEDIA_COMMONS", "page": page,
            "observation_method": "MEDIAWIKI_IMAGEINFO_AND_WIKITEXT_AFTER_BROWSEROS_NEO_DISCOVERY"},
        public_domain_basis={"policy_url": policy_url, "policy_capture_path": str(policy_path),
            "policy_capture_sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest()})
    rights = ROOT / "photo-rights-evidence.json"
    rights.write_bytes((json.dumps(receipt, indent=2) + "\n").encode("utf-8"))
    asset.update(rights_evidence_path=str(rights), rights_evidence_sha256=hashlib.sha256(rights.read_bytes()).hexdigest())
    validate_contextual_photo(asset, require_pixel_review=False)
    (ROOT / "photo-asset-unreviewed.json").write_bytes((json.dumps(asset, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({k: asset[k] for k in ("asset_id", "path", "sha256", "rights_status", "width", "height")}))


if __name__ == "__main__":
    main()
