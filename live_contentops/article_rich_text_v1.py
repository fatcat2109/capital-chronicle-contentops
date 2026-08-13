"""Canonical reader-facing rich-text and source-text sanitation primitives.

The newsroom may author a small, governed Markdown subset, but destinations consume this
native block/inline representation.  Raw Markdown and source-page markup are never reader-facing
transport payloads.
"""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "contentops.article_rich_text.v1"
_VISUAL_RE = re.compile(r"\[\[VISUAL:([^\]]+)\]\]")
_HTML_TAG_RE = re.compile(r"<\s*/?\s*[A-Za-z][^>]*>")
_DOCTYPE_RE = re.compile(r"<!DOCTYPE\b", re.IGNORECASE)
_SCRIPTISH_RE = re.compile(r"<\s*(?:script|style)\b", re.IGNORECASE)
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]\n]+)\]\((https?://[^)\s]+)\)")
_STRONG_RE = re.compile(r"\*\*([^*\n]+)\*\*")
_EMPHASIS_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)(.+)$")
_HEADING_RE = re.compile(r"^(#{2,4})\s+(.+)$")
_BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "br", "div", "footer", "h1", "h2",
    "h3", "h4", "h5", "h6", "header", "li", "main", "p", "section", "table", "td",
    "th", "tr",
}
_DROP_TAGS = {
    "canvas", "form", "head", "iframe", "nav", "noscript", "script", "style", "svg",
    "template",
}


class _ReaderTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.drop_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.casefold()
        if lowered in _DROP_TAGS:
            self.drop_depth += 1
        elif self.drop_depth == 0 and lowered in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.drop_depth == 0 and tag.casefold() in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.casefold()
        if lowered in _DROP_TAGS and self.drop_depth:
            self.drop_depth -= 1
        elif self.drop_depth == 0 and lowered in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.drop_depth == 0:
            self.parts.append(data)


def sanitize_source_text(value: str, *, maximum: int | None = None) -> str:
    """Return useful human-readable text; scripts, styles, tags and page chrome are omitted."""
    raw = str(value or "")
    if _HTML_TAG_RE.search(raw) or _DOCTYPE_RE.search(raw) or _SCRIPTISH_RE.search(raw):
        parser = _ReaderTextExtractor()
        try:
            parser.feed(raw)
            parser.close()
            raw = "\n".join(parser.parts)
        except Exception:
            return ""
    raw = html.unescape(raw)
    lines = [" ".join(line.split()) for line in raw.splitlines()]
    text = "\n".join(line for line in lines if line).strip()
    # A failed extraction must not leak source markup as a reader-facing fallback.
    if _HTML_TAG_RE.search(text) or _DOCTYPE_RE.search(text) or _SCRIPTISH_RE.search(text):
        return ""
    text = re.sub(r"\n{3,}", "\n\n", text)
    if maximum is not None and len(text) > maximum:
        text = text[: max(0, maximum - 1)].rstrip() + "…"
    return text


def reader_markup_findings(markdown: str) -> list[str]:
    findings: list[str] = []
    value = str(markdown or "")
    if _DOCTYPE_RE.search(value):
        findings.append("raw_doctype")
    if _HTML_TAG_RE.search(value):
        findings.append("raw_html")
    if _SCRIPTISH_RE.search(value):
        findings.append("script_or_style_markup")
    if "```" in value or "~~~" in value:
        findings.append("code_fence")
    if re.search(r"(?m)^#\s+", value):
        findings.append("level_one_heading")
    if _VISUAL_RE.search(_VISUAL_RE.sub("", value)):
        findings.append("malformed_visual_marker")
    return list(dict.fromkeys(findings))


def _inline_nodes(value: str, *, enclosing_mark: str = "") -> list[dict[str, str]]:
    patterns = (
        ("link", _MARKDOWN_LINK_RE),
        ("strong", _STRONG_RE),
        ("emphasis", _EMPHASIS_RE),
    )
    nodes: list[dict[str, str]] = []
    cursor = 0
    while cursor < len(value):
        found: tuple[int, int, str, re.Match[str]] | None = None
        for kind, pattern in patterns:
            match = pattern.search(value, cursor)
            if match and (found is None or match.start() < found[0]):
                found = (match.start(), match.end(), kind, match)
        if found is None:
            if value[cursor:]:
                nodes.append({
                    "type": enclosing_mark or "text",
                    "text": value[cursor:],
                })
            break
        start, end, kind, match = found
        if start > cursor:
            nodes.append({
                "type": enclosing_mark or "text",
                "text": value[cursor:start],
            })
        if kind == "link":
            node = {"type": "link", "text": match.group(1), "href": match.group(2)}
            if enclosing_mark:
                node["mark"] = enclosing_mark
            nodes.append(node)
        else:
            nodes.extend(_inline_nodes(match.group(1), enclosing_mark=kind))
        cursor = end
    return nodes or [{"type": enclosing_mark or "text", "text": value}]


def markdown_to_rich_text(markdown: str) -> dict[str, Any]:
    """Parse the supported article Markdown subset into destination-neutral native semantics."""
    findings = reader_markup_findings(markdown)
    if findings:
        raise ValueError("reader_facing_markup_blocked:" + ",".join(findings))
    value = _VISUAL_RE.sub("", str(markdown or ""))
    lines = value.splitlines()
    blocks: list[dict[str, Any]] = []
    paragraph: list[str] = []
    list_items: list[list[dict[str, str]]] = []

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(part.strip() for part in paragraph if part.strip()).strip()
            if text:
                blocks.append({"type": "paragraph", "content": _inline_nodes(text)})
            paragraph.clear()

    def flush_list() -> None:
        if list_items:
            blocks.append({"type": "bullet_list", "items": list(list_items)})
            list_items.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            flush_list()
            continue
        heading = _HEADING_RE.match(stripped)
        listed = _LIST_RE.match(stripped)
        if heading:
            flush_paragraph()
            flush_list()
            blocks.append({
                "type": "heading",
                "level": len(heading.group(1)),
                "content": _inline_nodes(heading.group(2).strip()),
            })
        elif listed:
            flush_paragraph()
            list_items.append(_inline_nodes(listed.group(1).strip()))
        else:
            flush_list()
            paragraph.append(stripped)
    flush_paragraph()
    flush_list()
    return {"schema_version": SCHEMA_VERSION, "blocks": blocks}


def _inline_html(nodes: Sequence[Mapping[str, Any]]) -> str:
    result: list[str] = []
    for node in nodes:
        text = html.escape(str(node.get("text") or ""), quote=False)
        kind = str(node.get("type") or "text")
        if kind == "link":
            href = str(node.get("href") or "")
            if not re.fullmatch(r"https?://[^\s]+", href):
                raise ValueError("rich_text_link_invalid")
            rendered = f'<a href="{html.escape(href, quote=True)}">{text}</a>'
            if node.get("mark") == "strong":
                rendered = f"<strong>{rendered}</strong>"
            elif node.get("mark") == "emphasis":
                rendered = f"<em>{rendered}</em>"
            result.append(rendered)
        elif kind == "strong":
            result.append(f"<strong>{text}</strong>")
        elif kind == "emphasis":
            result.append(f"<em>{text}</em>")
        else:
            result.append(text)
    return "".join(result)


def rich_text_to_html(document: Mapping[str, Any]) -> str:
    if document.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("rich_text_schema_invalid")
    output: list[str] = []
    for block in document.get("blocks") or []:
        kind = str(block.get("type") or "")
        if kind == "heading":
            level = max(2, min(4, int(block.get("level") or 2)))
            output.append(f"<h{level}>{_inline_html(block.get('content') or [])}</h{level}>")
        elif kind == "paragraph":
            output.append(f"<p>{_inline_html(block.get('content') or [])}</p>")
        elif kind == "bullet_list":
            items = "".join(
                f"<li>{_inline_html(item)}</li>" for item in (block.get("items") or [])
            )
            output.append(f"<ul>{items}</ul>")
        else:
            raise ValueError("rich_text_block_invalid")
    return "\n".join(output)


def rich_text_to_plain_text(document: Mapping[str, Any]) -> str:
    values: list[str] = []
    for block in document.get("blocks") or []:
        if block.get("type") == "bullet_list":
            groups = block.get("items") or []
        else:
            groups = [block.get("content") or []]
        for nodes in groups:
            values.append("".join(str(node.get("text") or "") for node in nodes).strip())
    return "\n\n".join(value for value in values if value)
