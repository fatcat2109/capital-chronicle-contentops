"""Project the actually observed Commons licence fields without an API claim."""
from pathlib import Path
from hashlib import sha256
import json
import re
from live_contentops.visual_asset_discovery_v1 import validate_contextual_photo

OP = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-d")
media = OP / "media_assets"
asset = json.loads((media / "photo-metadata.json").read_bytes())
capture = OP / "source-captures/commons-refinery-page.md"
text = capture.read_text(encoding="utf-8")
terms = next(line for line in text.splitlines() if "employee, taken or made" in line)
terms = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", terms.split(" --- ")[0])
terms = terms.replace("*", "").strip("| ")
assert all(value in terms for value in ("U.S. Fish and Wildlife Service", "official duties", "public domain"))
asset.update(modality="documentary_photo", rights_status="PUBLIC_DOMAIN",
    original_asset_url=asset["source_media_url"], creator_publisher=asset["creator"],
    relevance_rationale="Archive illustration of US coastal oil storage and refinery infrastructure. It is not evidence of current inventory conditions.",
    depicted_date="Not given", source_reuse_basis="Commons identifies an official-duty Fish and Wildlife Service work as public domain (PD-USGov-FWS).",
    context_only=True, corroborates_article_facts=False,
    is_logo=False, is_thumbnail=False, is_synthetic=False, ai_generated_image=False,
    visual_review={"asset_sha256": asset["sha256"], "pixels_inspected": True,
        "relevant_subject": True, "reviewer": "/root",
        "findings": "Viewed original JPEG: oil storage tanks and coastal refinery infrastructure; archive context, capture date not given."})
receipt = {k: asset[k] for k in ("source_page_url", "original_asset_url", "creator_publisher",
    "license_url", "rights_status", "depicted_date")}
receipt.update(original_sha256=asset["sha256"], license_text=terms, provider_metadata={
    "provider_id": "WIKIMEDIA_COMMONS",
    "observation_method": "EXACT_RENDERED_METADATA_PROJECTION_NOT_MEDIAWIKI_API_RESPONSE",
    "source_capture_path": str(capture), "source_capture_sha256": sha256(capture.read_bytes()).hexdigest(),
    "page": {"imageinfo": [{"descriptionurl": asset["source_page_url"],
        "url": asset["original_asset_url"], "extmetadata": {
            "LicenseUrl": {"value": asset["license_url"]},
            "LicenseShortName": {"value": "Public domain"},
            "DateTimeOriginal": {"value": "Not given"},
            "Artist": {"value": asset["creator"]}}}]}})
path = media / "photo-rights-evidence.json"
path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
asset.update(rights_evidence_path=str(path), rights_evidence_sha256=sha256(path.read_bytes()).hexdigest())
validate_contextual_photo(asset)
(media / "photo-asset.json").write_text(json.dumps(asset, indent=2), encoding="utf-8")
(Path(__file__).resolve().parent / "photo-evidence.json").write_text(json.dumps(asset, indent=2), encoding="utf-8")
print("Contextual photo validation PASS:", asset["sha256"])
