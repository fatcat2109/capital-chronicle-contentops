"""CC-245: fact cards in the site's design language (Jim, 4 Nov: the SEC image).

One deterministic renderer for every typographic card (source facts, post facts,
delivery and digest cards). It draws only the text it is given: callers pass
verbatim admitted facts and their attribution, and the key value must be an exact
substring of one of those facts, so no number or claim is added here.

Layout: paper background, ink type, the site's yellow accent and a dark key block
(public-desk tokens, CC-114). The name of the release or event is large, its key date,
figure or decision is the largest element, the facts fill the remaining space, and
the footer carries the source and the card's own date. Font sizes are fitted to the
content so no large area stays empty.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Sequence

# Public-desk tokens (ui/src/product/public-desk/public-desk.css, CC-114).
PAPER = "#F5F5F2"
SURFACE = "#EBEBE6"
RULE = "#D6D6CF"
INK = "#111111"
MUTED = "#55554F"
YELLOW = "#FDCF09"
FIELD = "#111111"
ON_FIELD = "#F5F5F2"
ON_FIELD_MUTED = "#A3A39C"

DESIGN = "CC245_SITE_FACT_CARD_V1"
X_SIZE = (1600, 900)          # X, Facebook, LinkedIn, Telegram, Discord, YouTube, Substack
INSTAGRAM_SIZE = (1080, 1350)  # Instagram portrait feed size

_FONT_CANDIDATES = {
    "black": ("seguibl.ttf", "segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
    "bold": ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
    "semibold": ("seguisb.ttf", "segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
    "regular": ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"),
}


@dataclass(frozen=True)
class CardSpec:
    """Everything the card shows; every string is drawn exactly as given."""
    title: str
    facts: Sequence[tuple[str, str]] = ()
    kicker: str = ""
    key_label: str = ""
    key_value: str = ""
    source_line: str = ""
    dated_line: str = ""
    notice: str = "Analysis, not financial advice."
    extra: dict = field(default_factory=dict)


def card_date(now: datetime | None = None) -> str:
    """The card's own date, in New York like the site's public times (reader policy)."""
    now = now or datetime.now(timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        local = now.astimezone(ZoneInfo("America/New_York"))
    except Exception:  # tz database missing: UTC date is still a true date
        local = now.astimezone(timezone.utc)
    return f"{local:%B} {local.day}, {local.year}"


def reader_date(value: str | None) -> str:
    """'2026-10-19T00:00:00Z' -> 'October 19, 2026'; other text is kept as given."""
    text = str(value or "").strip()
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", text)
    if not match:
        return text
    parsed = datetime(int(match[1]), int(match[2]), int(match[3]))
    return f"{parsed:%B} {parsed.day}, {parsed.year}"


_KEY_FIGURE = re.compile(
    r"(?<![\w.])[-+−]?\$?\d[\d,]*(?:\.\d+)?\s?(?:%|percent(?:age points?)?|pp|bp|basis points|"
    r"points?|million|billion|trillion)(?![\w])", re.I)
_DATE = re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|"
                   r"November|December) \d{1,2}, \d{4}\b")


def piece_dated_line(article) -> str:
    """The piece's own date from its reader date line, e.g. 'Capital Chronicle · November 3, 2026'.

    Taken from the article record, so the same article always renders the same card.
    """
    match = _DATE.search(str((article or {}).get("display_date") or ""))
    return "Capital Chronicle · " + match.group(0) if match else "Capital Chronicle"


def key_from_facts(facts: Sequence[tuple[str, str]]) -> tuple[str, str]:
    """Pick the card's key value as an exact substring of an admitted fact.

    A labelled date row (an event's scheduled date) wins; otherwise the first figure
    with a unit; otherwise the first full date. Returns ("", "") when none exists.
    """
    for label, value in facts:
        if "date" in label.casefold() and _DATE.search(value):
            return label, _DATE.search(value).group(0)
    for label, value in facts:
        match = _KEY_FIGURE.search(value)
        if match:
            return ("Key figure" if label in {"Reported fact", "What happened"} else label), match.group(0).strip()
    for label, value in facts:
        match = _DATE.search(value)
        if match:
            return label, match.group(0)
    return "", ""


def _font(weight: str, size: int):
    from PIL import ImageFont
    for name in _FONT_CANDIDATES[weight]:
        for candidate in (name, str(Path(r"C:\Windows\Fonts") / name), _matplotlib_font(name)):
            if not candidate:
                continue
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _matplotlib_font(name: str) -> str | None:
    if not name.startswith("DejaVu"):
        return None
    try:
        import matplotlib
        return str(Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf" / name)
    except Exception:
        return None


def _wrap(draw, text: str, font, width: int) -> list[str]:
    words, lines, current = str(text or "").split(), [], ""
    for word in words:
        candidate = (current + " " + word).strip()
        if current and draw.textlength(candidate, font=font) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _fit(draw, text: str, weight: str, width: int, height: int, *, start: int, floor: int,
         max_lines: int, leading: float = 1.12):
    """Largest font size whose wrapped text fits the box; never truncates silently."""
    for size in range(start, floor - 1, -2):
        font = _font(weight, size)
        lines = _wrap(draw, text, font, width)
        if (len(lines) <= max_lines and len(lines) * size * leading <= height
                and all(draw.textlength(line, font=font) <= width for line in lines)):
            return font, lines, size
    # Never block a post over layout: keep what fits and mark the cut (CC-186 point 3).
    font = _font(weight, floor)
    lines = _wrap(draw, text, font, width)
    fit = max(1, min(max_lines, int(height // (floor * leading)) or 1))
    if len(lines) > fit:
        lines = lines[:fit]
        while lines[-1] and draw.textlength(lines[-1] + "…", font=font) > width:
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1].rstrip() + "…"
    return font, lines, floor


def _fit_facts(draw, facts, width: int, height: int, *, start: int, floor: int):
    """One size for every fact so the list reads as a set and fills its column."""
    for size in range(start, floor - 1, -2):
        label_size = max(16, int(size * 0.58))
        value_font, label_font = _font("semibold", size), _font("bold", label_size)
        blocks = [(label, _wrap(draw, value, value_font, width)) for label, value in facts]
        needed = sum((label_size * 1.5 if label else 0) + len(lines) * size * 1.18 + size * 0.75
                     for label, lines in blocks)
        if needed <= height:
            return value_font, label_font, size, label_size, blocks, needed
    # At the smallest size, show the leading facts that fit; never block the post.
    size = floor
    label_size = max(16, int(size * 0.58))
    value_font, label_font = _font("semibold", size), _font("bold", label_size)
    blocks, needed = [], 0.0
    for label, value in facts:
        lines = _wrap(draw, value, value_font, width)
        block = (label_size * 1.5 if label else 0) + len(lines) * size * 1.18 + size * 0.75
        if blocks and needed + block > height:
            break
        blocks.append((label, lines))
        needed += block
    return value_font, label_font, size, label_size, blocks, needed


def render_fact_card(path: str | Path, spec: CardSpec, *, size: tuple[int, int] = X_SIZE) -> dict:
    """Render ``spec`` at ``size``; returns the layout facts tests and reviewers check."""
    from PIL import Image, ImageDraw

    if not spec.title.strip():
        raise ValueError("FACT_CARD_TITLE_REQUIRED")
    if spec.key_value and not any(spec.key_value in value for _, value in spec.facts) \
            and spec.key_value not in spec.title:
        raise ValueError("FACT_CARD_KEY_VALUE_MUST_BE_ADMITTED_TEXT")
    width, height = size
    portrait = height > width
    scale = width / 1600 if not portrait else width / 1080
    margin = int(64 * scale) if not portrait else 64
    image = Image.new("RGB", size, PAPER)
    draw = ImageDraw.Draw(image)

    # Masthead: brand at left with the site's yellow marker, kicker at right.
    brand_font = _font("black", int(30 * (scale if not portrait else 1.0)))
    marker = int(22 * (scale if not portrait else 1.0))
    top = margin
    draw.rectangle((margin, top + 6, margin + marker, top + 6 + marker), fill=YELLOW)
    draw.text((margin + marker + 14, top), "CAPITAL CHRONICLE", font=brand_font, fill=INK)
    if spec.kicker:
        kicker_font = _font("bold", int(22 * (scale if not portrait else 1.0)))
        kicker = spec.kicker.upper()
        while draw.textlength(kicker, font=kicker_font) > width * 0.55 and " " in kicker:
            kicker = kicker.rsplit(" ", 1)[0]
        draw.text((width - margin - draw.textlength(kicker, font=kicker_font), top + 6), kicker,
                  font=kicker_font, fill=MUTED)
    rule_y = top + int(52 * (scale if not portrait else 1.0))
    draw.line((margin, rule_y, width - margin, rule_y), fill=INK, width=3)

    # Footer: the full source line, then the card's own date and the notice.
    unit = scale if not portrait else 1.0
    small = _font("regular", int(22 * unit))
    small_bold = _font("bold", int(22 * unit))
    source_lines = _wrap(draw, spec.source_line, small_bold, width - 2 * margin)[:2] if spec.source_line else []
    footer_h = int((14 + 32 * (len(source_lines) + 1) + 8) * unit)
    footer_top = height - margin - footer_h
    draw.line((margin, footer_top, width - margin, footer_top), fill=RULE, width=2)
    fy = footer_top + int(14 * unit)
    for line in source_lines:
        draw.text((margin, fy), line, font=small_bold, fill=INK)
        fy += int(32 * unit)
    if spec.dated_line:
        draw.text((margin, fy), spec.dated_line, font=small, fill=MUTED)
    if spec.notice:
        draw.text((width - margin - draw.textlength(spec.notice, font=small), fy), spec.notice,
                  font=small, fill=MUTED)

    # Title: the release or event name, large; alone, it fills the whole body.
    body_top = rule_y + int(34 * unit)
    title_w = width - 2 * margin
    facts = [(label, value) for label, value in spec.facts if value and value != spec.key_value]
    available_bottom = footer_top - int(28 * unit)
    if spec.key_value or facts:
        title_font, title_lines, title_size = _fit(draw, spec.title, "bold", title_w, int(height * 0.24),
            start=int(78 * scale) if not portrait else 80, floor=int(40 * scale) if not portrait else 44, max_lines=3)
    else:
        title_font, title_lines, title_size = _fit(draw, spec.title, "black", title_w,
            available_bottom - body_top, start=int(150 * scale) if not portrait else 140,
            floor=int(48 * scale) if not portrait else 52, max_lines=8, leading=1.1)
    y = body_top
    if not (spec.key_value or facts):
        # Alone, the title block sits in the middle of the body, not against the top.
        y += max(0, int((available_bottom - body_top - len(title_lines) * title_size * 1.12) / 2))
    for line in title_lines:
        draw.text((margin, y), line, font=title_font, fill=INK)
        y += int(title_size * 1.12)
    y += int(24 * unit)
    key_box = None
    if spec.key_value:
        if portrait:
            box = (margin, y, width - margin, y + int((available_bottom - y) * (0.42 if facts else 1.0)))
        else:
            box = (margin, y, margin + int((width - 2 * margin) * (0.40 if facts else 1.0)), available_bottom)
        draw.rectangle(box, fill=FIELD)
        draw.rectangle((box[0], box[1], box[0] + int(12 * (scale if not portrait else 1.0)), box[3]), fill=YELLOW)
        pad = int(36 * (scale if not portrait else 1.0))
        label_font = _font("bold", int(24 * (scale if not portrait else 1.0)))
        inner_w = box[2] - box[0] - 2 * pad
        if spec.key_label:
            draw.text((box[0] + pad, box[1] + pad), spec.key_label.upper(), font=label_font, fill=YELLOW)
        label_h = int(24 * (scale if not portrait else 1.0)) + 18 if spec.key_label else 0
        key_font, key_lines, key_size = _fit(draw, spec.key_value, "black", inner_w,
            box[3] - box[1] - 2 * pad - label_h, start=int(150 * scale) if not portrait else 150,
            floor=int(44 * scale) if not portrait else 48, max_lines=3, leading=1.05)
        key_y = box[1] + pad + label_h + max(0, ((box[3] - box[1] - 2 * pad - label_h)
                                                 - len(key_lines) * key_size * 1.05) / 2)
        for line in key_lines:
            draw.text((box[0] + pad, key_y), line, font=key_font, fill=ON_FIELD)
            key_y += key_size * 1.05
        key_box = box
        if portrait:
            y = box[3] + int(30 * (scale if not portrait else 1.0))

    fill_ratio = None
    if facts:
        if key_box and not portrait:
            fx, fw = key_box[2] + int(44 * scale), width - margin - (key_box[2] + int(44 * scale))
        else:
            fx, fw = margin, width - 2 * margin
        fh = available_bottom - y
        value_font, label_font, value_size, label_size, blocks, needed = _fit_facts(
            draw, facts, fw, fh, start=int(46 * scale) if not portrait else 56, floor=16)
        fy = y + max(0, (fh - needed) / 2) if key_box and not portrait else y
        for label, lines in blocks:
            if label:
                draw.text((fx, fy), label.upper(), font=label_font, fill=MUTED)
                fy += label_size * 1.5
            for line in lines:
                draw.text((fx, fy), line, font=value_font, fill=INK)
                fy += value_size * 1.18
            fy += value_size * 0.35
            draw.line((fx, fy, fx + fw, fy), fill=RULE, width=2)
            fy += value_size * 0.40
        fill_ratio = round(needed / max(1, fh), 3)

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)
    return {"size": list(size), "title_size": title_size, "key_box": list(key_box) if key_box else None,
            "facts_shown": len(blocks) if facts else 0, "facts_given": len(facts),
            "facts_fill_ratio": fill_ratio, "design": DESIGN}
