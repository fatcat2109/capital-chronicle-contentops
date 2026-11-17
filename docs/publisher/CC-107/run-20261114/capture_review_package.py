"""Read the existing installed editorial package; create no public dispatch."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

LIVE = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(LIVE))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_manual_candidate_v1 import native_artifact_key
from live_contentops.native_desktop_editorial_v1 import native_review_revision, validate_release_media
from live_contentops.native_publication_latency_v1 import automated_media_check
from live_contentops.reader_article_contract_v1 import check_article, validate_publication_clock
from live_contentops.v1_simple_gemini_newsroom_v1 import _reader_safe_native_article

HERE = Path(__file__).resolve().parent
ROOT = Path(r"C:\Users\bullw\AppData\Local\CapitalChronicle\ContentOps\editorial-previews\cc107-nfp-dated-review-20261114-v1")
binding = json.loads((ROOT / "binding.json").read_bytes())
store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
row = store.get_outbox_message(native_artifact_key(store, binding["run_id"], "cc-editorial-final-"))
result = json.loads(row["payload"])
assert result["qualified_article_count"] == 1
article = result["article"]
reader = _reader_safe_native_article(article, article_mode=article["resolved_article_mode"],
    epistemic_state=article.get("epistemic_state"), legacy_presentation=False)
checks = check_article(article, result["evidence"])
assert not checks, checks
media = validate_release_media(result, require_pixel_review=False)
image_check = automated_media_check(result)
now = datetime.now(timezone.utc)
try:
    validate_publication_clock(article, now=now, destination="substack")
    publication_clock = "PASS"
except ValueError as exc:
    publication_clock = str(exc)
summary = {"operation_id": binding["run_id"], "observed_at_utc": now.isoformat(),
    "installed_root": str(LIVE), "article_identity": result["article_identity"],
    "package_revision": native_review_revision(result), "source_count": len(result["evidence"]),
    "source_hashes_match": all(sha256(d["canonical_content_text"].encode()).hexdigest() == d["canonical_content_sha256"] for d in result["evidence"]),
    "reader_findings": checks, "media": media, "automated_image_check": image_check,
    "data_cutoff_utc": article["reader_article_contract"]["data_cutoff_utc"],
    "publication_clock_check": publication_clock, "media_repair_rounds": 1,
    "derivative_preview_count": len(result["previews"]),
    "media_assets": [{k:a.get(k) for k in ("asset_id", "path", "sha256", "width", "height", "caption", "alt_text", "source_page_url", "attribution")} for a in result["media_assets"]],
    "public_write_performed": False, "new_review_published": False, "schedules_changed": False}
(ROOT / "final-review-package.json").write_text(json.dumps({"summary": summary, "article": article,
    "reader_article": reader, "previews": result["previews"], "media_assets": result["media_assets"],
    "evidence": result["evidence"]}, indent=2), encoding="utf-8")
(HERE / "review-package-readback.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
(HERE / "article-review.md").write_text("# " + reader["title"] + "\n\n" + reader.get("dek", "") +
    "\n\n" + reader["substack_body_markdown"] + "\n", encoding="utf-8")
(HERE / "derivative-previews.json").write_text(json.dumps(result["previews"], indent=2), encoding="utf-8")
print(json.dumps({k: summary[k] for k in ("article_identity", "package_revision", "reader_findings",
    "source_count", "source_hashes_match", "derivative_preview_count", "publication_clock_check")}))
