"""Resumable native semantic judgments in the existing opportunity outbox.

The frozen governed intake supplies admissibility. This layer never captures X, establishes
source truth, changes source records or owns a second cursor/store. Decisions are reusable
only for exact record bytes and this filter policy; corrections invalidate their own hash.
"""
from __future__ import annotations

import json
from collections import Counter
from urllib.parse import urlsplit

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of

POLICY = "contentops.native_headline_filter.v1"
BATCH_SIZE = 24


def _is_x(row):
    external = row.get("external_content") or {}
    urls = [row.get(k) for k in ("source_url", "tweet_url", "url", "url_or_source_ref")]
    urls += [external.get(k) for k in ("source_url", "tweet_url", "url", "url_or_source_ref")]
    return (str(row.get("source_platform") or external.get("source_platform") or "").upper()
            in {"X", "TWITTER", "X_LIST", "CANONICAL_X_LIST"}
            or any(urlsplit(str(u or "")).hostname in {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}
                   for u in urls))


def _validate(raw, expected):
    try:
        value = json.loads(raw)
        decisions = value["decisions"]
        if set(value) != {"schema_version", "decisions", "public_write_attempted"} or value["schema_version"] != POLICY:
            raise ValueError("filter_schema")
        if value["public_write_attempted"] is not False or not isinstance(decisions, list):
            raise ValueError("filter_authority_or_list")
        seen = set()
        for row in decisions:
            if set(row) != {"input_sha256", "headline_id", "decision", "reason", "group_key", "novelty"}:
                raise ValueError("filter_fields")
            key = row["input_sha256"]
            if key in seen or key not in expected or row["headline_id"] != expected[key]:
                raise ValueError("filter_identity")
            if row["decision"] not in {"KEEP", "REJECT", "DEFER"} or not isinstance(row["reason"], str) or len(row["reason"].strip()) < 8:
                raise ValueError("filter_decision_reason")
            if not all(isinstance(row[k], str) and row[k].strip() for k in ("group_key", "novelty")):
                raise ValueError("filter_group_novelty")
            seen.add(key)
        if seen != set(expected):
            raise ValueError("filter_incomplete_batch")
        return True, None, value, None
    except (ValueError, KeyError, TypeError) as exc:
        return False, "structured_output_schema_invalid", None, str(exc)


def filter_native_headlines(turn, rolling_input):
    rows = [dict(r) for r in rolling_input.get("headlines", [])]
    exact = {}
    bypass = []
    for row in rows:
        if not _is_x(row):
            bypass.append(row)
            continue
        # Locators are diagnostic; changes to source text, provenance, clocks, permissions,
        # correction/update identity or evidence context invalidate that exact record only.
        stable = {k: v for k, v in row.items() if k != "source_locator"}
        key = sha256_of([POLICY, stable])
        exact.setdefault(key, row)
    ordered = sorted(exact, key=lambda k: (str(exact[k].get("source_timestamp_utc") or ""),
                                            str(exact[k].get("headline_id") or ""), k))
    judgments = {}

    def retain(output, provenance):
        for value in output["decisions"]:
            key = value["input_sha256"]
            sealed = {**value, "request_sha256": provenance["request_sha256"],
                      "response_sha256": provenance["response_sha256"], "role": "filter",
                      "invocation_observation": provenance["observation"]}
            persisted = turn.store.register_outbox_message(message_id="native-filter-decision-" + key,
                work_item_id=turn.work, destination="internal:native-desktop-editorial",
                payload=canonical_bytes(sealed).decode(), status="EDITORIAL_INTERNAL")
            if json.loads(persisted["payload"]) != sealed:
                raise ValueError("NATIVE_FILTER_IMMUTABLE_DECISION_CONFLICT")

    # Recover an accepted batch even if interruption occurred between its durable return
    # and per-record materialization. No repeat semantic call or changed batch cursor.
    for row in turn.store.list_outbox_messages():
        if row["work_item_id"] != turn.work:
            continue
        request = json.loads(row["payload"])
        stage = str(request.get("stage") or "")
        if not stage.startswith("filter-") or "requested_model" not in request:
            continue
        if turn._get(stage, "response") is None:
            continue
        expected = {r["input_sha256"]: r["original_record"]["headline_id"]
                    for r in request["governed_input"]["records"]}
        output, provenance = turn(logical_invocation_id=turn.run_id + ":" + stage,
            prompt=request["prompt"], governed_input=request["governed_input"],
            validator=lambda raw: _validate(raw, expected))
        retain(output, provenance)
    for key in ordered:
        persisted = turn.store.get_outbox_message("native-filter-decision-" + key)
        if persisted:
            value = json.loads(persisted["payload"])
            if value["input_sha256"] != key or value["headline_id"] != exact[key]["headline_id"]:
                raise ValueError("NATIVE_FILTER_CACHED_BINDING_MISMATCH")
            judgments[key] = value
    missing = [k for k in ordered if k not in judgments]
    for offset in range(0, len(missing), BATCH_SIZE):
        keys = missing[offset:offset + BATCH_SIZE]
        stage = "filter-" + sha256_of([POLICY, keys])
        governed = {"policy": POLICY, "cursor_sha256": sha256_of(keys),
                    "records": [{"input_sha256": k, "original_record": exact[k]} for k in keys],
                    "semantic_judgment_is_source_truth": False}
        contract = {"schema_version": POLICY, "public_write_attempted": False, "decisions": [
            {"input_sha256": "exact input hash", "headline_id": "exact original ID", "decision": "KEEP | REJECT | DEFER",
             "reason": "specific relevance reason", "group_key": "semantic story grouping only",
             "novelty": "new development / correction / update / duplicate / uncertain"}]}
        prompt = ("You own semantic X-headline relevance filtering for Capital Chronicle. Judge EVERY record in this bounded batch. "
                  "Keep useful macro/markets/institutional stories, preserve useful corrections/updates and original identities. "
                  "Reject irrelevant/redundant items; defer unresolved relevance explicitly. A source claim is unverified reporting, "
                  "not event truth. Grouping never merges or rewrites original records. No source retrieval, selection of final angle, "
                  "article prose, numeric calculations or public writes. Return strict JSON only.\nOUTPUT_CONTRACT:\n"
                  + json.dumps(contract) + "\nGOVERNED_INPUT:\n" + json.dumps(governed, ensure_ascii=False))
        output, provenance = turn(logical_invocation_id=turn.run_id + ":" + stage, prompt=prompt,
                                  governed_input=governed,
                                  validator=lambda raw: _validate(raw, {k: exact[k]["headline_id"] for k in keys}))
        retain(output, provenance)
        for value in output["decisions"]:
            judgments[value["input_sha256"]] = json.loads(turn.store.get_outbox_message(
                "native-filter-decision-" + value["input_sha256"])["payload"])
    counts = Counter(j["decision"] for j in judgments.values())
    receipt = {"schema_version": POLICY, "scope": "ALL_X_RECORDS_IN_FROZEN_GOVERNED_INTAKE",
               "input_record_count": len(rows), "non_x_preserved_count": len(bypass),
               "exact_deduped_x_count": len(ordered), "seen": len(judgments),
               "kept": counts["KEEP"], "rejected": counts["REJECT"], "deferred": counts["DEFER"],
               "remaining_unprocessed": len(ordered) - len(judgments), "batch_size": BATCH_SIZE,
               "cursor_sha256": sha256_of(ordered), "decisions_sha256": sha256_of(judgments),
               "decisions": [judgments[k] for k in ordered], "source_truth_authority": False,
               "downstream_candidate_limit": 32, "public_write_performed": False}
    # Cached count changes on restart; keep it out of immutable output bytes.
    return {**rolling_input, "native_semantic_filter_applied": True,
            "headlines": bypass + [exact[k] for k in ordered if judgments[k]["decision"] == "KEEP"]}, receipt
