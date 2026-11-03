"""CC-144 deterministic post visuals, inside the existing media/review owners.

No acquisition, model call, publisher, store or schedule lives here. Cards project
already validated article claims; the native final review still inspects the pixels.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import re

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of

POLICY = "CC144_EVERY_POST_VISUAL_V1"
DESTINATIONS = ("telegram", "discord", "x", "linkedin", "facebook_page",
                "instagram_business", "threads", "youtube")
_NUMBERS = re.compile(r"(?<!\w)[+-]?\d[\d,]*(?:\.\d+)?%?")
_SURVEYS = re.compile(r"\b(?:ism|ismworld|s&p global|spglobal|pmi|conference[ -]board|umich|university of michigan|adp)\b", re.I)


def _normal(value):
    return " ".join(str(value or "").split())


def reject_private_survey_visual(document, context=""):
    """Decision 44 applies even when another receipt admits factual paraphrase."""
    identity = " ".join(str(document.get(k) or "") for k in (
        "publisher", "source_url", "url", "source_adapter_family", "title"))
    if _SURVEYS.search(identity + " " + context) or document.get("private_survey") is True:
        raise ValueError("PRIVATE_SURVEY_HEADLINE_ONLY_NO_VISUAL")


def public_visual_source(document):
    reject_private_survey_visual(document)
    constraints = document.get("source_reuse_constraints") or {}
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _underlying_source_rights
    rights, _ = _underlying_source_rights(document)
    if rights == "public_domain" and document.get("rights_evidence_sha256"):
        return "public_domain"
    if (constraints.get("scope") in {"ATTRIBUTED_REPORTED_FACTS_ONLY_INDEPENDENT_PUBLIC_PARAPHRASE",
            "ATTRIBUTED_ORIGINAL_FACTS_ONLY_INDEPENDENT_PUBLIC_PARAPHRASE"}
            and constraints.get("attribution_required") is True
            and constraints.get("policy_capture_sha256") and constraints.get("source_capture_sha256")):
        return "attributed_facts_independent_chart"
    raise ValueError("DATA_CARD_PUBLIC_RIGHTS_REQUIRED")


def _bound_fact(claim, article, documents):
    source = next((d for d in documents if d.get("source_id") == claim.get("source_id")), None)
    if not source or not claim.get("source_id"):
        raise ValueError("DATA_CARD_FACT_SOURCE_REQUIRED")
    rights = public_visual_source(source)
    text, excerpt = _normal(claim.get("claim_text")), _normal(claim.get("support_excerpt"))
    reject_private_survey_visual(source, text + " " + excerpt)
    body = _normal(" ".join(str(article.get(k) or "") for k in (
        "title", "dek", "substack_body_markdown", "social_hook", "search_title", "seo_title", "meta_description")))
    canonical = str(source.get("canonical_content_text") or "")
    if (not text or not excerpt or text not in body or excerpt not in _normal(canonical)
            or not set(_NUMBERS.findall(text)) <= set(_NUMBERS.findall(excerpt))):
        raise ValueError("DATA_CARD_FACT_OR_NUMBER_NOT_IN_POST_AND_SOURCE")
    url = source.get("url") or source.get("source_url")
    if not str(url or "").startswith("https://") or not source.get("publisher"):
        raise ValueError("DATA_CARD_PUBLIC_ATTRIBUTION_REQUIRED")
    return {"claim_id": claim.get("claim_id"), "text": text, "source_id": claim["source_id"],
        "document_id": source["document_id"], "support_excerpt": claim["support_excerpt"],
        "source_content_sha256": sha256(canonical.encode()).hexdigest(), "rights_class": rights,
        "rights_binding_sha256": sha256_of({k: source.get(k) for k in (
            "underlying_reuse_classification", "rights_evidence_sha256", "source_reuse_constraints")}),
        "publisher": source["publisher"], "url": url}


def _render_card(packet, path, mini_chart=None):
    from PIL import Image, ImageDraw, ImageFont
    from matplotlib.font_manager import findfont, FontProperties
    font_path = findfont(FontProperties(family="DejaVu Sans"))
    regular = ImageFont.truetype(font_path, 35)
    small = ImageFont.truetype(font_path, 25)
    heading = ImageFont.truetype(font_path, 52)
    canvas = Image.new("RGB", (1080, 2400), "#f5f2eb")
    draw = ImageDraw.Draw(canvas)

    def wrap(text, font, width):
        lines, current = [], ""
        for word in text.split():
            if draw.textlength(word, font=font) > width:
                raise ValueError("DATA_CARD_UNBREAKABLE_TEXT_TOO_WIDE")
            candidate = (current + " " + word).strip()
            if current and draw.textlength(candidate, font=font) > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        return lines + ([current] if current else [])

    draw.rectangle((0, 0, 1080, 16), fill="#12685a")
    draw.text((64, 58), "CAPITAL CHRONICLE", font=small, fill="#12685a")
    draw.text((64, 106), "Key facts", font=heading, fill="#142d33")
    y = 200
    for fact in packet["facts"]:
        for line in wrap(fact["text"], regular, 952):
            draw.text((64, y), line, font=regular, fill="#142d33")
            y += 49
        y += 12
        for line in wrap(fact["publisher"], small, 952):
            draw.text((64, y), line, font=small, fill="#4e666b")
            y += 35
        y += 32
    if mini_chart:
        available = min(680, 1350 - y - 130)
        if available < 420:
            raise ValueError("DATA_CARD_CONTENT_EXCEEDS_READABLE_LAYOUT")
        with Image.open(mini_chart) as original:
            image = original.convert("RGB")
            image.thumbnail((952, available), Image.Resampling.LANCZOS)
            canvas.paste(image, ((1080 - image.width) // 2, y))
            y += image.height + 30
    if y > 1250:
        raise ValueError("DATA_CARD_CONTENT_EXCEEDS_READABLE_LAYOUT")
    draw.line((64, y, 1016, y), fill="#b4c4bf", width=2)
    draw.text((64, y + 24), "Analysis, not financial advice.", font=small, fill="#4e666b")
    canvas = canvas.crop((0, 0, 1080, max(1080, y + 100)))
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, format="PNG")
    return canvas.size


def _validate_card_series(packet, article, documents):
    ids = {v["document_id"] for s in packet["series"] for p in s["points"] for v in p["inputs"]}
    if not ids <= {d.get("document_id") for d in documents}:
        raise ValueError("DATA_CARD_SERIES_SOURCE_REQUIRED")
    for document in documents:
        if document.get("document_id") in ids and public_visual_source(document) != "public_domain":
            raise ValueError("DATA_CARD_HISTORY_REQUIRES_PUBLIC_DOMAIN_SERIES")
    body_numbers = set(_NUMBERS.findall(_normal(article.get("substack_body_markdown"))))
    for series in packet["series"]:
        for point in series["points"]:
            if not set(_NUMBERS.findall(str(point["value"]))) <= body_numbers:
                raise ValueError("DATA_CARD_SERIES_NUMBER_NOT_IN_POST")


def build_post_data_card(article, claims, documents, *, output_dir, series_packet=None):
    """Render only admitted claims present in this post. No number extraction guesses."""
    facts, seen = [], set()
    for claim in claims:
        text = _normal(claim.get("claim_text"))
        if not text or text in seen or len(text) > 280:
            continue
        try:
            fact = _bound_fact(claim, article, documents)
        except ValueError as exc:
            if str(exc) in {"PRIVATE_SURVEY_HEADLINE_ONLY_NO_VISUAL", "DATA_CARD_PUBLIC_RIGHTS_REQUIRED"}:
                continue
            raise
        facts.append(fact)
        seen.add(text)
        if len(facts) == (1 if series_packet else 3):
            break
    if not facts:
        raise ValueError("DATA_CARD_NO_ADMITTED_PUBLIC_VISUAL_FACTS")
    packet = {"policy": POLICY, "facts": facts}
    mini = None
    if series_packet:
        from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_editorial_data_chart
        _validate_card_series(series_packet, article, documents)
        mini = build_editorial_data_chart(series_packet, documents, output_dir=output_dir)
        packet["series_asset"] = mini
    while True:
        digest = sha256_of(packet)
        asset_id = "post-facts-" + digest[:20]
        path = Path(output_dir).resolve() / "media_assets" / (asset_id + ".png")
        try:
            width, height = _render_card(packet, path, mini["path"] if mini else None)
            break
        except ValueError as exc:
            if str(exc) != "DATA_CARD_CONTENT_EXCEEDS_READABLE_LAYOUT" or len(facts) == 1:
                raise
            facts.pop()  # Keep complete claims and readable type inside Instagram's 4:5 limit.
    path.with_suffix(".json").write_bytes(canonical_bytes(packet))
    return {"asset_id": asset_id, "path": str(path), "sha256": sha256(path.read_bytes()).hexdigest(),
        "width": width, "height": height, "modality": "source_bound_data_card",
        "role": "supporting_fact_context", "media_role": "post_key_facts", "caption": "Key facts from the article.",
        "alt_text": " ".join(f["text"] for f in facts),
        "attribution": "Source: " + ", ".join(dict.fromkeys(f["publisher"] for f in facts)),
        "source_page_url": facts[0]["url"],
        "source_links": [{"document_id": f["document_id"], "url": f["url"], "label": f["publisher"]} for f in facts],
        "source_lineage": [{"document_id": f["document_id"], "source_url": f["url"]} for f in facts],
        "underlying_source_rights_status": "attributed_facts_independent_chart",
        "data_card_packet": packet, "transform_sha256": digest,
        "publication_authority": False}


def validate_post_data_card(asset, article, documents):
    packet = asset.get("data_card_packet") or {}
    if packet.get("policy") != POLICY or not 1 <= len(packet.get("facts", [])) <= 3:
        raise ValueError("DATA_CARD_PACKET_REQUIRED")
    for fact in packet["facts"]:
        rebound = _bound_fact({"claim_id": fact["claim_id"], "claim_text": fact["text"],
            "source_id": fact["source_id"], "support_excerpt": fact["support_excerpt"]}, article, documents)
        if fact != rebound:
            raise ValueError("DATA_CARD_SOURCE_OR_RIGHTS_CHANGED")
    if packet.get("series_asset"):
        from live_contentops.rolling_x_grounded_article_media_builder_v1 import validate_editorial_data_chart
        _validate_card_series(packet["series_asset"]["editorial_data_packet"], article, documents)
        validate_editorial_data_chart(packet["series_asset"], documents)
    if (sha256_of(packet) != asset.get("transform_sha256")
            or sha256(Path(asset["path"]).read_bytes()).hexdigest() != asset.get("sha256")):
        raise ValueError("DATA_CARD_PACKET_OR_BYTES_CHANGED")


def complete_post_visuals(article, claims, documents, assets, *, output_dir):
    """Run before previews/review; never mutate a prepared or sent package."""
    article = dict(article)
    assets = list(assets)
    decision = article.get("visual_editorial_decision") or {}
    if decision.get("story_kind") != "ANALYSIS":
        card = build_post_data_card(article, claims, documents, output_dir=output_dir,
            series_packet=decision.get("data_card_series"))
        assets.append(card)
    if not assets:
        raise ValueError("EVERY_POST_IMAGE_REQUIRED")
    fallback = next((a["asset_id"] for a in assets if a.get("modality") == "source_bound_data_card"), assets[0]["asset_id"])
    choices = decision.get("channel_media") or {}
    article["post_visual_policy"] = POLICY
    article["post_visual_destination_media"] = {d: list(choices.get(d) or [fallback]) for d in DESTINATIONS}
    return article, assets


def require_publication_image(destination, data):
    """One pre-send check across Neo and API transports. Readback never calls it."""
    assets = data.get("media_assets") or []
    if destination != "substack":
        payload = data.get("payloads", {}).get(destination) or {}
        selected = set(payload.get("media_asset_ids") or [])
        selected.update(a for post in payload.get("posts") or [] for a in post.get("media_asset_ids") or [])
        assets = [a for a in assets if a.get("asset_id") in selected]
    if not assets:
        raise ValueError("EVERY_POST_IMAGE_REQUIRED:" + destination)
    from PIL import Image
    for asset in assets:
        path = Path(asset.get("path") or asset.get("absolute_local_source_path") or "")
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != asset.get("sha256"):
            raise ValueError("PUBLICATION_IMAGE_BYTES_CHANGED:" + destination)
        with Image.open(path) as pixels:
            if pixels.format not in {"PNG", "JPEG", "WEBP"}:
                raise ValueError("PUBLICATION_IMAGE_FORMAT_UNSUPPORTED:" + destination)
            pixels.verify()
    if destination in {"discord", "facebook_page", "instagram_business", "threads"}:
        primary = data.get("primary_media") or {}
        if (not str(data.get("public_image_url") or "").startswith("https://")
                or primary.get("sha256") not in {a["sha256"] for a in assets}
                or primary.get("local_public_hash_continuity") is not True
                or primary.get("public_delivery_sha256") != primary.get("sha256")):
            raise ValueError("SELECTED_IMAGE_PUBLIC_DELIVERY_REQUIRED:" + destination)
