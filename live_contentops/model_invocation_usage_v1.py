"""CC-402: project retained native run returns into the existing invocation table.

Native subscriptions do not expose a per-piece USD charge. Keep it null unless a
run actually reports it. The original non-null token columns remain compatible;
usage_metadata_json is the authoritative nullable usage for these imported rows.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math


def _number(value, *, integer=False):
    return value if (type(value) is int if integer else type(value) in (int, float)) and math.isfinite(value) and value >= 0 else None


def import_native_invocations(store):
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
    return {"imported": added, "source": "retained_native_run_returns", "model_calls": 0}


def piece_usage(store, work_item_id):
    with store.get_read_only_connection() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM model_invocations WHERE work_item_id=? ORDER BY invoked_at,invocation_id", (work_item_id,))]
    records = [json.loads(r.get("usage_metadata_json") or "{}") for r in rows]
    costs = [r.get("cost_usd") for r in records]
    return {"work_item_id": work_item_id, "invocation_count": len(rows),
            "cost_usd": sum(costs) if costs and all(c is not None for c in costs) else None,
            "cost_state": "OBSERVED_RUN_COST" if costs and all(c is not None for c in costs) else "USD_COST_NOT_EXPOSED_BY_RUN_RECORD",
            "invocations": records}
