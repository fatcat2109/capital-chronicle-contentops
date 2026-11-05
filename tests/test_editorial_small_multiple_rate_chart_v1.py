"""The live chart consumer keeps fractional rates and long labels readable."""
import hashlib

import pytest

from live_contentops import rolling_x_grounded_article_media_builder_v1 as charts


@pytest.mark.parametrize("unit,expected", [
    ("percent", ["+1.2%", "+10.8%", "+0.3%", "+1.4%", "+3.4%", "+0.3%"]),
    ("USD", ["+1", "+11", "+0", "+1", "+3", "+0"]),
])
def test_source_bound_small_multiples_keep_value_precision_and_labels_inside_image(tmp_path, monkeypatch, unit, expected):
    numbers = [1.2, 10.8, 0.3, 1.4, 3.4, 0.3]
    names = ["Foods", "Energy", "Goods less foods and energy", "Trade services (margins)",
        "Transportation and warehousing", "Services less trade, transportation and warehousing"]
    text = "September 2026 controlled fixture: " + "; ".join(f"{name} {value}" for name, value in zip(names, numbers))
    digest = hashlib.sha256(text.encode()).hexdigest()
    doc = {"document_id": "controlled-rates", "url": "https://www.bls.gov/controlled-fixture",
        "publisher": "Controlled BLS fixture", "published_at_utc": "2026-10-15T12:30:00Z",
        "canonical_content_text": text, "canonical_content_sha256": digest,
        "source_reuse_constraints": {"attribution_required": True,
            "policy_capture_sha256": "a" * 64, "source_capture_sha256": digest}}
    points = [{"period": name, "value": value, "observation_kind": "REPORTED_ACTUAL",
        "inputs": [{"document_id": doc["document_id"], "support_excerpt": text,
            "value_text": str(value), "source_period_text": "September 2026",
            "source_content_sha256": digest, "metric": name, "unit": unit,
            "prepared_period": "2026-09", "period_basis": {"basis": "CONTROLLED_FIXTURE"}}]}
        for name, value in zip(names, numbers)]
    packet = {"asset_id": "controlled_fractional_rates", "chart_type": "SMALL_MULTIPLE_HORIZONTAL_DIVERGING_BARS",
        "title": "Controlled component rates", "question": "Are the exact rates readable?", "unit": unit,
        "zero_based": True, "source_caption": "Source: controlled fixture",
        "series": [{"name": "Goods categories", "points": points[:3]},
            {"name": "Services categories", "points": points[3:]}]}
    captured = []
    original = charts._draw_editorial_chart

    def capture(*args):
        figure = original(*args)
        captured.append(figure)
        return figure

    monkeypatch.setattr(charts, "_draw_editorial_chart", capture)
    asset = charts.build_editorial_data_chart(packet, [doc], output_dir=tmp_path)
    charts.validate_source_value_chart(asset, [doc])
    assert asset["computed_values"] == [numbers[:3], numbers[3:]]
    figure = captured[0]
    assert [text.get_text() for ax in figure.axes for text in ax.texts] == expected
    assert figure.axes[0].get_xlim() == figure.axes[1].get_xlim()
    assert figure.axes[0].get_xlim()[0] == 0
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    for ax in figure.axes:
        boxes = [label.get_window_extent(renderer) for label in ax.get_yticklabels()]
        assert all(box.x0 >= 0 and box.x1 <= figure.bbox.width for box in boxes)
        ordered = sorted(boxes, key=lambda box: box.y0)
        assert all(a.y1 < b.y0 for a, b in zip(ordered, ordered[1:]))
