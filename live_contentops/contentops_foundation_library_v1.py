"""Public newsroom library projection over retained research and the existing report outbox.

This is a read model and an internal outbox payload, not a source/wire/store/scheduler owner.
Editorial taxonomy and qualitative questions never grant Main analytical authority.
"""
from __future__ import annotations

import json
import re
import base64
import hashlib
from typing import Mapping, Sequence
from pathlib import Path

from live_contentops.capital_chronicle_latest_report_consumer_v1 import _private, _time, sha256_of

LIBRARY = "internal:cc-foundation-library"
PACKAGE = "internal:cc-foundation-library-package"
FAMILIES = ("FX_RATES", "METALS", "ENERGY", "INDEX_OPTIONS", "COMPANY_SEC", "CRYPTO")
SOURCE_GAPS = {
    "FX_RATES": "CURRENT_MARKET_QUOTES_AND_RELATIVE_RATE_PATH_NOT_VERIFIED",
    "METALS": "CURRENT_METAL_CURVE_REAL_YIELDS_AND_FLOWS_NOT_VERIFIED",
    "ENERGY": "CURRENT_REPLACEMENT_STORAGE_RELEASE_NOT_YET_RETAINED",
    "INDEX_OPTIONS": "INDEX_OPTION_CHAIN_EXPIRY_SETTLEMENT_IV_AND_OPEN_INTEREST_NOT_RETAINED",
    "COMPANY_SEC": "ISSUER_SPECIFIC_CURRENT_FILING_AND_REVISION_NOT_RETAINED",
    "CRYPTO": "CURRENT_MARKET_ONCHAIN_DATA_AND_PROPOSAL_FINALIZATION_NOT_VERIFIED",
}


def research_library(research, *, cutoff_utc: str, briefs: Sequence[Mapping] = ()):
    items = []
    for row in research.records.values():
        if _time(row["revision_at_utc"]) > _time(cutoff_utc):
            continue
        meta = row.get("research_metadata") or {}
        if meta.get("family") not in FAMILIES:
            continue
        published = row.get("source_timestamp_utc")
        items.append({"item_id": row["headline_id"], "family": meta["family"],
                      "assets": meta.get("assets", []), "horizons": meta.get("horizons", []),
                      "horizon_semantics": "EDITORIAL_QUESTIONS_NOT_MAIN_FORECASTS",
                      "proposition": row["headline_text"], "context_kind": meta.get("context_kind", "NOT_CLASSIFIED"),
                      "source_url": row["source_url"], "source_identity": row["source_identity"],
                      "source_capture_sha256": row["source_capture_sha256"],
                      "permission_sha256": row["source_permission_record_sha256"],
                      "text_sha256": row["text_sha256"], "originality": row["originality"],
                      "published_at_utc": published, "known_at_utc": row["known_at_utc"],
                      "source_modified_at_utc": meta.get("source_modified_at_utc"),
                      "revision_at_utc": row["revision_at_utc"], "revision_clock_basis": row["revision_clock_basis"],
                      "correction_of": row.get("correction_of"),
                      "current_market_state_verified": False,
                      "age_days_at_scan": int((_time(cutoff_utc) - _time(published)).total_seconds() // 86400) if published else None,
                      "next_editorial_question": meta.get("next_editorial_question"),
                      "rights_state": row["rights_state"], "stage": "RESEARCH_READY"})
    superseded_ids = {i["correction_of"] for i in items if i.get("correction_of")}
    for item in items:
        if item["item_id"] in superseded_ids:
            item["stage"] = "RESEARCH_SUPERSEDED"
    by_id = {item["item_id"]: item for item in items if item["stage"] == "RESEARCH_READY"}
    accepted_briefs, gaps = [], list(research.gaps)
    for brief in briefs:
        refs = brief.get("source_item_ids") or []
        if (_private(brief) or not refs or any(ref not in by_id for ref in refs)
                or not all(brief.get(k) for k in ("brief_id", "title", "audience_value", "mechanism",
                                                "competing_explanation", "scenarios", "falsifiers", "next_question"))):
            gaps.append({"state": "EDITORIAL_BRIEF_SOURCE_OR_SUBSTANCE_GAP", "brief_id": brief.get("brief_id")})
            continue
        accepted_briefs.append({**brief, "stage": "EDITOR_AUTHORED_RESEARCH_BRIEF",
                                "fresh_provider_draft": False, "qualified": False, "published": False,
                                "facts": [{"item_id": ref, "text": by_id[ref]["proposition"],
                                           "text_sha256": by_id[ref]["text_sha256"],
                                           "source_url": by_id[ref]["source_url"]} for ref in refs],
                                "inference_authority": "CONTENTOPS_QUALITATIVE_INFERENCE_NOT_CORE_OUTPUT",
                                "brief_sha256": sha256_of(brief)})
    operation = Path(__file__).resolve().parents[1] / "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal24/manual_binding.json"
    next_operation = "python scripts/run_native_desktop_editorial.py advance --binding '" + str(operation) + "'"
    return {"schema_version": "contentops.foundation_library.v1", "observed_at_utc": cutoff_utc,
            "research_revision": research.revision, "items": items, "briefs": accepted_briefs,
            "gaps": gaps, "families": [{"family": family,
                "useful_items": sum(item["family"] == family for item in by_id.values()),
                "briefs": sum(family in b.get("families", []) for b in accepted_briefs),
                "missing_inputs": sorted({g for b in accepted_briefs if family in b.get("families", []) for g in b.get("missing_inputs", [])})
                    or [SOURCE_GAPS[family]]} for family in FAMILIES],
            "counts": {"independent_items": len(by_id), "useful_families": len({i["family"] for i in by_id.values()}),
                       "independent_documents": len({i["source_capture_sha256"] for i in by_id.values()}),
                       "briefs": len(accepted_briefs), "fresh_provider_drafts": 0, "qualified": 0, "published": 0},
            "next_operation": next_operation,
            "model_execution_state": "LLM_OPERATOR_PAUSED_RESEARCH_CONTINUES", "public_write_performed": False}


def persist_library(tracker, research, *, cutoff_utc, briefs=()):
    from live_contentops.capital_chronicle_report_feed_v1 import _persist
    snapshot = research_library(research, cutoff_utc=cutoff_utc, briefs=briefs)
    # Identical research/brief revision is stored once. Scan clocks remain in feed telemetry.
    identity = sha256_of([snapshot["research_revision"],
        [{k: v for k, v in i.items() if k != "age_days_at_scan"} for i in snapshot["items"]],
        snapshot["briefs"], snapshot["gaps"], snapshot["next_operation"]])
    key = "cc-library-" + identity
    if not tracker.store.get_outbox_message(key):
        prior = [json.loads(r["payload"]).get("library_sequence", 0) for r in tracker.store.list_outbox_messages() if r["destination"] == LIBRARY]
        _persist(tracker.store, key, {**snapshot, "library_sequence": max(prior, default=0) + 1}, LIBRARY)
    reconcile_affected_work(tracker)
    return snapshot


def persist_research_package(tracker, package, *, research_revision):
    from live_contentops.capital_chronicle_report_feed_v1 import _persist
    if (package.get("stage") != "EDITOR_AUTHORED_RESEARCH_PACKAGE" or package.get("qualified") is not False
            or package.get("fresh_provider_draft") is not False or package.get("published") is not False):
        raise ValueError("RESEARCH_PACKAGE_STATE_INVALID")
    payload = {**package, "research_revision": research_revision}
    if sha256_of(payload.get("article")) != payload.get("article_identity"):
        raise ValueError("RESEARCH_ARTICLE_IDENTITY_MISMATCH")
    for media in payload.get("media_assets", []):
        encoded = media.get("preview_data_url")
        if encoded and (not encoded.startswith("data:image/png;base64,") or len(encoded) > 2_000_030
                or hashlib.sha256(base64.b64decode(encoded.split(",", 1)[1], validate=True)).hexdigest() != media.get("sha256")):
            raise ValueError("RESEARCH_MEDIA_BYTES_HASH_MISMATCH")
    key = "cc-library-package-" + sha256_of({k: v for k, v in payload.items()
        if k != "research_revision" or not payload.get("source_binding_sha256")})
    if not tracker.store.get_outbox_message(key):
        prior = [json.loads(r["payload"]).get("package_sequence", 0) for r in tracker.store.list_outbox_messages() if r["destination"] == PACKAGE]
        _persist(tracker.store, key, {**payload, "package_sequence": max(prior, default=0) + 1}, PACKAGE)
    reconcile_affected_work(tracker)


def reconcile_affected_work(tracker):
    """Register only changed/revision-requested dependencies in the existing internal outbox.

    Requests are consumed as context by the existing four-window owner. Never dispatch
    an LLM, schedule another window, or mark an old approval valid during a read.
    """
    from live_contentops.capital_chronicle_report_feed_v1 import _persist
    from live_contentops.contentops_editorial_desk_v1 import read_reviews
    projection = library_projection(tracker.store.list_outbox_messages(), read_reviews(tracker.store))
    if not projection:
        return
    for p in projection["packages"]:
        if p["source_revision_current"] and p["review"]["state"] not in {"REVISE", "STALE"}:
            continue
        brief = next((b for b in projection["briefs"] if b["brief_id"] == p["brief_id"]), {})
        request = {"brief_id": p["brief_id"], "previous_package_revision": p["package_revision"],
                   "target_brief_sha256": brief.get("brief_sha256"),
                   "target_source_binding_sha256": source_binding([i for i in projection["items"] if i["item_id"] in brief.get("source_item_ids", [])]),
                   "reason": "DEPENDENT_INPUT_CHANGED" if not p["source_revision_current"] else "EDITOR_REQUESTED_REVISION",
                   "action": "RENDER_AFFECTED_RESEARCH" if not p["source_revision_current"] or p["review"]["state"] == "REVISE" else "REVIEW_REVISED_PACKAGE",
                   "owner": "EXISTING_RESEARCH_RENDERER_THEN_NATIVE_CODEX_DESKTOP",
                   "routine_window_count": 4, "provider_call_allowed_now": False, "public_write_performed": False}
        _persist(tracker.store, "cc-research-revision-" + sha256_of(request), request, "internal:cc-foundation-revision-request")


def source_binding(items):
    """Only dependent source/claim/rights revisions invalidate a package, not a global scan."""
    keys = ("item_id", "text_sha256", "source_capture_sha256", "permission_sha256", "context_kind",
            "published_at_utc", "known_at_utc", "revision_at_utc", "correction_of", "stage")
    return sha256_of([{k: i.get(k) for k in keys} for i in sorted(items, key=lambda i: i["item_id"])])


def _asset_family(asset):
    if asset.startswith(("XAU", "XAG", "XPT", "XPD")):
        return "METALS"
    if asset.startswith(("BTC", "ETH", "SOL", "XRP", "LTC", "BCH")):
        return "CRYPTO"
    if asset in {"USOIL", "UKOIL", "XNGUSD"}:
        return "ENERGY"
    if asset in {"US500", "USTEC", "US30", "DE30", "JP225", "UK100", "HK50"}:
        return "INDEX_OPTIONS"
    if re.fullmatch(r"(?:USD|EUR|GBP|JPY|AUD|NZD|CAD|CHF|CNH){2}", asset):
        return "FX_RATES"
    return "UNCLASSIFIED_PUBLIC_ASSET"


def library_projection(rows, review_records=()):
    snapshots = [json.loads(row["payload"]) for row in rows if row["destination"] == LIBRARY]
    snapshot = dict(max(enumerate(snapshots), key=lambda pair: (pair[1].get("library_sequence", 0), pair[0]))[1]) if snapshots else None
    if snapshot is None:
        return None
    packages = {}
    for row in rows:
        if row["destination"] == PACKAGE:
            value = json.loads(row["payload"])
            if packages.get(value["brief_id"], {}).get("package_sequence", -1) > value.get("package_sequence", 0):
                continue
            packages[value["brief_id"]] = {**value, "source_revision_current": value.get("research_revision") == snapshot["research_revision"]}
    brief_hashes = {b["brief_id"]: b["brief_sha256"] for b in snapshot["briefs"]}
    brief_map = {b["brief_id"]: b for b in snapshot["briefs"]}
    for package in packages.values():
        brief = brief_map.get(package["brief_id"], {})
        dependencies = [i for i in snapshot["items"] if i["item_id"] in brief.get("source_item_ids", [])]
        if package.get("source_binding_sha256"):
            package["source_revision_current"] = (len(dependencies) == len(brief.get("source_item_ids", []))
                and package["source_binding_sha256"] == source_binding(dependencies))
        package["source_revision_current"] = (package["source_revision_current"]
            and package.get("brief_sha256") == brief_hashes.get(package["brief_id"]))
        package["package_revision"] = sha256_of([package["article_identity"], package.get("brief_sha256"),
            package.get("source_binding_sha256", package.get("research_revision")), package.get("previews"),
            [{k: v for k, v in m.items() if k not in {"path", "preview_data_url"}} for m in package.get("media_assets", [])]])
    reports, counts = {}, {}
    withdrawn = {json.loads(r["payload"])["source_report_sha256"] for r in rows
                 if r["destination"] == "internal:cc-report-withdrawal"}
    for row in rows:
        if row["destination"] != "internal:cc-report-receipt":
            continue
        report = json.loads(row["payload"])
        state = report.get("status", "UNKNOWN")
        counts[state] = counts.get(state, 0) + 1
        if state not in {"ADMITTED", "LINEAGE_ONLY_NOOP", "NO_MATERIAL_CHANGE_NOOP", "INVALIDATION_WITHDRAWAL_NOOP"}:
            continue
        prior = reports.get(report["report_id"])
        if prior and prior["report_version"] >= report["report_version"]:
            continue
        reports[report["report_id"]] = {
            "report_id": report["report_id"], "report_version": report["report_version"],
            "asset_ids": report.get("asset_ids", []), "families": sorted({_asset_family(a) for a in report.get("asset_ids", [])}),
            "family_basis": "EDITORIAL_SYMBOL_TAXONOMY_NOT_MAIN_ANALYTICAL_CLASSIFICATION",
            "status": state, "change_kind": report.get("change_kind"),
            "source_report_sha256": report.get("source_report_sha256"),
            "parent_report_sha256": report.get("parent_report_sha256"),
            "known_at_cutoff_utc": report.get("known_at_cutoff_utc"),
            "originality": "MAIN_ORIGIN_RECIRCULATION",
            "horizons": [{k: h.get(k) for k in ("horizon", "trading_sessions", "outlook")}
                         for h in report.get("horizon_blocks", [])],
            "withdrawn": report.get("source_report_sha256") in withdrawn or bool(report.get("withdrawal_only")),
            "current_market_state_verified": False,
            "context_kind": "DATED_MAIN_REPORT_NOT_CURRENT_MARKET_STATE",
            "changed_claim_ids": report.get("changed_claim_ids", []),
            "limitations": report.get("limitations", []),
            "public_claims": [{**{k: c.get(k) for k in ("claim_id", "producer_layer", "text", "exact_or_proxy", "basis_risk")},
                               "freshness_state": ", ".join(sorted({e.get("freshness_state") or "NOT_PROVIDED" for e in c.get("evidence", [])})) or "NOT_PROVIDED",
                               "evidence": [{k: e.get(k) for k in ("evidence_id", "source_url", "observation_time_utc", "known_at_utc",
                                            "retrieval_time_utc", "freshness_state", "pit_state", "exact_or_proxy", "rights_state")}
                                            for e in c.get("evidence", [])]}
                              for c in report.get("claims", [])],
            "next_editorial_question": "Which exact public claims changed, and what independent evidence tests their mechanism?"}
    for p in packages.values():
        expected_reports = p.get("main_report_bindings", [])
        p["main_report_bindings_current"] = all(
            reports.get(b["report_id"], {}).get("source_report_sha256") == b["source_report_sha256"]
            and not reports.get(b["report_id"], {}).get("withdrawn", True) for b in expected_reports)
        p["source_revision_current"] = p["source_revision_current"] and p["main_report_bindings_current"]
        p["package_revision"] = sha256_of([p["package_revision"], expected_reports])
    current_packages = [p for p in packages.values() if p["source_revision_current"]]
    result = {**snapshot, "main_reports": list(reports.values()), "report_admissions_and_noops": counts,
            "input_composition": {"independent_research_items": snapshot["counts"]["independent_items"],
                "evidence_complete_briefs": len(snapshot["briefs"]),
                "main_editorial_reports": sum(r["status"] == "ADMITTED" and not r["withdrawn"] for r in reports.values()),
                "main_unchanged_reports": sum(r["status"] == "NO_MATERIAL_CHANGE_NOOP" for r in reports.values()),
                "main_history_only_reports": sum(r["status"] == "LINEAGE_ONLY_NOOP" for r in reports.values()),
                "owner": "NATIVE_CODEX_DESKTOP", "routine_window_count": 4,
                "model_execution_state": "LLM_OPERATOR_PAUSED", "current_market_state_verified": False},
            "packages": list(packages.values()), "counts": {**snapshot["counts"],
                "editor_authored_packages": len(current_packages),
                "native_previews": sum(len(p.get("previews", {})) for p in current_packages),
                "media": sum(len(p.get("media_assets", [])) for p in current_packages)}}
    from live_contentops.contentops_editorial_desk_v1 import desk_projection, story_projection, publication_story_context
    result = desk_projection(result, review_records)
    result["stories"] = story_projection(result, rows)
    for row in reversed(rows):
        if row["destination"] == "internal:cc-report-editorial-stage":
            frozen_args = json.loads(row["payload"]).get("args")
            if frozen_args:
                result["stories"] = publication_story_context(result["stories"], frozen_args.get("published_memory", []), cutoff_utc=frozen_args["cutoff_utc"])
                result["publication_memory"] = {"source": "EXISTING_FROZEN_SIMPLE_POOL_CANONICAL_MEMORY",
                    "observed_at_utc": frozen_args["cutoff_utc"], "article_count": max((s["canonical_memory_article_count"] for s in result["stories"]), default=0)}
                break
    return result
