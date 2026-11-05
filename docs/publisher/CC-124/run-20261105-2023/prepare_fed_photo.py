"""Bind the exact Neo download and Commons Board licence; no network or public action."""
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

from PIL import Image

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from live_contentops.browser_rendered_source_recovery_v1 import _extract_rendered_page, _canonical_rendered_text
from live_contentops.visual_asset_discovery_v1 import validate_contextual_photo

ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-jobs-fx-watch-20261105-f\media_assets")
image_path = ROOT / "Eccles_Building_20110329.jpg"
digest = sha256(image_path.read_bytes()).hexdigest()
page = next(iter(json.loads((ROOT / "provider.json").read_bytes())["query"]["pages"].values()))
page["license_wikitext"] = json.loads((ROOT / "wikitext.json").read_bytes())["parse"]["wikitext"]["*"]
url, text, truncated = _extract_rendered_page((ROOT / "policyRaw-full.md").read_text(encoding="utf-8"))
assert not truncated
plain_policy = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text).replace("**", "")
policy = {"status": "PASS", "final_url": url, "retrieval_method": "READ_ONLY_BROWSEROS_NEO_PUBLIC_LICENSE",
    "canonical_content_text": _canonical_rendered_text(plain_policy), "public_write_performed": False,
    "credential_or_session_material_read": False}
policy_path = ROOT / "fed-board-policy.json"
policy_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
info = page["imageinfo"][0]
asset = {"asset_id": "cc124-fx-fed-archive", "path": str(image_path), "sha256": digest,
    "modality": "documentary_photo", "media_role": "context_photo", "source_page_url": info["descriptionurl"],
    "original_asset_url": info["url"].split("?", 1)[0], "creator_publisher": "Federalreserve",
    "source": "Federal Reserve Board via Wikimedia Commons", "license_name": "Public domain (Federal Reserve Board)",
    "license_url": url, "rights_status": "PUBLIC_DOMAIN", "depicted_date": info["extmetadata"]["DateTimeOriginal"]["value"],
    "source_reuse_basis": "The exact Commons PD-USGov-Federal Reserve template identifies a Board of Governors work; regional Reserve Banks are explicitly excluded.",
    "context_only": True, "corroborates_article_facts": False, "is_archive_context": True, "supports_headline": False,
    "is_logo": False, "is_thumbnail": False, "is_synthetic": False, "ai_generated_image": False,
    "relevance_rationale": "Archive institutional context for the Fed reference rates and yield discussion; no current meeting or market reaction is depicted.",
    "caption": "Archive context: the Federal Reserve's Eccles Building, March 2011. Photo: Federal Reserve Board (Federalreserve), via Wikimedia Commons; public domain.",
    "alt_text": "The front entrance and facade of the Federal Reserve's Eccles Building, photographed in March 2011.",
    "attribution": "Federal Reserve Board (Federalreserve) / Wikimedia Commons / public domain"}
with Image.open(image_path) as image:
    image.verify()
with Image.open(image_path) as image:
    asset.update(width=image.width, height=image.height)
receipt = {k: asset[k] for k in ("source_page_url", "original_asset_url", "creator_publisher", "license_url", "rights_status", "depicted_date")}
receipt.update(original_sha256=digest, license_text=policy["canonical_content_text"],
    provider_metadata={"provider_id": "WIKIMEDIA_COMMONS", "page": page,
        "observation_method": "EXACT_BROWSEROS_NEO_MEDIAWIKI_METADATA_AND_WIKITEXT_RETURNS",
        "source_capture_path": str(ROOT / "commons-source-read.md"),
        "source_capture_sha256": sha256((ROOT / "commons-source-read.md").read_bytes()).hexdigest()},
    public_domain_basis={"policy_url": url, "policy_capture_path": str(policy_path),
        "policy_capture_sha256": sha256(policy_path.read_bytes()).hexdigest()})
rights_path = ROOT / "photo-rights-evidence.json"
rights_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
asset.update(rights_evidence_path=str(rights_path), rights_evidence_sha256=sha256(rights_path.read_bytes()).hexdigest())
validate_contextual_photo(asset, require_pixel_review=False)
(ROOT / "photo-asset-unreviewed.json").write_text(json.dumps(asset, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: asset[k] for k in ("asset_id", "path", "sha256", "width", "height", "rights_status", "depicted_date")}))
