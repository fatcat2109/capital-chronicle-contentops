import json
from datetime import date, timedelta
from pathlib import Path

from live_contentops.media_content_audit_v6 import (
    audit_media_candidate,
    render_current_wti_visual_pack,
)


def test_audit_rejects_stale_wikimedia_chart_for_current_oil_article(tmp_path):
    image_path = tmp_path / "stale.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 4096)

    audit = audit_media_candidate(
        article_title="US recession risks rise as oil volatility spikes",
        article_text="Oil volatility is rising in the current macro setup.",
        image_path=image_path,
        public_image_url="https://upload.wikimedia.org/chart.png",
        source_metadata={
            "source_label": "upload.wikimedia.org",
            "visual_metric": "wti crude oil price chart",
            "time_coverage_end_year": 2023,
            "recent_direction": "down",
        },
        as_of_date="2026-07-07",
    )

    assert audit["audit_status"] == "FAIL"
    assert "media_provenance_weak_upload_host" in audit["blockers"]
    assert "media_outdated_time_coverage:2023<2025" in audit["blockers"]
    assert "media_metric_mismatch:expected_oil_volatility_context" in audit["blockers"]
    assert "media_direction_mismatch:expected_up_actual_down" in audit["blockers"]


def test_audit_accepts_current_source_backed_oil_volatility_chart(tmp_path):
    image_path = tmp_path / "current.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 4096)

    audit = audit_media_candidate(
        article_title="US recession risks rise as oil volatility spikes",
        article_text="The article focuses on current oil volatility and data transparency.",
        image_path=image_path,
        source_metadata={
            "canonical_source_label": "FRED series DCOILWTICO; underlying source U.S. Energy Information Administration",
            "visual_metric": "oil_volatility wti crude oil current price realized volatility",
            "latest_observation_year": 2026,
            "recent_direction": "up",
        },
        as_of_date="2026-07-07",
    )

    assert audit["audit_status"] == "PASS"
    assert audit["blockers"] == []


def test_render_current_wti_visual_pack_writes_assets_and_metadata(tmp_path):
    csv_path = tmp_path / "fred.csv"
    start = date(2025, 1, 1)
    rows = ["DATE,DCOILWTICO"]
    for idx in range(90):
        dt = start + timedelta(days=idx)
        rows.append(f"{dt.isoformat()},{70 + idx * 0.15:.2f}")
    csv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    assets = render_current_wti_visual_pack(
        article_title="US recession risks rise as oil volatility spikes",
        output_dir=tmp_path,
        as_of_date="2026-07-07",
        fetch_url=csv_path.resolve().as_uri(),
    )

    assert len(assets) == 2
    for asset in assets:
        path = Path(asset["local_path"])
        assert path.exists()
        metadata = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
        assert metadata["latest_observation_year"] == 2025
        assert "FRED series DCOILWTICO" in metadata["canonical_source_label"]
