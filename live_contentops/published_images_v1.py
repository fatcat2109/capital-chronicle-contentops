"""Decision 93's image register, shared by the sole publication coordinator.

Reservations fence concurrent article writes, including lost provider returns. They
are released only after the coordinator establishes absence. This is no work queue.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import os
from pathlib import Path
from statistics import median

from live_contentops.published_content_v1 import _locked_feed, canonical, read_records

SCHEMA = "contentops.published_images.v1"
DAILY_LIMIT = 2
NEAR_DISTANCE = 6
_COS = [[math.cos((2 * x + 1) * k * math.pi / 64) for x in range(32)] for k in range(8)]


class ImagePolicyError(ValueError):
    pass


def day_of(value):
    value = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if value.tzinfo is None:
        raise ImagePolicyError("PUBLICATION_CLOCK_REQUIRED")
    from live_contentops.newsroom_production_day_v1 import newsroom_production_date
    return newsroom_production_date(value).isoformat()


def fingerprint(path):
    """Exact SHA256 and 64-bit DCT perceptual hash, invariant to image encoding/size."""
    from PIL import Image, ImageOps
    path = Path(path)
    if not path.is_file():
        raise ImagePolicyError("IMAGE_MISSING")
    raw = path.read_bytes()
    try:
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source)
            width, height = image.size
            pixels = list(image.convert("L").resize((32, 32), Image.Resampling.LANCZOS).getdata())
    except (OSError, ValueError) as exc:
        raise ImagePolicyError("IMAGE_MISSING") from exc
    if min(width, height) < 32:
        raise ImagePolicyError("IMAGE_MISSING")
    rows = [[sum(pixels[y * 32 + x] * _COS[u][x] for x in range(32))
             for u in range(8)] for y in range(32)]
    coefficients = [sum(rows[y][u] * _COS[v][y] for y in range(32))
                    for v in range(8) for u in range(8)]
    midpoint = median(coefficients[1:])
    bits = sum((1 << i) for i, value in enumerate(coefficients) if i and value > midpoint)
    return {"sha256": sha256(raw).hexdigest(), "perceptual_hash": f"{bits:016x}",
            "width": width, "height": height}


def near(left, right):
    return (left["sha256"] == right["sha256"] or
            (int(left["perceptual_hash"], 16) ^ int(right["perceptual_hash"], 16)).bit_count() <= NEAR_DISTANCE)


def _read(raw):
    if raw and not raw.endswith(b"\n"):
        raise ImagePolicyError("IMAGE_REGISTER_TORN_TAIL")
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if any(row.get("schema_version") != SCHEMA or row.get("state") not in {"RESERVED", "PUBLISHED", "ABSENT"}
           for row in rows):
        raise ImagePolicyError("IMAGE_REGISTER_INVALID")
    return rows


def _append(handle, row):
    handle.seek(0, os.SEEK_END)
    data = canonical({"schema_version": SCHEMA, **row}) + b"\n"
    if handle.write(data) != len(data):
        raise ImagePolicyError("IMAGE_REGISTER_APPEND_INCOMPLETE")
    handle.flush()
    os.fsync(handle.fileno())


def _active(rows):
    latest = {}
    for row in rows:
        latest[row["record_id"]] = row
    return [row for row in latest.values() if row["state"] != "ABSENT"]


class PublishedImages:
    def __init__(self, path, *, published_feed=None):
        self.path = Path(path)
        self.published_feed = Path(published_feed) if published_feed is not None else None

    def records(self):
        return _read(self.path.read_bytes()) if self.path.is_file() else []

    def _daily_pieces(self, rows, now):
        day = day_of(now)
        pieces = {row.get("canonical_url") or row["piece_id"] for row in _active(rows)
                  if row.get("counts_as_article", True) and (row.get("day") == day
                      or day in row.get("possible_publication_days", []) or row["state"] == "RESERVED")}
        if self.published_feed and self.published_feed.is_file():
            pieces.update(next(o["url"] for o in row["outlets"] if o["name"] == "substack")
                          for row in read_records(self.published_feed)
                          if day_of(row["published_at_utc"]) == day)
        return pieces

    def reserve(self, *, piece_id, assets, lead_asset_id, now, canonical_url=None, enforce_cap=True):
        if not assets or lead_asset_id not in {a.get("asset_id") for a in assets}:
            raise ImagePolicyError("IMAGE_MISSING")
        images = []
        for asset in assets:
            item = fingerprint(asset.get("path") or asset.get("absolute_local_source_path") or "")
            if asset.get("sha256") and item["sha256"] != asset["sha256"]:
                raise ImagePolicyError("IMAGE_BYTES_CHANGED")
            images.append({"asset_id": asset["asset_id"], **item})
        with _locked_feed(self.path) as handle:
            rows = _read(handle.read())
            active = _active(rows)
            own = [r for r in active if r["piece_id"] == piece_id or
                   (canonical_url and r.get("canonical_url") == canonical_url)]
            # Sharing an article's image across its destinations is required distribution.
            others = [r for r in active if r not in own]
            if any(near(image, previous) for image in images for r in others for previous in r["images"]):
                raise ImagePolicyError("IMAGE_REUSED")
            already_today = any(r["day"] == day_of(now) or r["state"] == "PUBLISHED" for r in own)
            if enforce_cap and not already_today and len(self._daily_pieces(rows, now)) >= DAILY_LIMIT:
                raise ImagePolicyError("DAILY_ARTICLE_CAP_REACHED")
            record_id = sha256(canonical([piece_id, [i["sha256"] for i in images]])).hexdigest()
            existing = next((r for r in own if r["record_id"] == record_id), None)
            if existing:
                if existing["state"] == "RESERVED" and existing["day"] != day_of(now):
                    existing = {**existing, "day": day_of(now),
                                "recorded_at_utc": now.astimezone(timezone.utc).isoformat()}
                    _append(handle, existing)
                return existing
            row = {"record_id": record_id, "piece_id": piece_id, "state": "RESERVED",
                   "day": day_of(now), "recorded_at_utc": now.astimezone(timezone.utc).isoformat(),
                   "canonical_url": canonical_url, "counts_as_article": enforce_cap,
                   "lead_asset_id": lead_asset_id, "images": images}
            _append(handle, row)
            return row

    def settle(self, piece_id, *, state, now, canonical_url=None, published_at_utc=None):
        if state not in {"PUBLISHED", "ABSENT"}:
            raise ImagePolicyError("IMAGE_REGISTER_SETTLEMENT_INVALID")
        with _locked_feed(self.path) as handle:
            rows = _active(_read(handle.read()))
            for row in rows:
                if row["piece_id"] != piece_id or row["state"] == state:
                    continue
                # Confirmed publication is never undone by a later destination's absence.
                if row["state"] == "PUBLISHED" and state == "ABSENT":
                    continue
                _append(handle, {**row, "state": state,
                    "day": day_of(published_at_utc) if published_at_utc else row["day"],
                    "possible_publication_days": [] if published_at_utc else sorted({row["day"], day_of(now)}),
                    "published_at_utc": published_at_utc,
                    "publication_clock_basis": "OBSERVED_PUBLICATION_CLOCK" if published_at_utc else "RESERVATION_TO_READBACK_INTERVAL",
                    "canonical_url": canonical_url or row.get("canonical_url"),
                    "recorded_at_utc": now.astimezone(timezone.utc).isoformat()})

    def seed(self, *, piece_id, canonical_url, images, published_at, observation_ref,
             counts_as_article=True, clock_basis="OBSERVED_PUBLICATION_CLOCK"):
        """Admit exact retained send bytes or bytes from an observed public image URL."""
        if not images or not observation_ref:
            raise ImagePolicyError("PUBLISHED_IMAGE_OBSERVATION_REQUIRED")
        bound = [{"asset_id": str(i.get("asset_id") or index), **fingerprint(i["path"])}
                 for index, i in enumerate(images)]
        record_id = sha256(canonical([piece_id, observation_ref, [i["sha256"] for i in bound]])).hexdigest()
        row = {"record_id": record_id, "piece_id": piece_id, "state": "PUBLISHED",
               "canonical_url": canonical_url, "day": day_of(published_at),
               "published_at_utc": published_at,
               "publication_clock_basis": clock_basis,
               "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
               "counts_as_article": counts_as_article, "lead_asset_id": bound[0]["asset_id"],
               "images": bound, "observation_ref": observation_ref}
        with _locked_feed(self.path) as handle:
            prior = [r for r in _read(handle.read()) if r["record_id"] == record_id]
            if prior and all(prior[-1].get(k) == row.get(k) for k in row if k != "recorded_at_utc"):
                return False
            _append(handle, row)
        return True
