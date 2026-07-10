"""Ground the current EIA oil-release story in an official source packet."""
from __future__ import annotations

import hashlib
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any


SCHEMA_VERSION = "contentops.current_oil_release_source.v1"
EIA_PRESS_RELEASE_URL = "https://www.eia.gov/pressroom/releases/press590.php"
EIA_STEO_URL = "https://www.eia.gov/outlooks/steo/"
EIA_WPSR_URL = "https://www.eia.gov/petroleum/supply/weekly/"
FRED_WTI_URL = "https://fred.stlouisfed.org/series/DCOILWTICO"
FED_JUNE_STATEMENT_URL = "https://www.federalreserve.gov/newsevents/pressreleases/monetary20260617a.htm"


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._hidden_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag in {"script", "style", "noscript", "svg"}:
            self._hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._hidden_depth:
            self._hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._hidden_depth and data.strip():
            self.parts.append(data.strip())


def _visible_text(html: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(html)
    text = " ".join(" ".join(parser.parts).split())
    return text.replace("\u2019", "'").replace("\u2018", "'").replace("\xa0", " ")


def _money(text: str, pattern: str, label: str) -> float:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"official_eia_fact_missing:{label}")
    return float(match.group(1))


def parse_current_eia_oil_release(html: str, *, source_url: str = EIA_PRESS_RELEASE_URL) -> dict[str, Any]:
    text = _visible_text(html)
    if "EIA increases global oil production forecast" not in text:
        raise ValueError("official_eia_release_title_missing")
    release_match = re.search(r"(?:FOR IMMEDIATE RELEASE\s+)?(July\s+7,\s+2026)", text, flags=re.IGNORECASE)
    if not release_match:
        raise ValueError("official_eia_release_date_missing")
    if not re.search(
        r"(?:return|rebound) to near pre-conflict levels by year(?:'s)? end",
        text,
        flags=re.IGNORECASE,
    ):
        raise ValueError("official_eia_near_pre_conflict_forecast_missing")
    if not re.search(
        r"shut.?in production (?:restored|returning online) by (?:(?:the )?first quarter of|early) 2027",
        text,
        flags=re.IGNORECASE,
    ):
        raise ValueError("official_eia_restoration_timing_missing")

    facts = {
        "release_date": datetime.strptime(release_match.group(1), "%B %d, %Y").date().isoformat(),
        "global_output_near_pre_conflict_by_year_end": True,
        "most_shut_in_output_restored_by": "2027-Q1",
        "brent_june_average_usd_per_barrel": _money(
            text,
            r"Brent crude oil spot price averaged \$([0-9]+(?:\.[0-9]+)?) per barrel.*?in June",
            "brent_june_average",
        ),
        "brent_q3_2026_forecast_usd_per_barrel": _money(
            text,
            r"Brent crude oil prices? to average \$([0-9]+(?:\.[0-9]+)?)/b in the third quarter of 2026",
            "brent_q3_forecast",
        ),
        "brent_2027_forecast_usd_per_barrel": _money(
            text,
            r"Brent falling to an average of \$([0-9]+(?:\.[0-9]+)?)/b in 2027",
            "brent_2027_forecast",
        ),
        "gasoline_q3_2026_forecast_usd_per_gallon": _money(
            text,
            r"3Q26 averages declining to \$([0-9]+(?:\.[0-9]+)?)/gal",
            "gasoline_q3_forecast",
        ),
        "gasoline_q4_2026_forecast_usd_per_gallon": _money(
            text,
            r"about \$([0-9]+(?:\.[0-9]+)?)/gal in 4Q26",
            "gasoline_q4_forecast",
        ),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS_OFFICIAL_EIA_RELEASE_GROUNDED",
        "retrieved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_title": "EIA increases global oil production forecast after the opening of the Strait of Hormuz",
        "source_url": source_url,
        "supporting_source_urls": [EIA_STEO_URL, FRED_WTI_URL, FED_JUNE_STATEMENT_URL, EIA_WPSR_URL],
        "source_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "facts": facts,
        "numeric_truth_authority": "official_eia_release_plus_manifest_bound_fred_wti_series",
        "headline_feed_numeric_authority": False,
    }


def fetch_current_eia_oil_release_packet(
    *,
    source_url: str = EIA_PRESS_RELEASE_URL,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    def fetch_html(url: str) -> str:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "CapitalChronicleContentOps/1.0"},
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return response.read().decode("utf-8", errors="replace")

    html = fetch_html(source_url)
    packet = parse_current_eia_oil_release(html, source_url=source_url)
    supporting_retrievals: list[dict[str, Any]] = []
    for url, fact_name, pattern in (
        (
            EIA_STEO_URL,
            "next_steo_release_date",
            r"Next Release Date:\s*(August\s+11,\s+2026)",
        ),
        (
            EIA_WPSR_URL,
            "next_weekly_petroleum_status_report_date",
            r"Next Release Date:\s*(July\s+15,\s+2026)",
        ),
    ):
        support_text = _visible_text(fetch_html(url))
        match = re.search(pattern, support_text, flags=re.IGNORECASE)
        if not match:
            raise ValueError(f"official_eia_supporting_release_date_missing:{fact_name}")
        packet["facts"][fact_name] = datetime.strptime(match.group(1), "%B %d, %Y").date().isoformat()
        supporting_retrievals.append({
            "source_url": url,
            "source_text_sha256": hashlib.sha256(support_text.encode("utf-8")).hexdigest(),
            "verified_fact": fact_name,
        })
    packet["supporting_source_retrievals"] = supporting_retrievals
    return packet
