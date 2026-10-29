"""Dated V1 policy and bounded projections over existing native window records.

This module owns no timer, acquisition ledger, publication or model execution.
Issued bindings keep their frozen policy; the date gate never upgrades old work.
"""
from __future__ import annotations

import json
from pathlib import Path

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.newsroom_production_day_v1 import newsroom_production_date

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config/native_newsroom_volume_v1.json"
PHOTOLESS_INSTAGRAM_SKIP = "SKIPPED_PHOTOLESS_NEWS_POLICY"


def volume_policy(cutoff_utc, *, brief_only=False):
    config = json.loads(CONFIG_PATH.read_bytes())
    day = newsroom_production_date(cutoff_utc).isoformat()
    if day < config["effective_production_date"]:
        return None
    return {k: config[k] for k in ("policy_id", "effective_production_date", "source_request_limit",
            "non_chargeable_only", "source_resolvability_first", "photo_less_news_policy")} | {
        **config["brief_window" if brief_only else "full_window"], "brief_only": bool(brief_only)}


def bound_volume_policy(binding):
    """Only a new, explicitly bound policy changes an operation's limits."""
    policy = binding.get("volume_policy")
    if policy is None:
        return None
    if not isinstance(policy, dict):
        raise ValueError("NATIVE_VOLUME_POLICY_BINDING_INVALID")
    expected = volume_policy(binding["cutoff_utc"], brief_only=policy.get("brief_only", False))
    if expected != policy:
        raise ValueError("NATIVE_VOLUME_POLICY_BINDING_INVALID")
    return policy


def photo_less_brief(result):
    article = result.get("article") or result
    policy = article.get("volume_policy") or result.get("volume_policy")
    cutoff = article.get("volume_policy_cutoff_utc") or result.get("volume_policy_cutoff_utc")
    if not policy or not cutoff:
        return False
    bound_volume_policy({"volume_policy": policy, "cutoff_utc": cutoff})
    decision = article.get("visual_editorial_decision") or result.get("visual_editorial_decision") or {}
    mode = article.get("resolved_article_mode") or article.get("effective_article_mode")
    return (policy.get("photo_less_news_policy") is True and decision.get("story_kind") in {"NEWS", "POLICY"}
        and mode in {None, "BREAKING_BRIEF", "FOLLOW_UP_UPDATE"}
        and not any(a.get("modality") == "documentary_photo" for a in result.get("media_assets", [])))


def permitted_photo_less_skip(plan):
    if not plan.get("photo_less_news_policy"):
        return False
    if not bound_volume_policy({"volume_policy": plan.get("volume_policy"), "cutoff_utc": plan.get("volume_policy_cutoff_utc")}):
        return False
    skipped = plan.get("skipped_derivative_destinations") or []
    return (plan.get("resolved_article_mode") in {"BREAKING_BRIEF", "FOLLOW_UP_UPDATE"}
        and len(skipped) == 1 and skipped[0].get("destination") == "instagram_business"
        and skipped[0].get("status") == PHOTOLESS_INSTAGRAM_SKIP)


def native_selection(store, run_id):
    work = "cc-opportunity-" + sha256_of(run_id)
    values = []
    for kind in ("request", "response"):
        row = store.get_outbox_message("native-desktop-" + sha256_of([work, "select", kind]))
        values.append(json.loads(row["payload"]) if row else None)
    return tuple(values)


def window_progress(store, issued):
    """Carry actual global usage and admissions across the window's issued slots.

    Every revised slot reports a monotonically increasing window total. Earlier
    source counts are never summed twice on restart or reset after a refusal.
    """
    used, attempted, admitted, published = 0, set(), [], set()
    origin, origin_root = None, None
    for binding, _path in issued:
        run = binding["run_id"]
        request, response = native_selection(store, run)
        if origin is None and request and response:
            origin, origin_root = run, binding["output_dir"]
            admitted = [p["candidate_id"] for p in response["output"].get("ordered_candidate_plan", [])]
        root = Path(binding["output_dir"])
        evidence_path = root / "simple_gemini_evidence_v1.json"
        if evidence_path.is_file():
            evidence = json.loads(evidence_path.read_bytes())
            used = max(used, int(evidence.get("request_count", 0)))
            attempted.update(a["candidate_id"] for a in evidence.get("candidate_attempt_history", [])
                             if a.get("status") == "SOURCE_BLOCKED")
        final = store.get_outbox_message("cc-editorial-final-" + sha256_of(run))
        if final:
            value = json.loads(final["payload"])
            semantic = value.get("simple_result", value)
            used = max(used, int(semantic.get("source_request_count", 0)))
            attempted.update(a["candidate_id"] for a in semantic.get("candidate_attempt_history", [])
                             if a.get("status") == "SOURCE_BLOCKED")
            attempted.update(a["candidate_id"] for a in semantic.get("candidate_outcomes", [])
                             if a.get("candidate_id") and a.get("outcome") in {"HOLD", "SOURCE_BLOCKED", "REJECT"})
            selected = semantic.get("selected_candidate") or value.get("selected_candidate")
            if semantic.get("qualified_article_count") and selected:
                attempted.add(selected["candidate_id"])
        # Use the existing strict canonical contract, never a derivative count.
        from live_contentops.native_desktop_publication_v1 import publication_projection
        projection = publication_projection(store.list_outbox_messages(), store.list_platform_dispatches(),
            store.get_reconciliations_for_work_item(run), run_id=run)
        from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
        for canonical in projection.get("destinations", []):
            if (canonical.get("destination") == "substack"
                    and canonical.get("reconciliation_status") == "RECONCILED_CONFIRMED"
                    and DurablePublicationCoordinator._confirmed_public_object(canonical, destination="substack")):
                published.add(str(canonical["public_object_id"]))
    if issued and issued[0][0].get("volume_policy"):
        if used > issued[0][0]["volume_policy"]["source_request_limit"]:
            raise ValueError("EXISTING_WINDOW_SOURCE_BUDGET_EXCEEDED")
    return {"source_request_count": used, "admitted_candidate_ids": admitted,
        "attempted_candidate_ids": sorted(attempted), "published_article_count": len(published),
        "selection_origin_run_id": origin, "selection_origin_output_dir": origin_root}


def configure_volume_turn(turn, binding):
    policy = bound_volume_policy(binding)
    turn.volume_policy = policy
    turn.source_request_count_at_start = int(binding.get("source_request_count_at_start", 0))
    turn.inherited_selection = None
    if not policy:
        if turn.source_request_count_at_start:
            raise ValueError("SOURCE_BUDGET_CARRY_REQUIRES_BOUND_VOLUME_POLICY")
        return
    if not 0 <= turn.source_request_count_at_start <= policy["source_request_limit"]:
        raise ValueError("WINDOW_SOURCE_BUDGET_CARRY_INVALID")
    origin = binding.get("selection_origin_run_id")
    if origin and origin != turn.run_id:
        request, response = native_selection(turn.store, origin)
        if not request or not response or response["request_sha256"] != request["request_sha256"]:
            raise ValueError("EXACT_PRIOR_NATIVE_SELECTION_REQUIRED")
        if request["governed_input"]["cutoff_utc"] != binding["cutoff_utc"]:
            raise ValueError("CROSS_WINDOW_SELECTION_REUSE_FORBIDDEN")
        turn.inherited_selection = {"origin_run_id": origin, "request": request, "response": response,
            "excluded_candidate_ids": sorted(set(binding.get("attempted_candidate_ids", [])))}


def persist_native_day_measurement(store, binding):
    """Refresh the existing production-day projection from actual saved outcomes.

    No platform collection is performed here. A missing reader metric is null,
    and the measured latency ends at canonical readback, not an invented publish time.
    """
    from collections import Counter, defaultdict
    from datetime import datetime, timezone
    from live_contentops.newsroom_production_day_v1 import newsroom_production_day_id
    from live_contentops.native_desktop_publication_v1 import publication_projection
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes
    from live_contentops.native_brief_windows_v1 import quota_stop_observations
    if not bound_volume_policy(binding) or not binding.get("window_id"):
        return None
    day = newsroom_production_day_id(binding["cutoff_utc"])
    rows, dispatches = store.list_outbox_messages(), store.list_platform_dispatches()
    bindings = [json.loads(row["payload"]) for row in rows if row["message_id"].startswith("native-operation-binding-")]
    bindings = [b for b in bindings if b.get("volume_policy") and b.get("window_id")
                and newsroom_production_day_id(b["cutoff_utc"]) == day]
    admissions, qualified, first_causes, confirmed = set(), set(), {}, defaultdict(set)
    windows, latencies, readers, interventions = {}, [], [], []
    observations = store.list_performance_observations()
    preparations = [json.loads(row["payload"]) for row in rows if row["destination"] == "internal:native-story-preparation"]
    for current in bindings:
        run, window = current["run_id"], current["window_id"]
        request, response = native_selection(store, run)
        if response:
            admissions.update((window, p["candidate_id"]) for p in response["output"].get("ordered_candidate_plan", []))
        evidence_path = Path(current["output_dir"]) / "simple_gemini_evidence_v1.json"
        if evidence_path.is_file():
            evidence = json.loads(evidence_path.read_bytes())
            qualified.update((window, a["candidate_id"]) for a in evidence.get("candidate_attempt_history", [])
                             if a.get("status") == "SOURCE_QUALIFIED")
        final = store.get_outbox_message("cc-editorial-final-" + sha256_of(run))
        if final:
            value = json.loads(final["payload"])
            semantic = value.get("simple_result", value)
            for outcome in semantic.get("candidate_outcomes", []):
                first_causes.setdefault((window, outcome.get("candidate_id")), outcome["primary_cause"])
            interventions.extend(semantic.get("process_findings", []))
        checkpoint = store.get_outbox_message("native-window-" + sha256_of(window))
        checkpoint = json.loads(checkpoint["payload"]) if checkpoint else {}
        entry = checkpoint.get("actual_entry_utc")
        progress = window_progress(store, [(b, None) for b in bindings if b["window_id"] == window])
        windows[window] = {"source_request_count": progress["source_request_count"],
            "admitted_count": len(progress["admitted_candidate_ids"]),
            "distinct_canonical_published": progress["published_article_count"],
            "brief_only": current["volume_policy"]["brief_only"]}
        projection = publication_projection(rows, dispatches, store.get_reconciliations_for_work_item(run), run_id=run)
        for destination in projection.get("destinations", []):
            channel = destination["destination"]
            if (destination.get("reconciliation_status") != "RECONCILED_CONFIRMED"
                    or not DurablePublicationCoordinator._confirmed_public_object(destination, destination=channel)):
                continue
            object_id = str(destination["public_object_id"])
            confirmed[channel].add(object_id)
            metrics = [o for o in observations if o.get("dispatch_id") == destination["dispatch_id"]
                       and o.get("public_object_id") == object_id]
            exposed = [{"observation_id": o["observation_id"], "collection_status": o.get("collection_status"),
                "availability": json.loads(o.get("metric_availability_json") or "{}"),
                "metrics": json.loads(o.get("metrics_native_json") or "{}") or None} for o in metrics]
            available = any("AVAILABLE" in o["availability"].values() for o in exposed)
            readers.append({"channel": channel, "public_object_id": object_id,
                "availability": "OBSERVED" if available else "UNAVAILABLE", "observations": exposed or None})
            if channel == "substack":
                readbacks = store.list_readbacks_for_dispatch(destination["dispatch_id"])
                times = [r["read_at"] for r in readbacks
                    if json.loads(r["readback_data"]).get("verified") is True]
                seconds = None
                if entry and times:
                    seconds = (datetime.fromisoformat(min(times).replace("Z", "+00:00"))
                        - datetime.fromisoformat(entry.replace("Z", "+00:00"))).total_seconds()
                latencies.append({"run_id": run, "public_object_id": object_id,
                    "window_entry_to_canonical_readback_seconds": seconds})
    quota_stops = quota_stop_observations(store, production_date=newsroom_production_date(binding["cutoff_utc"]).isoformat())
    quota_stops.extend(i for i in interventions if i.get("cause") == "CODEX_QUOTA_STOP" and i not in quota_stops)
    measurement = {"observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "policy_id": binding["volume_policy"]["policy_id"], "admitted_items": len(admissions),
        "source_qualified_items": len(qualified), "distinct_canonical_items_published": len(confirmed["substack"]),
        "confirmed_copies_by_channel": {k: len(v) for k, v in confirmed.items()},
        "first_blocking_causes": dict(Counter(first_causes.values())), "windows": windows,
        "time_to_canonical": latencies, "interventions": interventions,
        "quota_stops": quota_stops,
        "reader_counts": readers or None,
        "reader_counts_availability": "OBSERVED" if any(r["availability"] == "OBSERVED" for r in readers) else "UNAVAILABLE",
        "pre_event_preparations_available": [{"event_id": p["event_id"], "known_at_utc": p["known_at_utc"],
            "planned_release_utc": p.get("planned_release_utc"), "source_admission_state": p["source_admission_state"]} for p in preparations],
        "distinct_daily_target": 8, "target_by_revised_production_day": 3,
        "tests_or_derivatives_are_original_publications": False}
    # Same existing day artifact. Preserve the existing snapshot's other fields.
    root = Path(binding["output_dir"]).parent.parent
    if root.name != day:
        raise ValueError("EXACT_NATIVE_PRODUCTION_DAY_OUTPUT_ROOT_REQUIRED")
    path = root / "newsroom_production_day_v1.json"
    payload = json.loads(path.read_bytes()) if path.is_file() else {
        "schema_version": "contentops.newsroom_production_day.v1", "newsroom_production_day_id": day}
    payload.update(native_volume_measurement=measurement)
    payload.pop("record_sha256", None)
    payload["record_sha256"] = sha256_of(payload)
    path.write_bytes(canonical_bytes(payload))
    return str(path)
