"""ContentOps assignment and five-window scheduler.

This module processes newsroom candidate pools, enforces hard gates, applies
multi-dimensional scoring, concentration penalties, update-chain rules, and
gated preemption to make deterministic daily scheduling decisions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "capital_chronicle.newsroom_schedule_decision.v1"

TAG_WEIGHTS = {
    "central_bank": 20,
    "inflation": 18,
    "labor": 16,
    "energy": 16,
    "geopolitics": 16,
    "volatility": 12,
    "risk_off": 12,
    "rates": 10,
    "earnings": 8,
}

OFFICIAL_SOURCE_TERMS = {
    "fed", "fomc", "treasury", "eia", "cpi", "jobs", "payroll", "opec", "inventory"
}


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _logical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def calculate_candidate_scores(
    candidate: Mapping[str, Any],
    cutoff_dt: datetime,
    weights: Mapping[str, float],
) -> dict[str, Any]:
    """Calculate normalized scores for a candidate at a given point in time."""
    title_summary = f"{candidate.get('title', '')} {candidate.get('summary', '')}".lower()
    tags = candidate.get("tags") or []
    
    # 1. Base Impact Score
    tag_impact = sum(TAG_WEIGHTS.get(str(t).lower(), 0) for t in tags)
    official_bonus = 15 if any(term in title_summary for term in OFFICIAL_SOURCE_TERMS) else 0
    raw_impact = 40 + tag_impact + official_bonus
    impact_score = min(100.0, max(0.0, float(raw_impact)))
    
    # 2. Base Urgency Score
    raw_urgency = 35 + (tag_impact * 1.2) + official_bonus
    urgency_score = min(100.0, max(0.0, float(raw_urgency)))
    
    # 3. Freshness Score
    known_at = _parse_utc(candidate["known_at_utc"])
    age_seconds = max(0.0, (cutoff_dt - known_at).total_seconds())
    max_age_hours = float((candidate.get("freshness") or {}).get("max_age_hours") or 36.0)
    max_age_seconds = max_age_hours * 3600.0
    
    # Freshness decays linearly
    freshness_score = min(100.0, max(0.0, (1.0 - (age_seconds / max_age_seconds)) * 100.0))
    
    # 4. Weighted Total
    total_score = (
        impact_score * weights.get("impact", 0.3) +
        urgency_score * weights.get("urgency", 0.4) +
        freshness_score * weights.get("freshness", 0.3)
    )
    
    return {
        "impact": round(impact_score, 2),
        "urgency": round(urgency_score, 2),
        "freshness": round(freshness_score, 2),
        "total": round(total_score, 2),
    }


def evaluate_window_decision(
    *,
    window: Mapping[str, Any],
    schedule_date: str,
    pool: Mapping[str, Any],
    previously_published: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Execute the deterministic scheduling logic for a single decision window."""
    window_id = window["window_id"]
    cutoff_time_str = window["target_cutoff_utc"]
    
    # Parse target cutoff datetime
    target_time = time.fromisoformat(cutoff_time_str)
    base_date = datetime.strptime(schedule_date, "%Y-%m-%d").date()
    cutoff_dt = datetime.combine(base_date, target_time, tzinfo=timezone.utc)
    
    # Invariant checks on the pool
    if pool.get("schema_version") != "capital_chronicle.newsroom_candidate_pool.v1":
        raise ValueError("unsupported_candidate_pool_schema")
        
    # Filter eligible candidates known before/at the cutoff
    eligible_pool = pool.get("eligible_candidates") or []
    candidates = []
    
    for c in eligible_pool:
        known_dt = _parse_utc(c["known_at_utc"])
        if known_dt <= cutoff_dt:
            candidates.append(c)
            
    # Track concentration metrics for previously published stories
    published_topics = {p["story_family"] for p in previously_published if p.get("story_family")}
    published_modes = {p["article_mode"] for p in previously_published if p.get("article_mode")}
    published_authorities = {
        auth
        for p in previously_published
        for auth in (p.get("authority") or {}).get("source_authorities") or []
    }
    
    scored_candidates = []
    backlog = []
    
    for c in candidates:
        scores = calculate_candidate_scores(c, cutoff_dt, window["score_weights"])
        
        # Apply concentration penalties
        penalties = []
        penalty_total = 0.0
        
        if c.get("story_family") in published_topics:
            penalties.append("topic_concentration")
            penalty_total += 15.0
        if c.get("article_mode") in published_modes:
            penalties.append("mode_concentration")
            penalty_total += 10.0
        
        c_authorities = set((c.get("authority") or {}).get("source_authorities") or [])
        if c_authorities.intersection(published_authorities):
            penalties.append("source_concentration")
            penalty_total += 12.0
            
        final_score = round(max(0.0, scores["total"] - penalty_total), 2)
        
        # Block update chain candidates if not material_update
        blocked_by_relationship = False
        relation = c.get("relationship")
        if relation in ("duplicate", "incremental_update"):
            blocked_by_relationship = True
            
        scored_info = {
            "candidate": c,
            "raw_scores": scores,
            "penalties": penalties,
            "penalty_total": penalty_total,
            "final_score": final_score,
            "relationship_blocked": blocked_by_relationship,
        }
        
        if blocked_by_relationship:
            backlog.append(scored_info)
        else:
            scored_candidates.append(scored_info)
            
    # Sort candidates by final score descending
    scored_candidates.sort(key=lambda x: x["final_score"], reverse=True)
    
    # Check preemption (high urgency items)
    preempted = None
    if window.get("preemption_allowed") and len(previously_published) >= window.get("daily_portfolio_limit", 99):
        # We are at or over limit, check if any eligible candidate qualifies for preemption
        high_urgency_candidates = [
            x for x in scored_candidates
            if x["raw_scores"]["urgency"] >= 80.0
            and x["final_score"] >= window["minimum_urgency_threshold"]
        ]
        if high_urgency_candidates:
            preempted = high_urgency_candidates[0]
            
    # Select candidate
    selected = None
    decision = "NO_PUBLICATION_THRESHOLD_NOT_MET"
    rationale = "No eligible candidates met the window urgency/impact thresholds."
    
    if preempted:
        selected = preempted
        decision = "PUBLISH"
        rationale = f"Preempted daily portfolio limit with highly urgent candidate: {selected['candidate']['title']}"
    elif len(previously_published) < window.get("daily_portfolio_limit", 99) and scored_candidates:
        top = scored_candidates[0]
        min_urgency = window["minimum_urgency_threshold"]
        min_impact = window["minimum_impact_threshold"]
        
        if (top["raw_scores"]["urgency"] >= min_urgency and 
            top["raw_scores"]["impact"] >= min_impact and 
            top["final_score"] >= min_urgency):
            selected = top
            decision = "PUBLISH"
            rationale = f"Top-ranked candidate meets thresholds: {selected['candidate']['title']}"
        elif (top["raw_scores"]["urgency"] >= (min_urgency - 10.0) or 
              top["raw_scores"]["impact"] >= (min_impact - 10.0) or 
              top["final_score"] >= (min_urgency - 10.0)):
            decision = "HOLD_FOR_MORE_EVIDENCE"
            rationale = f"Top candidate {top['candidate']['title']} is close to thresholds; holding."
            
    # Build result
    considered = selected or (scored_candidates[0] if scored_candidates else None)
    decision_packet = {
        "window_id": window_id,
        "name": window["name"],
        "cutoff_time_utc": cutoff_dt.isoformat().replace("+00:00", "Z"),
        "decision": decision,
        "rationale": rationale,
        "selected_candidate": selected["candidate"] if selected else None,
        "score_details": {
            "raw_scores": considered["raw_scores"] if considered else None,
            "penalties": considered["penalties"] if considered else [],
            "penalty_total": considered["penalty_total"] if considered else 0.0,
            "final_score": considered["final_score"] if considered else 0.0,
        },
        "backlog_candidates": [
            {
                "candidate_id": item["candidate"]["candidate_id"],
                "title": item["candidate"]["title"],
                "final_score": item["final_score"],
                "relationship": item["candidate"]["relationship"],
            }
            for item in sorted(scored_candidates[1:] if selected and not preempted else scored_candidates, key=lambda x: x["final_score"], reverse=True)
        ] + [
            {
                "candidate_id": item["candidate"]["candidate_id"],
                "title": item["candidate"]["title"],
                "final_score": item["final_score"],
                "relationship": item["candidate"]["relationship"],
                "blocked_reason": "update_chain_without_material_update",
            }
            for item in backlog
        ]
    }
    return decision_packet


def build_newsroom_schedule(
    *,
    schedule_date: str,
    pool_path: Path,
    windows_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Process all five windows sequentially to produce the newsroom schedule."""
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    config = json.loads(windows_path.read_text(encoding="utf-8"))
    
    # Simple self-contained schema/invariants verification
    errors = []
    if pool.get("schema_version") != "capital_chronicle.newsroom_candidate_pool.v1":
        errors.append("pool_schema_version_invalid")
    if not pool.get("database_binding") or not pool["database_binding"].get("head_sha"):
        errors.append("database_binding_missing")
        
    core = {k: v for k, v in pool.items() if k not in ("pool_id", "logical_hash")}
    expected_hash = _logical_hash(core)
    if pool.get("logical_hash") != expected_hash:
        errors.append("pool_logical_hash_mismatch")
        
    if errors:
        raise ValueError(f"candidate_pool_invalid: {', '.join(errors)}")
        
    previously_published = []
    decisions = []
    
    for window in config["windows"]:
        dec = evaluate_window_decision(
            window=window,
            schedule_date=schedule_date,
            pool=pool,
            previously_published=previously_published,
        )
        decisions.append(dec)
        if dec["decision"] == "PUBLISH":
            previously_published.append(dec["selected_candidate"])
            
    schedule = {
        "schema_version": SCHEMA_VERSION,
        "schedule_date": schedule_date,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "database_head_sha": pool["database_binding"]["head_sha"],
        "pool_logical_hash": pool["logical_hash"],
        "decisions": decisions,
        "summary": {
            "total_windows": len(decisions),
            "publications": len(previously_published),
            "backlog_count": sum(len(d["backlog_candidates"]) for d in decisions),
        }
    }
    
    digest = _logical_hash(schedule)
    schedule["schedule_id"] = f"cc-schedule-{digest[:20]}"
    schedule["logical_hash"] = digest
    
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"newsroom_schedule_{schedule_date.replace('-', '_')}.json"
    out_path.write_text(json.dumps(schedule, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return schedule


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic ContentOps daily schedule.")
    parser.add_argument("--date", required=True)
    parser.add_argument("--pool", type=Path, required=True)
    parser.add_argument("--windows", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    
    try:
        schedule = build_newsroom_schedule(
            schedule_date=args.date,
            pool_path=args.pool,
            windows_path=args.windows,
            output_dir=args.output_dir,
        )
        print(json.dumps({
            "schedule_id": schedule["schedule_id"],
            "publications": schedule["summary"]["publications"],
        }))
        return 0
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
