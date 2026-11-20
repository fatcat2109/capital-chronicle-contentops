"""Daily Antigravity job counts from ContentOps' retained call receipts (CC-690)."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .public_decision_checks_v1 import clock, object_json


JOBS = {
    "plan_layer_lines": "Plan posts due for source-bound analysis",
    "plan_analysis_page": "Distinct plans first announced",
    "daily_wrap_sections": "Pre-US wraps due",
    "weekend_wrap_sections": "Sunday wraps due",
    "article_claim_check": "Canonical article packages due",
    "x_reply_ranking": "Retained X reply ranking requests",
}
PASS_RATE = 90.0
LEGACY_CLAIM = "agy_light_assist_v1.json"
WRAP_JOB_NAMES = {
    "wrap_sections": "daily_wrap_sections",
    "pre_us_wrap_sections": "daily_wrap_sections",
    "weekly_wrap_sections": "weekend_wrap_sections",
    "claim_check": "article_claim_check",
    "reply_ranking": "x_reply_ranking",
}


def _contained(path, runtime):
    return path.is_file() and path.resolve().is_relative_to(runtime)


def _receipt_paths(root, runtime, start, end, output_folders):
    files = set()
    reply_requests = 0
    day = start.date()
    while day <= end.date():
        for folder in (root / "x_reply_pack" / "bot").glob(day.strftime("%Y%m%d") + "T*"):
            try:
                at = datetime.strptime(folder.name[:15], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            receipt = folder / "editorial" / "rank" / "light" / "light-call.json"
            if start < at <= end and (receipt.is_file() or any(folder.glob("reply-pack-request-*.json"))):
                reply_requests += 1
            if _contained(receipt, runtime):
                files.add(receipt)
        day += timedelta(days=1)
    for parent in ("plan_analysis", "plan-status-posts", "plan_status_posts", "owner-manual", "weekly"):
        folder = root / parent
        for pattern in ("*/layer-lines-*/light-call.json", "*/full-analysis-*/*/light-call.json",
                        "*/page-writer-cc688/*/*/light-call.json",
                        "*/daily-note-first-draft/*/result.json", "*/" + LEGACY_CLAIM):
            files.update(path for path in folder.glob(pattern) if _contained(path, runtime))
    for folder in output_folders:
        if not folder.is_relative_to(runtime):
            continue
        for pattern in (LEGACY_CLAIM, "daily-note-first-draft/*/result.json",
                        "*/*/light-call.json", "*/light-call.json"):
            files.update(path for path in folder.glob(pattern) if _contained(path, runtime))
    return sorted(files), reply_requests


def _legacy_record(path, row):
    if path.name == LEGACY_CLAIM and row.get("schema_version") == "contentops.agy_light_assist.v1":
        job = "article_claim_check"
        result = "PASS" if row.get("status") == "AGY_AVAILABLE" and not row.get("flags") else "FAIL"
        attempted = "returncode" in row or "AGY_TIMEOUT" in str(row.get("cause", ""))
    elif row.get("schema_version") == "contentops.daily_note_first_draft.v1":
        job = "daily_wrap_sections"
        result = "PASS" if row.get("status") == "DRAFT_CHECKS_PASS" else "FAIL"
        attempted = row.get("provider_call_attempted") is True
    else:
        return {}
    if not attempted:
        return {}
    cause = str(row.get("cause") or "")
    status = "TIMEOUT" if "TIMEOUT" in cause.upper() else "RETURNED" if row.get("output") else "FAILED"
    return {**row, "job": job, "result": result, "answered_by": "antigravity" if status == "RETURNED" else None,
            "attempts": [{"caller": "antigravity", "status": status, "cause": cause}],
            "fallback": "codex" if job == "daily_wrap_sections" and row.get("status") == "AGY_UNAVAILABLE" else None}


def _job_record(path, row, runtime, end):
    if path.name != "light-call.json":
        return _legacy_record(path, row)
    if row.get("job") in JOBS or row.get("job") in WRAP_JOB_NAMES:
        return {**row, "job": WRAP_JOB_NAMES.get(row["job"], row["job"])}
    if path.parent.parent.name == "rank" and "x_reply_pack" in path.relative_to(runtime).parts:
        call = path.parent.parent / "call.json"
        validated = object_json(call) if _contained(call, runtime) else {}
        checked_at = clock(validated.get("ended_at_utc"))
        verdict = None
        if checked_at and checked_at <= end:
            response = call.with_name("response.json")
            ranking = object_json(response).get("ranking") if _contained(response, runtime) else None
            if (validated.get("status") == "RETURNED" and isinstance(ranking, list)
                    and all(isinstance(item, dict) and isinstance(item.get("post_id"), str)
                            and type(item.get("quality_score")) is int and 0 <= item["quality_score"] <= 100
                            for item in ranking)):
                verdict = "PASS"
            else:
                verdict = "FAIL"
        return {**row, "job": "x_reply_ranking", "result": verdict}
    return {}


def _occupied_hours(intervals, start, end):
    occupied = timedelta()
    last = start
    for opened, closed in sorted(intervals):
        if closed > last:
            occupied += max(timedelta(), min(closed, end) - max(last, opened, start))
            last = max(closed, last)
    return occupied.total_seconds() / 3600


def daily_metrics(runtime, window, due, output_folders=()):
    runtime = Path(runtime).resolve()
    start, end = (clock(window[key]) for key in ("since_utc", "until_utc"))
    paths, reply_requests = _receipt_paths(runtime / "daily_app_outputs", runtime, start, end, output_folders)
    counts = defaultdict(Counter)
    intervals = defaultdict(list)
    seen = set()
    for path in paths:
        record = _job_record(path, object_json(path), runtime, end)
        job = record.get("job")
        if job not in JOBS:
            continue
        opened = clock(record.get("started_at_utc") or record.get("started_utc"))
        closed = clock(record.get("ended_at_utc") or record.get("ended_utc"))
        if not opened or opened > end or (closed and closed <= start):
            continue
        if path.name == LEGACY_CLAIM and record.get("prompt_sha256"):
            identity = job, opened, record["prompt_sha256"]
            if identity in seen:
                continue
            seen.add(identity)
        matched = [a for a in record.get("attempts", []) if a.get("caller") == "antigravity"]
        if not matched:
            if (start < opened <= end and closed and closed <= end and job == "plan_analysis_page"
                    and any(attempt.get("caller") == "codex" for attempt in record.get("attempts", []))):
                counts[job]["codex_takeovers"] += 1
                if record.get("fallback") == "frozen_plan":
                    counts[job]["code_fallbacks"] += 1
            continue
        if closed:
            intervals[job].append((opened, closed))
        if opened <= start:
            continue
        tally = counts[job]
        tally["calls"] += len(matched)
        result = record.get("result") if closed and closed <= end else None
        for attempt in matched:
            state = attempt.get("status") if closed and closed <= end else None
            cause = str(attempt.get("cause") or "").upper()
            if state and (state == "EMPTY" or "EMPTY" in cause):
                tally["empty_answers"] += 1
            if state == "TIMEOUT":
                tally["timeouts"] += 1
            if state == "RETURNED":
                if record.get("answered_by") == "antigravity" and result == "PASS":
                    tally["code_passes"] += 1
                elif result is None:
                    tally["unchecked_returns"] += 1
                else:
                    tally["code_rejects"] += 1
            if state is None:
                tally["calls_incomplete_at_cutoff"] += 1
        if result is not None:
            fallback = record.get("fallback")
            if record.get("answered_by") == "codex" or fallback == "codex":
                tally["codex_takeovers"] += 1
            elif fallback == "frozen_plan":
                tally["code_fallbacks"] += 1
        elif closed and closed <= end and record.get("answered_by") == "codex":
            tally["codex_takeovers"] += 1

    duration = (end - start).total_seconds() / 3600
    metrics = []
    for job, basis in JOBS.items():
        tally = counts[job]
        calls = tally["calls"]
        unobserved = tally["unchecked_returns"] + tally["calls_incomplete_at_cutoff"]
        rate = round(100 * tally["code_passes"] / calls, 2) if calls else None
        highest_rate = 100 * (tally["code_passes"] + unobserved) / calls if calls else None
        meets = True if rate is not None and rate >= PASS_RATE else False if highest_rate is not None and highest_rate < PASS_RATE else None
        metrics.append({"job": job, "due_basis": basis,
                        "posts_due": reply_requests if job == "x_reply_ranking" else due.get(job, 0),
                        **{key: tally[key] for key in ("calls", "code_passes", "code_rejects", "unchecked_returns",
                            "calls_incomplete_at_cutoff", "empty_answers", "timeouts", "code_fallbacks", "codex_takeovers")},
                        "code_pass_rate_pct": rate, "code_pass_rate_meets_90_pct": meets,
                        "hours_without_recorded_call": round(duration - _occupied_hours(intervals[job], start, end), 3),
                        "hours_idle_without_rate_limit": None,
                        "idle_evidence": "RUNNER_RATE_LIMIT_COVERAGE_UNAVAILABLE"})
    return {"code_pass_target_pct": PASS_RATE, "jobs": metrics}
