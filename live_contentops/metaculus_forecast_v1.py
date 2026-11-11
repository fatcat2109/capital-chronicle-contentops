"""CC-428: compile Main forecasts into Metaculus requests without sending them.

This is a consumer of Main's numbers, not an estimator or a publisher.  The
returned atomic forecast/comment request is for the existing publication owner.
The CC-428 command has no network, credential, schedule, or submission path.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import gzip
import json
import math
from pathlib import Path

from live_contentops.event_article_guard_v1 import PUBLIC_NOTICE
from live_contentops.preview_link_guard_v1 import find_forbidden_link
from live_contentops.public_time_v1 import require_public_time
from tools.product.desk_record_projection_v1 import public_text_problems


SCHEMA = "contentops.metaculus_dry_run.v1"
ENDPOINT = "https://www.metaculus.com/api/questions/bulk-forecast-comment/"
MARKETS = ("XAUUSD", "BTCUSD", "US500", "EURUSD", "USDJPY", "USOIL")
PROBABILITIES = {
    "probability_up_pct": "TERMINAL_ABOVE_REFERENCE",
    "probability_touch_pct": "TOUCH_PLAN_ENTRY",
    "probability_target_before_stop_pct": "TARGET_BEFORE_STOP",
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return sha256(canonical(value)).hexdigest()


def utc(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("FORECAST_CLOCK_REQUIRES_TIMEZONE")
    return parsed.astimezone(timezone.utc)


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _load(path):
    raw = Path(path).read_bytes()
    if str(path).endswith(".gz"):
        raw = gzip.decompress(raw)
    return json.loads(raw), sha256(raw).hexdigest()


def plan_forecasts(path):
    """Allowlist Main's public forecast fields. Never export execution/outcome rows.

    The currently observed export version is available at its generation clock.
    Registration and quote clocks do not prove these probability fields existed
    in that earlier version. This matters in a closed-round replay.
    """
    doc, raw_hash = _load(path)
    if doc.get("schema") != "CapitalChroniclePlanStatusV1":
        raise ValueError("MAIN_PUBLIC_PLAN_EXPORT_REQUIRED")
    if digest({k: v for k, v in doc.items() if k != "content_hash"}) != doc.get("content_hash"):
        raise ValueError("MAIN_PUBLIC_PLAN_EXPORT_HASH_MISMATCH")
    utc(doc["generated_at_utc"])
    forecasts = []
    for index, plan in enumerate(doc["plans"]):
        if plan.get("asset_id") not in MARKETS:
            continue
        values = plan.get("forecast_probabilities") or {}
        for field, measure in PROBABILITIES.items():
            value = values.get(field)
            if value is None:
                continue
            if not _number(value) or not 0 <= value <= 100:
                raise ValueError("MAIN_PROBABILITY_PERCENT_INVALID")
            contract = deepcopy((values.get("target_contracts") or {}).get(field))
            if contract is None:
                contract = {"instrument": plan["asset_id"], "measure": measure,
                    "unit": values.get("target_unit"),
                    "horizon_start_utc": values.get("reference_at_utc"),
                    "horizon_end_utc": values.get("horizon_end_utc"),
                    "resolution_source": values.get("resolution_source"),
                    "conditioning": values.get("conditioning")}
                if field == "probability_up_pct":
                    contract["predicate"] = {"operator": ">", "threshold": values.get("reference_price")}
            forecasts.append({
                "forecast_id": plan["plan_id"] + ":" + field,
                "assets": [plan["asset_id"]], "measure": measure,
                "format": "binary", "probability_yes": float(Decimal(str(value)) / 100),
                "source_value": value, "source_unit": "percent",
                "available_at_utc": doc["generated_at_utc"],
                "registered_at_utc": plan.get("registered_at_utc"),
                "reference_at_utc": values.get("reference_at_utc"),
                "reference_price": values.get("reference_price"),
                "horizon_end_utc": values.get("horizon_end_utc"),
                "probability_basis": values.get("probability_basis"),
                # Use any exact producer binding; otherwise expose every held
                # target component, leaving resolver/unit/conditioning unknown.
                "contract": contract,
                "source": {"path": str(path), "sha256": raw_hash,
                    "pointer": f"/plans/{index}/forecast_probabilities/{field}"},
                "public_model_estimate": True,
            })
    return {"kind": "MAIN_PUBLIC_PLAN_EXPORT", "source_path": str(path),
        "source_sha256": raw_hash, "generated_at_utc": doc["generated_at_utc"],
        "plan_count": len(doc["plans"]), "forecasts": forecasts}


def event_forecasts(path, *, observed_at_utc):
    """Project only Main's model probabilities, never the raw consensus/history.

    Retained scoring bundles state a data cutoff, not proof of when this exact
    bundle first existed. Retain that cutoff separately from today's observation.
    """
    doc, raw_hash = _load(path)
    forecasts = []
    for i, matrix in enumerate(doc.get("matrices", [])):
        probabilities = {b["branch"]: b["probability"] for b in matrix.get("branches", [])
                         if b.get("probability") is not None}
        if not probabilities:
            continue
        if any(not _number(v) or not 0 <= v <= 1 for v in probabilities.values()):
            raise ValueError("MAIN_EVENT_PROBABILITY_INVALID")
        forecasts.append({
            "forecast_id": doc["target"]["event_id"] + ":matrix:" + str(i),
            "assets": [doc["target"]["event_type"]], "format": "scenario_bands",
            "probabilities": probabilities, "source_value": probabilities,
            "source_unit": "probability", "target": deepcopy(matrix["target"]),
            "bands": deepcopy(matrix["bands"]),
            "available_at_utc": observed_at_utc, "data_cutoff_utc": matrix["cutoff_utc"],
            "probability_basis": matrix.get("probability_measure"),
            "conditioning": matrix.get("probability_scope"),
            "public_model_estimate": matrix.get("public_probabilities_eligible") is True,
            "contract": {"instrument": matrix["target"]["event_type"],
                "measure": matrix["target"].get("measure_id"), "unit": matrix["target"].get("unit"),
                "reference_period": matrix["target"].get("reference_period"),
                "horizon_start_utc": None,
                "horizon_end_utc": matrix["target"].get("released_at_utc"),
                "resolution_source": matrix["target"].get("release_identity"),
                "conditioning": matrix.get("probability_scope"), "bands": deepcopy(matrix["bands"])},
            "source": {"path": str(path), "sha256": raw_hash, "pointer": f"/matrices/{i}/branches"},
        })
    return {"kind": "MAIN_EVENT_SCENARIO_MATRIX", "source_path": str(path),
        "source_sha256": raw_hash, "observed_at_utc": observed_at_utc, "forecasts": forecasts}


def normalize_posts(posts):
    """Keep post and question IDs distinct, including numeric group children.

    API fields hidden by the gateway remain None. Do not substitute a post ID,
    a community forecast, or an outcome for missing question metadata.
    """
    rows = []
    for post in posts:
        questions = []
        if post.get("question"):
            questions.append(post["question"])
        questions.extend((post.get("group_of_questions") or {}).get("questions") or [])
        if post.get("conditional"):
            rows.append({"post_id": post["id"], "question_id": None,
                "title": post.get("title"), "type": "conditional",
                "contract": None, "metadata_cause": "CONDITIONAL_CONTRACT_NOT_IMPLEMENTED"})
        for q in questions:
            rows.append({"post_id": post["id"], "question_id": q.get("id"),
                "title": q.get("title") or post.get("title"), "type": q.get("type"),
                "open_at_utc": q.get("open_time"),
                "close_at_utc": q.get("actual_close_time") or q.get("scheduled_close_time"),
                "scaling": deepcopy(q.get("scaling")), "options": deepcopy(q.get("options")),
                "description": q.get("description"), "resolution_criteria": q.get("resolution_criteria"),
                "fine_print": q.get("fine_print"), "contract": None})
    return rows


def _contract_valid(contract):
    return isinstance(contract, dict) and all(contract.get(k) is not None for k in (
        "instrument", "measure", "unit", "horizon_start_utc", "horizon_end_utc",
        "resolution_source", "conditioning"))


def _forecast_body(question, forecast):
    qid = question.get("question_id")
    if not isinstance(qid, int) or isinstance(qid, bool) or qid <= 0:
        raise ValueError("PLATFORM_QUESTION_ID_UNAVAILABLE")
    kind = question.get("type")
    if kind == "binary" and forecast.get("format") == "binary":
        probability = forecast.get("probability_yes")
        if not _number(probability) or not 0 <= probability <= 1:
            raise ValueError("PROBABILITY_INVALID")
        return {"question": qid, "probability_yes": probability}
    if kind in {"numeric", "discrete", "date"} and forecast.get("format") == "continuous":
        scale = question.get("scaling")
        if not scale or scale != forecast.get("scaling"):
            raise ValueError("NUMERIC_SCALE_MISMATCH_OR_UNAVAILABLE")
        cdf = forecast.get("continuous_cdf")
        if (not isinstance(cdf, list) or len(cdf) != 201
                or any(not _number(v) or not 0 <= v <= 1 for v in cdf)
                or any(a > b for a, b in zip(cdf, cdf[1:]))):
            raise ValueError("MAIN_CDF_INVALID")
        return {"question": qid, "continuous_cdf": deepcopy(cdf)}
    if kind == "multiple_choice" and forecast.get("format") == "multiple_choice":
        values = forecast.get("probability_yes_per_category")
        options = question.get("options")
        if (not isinstance(values, dict) or not options or set(values) != set(options)
                or any(not _number(v) or not 0 <= v <= 1 for v in values.values())
                or abs(sum(values.values()) - 1) > 1e-9):
            raise ValueError("MAIN_OPTION_DISTRIBUTION_INVALID")
        return {"question": qid, "probability_yes_per_category": deepcopy(values)}
    raise ValueError("MAIN_DISTRIBUTION_DOES_NOT_MATCH_QUESTION_TYPE")


def _match(question, forecasts, *, as_of_utc, replay):
    topics = set(question.get("desk_topics") or [])
    related = topics | set(question.get("related_desk_topics") or [])
    candidates = [f for f in forecasts if related.intersection(f.get("assets", []))]
    if not topics:
        return None, ("RELATED_MARKET_IS_NOT_THE_QUESTION_INSTRUMENT" if candidates else
                      "OUTSIDE_SIX_MARKETS_CPI_PAYROLL_SCOPE"), candidates
    contract = question.get("contract")
    if not _contract_valid(contract):
        return None, "PLATFORM_FULL_RESOLUTION_CONTRACT_UNAVAILABLE", candidates
    exact = [f for f in candidates if _contract_valid(f.get("contract")) and f["contract"] == contract]
    if not exact:
        return None, "NO_EXACT_MAIN_TARGET_INSTRUMENT_HORIZON_RESOLVER", candidates
    close = question.get("close_at_utc")
    opening = question.get("open_at_utc")
    if not close or not opening:
        return None, "PLATFORM_QUESTION_CLOCK_UNAVAILABLE", candidates
    now, stop, start = utc(as_of_utc), utc(close), utc(opening)
    if not start < stop:
        return None, "PLATFORM_QUESTION_CLOCK_INVALID", candidates
    if replay and now < stop:
        return None, "CLOSED_ROUND_REPLAY_REQUIRES_CLOSED_QUESTION", candidates
    if not replay and not start <= now < stop:
        return None, "QUESTION_NOT_OPEN", candidates
    eligible = [f for f in exact if f.get("available_at_utc")
                and utc(f["available_at_utc"]) <= now and utc(f["available_at_utc"]) < stop]
    if not eligible:
        return None, "MAIN_VERSION_AVAILABLE_AFTER_FORECAST_DEADLINE", candidates
    # Distinct source versions of the same forecast are not extra votes. Never
    # average, complement, clip, select the nicest answer, or replay one twice.
    identities = {(f["forecast_id"], digest(f)) for f in eligible}
    if len(identities) != 1:
        return None, "AMBIGUOUS_EXACT_MAIN_FORECAST", candidates
    forecast = eligible[0]
    if not forecast.get("public_model_estimate"):
        return None, forecast.get("public_restriction") or "PUBLIC_SOURCE_RIGHTS_NOT_RECORDED", candidates
    return forecast, None, candidates


def compile_round(round_input, inventories, *, as_of_utc, replay=True, acting_user=None):
    """One answer per question and an atomic API body for each exact match.

    Closed-round matching is a replay, never a scored or submitted prediction.
    Source numbers remain useful in every mismatch row and in the inventory.
    """
    utc(as_of_utc)
    forecasts = [f for inventory in inventories for f in inventory["forecasts"]]
    rows, requests, seen = [], [], set()
    for question in round_input["questions"]:
        key = ("question", question["question_id"]) if question.get("question_id") is not None else (
            "post", question["post_id"])
        if key in seen:
            raise ValueError("DUPLICATE_PLATFORM_QUESTION")
        seen.add(key)
        forecast, cause, candidates = _match(question, forecasts, as_of_utc=as_of_utc, replay=replay)
        row = {"post_id": question["post_id"], "question_id": question.get("question_id"),
            "title": question["title"], "url": question.get("url"),
            "desk_topics": question.get("desk_topics", []),
            "related_desk_topics": question.get("related_desk_topics", []),
            "state": "ABSTAIN", "first_cause": cause,
            "candidate_forecast_ids": [f["forecast_id"] for f in candidates]}
        if forecast is not None:
            try:
                body = _forecast_body(question, forecast)
                explanation = forecast.get("public_explanation")
                if not isinstance(explanation, str) or not explanation.strip():
                    raise ValueError("MAIN_PUBLIC_EXPLANATION_UNAVAILABLE")
                if public_text_problems(explanation):
                    raise ValueError("MAIN_EXPLANATION_CONTAINS_PRIVATE_OR_RESTRICTED_CONTENT")
                if find_forbidden_link(explanation):
                    raise ValueError("PREVIEW_HOST_LINK_FORBIDDEN")
                require_public_time(explanation)
                text = explanation if PUBLIC_NOTICE in explanation else explanation + "\n\n" + PUBLIC_NOTICE
                payload = {"forecasts": [body], "comments": [{"on_post": question["post_id"],
                    "text": text,
                    "is_private": True, "included_forecast": True}]}
                if acting_user is not None:
                    payload["acting_user"] = acting_user
                request = {"method": "POST", "url": ENDPOINT, "json": payload,
                    "identity": {"round_id": round_input["round_id"], "question_id": question["question_id"]},
                    "source": deepcopy(forecast["source"]), "source_forecast_id": forecast["forecast_id"]}
                request["request_sha256"] = digest(request)
                requests.append(request)
                row.update(state="MATCHED_REPLAY" if replay else "PREPARED", first_cause=None,
                           source_forecast_id=forecast["forecast_id"], request_sha256=request["request_sha256"])
            except ValueError as exc:
                row["first_cause"] = str(exc)
        rows.append(row)
    return {"schema_version": SCHEMA, "round_id": round_input["round_id"],
        "generated_at_utc": as_of_utc, "mode": "CLOSED_ROUND_REPLAY" if replay else "CURRENT_PREPARATION",
        "listing_consistency": round_input.get("listing_consistency"),
        "advertised_question_count": round_input.get("advertised_question_count"),
        "submission_count": 0, "network_call_count": 0,
        "question_count": len(rows), "matched_count": len(requests),
        "abstained_count": sum(r["state"] == "ABSTAIN" for r in rows),
        "first_causes": dict(Counter(r["first_cause"] for r in rows if r["first_cause"])),
        "inventory": deepcopy(inventories), "answers": rows, "prepared_requests": requests,
        "external_score": None, "external_rank": None,
        "next_owner": "Ops Product", "write_scope": "CC-428 explicitly requires a dry run without submission"}
