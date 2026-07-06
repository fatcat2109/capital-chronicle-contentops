from pathlib import Path
from unittest.mock import patch

from live_contentops.macro_chart_renderer_v6 import render_macro_chart


def test_render_macro_chart_blocks_without_source(tmp_path):
    res = render_macro_chart("Macro chart", None, tmp_path)
    assert res["chart_status"] == "BLOCKED"
    assert "chart_source_csv_missing" in res["warnings"]


def test_render_macro_chart_blocks_without_numeric_series(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text("date,label\n2026-01,a\n", encoding="utf-8")
    res = render_macro_chart("Macro chart", source, tmp_path / "out")
    assert res["chart_status"] == "BLOCKED"
    assert "chart_numeric_series_missing" in res["warnings"]


def test_render_macro_chart_ready_with_mocked_matplotlib(tmp_path):
    source = tmp_path / "series.csv"
    source.write_text("date,value\n2026-01,1.5\n2026-02,2.0\n", encoding="utf-8")

    class Fig:
        def autofmt_xdate(self, rotation=0):
            pass
        def tight_layout(self):
            pass
        def savefig(self, path):
            Path(path).write_bytes(b"png")
    class Ax:
        def plot(self, *a, **k):
            pass
        def set_title(self, *a, **k):
            pass
        def set_xlabel(self, *a, **k):
            pass
        def set_ylabel(self, *a, **k):
            pass
        def grid(self, *a, **k):
            pass
    with patch("matplotlib.pyplot.subplots", return_value=(Fig(), Ax())), patch("matplotlib.pyplot.close"):
        res = render_macro_chart("Macro chart", source, tmp_path / "out")

    assert res["chart_status"] == "READY"
    assert Path(res["chart_path"]).exists()
    assert Path(res["metadata_path"]).exists()
    assert res["series"]["points"] == 2
