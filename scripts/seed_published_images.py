"""Seed decision 93's register from retained send bindings and a Neo public inventory.

Downloads only the exact public image URLs already observed in the supplied
inventory; no website scraping, browser control, credentials or publication.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.article_publication_quality_v1 import piece_id  # noqa: E402
from live_contentops.published_images_v1 import PublishedImages, fingerprint, _active  # noqa: E402
from live_contentops.media_manifest_authority_v1 import original_substack_media_url  # noqa: E402


def retained_images(store_path, register):
    connection = sqlite3.connect(Path(store_path).resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    rows = connection.execute("SELECT d.*,m.payload,m.work_item_id FROM platform_dispatches d JOIN outbox_messages m "
        "ON m.message_id=d.message_id WHERE d.status IN ('DISPATCH_CONFIRMED','EXTERNAL_REMOVAL_REPORTED_NO_RETRY') "
        "AND d.public_object_id IS NOT NULL").fetchall()
    connection.close()
    canonicals = {r["work_item_id"]: r["public_object_url"] for r in rows if r["platform"] == "substack"}
    count, images, gaps, without_images = 0, 0, [], []
    for row in rows:
        intent = json.loads(row["payload"])
        context_path = Path(str(intent.get("output_dir") or "")) / "run_context_v1.json"
        context = json.loads(context_path.read_bytes()) if context_path.is_file() else {}
        media = context.get("media") or {}
        assets = list(intent.get("media_assets") or media.get("assets") or [])
        assets += [a for a in media.get("delivery_only_assets") or [] if a.get("asset_id") not in {b.get("asset_id") for b in assets}]
        # Older text-first canonicals kept their social card only in the hosting
        # manifest. That is still a published image and remains usable evidence.
        manifest_path = context_path.parent / "delivery_media_manifest_v1.json"
        if not assets and row["platform"] != "substack" and manifest_path.is_file():
            assets = list(json.loads(manifest_path.read_bytes()).get("assets") or [])
        payload = intent.get("native_payload") or {}
        selected = list(payload.get("media_asset_ids") or []) if isinstance(payload, dict) else []
        if isinstance(payload, dict):
            selected += [i for p in payload.get("posts") or [] if isinstance(p, dict) for i in p.get("media_asset_ids") or []]
        if row["platform"] != "substack" and selected:
            assets = [a for a in assets if a.get("asset_id") in selected]
        known = []
        for asset in assets:
            path = Path(str(asset.get("path") or asset.get("absolute_local_source_path") or ""))
            if path.is_file() and fingerprint(path)["sha256"] == asset.get("sha256"):
                known.append({"asset_id": asset.get("asset_id"), "path": str(path)})
            else:
                gaps.append({"dispatch_id": row["dispatch_id"], "asset_id": asset.get("asset_id"), "cause": "RETAINED_IMAGE_BYTES_UNAVAILABLE"})
        if known:
            class Store:
                db_path = store_path
            count += int(register.seed(piece_id=piece_id(Store(), {"work_item_id": row["work_item_id"]}),
                canonical_url=canonicals.get(row["work_item_id"]), images=known,
                published_at=row["dispatched_at"], observation_ref="coordinator:" + row["dispatch_id"],
                counts_as_article=row["platform"] == "substack" and not bool(intent.get("plan_status_post") or intent.get("daily_digest")),
                clock_basis="RETAINED_COORDINATOR_DISPATCH_CLOCK"))
            images += len(known)
        else:
            without_images.append({"dispatch_id": row["dispatch_id"], "platform": row["platform"],
                                   "context_path": str(context_path), "context_exists": context_path.is_file()})
    return {"dispatches_inspected": len(rows), "register_rows_added": count, "image_occurrences": images,
            "without_bound_image": without_images, "gaps": gaps}


def public_images(inventory, register, cache):
    cache.mkdir(parents=True, exist_ok=True)
    count, downloaded, gaps = 0, {}, []
    for article in inventory["articles"]:
        images = []
        for index, image in enumerate(article["images"]):
            url = original_substack_media_url(image["url"])
            if urlsplit(url).hostname not in {"substack-post-media.s3.amazonaws.com", "substackcdn.com"}:
                raise ValueError("PUBLIC_IMAGE_HOST_NOT_OBSERVED")
            path = cache / (sha256(url.encode()).hexdigest() + ".image")
            try:
                if not path.is_file():
                    with urlopen(Request(url, headers={"User-Agent": "CapitalChronicle published-image inventory"}), timeout=15) as response:
                        raw = response.read(32 * 1024 * 1024 + 1)
                    if len(raw) > 32 * 1024 * 1024:
                        raise ValueError("PUBLIC_IMAGE_TOO_LARGE")
                    path.write_bytes(raw)
                item = fingerprint(path)
                downloaded[url] = {"path": str(path), **item}
                images.append({"asset_id": "public-" + str(index), "path": str(path)})
            except (OSError, ValueError) as exc:
                gaps.append({"article_url": article["url"], "image_url": url, "cause": type(exc).__name__})
        if images:
            if not article.get("published_at"):
                gaps.append({"article_url": article["url"], "cause": "PUBLICATION_CLOCK_ABSENT"})
                continue
            count += int(register.seed(piece_id=article["url"], canonical_url=article["url"], images=images,
                published_at=article["published_at"], observation_ref="neo-public-image-inventory:" + article["url"],
                counts_as_article="daily-digest" not in article["url"]))
    return {"articles_inspected": len(inventory["articles"]), "register_rows_added": count,
            "unique_images": len(downloaded), "images": list(downloaded.values()), "gaps": gaps}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--feed", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    register = PublishedImages(args.feed.parent / "published_images_v1.jsonl", published_feed=args.feed)
    result = {"recorded_at_utc": datetime.now(timezone.utc).isoformat(), "register": str(register.path),
              "retained": retained_images(args.store, register),
              "public": public_images(json.loads(args.inventory.read_bytes()), register, args.cache)}
    active = _active(register.records())
    result["register_summary"] = {"active_records": len(active),
        "distinct_exact_images": len({image["sha256"] for row in active for image in row["images"]}),
        "distinct_perceptual_hashes": len({image["perceptual_hash"] for row in active for image in row["images"]})}
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(args.result), "retained_rows": result["retained"]["register_rows_added"],
                      "public_rows": result["public"]["register_rows_added"],
                      "gaps": len(result["retained"]["gaps"]) + len(result["public"]["gaps"])}))


if __name__ == "__main__":
    main()
