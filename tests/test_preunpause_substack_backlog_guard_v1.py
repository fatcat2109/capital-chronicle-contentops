"""Hermetic adversarial tests for Substack plan_analysis_page staleness guard & pre-unpause outbox CLI.

Covers Cycle #31 / CC-692 requirements:
- Subgroup A (#13 outbox_33a7...): expired un-dispatched READY Substack plan_analysis_page auto-expires
  in recover_pending(), unblocking new Substack articles instead of BLOCKED_SAFE_RECOVERY_BACKLOG_REMAINS.
- Boundary precision: 1 second before entry_deadline_utc -> NOT expired; exact deadline -> expired.
- Active non-expired Substack plan_analysis_page -> NOT expired.
- Closed-plan page with final_status bound -> NOT spuriously expired on entry_deadline_utc.
- Non-plan Substack articles (regular article, wrap, digest) -> NEVER expired by plan guard.
- Subgroup B (#14 dispatch_4f58...): DISPATCH_ATTEMPT_STARTED / UNKNOWN_WRITE / RECONCILED_ABSENT_SAFE_TO_RETRY
  Substack rows preserve readback-first and no-auto-retry guarantees; NEVER auto-retired without durable
  verified absence proof.
- CLI scripts/reconcile_preunpause_outbox_v1.py: strict --dry-run default (byte-exact zero mutation),
  fail-closed interlocks (restored.json, active lease, fresh heartbeat, lock file, live process),
  clean idempotent --apply on scratch SQLite fixture across Subgroups A/B/D, expired derivatives,
  dead-parent UNKNOWN_WRITE polling targets (O56/O58/O60/O61), and opt-in --retire-cc603-backfill.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import reconcile_preunpause_outbox_v1 as cli  # noqa: E402
from live_contentops.destination_transport_registry_v1 import (  # noqa: E402
    REGISTRY_VERSION,
    registration_for_destination,
)
from live_contentops.durable_operational_store_v1 import (  # noqa: E402
    ContentOpsDurableStore,
)
from live_contentops.publication_coordinator_v1 import (  # noqa: E402
    ATTEMPT_STARTED,
    DERIVATIVE_EXPIRED_STALE_NO_WRITE,
    DISPATCH_CONFIRMED,
    DurablePublicationCoordinator,
    NATIVE_NEO_PENDING,
    PLAN_PAGE_EXPIRED_STALE_NO_WRITE,
    RECONCILED_ABSENT_SAFE_TO_RETRY,
    RECONCILED_CONFIRMED,
    UNKNOWN_WRITE,
    substack_plan_page_staleness,
)


@pytest.fixture(autouse=True)
def _no_article_media_for_synthetic_transport_tests(monkeypatch):
    """Synthetic coordinator fixtures have no media files on disk (mirrors test_publication_coordinator_v1)."""
    from live_contentops import publication_image_contract_v1

    monkeypatch.setattr(publication_image_contract_v1, "validate_write", lambda *args, **kwargs: None)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _set_operating_mode(store: ContentOpsDurableStore, mode: str) -> None:
    current = store.get_operating_control()
    if current["operating_mode"] != mode:
        store.update_operating_control(
            expected_state_version=int(current["state_version"]),
            operating_mode=mode,
            control_source="CONTROLLED_TEST",
        )


def _set_autonomous_mode(store: ContentOpsDurableStore) -> None:
    _set_operating_mode(store, "AUTONOMOUS_DEFAULT")


class _RecordingTransport:
    def __init__(self, *, readback_status: str = "AMBIGUOUS"):
        self.publish_calls: list[tuple[str, str]] = []
        self.readback_calls: list[tuple[str, str]] = []
        self.readback_status = readback_status

    def publish(self, *, destination, intent, authorization_context, **kwargs):
        work_item_id = str(intent["work_item_id"])
        self.publish_calls.append((destination, work_item_id))
        if destination == "substack":
            slug = work_item_id.lower().replace("_", "-")
            return {
                "status": "SUCCESS",
                "id": f"sub-{work_item_id}",
                "public_url": f"https://capitalchronicle.substack.com/p/{slug}",
                "observed_published_at_utc": "2026-11-29T18:05:00Z",
            }
        return {
            "status": "SUCCESS",
            "id": f"{destination}-{work_item_id}",
            "public_url": f"https://example.test/{destination}/{work_item_id}",
        }

    def readback(self, *, destination, public_object_id, public_object_url, intent):
        work_item_id = str(intent["work_item_id"])
        self.readback_calls.append((destination, work_item_id))
        if self.readback_status == "CONFIRMED":
            observed_id = public_object_id or f"sub-{work_item_id}"
            observed_url = (
                public_object_url
                or f"https://capitalchronicle.substack.com/p/{work_item_id.lower().replace('_', '-')}"
            )
            return {
                "status": "SUCCESS",
                "verified": True,
                "public_object_id": observed_id,
                "public_object_url": observed_url,
            }
        if self.readback_status == "ABSENT":
            return {
                "status": "ABSENT",
                "write_absent": True,
                "write_exists": False,
                "verified": False,
            }
        if self.readback_status == "EXISTS_INCOMPLETE":
            observed_id = public_object_id or f"sub-{work_item_id}"
            observed_url = (
                public_object_url
                or f"https://capitalchronicle.substack.com/p/{work_item_id.lower().replace('_', '-')}"
            )
            return {
                "status": "PARTIAL",
                "verified": False,
                "write_absent": False,
                "write_exists": True,
                "public_object_id": observed_id,
                "public_object_url": observed_url,
            }
        return {
            "status": "AMBIGUOUS",
            "verified": False,
        }


def _make_substack_plan(
    work_item_id: str,
    *,
    payload_text: str = "Conditional plan analysis.",
    output_dir: Path | str | None = None,
) -> dict:
    reg = registration_for_destination("substack")
    plan = {
        "schema_version": "contentops.publication_plan.v1",
        "story_identity": work_item_id,
        "article_identity": work_item_id,
        "package_identity": work_item_id,
        "transport_registry_version": REGISTRY_VERSION,
        "policy_mode_version": "AUTONOMOUS_DEFAULT:TEST",
        "publication_window": {"window_identity": work_item_id},
        "destinations": [
            {
                "destination": "substack",
                "platform": reg.platform,
                "surface": reg.surface,
                "transport_type": reg.transport_type,
                "transport_registry_version": REGISTRY_VERSION,
                "payload": payload_text,
                "payload_hash": hashlib.sha256(payload_text.encode("utf-8")).hexdigest(),
                "canonical_url": f"https://capitalchronicle.substack.com/p/{work_item_id}",
                "canonical_url_dependency": reg.canonical_url_dependency,
                "expected_destination_identity": reg.expected_identity,
                "readiness_state": "READY_AUTHENTICATED",
            }
        ],
    }
    if output_dir is not None:
        plan["output_dir"] = str(output_dir)
    plan["plan_hash"] = hashlib.sha256(
        json.dumps(plan, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return plan


def _seed_plan_analysis_page(
    store: ContentOpsDurableStore,
    *,
    plan_id: str,
    entry_deadline_utc: str | None,
    expires_at_utc: str | None = None,
    source_status: str = "WAITING",
    final_status: dict | None = None,
    parent_status: str = "EDITORIAL_INTERNAL",
    outbox_status: str = "READY",
    dispatch_status: str | None = None,
    reconciliation_status: str | None = None,
    ambiguous_readback: bool = False,
    override_intent_plan_hash: str | None = None,
    created_at: str = "2026-11-23T02:55:03.895027+00:00",
    public_object_id: str | None = None,
    public_object_url: str | None = None,
    publication_window_override: dict | None = None,
) -> dict[str, str]:
    page_id = f"plan-analysis-{plan_id}"
    reg = registration_for_destination("substack")
    body = f"Bearish plan analysis for {plan_id}."
    plan = {
        "schema_version": "contentops.publication_plan.v1",
        "plan_analysis_page": page_id,
        "story_identity": page_id,
        "article_identity": page_id,
        "package_identity": page_id,
        "output_dir": str(Path(store.db_path).parent),
        "transport_registry_version": REGISTRY_VERSION,
        "policy_mode_version": "AUTONOMOUS_DEFAULT:JIM_DECISION_113",
        "publication_window": publication_window_override or {"window_identity": page_id},
        "destinations": [
            {
                "destination": "substack",
                "surface": reg.surface,
                "transport_type": reg.transport_type,
                "payload": body,
                "payload_hash": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            }
        ],
    }
    plan["plan_hash"] = hashlib.sha256(
        json.dumps(plan, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    source_plan = {
        "plan_id": plan_id,
        "asset_id": "XAUUSD",
        "status": source_status,
        "registered_at_utc": "2026-11-23T02:43:45.942914Z",
        "zone": {"minimum": 3557.0, "maximum": 3566.0},
    }
    if entry_deadline_utc is not None:
        source_plan["entry_deadline_utc"] = entry_deadline_utc
    if expires_at_utc is not None:
        source_plan["expires_at_utc"] = expires_at_utc

    packet = {
        "schema_version": "contentops.plan_analysis_page.v1",
        "page_id": page_id,
        "plan_id": plan_id,
        "source_plan": source_plan,
        "plan": plan,
        "native_payload": {"title": f"Gold plan {plan_id}", "subtitle": "Sub", "body_markdown": body},
    }
    if final_status is not None:
        packet["final_status"] = final_status

    store.create_work_item(
        story_id=page_id,
        work_item_id=page_id,
        title=f"Plan page {plan_id}",
        target_surface="SUBSTACK_ARTICLE",
    )
    store.register_outbox_message(
        message_id=page_id,
        work_item_id=page_id,
        destination="internal:plan-analysis-page",
        payload=json.dumps(packet, sort_keys=True),
        status=parent_status,
    )

    intent_plan_hash = override_intent_plan_hash or plan["plan_hash"]
    ids = DurablePublicationCoordinator._ids(page_id, intent_plan_hash, "substack")
    intent = {
        "schema_version": "contentops.prewrite_intent.v1",
        "work_item_id": page_id,
        "plan_hash": intent_plan_hash,
        "plan_analysis_page": page_id,
        "story_identity": page_id,
        "article_identity": page_id,
        "package_identity": page_id,
        "resolved_article_mode": None,
        "publication_window": publication_window_override or {"window_identity": page_id},
        "destination_plan": {**plan["destinations"][0], "substack_delivery_mode": "WEB_ONLY"},
        "payload": body,
        "native_payload": packet["native_payload"],
        "transport_registry_version": REGISTRY_VERSION,
        "attempt_identity": ids["dispatch_id"],
    }
    store.register_outbox_message(
        message_id=ids["message_id"],
        work_item_id=page_id,
        destination="substack",
        payload=json.dumps(intent, sort_keys=True),
        status=outbox_status,
    )
    with closing(store.get_connection()) as conn:
        conn.execute(
            "UPDATE outbox_messages SET created_at=? WHERE message_id=?",
            (created_at, ids["message_id"]),
        )
        conn.commit()

    if dispatch_status is not None:
        store.register_platform_dispatch(
            dispatch_id=ids["dispatch_id"],
            message_id=ids["message_id"],
            platform="substack",
            status=dispatch_status,
            public_object_id=public_object_id,
            public_object_url=public_object_url,
        )
    if reconciliation_status is not None:
        store.register_reconciliation(
            reconciliation_id=ids["reconciliation_id"],
            work_item_id=page_id,
            status=reconciliation_status,
        )
    if ambiguous_readback:
        store.register_readback(
            readback_id="rb_ambig_" + ids["dispatch_id"],
            dispatch_id=ids["dispatch_id"],
            readback_data=json.dumps(
                {
                    "readback": {
                        "verified": False,
                        "write_absent": False,
                        "write_exists": False,
                        "status": "AMBIGUOUS",
                    }
                }
            ),
        )
    return {"page_id": page_id, **ids}


# ---------------------------------------------------------------------------
# Part 1 — DurablePublicationCoordinator Substack Plan Backlog Guard Tests
# ---------------------------------------------------------------------------


def test_expired_substack_plan_page_auto_expires_and_unblocks_new_substack_article(tmp_path):
    """Reproduces Cycle #31 #13 (outbox_33a7...): expired READY Substack plan page must not block."""
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    _set_autonomous_mode(store)
    seeded = _seed_plan_analysis_page(
        store,
        plan_id="plan_7c24bb53fe8d2a2845e98583",
        entry_deadline_utc="2026-11-23T20:00:00Z",
        expires_at_utc="2026-11-23T20:00:00Z",
    )
    original_payload = store.get_outbox_message(seeded["message_id"])["payload"]

    # Boundary check: 1 second BEFORE entry_deadline_utc => NOT stale.
    msg = store.get_outbox_message(seeded["message_id"])
    intent = json.loads(msg["payload"])
    stale_before, reason_before = substack_plan_page_staleness(
        store.get_outbox_message,
        msg,
        intent,
        now=datetime(2026, 11, 23, 19, 59, 59, tzinfo=timezone.utc),
    )
    assert (stale_before, reason_before) == (False, None)

    # Exact deadline boundary => stale.
    stale_exact, reason_exact = substack_plan_page_staleness(
        store.get_outbox_message,
        msg,
        intent,
        now=datetime(2026, 11, 23, 20, 0, 0, tzinfo=timezone.utc),
    )
    assert stale_exact is True
    assert reason_exact == "SUBSTACK_PLAN_ENTRY_DEADLINE_PASSED"

    # At relaunch clock (2026-11-29T18:00:00Z), execute_plan runs recover_pending preflight,
    # expires #13 cleanly, and unblocks publication of the new Substack article!
    transport = _RecordingTransport(readback_status="CONFIRMED")
    relaunch_now = datetime(2026, 11, 29, 18, 0, 0, tzinfo=timezone.utc)
    coordinator = DurablePublicationCoordinator(
        store=store,
        transport_runtime=transport,
        readiness_provider=lambda _: {"readiness_state": "READY_AUTHENTICATED"},
        clock=lambda: relaunch_now,
    )

    store.create_work_item(
        story_id="fresh-article-1",
        work_item_id="fresh-article-1",
        title="Fresh Post-Relaunch Article",
        target_surface="SUBSTACK_ARTICLE",
    )
    fresh_plan = _make_substack_plan("fresh-article-1", payload_text="Fresh market note.")
    result = coordinator.execute_plan("fresh-article-1", fresh_plan)

    assert result["distribution_status"] != "BLOCKED_SAFE_RECOVERY_BACKLOG_REMAINS"
    assert result["canonical_article_real_published"] is True
    # Exact expired row retired with zero dispatch row, immutable payload bytes, and RECOVERY_AUDIT incident.
    expired_row = store.get_outbox_message(seeded["message_id"])
    assert expired_row["status"] == PLAN_PAGE_EXPIRED_STALE_NO_WRITE
    assert expired_row["payload"] == original_payload
    assert store.get_platform_dispatch(seeded["dispatch_id"]) is None
    with closing(store.get_read_only_connection()) as conn:
        audit_row = conn.execute(
            "SELECT severity, description FROM incidents WHERE work_item_id=? AND severity='RECOVERY_AUDIT'",
            (seeded["page_id"],),
        ).fetchone()
    assert audit_row is not None
    audit_desc = json.loads(audit_row["description"])
    assert audit_desc["status"] == PLAN_PAGE_EXPIRED_STALE_NO_WRITE
    assert audit_desc["cause"] == "SUBSTACK_PLAN_ENTRY_DEADLINE_PASSED"
    assert audit_desc["public_write_performed"] is False
    # Transport NEVER published the expired plan; published ONLY the fresh article.
    assert transport.publish_calls == [("substack", "fresh-article-1")]

    # Verify recover_pending() summary shape directly on a second expired READY Substack plan page.
    seeded2 = _seed_plan_analysis_page(
        store,
        plan_id="plan_second_expired_check",
        entry_deadline_utc="2026-11-24T15:00:00Z",
    )
    recovery2 = coordinator.recover_pending()
    assert recovery2["stale_expired"] == 1
    assert recovery2["backlog_remaining"] == 0
    assert recovery2["stale_plan_pages_expired"] == [
        {
            "message_id": seeded2["message_id"],
            "work_item_id": seeded2["page_id"],
            "reason": "SUBSTACK_PLAN_ENTRY_DEADLINE_PASSED",
        }
    ]
    assert store.get_outbox_message(seeded2["message_id"])["status"] == PLAN_PAGE_EXPIRED_STALE_NO_WRITE
    assert store.get_platform_dispatch(seeded2["dispatch_id"]) is None

    # Direct _dispatch_message on the already-expired row stays fail-closed with 0 writes.
    direct_outcome = coordinator._dispatch_message(expired_row, canonical_url=None)
    assert direct_outcome["status"] == PLAN_PAGE_EXPIRED_STALE_NO_WRITE
    assert direct_outcome["publish_called"] is False
    assert transport.publish_calls == [("substack", "fresh-article-1")]


def test_active_non_expired_substack_plan_page_is_not_expired(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    _set_autonomous_mode(store)
    seeded = _seed_plan_analysis_page(
        store,
        plan_id="plan_active_future",
        entry_deadline_utc="2026-11-30T20:00:00Z",
        expires_at_utc="2026-11-30T20:00:00Z",
    )
    now = datetime(2026, 11, 29, 18, 0, 0, tzinfo=timezone.utc)
    transport = _RecordingTransport(readback_status="CONFIRMED")
    # Put store in KILL_SWITCH so recover_pending checks staleness without attempting live write
    # and we verify the row remains READY and NOT expired.
    _set_operating_mode(store, "KILL_SWITCH")
    coordinator = DurablePublicationCoordinator(
        store=store,
        transport_runtime=transport,
        readiness_provider=lambda _: {"readiness_state": "READY_AUTHENTICATED"},
        clock=lambda: now,
    )
    recovery = coordinator.recover_pending()

    assert recovery["stale_expired"] == 0
    assert recovery["backlog_remaining"] == 1
    assert store.get_outbox_message(seeded["message_id"])["status"] == "READY"
    assert transport.publish_calls == []


def test_non_plan_substack_articles_and_closed_plan_pages_are_preserved(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    now = datetime(2026, 11, 29, 18, 0, 0, tzinfo=timezone.utc)
    transport = _RecordingTransport()

    # 1. Non-plan Substack article (even with old created_at & expired window on non-plan article).
    store.create_work_item(
        story_id="regular-wrap",
        work_item_id="regular-wrap",
        title="Regular Weekly Wrap",
        target_surface="SUBSTACK_ARTICLE",
    )
    regular_plan = _make_substack_plan("regular-wrap", payload_text="Weekly market wrap.")
    regular_plan["publication_window"] = {
        "window_identity": "regular-wrap",
        "expires_at_utc": "2026-11-22T18:00:00Z",
    }
    coordinator = DurablePublicationCoordinator(
        store=store,
        transport_runtime=transport,
        readiness_provider=lambda _: {"readiness_state": "READY_AUTHENTICATED"},
        clock=lambda: now,
    )
    reg = coordinator.register_plan("regular-wrap", regular_plan)["registered"][0]

    # 2. Closed-plan analysis page with final_status explicitly bound.
    closed_page = _seed_plan_analysis_page(
        store,
        plan_id="plan_closed_record",
        entry_deadline_utc="2026-11-23T20:00:00Z",
        final_status={"status": "EXPIRED", "status_at_utc": "2026-11-23T20:01:00Z"},
    )

    _set_operating_mode(store, "KILL_SWITCH")
    recovery = coordinator.recover_pending()
    assert recovery["stale_expired"] == 0
    assert recovery["backlog_remaining"] == 2
    assert store.get_outbox_message(reg["message_id"])["status"] == "READY"
    assert store.get_outbox_message(closed_page["message_id"])["status"] == "READY"
    assert transport.publish_calls == []


def test_substack_dispatch_attempt_started_and_reconciled_absent_never_auto_retired_or_retried(tmp_path):
    """Reproduces Cycle #31 #14 (dispatch_4f58...) and Substack RECONCILED_ABSENT safety."""
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    _set_autonomous_mode(store)

    # #14: DISPATCH_ATTEMPT_STARTED on expired plan -> MUST become UNKNOWN_WRITE + readback only.
    seeded_14 = _seed_plan_analysis_page(
        store,
        plan_id="plan_1d9bc560342b94e3d5a0cdb1",
        entry_deadline_utc="2026-11-23T19:45:00Z",
        outbox_status="READY",
        dispatch_status=ATTEMPT_STARTED,
    )
    # Historical Substack RECONCILED_ABSENT_SAFE_TO_RETRY -> MUST NOT auto-retry or auto-expire.
    seeded_absent = _seed_plan_analysis_page(
        store,
        plan_id="plan_1ff14f488bdc84b20a3f51d2",
        entry_deadline_utc="2026-11-11T18:00:00Z",
        outbox_status=RECONCILED_ABSENT_SAFE_TO_RETRY,
        dispatch_status=RECONCILED_ABSENT_SAFE_TO_RETRY,
        reconciliation_status=RECONCILED_ABSENT_SAFE_TO_RETRY,
    )

    transport = _RecordingTransport(readback_status="AMBIGUOUS")
    coordinator = DurablePublicationCoordinator(
        store=store,
        transport_runtime=transport,
        readiness_provider=lambda _: {"readiness_state": "READY_AUTHENTICATED"},
        clock=lambda: datetime(2026, 11, 29, 18, 0, 0, tzinfo=timezone.utc),
    )

    recovery = coordinator.recover_pending()

    assert recovery["stale_expired"] == 0
    assert recovery["publish_calls"] == 0
    assert recovery["marked_unknown"] == 1
    assert recovery["readbacks"] == 1
    assert transport.publish_calls == []
    assert transport.readback_calls == [("substack", seeded_14["page_id"])]
    # #14 stays UNKNOWN_WRITE pending verified readback; never dropped or retired.
    assert store.get_platform_dispatch(seeded_14["dispatch_id"])["status"] == UNKNOWN_WRITE
    assert store.get_outbox_message(seeded_14["message_id"])["status"] == UNKNOWN_WRITE
    # Reconciled-absent Substack stays untouched.
    assert (
        store.get_platform_dispatch(seeded_absent["dispatch_id"])["status"]
        == RECONCILED_ABSENT_SAFE_TO_RETRY
    )
    assert (
        store.get_outbox_message(seeded_absent["message_id"])["status"]
        == RECONCILED_ABSENT_SAFE_TO_RETRY
    )


def test_adversarial_plan_staleness_edge_cases(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    now = datetime(2026, 11, 29, 18, 0, 0, tzinfo=timezone.utc)

    # 1. Unparseable deadline fails closed.
    bad_deadline = _seed_plan_analysis_page(
        store, plan_id="plan_bad_ts", entry_deadline_utc="not-a-timestamp"
    )
    msg = store.get_outbox_message(bad_deadline["message_id"])
    stale, reason = substack_plan_page_staleness(
        store.get_outbox_message, msg, json.loads(msg["payload"]), now=now
    )
    assert stale is True and reason == "SUBSTACK_PLAN_DEADLINE_UNPARSEABLE:entry_deadline_utc"

    # 2. Superseded plan_hash fails closed.
    superseded = _seed_plan_analysis_page(
        store,
        plan_id="plan_superseded",
        entry_deadline_utc="2026-12-05T20:00:00Z",
        override_intent_plan_hash="0" * 64,
    )
    msg2 = store.get_outbox_message(superseded["message_id"])
    stale2, reason2 = substack_plan_page_staleness(
        store.get_outbox_message, msg2, json.loads(msg2["payload"]), now=now
    )
    assert stale2 is True and reason2 == "SUBSTACK_PLAN_SUPERSEDED_REVISION"

    # 3. Parent packet already SETTLED fails closed.
    settled_parent = _seed_plan_analysis_page(
        store,
        plan_id="plan_parent_settled",
        entry_deadline_utc="2026-12-05T20:00:00Z",
        parent_status="SETTLED",
    )
    msg3 = store.get_outbox_message(settled_parent["message_id"])
    stale3, reason3 = substack_plan_page_staleness(
        store.get_outbox_message, msg3, json.loads(msg3["payload"]), now=now
    )
    assert stale3 is True and reason3 == "SUBSTACK_PLAN_PARENT_TERMINAL:SETTLED"

    # 4. Terminal source_plan status without final_status even before entry_deadline_utc.
    cancelled_open = _seed_plan_analysis_page(
        store,
        plan_id="plan_cancelled_open",
        entry_deadline_utc="2026-12-05T20:00:00Z",
        source_status="CANCELLED",
    )
    msg4 = store.get_outbox_message(cancelled_open["message_id"])
    stale4, reason4 = substack_plan_page_staleness(
        store.get_outbox_message, msg4, json.loads(msg4["payload"]), now=now
    )
    assert stale4 is True and reason4 == "SUBSTACK_PLAN_SETUP_TERMINAL:CANCELLED"

    # 5. Earlier expires_at_utc wins over later entry_deadline_utc + naive UTC clock works.
    earlier_exp = _seed_plan_analysis_page(
        store,
        plan_id="plan_earlier_exp",
        entry_deadline_utc="2026-12-05T20:00:00Z",
        expires_at_utc="2026-11-28T20:00:00Z",
    )
    msg5 = store.get_outbox_message(earlier_exp["message_id"])
    stale5, reason5 = substack_plan_page_staleness(
        store.get_outbox_message,
        msg5,
        json.loads(msg5["payload"]),
        now=datetime(2026, 11, 29, 18, 0, 0),  # naive UTC
    )
    assert stale5 is True and reason5 == "SUBSTACK_PLAN_ENTRY_DEADLINE_PASSED"


# ---------------------------------------------------------------------------
# Part 2 — Dry-Run-Default Pre-Unpause Reconciliation CLI Tests
# ---------------------------------------------------------------------------


def _build_full_preunpause_fixture_db(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    """Build a realistic SQLite fixture covering Subgroups A, B, D, derivatives, O56/O58/O60/O61, CC603."""
    db_path = tmp_path / "fixture_preunpause.sqlite3"
    store = ContentOpsDurableStore(db_path)
    refs: dict[str, Any] = {}

    # 1. Subgroup A (#13 expired READY Substack plan page, dispatch=None).
    refs["subgroup_a"] = _seed_plan_analysis_page(
        store,
        plan_id="plan_7c24bb53fe8d2a2845e98583",
        entry_deadline_utc="2026-11-23T20:00:00Z",
        expires_at_utc="2026-11-23T20:00:00Z",
    )

    # 2. Active non-expired Substack plan page (must be preserved).
    refs["active_plan"] = _seed_plan_analysis_page(
        store,
        plan_id="plan_active_dec01",
        entry_deadline_utc="2026-12-01T20:00:00Z",
    )

    # 3. Non-plan Substack READY article (must be preserved).
    store.create_work_item(
        story_id="nonplan-article",
        work_item_id="nonplan-article",
        title="Regular Article",
        target_surface="SUBSTACK_ARTICLE",
    )
    reg_sub = DurablePublicationCoordinator(store=store, transport_runtime=None).register_plan(
        "nonplan-article", _make_substack_plan("nonplan-article")
    )["registered"][0]
    refs["nonplan_substack"] = reg_sub

    # 4. Subgroup B1 (#14 DISPATCH_ATTEMPT_STARTED, no absence proof => NEVER auto-retire).
    refs["subgroup_b_held_attempt"] = _seed_plan_analysis_page(
        store,
        plan_id="plan_1d9bc560342b94e3d5a0cdb1",
        entry_deadline_utc="2026-11-23T19:45:00Z",
        outbox_status="READY",
        dispatch_status=ATTEMPT_STARTED,
    )

    # 5. Subgroup B2 (UNKNOWN_WRITE with ambiguous readback => NEVER auto-retire).
    refs["subgroup_b_held_ambig"] = _seed_plan_analysis_page(
        store,
        plan_id="plan_ambig_unknown",
        entry_deadline_utc="2026-11-23T19:45:00Z",
        outbox_status=UNKNOWN_WRITE,
        dispatch_status=UNKNOWN_WRITE,
        ambiguous_readback=True,
    )

    # 6. Subgroup B3 (expired #14-style row driven through REAL coordinator.readback_existing_dispatch()
    #    -> _reconcile() absence proof => safe to settle on --apply).
    refs["subgroup_b_verified_absent"] = _seed_plan_analysis_page(
        store,
        plan_id="plan_verified_absent",
        entry_deadline_utc="2026-11-23T19:45:00Z",
        outbox_status="READY",
        dispatch_status=ATTEMPT_STARTED,
    )
    b3_coordinator = DurablePublicationCoordinator(
        store=store,
        transport_runtime=_RecordingTransport(readback_status="ABSENT"),
        readiness_provider=lambda _: {"readiness_state": "READY_AUTHENTICATED"},
        clock=lambda: datetime(2026, 11, 29, 17, 55, 0, tzinfo=timezone.utc),
    )
    b3_rb = b3_coordinator.readback_existing_dispatch(refs["subgroup_b_verified_absent"]["dispatch_id"])
    assert b3_rb["reconciliation_status"] == RECONCILED_ABSENT_SAFE_TO_RETRY

    # 6b. Historical already-superseded Substack rows with RECONCILED_ABSENT_SAFE_TO_RETRY dispatch
    #     (mirrors live production DB rows dispatch_2961... / dispatch_71d0...) => MUST be excluded.
    refs["historical_superseded_media"] = _seed_plan_analysis_page(
        store,
        plan_id="plan_hist_superseded_media",
        entry_deadline_utc="2026-11-12T12:00:00Z",
        outbox_status="SUPERSEDED_UNSENT_MEDIA_REVISION",
        dispatch_status=RECONCILED_ABSENT_SAFE_TO_RETRY,
        reconciliation_status=RECONCILED_ABSENT_SAFE_TO_RETRY,
    )
    store.register_readback(
        readback_id="rb_hist_superseded",
        dispatch_id=refs["historical_superseded_media"]["dispatch_id"],
        readback_data=json.dumps(
            {
                "readback": {
                    "verified": False,
                    "write_absent": True,
                    "write_exists": False,
                    "canonical_url_valid": False,
                }
            }
        ),
    )

    # 7. Subgroup D (#01 NATIVE_NEO_TOOL_PENDING under SUPERSEDED_NOT_POSTED parent).
    wid_01 = "plan-status-post-2696e75fd567c7fe308225be6bef7d68"
    store.create_work_item(story_id=wid_01, work_item_id=wid_01, title="Superseded post", target_surface="MULTI_PLATFORM")
    store.register_outbox_message(
        message_id=wid_01,
        work_item_id=wid_01,
        destination="internal:plan-status-post",
        payload=json.dumps({"key": wid_01, "kind": "setup"}),
        status="SUPERSEDED_NOT_POSTED",
    )
    mid_01 = "outbox_5476618f81ce8b99dc5714029df32c5b"
    did_01 = "dispatch_5476618f81ce8b99dc5714029df32c5b"
    store.register_outbox_message(
        message_id=mid_01,
        work_item_id=wid_01,
        destination="substack_notes",
        payload=json.dumps({"work_item_id": wid_01, "plan_hash": "h01", "plan_status_post": wid_01}),
        status=NATIVE_NEO_PENDING,
    )
    store.register_platform_dispatch(
        dispatch_id=did_01, message_id=mid_01, platform="substack_notes", status=NATIVE_NEO_PENDING
    )
    refs["subgroup_d"] = {"work_item_id": wid_01, "message_id": mid_01, "dispatch_id": did_01}

    # Active NATIVE_NEO_TOOL_PENDING under READY parent (must NOT be settled).
    wid_active_neo = "plan-status-post-active-neo"
    store.create_work_item(
        story_id=wid_active_neo, work_item_id=wid_active_neo, title="Active neo", target_surface="MULTI_PLATFORM"
    )
    store.register_outbox_message(
        message_id=wid_active_neo,
        work_item_id=wid_active_neo,
        destination="internal:plan-status-post",
        payload=json.dumps({"key": wid_active_neo, "kind": "setup"}),
        status="READY",
    )
    store.register_outbox_message(
        message_id="outbox_active_neo",
        work_item_id=wid_active_neo,
        destination="substack_notes",
        payload=json.dumps({"work_item_id": wid_active_neo, "plan_hash": "han", "plan_status_post": wid_active_neo}),
        status=NATIVE_NEO_PENDING,
    )
    store.register_platform_dispatch(
        dispatch_id="dispatch_active_neo",
        message_id="outbox_active_neo",
        platform="substack_notes",
        status=NATIVE_NEO_PENDING,
    )
    refs["active_neo"] = {"message_id": "outbox_active_neo", "dispatch_id": "dispatch_active_neo"}

    # 8. Expired derivative READY rows (window expiry + dead parent + stale >24h) + 1 fresh READY derivative.
    store.register_outbox_message(
        message_id="outbox_expired_deriv_dead_parent",
        work_item_id=wid_01,
        destination="threads",
        payload=json.dumps({"work_item_id": wid_01, "plan_hash": "h01", "plan_status_post": wid_01}),
        status="READY",
    )
    store.create_work_item(
        story_id="cc689-weekly-2026-11-22",
        work_item_id="cc689-weekly-2026-11-22",
        title="Weekly wrap",
        target_surface="MULTI_PLATFORM",
    )
    store.register_outbox_message(
        message_id="outbox_expired_deriv_window",
        work_item_id="cc689-weekly-2026-11-22",
        destination="x",
        payload=json.dumps(
            {
                "work_item_id": "cc689-weekly-2026-11-22",
                "plan_hash": "hw22",
                "publication_window": {"expires_at_utc": "2026-11-22T18:00:00Z"},
            }
        ),
        status="READY",
    )
    store.create_work_item(
        story_id="fresh-deriv-item",
        work_item_id="fresh-deriv-item",
        title="Fresh derivative",
        target_surface="MULTI_PLATFORM",
    )
    store.register_outbox_message(
        message_id="outbox_fresh_deriv",
        work_item_id="fresh-deriv-item",
        destination="telegram",
        payload=json.dumps({"work_item_id": "fresh-deriv-item", "plan_hash": "hf1"}),
        status="READY",
    )
    with closing(store.get_connection()) as conn:
        conn.execute(
            "UPDATE outbox_messages SET created_at=? WHERE message_id=?",
            ("2026-11-29T17:00:00+00:00", "outbox_fresh_deriv"),
        )
        conn.commit()
    refs["expired_derivs"] = ["outbox_expired_deriv_dead_parent", "outbox_expired_deriv_window"]
    refs["fresh_deriv"] = "outbox_fresh_deriv"

    # 9. Dead-parent / late UNKNOWN_WRITE polling targets (O56, O58, O60, O61) + preserved O57/O59.
    # O60: x under SUPERSEDED_NOT_POSTED parent wid_01.
    store.register_outbox_message(
        message_id="outbox_o60_x",
        work_item_id=wid_01,
        destination="x",
        payload=json.dumps({"work_item_id": wid_01, "plan_hash": "h01", "plan_status_post": wid_01}),
        status=UNKNOWN_WRITE,
    )
    store.register_platform_dispatch(
        dispatch_id="dispatch_o60_x", message_id="outbox_o60_x", platform="x", status=UNKNOWN_WRITE
    )

    # O56: substack_notes under SUPERSEDED_NOT_POSTED parent.
    wid_56 = "plan-status-post-7e284f364a945bc2b95bdb16fb6a9d38"
    store.create_work_item(story_id=wid_56, work_item_id=wid_56, title="O56", target_surface="MULTI_PLATFORM")
    store.register_outbox_message(
        message_id=wid_56,
        work_item_id=wid_56,
        destination="internal:plan-status-post",
        payload=json.dumps({"key": wid_56}),
        status="SUPERSEDED_NOT_POSTED",
    )
    store.register_outbox_message(
        message_id="outbox_o56_notes",
        work_item_id=wid_56,
        destination="substack_notes",
        payload=json.dumps({"work_item_id": wid_56, "plan_hash": "h56", "plan_status_post": wid_56}),
        status=UNKNOWN_WRITE,
    )
    store.register_platform_dispatch(
        dispatch_id="dispatch_o56_notes",
        message_id="outbox_o56_notes",
        platform="substack_notes",
        status=UNKNOWN_WRITE,
    )

    # O61: x under STALE_NOT_POSTED parent.
    wid_61 = "plan-status-post-f5c31cea9e685249e77837187480105d"
    store.create_work_item(story_id=wid_61, work_item_id=wid_61, title="O61", target_surface="MULTI_PLATFORM")
    store.register_outbox_message(
        message_id=wid_61,
        work_item_id=wid_61,
        destination="internal:plan-status-post",
        payload=json.dumps({"key": wid_61}),
        status="STALE_NOT_POSTED",
    )
    store.register_outbox_message(
        message_id="outbox_o61_x",
        work_item_id=wid_61,
        destination="x",
        payload=json.dumps({"work_item_id": wid_61, "plan_hash": "h61", "plan_status_post": wid_61}),
        status=UNKNOWN_WRITE,
    )
    store.register_platform_dispatch(
        dispatch_id="dispatch_o61_x", message_id="outbox_o61_x", platform="x", status=UNKNOWN_WRITE
    )

    # O58: late (>24h) plan-analysis-link-* substack_notes UNKNOWN_WRITE.
    wid_58 = "plan-analysis-link-plan_add6d62299828744939aafc1-substack_notes-8e2e4ca9"
    store.create_work_item(story_id=wid_58, work_item_id=wid_58, title="O58", target_surface="MULTI_PLATFORM")
    store.register_outbox_message(
        message_id=wid_58,
        work_item_id=wid_58,
        destination="internal:plan-analysis-page",
        payload=json.dumps({"link_id": wid_58}),
        status="EDITORIAL_INTERNAL",
    )
    store.register_outbox_message(
        message_id="outbox_o58_notes",
        work_item_id=wid_58,
        destination="substack_notes",
        payload=json.dumps({"work_item_id": wid_58, "plan_hash": "h58", "plan_analysis_link": wid_58}),
        status=UNKNOWN_WRITE,
    )
    store.register_platform_dispatch(
        dispatch_id="dispatch_o58_notes",
        message_id="outbox_o58_notes",
        platform="substack_notes",
        status=UNKNOWN_WRITE,
    )
    with closing(store.get_connection()) as conn:
        conn.execute(
            "UPDATE outbox_messages SET created_at=? WHERE message_id IN (?, ?)",
            ("2026-11-22T20:18:50+00:00", wid_58, "outbox_o58_notes"),
        )
        conn.commit()

    # O57 (wrap substack_notes UNKNOWN_WRITE) -> preserved, NOT a dead-parent plan polling target.
    store.register_outbox_message(
        message_id="outbox_o57_wrap",
        work_item_id="cc689-weekly-2026-11-22",
        destination="substack_notes",
        payload=json.dumps({"work_item_id": "cc689-weekly-2026-11-22", "plan_hash": "hw22"}),
        status=UNKNOWN_WRITE,
    )
    store.register_platform_dispatch(
        dispatch_id="dispatch_o57_wrap",
        message_id="outbox_o57_wrap",
        platform="substack_notes",
        status=UNKNOWN_WRITE,
    )
    refs["dead_parent_uw"] = [
        ("outbox_o56_notes", "dispatch_o56_notes"),
        ("outbox_o58_notes", "dispatch_o58_notes"),
        ("outbox_o60_x", "dispatch_o60_x"),
        ("outbox_o61_x", "dispatch_o61_x"),
    ]
    refs["o58_parent"] = wid_58
    refs["preserved_o57"] = ("outbox_o57_wrap", "dispatch_o57_wrap")

    # 10. 9 CC603_PREPARED backfill rows (matching live count).
    cc603_ids = []
    for idx in range(9):
        cid = f"cc603-followup-fixture-{idx:02d}"
        store.create_work_item(story_id=cid, work_item_id=cid, title=f"CC603 {idx}", target_surface="MULTI_PLATFORM")
        store.register_outbox_message(
            message_id=cid,
            work_item_id=cid,
            destination="internal:plan-status-post",
            payload=json.dumps({"key": cid, "kind": "call_followup", "plan_id": f"plan_{idx}", "symbol": "XAUUSD"}),
            status="CC603_PREPARED",
        )
        cc603_ids.append(cid)
    refs["cc603_ids"] = cc603_ids

    # 11. Stale historical lease & stale Oct 31 heartbeat (must NOT falsely trigger interlocks).
    conn = store.get_connection()
    try:
        conn.execute(
            "INSERT INTO leases (lease_id, lease_key, work_item_id, owner_ref, fencing_token, acquired_at, renewed_at, expires_at, status) "
            "VALUES ('lease_old', 'old-key', NULL, 'old-owner', 1, '2026-11-20T00:00:00Z', '2026-11-20T00:00:00Z', '2026-11-20T00:15:00Z', 'ACTIVE')"
        )
        conn.execute(
            "INSERT INTO heartbeats (heartbeat_id, worker_id, lease_id, last_seen_at, status) "
            "VALUES ('hb_old', 'old-supervisor', NULL, '2026-10-31T02:49:41Z', 'ALIVE')"
        )
        conn.commit()
        # Checkpoint WAL cleanly to 0 bytes so dry-run uses immutable=1 and we can hash the single file.
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()

    return db_path, refs


def test_cli_dry_run_default_is_zero_mutation_byte_exact(tmp_path, capsys):
    db_path, refs = _build_full_preunpause_fixture_db(tmp_path)
    before_hash = _sha256_file(db_path)
    wal_path = Path(f"{db_path}-wal")
    before_wal = wal_path.stat().st_size if wal_path.exists() else 0

    rc = cli.main(["--db", str(db_path), "--now-utc", "2026-11-29T18:00:00Z"])
    assert rc == cli.EXIT_OK
    payload = json.loads(capsys.readouterr().out)

    assert payload["status"] == "DRY_RUN_OK"
    assert payload["mode"] == "dry_run"
    assert payload["applied"] is False
    assert payload["apply_interlocks_preview"]["ok"] is True

    counts = payload["audit"]["counts"]
    assert counts["subgroup_a_expired_substack_plan_pages"] == 1
    assert counts["active_substack_plan_pages_preserved"] == 1
    assert counts["non_plan_substack_ready_preserved"] == 1
    assert counts["subgroup_b_substack_readback_gated"] == 3
    assert counts["subgroup_b_readback_held"] == 2
    assert counts["subgroup_b_verified_absent_eligible"] == 1
    assert counts["subgroup_d_dead_parent_native_neo_pending"] == 1
    assert counts["expired_derivative_ready_rows"] == 2
    assert counts["active_derivative_ready_preserved"] == 1
    assert counts["dead_parent_unknown_write_polling_targets"] == 4
    assert counts["other_unknown_writes_preserved"] == 1
    assert counts["cc603_backfill_prepared"] == 9

    # Byte-exact zero-mutation proof on copied SQLite fixture.
    assert _sha256_file(db_path) == before_hash
    after_wal = wal_path.stat().st_size if wal_path.exists() else 0
    assert after_wal == before_wal == 0


def test_cli_usage_and_interlocks_fail_closed_with_zero_writes(tmp_path, capsys):
    db_path, _ = _build_full_preunpause_fixture_db(tmp_path)
    now = datetime(2026, 11, 29, 18, 0, 0, tzinfo=timezone.utc)

    # Usage: --apply without explicit --db refused.
    assert cli.main(["--apply"]) == cli.EXIT_USAGE_REFUSED
    assert json.loads(capsys.readouterr().out)["reason"] == "APPLY_REQUIRES_EXPLICIT_DB_PATH"

    # Usage: --apply + --dry-run refused.
    assert cli.main(["--apply", "--dry-run", "--db", str(db_path)]) == cli.EXIT_USAGE_REFUSED
    assert json.loads(capsys.readouterr().out)["reason"] == "CONFLICTING_MODE_FLAGS"

    # Interlock 1: restored.json exists => REFUSED_INTERLOCK, 0 writes.
    before_hash = _sha256_file(db_path)
    restored = tmp_path / "control" / "pause-20261123" / "restored.json"
    restored.parent.mkdir(parents=True, exist_ok=True)
    restored.write_text('{"started_at_utc":"2026-11-29T18:00:00Z"}\n', encoding="utf-8")
    rc1 = cli.main(
        ["--apply", "--db", str(db_path), "--now-utc", "2026-11-29T18:00:00Z", "--allow-copied-state-clock-override"]
    )
    assert rc1 == cli.EXIT_INTERLOCK_REFUSED
    out1 = json.loads(capsys.readouterr().out)
    assert out1["status"] == "REFUSED_INTERLOCK"
    assert any(b["code"] == "RESTORED_JSON_EXISTS" for b in out1["interlocks"]["blockers"])
    assert _sha256_file(db_path) == before_hash
    restored.unlink()

    # Interlock 2: held writer lock file => REFUSED_INTERLOCK, 0 writes.
    lock_file = tmp_path / "runner_v1.lock"
    lock_file.write_text(json.dumps({"pid": os.getpid()}), encoding="utf-8")
    fd = os.open(str(lock_file), os.O_RDWR | getattr(os, "O_BINARY", 0))
    try:
        if os.name == "nt":
            import msvcrt

            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        rc2, res2 = cli.apply_preunpause_reconciliation(
            db_path, now=now, allow_copied_state_clock_override=True
        )
        assert rc2 == cli.EXIT_INTERLOCK_REFUSED
        assert any(b["code"] == "ACTIVE_WRITER_LOCK_FILE" for b in res2["interlocks"]["blockers"])
        assert _sha256_file(db_path) == before_hash
    finally:
        if os.name == "nt":
            import msvcrt

            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        os.close(fd)
        lock_file.unlink()

    # Interlock 2b: unlocked lock file with alive parent PID => REFUSED; dead PID => allowed.
    pid_lock = tmp_path / "supervisor.lock"
    pid_lock.write_text(json.dumps({"pid": os.getppid()}), encoding="utf-8")
    rc2b, res2b = cli.apply_preunpause_reconciliation(
        db_path, now=now, allow_copied_state_clock_override=True
    )
    assert rc2b == cli.EXIT_INTERLOCK_REFUSED
    assert any(
        b["code"] == "ACTIVE_WRITER_LOCK_FILE" and str(b.get("reason", "")).startswith("LOCK_PID_ALIVE:")
        for b in res2b["interlocks"]["blockers"]
    )
    assert _sha256_file(db_path) == before_hash
    pid_lock.write_text(json.dumps({"pid": 999999999}), encoding="utf-8")
    interlock_dead = cli.check_apply_interlocks(db_path, now=now, check_live_processes=False)
    assert interlock_dead["ok"] is True
    pid_lock.unlink()

    # Interlock 3: active unexpired SQLite lease => REFUSED_INTERLOCK.
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            "INSERT INTO leases (lease_id, lease_key, work_item_id, owner_ref, fencing_token, acquired_at, renewed_at, expires_at, status) "
            "VALUES ('lease_live', 'live-key', NULL, 'live-owner', 2, '2026-11-29T17:58:00Z', '2026-11-29T17:58:00Z', '2026-11-29T18:10:00Z', 'ACTIVE')"
        )
        conn.commit()
    rc3, res3 = cli.apply_preunpause_reconciliation(
        db_path, now=now, allow_copied_state_clock_override=True
    )
    assert rc3 == cli.EXIT_INTERLOCK_REFUSED
    assert any(b["code"] == "ACTIVE_SQLITE_LEASE" for b in res3["interlocks"]["blockers"])
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("DELETE FROM leases WHERE lease_id='lease_live'")
        conn.commit()

    # Interlock 4: fresh ALIVE supervisor heartbeat => REFUSED_INTERLOCK.
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            "INSERT INTO heartbeats (heartbeat_id, worker_id, lease_id, last_seen_at, status) "
            "VALUES ('hb_live', 'live-sup', NULL, '2026-11-29T17:58:00Z', 'ALIVE')"
        )
        conn.commit()
    rc4, res4 = cli.apply_preunpause_reconciliation(
        db_path, now=now, allow_copied_state_clock_override=True
    )
    assert rc4 == cli.EXIT_INTERLOCK_REFUSED
    assert any(b["code"] == "ACTIVE_SUPERVISOR_HEARTBEAT" for b in res4["interlocks"]["blockers"])
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("DELETE FROM heartbeats WHERE heartbeat_id='hb_live'")
        conn.commit()

    # Interlock 5: simulated live DB with running supervisor process => REFUSED_INTERLOCK (uses real wall UTC).
    rc5, res5 = cli.apply_preunpause_reconciliation(
        db_path,
        production_store=db_path,
        process_scanner=lambda: [{"pid": 99999, "name": "python.exe", "command_line": "live_contentops.cli daily-app start"}],
    )
    assert rc5 == cli.EXIT_INTERLOCK_REFUSED
    assert any(b["code"] == "ACTIVE_WRITER_OR_SUPERVISOR_PROCESS" for b in res5["interlocks"]["blockers"])


def test_cli_apply_settles_safely_preserves_readback_gates_and_is_idempotent(tmp_path, capsys):
    db_path, refs = _build_full_preunpause_fixture_db(tmp_path)

    # Pass 1: --apply WITHOUT --retire-cc603-backfill (explicit copied-state replay clock; CC603 rows untouched).
    rc = cli.main(
        ["--apply", "--db", str(db_path), "--now-utc", "2026-11-29T18:00:00Z", "--allow-copied-state-clock-override"]
    )
    assert rc == cli.EXIT_OK
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "APPLIED"
    assert res["applied"] is True

    store = ContentOpsDurableStore(db_path, auto_migrate=False)

    # Subgroup A (#13) cleanly retired + parent settled.
    assert store.get_outbox_message(refs["subgroup_a"]["message_id"])["status"] == PLAN_PAGE_EXPIRED_STALE_NO_WRITE
    assert store.get_outbox_message(refs["subgroup_a"]["page_id"])["status"] == "SETTLED"

    # Active Substack plan & non-plan Substack article untouched.
    assert store.get_outbox_message(refs["active_plan"]["message_id"])["status"] == "READY"
    assert store.get_outbox_message(refs["nonplan_substack"]["message_id"])["status"] == "READY"

    # Subgroup B1 (#14 DISPATCH_ATTEMPT_STARTED) & B2 (ambiguous UNKNOWN_WRITE) HELD & UNTOUCHED!
    assert store.get_outbox_message(refs["subgroup_b_held_attempt"]["message_id"])["status"] == "READY"
    assert store.get_platform_dispatch(refs["subgroup_b_held_attempt"]["dispatch_id"])["status"] == ATTEMPT_STARTED
    assert store.get_outbox_message(refs["subgroup_b_held_ambig"]["message_id"])["status"] == UNKNOWN_WRITE
    assert store.get_platform_dispatch(refs["subgroup_b_held_ambig"]["dispatch_id"])["status"] == UNKNOWN_WRITE
    assert len(res["mutations"]["subgroup_b_held_readback_required"]) == 2

    # Subgroup B3 (real _reconcile() durable absence proof + expired) cleanly settled while preserving reconciliation.
    assert store.get_outbox_message(refs["subgroup_b_verified_absent"]["message_id"])["status"] == PLAN_PAGE_EXPIRED_STALE_NO_WRITE
    assert store.get_platform_dispatch(refs["subgroup_b_verified_absent"]["dispatch_id"])["status"] == PLAN_PAGE_EXPIRED_STALE_NO_WRITE
    assert store.get_outbox_message(refs["subgroup_b_verified_absent"]["page_id"])["status"] == "SETTLED"
    recs_b3 = store.get_reconciliations_for_work_item(refs["subgroup_b_verified_absent"]["page_id"])
    assert recs_b3[0]["status"] == RECONCILED_ABSENT_SAFE_TO_RETRY
    # Historical SUPERSEDED_UNSENT_MEDIA_REVISION row stays untouched.
    assert (
        store.get_outbox_message(refs["historical_superseded_media"]["message_id"])["status"]
        == "SUPERSEDED_UNSENT_MEDIA_REVISION"
    )
    assert (
        store.get_platform_dispatch(refs["historical_superseded_media"]["dispatch_id"])["status"]
        == RECONCILED_ABSENT_SAFE_TO_RETRY
    )

    # Subgroup D (#01): outbox PLAN_POST_SETTLED, dispatch preserved as NATIVE_NEO_TOOL_PENDING!
    assert store.get_outbox_message(refs["subgroup_d"]["message_id"])["status"] == "PLAN_POST_SETTLED"
    assert store.get_platform_dispatch(refs["subgroup_d"]["dispatch_id"])["status"] == NATIVE_NEO_PENDING
    # Active NATIVE_NEO_TOOL_PENDING untouched.
    assert store.get_outbox_message(refs["active_neo"]["message_id"])["status"] == NATIVE_NEO_PENDING

    # Expired derivative READY rows -> DERIVATIVE_EXPIRED_STALE_NO_WRITE; fresh READY untouched.
    for mid in refs["expired_derivs"]:
        assert store.get_outbox_message(mid)["status"] == DERIVATIVE_EXPIRED_STALE_NO_WRITE
    assert store.get_outbox_message(refs["fresh_deriv"])["status"] == "READY"

    # Dead-parent / late UNKNOWN_WRITE polling targets (O56/O58/O60/O61):
    # outbox -> PLAN_POST_SETTLED, dispatch -> UNKNOWN_WRITE preserved!
    for mid, did in refs["dead_parent_uw"]:
        assert store.get_outbox_message(mid)["status"] == "PLAN_POST_SETTLED"
        assert store.get_platform_dispatch(did)["status"] == UNKNOWN_WRITE
    assert store.get_outbox_message(refs["o58_parent"])["status"] == "SETTLED"
    # O57 wrap UNKNOWN_WRITE preserved untouched.
    assert store.get_outbox_message(refs["preserved_o57"][0])["status"] == UNKNOWN_WRITE
    assert store.get_platform_dispatch(refs["preserved_o57"][1])["status"] == UNKNOWN_WRITE

    # All 9 CC603_PREPARED rows untouched by default!
    assert all(store.get_outbox_message(cid)["status"] == "CC603_PREPARED" for cid in refs["cc603_ids"])
    assert res["post_audit_counts"]["cc603_backfill_prepared"] == 9
    assert res["mutations"]["cc603_backfill_retired"] == []

    # Pass 2: idempotency check (second --apply produces 0 new settlements).
    rc2 = cli.main(
        ["--apply", "--db", str(db_path), "--now-utc", "2026-11-29T18:00:00Z", "--allow-copied-state-clock-override"]
    )
    assert rc2 == cli.EXIT_OK
    res2 = json.loads(capsys.readouterr().out)
    assert res2["mutations"]["subgroup_a_retired"] == []
    assert res2["mutations"]["subgroup_b_verified_absent_retired"] == []
    assert res2["mutations"]["subgroup_d_settled"] == []
    assert res2["mutations"]["expired_derivative_ready_retired"] == []
    assert res2["mutations"]["dead_parent_unknown_writes_settled"] == []

    # Pass 3: explicit --retire-cc603-backfill retires the 9 CC603_PREPARED rows cleanly.
    rc3 = cli.main(
        [
            "--apply",
            "--db",
            str(db_path),
            "--now-utc",
            "2026-11-29T18:00:00Z",
            "--allow-copied-state-clock-override",
            "--retire-cc603-backfill",
        ]
    )
    assert rc3 == cli.EXIT_OK
    res3 = json.loads(capsys.readouterr().out)
    assert len(res3["mutations"]["cc603_backfill_retired"]) == 9
    assert res3["post_audit_counts"]["cc603_backfill_prepared"] == 0
    assert all(store.get_outbox_message(cid)["status"] == "SETTLED" for cid in refs["cc603_ids"])


def test_cc692_h1_end_to_end_real_reconcile_absence_and_negative_controls(tmp_path, capsys):
    """CC692-H1 regression: real coordinator.readback_existing_dispatch() -> _reconcile() -> CLI --apply."""
    db_path = tmp_path / "cc692_h1_e2e.sqlite3"
    store = ContentOpsDurableStore(db_path)
    relaunch_now = datetime(2026, 11, 29, 18, 0, 0, tzinfo=timezone.utc)

    # 1. Seed real #14 state (outbox READY, dispatch DISPATCH_ATTEMPT_STARTED, expired deadline).
    row14 = _seed_plan_analysis_page(
        store,
        plan_id="plan_1d9bc560342b94e3d5a0cdb1",
        entry_deadline_utc="2026-11-23T19:45:00Z",
        outbox_status="READY",
        dispatch_status=ATTEMPT_STARTED,
    )

    # Before readback: CLI holds #14 and refuses to retire it.
    rc_before = cli.main(
        ["--apply", "--db", str(db_path), "--now-utc", "2026-11-29T18:00:00Z", "--allow-copied-state-clock-override"]
    )
    assert rc_before == cli.EXIT_OK
    out_before = json.loads(capsys.readouterr().out)
    assert out_before["pre_audit_counts"]["subgroup_b_readback_held"] == 1
    assert out_before["pre_audit_counts"]["subgroup_b_verified_absent_eligible"] == 0
    assert out_before["mutations"]["subgroup_b_verified_absent_retired"] == []
    assert store.get_outbox_message(row14["message_id"])["status"] == "READY"
    assert store.get_platform_dispatch(row14["dispatch_id"])["status"] == ATTEMPT_STARTED

    # Drive REAL DurablePublicationCoordinator.readback_existing_dispatch() -> _reconcile() with absence.
    transport_absent = _RecordingTransport(readback_status="ABSENT")
    coordinator = DurablePublicationCoordinator(
        store=store,
        transport_runtime=transport_absent,
        readiness_provider=lambda _: {"readiness_state": "READY_AUTHENTICATED"},
        clock=lambda: datetime(2026, 11, 29, 17, 55, 0, tzinfo=timezone.utc),
    )
    rb_res = coordinator.readback_existing_dispatch(row14["dispatch_id"])
    assert rb_res["reconciliation_status"] == RECONCILED_ABSENT_SAFE_TO_RETRY
    assert store.get_outbox_message(row14["message_id"])["status"] == RECONCILED_ABSENT_SAFE_TO_RETRY
    assert store.get_platform_dispatch(row14["dispatch_id"])["status"] == RECONCILED_ABSENT_SAFE_TO_RETRY
    rbs = store.list_readbacks_for_dispatch(row14["dispatch_id"])
    assert len(rbs) == 1
    rb_obs = json.loads(rbs[0]["readback_data"])["readback"]
    assert rb_obs["verified"] is False
    assert rb_obs["write_absent"] is True
    assert rb_obs["write_exists"] is False
    assert rb_obs["canonical_url_valid"] is False

    # Now CLI --apply cleanly discovers & retires #14 end-to-end!
    rc_after = cli.main(
        ["--apply", "--db", str(db_path), "--now-utc", "2026-11-29T18:00:00Z", "--allow-copied-state-clock-override"]
    )
    assert rc_after == cli.EXIT_OK
    out_after = json.loads(capsys.readouterr().out)
    assert out_after["pre_audit_counts"]["subgroup_b_verified_absent_eligible"] == 1
    assert len(out_after["mutations"]["subgroup_b_verified_absent_retired"]) == 1
    assert out_after["mutations"]["subgroup_b_verified_absent_retired"][0]["dispatch_id"] == row14["dispatch_id"]
    assert out_after["mutations"]["subgroup_b_verified_absent_retired"][0]["parent_settled"] is True
    assert store.get_outbox_message(row14["message_id"])["status"] == PLAN_PAGE_EXPIRED_STALE_NO_WRITE
    assert store.get_platform_dispatch(row14["dispatch_id"])["status"] == PLAN_PAGE_EXPIRED_STALE_NO_WRITE
    assert store.get_outbox_message(row14["page_id"])["status"] == "SETTLED"

    # Second pass is idempotent (0 new mutations).
    rc_idem = cli.main(
        ["--apply", "--db", str(db_path), "--now-utc", "2026-11-29T18:00:00Z", "--allow-copied-state-clock-override"]
    )
    assert rc_idem == cli.EXIT_OK
    out_idem = json.loads(capsys.readouterr().out)
    assert out_idem["pre_audit_counts"]["subgroup_b_substack_readback_gated"] == 0
    assert out_idem["mutations"]["subgroup_b_verified_absent_retired"] == []

    # 2. Negative control A: later readback observes write_exists=True (even if dispatch/rec still say absent) => REFUSED.
    later_exists = _seed_plan_analysis_page(
        store,
        plan_id="plan_later_write_exists",
        entry_deadline_utc="2026-11-23T19:45:00Z",
        outbox_status="READY",
        dispatch_status=ATTEMPT_STARTED,
    )
    coordinator.readback_existing_dispatch(later_exists["dispatch_id"])
    assert store.get_platform_dispatch(later_exists["dispatch_id"])["status"] == RECONCILED_ABSENT_SAFE_TO_RETRY
    # Append a later readback observing write_exists=True.
    store.register_readback(
        readback_id="rb_later_write_exists",
        dispatch_id=later_exists["dispatch_id"],
        readback_data=json.dumps(
            {
                "dispatch_id": later_exists["dispatch_id"],
                "destination": "substack",
                "readback": {
                    "verified": False,
                    "write_absent": False,
                    "write_exists": True,
                    "observed_public_object_id": None,
                    "observed_public_object_url": None,
                },
            }
        ),
    )
    with closing(store.get_connection()) as conn:
        conn.execute(
            "UPDATE readbacks SET read_at=? WHERE readback_id=?",
            ("2026-11-29T17:59:00+00:00", "rb_later_write_exists"),
        )
        conn.commit()
    audit_neg = cli.audit_preunpause_outbox(db_path, now=relaunch_now)
    neg_entry = next(
        r for r in audit_neg["subgroup_b_substack_readback_gated"]
        if r["dispatch_id"] == later_exists["dispatch_id"]
    )
    assert neg_entry["verified_absence_proof"] is False
    assert neg_entry["absence_check_reason"] == "CONFLICTING_READBACK_WRITE_EXISTS"
    assert neg_entry["eligible_for_apply"] is False

    # 3. Negative control B: real second coordinator readback observing write_exists=True with object identity
    #    promotes dispatch to DISPATCH_CONFIRMED and removes it from Subgroup B completely.
    real_exists_row = _seed_plan_analysis_page(
        store,
        plan_id="plan_real_later_exists",
        entry_deadline_utc="2026-11-23T19:45:00Z",
        outbox_status="READY",
        dispatch_status=ATTEMPT_STARTED,
    )
    coordinator.readback_existing_dispatch(real_exists_row["dispatch_id"])
    exists_coordinator = DurablePublicationCoordinator(
        store=store,
        transport_runtime=_RecordingTransport(readback_status="EXISTS_INCOMPLETE"),
        readiness_provider=lambda _: {"readiness_state": "READY_AUTHENTICATED"},
        clock=lambda: datetime(2026, 11, 29, 17, 58, 0, tzinfo=timezone.utc),
    )
    exists_coordinator.readback_existing_dispatch(real_exists_row["dispatch_id"])
    assert store.get_platform_dispatch(real_exists_row["dispatch_id"])["status"] == DISPATCH_CONFIRMED
    assert store.get_outbox_message(real_exists_row["message_id"])["status"] == DISPATCH_CONFIRMED

    # 4. Negative control C: synthetic verified=True + write_absent=True is REJECTED (never treated as absence).
    bogus_verified = _seed_plan_analysis_page(
        store,
        plan_id="plan_bogus_verified_absent",
        entry_deadline_utc="2026-11-23T19:45:00Z",
        outbox_status=RECONCILED_ABSENT_SAFE_TO_RETRY,
        dispatch_status=RECONCILED_ABSENT_SAFE_TO_RETRY,
        reconciliation_status=RECONCILED_ABSENT_SAFE_TO_RETRY,
    )
    store.register_readback(
        readback_id="rb_bogus_verified",
        dispatch_id=bogus_verified["dispatch_id"],
        readback_data=json.dumps({"readback": {"verified": True, "write_absent": True, "write_exists": False}}),
    )

    # 5. Negative control D: non-plan Substack article and active (future) plan page with real absence proof
    #    are NEVER eligible for Subgroup B retirement.
    active_absent = _seed_plan_analysis_page(
        store,
        plan_id="plan_active_future_absent",
        entry_deadline_utc="2026-12-05T20:00:00Z",
        outbox_status="READY",
        dispatch_status=ATTEMPT_STARTED,
    )
    coordinator.readback_existing_dispatch(active_absent["dispatch_id"])

    store.create_work_item(
        story_id="nonplan-absent-article",
        work_item_id="nonplan-absent-article",
        title="Regular Non-Plan Article",
        target_surface="SUBSTACK_ARTICLE",
    )
    nonplan_reg = coordinator.register_plan(
        "nonplan-absent-article", _make_substack_plan("nonplan-absent-article")
    )["registered"][0]
    store.register_platform_dispatch(
        dispatch_id=nonplan_reg["dispatch_id"],
        message_id=nonplan_reg["message_id"],
        platform="substack",
        status=ATTEMPT_STARTED,
    )
    coordinator.readback_existing_dispatch(nonplan_reg["dispatch_id"])
    assert store.get_platform_dispatch(nonplan_reg["dispatch_id"])["status"] == RECONCILED_ABSENT_SAFE_TO_RETRY

    # 6. Confirmed-sibling protection (mirrors live DB dispatch_aa34b6ce...):
    #    retires obsolete verified-absent attempt while keeping parent EDITORIAL_INTERNAL untouched.
    sib_absent = _seed_plan_analysis_page(
        store,
        plan_id="plan_with_confirmed_sibling",
        entry_deadline_utc="2026-11-12T21:00:00Z",
        outbox_status="READY",
        dispatch_status=ATTEMPT_STARTED,
    )
    coordinator.readback_existing_dispatch(sib_absent["dispatch_id"])
    store.register_outbox_message(
        message_id="outbox_confirmed_sibling_sub",
        work_item_id=sib_absent["page_id"],
        destination="substack",
        payload=json.dumps({"work_item_id": sib_absent["page_id"], "plan_hash": "sib_confirmed"}),
        status=DISPATCH_CONFIRMED,
    )
    store.register_platform_dispatch(
        dispatch_id="dispatch_confirmed_sibling_sub",
        message_id="outbox_confirmed_sibling_sub",
        platform="substack",
        status=DISPATCH_CONFIRMED,
        public_object_id="224485432",
        public_object_url="https://capitalchronicle.substack.com/p/confirmed-sibling",
    )

    rc_mix = cli.main(
        ["--apply", "--db", str(db_path), "--now-utc", "2026-11-29T18:00:00Z", "--allow-copied-state-clock-override"]
    )
    assert rc_mix == cli.EXIT_OK
    out_mix = json.loads(capsys.readouterr().out)
    retired_dids = [m["dispatch_id"] for m in out_mix["mutations"]["subgroup_b_verified_absent_retired"]]
    assert retired_dids == [sib_absent["dispatch_id"]]
    assert out_mix["mutations"]["subgroup_b_verified_absent_retired"][0]["parent_settled"] is False
    # Parent preserved because of confirmed sibling!
    assert store.get_outbox_message(sib_absent["page_id"])["status"] == "EDITORIAL_INTERNAL"
    assert store.get_outbox_message(sib_absent["message_id"])["status"] == PLAN_PAGE_EXPIRED_STALE_NO_WRITE
    # All negative controls untouched!
    assert store.get_outbox_message(later_exists["message_id"])["status"] == RECONCILED_ABSENT_SAFE_TO_RETRY
    assert store.get_outbox_message(real_exists_row["message_id"])["status"] == DISPATCH_CONFIRMED
    assert store.get_outbox_message(bogus_verified["message_id"])["status"] == RECONCILED_ABSENT_SAFE_TO_RETRY
    assert store.get_outbox_message(active_absent["message_id"])["status"] == RECONCILED_ABSENT_SAFE_TO_RETRY
    assert store.get_outbox_message(nonplan_reg["message_id"])["status"] == RECONCILED_ABSENT_SAFE_TO_RETRY


def test_cc692_h2_future_now_utc_never_bypasses_wall_clock_interlocks_and_writer_regex(tmp_path, capsys):
    """CC692-H2 regression: future --now-utc MUST NOT bypass active wall-clock SQLite leases or heartbeats."""
    db_path, _ = _build_full_preunpause_fixture_db(tmp_path)
    wall_now = datetime.now(timezone.utc)
    future_now_arg = (max(wall_now, datetime(2026, 11, 29, 18, 0, 0, tzinfo=timezone.utc)) + timedelta(days=3)).isoformat().replace("+00:00", "Z")
    # Also test the exact documented pre-unpause relaunch timestamp when running prior to relaunch.
    for now_arg in ("2026-11-29T18:00:00Z", future_now_arg):
        # 1. Wall-clock unexpired ACTIVE lease => EXIT_INTERLOCK_REFUSED (rc=3) even with copied-state replay flag.
        lease_exp = (wall_now + timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
        lease_acq = wall_now.isoformat().replace("+00:00", "Z")
        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute(
                "INSERT INTO leases (lease_id, lease_key, work_item_id, owner_ref, fencing_token, acquired_at, renewed_at, expires_at, status) "
                "VALUES ('lease_wall_live', 'wall-live-key', NULL, 'live-writer', 7, ?, ?, ?, 'ACTIVE')",
                (lease_acq, lease_acq, lease_exp),
            )
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        before_hash = _sha256_file(db_path)

        rc_lease = cli.main(
            ["--apply", "--db", str(db_path), "--now-utc", now_arg, "--allow-copied-state-clock-override"]
        )
        assert rc_lease == cli.EXIT_INTERLOCK_REFUSED
        out_lease = json.loads(capsys.readouterr().out)
        assert out_lease["status"] == "REFUSED_INTERLOCK"
        assert out_lease["applied"] is False
        assert any(b["code"] == "ACTIVE_SQLITE_LEASE" for b in out_lease["interlocks"]["blockers"])
        assert _sha256_file(db_path) == before_hash

        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute("DELETE FROM leases WHERE lease_id='lease_wall_live'")
            conn.commit()

        # 2. Wall-clock fresh ALIVE supervisor heartbeat (30s old) => EXIT_INTERLOCK_REFUSED (rc=3), 0 writes.
        hb_seen = (wall_now - timedelta(seconds=30)).isoformat().replace("+00:00", "Z")
        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute(
                "INSERT INTO heartbeats (heartbeat_id, worker_id, lease_id, last_seen_at, status) "
                "VALUES ('hb_wall_live', 'wall-supervisor', NULL, ?, 'ALIVE')",
                (hb_seen,),
            )
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        before_hash_hb = _sha256_file(db_path)

        rc_hb = cli.main(
            ["--apply", "--db", str(db_path), "--now-utc", now_arg, "--allow-copied-state-clock-override"]
        )
        assert rc_hb == cli.EXIT_INTERLOCK_REFUSED
        out_hb = json.loads(capsys.readouterr().out)
        assert out_hb["status"] == "REFUSED_INTERLOCK"
        assert out_hb["applied"] is False
        assert any(b["code"] == "ACTIVE_SUPERVISOR_HEARTBEAT" for b in out_hb["interlocks"]["blockers"])
        assert _sha256_file(db_path) == before_hash_hb

        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute("DELETE FROM heartbeats WHERE heartbeat_id='hb_wall_live'")
            conn.commit()

    # 3. Verify LIVE_WRITER_PROCESS_PATTERN covers all 12 ContentOps writer/supervisor commands.
    expected_writer_cmds = [
        "python.exe -m live_contentops.cli daily-app start",
        "pythonw.exe daily_app_supervisor.py",
        "python.exe scripts/plan_status_posts.py --once",
        "python.exe scripts/plan_analysis_pages.py",
        "python.exe scripts/manual_desk_tick.py",
        "pythonw.exe -B -m live_contentops.market_wrap_job_v1 --publish",
        "python.exe run_v1_simple_gemini_scheduler.py --published-memory-store contentops_daily_app_v1.sqlite3",
        "pythonw.exe scripts/run_daily_digest_1900.py",
        "python.exe scripts/run_native_neo_executor.py",
        "python.exe scripts/run_sourced_replies.py",
        "python.exe scripts/substack_growth.py",
        "python.exe scripts/reconcile_preunpause_outbox_v1.py --apply --db store.sqlite3",
    ]
    for cmd in expected_writer_cmds:
        assert re.search(cli.LIVE_WRITER_PROCESS_PATTERN, cmd, re.IGNORECASE) is not None, cmd
    assert re.search(cli.LIVE_WRITER_PROCESS_PATTERN, "python.exe -m pytest tests/test_preunpause_substack_backlog_guard_v1.py", re.IGNORECASE) is None


def test_cc692_l2_settle_parent_link_sibling_guard_and_atomic_rollback(tmp_path, monkeypatch):
    """CC692-L2: sibling-dispatch guard on settle_parent_link + single-transaction rollback on mid-apply failure."""
    db_path, refs = _build_full_preunpause_fixture_db(tmp_path)
    store = ContentOpsDurableStore(db_path, auto_migrate=False)
    now = datetime(2026, 11, 29, 18, 0, 0, tzinfo=timezone.utc)

    # 1. Add a blocking confirmed sibling child under O58's plan-analysis-link-* parent.
    store.register_outbox_message(
        message_id="outbox_o58_sibling_confirmed",
        work_item_id=refs["o58_parent"],
        destination="x",
        payload=json.dumps({"work_item_id": refs["o58_parent"], "plan_hash": "h58_sib"}),
        status=DISPATCH_CONFIRMED,
    )
    store.register_platform_dispatch(
        dispatch_id="dispatch_o58_sibling_confirmed",
        message_id="outbox_o58_sibling_confirmed",
        platform="x",
        status=DISPATCH_CONFIRMED,
        public_object_id="x-99999",
        public_object_url="https://x.com/capitalchronicle/status/99999",
    )

    # 2. Simulate crash mid-apply -> verify single BEGIN IMMEDIATE transaction rolls back ALL mutations!
    orig_reg_incident = cli._tx_register_incident
    calls = {"n": 0}

    def _boom_on_third(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 3:
            raise RuntimeError("SIMULATED_MID_TX_FAILURE")
        return orig_reg_incident(*args, **kwargs)

    monkeypatch.setattr(cli, "_tx_register_incident", _boom_on_third)
    with pytest.raises(RuntimeError, match="SIMULATED_MID_TX_FAILURE"):
        cli.apply_preunpause_reconciliation(db_path, now=now, allow_copied_state_clock_override=True)

    # Zero partial writes survived rollback!
    assert store.get_outbox_message(refs["subgroup_a"]["message_id"])["status"] == "READY"
    assert store.get_outbox_message(refs["subgroup_a"]["page_id"])["status"] == "EDITORIAL_INTERNAL"
    assert store.get_outbox_message(refs["subgroup_b_verified_absent"]["message_id"])["status"] == RECONCILED_ABSENT_SAFE_TO_RETRY
    assert store.get_outbox_message(refs["subgroup_d"]["message_id"])["status"] == NATIVE_NEO_PENDING

    # 3. Restore normal incident writer -> apply commits cleanly and protects O58 parent because of confirmed sibling.
    monkeypatch.setattr(cli, "_tx_register_incident", orig_reg_incident)
    rc, res = cli.apply_preunpause_reconciliation(db_path, now=now, allow_copied_state_clock_override=True)
    assert rc == cli.EXIT_OK
    o58_mut = next(
        m for m in res["mutations"]["dead_parent_unknown_writes_settled"]
        if m["message_id"] == "outbox_o58_notes"
    )
    assert o58_mut["parent_settled"] is False
    assert store.get_outbox_message("outbox_o58_notes")["status"] == "PLAN_POST_SETTLED"
    assert store.get_outbox_message(refs["o58_parent"])["status"] == "EDITORIAL_INTERNAL"


def test_cc692_cc908_future_clock_cannot_retire_active_page_and_tx_reevaluates_deadline(
    tmp_path, capsys, monkeypatch
):
    """CC-908 [High] regression: future --now-utc cannot retire an active (+1d) READY page on --apply,
    live DB always forbids clock overrides, and BEGIN IMMEDIATE re-evaluates page & deadline atomically."""
    db_path = tmp_path / "cc908_wall_expiry.sqlite3"
    store = ContentOpsDurableStore(db_path)
    wall_now = datetime.now(timezone.utc)
    future_deadline = (wall_now + timedelta(days=1)).isoformat().replace("+00:00", "Z")
    expired_deadline = (wall_now - timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    eval_3d_ahead = (wall_now + timedelta(days=3)).isoformat().replace("+00:00", "Z")

    # Seed active READY Substack plan page (+1d deadline) and one genuinely expired page (-2h deadline).
    active_page = _seed_plan_analysis_page(
        store,
        plan_id="plan_active_plus_1d",
        entry_deadline_utc=future_deadline,
        outbox_status="READY",
    )
    expired_page = _seed_plan_analysis_page(
        store,
        plan_id="plan_expired_minus_2h",
        entry_deadline_utc=expired_deadline,
        outbox_status="READY",
    )
    with closing(store.get_connection()) as conn:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    before_hash = _sha256_file(db_path)

    # 1. Wall-clock dry-run sees +1d page active and -2h page expired, with 0-byte DB mutation.
    rc_dry = cli.main(["--db", str(db_path)])
    assert rc_dry == cli.EXIT_OK
    dry_out = json.loads(capsys.readouterr().out)
    assert dry_out["audit"]["counts"]["active_substack_plan_pages_preserved"] == 1
    assert dry_out["audit"]["counts"]["subgroup_a_expired_substack_plan_pages"] == 1
    assert _sha256_file(db_path) == before_hash

    # 2. Copied-store CLI --apply evaluated +3d ahead WITHOUT --allow-copied-state-clock-override =>
    #    REFUSED (EXIT_USAGE_REFUSED), 0-byte DB mutation, +1d page stays READY!
    rc_refused = cli.main(["--apply", "--db", str(db_path), "--now-utc", eval_3d_ahead])
    assert rc_refused == cli.EXIT_USAGE_REFUSED
    refused_out = json.loads(capsys.readouterr().out)
    assert refused_out["status"] == "REFUSED_USAGE"
    assert refused_out["applied"] is False
    assert refused_out["reason"] == "APPLY_CLOCK_OVERRIDE_REQUIRES_COPIED_STATE_REPLAY"
    assert _sha256_file(db_path) == before_hash
    assert store.get_outbox_message(active_page["message_id"])["status"] == "READY"
    assert store.get_outbox_message(expired_page["message_id"])["status"] == "READY"

    # 3. Direct Python apply_preunpause_reconciliation with future now and no opt-in => REFUSED, 0 writes.
    rc_py_ref, res_py_ref = cli.apply_preunpause_reconciliation(
        db_path, now=wall_now + timedelta(days=3)
    )
    assert rc_py_ref == cli.EXIT_USAGE_REFUSED
    assert res_py_ref["reason"] == "APPLY_CLOCK_OVERRIDE_REQUIRES_COPIED_STATE_REPLAY"
    assert _sha256_file(db_path) == before_hash

    # 4. Simulated LIVE production DB forbids --now-utc AND --allow-copied-state-clock-override ALWAYS!
    rc_live_ref, res_live_ref = cli.apply_preunpause_reconciliation(
        db_path,
        now=wall_now + timedelta(days=3),
        allow_copied_state_clock_override=True,
        production_store=db_path,
        process_scanner=lambda: [],
    )
    assert rc_live_ref == cli.EXIT_USAGE_REFUSED
    assert res_live_ref["reason"] == "APPLY_LIVE_DB_FORBIDS_CLOCK_OVERRIDE"
    assert res_live_ref["live_production_db"] is True
    assert _sha256_file(db_path) == before_hash

    monkeypatch.setattr(cli, "PRODUCTION_STORE", db_path)
    rc_live_cli = cli.main(
        ["--apply", "--db", str(db_path), "--now-utc", eval_3d_ahead, "--allow-copied-state-clock-override"]
    )
    assert rc_live_cli == cli.EXIT_USAGE_REFUSED
    live_cli_out = json.loads(capsys.readouterr().out)
    assert live_cli_out["reason"] == "APPLY_LIVE_DB_FORBIDS_CLOCK_OVERRIDE"
    assert _sha256_file(db_path) == before_hash
    monkeypatch.undo()

    # 5. Normal wall-clock --apply (no --now-utc) retires ONLY the genuinely expired -2h page and
    #    leaves the active +1d page READY (and parent EDITORIAL_INTERNAL)!
    rc_wall = cli.main(["--apply", "--db", str(db_path)])
    assert rc_wall == cli.EXIT_OK
    wall_out = json.loads(capsys.readouterr().out)
    assert wall_out["status"] == "APPLIED"
    assert wall_out["expiry_clock_mode"] == "WALL_UTC"
    assert [m["message_id"] for m in wall_out["mutations"]["subgroup_a_retired"]] == [expired_page["message_id"]]
    assert store.get_outbox_message(expired_page["message_id"])["status"] == PLAN_PAGE_EXPIRED_STALE_NO_WRITE
    assert store.get_outbox_message(expired_page["page_id"])["status"] == "SETTLED"
    assert store.get_outbox_message(active_page["message_id"])["status"] == "READY"
    assert store.get_outbox_message(active_page["page_id"])["status"] == "EDITORIAL_INTERNAL"

    # 6. In-transaction BEGIN IMMEDIATE re-evaluation (TOCTOU guard):
    #    Seed both a Subgroup A page and a Subgroup B verified-absent page whose deadlines are -2h during
    #    pre-tx audit, then extend BOTH deadlines to +1d right before BEGIN IMMEDIATE executes.
    #    The write transaction MUST re-evaluate current page & deadline under wall UTC and retire NEITHER!
    db_tx = tmp_path / "cc908_tx_reeval.sqlite3"
    store_tx = ContentOpsDurableStore(db_tx)
    sub_a_toctou = _seed_plan_analysis_page(
        store_tx,
        plan_id="plan_toctou_sub_a",
        entry_deadline_utc=expired_deadline,
        outbox_status="READY",
    )
    sub_b_toctou = _seed_plan_analysis_page(
        store_tx,
        plan_id="plan_toctou_sub_b",
        entry_deadline_utc=expired_deadline,
        outbox_status="READY",
        dispatch_status=ATTEMPT_STARTED,
    )
    coord_tx = DurablePublicationCoordinator(
        store=store_tx,
        transport_runtime=_RecordingTransport(readback_status="ABSENT"),
        readiness_provider=lambda _: {"readiness_state": "READY_AUTHENTICATED"},
        clock=lambda: wall_now - timedelta(minutes=5),
    )
    rb_tx = coord_tx.readback_existing_dispatch(sub_b_toctou["dispatch_id"])
    assert rb_tx["reconciliation_status"] == RECONCILED_ABSENT_SAFE_TO_RETRY

    orig_audit = cli.audit_preunpause_outbox
    extended = {"done": False}

    def _audit_then_extend_deadlines(*args, **kwargs):
        result = orig_audit(*args, **kwargs)
        if not extended["done"]:
            extended["done"] = True
            with closing(store_tx.get_connection()) as conn:
                for page_id in (sub_a_toctou["page_id"], sub_b_toctou["page_id"]):
                    row = conn.execute(
                        "SELECT payload FROM outbox_messages WHERE message_id=?", (page_id,)
                    ).fetchone()
                    doc = json.loads(row["payload"])
                    doc["source_plan"]["entry_deadline_utc"] = future_deadline
                    doc["source_plan"]["expires_at_utc"] = future_deadline
                    conn.execute(
                        "UPDATE outbox_messages SET payload=? WHERE message_id=?",
                        (json.dumps(doc), page_id),
                    )
                conn.commit()
        return result

    monkeypatch.setattr(cli, "audit_preunpause_outbox", _audit_then_extend_deadlines)
    rc_tx, res_tx = cli.apply_preunpause_reconciliation(db_tx)
    assert rc_tx == cli.EXIT_OK
    assert res_tx["expiry_clock_mode"] == "WALL_UTC"
    assert res_tx["pre_audit_counts"]["subgroup_a_expired_substack_plan_pages"] == 1
    assert res_tx["pre_audit_counts"]["subgroup_b_verified_absent_eligible"] == 1
    assert res_tx["mutations"]["subgroup_a_retired"] == []
    assert res_tx["mutations"]["subgroup_b_verified_absent_retired"] == []
    assert store_tx.get_outbox_message(sub_a_toctou["message_id"])["status"] == "READY"
    assert store_tx.get_outbox_message(sub_a_toctou["page_id"])["status"] == "EDITORIAL_INTERNAL"
    assert store_tx.get_outbox_message(sub_b_toctou["message_id"])["status"] == RECONCILED_ABSENT_SAFE_TO_RETRY
    assert store_tx.get_platform_dispatch(sub_b_toctou["dispatch_id"])["status"] == RECONCILED_ABSENT_SAFE_TO_RETRY
    assert store_tx.get_outbox_message(sub_b_toctou["page_id"])["status"] == "EDITORIAL_INTERNAL"


def test_cc692_cc910_live_apply_forbids_interlock_now_override_and_enforces_wall_utc_liveness(
    tmp_path, monkeypatch
):
    """CC-910 [Medium] regression: production-bound Python apply MUST refuse any caller-provided
    interlock_now override (0 writes, active lease/heartbeat untouched), derive both preflight and
    in-transaction liveness clocks strictly from wall UTC, and preserve copied-state replay."""
    db_path = tmp_path / "cc910_live_interlock.sqlite3"
    store = ContentOpsDurableStore(db_path)
    wall_now = datetime.now(timezone.utc)
    expired_deadline = (wall_now - timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    future_interlock = wall_now + timedelta(days=2)

    expired_page = _seed_plan_analysis_page(
        store,
        plan_id="plan_cc910_expired",
        entry_deadline_utc=expired_deadline,
        outbox_status="READY",
    )

    # Seed a wall-current ACTIVE SQLite lease (+10m) AND a fresh ALIVE heartbeat (-30s).
    lease_acq = wall_now.isoformat().replace("+00:00", "Z")
    lease_exp = (wall_now + timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
    hb_seen = (wall_now - timedelta(seconds=30)).isoformat().replace("+00:00", "Z")
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            "INSERT INTO leases (lease_id, lease_key, work_item_id, owner_ref, fencing_token, acquired_at, renewed_at, expires_at, status) "
            "VALUES ('lease_cc910_live', 'cc910-live-key', NULL, 'live-writer', 9, ?, ?, ?, 'ACTIVE')",
            (lease_acq, lease_acq, lease_exp),
        )
        conn.execute(
            "INSERT INTO heartbeats (heartbeat_id, worker_id, lease_id, last_seen_at, status) "
            "VALUES ('hb_cc910_live', 'cc910-supervisor', 'lease_cc910_live', ?, 'ALIVE')",
            (hb_seen,),
        )
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    before_hash = _sha256_file(db_path)

    # 1. Production-bound apply_preunpause_reconciliation with future interlock_now (and now=None)
    #    MUST fail closed with EXIT_USAGE_REFUSED / APPLY_LIVE_DB_FORBIDS_CLOCK_OVERRIDE, 0 writes,
    #    leaving expired page READY and active lease/heartbeat completely untouched.
    rc_ref, res_ref = cli.apply_preunpause_reconciliation(
        db_path,
        interlock_now=future_interlock,
        production_store=db_path,
        process_scanner=lambda: [],
    )
    assert rc_ref == cli.EXIT_USAGE_REFUSED
    assert res_ref["status"] == "REFUSED_USAGE"
    assert res_ref["applied"] is False
    assert res_ref["reason"] == "APPLY_LIVE_DB_FORBIDS_CLOCK_OVERRIDE"
    assert res_ref["live_production_db"] is True
    assert _sha256_file(db_path) == before_hash
    assert store.get_outbox_message(expired_page["message_id"])["status"] == "READY"
    with closing(sqlite3.connect(db_path)) as conn:
        lease_row = conn.execute(
            "SELECT status, expires_at FROM leases WHERE lease_id='lease_cc910_live'"
        ).fetchone()
        hb_row = conn.execute(
            "SELECT status, last_seen_at FROM heartbeats WHERE heartbeat_id='hb_cc910_live'"
        ).fetchone()
    assert lease_row == ("ACTIVE", lease_exp)
    assert hb_row == ("ALIVE", hb_seen)

    # Also refused when PRODUCTION_STORE is bound directly (without explicit production_store kwarg)
    # and even when allow_copied_state_clock_override=True.
    monkeypatch.setattr(cli, "PRODUCTION_STORE", db_path)
    rc_ref2, res_ref2 = cli.apply_preunpause_reconciliation(
        db_path,
        interlock_now=future_interlock,
        allow_copied_state_clock_override=True,
        process_scanner=lambda: [],
    )
    assert rc_ref2 == cli.EXIT_USAGE_REFUSED
    assert res_ref2["reason"] == "APPLY_LIVE_DB_FORBIDS_CLOCK_OVERRIDE"
    assert _sha256_file(db_path) == before_hash

    # Direct check_apply_interlocks and _resolve_interlock_clock on production store also refuse
    # caller-injected interlock_now and still evaluate wall-UTC lease/heartbeat blockers.
    direct_il = cli.check_apply_interlocks(
        db_path,
        interlock_now=future_interlock,
        process_scanner=lambda: [],
    )
    assert direct_il["ok"] is False
    blocker_codes = {b["code"] for b in direct_il["blockers"]}
    assert "APPLY_LIVE_DB_FORBIDS_CLOCK_OVERRIDE" in blocker_codes
    assert "ACTIVE_SQLITE_LEASE" in blocker_codes
    assert "ACTIVE_SUPERVISOR_HEARTBEAT" in blocker_codes
    with pytest.raises(ValueError, match="APPLY_LIVE_DB_FORBIDS_CLOCK_OVERRIDE"):
        cli._resolve_interlock_clock(interlock_now=future_interlock, live_production_db=True)

    # 2. Normal production-bound apply (interlock_now=None) refuses on wall-UTC active lease & heartbeat
    #    in preflight AND inside BEGIN IMMEDIATE if a lease appears concurrently after preflight.
    rc_live_block, res_live_block = cli.apply_preunpause_reconciliation(
        db_path,
        process_scanner=lambda: [],
    )
    assert rc_live_block == cli.EXIT_INTERLOCK_REFUSED
    assert res_live_block["applied"] is False
    live_codes = {b["code"] for b in res_live_block["interlocks"]["blockers"]}
    assert "ACTIVE_SQLITE_LEASE" in live_codes
    assert "ACTIVE_SUPERVISOR_HEARTBEAT" in live_codes
    assert _sha256_file(db_path) == before_hash

    # Remove lease/heartbeat so preflight passes, then inject a fresh lease right before BEGIN IMMEDIATE
    # to prove transaction-phase liveness also uses wall UTC and rolls back with zero mutations.
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("DELETE FROM leases WHERE lease_id='lease_cc910_live'")
        conn.execute("DELETE FROM heartbeats WHERE heartbeat_id='hb_cc910_live'")
        conn.commit()
    orig_audit = cli.audit_preunpause_outbox
    injected = {"done": False}

    def _audit_then_inject_live_lease(*args, **kwargs):
        out = orig_audit(*args, **kwargs)
        if not injected["done"]:
            injected["done"] = True
            now_tx = datetime.now(timezone.utc)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.execute(
                    "INSERT INTO leases (lease_id, lease_key, work_item_id, owner_ref, fencing_token, acquired_at, renewed_at, expires_at, status) "
                    "VALUES ('lease_cc910_toctou', 'cc910-tx-key', NULL, 'live-writer', 10, ?, ?, ?, 'ACTIVE')",
                    (
                        now_tx.isoformat().replace("+00:00", "Z"),
                        now_tx.isoformat().replace("+00:00", "Z"),
                        (now_tx + timedelta(minutes=10)).isoformat().replace("+00:00", "Z"),
                    ),
                )
                conn.commit()
        return out

    monkeypatch.setattr(cli, "audit_preunpause_outbox", _audit_then_inject_live_lease)
    rc_tx_ref, res_tx_ref = cli.apply_preunpause_reconciliation(
        db_path,
        process_scanner=lambda: [],
    )
    assert rc_tx_ref == cli.EXIT_INTERLOCK_REFUSED
    assert res_tx_ref["applied"] is False
    assert any(
        b["code"] == "ACTIVE_SQLITE_LEASE" and b["lease_id"] == "lease_cc910_toctou"
        for b in res_tx_ref["interlocks"]["blockers"]
    )
    assert store.get_outbox_message(expired_page["message_id"])["status"] == "READY"
    monkeypatch.undo()

    # 3. Copied-state replay path (non-production store):
    #    - interlock_now without allow_copied_state_clock_override=True fails closed (EXIT_USAGE_REFUSED).
    #    - explicit allow_copied_state_clock_override=True preserves copied-state replay cleanly.
    copied_db = tmp_path / "cc910_copied_replay.sqlite3"
    copied_store = ContentOpsDurableStore(copied_db)
    replay_page = _seed_plan_analysis_page(
        copied_store,
        plan_id="plan_cc910_replay",
        entry_deadline_utc="2026-11-12T21:00:00Z",
        outbox_status="READY",
    )
    rc_copy_ref, res_copy_ref = cli.apply_preunpause_reconciliation(
        copied_db,
        interlock_now=future_interlock,
    )
    assert rc_copy_ref == cli.EXIT_USAGE_REFUSED
    assert res_copy_ref["reason"] == "APPLY_CLOCK_OVERRIDE_REQUIRES_COPIED_STATE_REPLAY"
    assert copied_store.get_outbox_message(replay_page["message_id"])["status"] == "READY"

    replay_now = datetime(2026, 11, 29, 18, 0, 0, tzinfo=timezone.utc)
    rc_copy_ok, res_copy_ok = cli.apply_preunpause_reconciliation(
        copied_db,
        now=replay_now,
        interlock_now=wall_now,
        allow_copied_state_clock_override=True,
    )
    assert rc_copy_ok == cli.EXIT_OK
    assert res_copy_ok["applied"] is True
    assert res_copy_ok["expiry_clock_mode"] == "COPIED_STATE_REPLAY_OVERRIDE"
    assert copied_store.get_outbox_message(replay_page["message_id"])["status"] == PLAN_PAGE_EXPIRED_STALE_NO_WRITE


def test_cc692_cc915_optional_production_store_is_additive_and_keeps_canonical_on_wall_utc(
    tmp_path, monkeypatch
):
    """CC-915 [Medium] regression: injecting a distinct optional production_store MUST be additive
    (never replacing canonical PRODUCTION_STORE) so the canonical stand-in still classifies as
    production on wall UTC, runs default control/process checks, and blocks apply on active
    lease/heartbeat."""
    canonical_dir = tmp_path / "canonical_runtime"
    additional_dir = tmp_path / "additional_runtime"
    copied_dir = tmp_path / "copied_replay"
    canonical_dir.mkdir(parents=True, exist_ok=True)
    additional_dir.mkdir(parents=True, exist_ok=True)
    copied_dir.mkdir(parents=True, exist_ok=True)

    canonical_db = canonical_dir / "contentops_daily_app_v1.sqlite3"
    additional_db = additional_dir / "additional_prod.sqlite3"
    copied_db = copied_dir / "copied_replay.sqlite3"

    canonical_store = ContentOpsDurableStore(canonical_db)
    additional_store = ContentOpsDurableStore(additional_db)
    copied_store = ContentOpsDurableStore(copied_db)

    wall_now = datetime.now(timezone.utc)
    expired_deadline = (wall_now - timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    future_override = wall_now + timedelta(days=3)

    canonical_page = _seed_plan_analysis_page(
        canonical_store,
        plan_id="plan_cc915_canonical_expired",
        entry_deadline_utc=expired_deadline,
        outbox_status="READY",
    )
    additional_page = _seed_plan_analysis_page(
        additional_store,
        plan_id="plan_cc915_additional_expired",
        entry_deadline_utc=expired_deadline,
        outbox_status="READY",
    )
    copied_page = _seed_plan_analysis_page(
        copied_store,
        plan_id="plan_cc915_copied_expired",
        entry_deadline_utc="2026-11-12T21:00:00Z",
        outbox_status="READY",
    )

    lease_acq = wall_now.isoformat().replace("+00:00", "Z")
    lease_exp = (wall_now + timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
    hb_seen = (wall_now - timedelta(seconds=30)).isoformat().replace("+00:00", "Z")
    for target_db in (canonical_db, additional_db):
        with closing(sqlite3.connect(target_db)) as conn:
            conn.execute(
                "INSERT INTO leases (lease_id, lease_key, work_item_id, owner_ref, fencing_token, acquired_at, renewed_at, expires_at, status) "
                "VALUES ('lease_cc915_live', 'cc915-live-key', NULL, 'live-writer', 11, ?, ?, ?, 'ACTIVE')",
                (lease_acq, lease_acq, lease_exp),
            )
            conn.execute(
                "INSERT INTO heartbeats (heartbeat_id, worker_id, lease_id, last_seen_at, status) "
                "VALUES ('hb_cc915_live', 'cc915-supervisor', 'lease_cc915_live', ?, 'ALIVE')",
                (hb_seen,),
            )
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    canonical_before_hash = _sha256_file(canonical_db)
    additional_before_hash = _sha256_file(additional_db)

    monkeypatch.setattr(cli, "PRODUCTION_STORE", canonical_db)

    # 1. Identity classification: canonical ALWAYS classifies as production even when a distinct
    #    optional production_store is supplied; the optional identity is additive; third copies stay non-live.
    assert cli.is_live_production_db(canonical_db) is True
    assert cli.is_live_production_db(canonical_db, production_store=additional_db) is True
    assert cli.is_live_production_db(additional_db, production_store=additional_db) is True
    assert cli.is_live_production_db(copied_db, production_store=additional_db) is False

    # 2. Clock selection: _resolve_apply_expiry_clock classifies canonical as production and refuses
    #    clock overrides even when a distinct optional production_store is injected.
    exp_dt, exp_refusal, exp_mode, exp_live = cli._resolve_apply_expiry_clock(
        db_path=canonical_db,
        now=future_override,
        interlock_now=future_override,
        allow_copied_state_clock_override=True,
        production_store=additional_db,
    )
    assert exp_dt is None
    assert exp_refusal == "APPLY_LIVE_DB_FORBIDS_CLOCK_OVERRIDE"
    assert exp_mode == "REFUSED"
    assert exp_live is True

    # 3. apply_preunpause_reconciliation on canonical with distinct optional production_store:
    #    - clock overrides refused fail-closed with 0 writes;
    #    - wall-UTC apply STILL invokes default process scan and blocks on canonical's active lease & heartbeat.
    rc_override, res_override = cli.apply_preunpause_reconciliation(
        canonical_db,
        now=future_override,
        interlock_now=future_override,
        allow_copied_state_clock_override=True,
        production_store=additional_db,
        process_scanner=lambda: [],
    )
    assert rc_override == cli.EXIT_USAGE_REFUSED
    assert res_override["reason"] == "APPLY_LIVE_DB_FORBIDS_CLOCK_OVERRIDE"
    assert res_override["live_production_db"] is True
    assert _sha256_file(canonical_db) == canonical_before_hash

    scanner_calls = {"count": 0}

    def _recording_scanner() -> list[dict]:
        scanner_calls["count"] += 1
        return []

    rc_apply, res_apply = cli.apply_preunpause_reconciliation(
        canonical_db,
        production_store=additional_db,
        process_scanner=_recording_scanner,
    )
    assert rc_apply == cli.EXIT_INTERLOCK_REFUSED
    assert res_apply["applied"] is False
    assert res_apply["expiry_clock_mode"] == "WALL_UTC"
    assert res_apply["interlocks"]["live_production_db"] is True
    assert scanner_calls["count"] == 1
    blocker_codes = {b["code"] for b in res_apply["interlocks"]["blockers"]}
    assert "ACTIVE_SQLITE_LEASE" in blocker_codes
    assert "ACTIVE_SUPERVISOR_HEARTBEAT" in blocker_codes
    assert _sha256_file(canonical_db) == canonical_before_hash
    assert canonical_store.get_outbox_message(canonical_page["message_id"])["status"] == "READY"

    # 4. Control-dir interlock check uses canonical's control/restored.json even when an alternate
    #    control_dir AND distinct optional production_store are supplied.
    canonical_restored = canonical_dir / "control" / "restored.json"
    canonical_restored.parent.mkdir(parents=True, exist_ok=True)
    canonical_restored.write_text('{"started_at_utc":"2026-11-27T00:00:00Z"}\n', encoding="utf-8")
    alt_control = tmp_path / "empty_alt_control"
    alt_control.mkdir(parents=True, exist_ok=True)
    il_canonical = cli.check_apply_interlocks(
        canonical_db,
        interlock_now=future_override,
        control_dir=alt_control,
        production_store=additional_db,
        process_scanner=_recording_scanner,
    )
    assert il_canonical["ok"] is False
    assert il_canonical["live_production_db"] is True
    assert scanner_calls["count"] == 2
    il_codes = {b["code"] for b in il_canonical["blockers"]}
    assert "APPLY_LIVE_DB_FORBIDS_CLOCK_OVERRIDE" in il_codes
    assert "RESTORED_JSON_EXISTS" in il_codes
    assert "ACTIVE_SQLITE_LEASE" in il_codes
    assert "ACTIVE_SUPERVISOR_HEARTBEAT" in il_codes
    assert any(
        b["code"] == "RESTORED_JSON_EXISTS"
        and os.path.normcase(b["path"]) == os.path.normcase(str(canonical_restored))
        for b in il_canonical["blockers"]
    )
    canonical_restored.unlink()

    # 5. Additive additional_db ALSO enforces wall-UTC production guards, while third-party copied_db
    #    retains explicit copied-state replay behavior.
    rc_add, res_add = cli.apply_preunpause_reconciliation(
        additional_db,
        production_store=additional_db,
        process_scanner=_recording_scanner,
    )
    assert rc_add == cli.EXIT_INTERLOCK_REFUSED
    assert res_add["interlocks"]["live_production_db"] is True
    assert scanner_calls["count"] == 3
    add_codes = {b["code"] for b in res_add["interlocks"]["blockers"]}
    assert "ACTIVE_SQLITE_LEASE" in add_codes
    assert "ACTIVE_SUPERVISOR_HEARTBEAT" in add_codes
    assert _sha256_file(additional_db) == additional_before_hash
    assert additional_store.get_outbox_message(additional_page["message_id"])["status"] == "READY"

    replay_now = datetime(2026, 11, 29, 18, 0, 0, tzinfo=timezone.utc)
    rc_copied, res_copied = cli.apply_preunpause_reconciliation(
        copied_db,
        now=replay_now,
        interlock_now=wall_now,
        allow_copied_state_clock_override=True,
        production_store=additional_db,
        process_scanner=_recording_scanner,
    )
    assert rc_copied == cli.EXIT_OK
    assert res_copied["applied"] is True
    assert res_copied["expiry_clock_mode"] == "COPIED_STATE_REPLAY_OVERRIDE"
    assert res_copied["interlocks"]["live_production_db"] is False
    assert scanner_calls["count"] == 3
    assert copied_store.get_outbox_message(copied_page["message_id"])["status"] == PLAN_PAGE_EXPIRED_STALE_NO_WRITE


def test_cc692_cc926_same_file_alias_resolves_canonical_sqlite_wal_namespace(
    tmp_path, monkeypatch, capsys
):
    """CC-926 [Medium] regression: a same-file hard link / alias matching a canonical or configured
    production store MUST resolve to ONE canonical configured SQLite pathname so liveness reads,
    audits, and write transactions all share its authoritative -wal/-shm journal namespace.

    Proves with a real uncheckpointed SQLite WAL containing active lease & fresh supervisor
    heartbeat rows, an NTFS hard link alias (os.link), and a distinct additional configured
    production store that BOTH the configured path AND the same-file alias detect the exact same
    ACTIVE_SQLITE_LEASE and ACTIVE_SUPERVISOR_HEARTBEAT blockers (and never create alias -wal/-shm),
    while preserving copied-store replay clock and settlement behavior.
    """
    canonical_dir = tmp_path / "canonical_runtime"
    canonical_alias_dir = tmp_path / "canonical_alias_dir"
    additional_dir = tmp_path / "additional_runtime"
    additional_alias_dir = tmp_path / "additional_alias_dir"
    copied_dir = tmp_path / "copied_replay"
    for folder in (
        canonical_dir,
        canonical_alias_dir,
        additional_dir,
        additional_alias_dir,
        copied_dir,
    ):
        folder.mkdir(parents=True, exist_ok=True)

    canonical_db = canonical_dir / "contentops_daily_app_v1.sqlite3"
    canonical_alias = canonical_alias_dir / "hardlink_canonical_alias.sqlite3"
    additional_db = additional_dir / "additional_prod.sqlite3"
    additional_alias = additional_alias_dir / "hardlink_additional_alias.sqlite3"
    copied_db = copied_dir / "copied_replay.sqlite3"

    canonical_store = ContentOpsDurableStore(canonical_db)
    additional_store = ContentOpsDurableStore(additional_db)
    copied_store = ContentOpsDurableStore(copied_db)

    wall_now = datetime.now(timezone.utc)
    expired_deadline = (wall_now - timedelta(hours=2)).isoformat().replace("+00:00", "Z")

    canonical_page = _seed_plan_analysis_page(
        canonical_store,
        plan_id="plan_cc926_canonical_expired",
        entry_deadline_utc=expired_deadline,
        outbox_status="READY",
    )
    additional_page = _seed_plan_analysis_page(
        additional_store,
        plan_id="plan_cc926_additional_expired",
        entry_deadline_utc=expired_deadline,
        outbox_status="READY",
    )
    copied_page = _seed_plan_analysis_page(
        copied_store,
        plan_id="plan_cc926_copied_expired",
        entry_deadline_utc="2026-11-12T21:00:00Z",
        outbox_status="READY",
    )

    # Flush base pages to the main DB files before creating hard links and uncheckpointed WAL rows.
    for target_db in (canonical_db, additional_db, copied_db):
        with closing(sqlite3.connect(target_db)) as conn:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    os.link(canonical_db, canonical_alias)
    os.link(additional_db, additional_alias)
    assert os.path.samefile(canonical_db, canonical_alias)
    assert os.path.samefile(additional_db, additional_alias)
    assert not os.path.samefile(canonical_db, additional_db)
    assert not os.path.samefile(canonical_db, copied_db)

    monkeypatch.setattr(cli, "PRODUCTION_STORE", canonical_db)

    canonical_wal = Path(f"{canonical_db}-wal")
    canonical_alias_wal = Path(f"{canonical_alias}-wal")
    canonical_alias_shm = Path(f"{canonical_alias}-shm")
    additional_wal = Path(f"{additional_db}-wal")
    additional_alias_wal = Path(f"{additional_alias}-wal")
    additional_alias_shm = Path(f"{additional_alias}-shm")

    lease_acq = wall_now.isoformat().replace("+00:00", "Z")
    lease_exp = (wall_now + timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
    hb_seen = (wall_now - timedelta(seconds=30)).isoformat().replace("+00:00", "Z")

    canonical_writer = sqlite3.connect(str(canonical_db), isolation_level=None)
    additional_writer = sqlite3.connect(str(additional_db), isolation_level=None)
    try:
        for writer, lease_id, hb_id, worker_id in (
            (canonical_writer, "lease_cc926_canon_wal", "hb_cc926_canon_wal", "cc926-canon-sup"),
            (additional_writer, "lease_cc926_add_wal", "hb_cc926_add_wal", "cc926-add-sup"),
        ):
            writer.execute("PRAGMA journal_mode=WAL")
            writer.execute("PRAGMA wal_autocheckpoint=0")
            writer.execute("BEGIN IMMEDIATE")
            writer.execute(
                "INSERT INTO leases (lease_id, lease_key, work_item_id, owner_ref, fencing_token, acquired_at, renewed_at, expires_at, status) "
                "VALUES (?, ?, NULL, 'live-writer', 12, ?, ?, ?, 'ACTIVE')",
                (lease_id, f"{lease_id}-key", lease_acq, lease_acq, lease_exp),
            )
            writer.execute(
                "INSERT INTO heartbeats (heartbeat_id, worker_id, lease_id, last_seen_at, status) "
                "VALUES (?, ?, ?, ?, 'ALIVE')",
                (hb_id, worker_id, lease_id, hb_seen),
            )
            writer.execute("COMMIT")

        # Also insert an expired Subgroup A page solely inside canonical's uncheckpointed WAL so
        # audit_preunpause_outbox via the alias proves WAL visibility for audit reads too.
        wal_only_page_id = "plan-analysis-plan_cc926_wal_only"
        wal_only_msg_id = "outbox_cc926_wal_only_sub"
        wal_only_parent_payload = json.dumps(
            {
                "plan_id": "plan_cc926_wal_only",
                "source_plan": {
                    "plan_id": "plan_cc926_wal_only",
                    "status": "WAITING",
                    "entry_deadline_utc": expired_deadline,
                    "expires_at_utc": expired_deadline,
                },
            }
        )
        wal_only_sub_payload = json.dumps(
            {
                "work_item_id": wal_only_page_id,
                "plan_hash": "hash_cc926_wal_only",
                "plan_analysis_page": wal_only_page_id,
                "destination": "substack",
            }
        )
        canonical_writer.execute("BEGIN IMMEDIATE")
        canonical_writer.execute(
            "INSERT INTO work_items (work_item_id, story_id, title, current_state, state_version, target_surface, created_at, updated_at) "
            "VALUES (?, ?, 'WAL-only expired page', 'OUTBOX_READY', 1, 'SUBSTACK_ARTICLE', ?, ?)",
            (wal_only_page_id, wal_only_page_id, lease_acq, lease_acq),
        )
        canonical_writer.execute(
            "INSERT INTO outbox_messages (message_id, work_item_id, destination, payload, status, created_at) "
            "VALUES (?, ?, 'internal:plan-analysis-page', ?, 'EDITORIAL_INTERNAL', ?)",
            (wal_only_page_id, wal_only_page_id, wal_only_parent_payload, lease_acq),
        )
        canonical_writer.execute(
            "INSERT INTO outbox_messages (message_id, work_item_id, destination, payload, status, created_at) "
            "VALUES (?, ?, 'substack', ?, 'READY', ?)",
            (wal_only_msg_id, wal_only_page_id, wal_only_sub_payload, lease_acq),
        )
        canonical_writer.execute("COMMIT")

        # Prove the active lease/heartbeat rows live ONLY in the real uncheckpointed canonical/additional WALs.
        assert canonical_wal.is_file() and canonical_wal.stat().st_size > 0
        assert not canonical_alias_wal.exists()
        assert additional_wal.is_file() and additional_wal.stat().st_size > 0
        assert not additional_alias_wal.exists()
        with closing(
            sqlite3.connect(f"file:{canonical_db.resolve().as_posix()}?mode=ro&immutable=1", uri=True)
        ) as main_only_conn:
            assert main_only_conn.execute("SELECT COUNT(*) FROM leases").fetchone()[0] == 0
            assert main_only_conn.execute("SELECT COUNT(*) FROM heartbeats").fetchone()[0] == 0

        canonical_db_hash_before = _sha256_file(canonical_db)
        canonical_wal_hash_before = _sha256_file(canonical_wal)
        additional_db_hash_before = _sha256_file(additional_db)
        additional_wal_hash_before = _sha256_file(additional_wal)

        # 1. Single canonical configured pathname resolution across canonical, alias, additional, and copied paths.
        assert cli.resolve_sqlite_db_path(canonical_db, production_store=additional_db) == canonical_db.resolve()
        assert cli.resolve_sqlite_db_path(canonical_alias, production_store=additional_db) == canonical_db.resolve()
        # Even passing the alias as production_store keeps canonical PRODUCTION_STORE precedence.
        assert cli.resolve_sqlite_db_path(canonical_alias, production_store=canonical_alias) == canonical_db.resolve()
        assert cli.resolve_sqlite_db_path(additional_db, production_store=additional_db) == additional_db.resolve()
        assert cli.resolve_sqlite_db_path(additional_alias, production_store=additional_db) == additional_db.resolve()
        assert cli.resolve_sqlite_db_path(copied_db, production_store=additional_db) == copied_db

        scanner_calls = {"count": 0}

        def _zero_process_scanner() -> list[dict]:
            scanner_calls["count"] += 1
            return []

        # 2. Liveness interlocks: configured path AND same-file alias detect the exact same WAL blockers.
        il_canon = cli.check_apply_interlocks(
            canonical_db,
            production_store=additional_db,
            process_scanner=_zero_process_scanner,
        )
        il_alias = cli.check_apply_interlocks(
            canonical_alias,
            production_store=additional_db,
            process_scanner=_zero_process_scanner,
        )
        il_alias_self_prod = cli.check_apply_interlocks(
            canonical_alias,
            production_store=canonical_alias,
            process_scanner=_zero_process_scanner,
        )
        for il in (il_canon, il_alias, il_alias_self_prod):
            assert il["ok"] is False
            assert il["live_production_db"] is True
            assert il["resolved_db_path"] == str(canonical_db.resolve())
            assert {b["code"] for b in il["blockers"]} == {
                "ACTIVE_SQLITE_LEASE",
                "ACTIVE_SUPERVISOR_HEARTBEAT",
            }
            assert any(b.get("lease_id") == "lease_cc926_canon_wal" for b in il["blockers"])
            assert any(b.get("heartbeat_id") == "hb_cc926_canon_wal" for b in il["blockers"])
        assert scanner_calls["count"] == 3

        # 3. Read-only audit & CLI --dry-run via alias read canonical WAL and see the WAL-only row.
        audit_canon = cli.audit_preunpause_outbox(
            canonical_db, now=wall_now, production_store=additional_db
        )
        audit_alias = cli.audit_preunpause_outbox(
            canonical_alias, now=wall_now, production_store=additional_db
        )
        assert audit_canon["db_path"] == str(canonical_db.resolve())
        assert audit_alias["db_path"] == str(canonical_db.resolve())
        expected_expired_ids = {canonical_page["message_id"], wal_only_msg_id}
        assert {
            row["message_id"] for row in audit_canon["subgroup_a_expired_substack_plan_pages"]
        } == expected_expired_ids
        assert {
            row["message_id"] for row in audit_alias["subgroup_a_expired_substack_plan_pages"]
        } == expected_expired_ids

        rc_dry_alias = cli.main(["--db", str(canonical_alias)])
        assert rc_dry_alias == cli.EXIT_OK
        dry_alias_out = json.loads(capsys.readouterr().out)
        assert dry_alias_out["apply_interlocks_preview"]["ok"] is False
        assert dry_alias_out["apply_interlocks_preview"]["resolved_db_path"] == str(canonical_db.resolve())
        assert {
            b["code"] for b in dry_alias_out["apply_interlocks_preview"]["blockers"]
        } == {"ACTIVE_SQLITE_LEASE", "ACTIVE_SUPERVISOR_HEARTBEAT"}
        assert dry_alias_out["audit"]["db_path"] == str(canonical_db.resolve())
        assert dry_alias_out["audit"]["counts"]["subgroup_a_expired_substack_plan_pages"] == 2

        # 4. apply_preunpause_reconciliation on configured path AND same-file alias both block on WAL rows
        #    with zero mutation to DB/WAL and zero alias WAL/SHM creation.
        rc_c, res_c = cli.apply_preunpause_reconciliation(
            canonical_db,
            production_store=additional_db,
            process_scanner=_zero_process_scanner,
        )
        rc_a, res_a = cli.apply_preunpause_reconciliation(
            canonical_alias,
            production_store=additional_db,
            process_scanner=_zero_process_scanner,
        )
        for rc, res in ((rc_c, res_c), (rc_a, res_a)):
            assert rc == cli.EXIT_INTERLOCK_REFUSED
            assert res["applied"] is False
            assert res["expiry_clock_mode"] == "WALL_UTC"
            assert res["resolved_db_path"] == str(canonical_db.resolve())
            assert res["interlocks"]["resolved_db_path"] == str(canonical_db.resolve())
            assert res["audit"]["db_path"] == str(canonical_db.resolve())
            assert {b["code"] for b in res["interlocks"]["blockers"]} == {
                "ACTIVE_SQLITE_LEASE",
                "ACTIVE_SUPERVISOR_HEARTBEAT",
            }
        assert _sha256_file(canonical_db) == canonical_db_hash_before
        assert _sha256_file(canonical_wal) == canonical_wal_hash_before
        assert not canonical_alias_wal.exists()
        assert not canonical_alias_shm.exists()

        # 5. Additional configured production_store AND its same-file alias ALSO resolve to additional_db
        #    and detect identical uncheckpointed WAL blockers from additional_db-wal.
        rc_add_c, res_add_c = cli.apply_preunpause_reconciliation(
            additional_db,
            production_store=additional_db,
            process_scanner=_zero_process_scanner,
        )
        rc_add_a, res_add_a = cli.apply_preunpause_reconciliation(
            additional_alias,
            production_store=additional_db,
            process_scanner=_zero_process_scanner,
        )
        for rc, res in ((rc_add_c, res_add_c), (rc_add_a, res_add_a)):
            assert rc == cli.EXIT_INTERLOCK_REFUSED
            assert res["applied"] is False
            assert res["resolved_db_path"] == str(additional_db.resolve())
            assert res["interlocks"]["live_production_db"] is True
            assert res["interlocks"]["resolved_db_path"] == str(additional_db.resolve())
            assert {b["code"] for b in res["interlocks"]["blockers"]} == {
                "ACTIVE_SQLITE_LEASE",
                "ACTIVE_SUPERVISOR_HEARTBEAT",
            }
            assert any(b.get("lease_id") == "lease_cc926_add_wal" for b in res["interlocks"]["blockers"])
            assert any(b.get("heartbeat_id") == "hb_cc926_add_wal" for b in res["interlocks"]["blockers"])
        assert _sha256_file(additional_db) == additional_db_hash_before
        assert _sha256_file(additional_wal) == additional_wal_hash_before
        assert not additional_alias_wal.exists()
        assert not additional_alias_shm.exists()
        assert additional_store.get_outbox_message(additional_page["message_id"])["status"] == "READY"

        # 6. Write-transaction path via same-file alias uses canonical SQLite pathname & WAL:
        #    6a. TOCTOU active lease committed into canonical_db-wal after preflight is caught inside
        #        BEGIN IMMEDIATE and rolled back without creating any alias -wal/-shm.
        canonical_writer.execute("BEGIN IMMEDIATE")
        canonical_writer.execute("DELETE FROM leases WHERE lease_id='lease_cc926_canon_wal'")
        canonical_writer.execute("DELETE FROM heartbeats WHERE heartbeat_id='hb_cc926_canon_wal'")
        canonical_writer.execute("COMMIT")

        orig_audit = cli.audit_preunpause_outbox
        injected = {"done": False}
        audit_seen_paths: list[Path] = []

        def _audit_then_inject_wal_lease(target_path, *args, **kwargs):
            audit_seen_paths.append(Path(target_path))
            out = orig_audit(target_path, *args, **kwargs)
            if not injected["done"]:
                injected["done"] = True
                now_tx = datetime.now(timezone.utc)
                canonical_writer.execute("BEGIN IMMEDIATE")
                canonical_writer.execute(
                    "INSERT INTO leases (lease_id, lease_key, work_item_id, owner_ref, fencing_token, acquired_at, renewed_at, expires_at, status) "
                    "VALUES ('lease_cc926_toctou_wal', 'cc926-toctou-key', NULL, 'live-writer', 13, ?, ?, ?, 'ACTIVE')",
                    (
                        now_tx.isoformat().replace("+00:00", "Z"),
                        now_tx.isoformat().replace("+00:00", "Z"),
                        (now_tx + timedelta(minutes=10)).isoformat().replace("+00:00", "Z"),
                    ),
                )
                canonical_writer.execute("COMMIT")
            return out

        monkeypatch.setattr(cli, "audit_preunpause_outbox", _audit_then_inject_wal_lease)
        rc_toctou, res_toctou = cli.apply_preunpause_reconciliation(
            canonical_alias,
            production_store=additional_db,
            process_scanner=_zero_process_scanner,
        )
        monkeypatch.setattr(cli, "audit_preunpause_outbox", orig_audit)
        assert rc_toctou == cli.EXIT_INTERLOCK_REFUSED
        assert res_toctou["applied"] is False
        assert res_toctou["resolved_db_path"] == str(canonical_db.resolve())
        assert audit_seen_paths == [canonical_db.resolve()]
        assert any(
            b["code"] == "ACTIVE_SQLITE_LEASE" and b["lease_id"] == "lease_cc926_toctou_wal"
            for b in res_toctou["interlocks"]["blockers"]
        )
        assert not canonical_alias_wal.exists()
        assert not canonical_alias_shm.exists()
        assert canonical_store.get_outbox_message(canonical_page["message_id"])["status"] == "READY"

        #    6b. Once interlocks are genuinely clear, apply via canonical_alias writes through
        #        canonical_db's WAL namespace and NEVER creates canonical_alias-wal or -shm.
        canonical_writer.execute("BEGIN IMMEDIATE")
        canonical_writer.execute("DELETE FROM leases WHERE lease_id='lease_cc926_toctou_wal'")
        canonical_writer.execute("COMMIT")

        rc_apply_alias, res_apply_alias = cli.apply_preunpause_reconciliation(
            canonical_alias,
            production_store=additional_db,
            process_scanner=_zero_process_scanner,
        )
        assert rc_apply_alias == cli.EXIT_OK
        assert res_apply_alias["applied"] is True
        assert res_apply_alias["expiry_clock_mode"] == "WALL_UTC"
        assert res_apply_alias["resolved_db_path"] == str(canonical_db.resolve())
        assert {
            m["message_id"] for m in res_apply_alias["mutations"]["subgroup_a_retired"]
        } == expected_expired_ids
        assert not canonical_alias_wal.exists()
        assert not canonical_alias_shm.exists()
        assert (
            canonical_store.get_outbox_message(canonical_page["message_id"])["status"]
            == PLAN_PAGE_EXPIRED_STALE_NO_WRITE
        )
        assert (
            canonical_store.get_outbox_message(wal_only_msg_id)["status"]
            == PLAN_PAGE_EXPIRED_STALE_NO_WRITE
        )

        # 7. Supported copied-store replay clock and settlement path stays intact.
        scanner_before_copied = scanner_calls["count"]
        replay_now = datetime(2026, 11, 29, 18, 0, 0, tzinfo=timezone.utc)
        rc_copied, res_copied = cli.apply_preunpause_reconciliation(
            copied_db,
            now=replay_now,
            interlock_now=wall_now,
            allow_copied_state_clock_override=True,
            production_store=additional_db,
            process_scanner=_zero_process_scanner,
        )
        assert rc_copied == cli.EXIT_OK
        assert res_copied["applied"] is True
        assert res_copied["expiry_clock_mode"] == "COPIED_STATE_REPLAY_OVERRIDE"
        assert res_copied["interlocks"]["live_production_db"] is False
        assert res_copied["resolved_db_path"] == str(copied_db)
        assert scanner_calls["count"] == scanner_before_copied
        assert (
            copied_store.get_outbox_message(copied_page["message_id"])["status"]
            == PLAN_PAGE_EXPIRED_STALE_NO_WRITE
        )
    finally:
        canonical_writer.close()
        additional_writer.close()
