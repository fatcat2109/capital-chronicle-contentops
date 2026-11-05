"""Jim's decision 83 (5 Nov): until Capital Chronicle owns its own domain, no post on social media
or Substack links to the preview or any other host. Every final payload is checked before its write;
a match is a definite no-write with PREVIEW_HOST_LINK_FORBIDDEN. No exceptions until we own a
domain; after that, only that domain."""
from __future__ import annotations

import re
from typing import Any, Iterable, Mapping

REASON = "PREVIEW_HOST_LINK_FORBIDDEN"
FORBIDDEN = re.compile(
    r"github\.io|pages\.dev|workers\.dev|netlify\.app|vercel\.app|fatcat2109|capital-chronicle-preview", re.I)


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item)


def find_forbidden_link(*values: Any) -> str | None:
    """The first forbidden host text in any string of the given values, else None."""
    for text in _strings(list(values)):
        match = FORBIDDEN.search(text)
        if match:
            return match.group(0)
    return None


def posted_values(intent: Mapping[str, Any], canonical_url: Any = None) -> list:
    """What a write can put in public: its copy, its frozen per-destination payload and its link."""
    plan = intent.get("destination_plan") or {}
    return [intent.get("payload"), intent.get("native_payload"), plan.get("payload"),
            intent.get("canonical_url"), canonical_url]


def refusal(destination: str, match: str) -> dict:
    return {"destination": destination, "status": REASON, "reason_code": REASON, "matched": match,
            "definite_no_write": True, "public_write_performed": False, "publish_called": False}
