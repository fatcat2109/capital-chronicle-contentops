"""CC-253: backfill the hosted media rows of the four refused pieces from their own input rows.

Dry run (writes nothing outside --out):
    python docs/publisher/CC-253/backfill_hosted_media_fields.py --out DIR
Apply (in place, only if every live manifest still has the dry run's before-hash):
    python docs/publisher/CC-253/backfill_hosted_media_fields.py --out DIR --apply --expect SUMMARY

The dry run writes each piece's current manifest (<run>.before.json), the proposed one
(<run>.after.json) and backfill-summary.json into --out. Nothing is inferred:
- a row with its own input row (run_context_v1.json media.assets, same id and sha256) gets the
  ARTICLE_MEDIA_FIELDS that input row records and the hosted row lacks;
- a generated post card ("post-card-" + 20 hex, build_post_image_card) becomes delivery-only;
- a row with no input row that is outside the article's reviewed visual decision (its charts and
  contextual photos) becomes delivery-only, since the reader can never place it;
- a row that already carries modality, or is already delivery-only, stays as it is;
- anything else is reported UNRESOLVED and left unchanged.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from live_contentops.cloudinary_delivery_media_v1 import ARTICLE_MEDIA_FIELDS  # noqa: E402

OUTPUTS = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual")
# Resolved 5 Nov 03:20Z from the publication store, as the newsroom reader resolves them.
PIECES = {
    "substack:223555673": OUTPUTS / "cc124-next-article-20261105-a" / "reviewed-handoff"
    / "d619ecc2cd48e8bb6d74958fc5e2295b08fc843402b2b6e4f94b0e07ffd05011",  # PPI
    "substack:223408612": OUTPUTS / "cc124-next-article-20261103-b" / "reviewed-handoff"
    / "5692377ae23398763a31865c1f5892fd0b079d6bb12846ae0b5e225a13a11ba3",  # SEC
    "substack:223199520": OUTPUTS / "cc074-retro-fomc-20261028-v1" / "reviewed-handoff"
    / "babd5c02bcedea40f218c7c582c6982e3c4524936b7e649450dcc63aa1505d43",  # FOMC
    "substack:223246940": OUTPUTS / "cc124-prepare-20261103-a" / "reviewed-handoff"
    / "ea18bb4724470d8440aea1718abc0c18c32befac1c8ba9a56b0f457fad85d305",  # CPI
}
POST_CARD_ID = re.compile(r"post-card-[0-9a-f]{20}")
DELIVERY_ONLY = {"media_role": "delivery_only", "article_inclusion": False,
                 "canonical_article_media": False, "delivery_only": True}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _encode(value: dict, like: bytes) -> bytes:
    """The writer's own format (indent 2, sorted keys, trailing newline) and line endings."""
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if b"\r\n" in like:
        text = text.replace("\n", "\r\n")
    return text.encode("utf-8")


def backfill(package: Path) -> tuple[bytes, bytes, list[dict]]:
    manifest_path = package / "delivery_media_manifest_v1.json"
    before_bytes = manifest_path.read_bytes()
    manifest = json.loads(before_bytes)
    media = _read_json(package / "run_context_v1.json").get("media") or {}
    inputs = {(row.get("asset_id"), str(row.get("sha256") or "").casefold()): row
              for row in media.get("assets") or [] if isinstance(row, dict)}
    decision = _read_json(package / "article_manifest_v1.json").get("visual_editorial_decision") or {}
    reviewed = {c.get("asset_id") for c in decision.get("charts") or []} | set(decision.get("contextual_photo_ids") or [])
    rows, report = [], []
    for original in manifest.get("assets") or []:
        row = dict(original)
        mid, sha = row.get("media_asset_id"), str(row.get("sha256") or "").casefold()
        raw = inputs.get((mid, sha))
        added: list[str] = []
        if row.get("media_role") == "delivery_only" and row.get("delivery_only") is True:
            basis = "ALREADY_DELIVERY_ONLY"
        elif POST_CARD_ID.fullmatch(str(mid)):
            basis = "POST_CARD"
            row.update(DELIVERY_ONLY)
        elif raw is not None:
            basis = "INPUT_ROW"
            added = [k for k in ARTICLE_MEDIA_FIELDS if raw.get(k) not in (None, "") and row.get(k) in (None, "")]
            row.update({k: raw[k] for k in added})
        elif row.get("modality"):
            basis = "ALREADY_COMPLETE"
        elif mid not in reviewed:
            basis = "NOT_IN_REVIEWED_VISUAL_DECISION"
            row.update(DELIVERY_ONLY)
        else:
            basis = "UNRESOLVED"
        rows.append(row)
        report.append({"media_asset_id": mid, "sha256": sha, "basis": basis, "added_fields": added,
                       "delivery_only_set": basis in {"POST_CARD", "NOT_IN_REVIEWED_VISUAL_DECISION"}})
    after_bytes = _encode({**manifest, "assets": rows}, before_bytes)
    return before_bytes, after_bytes, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expect", type=Path, help="the dry run's backfill-summary.json (required with --apply)")
    args = parser.parse_args()
    expected = {p["content_id"]: p for p in _read_json(args.expect)["pieces"]} if args.expect else {}
    if args.apply and not expected:
        parser.error("--apply needs --expect")
    args.out.mkdir(parents=True, exist_ok=True)
    pieces = []
    for content_id, package in PIECES.items():
        before, after, report = backfill(package)
        piece = {"content_id": content_id, "package": str(package),
                 "before_sha256": sha256(before).hexdigest(), "after_sha256": sha256(after).hexdigest(),
                 "changed": before != after, "rows": report}
        name = package.parent.parent.name
        (args.out / f"{name}.before.json").write_bytes(before)
        (args.out / f"{name}.after.json").write_bytes(after)
        if args.apply and piece["changed"]:
            want = expected.get(content_id) or {}
            if (piece["before_sha256"], piece["after_sha256"]) != (want.get("before_sha256"), want.get("after_sha256")):
                raise SystemExit(f"STOP {content_id}: the live manifest or the proposed bytes changed since the dry run")
            target = package / "delivery_media_manifest_v1.json"
            temporary = target.with_name(target.name + ".cc253-tmp")
            temporary.write_bytes(after)
            os.replace(temporary, target)
            if sha256(target.read_bytes()).hexdigest() != piece["after_sha256"]:
                raise SystemExit(f"STOP {content_id}: readback differs from the written bytes")
            piece["applied"] = True
        pieces.append(piece)
    summary = {"schema": "contentops.cc253_hosted_media_backfill.v1", "applied": bool(args.apply), "pieces": pieces}
    (args.out / ("backfill-applied.json" if args.apply else "backfill-summary.json")).write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    for piece in pieces:
        bases = [f'{r["media_asset_id"]}:{r["basis"]}' + (f'+{len(r["added_fields"])}' if r["added_fields"] else "")
                 for r in piece["rows"]]
        print(piece["content_id"], "changed" if piece["changed"] else "unchanged",
              piece["before_sha256"][:12], "->", piece["after_sha256"][:12], "|", ", ".join(bases))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
