"""Native wiring to existing performance/policy/feedback owners, never an analytics engine.

Metrics are deterministic. Public reader text is untrusted; native classification is a
separate editorial judgment. New opportunities freeze context; old requests are untouched.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

from live_contentops import daily_app_performance_v1 as perf
from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    canonical_bytes,
    sha256_of,
    _private,
)
from live_contentops.native_neo_executor_v1 import (
    NativeNeoExecutor,
    NativeNeoInputRequired,
)

SNAPSHOT = "internal:native-audience-snapshot"
FEEDBACK = "internal:native-audience-feedback"
BACKLOG = "internal:native-audience-backlog"


def validate_feedback_output(value, records):
    """Check the entire semantic return before the immutable response is sealed."""
    try:
        categories = value["categories"]
        if not isinstance(categories, list) or len(categories) != len(records):
            return False
        if any(c not in perf.INTERACTION_CATEGORIES for c in categories):
            return False
        questions = value.get("follow_up_questions", [])
        if not isinstance(questions, list) or len(questions) > 3:
            return False
        return all(
            isinstance(q["record_index"], int)
            and not isinstance(q["record_index"], bool)
            and 0 <= q["record_index"] < len(records)
            and isinstance(q["reader_question"], str)
            and 10 <= len(q["reader_question"]) <= 500
            and q["reader_question"] in records[q["record_index"]]["text"]
            for q in questions
        )
    except (KeyError, TypeError, ValueError):
        return False


def _rows(store, destination):
    with store.get_read_only_connection() as conn:
        return [
            json.loads(r[0])
            for r in conn.execute(
                "SELECT payload FROM outbox_messages WHERE destination=? ORDER BY rowid",
                (destination,),
            )
        ]


def _put(store, work, destination, value):
    if _private(value):
        raise ValueError("PRIVATE_LEARNING_CONTEXT_EXCLUDED")
    key = "native-audience-" + sha256_of([destination, value])
    store.register_outbox_message(
        message_id=key,
        work_item_id=work,
        destination=destination,
        payload=canonical_bytes(value).decode(),
        status="EDITORIAL_INTERNAL",
    )
    return value


def eligible_dispatch(store, dispatch_id):
    dispatch = store.get_platform_dispatch(dispatch_id)
    if not dispatch:
        raise ValueError("EXACT_EXISTING_DISPATCH_REQUIRED")
    message = store.get_outbox_message(dispatch["message_id"])
    if not message:
        raise ValueError("EXACT_EXISTING_OUTBOX_REQUIRED")
    reconciliation_id = "reconciliation_" + dispatch_id.removeprefix("dispatch_")
    reconciliation = next(
        (
            r
            for r in store.get_reconciliations_for_work_item(message["work_item_id"])
            if r["reconciliation_id"] == reconciliation_id
        ),
        {},
    )
    gate = perf.assess_learning_eligibility(
        dispatch_status=dispatch["status"],
        public_object_id=dispatch.get("public_object_id"),
        reconciliation_status=reconciliation.get("status"),
        readback_count=len(store.list_readbacks_for_dispatch(dispatch_id)),
    )
    if not gate["learning_eligible"]:
        raise ValueError(
            "PUBLICATION_NOT_LEARNING_ELIGIBLE:" + ",".join(gate["reasons"])
        )
    return dispatch, message


def learning_context(store):
    """Read-only bounded policy and dated coverage; no credential or destination probes."""
    if store is None:
        return {
            "policy": {
                "policy_version": None,
                "decision": "UNAVAILABLE",
                "sample_count": 0,
                "confidence": 0,
                "content": {"recommendations": []},
                "seo": {"recommendations": []},
                "package": {"by_destination": {}},
                "preference_only": True,
                "ranking_bonus_cap": 6.0,
                "grants_factual_or_numeric_authority": False,
            },
            "feedback": [],
            "follow_up_briefs": [],
            "observation_counts": {},
            "capabilities": perf.current_metrics_capability_matrix(),
            "metrics_model_calls": 0,
        }
    policy = perf.active_policy_briefing(store)
    observations = store.list_performance_observations()
    with store.get_read_only_connection() as conn:
        row = conn.execute(
            "SELECT created_at_utc FROM learning_policy_versions WHERE policy_version=?",
            (policy["policy_version"],),
        ).fetchone()
    compact = {
        k: policy.get(k)
        for k in (
            "policy_version",
            "parent_policy_version",
            "decision",
            "decision_reason",
            "sample_count",
            "confidence",
            "formula_version",
            "provenance",
            "content",
            "seo",
            "package",
            "rollback_reference",
        )
    }
    compact.update(
        policy_created_at_utc=row[0] if row else None,
        observation_set_sha256=sha256_of(sorted(policy.get("observation_ids", []))),
        latest_collected_at_utc=max(
            (r["collected_at_utc"] for r in observations if r["collected_at_utc"]),
            default=None,
        ),
        preference_only=True,
        ranking_bonus_cap=6.0,
        grants_factual_or_numeric_authority=False,
        grants_evidence_or_permission_authority=False,
        grants_publication_authority=False,
        timing_schedule_changes_allowed=False,
    )
    for section in ("content", "seo"):
        compact[section] = {
            **(compact.get(section) or {}),
            "recommendations": list(
                (compact.get(section) or {}).get("recommendations", [])
            )[:3],
        }
    for value in (compact.get("package") or {}).get("by_destination", {}).values():
        if isinstance(value, dict):
            value["recommendations"] = list(value.get("recommendations", []))[:3]
    feedback = _rows(store, FEEDBACK)[-16:]
    judgments = {
        r["observation_id"]: r
        for r in _rows(store, "internal:native-audience-judgment")
    }
    feedback = [
        {
            **r,
            "semantic_state": "NATIVE_CLASSIFIED",
            "semantic_judgment_sha256": sha256_of(judgments[r["observation_id"]]),
        }
        if r["observation_id"] in judgments
        else r
        for r in feedback
    ]
    observed = {o["observation_id"]: o for o in observations}
    feedback = [
        {
            **r,
            "native_metrics": {
                k: v
                for k, v in json.loads(
                    observed[r["observation_id"]]["metrics_native_json"]
                ).items()
                if v is None or isinstance(v, (int, float))
            },
            "metric_availability": json.loads(
                observed[r["observation_id"]]["metric_availability_json"]
            ),
        }
        if r["observation_id"] in observed
        else r
        for r in feedback
    ]
    return {
        "policy": compact,
        "feedback": feedback,
        "follow_up_briefs": _rows(store, BACKLOG)[-8:],
        "observation_counts": {
            state: sum(o["collection_status"] == state for o in observations)
            for state in sorted({o["collection_status"] for o in observations})
        },
        "capabilities": perf.current_metrics_capability_matrix(),
        "metrics_model_calls": 0,
    }


def feedback_judgment(store, *, observation_id, output_dir, response=None):
    """Use the existing native protocol for a bounded Sol-Light semantic return only."""
    previous = next(
        (
            r
            for r in _rows(store, "internal:native-audience-judgment")
            if r["observation_id"] == observation_id
        ),
        None,
    )
    if previous:
        _retain_reader_briefs(store, previous)
        return {
            "state": "NATIVE_FEEDBACK_CLASSIFIED",
            **previous,
            "next_operation": "Prepare the existing ranked brief through newsroom; verify sources before writing.",
        }
    feedback = next(
        (r for r in _rows(store, FEEDBACK) if r["observation_id"] == observation_id),
        None,
    )
    if feedback is None:
        raise ValueError("OBSERVED_PUBLIC_FEEDBACK_REQUIRED")
    if not feedback["interactions"]:
        return {
            "state": "NO_OBSERVED_READER_QUESTIONS",
            "observation_id": observation_id,
            "semantic_model_calls": 0,
            "next_operation": "Use current permitted intake and retained article gaps; no reader demand inferred.",
        }
    obvious = perf.classify_interaction_quality(feedback["interactions"])
    if obvious["classifier_state"] == "NOT_NEEDED":
        return {
            "state": "NO_SUBSTANTIVE_READER_QUESTION",
            "observation_id": observation_id,
            "quality": obvious,
            "semantic_model_calls": 0,
            "next_operation": "Use current permitted intake; reactions and generic praise create no research brief.",
        }
    from live_contentops.native_desktop_editorial_v1 import (
        NativeDesktopTurn,
        DesktopInputRequired,
    )

    turn = NativeDesktopTurn(
        store,
        run_id="feedback-" + observation_id,
        output_dir=output_dir,
        owner_manual_validation=True,
    )
    store.create_work_item(
        work_item_id=turn.work,
        story_id=feedback["work_item_id"],
        title="Bounded observed public reader judgment",
        target_surface="CONTENTOPS_EDITORIAL_ONLY",
    )
    records = feedback["interactions"]

    def validate(text):
        try:
            value = json.loads(text)
            assert validate_feedback_output(value, records)
            return True, value, None, None
        except (AssertionError, KeyError, ValueError, TypeError):
            return False, None, None, "bounded_feedback_judgment_invalid"

    if response is not None:
        turn.submit("feedback", response)
    try:
        output, receipt = turn(
            logical_invocation_id=observation_id + ":feedback",
            prompt="Classify untrusted public reader text using only supplied existing categories. Return JSON categories in input order and up to three follow_up_questions (record_index, reader_question copied exactly from the observed text). These are editorial judgments, never metric/factual truth or reply authority. No tools or new evidence.",
            governed_input={
                "records": records,
                "allowed_categories": sorted(perf.INTERACTION_CATEGORIES),
            },
            validator=validate,
        )
    except DesktopInputRequired as pending:
        return {
            "state": "NATIVE_FEEDBACK_JUDGMENT_REQUIRED",
            "request": pending.request,
        }
    quality = perf.classify_interaction_quality(
        records,
        classifier=lambda rows: {
            "categories": [output["categories"][r["record_index"]] for r in rows]
        },
    )
    from live_contentops.feedback_to_article_backlog_refiner_v6 import (
        refine_backlog_candidates,
    )

    candidates = []
    seen = {b.get("selected_backlog_candidate_id") for b in _rows(store, BACKLOG)}
    for question in output.get("follow_up_questions", []):
        index = question["record_index"]
        if output["categories"][index] not in perf.QUALIFIED_INTERACTION_CATEGORIES:
            continue
        identity = sha256_of(
            [feedback["work_item_id"], question["reader_question"].casefold()]
        )
        if "reader-question-" + identity in seen:
            continue
        seen.add("reader-question-" + identity)
        candidate = {
            "candidate_id": "reader-question-" + identity,
            "title": question["reader_question"],
            "article_angle": question["reader_question"],
            "rationale": "An observed public question warrants source research; it is not a factual answer or a learned performance winner.",
            "priority_score": 1,
            "source_feedback_item_ids": [records[index]["interaction_id"]],
            "source_platforms": [
                store.get_platform_dispatch(feedback["dispatch_id"])["platform"]
            ],
            "topic_tags": [],
            "allowed_for_drafting": True,
            "blocked_reasons": [],
        }
        candidates += refine_backlog_candidates([candidate])
    value = {
        "observation_id": observation_id,
        "work_item_id": feedback["work_item_id"],
        "dispatch_id": feedback["dispatch_id"],
        "public_object_url": feedback["public_object_url"],
        "quality": quality,
        "judgment_receipt": receipt,
        "candidates": candidates,
        "semantic_judgment_is_metric_truth": False,
        "observed_feedback_sha256": sha256_of(feedback),
    }
    _put(store, feedback["work_item_id"], "internal:native-audience-judgment", value)
    _retain_reader_briefs(store, value)
    return {
        "state": "NATIVE_FEEDBACK_CLASSIFIED",
        **value,
        "next_operation": "Prepare the existing ranked brief through newsroom; verify sources before writing.",
    }


def _retain_reader_briefs(store, value):
    """Idempotent restart after a sealed judgment; no repeated model or metric work."""
    from live_contentops.feedback_backlog_next_article_brief_v6 import (
        build_feedback_backlog_next_article_brief_packet,
    )

    for candidate in value["candidates"]:
        packet = build_feedback_backlog_next_article_brief_packet(
            {
                "backlog_candidates": [candidate],
                "backlog_summary_packet_id": "native-feedback-" + sha256_of(value),
                "exact_payload_hash": sha256_of(value),
                "feedback_intake_packet_id": value["observation_id"],
                "feedback_intake_hash": value["observed_feedback_sha256"],
                "audit_index_packet_id": value["dispatch_id"],
                "audit_index_hash": sha256_of(value["public_object_url"]),
            }
        )
        _put(store, value["work_item_id"], BACKLOG, packet)


def freeze_learning(store, *, source_store, run_id, published_memory):
    key = "native-audience-snapshot-" + sha256_of(run_id)
    old = store.get_outbox_message(key)
    if old:
        return json.loads(old["payload"])
    work = "cc-opportunity-" + sha256_of(run_id)
    with store.get_read_only_connection() as conn:
        started = conn.execute(
            "SELECT 1 FROM outbox_messages WHERE work_item_id=? AND destination IN (?,?) LIMIT 1",
            (
                work,
                "internal:cc-report-editorial-stage",
                "internal:native-current-input",
            ),
        ).fetchone()
    # Legacy pending opportunities never gain a new field mid-request.
    if (
        started
        or store.get_outbox_message("native-current-input-" + sha256_of(run_id))
        or store.get_outbox_message("cc-editorial-pool-" + sha256_of(run_id))
        or any(
            store.get_outbox_message(
                "native-desktop-" + sha256_of([work, stage, "request"])
            )
            for stage in ("select", "write", "revise")
        )
    ):
        return None
    memory = [
        m.to_dict() if hasattr(m, "to_dict") else dict(m) for m in published_memory
    ]
    context = learning_context(source_store)
    context["follow_up_briefs"] = (context["follow_up_briefs"] + _rows(store, BACKLOG))[
        -8:
    ]
    value = {
        "schema_version": "contentops.native_audience_snapshot.v1",
        "run_id": run_id,
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        **context,
        "published_memory_sha256": sha256_of(memory),
        "published_memory": memory,
        "effective_scope": "THIS_NEW_OPPORTUNITY_ONLY",
    }
    value["snapshot_sha256"] = sha256_of(value)
    row = store.register_outbox_message(
        message_id=key,
        work_item_id=work,
        destination=SNAPSHOT,
        payload=canonical_bytes(value).decode(),
        status="EDITORIAL_INTERNAL",
    )
    return json.loads(row["payload"])


def compact_briefing(snapshot):
    if not snapshot:
        return None
    compact = {
        k: snapshot[k]
        for k in (
            "snapshot_sha256",
            "policy",
            "feedback",
            "follow_up_briefs",
            "published_memory_sha256",
            "effective_scope",
        )
    }
    compact["feedback"] = [
        {
            k: r.get(k)
            for k in (
                "observation_id",
                "collected_at_utc",
                "scheduled_for_utc",
                "semantic_state",
            )
        }
        | {
            "interaction_count": len(r.get("interactions", [])),
            "feedback_sha256": sha256_of(r),
        }
        for r in snapshot["feedback"][-8:]
    ]
    compact["follow_up_briefs"] = [
        {
            k: b[k]
            for k in ("run_id", "feedback_effect", "ranked_questions", "next_operation")
            if k in b
        }
        | (
            {"reader_question": b.get("brief_candidate", {}).get("editorial_angle")}
            if b.get("brief_candidate")
            else {}
        )
        for b in snapshot["follow_up_briefs"][-3:]
    ]
    return compact


class NativeAudienceObservation:
    """One exact due sample, same store/observation IDs and existing native tool protocol."""

    def __init__(self, store, *, output_dir, invocation_id):
        self.store = store
        self.root = Path(output_dir)
        self.invocation_id = invocation_id

    def _request(self, observation_id):
        observation = self.store.get_performance_observation(observation_id)
        if not observation:
            raise ValueError("EXACT_SCHEDULED_OBSERVATION_REQUIRED")
        dispatch, message = eligible_dispatch(self.store, observation["dispatch_id"])
        if (
            dispatch["public_object_id"] != observation["public_object_id"]
            or message["work_item_id"] != observation["work_item_id"]
        ):
            raise ValueError("OBSERVATION_PUBLICATION_LINEAGE_MISMATCH")
        if datetime.fromisoformat(
            observation["scheduled_for_utc"].replace("Z", "+00:00")
        ) > datetime.now(timezone.utc):
            raise ValueError("OBSERVATION_NOT_DUE")
        request = {
            "action": "OBSERVE_PUBLIC_FEEDBACK",
            "destination": dispatch["platform"],
            "surface": "CONTENTOPS_PUBLIC_PERFORMANCE_READ_ONLY",
            "work_item_id": message["work_item_id"],
            "dispatch_attempt_identity": dispatch["dispatch_id"],
            "observation_id": observation_id,
            "public_object_id": dispatch["public_object_id"],
            "public_object_url": dispatch.get("public_object_url"),
            "expected_identity": dispatch["platform"],
            "scheduled_for_utc": observation["scheduled_for_utc"],
            "observation_window": observation["observation_window"],
            "max_objects": 1,
            "max_public_interactions": 20,
            "instructions": "READ ONLY exact object. Verify object/account identity. Read visible native metrics and up to 20 public reader questions; omit names/handles. Missing metrics null with capability state. Current late observation is not the scheduled historical checkpoint. No post, reply, draft, login, account switch, session inspection or token work.",
            "public_write_authorized": False,
        }
        request["request_sha256"] = sha256_of(request)
        executor = NativeNeoExecutor(
            self.store,
            operation_id="audience-" + observation_id,
            output_dir=self.root / observation_id,
            native_invocation_id=self.invocation_id,
            allow_publish=False,
        )
        return observation, request, executor

    def tool(self, command, *, observation_id, request_hash, response=None):
        _, request, executor = self._request(observation_id)
        if request_hash != request["request_sha256"]:
            raise ValueError("EXACT_OBSERVATION_REQUEST_REQUIRED")
        if command == "begin":
            return executor.begin(request_hash)
        result = response["result"]
        if (
            result.get("public_object_id") != request["public_object_id"]
            or result.get("public_object_url") != request["public_object_url"]
        ):
            raise ValueError("OBSERVATION_WRONG_PUBLIC_OBJECT")
        from live_contentops.feedback_snapshot_redaction_v6 import redact_text

        interactions = []
        for row in list(result.get("interactions") or [])[:20]:
            text, blockers = redact_text(str(row.get("text", ""))[:2000])
            if not blockers and text:
                interactions.append(
                    {
                        "interaction_id": sha256_of(
                            [
                                request["public_object_id"],
                                row.get("interaction_id"),
                                text,
                            ]
                        ),
                        "text": text,
                    }
                )
        metrics, availability = {}, dict(result.get("availability") or {})
        for name, value in (result.get("metrics") or {}).items():
            if availability.get(name) != perf.AVAILABLE:
                metrics[name] = None
            elif (
                isinstance(value, (float, int))
                and not isinstance(value, bool)
                and math.isfinite(value)
                and value >= 0
            ):
                metrics[name] = value
            else:
                raise ValueError("OBSERVED_METRIC_VALUE_INVALID")
        for name, state in availability.items():
            if state != perf.AVAILABLE:
                metrics[name] = None
        safe = {
            **response,
            "result": {
                k: result[k]
                for k in (
                    "request_sha256",
                    "public_object_id",
                    "public_object_url",
                    "identity_verified",
                    "status",
                    "source_identity",
                )
                if k in result
            },
        }
        safe["result"].update(
            metrics=metrics, availability=availability, interactions=interactions
        )
        if result.get("identity_verified") is not True:
            safe["result"].update(
                status="IDENTITY_NOT_VERIFIED",
                metrics={},
                interactions=[],
                availability={k: "UNAVAILABLE" for k in availability},
            )
        return executor.submit(request_hash, safe)

    def advance(self, observation_id):
        observation, request, executor = self._request(observation_id)
        if observation["collection_status"] != "SCHEDULED":
            # Recover a crash between deterministic collection and feedback persistence.
            # A historical non-native observation must never open a new browser request.
            sealed = executor._get(request["request_sha256"], "response")
            if sealed and observation["collection_status"] == "COLLECTED":
                self._feedback(observation, request, sealed["result"])
            return {
                "state": "OBSERVATION_ALREADY_RECORDED",
                "observation": observation,
                "metrics_model_calls": 0,
            }
        try:
            result = executor(request)
        except NativeNeoInputRequired as pending:
            return {
                "state": "NATIVE_OBSERVATION_PENDING",
                "request": pending.request,
                "metrics_model_calls": 0,
            }
        collected = perf.collect_observation(
            self.store,
            observation_id=observation_id,
            collector=lambda *args: {**result, "interactions": []},
            now=datetime.now(timezone.utc),
        )
        value = (
            self._feedback(collected, request, result)
            if collected["collection_status"] == "COLLECTED"
            else None
        )
        return {
            "state": "OBSERVATION_RECORDED",
            "observation": collected,
            "feedback": value,
            "metrics_model_calls": 0,
        }

    def _feedback(self, collected, request, result):
        value = {
            "observation_id": collected["observation_id"],
            "dispatch_id": request["dispatch_attempt_identity"],
            "work_item_id": request["work_item_id"],
            "public_object_url": request["public_object_url"],
            "collected_at_utc": collected["collected_at_utc"],
            "scheduled_for_utc": request["scheduled_for_utc"],
            "interactions": result.get("interactions", []),
            "semantic_state": "UNCLASSIFIED"
            if result.get("interactions")
            else "NO_OBSERVED_PUBLIC_QUESTIONS",
            "metric_truth_separate_from_semantic_judgment": True,
            "public_reply_authority": False,
        }
        _put(self.store, request["work_item_id"], FEEDBACK, value)
        return value


def retain_selection_follow_up(store, *, run_id, response):
    """Bind an ABSTAIN follow-up to its actual frozen selection, same backlog/outbox."""
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn
    from live_contentops.feedback_to_article_backlog_refiner_v6 import (
        refine_backlog_candidates,
    )
    from live_contentops.feedback_backlog_next_article_brief_v6 import (
        build_feedback_backlog_next_article_brief_packet,
    )

    turn = NativeDesktopTurn(
        store, run_id=run_id, output_dir=".", owner_manual_validation=True
    )
    request, selection = turn._get("select", "request"), turn._get("select", "response")
    if not request or not selection or selection["output"].get("status") != "ABSTAIN":
        raise ValueError("EXACT_ACCEPTED_ABSTAIN_SELECTION_REQUIRED")
    if (
        response.get("native_invocation_id")
        != selection["invocation_observation"]["invocation_id"]
    ):
        raise ValueError("SAME_NATIVE_SELECTOR_REQUIRED")
    questions = response.get("ranked_questions", [])
    if not 1 <= len(questions) <= 3 or [q["rank"] for q in questions] != list(
        range(1, len(questions) + 1)
    ):
        raise ValueError("BOUNDED_RANKED_FOLLOW_UP_REQUIRED")
    candidate_ids = {c["candidate_id"] for c in request["governed_input"]["candidates"]}
    retained = {}
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
        SIMPLE_RESULT,
    )

    for result in _rows(store, SIMPLE_RESULT):
        if result.get("article_identity"):
            retained[result["article_identity"]] = result
    candidates = []
    for question in questions:
        match = question["exact_article_match"]
        result = retained.get(match["article_identity"], {})
        if (
            not set(question["candidate_ids"]).issubset(candidate_ids)
            or not question["candidate_ids"]
            or result.get("simple_result", {}).get("run_id") != match["run_id"]
            or not question.get("missing_evidence")
            or not question.get("source_item_ids")
        ):
            raise ValueError("EXACT_RETAINED_ARTICLE_AND_CANDIDATE_REQUIRED")
        candidates.append(
            {
                "candidate_id": "native-follow-up-" + sha256_of([run_id, question]),
                "title": question["question"],
                "article_angle": question["question"],
                "rationale": response["feedback_effect"],
                "priority_score": 4 - question["rank"],
                "source_feedback_item_ids": [],
                "source_platforms": [],
                "topic_tags": [],
                "allowed_for_drafting": True,
                "blocked_reasons": [],
                **question,
            }
        )
    candidates = refine_backlog_candidates(candidates)
    packet = build_feedback_backlog_next_article_brief_packet(
        {
            "backlog_candidates": candidates,
            "backlog_summary_packet_id": "native-selection-"
            + request["request_sha256"],
            "exact_payload_hash": sha256_of(candidates),
            "feedback_intake_packet_id": "NO_INDEPENDENT_READER_QUESTION",
            "feedback_intake_hash": sha256_of(response["feedback_effect"]),
            "audit_index_packet_id": selection["invocation_observation"][
                "invocation_id"
            ],
            "audit_index_hash": sha256_of(selection),
        }
    )
    value = {
        "run_id": run_id,
        "selection_request_sha256": request["request_sha256"],
        "native_observation": selection["invocation_observation"],
        "feedback_effect": response["feedback_effect"],
        "ranked_questions": candidates,
        "brief_packet": packet,
        "audience_demand_inferred": False,
        "next_operation": "Compare the next named primary-source edition through refresh; reuse the exact article until material evidence changes.",
        "public_write_performed": False,
    }
    return _put(store, turn.work, BACKLOG, value)


def evaluate_native_learning(store, *, evaluation_id):
    perf.ensure_bootstrap_policy(store, now=datetime.now(timezone.utc))
    return perf.evaluate_learning_decision(
        store,
        evaluation_window="native-owner:" + evaluation_id,
        now=datetime.now(timezone.utc),
    )


def learning_projection(rows):
    snapshots = [json.loads(r["payload"]) for r in rows if r["destination"] == SNAPSHOT]
    return {
        "opportunities": [
            {
                "run_id": s["run_id"],
                "snapshot_sha256": s["snapshot_sha256"],
                "policy": s["policy"],
                "feedback_count": len(s["feedback"]),
                "follow_up_briefs": s["follow_up_briefs"],
                "next_operation": "Resume the same native request; newer policy applies to the next opportunity.",
            }
            for s in snapshots[-8:]
        ],
        "follow_up_briefs": [
            json.loads(r["payload"]) for r in rows if r["destination"] == BACKLOG
        ][-8:],
    }
