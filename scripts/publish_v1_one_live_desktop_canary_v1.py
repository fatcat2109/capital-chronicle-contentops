"""Publish the one owner-granted Desktop-primary V1 canary through canonical transports.

This is deliberately a one-shot operator wrapper around DurablePublicationCoordinator.  It
registers and dispatches only the exact hash-bound canary work item, so unrelated durable recovery
obligations cannot cross the much narrower owner grant.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops.destination_transport_registry_v1 import (
    DestinationReadinessManager,
    V1_REQUIRED_PUBLICATION_DESTINATIONS,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.production_orchestrator_v1 import ContentOpsProductionOrchestrator
from live_contentops.publication_coordinator_v1 import (
    CanonicalDestinationTransportRuntimeV1,
    DurablePublicationCoordinator,
)


TASK = "TASK_V1_ONE_LIVE_DESKTOP_PRIMARY_HYBRID_CANARY_PUBLICATION_AND_RECONCILIATION_V1"
EXPECTED_STARTING_SHA = "bcdada4674402be42d1624cdd1ea5029617aef98"
EXPECTED_TITLE = "State Department Approves Possible APKWS II Sale to Italy"
EXPECTED_MODE = "DATA_OR_DOCUMENT_LENS"
EXPECTED_EVIDENCE_ID = "official-primary-ffb8e742e0932254c29d"
EXPECTED_MARKDOWN_SHA256 = "32bff9996e59bd924e9d41f10b4ed29fcbf9a431a38f187ee727929c12585d65"
EXPECTED_HTML_SHA256 = "2d037d6df2956779157b37a6d7ddc848a5f3b9111db339eb7bde3cbb1d1c5286"
EXPECTED_RELEASE_LOCK_SHA256 = "6c6f0c54117cf4d88478f1773de08c51c769d7e22e218af948ce5e24717c7241"
WORK_ITEM_ID = "owner-one-live-desktop-primary-hybrid-canary-6c6f0c54117c"
CONTROL_SOURCE = "OWNER_ONE_LIVE_CANARY_V1"
DERIVATIVE_ORDER = (
    "telegram",
    "discord",
    "x",
    "linkedin",
    "facebook_page",
    "instagram_business",
    "threads",
    "youtube",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(value), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _listener_active(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(0.25)
        return client.connect_ex(("127.0.0.1", int(port))) == 0


def _safe_store_snapshot(store: ContentOpsDurableStore) -> dict[str, Any]:
    dispatches = list(store.list_platform_dispatches())
    outbox = list(store.list_outbox_messages())
    reconciliations: list[dict[str, Any]] = []
    for work_item_id in sorted(
        {str(row.get("work_item_id") or "") for row in outbox if row.get("work_item_id")}
    ):
        reconciliations.extend(store.get_reconciliations_for_work_item(work_item_id))
    return {
        "captured_at_utc": _utc_now(),
        "operating_control": store.get_operating_control(),
        "dispatch_count": len(dispatches),
        "outbox_count": len(outbox),
        "reconciliation_count": len(reconciliations),
        "dispatch_status_counts": dict(Counter(str(row.get("status") or "") for row in dispatches)),
        "outbox_status_counts": dict(Counter(str(row.get("status") or "") for row in outbox)),
        "unknown_write_count": sum(
            str(row.get("status") or "") == "UNKNOWN_WRITE" for row in dispatches
        ),
        "dispatch_ids": sorted(str(row.get("dispatch_id") or "") for row in dispatches),
        "message_ids": sorted(str(row.get("message_id") or "") for row in outbox),
        "pending_obligations": [
            {
                "message_id": str(row.get("message_id") or ""),
                "work_item_id": str(row.get("work_item_id") or ""),
                "destination": str(row.get("destination") or ""),
                "status": str(row.get("status") or ""),
                "created_at": str(row.get("created_at") or ""),
            }
            for row in outbox
            if str(row.get("status") or "")
            in {"READY", "RECONCILED_ABSENT_SAFE_TO_RETRY", "UNKNOWN_WRITE"}
        ],
    }


def _safe_outcome(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value.get(key)
        for key in (
            "destination",
            "status",
            "publish_called",
            "public_object_id",
            "public_object_url",
            "reconciliation_status",
        )
        if value.get(key) not in (None, "")
    }


def _validate_locked_inputs(*, repo_root: Path, output_dir: Path) -> dict[str, Any]:
    evidence_dir = (
        repo_root
        / "docs"
        / "automation"
        / "TASK_V1_DESKTOP_PRIMARY_HYBRID_EDITORIAL_PARITY_AND_FINAL_CANARY_READY_V1"
    )
    article_markdown = evidence_dir / "article.md"
    article_html = evidence_dir / "canonical_article.html"
    canary_receipt = _read_json(evidence_dir / "canary_receipt_v1.json")
    plan = _read_json(output_dir / "publication_plan_current_jit_v1.json")
    lock = _read_json(output_dir / "release_candidate_lock_v1.json")
    run_context = _read_json(output_dir / "run_context_v1.json")
    article = dict(run_context.get("article") or {})
    destinations = {
        str(row.get("destination") or "")
        for row in (plan.get("destinations") or [])
        if isinstance(row, Mapping)
    }
    blockers: list[str] = []
    if _file_hash(article_markdown) != EXPECTED_MARKDOWN_SHA256:
        blockers.append("canonical_markdown_sha256_mismatch")
    if _file_hash(article_html) != EXPECTED_HTML_SHA256:
        blockers.append("canonical_html_sha256_mismatch")
    if str(lock.get("lock_sha256") or "") != EXPECTED_RELEASE_LOCK_SHA256:
        blockers.append("release_lock_sha256_mismatch")
    if str(plan.get("package_identity") or "") != EXPECTED_RELEASE_LOCK_SHA256:
        blockers.append("publication_plan_release_identity_mismatch")
    if str(article.get("title") or "") != EXPECTED_TITLE:
        blockers.append("article_title_mismatch")
    if str(article.get("effective_article_mode") or "") != EXPECTED_MODE:
        blockers.append("article_mode_mismatch")
    if set(article.get("evidence_document_ids") or []) != {EXPECTED_EVIDENCE_ID}:
        blockers.append("article_evidence_identity_mismatch")
    if destinations != set(V1_REQUIRED_PUBLICATION_DESTINATIONS):
        blockers.append("publication_destination_set_mismatch")
    if len(plan.get("destinations") or []) != 9:
        blockers.append("publication_destination_count_mismatch")
    if plan.get("pre_substack_blockers") or plan.get("skipped_derivative_destinations"):
        blockers.append("publication_plan_contains_holds_or_skips")
    if int((canary_receipt.get("article") or {}).get("canonical_article_media_count") or 0) != 0:
        blockers.append("canonical_article_media_count_not_zero")
    if int(canary_receipt.get("unknown_write_count") or 0) != 0:
        blockers.append("locked_canary_unknown_write_nonzero")
    artifact_text = json.dumps(
        {
            "article": article,
            "plan": plan,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    if "[[SOURCE:" in artifact_text or "pending-publication" in artifact_text:
        blockers.append("unresolved_source_or_pending_publication_marker")
    return {
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "plan": plan,
        "lock": lock,
        "article": article,
        "canonical_markdown_sha256": _file_hash(article_markdown),
        "canonical_html_sha256": _file_hash(article_html),
        "release_lock_sha256": str(lock.get("lock_sha256") or ""),
        "publication_plan_sha256": _canonical_hash(plan),
        "canonical_article_media_count": int(
            (canary_receipt.get("article") or {}).get("canonical_article_media_count") or 0
        ),
    }


def run(
    *,
    repo_root: Path,
    output_dir: Path,
    store_path: Path,
    receipt_path: Path,
    execute_owner_grant: bool,
) -> dict[str, Any]:
    locked = _validate_locked_inputs(repo_root=repo_root, output_dir=output_dir)
    if locked["status"] != "PASS":
        raise RuntimeError("locked_input_validation_failed:" + ",".join(locked["blockers"]))
    store = ContentOpsDurableStore(store_path)
    before = _safe_store_snapshot(store)
    if int(before["unknown_write_count"]) != 0:
        raise RuntimeError("preexisting_unknown_write_requires_stop")
    if any(
        str(row.get("work_item_id") or "") == WORK_ITEM_ID
        for row in store.list_outbox_messages()
    ):
        raise RuntimeError("exact_canary_work_item_already_registered_no_blind_retry")

    orchestrator = ContentOpsProductionOrchestrator()
    readiness = DestinationReadinessManager(
        store=store,
        edge_runtime_ensurer=lambda **kwargs: orchestrator.execute(
            "ensure_canonical_edge_publishing_runtime",
            urls=tuple(kwargs.get("urls") or ()),
        ),
    )
    jit = readiness.verify_full_v1_transaction_preflight(
        attempt_identity=EXPECTED_RELEASE_LOCK_SHA256,
        persist=True,
    )
    jit_destinations = dict(jit.get("destinations") or {})
    jit_ready = bool(
        jit.get("status") == "READY"
        and jit.get("all_required_destinations_ready") is True
        and int(jit.get("unknown_write_count") or 0) == 0
        and set(jit_destinations) == set(V1_REQUIRED_PUBLICATION_DESTINATIONS)
        and all(
            row.get("identity_match") is True
            and row.get("write_eligible") is True
            and str((row.get("sanitized_detail") or {}).get("jit_attempt_identity") or "")
            == EXPECTED_RELEASE_LOCK_SHA256
            for row in jit_destinations.values()
        )
    )
    prewrite = {
        "captured_at_utc": _utc_now(),
        "locked_input_status": locked["status"],
        "canonical_markdown_sha256": locked["canonical_markdown_sha256"],
        "canonical_html_sha256": locked["canonical_html_sha256"],
        "release_lock_sha256": locked["release_lock_sha256"],
        "publication_plan_sha256": locked["publication_plan_sha256"],
        "canonical_article_media_count": locked["canonical_article_media_count"],
        "store_unknown_write_count": before["unknown_write_count"],
        "daily_app_listener_5174_active": _listener_active(5174),
        "jit": jit,
        "jit_ready": jit_ready,
        "public_write_performed": False,
    }
    if not jit_ready:
        raise RuntimeError("fresh_nine_surface_jit_failed")
    if not execute_owner_grant:
        receipt = {
            "schema_version": "contentops.one_live_desktop_primary_hybrid_canary.v1",
            "task": TASK,
            "classification": "PREWRITE_READY_ZERO_PUBLIC_WRITE",
            "owner_grant_scope": {
                "title": EXPECTED_TITLE,
                "mode": EXPECTED_MODE,
                "evidence_id": EXPECTED_EVIDENCE_ID,
                "canonical_markdown_sha256": EXPECTED_MARKDOWN_SHA256,
                "canonical_html_sha256": EXPECTED_HTML_SHA256,
                "release_lock_sha256": EXPECTED_RELEASE_LOCK_SHA256,
            },
            "prewrite": prewrite,
            "store_before": before,
            "public_write_count": 0,
            "unknown_write_count": 0,
        }
        _write_json(receipt_path, receipt)
        return receipt

    if prewrite["daily_app_listener_5174_active"]:
        raise RuntimeError("daily_app_runtime_must_be_stopped_before_narrow_owner_grant")
    previous_control = dict(store.get_operating_control())
    if str(previous_control.get("operating_mode") or "") not in {
        "SHADOW_ONLY",
        "KILL_SWITCH",
        "SUPERVISED_OPERATOR_GATE",
    }:
        raise RuntimeError("unexpected_prepublication_operating_mode")

    plan = dict(locked["plan"])
    transport = CanonicalDestinationTransportRuntimeV1()
    coordinator = DurablePublicationCoordinator(
        store=store,
        transport_runtime=transport,
        readiness_manager=readiness,
    )
    registration: dict[str, Any] = {}
    outcomes: dict[str, dict[str, Any]] = {}
    delivery_media_preparation: dict[str, Any] = {
        "status": "NOT_STARTED",
        "public_write_performed": False,
    }
    canonical_url = ""
    execution_started_at = _utc_now()
    execution_error: str | None = None
    restored_control: dict[str, Any] | None = None
    try:
        active_control = store.update_operating_control(
            expected_state_version=int(previous_control["state_version"]),
            operating_mode="AUTONOMOUS_DEFAULT",
            control_source=CONTROL_SOURCE,
        )
        store.create_work_item(
            story_id=str(plan.get("story_identity") or EXPECTED_EVIDENCE_ID),
            title=EXPECTED_TITLE,
            target_surface="SUBSTACK_ARTICLE",
            work_item_id=WORK_ITEM_ID,
            actor_ref=CONTROL_SOURCE,
            correlation_id="corr_" + WORK_ITEM_ID,
        )
        registration = coordinator.register_plan(WORK_ITEM_ID, plan)
        exact_messages = {
            str(row.get("destination") or ""): row
            for row in store.list_outbox_messages()
            if str(row.get("work_item_id") or "") == WORK_ITEM_ID
        }
        if set(exact_messages) != set(V1_REQUIRED_PUBLICATION_DESTINATIONS):
            raise RuntimeError("registered_exact_destination_set_mismatch")

        substack = coordinator._dispatch_message(  # noqa: SLF001 - one-shot owner wrapper
            exact_messages["substack"],
            canonical_url=None,
        )
        outcomes["substack"] = _safe_outcome(substack)
        canonical_confirmed = bool(
            substack.get("status") == "DISPATCH_CONFIRMED"
            and substack.get("reconciliation_status") == "RECONCILED_CONFIRMED"
            and str(substack.get("public_object_url") or "").startswith(
                "https://capitalchronicle.substack.com/p/"
            )
        )
        if not canonical_confirmed:
            return_after_substack = True
        else:
            return_after_substack = False
            canonical_url = str(substack["public_object_url"])
            unknown_count = sum(
                str(row.get("status") or "") == "UNKNOWN_WRITE"
                for row in store.list_platform_dispatches()
            )
            if unknown_count:
                return_after_substack = True
            else:
                delivery_media_preparation = dict(
                    transport.prepare_delivery_media(
                        work_item_id=WORK_ITEM_ID,
                        plan=plan,
                        preconditions={
                            "canonical_publication_status": "RECONCILED_CONFIRMED",
                            "unknown_write_count": 0,
                        },
                    )
                    or {}
                )

        if not return_after_substack:
            delivery_blocked = str(delivery_media_preparation.get("status") or "") not in {
                "DELIVERY_MEDIA_PREPARATION_NOT_REQUIRED_BY_TRANSPORT",
                "CLOUDINARY_DELIVERY_MEDIA_READY",
                "CLOUDINARY_DELIVERY_MEDIA_NOT_REQUIRED",
            }
            for destination in DERIVATIVE_ORDER:
                message = exact_messages[destination]
                intent = json.loads(str(message["payload"]))
                destination_plan = dict(intent.get("destination_plan") or {})
                if delivery_blocked and destination_plan.get("delivery_media_required") is True:
                    outcomes[destination] = {
                        "destination": destination,
                        "status": str(
                            delivery_media_preparation.get("status")
                            or "DESTINATION_LOCAL_DELIVERY_MEDIA_HOLD"
                        ),
                        "publish_called": False,
                    }
                    continue
                finalized = coordinator._finalize_derivative_intent(  # noqa: SLF001
                    message,
                    canonical_url=canonical_url,
                )
                if finalized != "READY":
                    outcomes[destination] = {
                        "destination": destination,
                        "status": finalized,
                        "publish_called": False,
                    }
                    continue
                refreshed = store.get_outbox_message(str(message["message_id"])) or message
                outcome = coordinator._dispatch_message(  # noqa: SLF001
                    refreshed,
                    canonical_url=canonical_url,
                )
                outcomes[destination] = _safe_outcome(outcome)
        current_control = store.get_operating_control()
        restored_control = store.update_operating_control(
            expected_state_version=int(current_control["state_version"]),
            operating_mode=str(previous_control["operating_mode"]),
            control_source=CONTROL_SOURCE,
        )
    except Exception as exc:
        execution_error = type(exc).__name__
    finally:
        if restored_control is None:
            try:
                current_control = store.get_operating_control()
                if str(current_control.get("operating_mode") or "") == "AUTONOMOUS_DEFAULT":
                    restored_control = store.update_operating_control(
                        expected_state_version=int(current_control["state_version"]),
                        operating_mode=str(previous_control["operating_mode"]),
                        control_source=CONTROL_SOURCE,
                    )
            except Exception:
                restored_control = None

    after = _safe_store_snapshot(store)
    before_dispatch_ids = set(before["dispatch_ids"])
    before_message_ids = set(before["message_ids"])
    new_dispatches = [
        row
        for row in store.list_platform_dispatches()
        if str(row.get("dispatch_id") or "") not in before_dispatch_ids
    ]
    new_messages = [
        row
        for row in store.list_outbox_messages()
        if str(row.get("message_id") or "") not in before_message_ids
    ]
    exact_new_message_ids = {
        str(row.get("message_id") or "")
        for row in new_messages
        if str(row.get("work_item_id") or "") == WORK_ITEM_ID
    }
    extra_dispatches = [
        str(row.get("dispatch_id") or "")
        for row in new_dispatches
        if str(row.get("message_id") or "") not in exact_new_message_ids
    ]
    exact_unknown = sum(
        str(row.get("status") or "") == "UNKNOWN_WRITE"
        for row in new_dispatches
        if str(row.get("message_id") or "") in exact_new_message_ids
    )
    derivative_outcomes = {k: v for k, v in outcomes.items() if k != "substack"}
    derivative_attempted_count = sum(v.get("publish_called") is True for v in derivative_outcomes.values())
    object_confirmed_count = sum(
        str(v.get("status") or "") == "DISPATCH_CONFIRMED"
        and str(v.get("reconciliation_status") or "")
        in {"RECONCILED_CONFIRMED", "RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE"}
        for v in derivative_outcomes.values()
    )
    strict_confirmed_count = sum(
        str(v.get("status") or "") == "DISPATCH_CONFIRMED"
        and str(v.get("reconciliation_status") or "") == "RECONCILED_CONFIRMED"
        for v in derivative_outcomes.values()
    )
    readback_limited_count = sum(
        str(v.get("reconciliation_status") or "")
        == "RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE"
        for v in derivative_outcomes.values()
    )
    canonical = dict(outcomes.get("substack") or {})
    success = bool(
        canonical.get("status") == "DISPATCH_CONFIRMED"
        and canonical.get("reconciliation_status") == "RECONCILED_CONFIRMED"
        and canonical_url.startswith("https://capitalchronicle.substack.com/p/")
        and derivative_attempted_count == 8
        and strict_confirmed_count == 8
        and exact_unknown == 0
        and int(after["unknown_write_count"]) == 0
        and not extra_dispatches
        and restored_control is not None
        and str(restored_control.get("operating_mode") or "")
        == str(previous_control.get("operating_mode") or "")
    )
    receipt = {
        "schema_version": "contentops.one_live_desktop_primary_hybrid_canary.v1",
        "task": TASK,
        "classification": (
            "PASS_ONE_LIVE_DESKTOP_PRIMARY_HYBRID_CANARY_9_SURFACE_RECONCILED"
            if success
            else (
                "BLOCKED_UNKNOWN_WRITE_RECONCILIATION_REQUIRED"
                if exact_unknown or int(after["unknown_write_count"])
                else "PARTIAL_DISTRIBUTION_RECOVERY_REQUIRED"
            )
        ),
        "execution_started_at_utc": execution_started_at,
        "execution_finished_at_utc": _utc_now(),
        "execution_error_class": execution_error,
        "starting_branch_sha": EXPECTED_STARTING_SHA,
        "owner_grant_scope": {
            "title": EXPECTED_TITLE,
            "mode": EXPECTED_MODE,
            "evidence_id": EXPECTED_EVIDENCE_ID,
            "canonical_markdown_sha256": EXPECTED_MARKDOWN_SHA256,
            "canonical_html_sha256": EXPECTED_HTML_SHA256,
            "release_lock_sha256": EXPECTED_RELEASE_LOCK_SHA256,
            "other_public_writes_authorized": False,
            "automation_enablement_authorized": False,
            "four_thirty_two_start_authorized": False,
        },
        "prewrite": prewrite,
        "registration": registration,
        "canonical_url": canonical_url or None,
        "delivery_media_preparation": delivery_media_preparation,
        "per_destination": outcomes,
        "derivative_attempted_count": derivative_attempted_count,
        "derivative_confirmed_count": strict_confirmed_count,
        "derivative_public_object_confirmed_count": object_confirmed_count,
        "derivative_readback_limited_count": readback_limited_count,
        "unknown_write_count": int(after["unknown_write_count"]),
        "exact_canary_unknown_write_count": exact_unknown,
        "extra_dispatch_ids": extra_dispatches,
        "proof_no_extra_dispatch": not extra_dispatches,
        "store_before": before,
        "store_after": after,
        "operating_control_before": previous_control,
        "operating_control_restored": restored_control,
        "automation_enablement_performed": False,
        "four_thirty_two_started": False,
        "new_writer_invoked": False,
        "new_evidence_acquired": False,
    }
    _write_json(receipt_path, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--store-path", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--execute-owner-grant", action="store_true")
    args = parser.parse_args()
    receipt = run(
        repo_root=args.repo_root.resolve(),
        output_dir=args.output_dir.resolve(),
        store_path=args.store_path.resolve(),
        receipt_path=args.receipt.resolve(),
        execute_owner_grant=args.execute_owner_grant,
    )
    print(
        json.dumps(
            {
                "classification": receipt["classification"],
                "canonical_url": receipt.get("canonical_url"),
                "derivative_attempted_count": receipt.get("derivative_attempted_count", 0),
                "derivative_confirmed_count": receipt.get("derivative_confirmed_count", 0),
                "unknown_write_count": receipt.get("unknown_write_count", 0),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
