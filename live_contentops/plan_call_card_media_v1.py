"""Source-bound call-level diagrams. No price history is synthesized."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import textwrap

from .fact_card_design_v1 import _font, PAPER, INK, MUTED, RULE, YELLOW
from .plan_call_cards_v1 import level, _clock, ending_words
from .event_article_guard_v1 import PUBLIC_NOTICE, CONFLICTS_NOTICE


def render(row, folder):
    from PIL import Image, ImageDraw
    packet = {k: row.get(k) for k in ("key", "kind", "instrument_title", "short_id", "levels", "reasons",
        "record_line", "time_exit_utc", "entry_deadline_utc", "card_keys", "text", "at_utc", "source_content_hash", "analysis_publication")}
    packet["renderer"] = "CC399_CALL_CARD_JPEG_V1"
    digest = hashlib.sha256(json.dumps(packet, sort_keys=True).encode()).hexdigest()
    path = Path(folder).resolve() / "media_assets" / f"call-card-{digest[:20]}.jpg"
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1440, 1440), PAPER)
    draw = ImageDraw.Draw(image)
    ink, muted, cyan, gold = INK, MUTED, "#23635c", "#735b00"

    def text(x, y, value, size=30, color=ink, weight="regular", width=80):
        lines = textwrap.wrap(str(value), width=width, break_long_words=False) or [""]
        for line in lines:
            draw.text((x, y), line, fill=color, font=_font(weight, size))
            y += int(size * 1.4)
        return y

    draw.rectangle((72, 0, 304, 12), fill=YELLOW)
    text(72, 55, "CAPITAL CHRONICLE", 28, cyan, width=60)
    if row["kind"] == "run":
        text(72, 160, row["lead"], 64, width=30)
        text(72, 450, "One card per call. Fills and endings stay under their card.", 38, width=48)
        text(72, 1170, _clock(row["at_utc"]), 30, muted)
    else:
        title = row["instrument_title"]
        text(72, 115, title, 49, width=47)
        plan = row["levels"]
        side = "LONG" if plan.get("direction") == "bullish" else "SHORT"
        text(72, 198, f"{side} IDEA   /   #{row['short_id']}", 30, gold)
        if row["kind"] != "setup":
            text(72, 253, ending_words(row) if row["kind"] == "result" else "Model position open", 34, cyan, width=61)
        else:
            text(72, 253, "Conditional on the entry shown below", 30, muted)
        text(72, 330, "PLAN LEVELS  ·  price levels, not price history", 24, muted)
        values = {"Invalidation": plan.get("invalidation_level")}
        for index, value in enumerate(plan.get("target") or []):
            values["Target" if len(plan["target"]) == 1 else f"Target {index + 1}"] = value
        low, high = plan.get("zone_low"), plan.get("zone_high")
        numeric = [float(v) for v in (*values.values(), low, high) if v is not None]
        if numeric:
            bottom, top = min(numeric), max(numeric)
            span = top - bottom or max(abs(top) * .01, .01)
            bottom -= span * .20
            top += span * .20
            def y(value):
                return 735 - int((float(value) - bottom) / (top - bottom) * 335)
            draw.line((115, 385, 115, 760), fill=muted, width=2)
            if low is not None and high is not None:
                first, last = min(y(low), y(high)), max(y(low), y(high))
                draw.rectangle((115, first - 4, 810, last + 4), fill="#a4d4ca")
                text(850, (first + last) // 2 - 18, "Entry zone", 26, cyan, width=30)
                text(850, (first + last) // 2 + 22, f"{level(low, plan)}–{level(high, plan)}", 27, cyan, width=30)
            for name, value in values.items():
                if value is None:
                    continue
                color = "#a33440" if name == "Invalidation" else gold
                draw.line((115, y(value), 810, y(value)), fill=color, width=4)
                text(850, y(value) - 18, f"{name}: {level(value, plan)}", 27, color, width=29)
        line = 800
        if row.get("price_basis") == "plan":
            line = text(72, line, "Levels use the plan's prices.", 23, muted)
        if row.get("time_exit_utc"):
            line = text(72, line, "Time exit: " + _clock(row["time_exit_utc"]), 27, width=80)
        if row.get("entry_deadline_utc"):
            line = text(72, line, "Entry window to " + _clock(row["entry_deadline_utc"]), 25, muted, width=80)
        if plan.get("chance_pct") is not None:
            line = text(72, line, f"{plan['chance_label']}: {plan['chance_pct']:g}% (model estimate)", 27, gold)
        for reason in ([] if row.get("analysis_publication") else row.get("reasons") or []):
            line = text(72, line + 8, "• " + reason, 23, width=102)
        if row.get("analysis_publication"):
            text(72, line + 20, "The structured summary and full analysis accompany this card.", 25, muted, width=90)
        if row.get("record_line"):
            text(72, 1240, row["record_line"], 24, muted, width=95)
    draw.line((72, 1324, 1368, 1324), fill=RULE, width=2)
    text(72, 1344, PUBLIC_NOTICE, 23, muted, width=100)
    text(72, 1383, CONFLICTS_NOTICE, 22, muted, width=105)
    image.save(path, format="JPEG", quality=95, subsampling=0, optimize=True)
    return {"asset_id": "call-card-" + digest[:20], "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "width": 1440, "height": 1440,
        "mime_type": "image/jpeg", "modality": "plan_fact_card", "card_kind": "PLAN_FACT_CARD",
        "media_role": "delivery_only", "role": "plan_facts", "delivery_only": True,
        "article_inclusion": False, "canonical_article_media": False,
        "provenance_status": "VERIFIED_CAPITAL_CHRONICLE_PLAN_EXPORT",
        "rights_basis": "Capital Chronicle's own source-bound call levels and original diagram (CC-399).",
        "attribution": "Capital Chronicle", "caption": row["lead"], "alt_text": row["text"],
        "data_card_packet": packet, "chart_spec": {"kind": "call_levels", "levels": row.get("levels"),
            "source_content_hash": row.get("source_content_hash"), "price_history": False},
        "publication_authority": False}
