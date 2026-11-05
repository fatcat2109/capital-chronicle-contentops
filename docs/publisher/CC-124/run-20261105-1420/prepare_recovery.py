"""Bind the actual retained Neo captures to the existing source request."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
from PIL import Image

from live_contentops.contentops_source_research_v1 import RetainedSourceResearch

RUN = Path(__file__).resolve().parent
OP = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-d")
root = OP / "source-editions-eia"
index = json.loads((root / "index.json").read_bytes())
research = RetainedSourceResearch(root)
assert not research.gaps, research.gaps
request = json.loads((RUN / "source-recovery-input-first-attempt.json").read_bytes())
request["supporting_headline_ids"] = list(research.records)
for spec in index["records"]:
    if spec.get("capture_class") == "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE":
        capture = json.loads((root / spec["capture_path"]).read_bytes())
        path = root / (spec["headline_id"] + "-visible.md")
        path.write_bytes(capture["rendered_markdown"].encode("utf-8"))
        assert sha256(path.read_bytes()).hexdigest() == spec["source_capture_sha256"]
        for entry in request["additional_source_requests"]:
            if (entry["url"] == research.records[spec["headline_id"]]["document"]["source_url"]
                    or (spec["headline_id"] == "cc124-eia-summary-20261104"
                        and entry["url"] == "https://ir.eia.gov/wpsr/summary.txt")):
                entry.update(capture_path=str(path), capture_sha256=sha256(path.read_bytes()).hexdigest())
now = datetime.now(timezone.utc).isoformat()
photo = OP / "media_assets/Oil_refinery_coastal_Texas.jpg"
media_url = "https://upload.wikimedia.org/wikipedia/commons/d/d9/Oil_refinery_coastal_Texas.jpg?utm_source=commons.wikimedia.org&utm_campaign=index&utm_content=original"
failed = OP / "source-captures/photo-inline-first-attempt.json"
failed.write_text(json.dumps({"operation": "BrowserOS Neo download original link",
    "error": "Download timed out after 60000ms", "observed_browser_url": media_url,
    "observed_state": "INLINE_ORIGINAL_IMAGE_DISPLAYED", "download_event_observed": False,
    "verified_at_utc": now, "public_write_performed": False}, indent=2), encoding="utf-8")
for url, path, reason in [
    ("https://commons.wikimedia.org/wiki/Special:MediaSearch?type=image&search=oil%20refinery%20public%20domain", OP / "source-captures/commons-photo-search.md", "Find an authentic lawful contextual refinery photo."),
    ("https://commons.wikimedia.org/wiki/File:Oil_refinery_coastal_Texas.jpg", OP / "source-captures/commons-refinery-page.md", "Verify creator, archive context, original image and PD-USGov-FWS licence."),
    (media_url, failed, "First original-image link navigated inline without a download event; preserve the observed failure."),
    (media_url, photo, "Same-origin download attribute acquired the exact original after the observed inline-image cause was corrected."),
]:
    request["additional_source_requests"].append({"url": url, "reason": reason,
        "non_chargeable": True, "observed_at_utc": now,
        "observation_clock_basis": "LOCAL_CAPTURE_VERIFIED_AFTER_NEO_ACQUISITION_DOWNLOAD_TIME_UNEXPOSED",
        "capture_path": str(path), "capture_sha256": sha256(path.read_bytes()).hexdigest()})
request["owner_instruction"] += " Include the official report title/date page and actual photo lookup/download attempts in the same budget. Archive photo is media context, never release evidence. All acquisitions are complete before MAX freeze. Focus USOIL under Jim decision 79, without inventing a current plan or market reaction."
(RUN / "source-recovery-input.json").write_text(json.dumps(request, indent=2), encoding="utf-8")
width, height = Image.open(photo).size
metadata = {"asset_id": "cc124-archive-texas-refinery-fws", "path": str(photo),
    "sha256": sha256(photo.read_bytes()).hexdigest(), "width": width, "height": height,
    "modality": "photograph", "media_role": "context_photo",
    "source_page_url": "https://commons.wikimedia.org/wiki/File:Oil_refinery_coastal_Texas.jpg",
    "source_media_url": media_url.split("?")[0], "creator": "U.S. Fish and Wildlife Service",
    "source": "Wikimedia Commons; U.S. Fish and Wildlife Service",
    "license_name": "Public domain (PD-USGov-FWS)",
    "license_url": "https://commons.wikimedia.org/wiki/File:Oil_refinery_coastal_Texas.jpg#Licensing",
    "underlying_source_rights_status": "public_domain",
    "source_page_capture_path": str(OP / "source-captures/commons-refinery-page.md"),
    "source_page_capture_sha256": sha256((OP / "source-captures/commons-refinery-page.md").read_bytes()).hexdigest(),
    "source_photo_capture_date": None, "source_photo_capture_date_state": "NOT_GIVEN_BY_SOURCE",
    "commons_upload_date": "2013-03-01", "is_archive_context": True, "supports_headline": False,
    "caption": "Archive context: a coastal Texas oil refinery. Photo: U.S. Fish and Wildlife Service, via Wikimedia Commons (public domain).",
    "alt_text": "Archive aerial photograph of storage tanks and coastal refinery infrastructure in Texas.",
    "attribution": "U.S. Fish and Wildlife Service / Wikimedia Commons / public domain",
    "pixel_inspection": {"reviewer": "/root", "observed": "Aerial photograph of cylindrical storage tanks, refinery infrastructure and coastal waterways; archive context, no evidence of current inventory conditions."},
    "source_request_count_total_including_prior_evidence": 3 + len(request["additional_source_requests"])}
(OP / "media_assets/photo-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
(RUN / "photo-evidence.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
print(json.dumps({"verified_source_records": len(research.records),
    "charged_total": 3 + len(request["additional_source_requests"]), "source_request_limit": 20,
    "photo": {"path": str(photo), "width": width, "height": height, "sha256": metadata["sha256"]}}))
