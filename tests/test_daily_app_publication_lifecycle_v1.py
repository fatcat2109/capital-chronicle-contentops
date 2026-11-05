"""Final Daily App supervisor: production-epoch immutability and kill-switch reporting.

The supervisor-run publication lifecycle cases moved off the live path (see the CC-288 note);
the live publication rules are tested in tests/test_publication_coordinator_v1.py.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from live_contentops.daily_app_supervisor_v1 import (
    ContentOpsDailyAppSupervisor,
    ProductionEpochConflictError,
    STATUS_DISPATCH_CONFIRMED,
)
from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
)

WINDOW_START = datetime(2026, 8, 10, 13, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 8, 10, 15, tzinfo=timezone.utc)
INSIDE_WINDOW = datetime(2026, 8, 10, 14, tzinfo=timezone.utc)

EPOCH_A = "2026-08-09T13:27:00.663942Z"
EPOCH_DIFFERENT = "2026-08-09T14:00:00.000000Z"


def _fixed_clock(dt):
    return lambda: dt


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------


def _plan_cycle(destinations=("substack",), package_identity="pkg-1"):
    def cycle(*, run_id, output_dir, cutoff_utc, publication_enabled, **kwargs):
        root = Path(output_dir)
        body = f"# Governed lifecycle fixture {run_id}\n\nEvidence-bound final analysis."
        identity = hashlib.sha256(body.encode("utf-8")).hexdigest()
        governed_hash = hashlib.sha256(f"governed-{run_id}".encode()).hexdigest()

        def write_json(name, value):
            root.mkdir(parents=True, exist_ok=True)
            (root / name).write_text(json.dumps(value), encoding="utf-8")

        write_json(
            "article_manifest_v1.json",
            {
                "title": f"Governed lifecycle fixture {run_id}",
                "substack_body_markdown": body,
                "resolved_article_mode": "STANDARD_NEWS_ANALYSIS",
                "institutional_edge_editorial_validation": {"classification": "PASS"},
            },
        )
        write_json(
            "grounded_support_v1.json",
            {
                "status": "PASS",
                "targeted_evidence": {
                    "evidence_documents": [{"evidence_id": f"evidence-{run_id}"}]
                },
            },
        )
        write_json("media_manifest_v1.json", {"status": "PASS"})
        write_json("editorial_quality_gate_v1.json", {"classification": "PASS"})
        write_json(
            "native_payloads_rehearsal_v1.json",
            {
                destination: {"text": destination}
                for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS
            },
        )
        write_json(
            "release_candidate_lock_v1.json",
            {
                "article_body_sha256": identity,
                "source_packet_sha256": hashlib.sha256(
                    f"source-{run_id}".encode()
                ).hexdigest(),
                "payload_sha256": {
                    destination: hashlib.sha256(destination.encode()).hexdigest()
                    for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS
                },
                "public_write_performed": False,
            },
        )
        write_json(
            "no_write_rehearsal_v1.json",
            {"classification": "PASS_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL"},
        )
        write_json(
            "rolling_x_grounded_article_media_v1.json",
            {
                "editorial_worker_receipt": {
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "HIGH",
                    "fresh": True,
                    "isolated": True,
                    "resume_existing": False,
                    "governed_input_hash": governed_hash,
                    "bounded_revision_count": 0,
                    "public_write_attempted": False,
                },
                "editorial_worker_validation": {"coordinator_resumes": True},
            },
        )
        return {
            "run_id": run_id,
            "classification": "PASS_PUBLICATION_PLAN_READY",
            "editorial_worker_routing": {"governed_input_hash": governed_hash},
            "publication_lifecycle_plan": {
                "ready_destinations": list(destinations),
                "package_identity": package_identity,
                "article_identity": identity,
                "story_identity": f"story-{run_id}",
                "update_chain_identity": f"chain-{run_id}",
                "resolved_article_mode": "STANDARD_NEWS_ANALYSIS",
                "required_derivative_destinations": list(
                    V1_REQUIRED_DERIVATIVE_DESTINATIONS
                ),
                "destinations": [
                    {"destination": "substack"},
                    *[
                        {"destination": destination}
                        for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS
                    ],
                ],
            },
            "public_write_performed": False,
            "unknown_write_detected": False,
        }

    return cycle


def _publisher(status="DISPATCH_CONFIRMED", public_object_id="obj-1", raise_exc=None, calls=None):
    def publisher(destination, package_identity):
        if calls is not None:
            calls.append((destination, package_identity))
        if raise_exc is not None:
            raise raise_exc
        result = {"status": status}
        if public_object_id is not None:
            result["public_object_id"] = public_object_id
        return result

    return publisher


def _readback(
    *,
    verified=True,
    public_object_id="obj-1",
    mismatch_dispatch=False,
    mismatch_destination=False,
    mismatch_object=False,
    raise_exc=None,
    empty=False,
    calls=None,
    write_occurred=None,
):
    def provider(dispatch_id, destination, expected_object):
        if calls is not None:
            calls.append((dispatch_id, destination, expected_object))
        if raise_exc is not None:
            raise raise_exc
        if empty:
            return {}
        payload = {
            "verified": verified,
            "dispatch_id": ("OTHER-DISPATCH" if mismatch_dispatch else dispatch_id),
            "destination": ("OTHER-DEST" if mismatch_destination else destination),
            "public_object_id": ("OTHER-OBJ" if mismatch_object else public_object_id),
        }
        if write_occurred is not None:
            payload["write_occurred"] = write_occurred
        return payload

    return provider


def _life(
    tmp_path,
    *,
    publisher,
    readback,
    clock=None,
    destinations=("substack",),
    package_identity="pkg-1",
    mode="AUTONOMOUS_DEFAULT",
    enable=True,
):
    return ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "life.sqlite3",
        output_root=tmp_path / "out",
        operating_mode=mode,
        clock=clock or _fixed_clock(INSIDE_WINDOW),
        newsroom_cycle=_plan_cycle(destinations=destinations, package_identity=package_identity),
        publication_publisher=publisher,
        publication_readback_provider=readback,
        enable_publication_lifecycle=enable,
    )


def _window_id(store):
    conn = store.get_connection()
    try:
        row = conn.execute(
            "SELECT work_item_id FROM work_items ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        return row["work_item_id"] if row else None
    finally:
        conn.close()




# --------------------------------------------------------------------------------------
# Production epoch immutability
# --------------------------------------------------------------------------------------


def _epoch_supervisor(tmp_path, epoch, clock=None):
    return ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "epoch.sqlite3",
        output_root=tmp_path / "out",
        clock=clock or _fixed_clock(INSIDE_WINDOW),
        newsroom_cycle=lambda **kwargs: {"classification": "NO_PUBLICATION"},
        production_epoch_start_utc=epoch,
    )


def test_epoch_initialized_once(tmp_path):
    sup = _epoch_supervisor(tmp_path, EPOCH_A)
    assert sup.production_epoch_start_utc == EPOCH_A
    assert sup._load_production_epoch() is not None


def test_same_epoch_restart_passes(tmp_path):
    _epoch_supervisor(tmp_path, EPOCH_A)
    # Restart supplying the exact same epoch -> idempotent PASS, no conflict.
    sup = _epoch_supervisor(tmp_path, EPOCH_A)
    assert sup.production_epoch_start_utc == EPOCH_A


def test_conflicting_epoch_fails_closed(tmp_path):
    _epoch_supervisor(tmp_path, EPOCH_A)
    with pytest.raises(ProductionEpochConflictError):
        _epoch_supervisor(tmp_path, EPOCH_DIFFERENT)


def test_conflicting_epoch_does_not_mutate_persisted(tmp_path):
    before = _epoch_supervisor(tmp_path, EPOCH_A)._load_production_epoch()
    try:
        _epoch_supervisor(tmp_path, EPOCH_DIFFERENT)
    except ProductionEpochConflictError:
        pass
    after = _epoch_supervisor(tmp_path, None)._load_production_epoch()
    assert before == after


def test_epoch_survives_restart_without_config(tmp_path):
    _epoch_supervisor(tmp_path, EPOCH_A)
    restarted = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "epoch.sqlite3",
        output_root=tmp_path / "out",
        clock=_fixed_clock(INSIDE_WINDOW),
        newsroom_cycle=lambda **kwargs: {"classification": "NO_PUBLICATION"},
    )
    assert restarted.production_epoch_start_utc == EPOCH_A


def test_conflict_error_reports_both_instances(tmp_path):
    _epoch_supervisor(tmp_path, EPOCH_A)
    with pytest.raises(ProductionEpochConflictError) as exc:
        _epoch_supervisor(tmp_path, EPOCH_DIFFERENT)
    msg = str(exc.value)
    assert "13:27:00.663942" in msg
    assert "14:00:00" in msg


# CC-288: the supervisor-run publication lifecycle cases were removed (readback verification,
# controlled no-write, UNKNOWN_WRITE recovery, kill-switch recovery and restart idempotency through
# tick()). They drove ContentOpsDailyAppSupervisor's own window execution and
# drive_canonical_publication_lifecycle, which the live runtime no longer reaches: production_runtime_v1
# binds the routine owner NATIVE_CODEX_DESKTOP (3e69658a, 20 Oct), so _due_windows and _execute_window
# never run a window, and it passes publication_coordinator, so a plan goes to
# DurablePublicationCoordinator.publish_plan. The coordinator's tests guard the same rules on the live
# path (tests/test_publication_coordinator_v1.py: unknown writes read back and never retried, kill
# switch before any send, restart never republishes, exact readback identity).


# --------------------------------------------------------------------------------------
# Kill switch safety
# --------------------------------------------------------------------------------------


def test_kill_switch_blocks_new_dispatch(tmp_path):
    sup = _life(
        tmp_path,
        publisher=_publisher(STATUS_DISPATCH_CONFIRMED, "obj-1"),
        readback=_readback(verified=True, public_object_id="obj-1"),
        mode="KILL_SWITCH",
    )
    report = sup.tick(now=INSIDE_WINDOW)
    assert report["kill_switch_active"] is True
    assert report["windows_dispatched"] == 0
    assert _window_id(sup._store) is None  # no work item created under kill switch
