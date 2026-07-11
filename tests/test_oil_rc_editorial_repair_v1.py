from pathlib import Path

from live_contentops import oil_rc_editorial_repair_v1 as repair


def test_fred_rows_rejects_short_series():
    raw = b"DATE,DCOILWTICO\n2026-01-01,70\n"
    try:
        repair._fred_rows(raw)
    except ValueError as error:
        assert str(error) == "insufficient_fred_wti_observations"
    else:
        raise AssertionError("short series must fail")


def test_repair_constants_use_official_sources():
    assert repair.EIA_MAP_URL.startswith("https://www.eia.gov/")
    assert repair.FRED_CSV.startswith("https://fred.stlouisfed.org/")


def test_dimensions_reads_real_image(tmp_path: Path):
    from PIL import Image

    path = tmp_path / "visual.png"
    Image.new("RGB", (640, 360)).save(path)
    assert repair._dimensions(path) == (640, 360)


def test_local_editorial_gate_fails_closed_on_visual_block(tmp_path: Path):
    packet = {
        "visual_assets": [],
        "source_wording_calibrated": True,
        "process_language_absent": True,
        "article_mode": "analysis",
        "as_of_utc": "2026-07-06T23:59:59Z",
        "visual_asset_count": 0,
        "public_write_performed": False,
        "body_sha256": "a" * 64,
    }
    result = repair.evaluate_oil_rc_repair_packet(output_dir=tmp_path, packet=packet)
    assert result["status"] == "BLOCK_LOCAL_REPAIR_GATES"
    assert result["deterministic_checks"]["visual_composition"] is False
