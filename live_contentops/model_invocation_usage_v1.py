"""CC-402: project retained native run returns into the existing invocation table.

Native subscriptions do not expose a per-piece USD charge. Keep it null unless a
run actually reports it. The original non-null token columns remain compatible;
usage_metadata_json is the authoritative nullable usage for these imported rows.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import re
from zoneinfo import ZoneInfo


def _number(value, *, integer=False):
    return value if (type(value) is int if integer else type(value) in (int, float)) and math.isfinite(value) and value >= 0 else None


def import_native_invocations(store, *, lane_run_root=None):
    """Idempotent by exact retained response, not an ambiguous '/root' chat label."""
    store.ensure_model_usage_column()
    with store.get_read_only_connection() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT message_id,work_item_id,created_at,json_extract(payload,'$.invocation_observation') observation,"
            "json_extract(payload,'$.usage') usage,json_extract(payload,'$.cost_usd') cost_usd,"
            "json_extract(payload,'$.request_sha256') request_sha256 FROM outbox_messages "
            "WHERE destination='internal:native-desktop-editorial' AND json_type(payload,'$.output') IS NOT NULL "
            "AND json_type(payload,'$.invocation_observation')='object' "
            "AND coalesce(json_extract(payload,'$.reused_native_selection'),0)=0 ORDER BY rowid")]
        existing = {r[0] for r in conn.execute("SELECT invocation_id FROM model_invocations")}
        requests = {r["request_sha256"]: dict(r) for r in conn.execute(
            "SELECT json_extract(payload,'$.request_sha256') request_sha256,"
            "json_extract(payload,'$.requested_model') requested_model,"
            "json_extract(payload,'$.requested_reasoning_effort') requested_reasoning_effort,"
            "json_extract(payload,'$.stage') stage FROM outbox_messages "
            "WHERE destination='internal:native-desktop-editorial' AND json_type(payload,'$.requested_model')='text'")}
    added = 0
    for row in rows:
        value = row
        observation = json.loads(row["observation"])
        key = "native-usage-" + sha256(row["message_id"].encode()).hexdigest()
        if key in existing:
            continue
        request = requests.get(value.get("request_sha256"), {})
        usage = observation.get("usage") or json.loads(value.get("usage") or "{}")
        if not isinstance(usage, dict):
            usage = {}
        prompt = _number(usage.get("prompt_tokens", usage.get("input_tokens")), integer=True)
        completion = _number(usage.get("completion_tokens", usage.get("output_tokens")), integer=True)
        cost = _number(usage.get("cost_usd", observation.get("cost_usd", value.get("cost_usd"))))
        metadata = {
            "source_record_id": row["message_id"], "request_sha256": value.get("request_sha256"),
            "stage": request.get("stage"), "native_invocation_id": observation.get("invocation_id"),
            "model": observation.get("model"), "configured_model": observation.get("configured_model") or request.get("requested_model"),
            "reasoning_effort": observation.get("reasoning_effort"),
            "configured_reasoning_effort": observation.get("configured_reasoning_effort") or request.get("requested_reasoning_effort"),
            "configuration_status": observation.get("configuration_status"),
            "prompt_tokens": prompt, "completion_tokens": completion, "cost_usd": cost,
            "usage_state": "OBSERVED" if prompt is not None and completion is not None else "NOT_EXPOSED_BY_RUN_RECORD",
            "cost_state": "OBSERVED_RUN_COST" if cost is not None else "USD_COST_NOT_EXPOSED_BY_RUN_RECORD",
            "observation_source": observation.get("observation_source"),
        }
        with store.get_connection() as conn:
            count = conn.execute(
                "INSERT OR IGNORE INTO model_invocations "
                "(invocation_id,work_item_id,model_id,prompt_tokens,completion_tokens,invoked_at,usage_metadata_json) "
                "VALUES (?,?,?,?,?,?,?)",
                (key, row["work_item_id"], observation.get("model") or metadata["configured_model"] or "UNREPORTED",
                 prompt or 0, completion or 0, observation.get("observed_at_utc") or row["created_at"],
                 json.dumps(metadata, sort_keys=True)),
            ).rowcount
        added += count
    lane = import_lane_run_usage(store, root=lane_run_root)
    return {"imported": added + lane, "native_returns_imported": added, "lane_runs_updated": lane,
            "source": "retained_native_returns_and_lane_run_records", "model_calls": 0}


def import_lane_run_usage(store, *, root=None):
    """Read only a terminal CLI counter, bound to one item and one dated piece.

    Resumes repeat a cumulative counter. Keep the largest reported total; never
    add it to the native role token counts or price a subscription as API usage.
    """
    root = Path(root) if root is not None else Path(store.db_path).parent.parent.parent / "ResearchRuns/claude-ops-integrations/codex-exec"
    with store.get_read_only_connection() as conn:
        candidates = {r[0] for r in conn.execute("SELECT DISTINCT work_item_id FROM model_invocations")}
        live_work = {r[0] for r in conn.execute("SELECT work_item_id FROM work_items")}
        binding_owners = {}
        for row in conn.execute("SELECT work_item_id,json_extract(payload,'$.work_item_id') FROM outbox_messages WHERE destination='internal:native-publication-binding'"):
            candidates.add(row[1])
            binding_owners.setdefault(row[1], set()).add(row[0])
    pieces = {}
    for work in candidates:
        match = re.fullmatch(r"cc(\d+)-.*?(20\d{6})(?:-.*)?", str(work))
        if match:
            pieces.setdefault(("CC-" + match[1], match[2]), set()).add(work)
    updated = 0
    for path in sorted(root.glob("*/launch.json")):
        try:
            launch = json.loads(path.read_bytes())
            items = launch.get("items")
            if not isinstance(items, list) or len(items) != 1:
                continue
            started = datetime.fromisoformat(launch["started_utc"].replace("Z", "+00:00"))
            if started.tzinfo is None:
                continue
            matches = pieces.get((items[0], started.astimezone(ZoneInfo("Asia/Bangkok")).strftime("%Y%m%d")), set())
            if len(matches) != 1:
                continue
            totals, sources = [], []
            for log in sorted(path.parent.glob("stderr*.txt")):
                with log.open("rb") as stream:
                    stream.seek(max(0, log.stat().st_size - 2048))
                    tail = stream.read().decode("utf-8", "replace")
                values = re.findall(r"(?:^|\n)tokens used\s*\n([\d,]+)\s*\Z", tail)
                if values:
                    totals.append(int(values[-1].replace(",", "")))
                    sources.append({"path": str(log), "reported_tokens_used": totals[-1]})
            if not totals:
                continue
            work = next(iter(matches))
            owners = {work} if work in live_work else binding_owners.get(work, set())
            if len(owners) != 1:
                continue
            owner = next(iter(owners))
            metadata = {"source_record_id": str(path), "usage_scope": "CUMULATIVE_CLI_RUN_TOTAL",
                "bound_piece_work_item_id": work, "piece_binding_method": "SINGLE_ITEM_SINGLE_DATED_BOUND_PIECE",
                "stage": "lane-run", "model": None, "reasoning_effort": None,
                "configured_model": launch.get("model"), "configured_reasoning_effort": launch.get("reasoning_effort"),
                "configuration_status": "CONFIGURED_NOT_OBSERVED", "cli_reported_tokens_used": max(totals),
                "prompt_tokens": None, "completion_tokens": None, "cost_usd": None,
                "usage_state": "CLI_TOTAL_OBSERVED_INPUT_OUTPUT_SPLIT_NOT_EXPOSED",
                "cost_state": "USD_COST_NOT_EXPOSED_BY_RUN_RECORD", "source_counters": sources}
            encoded = json.dumps(metadata, sort_keys=True)
            key = "lane-run-usage-" + sha256(str(path.resolve()).encode()).hexdigest()
            with store.get_connection() as conn:
                current = conn.execute("SELECT usage_metadata_json FROM model_invocations WHERE invocation_id=?", (key,)).fetchone()
                if current and current[0] == encoded:
                    continue
                conn.execute("INSERT INTO model_invocations (invocation_id,work_item_id,model_id,prompt_tokens,completion_tokens,invoked_at,usage_metadata_json) "
                    "VALUES (?,?,?,0,0,?,?) ON CONFLICT(invocation_id) DO UPDATE SET usage_metadata_json=excluded.usage_metadata_json",
                    (key, owner, launch.get("model") or "UNREPORTED", started.astimezone(timezone.utc).isoformat(), encoded))
                updated += 1
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return updated


def piece_usage(store, work_item_id):
    with store.get_read_only_connection() as conn:
        owners = {work_item_id}
        owners.update(row[0] for row in conn.execute(
            "SELECT work_item_id FROM outbox_messages WHERE destination='internal:native-publication-binding' "
            "AND json_extract(payload,'$.work_item_id')=?", (work_item_id,)))
        rows = [dict(r) for r in conn.execute("SELECT * FROM model_invocations WHERE work_item_id IN (" +
            ",".join("?" for _ in owners) + ") ORDER BY invoked_at,invocation_id", tuple(owners))]
    records = [json.loads(r.get("usage_metadata_json") or "{}") for r in rows]
    costs = [r.get("cost_usd") for r in records]
    return {"work_item_id": work_item_id, "invocation_count": len(rows),
            "cost_usd": sum(costs) if costs and all(c is not None for c in costs) else None,
            "cost_state": "OBSERVED_RUN_COST" if costs and all(c is not None for c in costs) else "USD_COST_NOT_EXPOSED_BY_RUN_RECORD",
            "lane_run_usage": [r for r in records if r.get("usage_scope") == "CUMULATIVE_CLI_RUN_TOTAL"],
            "invocations": records}
