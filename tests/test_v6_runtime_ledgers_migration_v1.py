"""Isolated tmp_path tests for ContentOps V6 ledger Runtime-path migration.

Verifies that default writes for:
  - public_dispatch_duplicate_ledger_v6.jsonl
  - live_telemetry_registry_v6.jsonl
target A:\\Capital Chronicle\\Runtime\\ContentOps\\v6_ledgers\\... (never tracked docs/automation/...),
while preserving 100% backward-compatible read fallback, atomic first-write seeding, CRLF->LF
normalization, rotation safety, test-path isolation, and idempotent operator cutover migration.

Zero writes under A:\\Capital Chronicle\\...; 100% isolated under tmp_path.
Operator: T3 Code, Gemini 4 Neon xhigh, antigravity_14
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from live_contentops import (
    full_pipeline_north_star_debug_and_live_run_v0 as north_star_debug,
    live_production_pipeline_runner_v6 as live_runner,
    live_telemetry_v6 as lt,
    operator_approved_supervised_live_daily_run_v0 as operator_daily,
    public_candidate_preflight_v6 as preflight,
    public_dispatch_freeze_guard_v6 as guard,
    public_permissive_supervised_mode_v0 as permissive,
    substack_first_north_star_pipeline_loop_v1 as substack_loop,
    terra_ultra_north_star_full_automation_v1 as terra_ultra,
    v6_post_release_operator_governance as governance,
    v6_runtime_ledgers_v1 as v6_rt,
)
from live_contentops.platform_error_classifier import PlatformErrorSafetyError


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_crlf_jsonl(path: Path, rows: list[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = "\r\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\r\n"
    path.write_bytes(raw.encode("utf-8"))
    return _sha256(path)


# ---------------------------------------------------------------------------
# 1. Canonical Default Path Wiring Across All V6 Modules
# ---------------------------------------------------------------------------


def test_all_v6_default_ledger_constants_point_to_runtime_root_not_docs_automation():
    expected_dispatch = v6_rt.CANONICAL_PUBLIC_DISPATCH_LEDGER
    expected_telemetry = v6_rt.CANONICAL_LIVE_TELEMETRY_FILE
    expected_runtime_prefix = str(v6_rt.RUNTIME_ROOT).lower()

    dispatch_paths = [
        expected_dispatch,
        guard.DEFAULT_PUBLIC_DISPATCH_LEDGER,
        live_runner.PUBLIC_DISPATCH_LEDGER_PATH,
        preflight.DEFAULT_LEDGER,
        permissive.DEFAULT_DUPLICATE_LEDGER,
        north_star_debug.DEFAULT_DUPLICATE_LEDGER,
        operator_daily.DEFAULT_DUPLICATE_LEDGER,
        substack_loop.PUBLIC_DISPATCH_LEDGER,
        terra_ultra.PUBLIC_DISPATCH_LEDGER,
    ]
    for p in dispatch_paths:
        assert Path(p) == expected_dispatch
        lower = str(p).lower()
        assert lower.startswith(expected_runtime_prefix)
        assert "docs/automation" not in lower and "docs\\automation" not in lower

    telemetry_paths = [
        expected_telemetry,
        Path(lt.TELEMETRY_FILE),
        governance.TELEMETRY_LOG_PATH,
    ]
    for p in telemetry_paths:
        assert Path(p) == expected_telemetry
        lower = str(p).lower()
        assert lower.startswith(expected_runtime_prefix)
        assert "docs/automation" not in lower and "docs\\automation" not in lower

    assert Path(lt.TELEMETRY_DIR) == v6_rt.CANONICAL_LIVE_TELEMETRY_DIR

    # Ensure the live eight-platform Telegram publish paths no longer hardcode tracked docs/automation.
    impl_src = (
        Path(__file__).resolve().parents[1]
        / "live_contentops"
        / "_eight_platform_substack_first_pipeline_impl_v1.py"
    ).read_text(encoding="utf-8")
    assert "docs/automation/V6_PUBLIC_DISPATCH_FREEZE/public_dispatch_duplicate_ledger_v6.jsonl" not in impl_src


# ---------------------------------------------------------------------------
# 2. Public Dispatch Duplicate Freeze Ledger: Fallback, Seed, Union, Isolation
# ---------------------------------------------------------------------------


def test_dispatch_ledger_read_fallback_preserves_3_month_history_with_zero_writes(tmp_path, monkeypatch):
    legacy = tmp_path / "repo" / "docs" / "automation" / "V6_PUBLIC_DISPATCH_FREEZE" / "public_dispatch_duplicate_ledger_v6.jsonl"
    runtime = tmp_path / "runtime" / "v6_ledgers" / "public_dispatch_freeze" / "public_dispatch_duplicate_ledger_v6.jsonl"

    topic_hash = guard.build_public_dispatch_topic_hash("Historical Aug 2026 macro call", "rates")
    payload_hash = guard.build_public_dispatch_payload_hash(
        platform="telegram",
        action="photo",
        body_text="Historical published post body with substantial analytical commentary for readers.",
        canonical_url="https://capitalchronicle.substack.com/p/historical-aug-2026",
        media_url="https://cdn.example.com/chart-aug.png",
        topic_hash=topic_hash,
    )
    legacy_rows = [
        {
            "record_type": "incident_duplicate_freeze",
            "platform": "telegram",
            "canonical_url": "https://capitalchronicle.substack.com/p/crude-awakening",
            "topic_hint": "Crude awakening oil volatility",
            "media_hint": "WTI chart",
        },
        {
            "record_type": "public_dispatch_payload",
            "platform": "telegram",
            "action": "photo",
            "run_id": "run_20260831",
            "topic_hash": topic_hash,
            "payload_hash": payload_hash,
            "canonical_url": "https://capitalchronicle.substack.com/p/historical-aug-2026",
            "media_url": "https://cdn.example.com/chart-aug.png",
            "status": "SUCCESS",
        },
    ]
    legacy_sha_before = _write_crlf_jsonl(legacy, legacy_rows)

    monkeypatch.setattr(guard, "DEFAULT_PUBLIC_DISPATCH_LEDGER", runtime)
    monkeypatch.setattr(guard, "LEGACY_PUBLIC_DISPATCH_LEDGER", legacy)

    # Read-only load falls back seamlessly to legacy and creates ZERO files under runtime.
    prior = guard.load_public_dispatch_hashes()
    assert not runtime.exists()
    assert _sha256(legacy) == legacy_sha_before
    assert payload_hash in prior["payload_hashes"]
    assert topic_hash in prior["topic_hashes"]
    assert len(prior["canonical_url_hashes"]) == 2

    # Freeze guard blocks any attempted re-dispatch matching 3-month legacy history.
    marker = guard.make_public_dispatch_approval_marker(
        run_id="run_20261126",
        topic_hash=topic_hash,
        payload_hash=payload_hash,
        platform="telegram",
    )
    decision = guard.evaluate_public_dispatch_freeze(
        platform="telegram",
        action="photo",
        run_id="run_20261126",
        topic_hash=topic_hash,
        operator_approval_marker=marker,
        body_text="Historical published post body with substantial analytical commentary for readers.",
        canonical_url="https://capitalchronicle.substack.com/p/historical-aug-2026",
        media_url="https://cdn.example.com/chart-aug.png",
        payload_hash=payload_hash,
        prior_dispatch_hashes=prior,
    )
    assert decision["dispatch_allowed"] is False
    assert decision["status"] == guard.GUARD_STATUS_BLOCKED
    assert "duplicate_payload_hash" in decision["blockers"]
    assert "duplicate_topic_hash" in decision["blockers"]
    assert "duplicate_canonical_url_hash" in decision["blockers"]


def test_dispatch_ledger_first_write_auto_seeds_runtime_normalizes_lf_and_never_mutates_legacy(tmp_path, monkeypatch):
    legacy = tmp_path / "repo" / "public_dispatch_duplicate_ledger_v6.jsonl"
    runtime = tmp_path / "runtime" / "v6_ledgers" / "public_dispatch_freeze" / "public_dispatch_duplicate_ledger_v6.jsonl"

    old_row = {
        "record_type": "public_dispatch_payload",
        "platform": "telegram",
        "action": "post",
        "run_id": "run_legacy_1",
        "topic_hash": "old_topic_hash_1",
        "payload_hash": "old_payload_hash_1",
        "canonical_url": "https://capitalchronicle.substack.com/p/old-post-1",
        "status": "SUCCESS",
    }
    legacy_sha_before = _write_crlf_jsonl(legacy, [old_row])

    monkeypatch.setattr(guard, "DEFAULT_PUBLIC_DISPATCH_LEDGER", runtime)
    monkeypatch.setattr(guard, "LEGACY_PUBLIC_DISPATCH_LEDGER", legacy)

    guard.append_public_dispatch_ledger(
        ledger_path=guard.DEFAULT_PUBLIC_DISPATCH_LEDGER,
        platform="telegram",
        action="photo",
        run_id="run_new_2",
        topic_hash="new_topic_hash_2",
        payload_hash="new_payload_hash_2",
        canonical_url="https://capitalchronicle.substack.com/p/new-post-2",
        media_url="https://cdn.example.com/new-2.png",
        status="SUCCESS",
    )

    assert runtime.is_file()
    # Runtime file is strictly LF-only even though legacy source had CRLF.
    assert b"\r" not in runtime.read_bytes()
    # Legacy tracked repo file was NEVER modified.
    assert _sha256(legacy) == legacy_sha_before

    rows = guard.read_public_dispatch_ledger_rows()
    assert len(rows) == 2
    prior = guard.load_public_dispatch_hashes()
    assert {"old_payload_hash_1", "new_payload_hash_2"} <= prior["payload_hashes"]
    assert {"old_topic_hash_1", "new_topic_hash_2"} <= prior["topic_hashes"]

    # Post-cutover git-checkout simulation: legacy reverts to baseline subset, runtime keeps full history without duplication.
    _write_crlf_jsonl(legacy, [old_row])
    rows_after_checkout = guard.read_public_dispatch_ledger_rows()
    assert len(rows_after_checkout) == 2
    assert {r["payload_hash"] for r in rows_after_checkout} == {"old_payload_hash_1", "new_payload_hash_2"}


def test_dispatch_ledger_union_protects_history_even_if_runtime_was_created_without_seeding(tmp_path, monkeypatch):
    legacy = tmp_path / "repo" / "public_dispatch_duplicate_ledger_v6.jsonl"
    runtime = tmp_path / "runtime" / "public_dispatch_duplicate_ledger_v6.jsonl"
    _write_crlf_jsonl(legacy, [{"payload_hash": "legacy_only_hash", "topic_hash": "legacy_topic"}])
    runtime.parent.mkdir(parents=True, exist_ok=True)
    runtime.write_text(json.dumps({"payload_hash": "runtime_only_hash", "topic_hash": "runtime_topic"}) + "\n", encoding="utf-8")

    monkeypatch.setattr(guard, "DEFAULT_PUBLIC_DISPATCH_LEDGER", runtime)
    monkeypatch.setattr(guard, "LEGACY_PUBLIC_DISPATCH_LEDGER", legacy)

    prior = guard.load_public_dispatch_hashes()
    assert prior["payload_hashes"] == {"legacy_only_hash", "runtime_only_hash"}
    assert prior["topic_hashes"] == {"legacy_topic", "runtime_topic"}


def test_dispatch_ledger_explicit_custom_path_and_none_stay_strictly_isolated(tmp_path):
    custom = tmp_path / "isolated_ledger.jsonl"
    # Must NOT bleed repo legacy rows into an explicit tmp_path custom ledger.
    assert guard.read_public_dispatch_ledger_rows(custom) == []
    assert guard.load_public_dispatch_hashes(custom)["payload_hashes"] == set()
    assert guard.load_public_dispatch_hashes(None)["payload_hashes"] == set()

    # None append is a safe no-op.
    guard.append_public_dispatch_ledger(
        ledger_path=None,
        platform="telegram",
        action="post",
        run_id="r0",
        topic_hash="t0",
        payload_hash="p0",
    )
    assert not custom.exists()

    # Writing to explicit custom path writes ONLY the appended row (no repo seed bleed).
    guard.append_public_dispatch_ledger(
        ledger_path=custom,
        platform="telegram",
        action="post",
        run_id="r1",
        topic_hash="t1",
        payload_hash="p1",
    )
    assert b"\r" not in custom.read_bytes()
    rows = guard.read_public_dispatch_ledger_rows(custom)
    assert len(rows) == 1 and rows[0]["payload_hash"] == "p1"


# ---------------------------------------------------------------------------
# 3. Live Telemetry Registry & Post-Release Operator Governance
# ---------------------------------------------------------------------------


def test_telemetry_registry_fallback_auto_seed_lf_writes_and_secret_guard(tmp_path, monkeypatch):
    legacy = tmp_path / "repo" / "docs" / "automation" / "V6_LIVE_TELEMETRY" / "live_telemetry_registry_v6.jsonl"
    runtime = tmp_path / "runtime" / "v6_ledgers" / "live_telemetry" / "live_telemetry_registry_v6.jsonl"

    legacy_events = [
        {"event_id": "tel_old_1", "platform_id": "telegram", "action": "photo", "success": True, "latency_ms": 120.0},
        {"event_id": "tel_old_2", "platform_id": "x", "action": "post", "success": True, "latency_ms": 200.0},
    ]
    legacy_sha_before = _write_crlf_jsonl(legacy, legacy_events)

    monkeypatch.setattr(lt, "TELEMETRY_FILE", str(runtime))
    monkeypatch.setattr(lt, "TELEMETRY_DIR", str(runtime.parent))
    monkeypatch.setattr(lt, "LEGACY_TELEMETRY_FILE", str(legacy))

    # 1. Pre-cutover read-only query sees legacy events (with X readback normalization) and creates 0 files.
    reg = lt.TelemetryRegistry()
    events = reg.get_events()
    assert not runtime.exists()
    assert len(events) == 2
    assert events[1]["publication_state"] == "UNVERIFIED"
    assert events[1]["publication_confirmed"] is False

    # 2. Unsafe secret event fails BEFORE seeding or creating the runtime file.
    unsafe = lt.TelemetryEvent(
        platform_id="telegram",
        action="post",
        success=False,
        response_summary="token=123456:ABCdef123XYZ456_abc_def_ghi_jkl",
    )
    with pytest.raises(PlatformErrorSafetyError):
        reg.record_event(unsafe)
    assert not runtime.exists()

    # 3. Valid write via classify_and_record_dispatch auto-seeds Runtime (LF-only), appends new event, keeps legacy untouched.
    ev = lt.classify_and_record_dispatch(
        platform_id="discord",
        action="post",
        adapter_result={"status": "SUCCESS", "id": "msg_999"},
        latency_ms=85.0,
        payload_size_bytes=256,
    )
    assert ev.success is True
    assert runtime.is_file()
    assert b"\r" not in runtime.read_bytes()
    assert _sha256(legacy) == legacy_sha_before
    all_events = reg.get_events()
    assert len(all_events) == 3
    assert [e["platform_id"] for e in all_events] == ["telegram", "x", "discord"]

    # 4. Explicit custom registry_file stays 100% isolated from legacy.
    custom = tmp_path / "custom_telemetry.jsonl"
    custom_reg = lt.TelemetryRegistry(str(custom))
    assert custom_reg.get_events() == []
    custom_reg.record_event(lt.TelemetryEvent(platform_id="telegram", action="post", success=True))
    assert len(custom_reg.get_events()) == 1


def test_governance_audit_and_rotation_preserve_legacy_and_do_not_resurrect_rotated_lines(tmp_path, monkeypatch):
    legacy = tmp_path / "repo" / "docs" / "automation" / "V6_LIVE_TELEMETRY" / "live_telemetry_registry_v6.jsonl"
    runtime = tmp_path / "runtime" / "v6_ledgers" / "live_telemetry" / "live_telemetry_registry_v6.jsonl"

    legacy_rows = [
        {"event_id": f"tel_{i}", "platform_id": "telegram", "action": "photo", "success": True, "latency_ms": 100.0 + i}
        for i in range(6)
    ]
    legacy_sha_before = _write_crlf_jsonl(legacy, legacy_rows)

    monkeypatch.setattr(governance, "TELEMETRY_LOG_PATH", runtime)
    monkeypatch.setattr(governance, "LEGACY_TELEMETRY_LOG_PATH", legacy)
    monkeypatch.setattr(lt, "TELEMETRY_FILE", str(runtime))
    monkeypatch.setattr(lt, "LEGACY_TELEMETRY_FILE", str(legacy))

    # Pre-cutover audit falls back read-only to legacy with 0 runtime writes.
    pre_audit = governance.audit_telemetry_registry()
    assert pre_audit["exists"] is True and pre_audit["total_entries"] == 6
    assert not runtime.exists()

    # Rotate with max_lines=4: seeds runtime, archives 4 oldest lines into Runtime archive, keeps 2 newest in Runtime.
    rot = governance.rotate_telemetry_log(max_lines=4)
    assert rot == {"rotated": True, "archived_lines": 4}
    assert runtime.is_file()
    archive = runtime.parent / "live_telemetry_registry_v6_archive.jsonl"
    assert archive.is_file()
    assert b"\r" not in runtime.read_bytes()
    assert b"\r" not in archive.read_bytes()
    # Legacy tracked repo file is 100% untouched!
    assert _sha256(legacy) == legacy_sha_before

    # Post-rotation reads see ONLY the 2 kept Runtime events (rotated legacy lines are NOT resurrected).
    post_audit = governance.audit_telemetry_registry()
    assert post_audit["total_entries"] == 2
    assert post_audit["telemetry_archive"]["exists"] is True
    assert post_audit["telemetry_archive"]["total_entries"] == 4
    assert [e["event_id"] for e in lt.TelemetryRegistry().get_events()] == ["tel_4", "tel_5"]


# ---------------------------------------------------------------------------
# 4. Idempotent Operator Migration Helper & Downstream Preflight Integration
# ---------------------------------------------------------------------------


def test_migrate_all_v6_ledgers_dry_run_seed_idempotency_and_missing_row_merge(tmp_path):
    repo_root = tmp_path / "repo"
    runtime_root = tmp_path / "Runtime" / "ContentOps"

    legacy_dispatch = repo_root / v6_rt.LEGACY_PUBLIC_DISPATCH_LEDGER_REL
    legacy_telemetry = repo_root / v6_rt.LEGACY_LIVE_TELEMETRY_REL
    d_sha = _write_crlf_jsonl(legacy_dispatch, [
        {"record_type": "public_dispatch_payload", "payload_hash": "h1", "topic_hash": "t1"},
        {"record_type": "public_dispatch_payload", "payload_hash": "h2", "topic_hash": "t2"},
    ])
    t_sha = _write_crlf_jsonl(legacy_telemetry, [
        {"event_id": "e1", "platform_id": "telegram", "success": True},
        {"event_id": "e2", "platform_id": "discord", "success": False},
        {"event_id": "e3", "platform_id": "threads", "success": True},
    ])

    # 1. Dry-run makes zero writes.
    dry = v6_rt.migrate_all_v6_ledgers(runtime_root=runtime_root, repo_root=repo_root, dry_run=True)
    assert dry["public_dispatch_duplicate_ledger"]["status"] == "WOULD_SEED"
    assert dry["public_dispatch_duplicate_ledger"]["source_rows"] == 2
    assert dry["live_telemetry_registry"]["status"] == "WOULD_SEED"
    assert dry["live_telemetry_registry"]["source_rows"] == 3
    assert not (runtime_root / "v6_ledgers").exists()

    # 2. Real migration seeds both cleanly, LF-only, source_mutated=False.
    first = v6_rt.migrate_all_v6_ledgers(runtime_root=runtime_root, repo_root=repo_root, dry_run=False)
    assert first["public_dispatch_duplicate_ledger"]["status"] == "SEEDED"
    assert first["public_dispatch_duplicate_ledger"]["target_rows_after"] == 2
    assert first["public_dispatch_duplicate_ledger"]["source_mutated"] is False
    assert first["live_telemetry_registry"]["status"] == "SEEDED"
    assert first["live_telemetry_registry"]["target_rows_after"] == 3
    assert first["live_telemetry_registry"]["source_mutated"] is False
    assert _sha256(legacy_dispatch) == d_sha
    assert _sha256(legacy_telemetry) == t_sha

    rt_dispatch = Path(first["public_dispatch_duplicate_ledger"]["target_path"])
    rt_telemetry = Path(first["live_telemetry_registry"]["target_path"])
    assert b"\r" not in rt_dispatch.read_bytes()
    assert b"\r" not in rt_telemetry.read_bytes()

    # 3. Re-running migration is 100% idempotent (0 rows added, byte-identical).
    rt_d_sha = _sha256(rt_dispatch)
    rt_t_sha = _sha256(rt_telemetry)
    second = v6_rt.migrate_all_v6_ledgers(runtime_root=runtime_root, repo_root=repo_root, dry_run=False)
    assert second["public_dispatch_duplicate_ledger"]["status"] == "ALREADY_UP_TO_DATE"
    assert second["public_dispatch_duplicate_ledger"]["rows_added"] == 0
    assert second["live_telemetry_registry"]["status"] == "ALREADY_PRESENT_UNTOUCHED"
    assert _sha256(rt_dispatch) == rt_d_sha
    assert _sha256(rt_telemetry) == rt_t_sha

    # 4. If a late legacy dispatch row appears, migrate_v6_ledger unions ONLY the missing row non-destructively.
    _write_crlf_jsonl(legacy_dispatch, [
        {"record_type": "public_dispatch_payload", "payload_hash": "h1", "topic_hash": "t1"},
        {"record_type": "public_dispatch_payload", "payload_hash": "h2", "topic_hash": "t2"},
        {"record_type": "public_dispatch_payload", "payload_hash": "h3_late", "topic_hash": "t3_late"},
    ])
    merged = v6_rt.migrate_v6_ledger(runtime_path=rt_dispatch, legacy_path=legacy_dispatch, union_if_exists=True)
    assert merged["status"] == "MERGED_MISSING_ROWS"
    assert merged["rows_added"] == 1
    assert merged["target_rows_after"] == 3
    assert b"\r" not in rt_dispatch.read_bytes()


def test_downstream_permissive_mode_uses_runtime_fallback_without_mutating_legacy(tmp_path, monkeypatch):
    legacy = tmp_path / "repo" / "public_dispatch_duplicate_ledger_v6.jsonl"
    runtime = tmp_path / "runtime" / "public_dispatch_duplicate_ledger_v6.jsonl"
    _write_crlf_jsonl(legacy, [{"topic_hash": "abc123", "duplicate_family": "oil_test"}])

    monkeypatch.setattr(guard, "DEFAULT_PUBLIC_DISPATCH_LEDGER", runtime)
    monkeypatch.setattr(guard, "LEGACY_PUBLIC_DISPATCH_LEDGER", legacy)
    monkeypatch.setattr(permissive, "DEFAULT_DUPLICATE_LEDGER", runtime)

    rows = permissive.load_duplicate_ledger(permissive.DEFAULT_DUPLICATE_LEDGER)
    assert len(rows) == 1 and rows[0]["topic_hash"] == "abc123"
    assert not runtime.exists()
