"""Minimal local macro chart renderer for V6 media readiness.

No data is fabricated: callers must provide a CSV with at least one numeric
column. If plotting support or data is missing, the renderer returns a blocked
metadata packet instead of producing fake evidence.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

DEFAULT_CHART_DIR = Path("docs/automation/V6_MEDIA_SYSTEM/generated_charts")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _blocked(topic: str, reason: str) -> dict[str, Any]:
    return {
        "chart_status": "BLOCKED",
        "topic": topic,
        "chart_path": None,
        "metadata_path": None,
        "source_path": None,
        "warnings": [reason],
    }


def render_macro_chart(topic: str, source_csv: str | Path | None, output_dir: str | Path = DEFAULT_CHART_DIR) -> dict[str, Any]:
    out_dir = Path(output_dir)
    if not source_csv:
        return _blocked(topic, "chart_source_csv_missing")
    source = Path(source_csv)
    if not source.exists():
        return _blocked(topic, "chart_source_csv_not_found")

    try:
        import matplotlib  # type: ignore

        # Deterministic headless rendering: without this the default backend can be an
        # interactive GUI one, which fails outright where no display/Tk is available.
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return _blocked(topic, "matplotlib_unavailable")

    with source.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return _blocked(topic, "chart_source_csv_empty")

    fields = list(rows[0].keys())
    x_field = fields[0]
    y_field = None
    y_values: list[float] = []
    for field in fields[1:]:
        vals: list[float] = []
        for row in rows:
            try:
                vals.append(float(str(row.get(field, "")).replace(",", "")))
            except ValueError:
                vals = []
                break
        if vals:
            y_field = field
            y_values = vals
            break
    if not y_field:
        return _blocked(topic, "chart_numeric_series_missing")

    x_values = [str(row.get(x_field, "")) for row in rows]
    safe = "".join(ch if ch.isalnum() else "_" for ch in topic.lower()).strip("_")[:64] or "macro_chart"
    out_dir.mkdir(parents=True, exist_ok=True)
    chart_path = out_dir / f"{safe}.png"
    metadata_path = out_dir / f"{safe}.json"

    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=160)
    ax.plot(x_values, y_values, color="#2563eb", linewidth=2.5, marker="o")
    ax.set_title(topic[:100])
    ax.set_xlabel(x_field)
    ax.set_ylabel(y_field)
    ax.grid(True, alpha=0.25)
    fig.autofmt_xdate(rotation=35)
    fig.tight_layout()
    fig.savefig(chart_path)
    plt.close(fig)

    metadata = {
        "chart_status": "READY",
        "topic": topic,
        "chart_path": str(chart_path),
        "metadata_path": str(metadata_path),
        "source_path": str(source),
        "source_sha256": _sha256(source),
        "chart_sha256": _sha256(chart_path),
        "series": {"x": x_field, "y": y_field, "points": len(y_values)},
        "warnings": [],
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata
