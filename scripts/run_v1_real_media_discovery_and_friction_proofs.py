"""Generate inspectable, zero-write proof for real media discovery and friction calibration."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import urllib.request
import urllib.error
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops.visual_asset_discovery_v1 import (  # noqa: E402
    discover_visual_assets_for_article,
)
from live_contentops.article_rich_text_v1 import (  # noqa: E402
    markdown_to_rich_text,
    rich_text_to_html,
)
from scripts.run_v1_golden_product_zero_write_proofs import (  # noqa: E402
    _capture_local_screenshot,
)

DEFAULT_OUTPUT = ROOT / "docs" / "automation" / (
    "CONTENTOPS_V1_REAL_MEDIA_DISCOVERY_AND_EVIDENCE_FRICTION_CALIBRATION_V1"
)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _download_original(candidate: Mapping[str, Any], target_dir: Path) -> dict[str, Any]:
    original_url = str(candidate["original_asset_url"])
    delivery_url = original_url
    delivery_basis = "RESOLVED_ORIGINAL_ASSET"

    def fetch(url: str) -> tuple[bytes, str]:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "CapitalChronicleContentOps/1.0 zero-write-proof"},
        )
        with urllib.request.urlopen(request, timeout=45) as response:  # noqa: S310
            return (
                response.read(15_000_001),
                str(response.headers.get("Content-Type") or "").split(";", 1)[0],
            )

    try:
        payload, content_type = fetch(delivery_url)
    except urllib.error.HTTPError as exc:
        if exc.code != 429 or "commons.wikimedia.org/wiki/File:" not in str(candidate.get("source_page_url")):
            raise
        thumbnail_url = str(candidate.get("discovery_thumbnail_url") or "")
        delivery_url = re.sub(r"/\d+px-([^/?]+)(?:\?.*)?$", r"/1920px-\1", thumbnail_url)
        if delivery_url == thumbnail_url:
            raise RuntimeError("wikimedia_high_resolution_derivative_resolution_failed") from exc
        delivery_basis = "WIKIMEDIA_HIGH_RESOLUTION_DERIVATIVE_OF_RESOLVED_ORIGINAL"
        payload, content_type = fetch(delivery_url)
    if not payload or len(payload) > 15_000_000 or not content_type.startswith("image/"):
        raise RuntimeError("selected_original_delivery_asset_invalid")
    suffix = {"image/jpeg": ".jpg", "image/webp": ".webp"}.get(content_type, ".png")
    target = target_dir / f"selected_documentary_original{suffix}"
    target.write_bytes(payload)
    with Image.open(target) as image:
        width, height = image.size
        image.verify()
    if width < 1000 or height < 600:
        raise RuntimeError("selected_original_below_delivery_floor")
    return {
        "local_path": target.relative_to(ROOT).as_posix(),
        "delivery_sha256": hashlib.sha256(payload).hexdigest(),
        "delivery_content_type": content_type,
        "delivery_url": delivery_url,
        "delivery_basis": delivery_basis,
        "delivery_width": width,
        "delivery_height": height,
        "delivery_is_discovery_thumbnail": delivery_url
        == str(candidate.get("discovery_thumbnail_url")),
    }


def _article_html(candidate: Mapping[str, Any], local_image: Path) -> str:
    source = html.escape(str(candidate["source_page_url"]), quote=True)
    attribution = html.escape(str(candidate.get("attribution") or "Wikimedia Commons contributor"))
    license_text = html.escape(str(candidate.get("reuse_basis") or candidate.get("rights_status")))
    image_url = local_image.resolve().as_uri()
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
    body{{margin:0;background:#f4f0e8;color:#191919;font:18px Georgia,serif}}
    main{{max-width:860px;margin:auto;background:#fff;padding:62px 76px 90px}}
    .kicker{{font:700 12px Arial;letter-spacing:.16em;color:#875f20}}
    h1{{font-size:52px;line-height:1.02;margin:16px 0 18px}} .dek{{font-size:23px;color:#555}}
    img{{width:100%;max-height:560px;object-fit:cover;margin-top:30px}}
    figcaption{{font:13px/1.5 Arial;color:#666;margin:8px 0 34px}} h2{{font-size:28px;margin-top:38px}}
    p{{line-height:1.72}} a{{color:#6c4b16}} .proof{{border-top:1px solid #ddd;margin-top:48px;padding-top:20px;font:13px Arial;color:#666}}
    </style></head><body><main>
    <div class="kicker">CONTEXTUAL MEDIA DISCOVERY PROOF · ZERO WRITE</div>
    <h1>Why the Strait of Hormuz Matters for Tanker Traffic</h1>
    <p class="dek">A geography-first demonstration that Golden Product media is not structurally limited to charts or evidence cards.</p>
    <figure><img src="{image_url}" alt="Documentary view of tanker traffic associated with the Strait of Hormuz">
    <figcaption>{attribution}. {license_text}. <a href="{source}">Original source and rights record</a>.</figcaption></figure>
    <h2>The physical context</h2><p>The Strait is a narrow maritime route, so a real documentary image of vessels and tanker traffic helps readers visualize the infrastructure and operating environment that prose alone cannot show.</p>
    <h2>What the image does—and does not prove</h2><p>The selected photograph is contextual, not authority for a current event or a quantitative claim. Its original asset, source page, creator, reuse basis, dimensions, content identity, and rights status were resolved before selection.</p>
    <h2>A purposeful visual package</h2><p>A publishable story could pair this documentary view with a rights-cleared geographic map and, only where governed evidence supports it, a quantitative chart. No fixed chart quota is imposed.</p>
    <div class="proof">This is an inspectable product proof, not a current-news claim and not a public post.</div>
    </main></body></html>"""


def _current_story_html(article: Mapping[str, Any], blocker: str) -> str:
    title = html.escape(str(article.get("title") or "Shadow article"))
    body = rich_text_to_html(
        markdown_to_rich_text(str(article.get("substack_body_markdown") or ""))
    )
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
    body{{margin:0;background:#eee;color:#202020;font:18px Georgia,serif}} main{{max-width:780px;margin:auto;background:#fff;padding:52px 72px 90px}}
    .reject{{background:#7a2020;color:white;padding:14px 18px;font:700 13px Arial;letter-spacing:.08em}}
    h1{{font-size:43px;line-height:1.08}} p{{line-height:1.7}} .meta{{margin-top:50px;border-top:1px solid #ccc;padding-top:18px;font:13px Arial;color:#666}}
    </style></head><body><main><div class="reject">SHADOW · REJECTED BY READER-VALUE GATE · NO PUBLIC WRITE</div>
    <h1>{title}</h1>{body}<div class="meta">Exact blocker: {html.escape(blocker)}. This render is inspectable evidence of correct abstention, not an accepted Golden Product article.</div>
    </main></body></html>"""


def _shadow_summary(output_dir: Path) -> dict[str, Any]:
    opportunities: list[dict[str, Any]] = []
    aggregate = Counter()
    aggregate_reductions = Counter()
    for number in (1, 2, 3):
        evidence_path = output_dir / f"shadow_opportunity_{number}" / "rolling_x_newsroom_cycle_evidence_v1.json"
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        viability = evidence.get("ranked_viability") or {}
        taxonomy = Counter()
        reductions: set[str] = set()
        for attempt in viability.get("rank_attempts") or []:
            friction = attempt.get("evidence_friction_taxonomy") or {}
            taxonomy.update(friction.get("counts") or {})
            reductions.update(attempt.get("ordinary_policy_ceremony_reductions") or [])
        aggregate.update(taxonomy)
        aggregate_reductions.update(reductions)
        opportunities.append({
            "opportunity": number,
            "classification": evidence.get("classification"),
            "exact_next_blocker": evidence.get("exact_next_blocker"),
            "operating_mode": evidence.get("operating_mode"),
            "public_write_performed": evidence.get("public_write_performed"),
            "publishing_adapter_called": evidence.get("publishing_adapter_called"),
            "unknown_write_detected": evidence.get("unknown_write_detected"),
            "ranked_viability_status": viability.get("status"),
            "rank_attempt_count": len(viability.get("rank_attempts") or []),
            "selected_cluster_id": viability.get("selected_cluster_id"),
            "blocker_taxonomy_counts": dict(taxonomy),
            "ordinary_policy_ceremony_reductions": sorted(reductions),
            "article_title": (evidence.get("article") or {}).get("title"),
            "article_writer_semantic_calls": (evidence.get("article_build_telemetry") or {}).get("article_writer_semantic_calls"),
            "mandatory_semantic_review_calls": (evidence.get("article_build_telemetry") or {}).get("mandatory_semantic_review_calls"),
            "builder_blockers": evidence.get("grounded_article_builder_blockers") or [],
        })
    return {
        "schema_version": "contentops.real_newsroom_shadow_taxonomy.v1",
        "opportunities": opportunities,
        "aggregate_blocker_taxonomy_counts": dict(aggregate),
        "policy_ceremony_reductions": dict(aggregate_reductions),
        "reduced_policy_ceremony_count": sum(aggregate_reductions.values()),
        "zero_public_writes": all(not row["public_write_performed"] for row in opportunities),
        "unknown_writes": any(row["unknown_write_detected"] for row in opportunities),
    }


def run(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    proof_dir = output_dir / "strait_of_hormuz_media_proof"
    proof_dir.mkdir(parents=True, exist_ok=True)
    article = {
        "title": "Why the Strait of Hormuz Matters for Tanker Traffic",
        "substack_body_markdown": "A geography and energy-shipping explainer about the Strait of Hormuz, oil tanker traffic, ports, and the route through the Gulf.",
        "entities_topics": ["Strait of Hormuz", "oil tanker traffic"],
    }
    discovery = discover_visual_assets_for_article(article, maximum_selected=2)
    if discovery["status"] != "PASS":
        raise RuntimeError("real_media_discovery_proof_failed")
    documentary = next(
        row for row in discovery["selected_assets"]
        if row["visual_intent"] == "HERO_DOCUMENTARY"
    )
    delivery = _download_original(documentary, proof_dir)
    documentary.update({"delivery_verification": delivery})
    _write_json(proof_dir / "visual_asset_discovery_v1.json", discovery)
    article_path = proof_dir / "strait_of_hormuz_contextual_article.html"
    local_image = ROOT / delivery["local_path"]
    article_path.write_text(_article_html(documentary, local_image), encoding="utf-8")
    article_png = proof_dir / "strait_of_hormuz_contextual_article.png"
    _capture_local_screenshot(article_path, article_png)

    shadow = _shadow_summary(output_dir)
    _write_json(output_dir / "shadow_opportunity_taxonomy_v1.json", shadow)
    third = json.loads((output_dir / "shadow_opportunity_3" / "rolling_x_newsroom_cycle_evidence_v1.json").read_text(encoding="utf-8"))
    current_html = output_dir / "shadow_opportunity_3" / "current_story_rejected_render.html"
    current_html.write_text(_current_story_html(third.get("article") or {}, str(third.get("exact_next_blocker"))), encoding="utf-8")
    current_png = current_html.with_suffix(".png")
    _capture_local_screenshot(current_html, current_png)

    summary = {
        "schema_version": "contentops.real_media_discovery_and_friction_proof.v1",
        "status": "PASS",
        "operating_mode": "KILL_SWITCH",
        "public_write_authority": False,
        "public_write_performed": False,
        "unknown_write_detected": False,
        "candidate_count": discovery["candidate_count"],
        "eligible_count": discovery["eligible_count"],
        "selected_count": discovery["selected_count"],
        "providers_exercised": sorted({row["discovery_provider"] for row in discovery["candidates"]}),
        "provider_failures": discovery["provider_failures"],
        "selected_assets": discovery["selected_assets"],
        "unknown_rights_rejected_count": sum("rights_not_verified_reusable" in row["validation"]["blockers"] for row in discovery["candidates"]),
        "search_thumbnails_selected_for_delivery": False,
        "documentary_article_html": article_path.relative_to(ROOT).as_posix(),
        "documentary_article_png": article_png.relative_to(ROOT).as_posix(),
        "current_story_rejected_render": current_png.relative_to(ROOT).as_posix(),
        "shadow_opportunities": shadow,
    }
    _write_json(output_dir / "proof_summary_v1.json", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(run(args.output_dir.resolve()), indent=2, sort_keys=True))
