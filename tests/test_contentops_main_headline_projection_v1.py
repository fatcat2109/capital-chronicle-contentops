import hashlib
import json
from pathlib import Path

from live_contentops.contentops_main_headline_projection_v1 import (
    MainHeadlineExporter,
    project_headline,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

from live_contentops.contentops_source_research_v1 import RetainedSourceResearch

NOW = "2026-10-19T06:30:00Z"
RESEARCH_ROOT = Path(__file__).resolve().parents[1] / "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal20/retained_research"
RESEARCH = RetainedSourceResearch(RESEARCH_ROOT)

def project(row, *, cutoff_utc, locator):
    return project_headline(row, cutoff_utc=cutoff_utc, locator=locator, permission_resolver=RESEARCH.permission_for)


def official():
    return RESEARCH.headlines(cutoff_utc=NOW)[0]


def test_real_unicode_SEC_proposition_matches_Main_native_utf8_wire_hash():
    root = Path(__file__).parents[1] / "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal21/retained_research"
    research = RetainedSourceResearch(root)
    row = next(r for r in research.headlines(cutoff_utc="2026-10-19T12:00:00Z") if r["headline_id"] == "goal21-sec-cross-trading")
    projected, reason = project_headline(row, cutoff_utc="2026-10-19T12:00:00Z", locator={}, permission_resolver=research.permission_for)
    assert reason is None and "\u2019" in projected["headline_text"]
    unsigned = {k: v for k, v in projected.items() if k != "projection_sha256"}
    native = hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    escaped = hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    assert native != escaped and projected["projection_sha256"] == native


def test_unknown_x_permissions_remain_gap_even_with_canonical_marker():
    row = {
        **official(),
        "rights_state": None,
        "source_platform": "x_cdp_list_latest_tweets_timeline",
        "canonical_x_list_provenance": {"owner_curated_canonical_x_list": True},
    }
    projected, reason = project(row, cutoff_utc=NOW, locator={})
    assert (
        projected is None and reason == "SOURCE_RIGHTS_MISSING_NO_GOVERNED_INHERITANCE"
    )


def test_official_permission_clocks_and_private_data_boundaries():
    projected, reason = project(official(), cutoff_utc=NOW, locator={})
    assert not reason and projected["rights_evidence_sha256"] == official()["rights_evidence_sha256"]
    assert projected["underlying_event_truth_granted"] is False
    assert projected["public_republication_authority"] is False
    assert projected["context_only"] is True
    assert project(
        {**official(), "account_id": "NEVER_COPY"}, cutoff_utc=NOW, locator={}
    ) == (None, "PRIVATE_CONTEXT_EXCLUDED")
    assert (
        project(
            {**official(), "retrieval_time_utc": "2026-10-19T17:00:00Z"},
            cutoff_utc=NOW,
            locator={},
        )[1]
        == "FUTURE_HEADLINE_DEFERRED"
    )


def test_record_bound_permission_not_handle_or_blanket_grant():
    row = {**official(), "rights_state": None}
    row["source_permissions"] = {
        "source_identity": row["source_identity"],
        "content_sha256": hashlib.sha256(row["headline_text"].encode()).hexdigest(),
        "INTERNAL_ANALYSIS_ALLOWED": True,
        "MODEL_INPUT_ALLOWED": True,
        "LLM_INPUT_ALLOWED": True,
        "provider_safe": True,
        "permitted_consumers": ["internal_research"],
        "rights_evidence_sha256": "a" * 64,
    }
    assert project(row, cutoff_utc=NOW, locator={})[0] is None
    row["headline_text"] += " unbound addition"
    assert project(row, cutoff_utc=NOW, locator={})[0] is None


def test_bounded_cursor_resume_append_and_prefix_poison(tmp_path):
    source = tmp_path / "sidecar.jsonl"
    unknown = {
        "headline_text": "RESTRICTED_BODY_NEVER_EXPORTED",
        "source_platform": "x_cdp_list_latest_tweets_timeline",
    }
    source.write_text(
        json.dumps(unknown) + "\n" + json.dumps(official()) + "\n", encoding="utf-8"
    )
    exporter = MainHeadlineExporter(
        ContentOpsDurableStore(tmp_path / "isolated.sqlite3"), research=RESEARCH
    )
    exporter.research = None
    exporter.permission_for = RESEARCH.permission_for
    first = exporter.export(batch_id="one", paths=[source], cutoff_utc=NOW, max_rows=1)
    assert first["eligible_rows"] == 0 and first["missing_rows"] == 1
    assert "RESTRICTED_BODY" not in json.dumps(first)
    assert (
        exporter.export(batch_id="one", paths=[source], cutoff_utc=NOW, max_rows=1)
        == first
    )
    second = exporter.export(batch_id="two", paths=[source], cutoff_utc=NOW, max_rows=1)
    assert second["eligible_rows"] == 1 and second["source_rows_scanned"] == 1
    third = exporter.export(batch_id="three", paths=[source], cutoff_utc=NOW)
    assert third["source_rows_scanned"] == third["eligible_rows"] == 0
    source.write_text("x" + source.read_text(), encoding="utf-8")
    poisoned = exporter.export(batch_id="four", paths=[source], cutoff_utc=NOW)
    assert poisoned["gaps"][0]["state"] == "HEADLINE_SOURCE_PREFIX_CHANGED"


def test_future_record_does_not_starve_later_rows_and_recovers_after_restart(tmp_path):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    base = official()
    future = {**base, "headline_id": "future", "retrieval_time_utc": "2026-10-20T06:00:00Z", "revision_at_utc": "2026-10-20T06:00:00Z"}
    source = tmp_path / "arrivals.jsonl"
    source.write_text(json.dumps(future) + "\nnull\n" + json.dumps(base) + "\n", encoding="utf8")
    store = ContentOpsDurableStore(tmp_path / "late.sqlite3")
    exporter = MainHeadlineExporter(store)
    exporter.permission_for = lambda row, cutoff: RESEARCH.records[base["headline_id"]]["source_permissions"] if row.get("headline_id") in {base["headline_id"], "future"} else None
    first = exporter.export(batch_id="before", paths=[source], cutoff_utc=NOW)
    assert first["eligible_rows"] == 1 and first["source_rows_scanned"] == 3
    assert len(first["deferred"][sha256_of(str(source.resolve()))]) == 1
    restarted = MainHeadlineExporter(store)
    restarted.permission_for = exporter.permission_for
    recovered = restarted.export(batch_id="after", paths=[source], cutoff_utc="2026-10-20T07:00:00Z")
    assert recovered["eligible_rows"] == 1 and recovered["rows"][0]["headline_id"] == "future"
    assert not recovered["deferred"][sha256_of(str(source.resolve()))]
