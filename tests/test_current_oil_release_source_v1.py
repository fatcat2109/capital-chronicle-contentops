from __future__ import annotations

import pytest

from live_contentops.current_oil_release_source_v1 import parse_current_eia_oil_release


FIXTURE = """
<html><body>
<h1>EIA increases global oil production forecast after the opening of the Strait of Hormuz</h1>
<p>FOR IMMEDIATE RELEASE July 7, 2026</p>
<p>EIA expects crude oil output and trade flows to return to near pre-conflict levels by year's end, with most shut-in production restored by the first quarter of 2027.</p>
<p>The Brent crude oil spot price averaged $85 per barrel (b) in June.</p>
<p>EIA forecasts Brent crude oil prices to average $74/b in the third quarter of 2026, with Brent falling to an average of $65/b in 2027.</p>
<p>Gasoline 3Q26 averages declining to $3.80/gal, then about $3.40/gal in 4Q26.</p>
</body></html>
"""


def test_parses_only_official_release_facts_into_grounding_packet() -> None:
    packet = parse_current_eia_oil_release(FIXTURE)
    assert packet["status"] == "PASS_OFFICIAL_EIA_RELEASE_GROUNDED"
    assert packet["facts"]["release_date"] == "2026-07-07"
    assert packet["facts"]["brent_q3_2026_forecast_usd_per_barrel"] == 74.0
    assert packet["facts"]["gasoline_q4_2026_forecast_usd_per_gallon"] == 3.4
    assert packet["headline_feed_numeric_authority"] is False


def test_missing_core_forecast_fails_closed() -> None:
    with pytest.raises(ValueError, match="near_pre_conflict"):
        parse_current_eia_oil_release(FIXTURE.replace("return to near pre-conflict levels by year's end", "remain uncertain"))


@pytest.mark.parametrize(
    "wording",
    (
        "rebound to near pre-conflict levels by year's end",
        "return to near pre-conflict levels by year end",
    ),
)
def test_accepts_both_live_eia_forecast_phrasings(wording: str) -> None:
    packet = parse_current_eia_oil_release(
        FIXTURE.replace("return to near pre-conflict levels by year's end", wording)
    )
    assert packet["facts"]["global_output_near_pre_conflict_by_year_end"] is True
