"""Measured unchanged-month extraction failures are repaired from held bytes."""
from hashlib import sha256
import gzip
import json
from types import SimpleNamespace

import pytest

from live_contentops.official_release_history_v1 import (
    _ppi_sentence_change, history_documents, preserve_prewrite_history_correction, reconcile_ppi_history,
)


@pytest.mark.parametrize("period,prior", [("2025-02", 0.6), ("2025-06", 0.3), ("2026-07", -0.1)])
def test_unchanged_current_month_does_not_take_a_later_number(tmp_path, period, prior):
    import calendar
    month = calendar.month_name[int(period[5:])]
    text = (f"The Producer Price Index for final demand was unchanged in {month}, seasonally adjusted. "
        "Final demand prices edged down 0.1 percent in the prior month. "
        f"Prices for final demand less foods, energy, and trade services rose 0.4 percent in {month}.")
    raw = ("<html><pre>" + text + "</pre></html>").encode()
    (tmp_path / "source.gz").write_bytes(gzip.compress(raw))
    original = {"value": prior, "source_sha256": sha256(raw).hexdigest(),
        "source_relative_artifact": "source.gz", "source_url": "https://www.bls.gov/news.release/archives/ppi_08122026.htm",
        "release_datetime_utc": "2026-08-12T12:30:00Z", "availability": "OBSERVED"}
    history = {"dataset_sha256": "a" * 64, "archive_root": str(tmp_path), "cutoff_utc": "2026-11-05T00:00:00Z",
        "window": [period, period], "series": [{"name": "PPI_FINAL_DEMAND_MOM", "official_series_id": "WPSFD4",
            "unit": "percent", "measure": "MONTH_ON_MONTH", "seasonal_adjustment": "SA",
            "observations": [{"period": period, "value": prior, "availability": "OBSERVED", "source_record": original}]}]}
    fixed = reconcile_ppi_history(history)
    assert history["series"][0]["observations"][0]["value"] == prior
    observed = fixed["series"][0]["observations"][0]
    assert observed["value"] == 0
    assert observed["source_record"]["producer_record_preserved"] == original
    assert "was unchanged" in fixed["projection_corrections"][0]["exact_source_span"]
    assert fixed["series"][1]["observations"][0]["value"] == 0.4
    docs = history_documents(fixed)
    assert "0 percent" in docs[0]["canonical_content_text"]
    assert "0.4 percent" in docs[1]["canonical_content_text"]


def test_combined_release_uses_the_requested_months_own_clause():
    text = ("The index for final demand less foods, energy, and trade services advanced 0.2 percent "
        "in November after moving up 0.7 percent in October.")
    assert _ppi_sentence_change(text, "2025-10", core=True)[0] == 0.7
    assert _ppi_sentence_change(text, "2025-11", core=True)[0] == 0.2
    assert _ppi_sentence_change(text, "2025-09", core=True) is None


def test_unknown_or_mismatched_source_hash_is_not_reconciled(tmp_path):
    (tmp_path / "source.gz").write_bytes(gzip.compress(b"changed source"))
    history = {"archive_root": str(tmp_path), "series": [{"name": "PPI_FINAL_DEMAND_MOM", "observations": [
        {"period": "2026-07", "value": -0.1, "source_record": {
            "source_relative_artifact": "source.gz", "source_sha256": "f" * 64}}]}]}
    with pytest.raises(ValueError, match="SOURCE_CAPTURE_HASH_CHANGED"):
        reconcile_ppi_history(history)


def test_prewrite_correction_retains_old_evidence_without_replacing_native_requests(tmp_path):
    old = {"selected_source_pack": [{"document_id": "old-ppi-projection", "canonical_content_sha256": "a" * 64,
        "source_authority_class": "official_release_history_from_cc010"}]}
    raw = json.dumps(old).encode()
    (tmp_path / "simple_gemini_evidence_v1.json").write_bytes(raw)
    (tmp_path / "editorial_media_plan_required.json").write_bytes(b'{"old":"media"}')
    (tmp_path / "desktop_request_media-plan.json").write_bytes(b'{"frozen":"native"}')
    turn = SimpleNamespace(root=tmp_path, frozen_request=lambda stage: None)
    history = {"projection_corrections": [{"period": "2026-07", "reported_value": 0}]}
    docs = [{"document_id": "correct-ppi-projection", "canonical_content_sha256": "b" * 64}]
    preserve_prewrite_history_correction(turn, history, docs)
    assert not (tmp_path / "simple_gemini_evidence_v1.json").exists()
    assert next((tmp_path / "source-recovery-history").rglob('simple_gemini_evidence_v1.json')).read_bytes() == raw
    assert (tmp_path / "desktop_request_media-plan.json").read_bytes() == b'{"frozen":"native"}'
