"""Fact cards retain exact displays without inventing electorate totals or scales."""
from copy import deepcopy
from hashlib import sha256

import pytest

from live_contentops.rolling_x_grounded_article_media_builder_v1 import _editorial_data_values, _draw_editorial_chart


def controlled_card():
    text = ("Controlled poll on 2 November 2026 reports Democrats 51.1% and Republicans 42.8%. "
            "First polls close at 23:00 UTC on 3 November 2026.")
    doc = {"document_id": "controlled", "canonical_content_text": text,
           "source_reuse_constraints": {"attribution_required": True, "policy_capture_sha256": "a" * 64,
                                         "source_capture_sha256": "b" * 64}}
    points = [{"period": label, "value": value, "display_value": display, "transform": "IDENTITY",
               "observation_kind": "ESTIMATE", "inputs": [{"document_id": "controlled", "value_text": display.rstrip("%"),
               "support_excerpt": text, "source_period_text": "2 November 2026",
               "source_content_sha256": sha256(text.encode()).hexdigest(), "metric": "Generic-ballot share",
               "unit": "percent", "prepared_period": "2 November 2026",
               "period_basis": {"source_period": "2 November 2026"}}]}
              for label, value, display in (("Democrats", 51.1, "51.1%"), ("Republicans", 42.8, "42.8%"))]
    packet = {"chart_type": "fact_card", "question": "What does the controlled poll report?",
              "title": "Controlled polling snapshot", "subtitle": "2 November 2026", "unit": "percent",
              "fact_card_note": "Voting intentions, not chamber-control probabilities.",
              "fact_card_footer": "First polls close: 23:00 UTC on 3 November",
              "source_caption": "Controlled synthetic source.", "series": [{"label": "Reported shares", "points": points}]}
    return packet, [doc]


def test_fact_card_keeps_two_source_exact_independent_callouts():
    import matplotlib.pyplot as plt
    import numpy as np
    packet, docs = controlled_card()
    values = _editorial_data_values(packet, docs)
    assert values == [[51.1, 42.8]]
    fig = _draw_editorial_chart(packet, values, plt, np)
    try:
        labels = [t.get_text() for t in fig.texts]
        assert "51.1%" in labels and "42.8%" in labels
        assert not fig.axes[0].patches and not fig.axes[0].lines
        assert [t.get_fontsize() for t in fig.texts if t.get_text() in {"51.1%", "42.8%"}] == [43, 43]
    finally:
        plt.close(fig)


@pytest.mark.parametrize("fault,cause", [
    ("rounding", "FACT_CARD_EXACT_SOURCE_DISPLAY_REQUIRED"),
    ("time", "FACT_CARD_TEXT_NUMBER_UNBOUND"),
    ("remainder", "EDITORIAL_CHART_COMPUTED_VALUE_CHANGED"),
    ("instruction", "PRIVATE_OR_EXECUTION_COPY_FORBIDDEN"),
])
def test_card_refuses_rounded_invented_or_private_display(fault, cause):
    packet, docs = controlled_card()
    packet = deepcopy(packet)
    if fault == "rounding":
        packet["series"][0]["points"][0]["display_value"] = "51%"
    elif fault == "time":
        packet["fact_card_footer"] = "First polls close: 23:59 UTC on 3 November"
    elif fault == "remainder":
        packet["series"][0]["points"][0]["value"] = 6.1
    else:
        packet["fact_card_note"] = "Buy gold now."
    with pytest.raises(ValueError, match=cause):
        _editorial_data_values(packet, docs)
