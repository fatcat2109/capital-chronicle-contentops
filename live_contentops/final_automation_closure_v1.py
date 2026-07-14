"""Final RC repair and release-readiness closure operations."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from .edge_cdp_publishing_adapter_v1 import (
    delete_threads_post_via_edge_exact,
    edit_existing_linkedin_post_via_edge,
    readback_linkedin_activity_via_edge,
    verify_threads_post_unavailable_via_edge,
)
from .facebook_page_adapter_v6 import execute_facebook_edit, readback_facebook_post
from .threads_adapter_v6 import execute_threads_delete_exact, execute_threads_post, readback_threads_chain, readback_threads_post

TASK_LABEL = "TASK_CONTENTOPS_FINAL_AUTOMATION_PIPELINE_CLOSURE_LIVE_REPAIR_CANARY_AND_V1_0_RC_V1"
RC_DIR = Path("docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/contentops_v1_0_rc_20260711_1")
FED_DIR = Path("docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1")
AUTHORIZED_THREADS_TARGETS = {
    "17967130901934350": {
        "url": "https://www.threads.com/@official.capitalchronicle/post/DaoFORbk9vY",
        "text": "Why it matters: Reopened Hormuz transit, restored shut-in production and rebuilding inventories determine whether the supply recovery translates into a durable decline in crude prices.",
    },
    "18368836642225190": {
        "url": "https://www.threads.com/@official.capitalchronicle/post/DaoFQMQk33-",
        "text": "Policy context: Lower gasoline prices can ease headline inflation, but Federal Reserve policy still depends on broader price persistence, labor conditions and inflation expectations.",
    },
}


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required:{path}")
    return value


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _fed_restore_authority() -> dict[str, Any]:
    payloads = _read(FED_DIR / "native_payloads_v1.json")
    evidence = _read(FED_DIR / "run_evidence_v1.json")
    media = dict(evidence["media"]["assets"][0])
    chart_path = Path(str(media.get("path") or media.get("local_path") or ""))
    return {
        "post_id": "7481311616265895936",
        "public_url": "https://www.linkedin.com/feed/update/urn:li:activity:7481311616265895936/",
        "text": str(payloads["linkedin"]["text"]),
        "canonical_url": "https://capitalchronicle.substack.com/p/effective-fed-funds-rate-holds-at",
        "chart_path": str(chart_path.resolve()),
        "chart_sha256": hashlib.sha256(chart_path.read_bytes()).hexdigest(),
    }


def build_historical_repair_plan(*, output_dir: Path) -> dict[str, Any]:
    fed = _fed_restore_authority()
    rc = _read(RC_DIR / "run_evidence_v1.json")
    plan = {
        "schema_version": "contentops.final_automation_historical_repair_plan.v1",
        "task_label": TASK_LABEL,
        "created_at_utc": _now(),
        "linkedin_restore": {**fed, "text": None, "text_sha256": _sha(fed["text"]), "text_authority_path": str(FED_DIR / "native_payloads_v1.json")},
        "threads_delete_allowlist": [{"post_id": key, **value} for key, value in AUTHORIZED_THREADS_TARGETS.items()],
        "threads_valid_chain": {
            "root_id": "18087989708109547",
            "root_url": "https://www.threads.com/@official.capitalchronicle/post/DaoGFXikwV3",
            "reply_ids": ["18402541432082518", "18166762501444151"],
        },
        "facebook_edit": {
            "post_id": str(rc["results"]["facebook_page"]["id"]),
            "public_url": str(rc["results"]["facebook_page"]["public_url"]),
            "canonical_url": str(rc["results"]["substack"]["public_url"]),
        },
        "fresh_oil_linkedin": {"status": "BLOCKED_UNTIL_REPAIRED_OIL_ARTICLE_PASSES"},
        "fresh_generalized_canary": {"status": "BLOCKED_UNTIL_GENERIC_DQR_AND_FRESHNESS_PASS"},
    }
    _write(output_dir / "historical_repair_plan_v1.json", plan)
    return plan


def restore_historical_linkedin(*, output_dir: Path, cdp_port: int) -> dict[str, Any]:
    authority = _fed_restore_authority()
    before = readback_linkedin_activity_via_edge(
        cdp_port=cdp_port,
        public_url=authority["public_url"],
        post_id=authority["post_id"],
        expected_text=authority["text"],
        canonical_url=authority["canonical_url"],
        chart_path=authority["chart_path"],
        public_screenshot_path=output_dir / "linkedin_historical_before.png",
    )
    if not (before.get("destination_identity") == "linkedin:jimcc" and before.get("meaningful_media_visible")):
        result = {"status": "BLOCKED_LINKEDIN_HISTORICAL_IDENTITY_OR_MEDIA_MISMATCH", "before": before}
        _write(output_dir / "linkedin_historical_integrity_v1.json", result)
        return result
    edit = edit_existing_linkedin_post_via_edge(
        cdp_port=cdp_port,
        public_url=authority["public_url"],
        post_id=authority["post_id"],
        text=authority["text"],
        canonical_url=authority["canonical_url"],
        public_screenshot_path=output_dir / "linkedin_historical_after.png",
    )
    after = readback_linkedin_activity_via_edge(
        cdp_port=cdp_port,
        public_url=authority["public_url"],
        post_id=authority["post_id"],
        expected_text=authority["text"],
        canonical_url=authority["canonical_url"],
        chart_path=authority["chart_path"],
    )
    result = {
        "status": "SUCCESS" if edit.get("status") == "SUCCESS" and after.get("status") == "SUCCESS" else "FAILED_LINKEDIN_HISTORICAL_RESTORE",
        "post_id": authority["post_id"],
        "public_url": authority["public_url"],
        "payload_sha256": _sha(authority["text"]),
        "media_sha256": authority["chart_sha256"],
        "before": before,
        "edit": edit,
        "after": after,
    }
    _write(output_dir / "linkedin_historical_integrity_v1.json", result)
    return result


def delete_authorized_threads_posts(*, output_dir: Path, cdp_port: int) -> dict[str, Any]:
    receipts = []
    allowlist = frozenset(AUTHORIZED_THREADS_TARGETS)
    prior_receipt_path = output_dir / "threads_exact_deletion_receipts_v1.json"
    prior_cleanup = _read(prior_receipt_path) if prior_receipt_path.is_file() else {}
    prior_receipts = {
        str(row.get("post_id") or ""): dict(row)
        for row in (prior_cleanup.get("deletion_receipts") or [])
        if isinstance(row, Mapping)
    }
    for post_id, target in AUTHORIZED_THREADS_TARGETS.items():
        if (prior_receipts.get(post_id) or {}).get("status") == "SUCCESS":
            receipts.append({**prior_receipts[post_id], "idempotency_state": "ALREADY_DELETED_VERIFIED_FROZEN"})
            continue
        receipt = execute_threads_delete_exact(
            post_id=post_id,
            expected_permalink=target["url"],
            expected_text=target["text"],
            allowed_post_ids=allowlist,
        )
        subcode = int((((receipt.get("before_readback") or {}).get("error_response") or {}).get("error") or {}).get("error_subcode") or 0)
        if receipt.get("status") == "BLOCKED_THREADS_DELETE_EXACT_IDENTITY_MISMATCH" and subcode == 33:
            unavailable = verify_threads_post_unavailable_via_edge(
                cdp_port=cdp_port,
                public_url=target["url"],
                expected_text=target["text"],
                public_screenshot_path=output_dir / f"threads_deleted_{post_id}.png",
            )
            if unavailable.get("status") == "SUCCESS":
                receipt = {
                    **receipt,
                    "status": "SUCCESS",
                    "delete_transport": "reconciled_delayed_canonical_edge_delete",
                    "after_readback": unavailable,
                    "idempotency_state": "ALREADY_DELETED_VERIFIED",
                }
            else:
                edge_retry = delete_threads_post_via_edge_exact(
                    cdp_port=cdp_port,
                    public_url=target["url"],
                    post_id=post_id,
                    expected_text=target["text"],
                    allowed_post_ids=allowlist,
                    public_screenshot_path=output_dir / f"threads_deleted_{post_id}.png",
                )
                if edge_retry.get("status") == "SUCCESS":
                    receipt = {
                        **receipt,
                        "status": "SUCCESS",
                        "delete_transport": "canonical_edge_exact_text_scoped_retry",
                        "edge_fallback": edge_retry,
                    }
        if receipt.get("status") == "FAILED_THREADS_DELETE" and int(receipt.get("error_code") or 0) == 500:
            receipt = {
                **receipt,
                "api_fallback_reason": "threads_api_application_permission_denied",
                "edge_fallback": delete_threads_post_via_edge_exact(
                    cdp_port=cdp_port,
                    public_url=target["url"],
                    post_id=post_id,
                    expected_text=target["text"],
                    allowed_post_ids=allowlist,
                    public_screenshot_path=output_dir / f"threads_deleted_{post_id}.png",
                ),
            }
            if receipt["edge_fallback"].get("status") == "SUCCESS":
                receipt["status"] = "SUCCESS"
                receipt["delete_transport"] = "canonical_edge_exact_post_fallback"
        receipts.append(receipt)
    root = readback_threads_post(
        post_id="18087989708109547",
        expected_text="EIA Sees Oil Supply Nearing Pre-War Levels as Hormuz Flows Resume",
        canonical_url="https://capitalchronicle.substack.com/p/eia-sees-oil-supply-nearing-pre-war",
    )
    chain = readback_threads_chain(
        root_id="18087989708109547",
        reply_expectations=[
            {"id": "18402541432082518", "text": AUTHORIZED_THREADS_TARGETS["17967130901934350"]["text"]},
            {"id": "18166762501444151", "text": AUTHORIZED_THREADS_TARGETS["18368836642225190"]["text"]},
        ],
    )
    chain_recovery: dict[str, Any] | None = dict(prior_cleanup.get("valid_chain_recovery") or {}) or None
    ordered = list(chain.get("ordered_replies") or [])
    first_missing = bool(ordered and not ordered[0].get("parent_child_verified"))
    second_preserved = bool(len(ordered) > 1 and ordered[1].get("parent_child_verified"))
    if first_missing and second_preserved and not (chain_recovery and chain_recovery.get("status") == "SUCCESS"):
        rc = _read(RC_DIR / "run_evidence_v1.json")
        media = next(
            dict(row) for row in rc["delivery_media_manifest"]["assets"]
            if str(row.get("media_asset_id") or "") == "recent_price"
        )
        replacement_text = AUTHORIZED_THREADS_TARGETS["17967130901934350"]["text"] + "\n\nFor informational purposes only; not financial advice."
        write = execute_threads_post(
            text=replacement_text,
            media_type="IMAGE",
            image_url=str(media["verified_public_delivery_url"]),
            reply_to_id="18087989708109547",
            expected_media_sha256=str(media["sha256"]),
        )
        replacement_id = str(write.get("id") or "")
        replacement_readback = readback_threads_post(
            post_id=replacement_id,
            expected_text=replacement_text,
            expected_media_local_path=str(media["absolute_local_source_path"]),
        ) if replacement_id else {"status": "FAILED_THREADS_REPLACEMENT_ID_MISSING"}
        chain_recovery = {
            "status": "SUCCESS" if write.get("status") == "SUCCESS" and replacement_readback.get("status") == "SUCCESS" else "FAILED_THREADS_VALID_REPLY_RESTORE",
            "reason": "authorized malformed target and valid first reply shared identical text on the Threads permalink page; exact-ID API delete was permission-blocked and the UI fallback removed the valid duplicate-text reply",
            "deleted_valid_reply_id": "18402541432082518",
            "replacement_reply_id": replacement_id or None,
            "replacement_public_url": replacement_readback.get("public_url"),
            "parent_root_id": "18087989708109547",
            "write": write,
            "readback": replacement_readback,
            "order_caveat": "replacement first-mechanism reply is newer than preserved policy-context reply 18166762501444151",
        }
    result = {
        "status": (
            "SUCCESS_WITH_REPLACED_VALID_REPLY_ORDER_CAVEAT"
            if all(row.get("status") == "SUCCESS" for row in receipts) and root.get("status") == "SUCCESS" and chain_recovery and chain_recovery.get("status") == "SUCCESS"
            else ("SUCCESS" if all(row.get("status") == "SUCCESS" for row in receipts) and root.get("status") == "SUCCESS" and chain.get("status") == "SUCCESS" else "FAILED_THREADS_EXACT_CLEANUP_OR_VALID_CHAIN_READBACK")
        ),
        "deletion_receipts": receipts,
        "preserved_valid_root": root,
        "preserved_valid_chain": chain,
        "deleted_post_ids": [row.get("post_id") for row in receipts if row.get("status") == "SUCCESS"],
        "valid_chain_recovery": chain_recovery,
    }
    _write(output_dir / "threads_exact_deletion_receipts_v1.json", result)
    return result


def repair_facebook_copy(*, output_dir: Path) -> dict[str, Any]:
    rc = _read(RC_DIR / "run_evidence_v1.json")
    payloads = _read(RC_DIR / "native_payloads_v1.json")
    original = str(payloads["facebook_page"]["text"])
    corrected = original.replace("The relevant transmission channel is Reopened", "The market mechanism is reopened")
    post_id = str(rc["results"]["facebook_page"]["id"])
    canonical_url = str(rc["results"]["substack"]["public_url"])
    primary = dict(rc["delivery_media_manifest"]["assets"][0])
    before = readback_facebook_post(post_id=post_id, expected_text=original, canonical_url=canonical_url, expected_media_local_path=str(primary["absolute_local_source_path"]))
    edit = execute_facebook_edit(post_id=post_id, message=corrected)
    after = readback_facebook_post(post_id=post_id, expected_text=corrected, canonical_url=canonical_url, expected_media_local_path=str(primary["absolute_local_source_path"]))
    result = {
        "status": "SUCCESS" if edit.get("status") == "SUCCESS" and after.get("status") == "SUCCESS" else "FAILED_FACEBOOK_COPY_REPAIR",
        "post_id": post_id,
        "public_url": after.get("public_url") or rc["results"]["facebook_page"]["public_url"],
        "payload_sha256": _sha(corrected),
        "before": before,
        "edit": edit,
        "after": after,
    }
    _write(output_dir / "facebook_copy_repair_v1.json", result)
    return result


def run_historical_repairs(*, output_dir: Path, cdp_port: int) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    build_historical_repair_plan(output_dir=output_dir)
    prior_path = output_dir / "historical_repair_result_v1.json"
    prior = _read(prior_path) if prior_path.is_file() else {}
    prior_linkedin = dict(prior.get("linkedin") or {})
    prior_threads = dict(prior.get("threads") or {})
    prior_facebook = dict(prior.get("facebook") or {})
    linkedin = prior_linkedin if prior_linkedin.get("status") == "SUCCESS" else restore_historical_linkedin(output_dir=output_dir, cdp_port=cdp_port)
    threads = prior_threads if prior_threads.get("status") == "SUCCESS" else delete_authorized_threads_posts(output_dir=output_dir, cdp_port=cdp_port)
    facebook = prior_facebook if prior_facebook.get("status") == "SUCCESS" else repair_facebook_copy(output_dir=output_dir)
    result = {
        "schema_version": "contentops.final_automation_historical_repair_result.v1",
        "task_label": TASK_LABEL,
        "classification": "PASS_HISTORICAL_RC_TARGETED_REPAIR" if all(row.get("status") == "SUCCESS" for row in (linkedin, threads, facebook)) else "BLOCKED_HISTORICAL_RC_TARGETED_REPAIR",
        "linkedin": linkedin,
        "threads": threads,
        "facebook": facebook,
        "successful_components_frozen_on_resume": [
            name for name, value in (("linkedin", prior_linkedin), ("threads", prior_threads), ("facebook", prior_facebook))
            if value.get("status") == "SUCCESS"
        ],
        "fresh_oil_linkedin_created": False,
        "oil_substack_edited": False,
    }
    _write(output_dir / "historical_repair_result_v1.json", result)
    return result


def verify_release_readiness(*, output_dir: Path, generic_result_path: Path | None = None) -> dict[str, Any]:
    repair_path = output_dir / "historical_repair_result_v1.json"
    repair = _read(repair_path) if repair_path.is_file() else {}
    generic = _read(generic_result_path) if generic_result_path and generic_result_path.is_file() else {}
    current_generic_run = bool(generic.get("generic_live_path_used") and isinstance(generic.get("results"), dict))
    if current_generic_run:
        run_dir = generic_result_path.parent if generic_result_path else output_dir
        preflight = _read(run_dir / "generic_database_preflight_result_v1.json")
        freshness = _read(run_dir / "freshness_market_state_decision_v2.json")
        release_lock = _read(run_dir / "release_candidate_lock_v1.json")
        audit = _read(run_dir / "operator_manual_audit_packet_v1.json")
        required = ("substack", "telegram", "discord", "x", "linkedin", "facebook_page", "instagram_business", "threads", "youtube")
        results = generic.get("results") or {}
        try:
            tag_absent = not subprocess.run(
                ["git", "tag", "--list", "v1.0"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            tag_absent = False
        final_repair = dict(generic.get("final_auction_logic_repair") or {})
        checks = {
            "generic_live_path_used": True,
            "legacy_topic_adapter_not_used": generic.get("legacy_topic_adapter_used") is False,
            "story_scoped_publication_authorized": preflight.get("publication_eligible") is True,
            "freshness_passed": freshness.get("decision") == "PASS" and not freshness.get("blockers"),
            "release_lock_passed": bool(
                release_lock.get("generic_live_path_used")
                and release_lock.get("legacy_topic_adapter_used") is False
                and release_lock.get("lock_sha256")
                and all(row.get("exists") for row in (release_lock.get("artifacts") or {}).values())
            ),
            "substack_plus_eight_derivatives_passed": all((results.get(name) or {}).get("status") == "SUCCESS" for name in required),
            "no_unresolved_unknown": not any("UNKNOWN" in str((results.get(name) or {}).get("status") or "") for name in required),
            "substack_caption_repair_verified": (generic.get("substack_caption_repair") or {}).get("status") == "SUCCESS",
            "final_auction_logic_repair_verified": final_repair.get("status") == "SUCCESS",
            "final_repair_numeric_claims_preserved": final_repair.get("numeric_claims_preserved") is True,
            "final_repair_derivatives_frozen": bool(
                final_repair.get("frozen_derivatives_preserved")
                and final_repair.get("derivative_writes_performed") is False
                and final_repair.get("video_adapters_invoked") is False
            ),
            "machine_audit_passed": (audit.get("machine_qa") or {}).get("status") == "PASS",
            "v1_tag_absent": tag_absent,
        }
    else:
        checks = {
            "historical_repairs_complete": repair.get("classification") == "PASS_HISTORICAL_RC_TARGETED_REPAIR",
            "oil_substack_repaired": bool(repair.get("oil_substack_edited")),
            "fresh_oil_linkedin_created": bool(repair.get("fresh_oil_linkedin_created")),
            "generic_live_path_used": bool(generic.get("generic_live_path_used")),
            "freshness_passed": bool(generic.get("freshness_passed")),
            "dqr_permissions_passed": bool(generic.get("dqr_permissions_passed")),
            "substack_plus_eight_derivatives_passed": bool(generic.get("substack_plus_eight_derivatives_passed")),
            "no_unresolved_unknown": not bool(generic.get("unresolved_unknown_writes")),
        }
    blockers = [name for name, passed in checks.items() if not passed]
    result = {
        "schema_version": "contentops.final_release_readiness_verifier.v1",
        "task_label": TASK_LABEL,
        "classification": "AWAITING_OPERATOR_FINAL_V1_0_ACCEPTANCE_NO_ENGINEERING_BLOCKERS" if not blockers else "BLOCKED_FINAL_AUTOMATION_PIPELINE_CLOSURE",
        "checks": checks,
        "blockers": blockers,
        "v1_0_tag_allowed": False,
        "release_finalizer_command": f'python -m live_contentops.eight_platform_substack_first_pipeline_v1 --run-id v1.0 --output-dir "{output_dir}" --finalize-v1-tag --operator-final-acceptance ACCEPT',
    }
    _write(output_dir / "final_release_readiness_v1.json", result)
    return result


def finalize_v1_tag(*, verifier_path: Path, operator_acceptance: str) -> dict[str, Any]:
    """Create the release tag only after an explicit, synchronized acceptance gate."""
    verifier = _read(verifier_path) if verifier_path.is_file() else {}
    checks = {
        "operator_acceptance": operator_acceptance == "ACCEPT",
        "verifier_passed": verifier.get("classification") == "AWAITING_OPERATOR_FINAL_V1_0_ACCEPTANCE_NO_ENGINEERING_BLOCKERS",
        "verifier_has_no_blockers": not bool(verifier.get("blockers")),
    }

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], check=True, capture_output=True, text=True
        ).stdout.strip()

    tag_name = "v1.0"
    tag_message = "Capital Chronicle ContentOps v1.0 — database-authorized supervised nine-surface release"
    try:
        branch = git("branch", "--show-current")
        local_head = git("rev-parse", "HEAD")
        remote_head = git("rev-parse", "origin/master")
        existing_tag = git("tag", "--list", tag_name)
    except (OSError, subprocess.CalledProcessError) as error:
        return {
            "status": "BLOCKED_RELEASE_FINALIZER_GIT_STATE_UNAVAILABLE",
            "checks": checks,
            "error_type": type(error).__name__,
            "tag_created": False,
        }
    checks.update({
        "branch_is_master": branch == "master",
        "local_matches_remote": local_head == remote_head,
        "tag_absent": not existing_tag,
    })
    if not all(checks.values()):
        return {
            "status": "BLOCKED_RELEASE_FINALIZER_PRECONDITIONS",
            "checks": checks,
            "branch": branch,
            "local_head": local_head,
            "remote_head": remote_head,
            "tag_created": False,
        }
    try:
        git("tag", "-a", tag_name, "-m", tag_message)
        git("push", "origin", tag_name)
        remote_tag = git("ls-remote", "origin", f"refs/tags/{tag_name}^{{}}")
    except (OSError, subprocess.CalledProcessError) as error:
        return {
            "status": "BLOCKED_RELEASE_TAG_CREATE_OR_PUSH_FAILED",
            "checks": checks,
            "tag": tag_name,
            "commit_sha": local_head,
            "tag_created": bool(git("tag", "--list", tag_name)),
            "error_type": type(error).__name__,
        }
    remote_commit = remote_tag.split()[0] if remote_tag else ""
    if remote_commit != local_head:
        return {
            "status": "BLOCKED_RELEASE_REMOTE_TAG_VERIFICATION_FAILED",
            "checks": checks,
            "tag": tag_name,
            "commit_sha": local_head,
            "remote_tag_commit_sha": remote_commit or None,
            "tag_created": True,
        }
    return {
        "status": "SUCCESS_RELEASE_TAG_CREATED_AND_PUSHED",
        "checks": checks,
        "tag": tag_name,
        "tag_message": tag_message,
        "commit_sha": local_head,
        "remote_tag_commit_sha": remote_commit,
        "tag_created": True,
    }
