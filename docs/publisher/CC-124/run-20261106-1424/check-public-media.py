"""Hash the two public originals already observed in the Neo canonical readback."""
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = []
for name, url, expected in [
    ("archive-photo.jpeg", "https://substack-post-media.s3.amazonaws.com/public/images/54db29b3-0536-4108-9f95-d21e90a004a0_3000x2041.jpeg", "9daa459a37b2edae6159f9f4d98b7a2b91ef3d5e0cbd25b9fe85fb556f174a62"),
    ("review-card.png", "https://substack-post-media.s3.amazonaws.com/public/images/46fdd49e-43a6-472d-ac87-9a67fc365d7f_1080x1350.png", "cce5a0dde9bee65fdc247c96ae95bedac121d176185163e5b2f16d58a00ceda4"),
]:
    with urllib.request.urlopen(url, timeout=15) as response:
        data = response.read()
    target = HERE / "media" / "public-originals" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    observed = hashlib.sha256(data).hexdigest()
    rows.append({"url": url, "path": str(target), "bytes": len(data),
                 "sha256": observed, "expected_sha256": expected, "matches": observed == expected})
    assert observed == expected, name
result = {"observed_at_utc": datetime.now(timezone.utc).isoformat(),
          "method": "Binary hash of the public S3 originals referenced by the images in Neo page 687. Neo anchor download timed out; no browser session or secret material accessed.",
          "assets": rows}
(HERE / "public-media-hash-check.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
