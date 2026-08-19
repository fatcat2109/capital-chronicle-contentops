from __future__ import annotations

from datetime import datetime, timezone

from live_contentops.grounded_news_research_v1 import (
    GroundedNewsResearchV1,
    _source_ref,
)


CUTOFF = "2026-08-17T17:03:28.055185Z"


def _document(
    document_id: str,
    title: str,
    published_at_utc: str,
    publisher: str,
) -> dict:
    return {
        "document_id": document_id,
        "title": title,
        "publisher": publisher,
        "source_identity": publisher.casefold().replace(" ", "") + ".example",
        "source_authority_class": "reputable_secondary_source",
        "source_url": f"https://{publisher.casefold().replace(' ', '')}.example/{document_id}",
        "published_at_utc": published_at_utc,
        "event_time_utc": published_at_utc,
        "canonical_content_text": title,
        "canonical_content_sha256": (document_id * 64)[:64],
        "public_claim_allowed": True,
        "secondary_listing_only": True,
    }


def _request(*, enhanced: bool = True) -> dict:
    return {
        "cluster_id": "kushner-state-regression",
        "headline_ids": ["headline-kushner"],
        "story_type": "geopolitical_event" if enhanced else "company_sector_event",
        "article_mode": "breaking",
        "requested_article_mode": "BREAKING_BRIEF",
        "effective_article_mode": "BREAKING_BRIEF",
        "needed_evidence": ["Confirm the latest state of the Netanyahu talks."],
        "story_context": {
            "leaf_summaries": ["Kushner met Hamas in Cairo over Gaza."],
            "entities_topics": ["Jared Kushner", "Benjamin Netanyahu", "Gaza"],
        },
    }


def _research(
    *,
    initial_documents: list[dict],
    closure_documents: list[dict],
    enhanced: bool = True,
    synthesis_statement: str | None = None,
) -> tuple[dict, list[dict], list[str]]:
    retrievals: list[dict] = []
    phases: list[str] = []

    def retriever(request: dict) -> dict:
        retrievals.append(request)
        closure = (
            (request.get("evidence_enrichment_context") or {}).get("reason")
            == "LATEST_EVENT_STATE_CLOSURE"
        )
        documents = closure_documents if closure else initial_documents
        return {
            "status": "PASS" if documents else "BLOCKED",
            "evidence_documents": documents,
            "provenance": {
                "request_count_for_candidate": len(
                    (request.get("story_context") or {}).get(
                        "grounded_research_queries"
                    )
                    or []
                ),
                "retrieved_at_utc": CUTOFF,
            },
            "blockers": [] if documents else ["public_source_unavailable"],
        }

    def model_call(phase: str, _prompt: str) -> dict:
        phases.append(phase)
        if phase == "query_plan":
            return {
                "queries": [
                    "Kushner Hamas Cairo Gaza",
                    "Kushner Netanyahu Gaza talks",
                    "Netanyahu Gaza talks outcome",
                ],
                "verification_questions": [],
                "preferred_source_classes": ["reputable_professional_reporting"],
            }
        documents = [*initial_documents, *closure_documents]
        current = [
            row
            for row in documents
            if "Netanyahu" in row["title"]
            and "ahead of" not in row["title"]
            and "scheduled" not in row["title"]
            and "set to" not in row["title"]
            and datetime.fromisoformat(
                row["published_at_utc"].replace("Z", "+00:00")
            )
            <= datetime.fromisoformat(CUTOFF.replace("Z", "+00:00"))
        ]
        chosen = current[-1] if current else documents[-1]
        statement = synthesis_statement or chosen["title"]
        return {
            "core_factual_proposition": statement,
            "confirmed_facts": [
                {
                    "fact_id": "fact-latest-state",
                    "factual_statement": statement,
                    "source_refs": [
                        _source_ref(row) for row in (current or [chosen])
                    ],
                    "confidence_class": "CONFIRMED",
                    "direct_or_inferred": "DIRECT",
                }
            ],
            "attributed_numeric_facts": [],
            "context": [],
            "uncertainties": [],
            "contradictions": [],
            "unsupported_or_unverified": [],
            "suggested_article_mode": "BREAKING_BRIEF",
        }

    result = GroundedNewsResearchV1(
        evaluation_as_of_utc=CUTOFF,
        public_retriever=retriever,
        structured_model_call=model_call,
        max_queries=3,
    )(_request(enhanced=enhanced))
    return result, retrievals, phases


def test_frozen_kushner_regression_binds_newer_pre_cutoff_outcome_and_removes_future_state():
    initial = [
        _document(
            "old-completed-hamas",
            "Kushner met Hamas in Cairo over Gaza",
            "2026-08-17T10:00:00Z",
            "Al Jazeera",
        ),
        _document(
            "old-planned-netanyahu",
            "Kushner met Hamas ahead of planned talks with Netanyahu on Gaza",
            "2026-08-17T12:00:00Z",
            "The Guardian",
        ),
    ]
    closure = [
        _document(
            "stale-closure-forward",
            "Kushner remained scheduled for Netanyahu Gaza talks",
            "2026-08-17T15:00:00Z",
            "Financial Times",
        ),
        _document(
            "new-netanyahu-outcome",
            "Kushner and Netanyahu Gaza talks ended with no breakthrough",
            "2026-08-17T16:00:00Z",
            "Reuters",
        ),
        _document(
            "new-netanyahu-outcome-corroboration",
            "Kushner and Netanyahu Gaza talks ended without a breakthrough",
            "2026-08-17T16:10:00Z",
            "Associated Press",
        ),
        _document(
            "post-cutoff-no-authority",
            "Kushner and Netanyahu set to hold new Gaza talks",
            "2026-08-17T17:30:00Z",
            "BBC",
        ),
    ]

    result, retrievals, phases = _research(
        initial_documents=initial,
        closure_documents=closure,
        enhanced=True,
    )

    assert result["status"] == "PASS", result["blockers"]
    state = result["latest_event_state_closure"]
    assert state["status"] == "PASS"
    assert state["enhanced_breaking_zero_substantive_body"] is True
    assert state["latest_supported_state"] == "OCCURRED_OR_OUTCOME_REPORTED"
    assert state["supporting_document_ids"] == [
        "new-netanyahu-outcome-corroboration"
    ]
    assert state["superseded_document_ids"] == [
        "old-planned-netanyahu",
        "stale-closure-forward",
    ]
    assert state["post_cutoff_document_ids_rejected"] == [
        "post-cutoff-no-authority"
    ]
    document_ids = {row["document_id"] for row in result["evidence_documents"]}
    assert "old-planned-netanyahu" not in document_ids
    assert "stale-closure-forward" not in document_ids
    assert "post-cutoff-no-authority" not in document_ids
    assert "new-netanyahu-outcome" in document_ids
    governed_text = str(result["research_packet"])
    for stale in (
        "ahead of Netanyahu talks",
        "scheduled to meet Netanyahu afterward",
        "planned Netanyahu talks",
        "watch for statements after the planned talks",
    ):
        assert stale.casefold() not in governed_text.casefold()
    assert len(retrievals) == 2
    assert state["query_budget"] == {
        "maximum_queries": 3,
        "initial_queries_used": 2,
        "closure_queries_used": 1,
    }
    assert phases == ["query_plan", "source_synthesis"]


def test_enhanced_breaking_title_only_forward_state_fails_before_synthesis_when_unresolved():
    initial = [
        _document(
            "old-planned-netanyahu",
            "Kushner met Hamas ahead of planned talks with Netanyahu on Gaza",
            "2026-08-17T12:00:00Z",
            "The Guardian",
        )
    ]
    result, retrievals, phases = _research(
        initial_documents=initial,
        closure_documents=[],
        enhanced=True,
        synthesis_statement="The Netanyahu meeting occurred.",
    )

    assert result["status"] == "BLOCKED"
    assert result["blockers"] == ["latest_event_state_unresolved"]
    assert result["latest_event_state_closure"]["status"] == "BLOCKED"
    assert phases == ["query_plan"]
    assert len(retrievals) == 2


def test_completed_event_uses_no_latest_state_retrieval():
    completed = _document(
        "completed-event",
        "The central bank published its policy decision and held rates unchanged",
        "2026-08-17T15:00:00Z",
        "Reuters",
    )
    result, retrievals, phases = _research(
        initial_documents=[completed],
        closure_documents=[],
        enhanced=False,
    )

    assert result["status"] == "PASS"
    assert result["latest_event_state_closure"]["status"] == "NOT_REQUIRED"
    assert len(retrievals) == 1
    assert phases == ["source_synthesis"]


def test_truly_future_state_requires_a_distinct_newer_source_to_remain_future():
    initial = [
        _document(
            "future-first",
            "Company set to meet regulators on the Atlas license",
            "2026-08-17T12:00:00Z",
            "Reuters",
        )
    ]
    closure = [
        _document(
            "future-confirmed",
            "Company meeting with regulators on the Atlas license remains scheduled",
            "2026-08-17T16:00:00Z",
            "Associated Press",
        )
    ]
    result, retrievals, _phases = _research(
        initial_documents=initial,
        closure_documents=closure,
        enhanced=False,
    )

    assert result["status"] == "PASS", result["blockers"]
    assert result["latest_event_state_closure"]["latest_supported_state"] == (
        "FUTURE_STATE_SUPPORTED"
    )
    assert len(retrievals) == 2


def test_older_completed_document_cannot_override_a_newer_forward_state():
    initial = [
        _document(
            "future-newer",
            "Company set to meet regulators on the Atlas license",
            "2026-08-17T15:00:00Z",
            "Reuters",
        )
    ]
    closure = [
        _document(
            "completed-older",
            "Company and regulators concluded Atlas license talks",
            "2026-08-17T14:00:00Z",
            "Associated Press",
        )
    ]
    result, _retrievals, phases = _research(
        initial_documents=initial,
        closure_documents=closure,
        enhanced=False,
        synthesis_statement="The talks concluded.",
    )

    assert result["status"] == "BLOCKED"
    assert result["blockers"] == ["latest_event_state_unresolved"]
    assert phases == []
