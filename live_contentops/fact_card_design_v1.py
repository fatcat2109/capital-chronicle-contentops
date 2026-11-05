"""CC-245, redesigned in CC-290: fact cards in the site's design language.

One deterministic renderer for every typographic card (source facts, post facts,
delivery, digest and title cards). It draws only the text it is given: callers pass
verbatim admitted facts and their attribution, and the key value must be an exact
substring of one of those facts (or of the title), so no number or claim is added here.

CC-290 (Jim, 5 Nov: the black block drew too much attention and the edges did not
line up) keeps that content binding and changes the layout and the hero choice:

- One grid. Every block starts on the same left edge (large type is set by its ink,
  not its pen position) and ends inside the same right edge; the X-size card adds one
  column line. Vertical gaps are multiples of one unit and grow together.
- Hierarchy: the title, then the key figure, then the facts, then the source footer.
- The hero is ink on paper under a short yellow accent, never a dark slab: the first
  fact "promoted", with its label, the figure large and the fact's own sentence.
- A figure beats a date: a date key that is not still ahead of the piece's own date
  gives way to the first admitted figure with a unit, quoted exactly from its fact.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from functools import lru_cache
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

DESIGN = "CC290_SITE_FACT_CARD_V2"
X_SIZE = (1600, 900)          # X, Facebook, LinkedIn, Telegram, Discord, YouTube, Substack
INSTAGRAM_SIZE = (1080, 1350)  # Instagram portrait feed size

_FONT_CANDIDATES = {
    "black": ("seguibl.ttf", "segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
    "bold": ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
    "semibold": ("seguisb.ttf", "segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
    "regular": ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"),
}

# The grid: MARGIN is the one left and right edge, UNIT the spacing step, GUTTER the
# space between the X-size card's two columns.
MARGIN = 64
UNIT = 8
GUTTER = 48

# Type scale per format, (largest, smallest). Title, key figure and fact text step down
# together, so their proportions hold on every card; the step chosen is the largest whose
# body fills at most _FILL_TARGET of the space, and the body's gaps then grow together
# (up to _GAP_GROWTH) to take the rest. A sparse card still left short is centred.
_SCALE = {
    "portrait": {"title": (120, 52), "figure": (176, 72), "fact": (56, 28)},
    "landscape": {"title": (100, 46), "figure": (150, 60), "fact": (48, 22)},
}
_LEVELS = 28
_FILL_TARGET = 0.88
_GAP_GROWTH = 2.0
_FIGURE_OVER_TITLE = 1.3       # the key figure is never more than 1.3x the title
_DATE_OVER_FACT = 1.3          # a date or text key reads as an emphasised row, not a poster
_FACT_UNDER_TITLE = 0.6        # fact text stays at most 0.6x the title, so the title leads
_FACT_FLOOR = 16               # below the scale, facts shrink to this before rows are cut
_TITLE_LINES = {"portrait": 3, "landscape": 2}
_TITLE_FLOOR = {"portrait": 40, "landscape": 36}
_TITLE_ONLY = {"portrait": (196, 64), "landscape": (176, 60)}   # a card with no fact: the title is the body


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
    image_path: str = ""   # an admitted chart image (e.g. a CC-144 series mini chart)
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
_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
_DATE = re.compile(r"\b(?:" + _MONTHS + r") \d{1,2}, \d{4}\b")
# A key that only names a period: "June 30, 2025", "June 2025", "Q2 2025" or "2025".
_PERIOD = re.compile(r"(?:(?:" + _MONTHS + r")(?: \d{1,2},)? \d{4}|Q[1-4] \d{4}|\d{4})")
_SCHEDULED = re.compile(r"\b(?:scheduled|next|upcoming|due)\b", re.I)
_GENERIC_LABELS = {"", "reported fact", "what happened", "key figure"}


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
    The renderer's ``hero_for`` then lets a figure replace a date that is not ahead.
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


def _period_start(value: str) -> date | None:
    """The first day a period key covers ('Q2 2025' -> April 1, 2025), or None."""
    text = value.strip()
    try:
        match = re.fullmatch(r"(" + _MONTHS + r")(?: (\d{1,2}),)? (\d{4})", text)
        if match:
            month = _MONTHS.split("|").index(match[1]) + 1
            return date(int(match[3]), month, int(match[2] or 1))
        match = re.fullmatch(r"Q([1-4]) (\d{4})", text)
        if match:
            return date(int(match[2]), int(match[1]) * 3 - 2, 1)
        if re.fullmatch(r"\d{4}", text):
            return date(int(text), 1, 1)
    except ValueError:      # not a real calendar day ("February 30, 2026")
        return None
    return None


def hero_for(spec: CardSpec) -> tuple[str, str]:
    """The card's hero (label, value): the caller's key, except that a figure beats a date.

    A key that only names a date or period gives way to the first admitted figure with
    a unit, quoted exactly from a labelled fact, unless the period is still ahead: it
    starts after the piece's own date, or its label says scheduled, next, upcoming or
    due. Unlabelled rows are list items (a digest's titles), never a figure's source.
    """
    label, value = spec.key_label, spec.key_value
    if not value or not _PERIOD.fullmatch(value.strip()) or _SCHEDULED.search(label or ""):
        return label, value
    starts = _period_start(value)
    piece = _DATE.search(spec.dated_line or "")
    if starts is not None and piece is not None and starts > _period_start(piece.group(0)):
        return label, value
    for fact_label, text in spec.facts:
        if not str(fact_label or "").strip():
            continue
        match = _KEY_FIGURE.search(str(text or ""))
        if match:
            shown = "Key figure" if fact_label.strip().casefold() in _GENERIC_LABELS else fact_label
            return shown, match.group(0).strip()
    return label, value


def _is_figure(value: str) -> bool:
    """A number with or without its unit ("0.6%", "$40 million", "52.4"), not a date or phrase."""
    text = value.strip()
    return (len(text) <= 16 and any(ch.isdigit() for ch in text) and not _PERIOD.fullmatch(text)
            and not re.search(r"[A-Za-z]{3,}", _KEY_FIGURE.sub("", text)))


# ---- type ------------------------------------------------------------------------

@lru_cache(maxsize=512)
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


@lru_cache(maxsize=1)
def _measure():
    from PIL import Image, ImageDraw
    return ImageDraw.Draw(Image.new("RGB", (1, 1)))


@lru_cache(maxsize=65536)
def _bbox(text: str, weight: str, size: int) -> tuple[int, int, int, int]:
    """Layout box of ``text`` from its left baseline origin: the pen start to the advance."""
    return _measure().textbbox((0, 0), text, font=_font(weight, size), anchor="ls")


@lru_cache(maxsize=4096)
def _ink(text: str, weight: str, size: int) -> tuple[int, int]:
    """Where the ink of ``text`` starts and ends, from its pen origin, measured above the
    baseline: a glyph's side bearing can be a tenth of the size ('1' in a 128px figure
    starts 13px in), and a descender's hook ('j') must not push a line off the edge."""
    from PIL import Image, ImageDraw
    left, top, right, _ = _bbox(text, weight, size)
    pad = size
    canvas = Image.new("L", (max(1, right - left + 2 * pad), max(1, pad - top)))
    ImageDraw.Draw(canvas).text((pad, canvas.height), text, font=_font(weight, size), fill=255, anchor="ls")
    box = canvas.getbbox()
    return (box[0] - pad, box[2] - pad) if box else (0, 0)


def _ink_width(text: str, weight: str, size: int) -> int:
    """The width a line needs: its advance, which always contains its ink."""
    left, _, right, _ = _bbox(text, weight, size)
    return right - left


def _cap(weight: str, size: int) -> int:
    """Baseline to the top of a capital: the visual top of a line of type."""
    return -_bbox("H", weight, size)[1]


def _greedy(text: str, weight: str, size: int, width: int) -> tuple[str, ...]:
    words, lines, current = str(text or "").split(), [], ""
    for word in words:
        candidate = (current + " " + word).strip()
        if current and _ink_width(candidate, weight, size) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return tuple(lines)


@lru_cache(maxsize=8192)
def _wrap(text: str, weight: str, size: int, width: int, balance: bool = False) -> tuple[str, ...]:
    """Greedy lines; ``balance`` evens a title's lines (breaking after its colon when that
    costs no extra line), and a body text never ends on one lone word if avoidable."""
    lines = _greedy(text, weight, size, width)
    if len(lines) < 2:
        return lines
    if balance:
        head, colon, tail = text.partition(": ")
        if colon and tail:
            split = _wrap(head + ":", weight, size, width, True) + _wrap(tail, weight, size, width, True)
            if len(split) <= len(lines):
                return split
        low, high, best = width // 3, width, lines
        while low < high:
            middle = (low + high) // 2
            trial = _greedy(text, weight, size, middle)
            if len(trial) <= len(lines):
                best, high = trial, middle
            else:
                low = middle + 1
        return best
    if len(lines[-1].split()) == 1 and len(lines[-2].split()) > 2:
        for step in range(1, 7):
            trial = _greedy(text, weight, size, int(width * (1 - 0.03 * step)))
            if len(trial) == len(lines) and len(trial[-1].split()) > 1:
                return trial
    return lines


def _clip(lines: Sequence[str], weight: str, size: int, width: int, count: int) -> list[str]:
    """Keep ``count`` lines and mark the cut; used only when nothing smaller fits."""
    kept = list(lines[:max(1, count)])
    if len(kept) < len(lines):
        last = kept[-1]
        while " " in last and _ink_width(last + "…", weight, size) > width:
            last = last.rsplit(" ", 1)[0]
        while last and _ink_width(last + "…", weight, size) > width:
            last = last[:-1]
        kept[-1] = last.rstrip(" ,;:") + "…"
    return kept


def _clean_break(title: str, lines: Sequence[str]) -> bool:
    """A title with a colon reads best broken right after it, on a line of two or more words."""
    if ": " not in title or len(lines) < 2:
        return True
    head_words = len(title.partition(": ")[0].split())
    return any(line.endswith(":") and (len(line.split()) > 1 or head_words == 1) for line in lines[:-1])


@dataclass
class _Text:
    name: str
    lines: list
    weight: str
    size: int
    pitch: float
    color: str

    @property
    def cap(self) -> int:
        return _cap(self.weight, self.size)

    @property
    def height(self) -> float:
        """Cap top of the first line to the baseline of the last."""
        return self.cap + (len(self.lines) - 1) * self.pitch if self.lines else 0.0


def _text(name, text, weight, size, width, color, *, leading, balance=False, upper=False) -> _Text:
    shown = str(text or "").upper() if upper else str(text or "")
    return _Text(name, list(_wrap(shown, weight, size, width, balance)), weight, size, size * leading, color)


def _set(draw, x: float, baseline: float, text: str, weight: str, size: int, color: str, *, align="left") -> int:
    """Set ``text`` so that its ink, not its pen position, starts at ``x`` (or ends just
    before ``x`` when right-aligned). Returns where the ink ends."""
    left, right = _ink(text, weight, size)
    origin = round(x - left if align == "left" else x - right)
    draw.text((origin, round(baseline)), text, font=_font(weight, size), fill=color, anchor="ls")
    return origin + right


# ---- the body --------------------------------------------------------------------

@dataclass
class _Row:
    label: str
    value: str


@dataclass
class _Plan:
    """One column, as ops: ("text", _Text) | ("gap", px, grows) | ("rule", px, color, length)."""
    ops: list
    rows_shown: int = 0

    def height(self, grow: float = 1.0) -> float:
        total = 0.0
        for op in self.ops:
            if op[0] == "text":
                total += op[1].height
            elif op[0] == "gap":
                total += op[1] * (grow if op[2] else 1.0)
            else:
                total += op[1]
        return total


def _column(width, *, hero, rows, fact, figure, accent=True, offset=False) -> _Plan:
    """The yellow accent, then the hero (label, figure, sentence), then the rows.

    ``offset`` starts a column without the accent at the same height as one with it, so
    the first labels of the two columns share one cap line.
    """
    label_size = min(24, max(18, round(fact * 0.52)))
    ops, shown = [], 0
    if accent:
        ops += [("rule", UNIT, YELLOW, min(width, 12 * UNIT)), ("gap", 3 * UNIT, True)]
    elif offset:
        ops += [("gap", UNIT, False), ("gap", 3 * UNIT, True)]
    if hero:
        label, value, sentence = hero
        if label:
            ops += [("text", _text("hero_label", label, "bold", label_size, width, MUTED, leading=1.2, upper=True)),
                    ("gap", UNIT * max(2, round(figure / 48)), True)]
        lines = ([value] if _ink_width(value, "bold", figure) <= width
                 else list(_wrap(value, "bold", figure, width, True)))
        ops.append(("text", _Text("hero_value", lines, "bold", figure, figure * 1.04, INK)))
        if sentence:
            ops += [("gap", UNIT * max(3, round(figure / 32)), True),
                    ("text", _text("hero_fact", sentence, "semibold", fact, width, INK, leading=1.24))]
            shown += 1
    for index, row in enumerate(rows):
        if index or hero:
            ops += [("gap", 2.5 * UNIT, True), ("rule", 2, RULE, width), ("gap", 2.5 * UNIT, True)]
        if row.label:
            ops += [("text", _text("fact_label", row.label, "bold", label_size, width, MUTED, leading=1.2,
                                   upper=True)), ("gap", 1.5 * UNIT, True)]
        ops.append(("text", _text("fact", row.value, "semibold", fact, width, INK, leading=1.24)))
        shown += 1
    return _Plan(ops, shown)


def _draw_column(draw, plan: _Plan, x: int, top: float, grow: float, blocks: list) -> float:
    y = top
    for op in plan.ops:
        if op[0] == "gap":
            y += op[1] * (grow if op[2] else 1.0)
        elif op[0] == "rule":
            _, thickness, color, length = op
            draw.rectangle((x, round(y), x + length - 1, round(y) + thickness - 1), fill=color)
            blocks.append({"name": "accent" if color == YELLOW else "rule",
                           "box": [x, round(y), x + length, round(y) + thickness]})
            y += thickness
        else:
            block = op[1]
            baseline, right = y + block.cap, x
            for line in block.lines:
                right = max(right, _set(draw, x, baseline, line, block.weight, block.size, block.color))
                baseline += block.pitch
            blocks.append({"name": block.name, "box": [x, round(y), right, round(y + block.height)],
                           "baseline": round(y + block.cap)})
            y += block.height
    return y


class _Body:
    """Lays out the body: one step of the type scale for every block, one gap factor."""

    def __init__(self, spec, fmt, content, columns, hero, rows, chart, available):
        self.spec, self.fmt, self.content, self.columns = spec, fmt, content, columns
        self.hero, self.rows, self.chart, self.available = hero, rows, chart, available
        self.scale = _SCALE[fmt]

    def levels(self):
        for level in range(_LEVELS + 1):
            t = level / _LEVELS
            yield {name: int(round((high - (high - low) * t) / 2) * 2) for name, (high, low) in self.scale.items()}

    def title(self, size) -> _Text:
        """The largest title up to ``size`` within the format's line count; one more line
        is allowed only below the scale, and a cut only beyond that. A title with a colon
        may go up to a fifth smaller to break after the colon rather than mid-phrase."""
        lines, scale_low = _TITLE_LINES[self.fmt], self.scale["title"][1]
        first = None
        for step in range(size, _TITLE_FLOOR[self.fmt] - 1, -2):
            block = _text("title", self.spec.title, "bold", step, self.content, INK, leading=1.06, balance=True)
            if (len(block.lines) > lines + (1 if step <= scale_low else 0)
                    or max(_ink_width(line, "bold", step) for line in block.lines) > self.content):
                continue
            if first and (step < first.size * 0.8 or len(block.lines) > len(first.lines)):
                return first
            if _clean_break(self.spec.title, block.lines):
                return block
            first = first or block
        if first:
            return first
        block.lines = _clip(block.lines, "bold", block.size, self.content, lines + 1)
        return block

    def figure(self, figure, fact, title, width) -> int:
        """The key figure's size: the step's, at most _FIGURE_OVER_TITLE x the title; a date or
        text key at _DATE_OVER_FACT x the facts; smaller only if wider than its column."""
        hero = self.hero
        if not hero:
            return figure
        size = min(figure, int(title.size * _FIGURE_OVER_TITLE) // 2 * 2)
        if not _is_figure(hero[1]):
            size = int(round(fact * _DATE_OVER_FACT / 2)) * 2
        while size > fact and _ink_width(hero[1], "bold", size) > width:
            size -= 2
        return max(size, fact)

    def plan(self, sizes, *, rows=None, title=None):
        """Lay out the body at one step; returns the sizes used, the title and the columns."""
        rows = self.rows if rows is None else rows
        title = title or self.title(sizes["title"])
        cap = max(self.scale["fact"][1], int(title.size * _FACT_UNDER_TITLE) // 2 * 2)
        fact = min(sizes["fact"], cap)
        width = self.columns[0] if self.columns else self.content
        figure = self.figure(sizes["figure"], fact, title, width)
        used = {"title": title.size, "figure": figure if self.hero else 0, "fact": fact}
        if not self.columns or self.chart:
            return used, title, _column(width, hero=self.hero, rows=rows, fact=fact, figure=figure), None
        # Two columns: the hero heads the left one; the rows flow in reading order, as
        # many under the hero as keeps the taller column shortest.
        left_w, _, right_w = self.columns
        best = None
        for split in range(0 if self.hero else 1, len(rows) + 1):
            main = _column(left_w, hero=self.hero, rows=rows[:split], fact=fact, figure=figure)
            side = _column(right_w, hero=None, rows=rows[split:], fact=fact, figure=figure, accent=False,
                           offset=True) if rows[split:] else None
            tallest = max(main.height(), side.height() if side else 0.0)
            if best is None or tallest < best[0] - 0.5:
                best = (tallest, main, side)
        return used, title, best[1], best[2]

    def needed(self, title, main, side, grow=1.0) -> float:
        tallest = max(main.height(grow), side.height(grow) if side else 0.0)
        chart = self.available * 0.45 if (self.chart and not self.columns) else 0.0
        return title.height + 5 * UNIT * grow + tallest + chart

    def fit(self):
        fallback = None
        for sizes in self.levels():
            used, *planned = self.plan(sizes)
            needed = self.needed(*planned)
            if needed <= self.available * _FILL_TARGET:
                return (used, *planned)
            if fallback is None and needed <= self.available:
                fallback = (used, *planned)
        return fallback or self.overflow()

    def overflow(self):
        """Nothing on the scale fits: the smallest title and figure, facts down to the floor,
        then the last rows are left out, then the last lines (marked with an ellipsis)."""
        low = {name: pair[1] for name, pair in self.scale.items()}
        title = self.title(low["title"])
        for fact in range(low["fact"], _FACT_FLOOR - 1, -2):
            used, *planned = self.plan({**low, "fact": fact}, title=title)
            if self.needed(*planned) <= self.available:
                return (used, *planned)
        sizes = {**low, "fact": _FACT_FLOOR}
        for count in range(len(self.rows) - 1, 0, -1):
            used, *planned = self.plan(sizes, rows=self.rows[:count], title=title)
            if self.needed(*planned) <= self.available:
                return (used, *planned)
        used, title, main, side = self.plan(sizes, rows=self.rows[:1], title=title)
        room = self.available - title.height - 5 * UNIT
        for plan, width in ((main, self.columns[0] if self.columns else self.content),
                            (side, self.columns[2] if self.columns else self.content)):
            texts = [op[1] for op in plan.ops if op[0] == "text"] if plan else []
            while texts and plan.height() > room and len(texts[-1].lines) > 1:
                block = texts[-1]
                block.lines = _clip(block.lines, block.weight, block.size, width, len(block.lines) - 1)
        return used, title, main, side

    def grow(self, title, main, side) -> float:
        """One factor for every body gap, at most _GAP_GROWTH, so the body reaches the footer."""
        if self.chart or self.needed(title, main, side) >= self.available:
            return 1.0
        low, high = 1.0, _GAP_GROWTH
        for _ in range(20):
            middle = (low + high) / 2
            if self.needed(title, main, side, middle) <= self.available:
                low = middle
            else:
                high = middle
        return low


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
    fmt = "portrait" if portrait else "landscape"
    left, right = MARGIN, width - MARGIN
    content = right - left
    image = Image.new("RGB", size, PAPER)
    draw = ImageDraw.Draw(image)
    blocks: list = []

    # Masthead: the yellow square (as tall as the wordmark's capitals) and the wordmark on
    # the left edge, the kicker on the right edge, one baseline; an ink rule below.
    brand_cap = _cap("black", 30)
    baseline = MARGIN + brand_cap
    draw.rectangle((left, MARGIN, left + brand_cap - 1, baseline - 1), fill=YELLOW)
    wordmark_x = left + brand_cap + 12
    wordmark_right = _set(draw, wordmark_x, baseline, "CAPITAL CHRONICLE", "black", 30, INK)
    if spec.kicker:
        kicker = spec.kicker.upper()
        while _ink_width(kicker, "bold", 22) > right - wordmark_right - 4 * UNIT and " " in kicker:
            kicker = kicker.rsplit(" ", 1)[0]
        _set(draw, right, baseline, kicker, "bold", 22, MUTED, align="right")
    rule_top = baseline + 3 * UNIT
    draw.rectangle((left, rule_top, right - 1, rule_top + 2), fill=INK)
    blocks.append({"name": "masthead", "box": [left, MARGIN, right, rule_top + 3]})
    body_top = rule_top + 3 + 5 * UNIT

    # Footer, on the bottom margin: the full source line, then the card's own date and the
    # notice; an ink rule above it closes the body.
    source_lines = list(_wrap(spec.source_line, "bold", 22, content))[:2] if spec.source_line else []
    pitch, last_baseline = 30, height - MARGIN
    first_baseline = last_baseline - pitch * len(source_lines)
    footer_rule = round(first_baseline - _cap("regular", 22) - 2.5 * UNIT - 2)
    draw.rectangle((left, footer_rule, right - 1, footer_rule + 1), fill=INK)
    for index, line in enumerate(source_lines):
        _set(draw, left, first_baseline + index * pitch, line, "bold", 22, INK)
    if spec.dated_line:
        _set(draw, left, last_baseline, spec.dated_line, "regular", 22, MUTED)
    if spec.notice:
        _set(draw, right, last_baseline, spec.notice, "regular", 22, MUTED, align="right")
    blocks.append({"name": "footer", "box": [left, footer_rule, right, last_baseline]})
    body_bottom = footer_rule - 5 * UNIT

    # What the body shows: the hero (a figure beats a past date) and the remaining rows.
    hero_label, hero_value = hero_for(spec)
    rows, sentence = [], ""
    for label, value in ((str(label or ""), str(value or "")) for label, value in spec.facts):
        if not value or (hero_value and value == hero_value):
            continue                                  # empty, or the hero is this whole row
        if hero_value and not sentence and hero_value in value:
            sentence = value                          # the hero's own sentence
            continue
        rows.append(_Row(label.strip(), value))
    facts_given = (1 if sentence else 0) + len(rows)
    hero = (hero_label.strip(), hero_value, sentence) if hero_value else None
    chart = spec.image_path or ""
    if not hero and not rows and not chart:
        return _title_only(image, spec, path, size, left, content, body_top, body_bottom, blocks)

    # The X-size card has two columns (five twelfths, then seven) when there is more
    # than one thing to show; portrait is always one column.
    columns = None
    if not portrait and (chart or (1 if hero else 0) + len(rows) > 1):
        left_w = round((content - GUTTER) * 5 / 12)
        columns = (left_w, left + left_w + GUTTER, right - (left + left_w + GUTTER))
    available = body_bottom - body_top
    body = _Body(spec, fmt, content, columns, hero, rows, chart, available)
    sizes, title, main, side = body.fit()
    grow = body.grow(title, main, side)
    spare = available - body.needed(title, main, side, grow)
    y = body_top + (round(spare * 0.45) if spare > 4 * UNIT and not chart else 0)

    # Draw: the title on the body's first line, then the columns from one shared top.
    title_top, baseline, title_right = y, y + title.cap, left
    for line in title.lines:
        title_right = max(title_right, _set(draw, left, baseline, line, "bold", title.size, INK))
        baseline += title.pitch
    blocks.append({"name": "title", "box": [left, round(title_top), title_right, round(title_top + title.height)],
                   "baseline": round(title_top + title.cap)})
    y += title.height + 5 * UNIT * grow
    body_start = y
    if columns:
        end = _draw_column(draw, main, left, y, grow, blocks)
        if side:
            end = max(end, _draw_column(draw, side, columns[1], y, grow, blocks))
        if chart:
            _paste_chart(image, chart, (columns[1], round(body_start), right, round(body_bottom)), blocks)
            end = body_bottom
    else:
        end = _draw_column(draw, main, left, y, grow, blocks)
        if chart:
            _paste_chart(image, chart, (left, round(end + 4 * UNIT), right, round(body_bottom)), blocks)
            end = body_bottom
    hero_parts = [b["box"] for b in blocks if b["name"] in {"accent", "hero_label", "hero_value", "hero_fact"}]
    hero_box = ([min(b[0] for b in hero_parts), min(b[1] for b in hero_parts),
                 max(b[2] for b in hero_parts), max(b[3] for b in hero_parts)] if hero and hero_parts else None)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)
    return {"size": list(size), "title_size": title.size, "key_box": hero_box,
            "hero": [hero[0], hero[1]] if hero else None, "figure_size": sizes["figure"] if hero else None,
            "columns": [left, columns[1]] if columns else [left],
            "facts_shown": main.rows_shown + (side.rows_shown if side else 0), "facts_given": facts_given,
            "facts_size": sizes["fact"] if facts_given else None,
            "facts_fill_ratio": (round(min(1.0, (end - body_start) / max(1.0, body_bottom - body_start)), 3)
                                 if facts_given else None),
            "gap_scale": round(grow, 3), "blocks": blocks, "margin": MARGIN, "design": DESIGN}


def _paste_chart(image, chart_path, box, blocks):
    from PIL import Image as _Image
    box_w, box_h = box[2] - box[0], box[3] - box[1]
    if box_w <= 0 or box_h <= 0:
        return
    with _Image.open(chart_path) as original:
        chart = original.convert("RGB")
    chart.thumbnail((box_w, box_h), _Image.Resampling.LANCZOS)
    top = box[1] + (box_h - chart.height) // 2       # on the column's left edge, centred in its slot
    image.paste(chart, (box[0], top))
    blocks.append({"name": "chart", "box": [box[0], top, box[0] + chart.width, top + chart.height]})


def _title_only(image, spec, path, size, left, content, body_top, body_bottom, blocks):
    """CC-267: a card with no fact is its title, as large as the body allows, under the accent."""
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    available = body_bottom - body_top
    accent_h = UNIT + 4 * UNIT
    high, low = _TITLE_ONLY["portrait" if size[1] > size[0] else "landscape"]
    # Of the sizes that fit, prefer one whose title fills at least 55% of the body (no blank
    # page), then a break after the title's colon, then the fewest lines of a single word
    # (a column of single words reads as a list), then the largest.
    ranked = []
    for title_size in range(high, low - 1, -4):
        title = _text("title", spec.title, "bold", title_size, content, INK, leading=1.04, balance=True)
        if (len(title.lines) > 8 or accent_h + title.height > available * 0.85
                or max(_ink_width(line, "bold", title_size) for line in title.lines) > content):
            continue
        lone = sum(len(line.split()) == 1 for line in title.lines)
        ranked.append(((accent_h + title.height >= available * 0.55, _clean_break(spec.title, title.lines),
                        -lone, title_size), title))
    chosen = max(ranked, key=lambda item: item[0])[1] if ranked else None
    if chosen is None:
        chosen = _text("title", spec.title, "bold", low, content, INK, leading=1.04, balance=True)
        keep = max(1, int((available - accent_h - chosen.cap) // chosen.pitch) + 1)
        chosen.lines = _clip(chosen.lines, "bold", low, content, keep)
    top = body_top + max(0, (available - accent_h - chosen.height) * 0.45)   # optical centre
    draw.rectangle((left, round(top), left + 12 * UNIT - 1, round(top) + UNIT - 1), fill=YELLOW)
    blocks.append({"name": "accent", "box": [left, round(top), left + 12 * UNIT, round(top) + UNIT]})
    y = top + accent_h
    baseline, right = y + chosen.cap, left
    for line in chosen.lines:
        right = max(right, _set(draw, left, baseline, line, "bold", chosen.size, INK))
        baseline += chosen.pitch
    blocks.append({"name": "title", "box": [left, round(y), right, round(y + chosen.height)],
                   "baseline": round(y + chosen.cap)})
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)
    return {"size": list(size), "title_size": chosen.size, "key_box": None, "hero": None, "figure_size": None,
            "columns": [left], "facts_shown": 0, "facts_given": 0, "facts_size": None, "facts_fill_ratio": None,
            "gap_scale": 1.0, "blocks": blocks, "margin": MARGIN, "design": DESIGN}
