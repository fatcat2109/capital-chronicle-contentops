"""Deterministic preselection intelligence inside the canonical rolling-X newsroom.

This seam performs two cheap, authority-free operations before expensive story work:

* it compacts a very large rolling intake to a fresh, evidence-reachable assignment universe;
* it enriches/reranks/holds the compact global-editor shortlist before targeted evidence.

Both operations perform zero model/provider calls and grant no factual authority.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

from live_contentops.capital_chronicle_data_catalog_v1 import (
    derive_story_scoped_cc_semantics,
    inspect_governed_cc_surfaces,
    query_story_scoped_cc_context,
)
from live_contentops.editorial_portfolio_v1 import (
    DECISION_BREAKING_NEW_STORY,
    DECISION_DEEPEN_EXISTING_STORY,
    DECISION_HOLD,
    DECISION_LOW_DELTA_REPEAT,
    DECISION_MATERIAL_FOLLOW_UP,
    DECISION_QUIET_DAY_USEFUL,
    PublishedArticleRef,
    build_material_follow_up_context,
    classify_story_novelty,
    concentration_penalty,
    portfolio_state_today,
    select_growth_editorial_mode,
)

SCHEMA_VERSION = "contentops.preselection_intelligence.v1"
ASSIGNMENT_COMPACTION_SCHEMA_VERSION = "contentops.rolling_x_assignment_compaction.v1"
# Live telemetry proved that 128 headlines can consume nearly the entire 250k hard cycle cap
# before the quality-first writer/reviewer run.  Sixty-four preserves a broad ranked universe
# while leaving circuit-breaker headroom for the final editorial stages.
DEFAULT_MAX_ASSIGNMENT_HEADLINES = 64

_DECISION_BONUS = {
    DECISION_BREAKING_NEW_STORY: 12.0,
    DECISION_MATERIAL_FOLLOW_UP: 11.0,
    DECISION_DEEPEN_EXISTING_STORY: 7.0,
    DECISION_QUIET_DAY_USEFUL: 4.0,
    DECISION_LOW_DELTA_REPEAT: -1000.0,
    DECISION_HOLD: -1000.0,
}

_CAPABILITY_MODE = {
    "BREAKING_BRIEF": "straight_news",
    "FOLLOW_UP_UPDATE": "straight_news",
    "CAPITAL_CHRONICLE_DEEP_DIVE": "deep_analysis",
    "STANDARD_NEWS_ANALYSIS": "analysis",
    "CAPITAL_CHRONICLE_VIEW": "analysis",
    "WHAT_THE_MARKET_IS_MISSING": "analysis",
    "EVERGREEN_EXPLAINER": "explainer",
    "DATA_OR_DOCUMENT_LENS": "analysis",
    "WEEK_AHEAD_OR_WATCH": "analysis",
}

_KNOWN_OFFICIAL_SUFFIXES = (
    ".gov", ".gov.au", ".gov.uk", ".europa.eu", ".int",
)

_OBSERVED_ACCESS_FAILURE_KEYS = frozenset(
    {
        "http_401_count",
        "http_403_count",
        "http_404_count",
        "paywall_count",
        "waf_count",
        "dead_link_count",
        "access_failure_count",
    }
)

_KNOWN_ACCESS_RISK_HOSTS = frozenset(
    {
        "bloomberg.com",
        "ft.com",
        "nytimes.com",
        "reuters.com",
        "wsj.com",
        "www.bloomberg.com",
        "www.ft.com",
        "www.nytimes.com",
        "www.reuters.com",
        "www.wsj.com",
    }
)


def _evidence_reachability(
    cluster: Mapping[str, Any],
    cc_context: Mapping[str, Any],
    *,
    sourceability_observations: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Rank expected acquisition feasibility without granting evidence authority.

    Every input is either an already-registered locator/capability or an observed transport
    outcome.  The score may change work order; only the governed loaders can turn retrieved
    bytes into an accepted evidence document.
    """
    from live_contentops.official_primary_evidence_loader_v1 import (
        OFFICIAL_HOSTS_BY_FAMILY,
    )
    from live_contentops.official_primary_source_locator_v1 import (
        routed_official_locator_families,
    )
    from live_contentops.public_secondary_evidence_loader_v1 import REPUTABLE_SECONDARY_HOSTS
    from live_contentops.source_capability_registry_v2 import (
        effective_rolling_x_capability_registry,
        resolve_story_capabilities,
    )

    urls = list(
        dict.fromkeys(
            str(value)
            for value in (
                list(cluster.get("public_source_urls") or [])
                + list(cluster.get("official_source_urls") or [])
                + [
                    row.get("url")
                    for row in (
                        list(cluster.get("public_source_url_bindings") or [])
                        + list(cluster.get("official_source_url_bindings") or [])
                    )
                    if isinstance(row, Mapping)
                ]
            )
            if str(value).startswith("https://")
        )
    )
    hosts = {str(urlsplit(value).hostname or "").casefold() for value in urls}
    registered_official_families = sorted(
        family
        for family, family_hosts in OFFICIAL_HOSTS_BY_FAMILY.items()
        if hosts.intersection(family_hosts)
    )
    routed_locator_families = sorted(
        set(routed_official_locator_families({"story_context": dict(cluster)}))
    )
    official = bool(registered_official_families or routed_locator_families)
    official_suffix_candidate = any(host.endswith(_KNOWN_OFFICIAL_SUFFIXES) for host in hosts)
    reputable_secondary = any(host in REPUTABLE_SECONDARY_HOSTS for host in hosts)
    cc_relevant = float(cc_context.get("cc_context_richness") or 0.0) >= 0.35
    cc_authority = cluster.get("capital_chronicle_publication_authority")
    cc_authority = cc_authority if isinstance(cc_authority, Mapping) else {}
    exact_cc_packet = bool(
        cc_authority.get("authorized") is True
        and cc_authority.get("state") == "PUBLICATION_PACKET_AVAILABLE"
        and cc_authority.get("packet_sha256")
        and cc_authority.get("exact_story_consumer_use_binding_verified") is True
    )

    capability = resolve_story_capabilities(
        {
            "story_type": str(cluster.get("story_type") or "general_public_event"),
            "article_mode": str(cluster.get("capability_article_mode") or "straight_news"),
            "product_article_mode": str(
                cluster.get("resolved_article_mode")
                or cluster.get("effective_article_mode")
                or "BREAKING_BRIEF"
            ),
        },
        effective_rolling_x_capability_registry(),
    )
    expected_families = {
        str(value) for value in capability.get("source_adapter_families") or []
    }
    available_families = set(registered_official_families).union(
        routed_locator_families
    )
    if reputable_secondary:
        available_families.add("public_secondary")
    if exact_cc_packet:
        available_families.update(
            {"capital_chronicle_market_state", "capital_chronicle_database"}
        )
    bounded_discovery = bool(
        "public_secondary" in expected_families or not available_families
    )
    if bounded_discovery:
        available_families.add("public_secondary")
    family_coverage = (
        len(expected_families.intersection(available_families)) / len(expected_families)
        if expected_families
        else 0.0
    )

    observations = sourceability_observations or {}
    observed_hosts = observations.get("hosts")
    observed_hosts = observed_hosts if isinstance(observed_hosts, Mapping) else {}
    successful_retrievals = 0
    access_failures = 0
    for host in hosts:
        observation = observed_hosts.get(host)
        if not isinstance(observation, Mapping):
            observation = observed_hosts.get(host.removeprefix("www."))
        if not isinstance(observation, Mapping):
            continue
        successful_retrievals += int(
            observation.get("successful_retrieval_count") or 0
        )
        access_failures += sum(
            int(observation.get(key) or 0) for key in _OBSERVED_ACCESS_FAILURE_KEYS
        )
    repeated_access_failure = access_failures >= 2
    known_access_risk = bool(hosts.intersection(_KNOWN_ACCESS_RISK_HOSTS))
    expected_request_cost = (
        0
        if exact_cc_packet
        else 1
        if registered_official_families or reputable_secondary
        else 2
        if routed_locator_families
        else 3
    ) + min(2, access_failures)
    raw_score = (
        (0.38 if registered_official_families else 0.0)
        + (0.28 if routed_locator_families else 0.0)
        + (0.44 if exact_cc_packet else 0.0)
        + (0.28 if reputable_secondary else 0.0)
        + (0.2 if successful_retrievals else 0.0)
        + (0.18 * family_coverage)
        + (0.08 if bounded_discovery else 0.0)
        + (0.06 if urls else 0.0)
        + (0.05 if cc_relevant else 0.0)
        - (0.2 if repeated_access_failure else 0.0)
        - (0.08 if known_access_risk and not successful_retrievals else 0.0)
        - (0.025 * expected_request_cost)
    )
    score = max(0.0, min(1.0, raw_score))
    return {
        "score": round(score, 4),
        "known_official_path": official,
        "registered_official_locator_families": registered_official_families,
        "context_routed_official_locator_families": routed_locator_families,
        "unregistered_official_suffix_candidate": official_suffix_candidate and not official,
        "reputable_public_secondary_path": reputable_secondary,
        "capital_chronicle_relevant_context": cc_relevant,
        "exact_matching_cc_publication_authorized_packet": exact_cc_packet,
        "public_source_candidate_count": len(urls),
        "expected_evidence_capabilities": list(
            capability.get("required_evidence_capabilities") or []
        ),
        "expected_adapter_families": sorted(expected_families),
        "available_adapter_families": sorted(available_families),
        "adapter_family_coverage": round(family_coverage, 4),
        "bounded_discovery_recovery_available": bounded_discovery,
        "observed_same_day_host_success_count": successful_retrievals,
        "observed_access_failure_count": access_failures,
        "observed_repeated_access_failure": repeated_access_failure,
        "known_paywall_waf_or_dead_link_risk": known_access_risk,
        "expected_request_cost": expected_request_cost,
        "mode_downgrade_viable": True,
        "ranking_only": True,
        "factual_authority_granted": False,
        "numeric_authority_granted": False,
        "capital_chronicle_authority_granted": False,
        "publication_authority_granted": False,
    }


def _preselection_cc_publication_authority(
    cluster: Mapping[str, Any],
    *,
    cc_catalog: Mapping[str, Any],
    evaluation_as_of: datetime,
    article_mode: str,
) -> dict[str, Any]:
    """Resolve only an exact, current story-bound packet for sourceability ranking.

    The targeted evidence adapter repeats this resolution before accepting any evidence.  This
    earlier read-only check exists solely so a genuinely matching governed packet is visible to
    the cheap work-order score instead of being discovered after expensive acquisition begins.
    """
    from live_contentops.cc_evidence_bridge_v2 import build_evidence_packet_from_cc_root
    from live_contentops.cc_publication_authority_v1 import resolve_publication_authority
    from live_contentops.freshness_market_state_v2 import evaluate_freshness

    cc_root = str(cc_catalog.get("cc_root") or "").strip()
    story_binding = {
        "cluster_id": cluster.get("cluster_id"),
        "headline_ids": list(cluster.get("headline_ids") or []),
        "request_logical_hash": cluster.get("request_logical_hash"),
    }
    unavailable = {
        "state": "PUBLICATION_PACKET_NOT_AVAILABLE",
        "authorized": False,
        "packet_id": None,
        "packet_sha256": None,
        "exact_story_consumer_use_binding_verified": False,
        "reason_codes": ["NO_PUBLICATION_AUTHORIZED_CC_PACKET_FOR_STORY"],
        "ordinary_latest_web_article_may_continue": True,
        "llm_numeric_authority": False,
    }
    if not cc_root:
        return unavailable
    try:
        packet = build_evidence_packet_from_cc_root(
            cc_root,
            as_of_utc=evaluation_as_of.isoformat().replace("+00:00", "Z"),
            story_binding=story_binding,
        )
        assignment = packet.get("publication_assignment") or {}
        freshness = evaluate_freshness(
            packet,
            {
                "article_mode": _CAPABILITY_MODE.get(article_mode, "analysis"),
                "market_sensitive": bool(assignment.get("market_sensitive")),
                "market_snapshot_required": bool(assignment.get("market_sensitive")),
                "fresh_material_delta": bool(assignment.get("fresh_material_delta")),
                "readiness_evaluation_basis": "CURRENT_OPERATOR_READINESS",
                "operator_evaluation_as_of_utc": evaluation_as_of.isoformat().replace(
                    "+00:00", "Z"
                ),
            },
        )
        resolution = resolve_publication_authority(
            packet,
            story_binding=story_binding,
            current_readiness_blockers=(
                list(freshness.get("blockers") or [])
                if freshness.get("decision") != "PASS"
                else []
            ),
        )
    except (FileNotFoundError, OSError, RuntimeError, TypeError, ValueError):
        return unavailable
    exact = bool(
        resolution.get("authorized") is True
        and resolution.get("state") == "PUBLICATION_PACKET_AVAILABLE"
    )
    return {
        **dict(resolution),
        "exact_story_consumer_use_binding_verified": exact,
        "preselection_ranking_only": True,
        "publication_authority_granted_at_preselection": False,
        "llm_numeric_authority": False,
    }


def _logical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _source_timestamp(row: Mapping[str, Any]) -> datetime:
    raw = str(row.get("source_timestamp_utc") or "")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _raw_assignment_reachability(row: Mapping[str, Any]) -> tuple[int, int]:
    """Return cheap locator signals only; never claim that a source supports a fact."""
    external = row.get("external_content")
    if not isinstance(external, Mapping):
        return 0, 0
    urls = [
        str(value)
        for value in (external.get("official_source_urls") or [])
        if str(value).startswith("https://")
    ]
    follow_up_locators = [
        str(value)
        for value in (external.get("follow_up_data_need_candidates") or [])
        if str(value).strip()
    ]
    return int(bool(urls)), int(bool(follow_up_locators))


def compact_rolling_x_assignment_universe(
    rolling_input: Mapping[str, Any],
    *,
    max_headlines: int = DEFAULT_MAX_ASSIGNMENT_HEADLINES,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bound semantic assignment cost while preserving the full intake as durable evidence.

    Selection is deterministic: known public locator signals rank first, then freshness and the
    stable headline identity. Held headlines remain in the original intake artifact and are
    represented here by counts and an identity hash. They may re-enter a later rolling window;
    this seam does not declare them false, duplicate, or permanently rejected.
    """
    if max_headlines < 1:
        raise ValueError("rolling_x_assignment_compaction_limit_invalid")
    headlines = rolling_input.get("headlines")
    if not isinstance(headlines, list) or not all(isinstance(row, Mapping) for row in headlines):
        raise ValueError("rolling_x_assignment_compaction_headlines_invalid")
    unique_ids = [str(value) for value in (rolling_input.get("unique_headline_ids") or [])]
    row_ids = [str(row.get("headline_id") or "") for row in headlines]
    if any(not value for value in row_ids) or len(row_ids) != len(set(row_ids)):
        raise ValueError("rolling_x_assignment_compaction_identity_invalid")
    if set(row_ids) != set(unique_ids):
        raise ValueError("rolling_x_assignment_compaction_coverage_invalid")

    ranked = sorted(
        (dict(row) for row in headlines),
        key=lambda row: (
            -_raw_assignment_reachability(row)[0],
            -_raw_assignment_reachability(row)[1],
            -_source_timestamp(row).timestamp(),
            str(row.get("headline_id") or ""),
        ),
    )
    selected = ranked[:max_headlines]
    selected_ids = [str(row["headline_id"]) for row in selected]
    held_ids = [str(row["headline_id"]) for row in ranked[max_headlines:]]
    counts = dict(rolling_input.get("counts") or {})
    counts["accepted_in_full_rolling_intake"] = len(headlines)
    counts["accepted"] = len(selected)

    compacted = {
        **dict(rolling_input),
        "headlines": selected,
        "unique_headline_ids": selected_ids,
        "counts": counts,
        "complete_input_coverage": True,
        "assignment_compaction_applied": len(held_ids) > 0,
        "full_rolling_input_canonical_hash": rolling_input.get("canonical_input_hash"),
    }
    canonical_material = {
        "schema_version": compacted.get("schema_version"),
        "cutoff_time_utc": compacted.get("cutoff_time_utc"),
        "window_start_utc": compacted.get("window_start_utc"),
        "window_hours": compacted.get("window_hours"),
        "unique_headline_ids": compacted.get("unique_headline_ids"),
        "headlines": [
            {key: value for key, value in row.items() if key != "source_locator"}
            for row in selected
        ],
    }
    compacted["canonical_input_hash"] = _logical_hash(canonical_material)
    evidence = {
        "schema_version": ASSIGNMENT_COMPACTION_SCHEMA_VERSION,
        "full_rolling_headline_count": len(headlines),
        "assignment_headline_count": len(selected),
        "held_before_semantic_assignment_count": len(held_ids),
        "max_assignment_headlines": int(max_headlines),
        "full_rolling_input_canonical_hash": rolling_input.get("canonical_input_hash"),
        "assignment_input_canonical_hash": compacted["canonical_input_hash"],
        "selected_headline_ids_hash": _logical_hash(selected_ids),
        "held_headline_ids_hash": _logical_hash(held_ids),
        "selection_order": [
            "known_public_locator_signal",
            "follow_up_locator_signal",
            "source_timestamp_descending",
            "headline_id",
        ],
        "full_intake_artifact_preserved": True,
        "llm_or_provider_calls": 0,
        "factual_or_numeric_authority_granted": False,
        "publication_authority_granted": False,
    }
    evidence["compaction_logical_hash"] = _logical_hash(evidence)
    return compacted, evidence


def apply_preselection_intelligence(
    clusters: Sequence[Mapping[str, Any]],
    *,
    published_corpus: Sequence[PublishedArticleRef],
    cc_catalog: Mapping[str, Any],
    learning_policy: Mapping[str, Any] | None = None,
    material_event_priority: Mapping[str, Any] | None = None,
    sourceability_observations: Mapping[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Enrich and rerank the compact shortlist before any expensive story path."""
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    portfolio = portfolio_state_today(published_corpus, now=moment)
    evaluated: list[dict[str, Any]] = []
    original_order = [str(row.get("cluster_id") or "") for row in clusters]
    active_policy = dict(learning_policy or {})
    content_policy = dict(active_policy.get("content") or {})
    content_preferences = [
        dict(row) for row in (content_policy.get("recommendations") or [])
        if isinstance(row, Mapping)
    ][:3]
    seo_policy = dict(active_policy.get("seo") or {})
    material_priority = dict(material_event_priority or {})
    governed_surfaces = inspect_governed_cc_surfaces(cc_catalog)
    publication_surface = dict(
        (governed_surfaces.get("surfaces") or {}).get("publication_evidence_packet")
        or {}
    )
    priority_headline_ids = {
        str(value) for value in (material_priority.get("headline_ids") or []) if str(value)
    }
    priority_update_chains = {
        str(value)
        for value in (material_priority.get("update_chain_identities") or [])
        if str(value)
    }
    for cluster_value in clusters:
        cluster = dict(cluster_value)
        original_rank = int(cluster.get("rank") or 0)
        # ``cluster_id`` is already the canonical story identity on this route. Propagate it as
        # the update-chain identity instead of inventing an unrelated second identifier.
        update_chain_identity = str(
            cluster.get("update_chain_identity") or cluster.get("cluster_id") or ""
        )
        cluster["update_chain_identity"] = update_chain_identity
        semantic_activation = derive_story_scoped_cc_semantics(cluster)
        cc_context = query_story_scoped_cc_context(
            cc_catalog,
            [str(value) for value in semantic_activation.get("query_terms") or []],
        )
        cc_context = dict(cc_context)
        cc_context.setdefault("semantic_activation", semantic_activation)
        cc_context.setdefault("zero_context_reason", semantic_activation.get("zero_context_reason"))
        publication_discovery = {
            "state": (
                "PUBLICATION_PACKET_NOT_AVAILABLE"
                if publication_surface.get("state") == "MISSING"
                else "PUBLICATION_PACKET_PRESENT_BUT_NOT_AUTHORIZED"
            ),
            "authority_class": publication_surface.get("authority_class"),
            "packet_id": publication_surface.get("packet_id"),
            "packet_sha256": publication_surface.get("sha256"),
            "catalog_fingerprint": cc_catalog.get("catalog_fingerprint"),
            "reason_codes": [
                "NO_PUBLICATION_AUTHORIZED_CC_PACKET_FOR_STORY"
                if publication_surface.get("state") == "MISSING"
                else "EXACT_STORY_CONSUMER_USE_BINDING_PENDING_EVIDENCE_ADAPTER"
            ],
            "publication_authority_granted_at_preselection": False,
            "ordinary_latest_web_article_may_continue": True,
            "llm_numeric_authority": False,
        }
        novelty = classify_story_novelty(
            cluster,
            published_corpus=published_corpus,
            cc_context_richness=float(cc_context.get("cc_context_richness") or 0.0),
            now=moment,
        )
        decision = str(novelty["decision"])
        mode_resolution = select_growth_editorial_mode(cluster, novelty)
        if mode_resolution["quiet_day_utility_candidate"]:
            decision = DECISION_QUIET_DAY_USEFUL
        concentration = concentration_penalty(
            [str(value) for value in (cluster.get("entities_topics") or [])], portfolio
        )
        # Material follow-ups can overcome the soft concentration penalty; it remains visible.
        effective_concentration = (
            concentration * 0.25 if decision == DECISION_MATERIAL_FOLLOW_UP else concentration
        )
        # The expanded pool can contain dozens of candidates. Keep editorial rank as a useful
        # tiebreaker without allowing linear decay to make an exact-official path unreachable.
        base_score = 100.0 - min(max(1, original_rank) - 1, 8) * 2.0
        preselection_cc_authority = _preselection_cc_publication_authority(
            cluster,
            cc_catalog=cc_catalog,
            evaluation_as_of=moment,
            article_mode=str(mode_resolution["mode"]),
        )
        reachability = _evidence_reachability(
            {
                **cluster,
                "capital_chronicle_publication_authority": preselection_cc_authority,
                "resolved_article_mode": str(mode_resolution["mode"]),
                "capability_article_mode": _CAPABILITY_MODE.get(
                    str(mode_resolution["mode"])
                ),
            },
            cc_context,
            sourceability_observations=sourceability_observations,
        )
        score = (
            base_score
            + _DECISION_BONUS[decision]
            + 36.0 * float(cc_context.get("cc_context_richness") or 0.0)
            - 24.0 * effective_concentration
            + 28.0 * float(reachability["score"])
        )
        resolved_mode = str(mode_resolution["mode"])
        learning_bonus = 0.0
        learning_matches: list[dict[str, Any]] = []
        feature_values = {
            "article_mode": resolved_mode,
            "update_mode": decision,
            "topic_family": [str(value) for value in (cluster.get("entities_topics") or [])],
            "story_type": str(cluster.get("story_type") or ""),
        }
        for preference in content_preferences:
            feature = str(preference.get("feature") or "")
            preferred = str(preference.get("preferred_value") or "").casefold()
            candidate_value = feature_values.get(feature)
            if isinstance(candidate_value, list):
                matched = preferred in {
                    str(value).casefold() for value in candidate_value
                }
            else:
                matched = bool(preferred and str(candidate_value or "").casefold() == preferred)
            if matched:
                learning_bonus += 2.0
                learning_matches.append({
                    "feature": feature,
                    "preferred_value": preference.get("preferred_value"),
                    "support_count": preference.get("support_count"),
                })
        learning_bonus = min(6.0, learning_bonus)
        score += learning_bonus
        cluster_headline_ids = {
            str(value) for value in (cluster.get("headline_ids") or []) if str(value)
        }
        material_priority_match = bool(
            priority_headline_ids.intersection(cluster_headline_ids)
            or (update_chain_identity and update_chain_identity in priority_update_chains)
        )
        material_priority_bonus = 80.0 if material_priority_match else 0.0
        score += material_priority_bonus
        follow_up_context = build_material_follow_up_context(
            cluster, novelty, published_corpus
        )
        cluster.update({
            "preselection_original_rank": original_rank,
            "editorial_classification": decision,
            "resolved_article_mode": resolved_mode,
            "growth_editorial_mode_resolution": mode_resolution,
            "capability_article_mode": _CAPABILITY_MODE.get(resolved_mode),
            "capital_chronicle_context": cc_context,
            "capital_chronicle_semantic_activation": semantic_activation,
            "capital_chronicle_publication_authority_discovery": publication_discovery,
            "capital_chronicle_publication_authority": preselection_cc_authority,
            "portfolio_concentration_penalty": concentration,
            "portfolio_concentration_penalty_effective": round(effective_concentration, 4),
            "preselection_score": round(score, 4),
            "learning_priority_bonus": round(learning_bonus, 4),
            "learning_preference_matches": learning_matches,
            "learning_policy_version": active_policy.get("policy_version"),
            "learning_policy_sample_count": active_policy.get("sample_count", 0),
            "learning_policy_confidence": active_policy.get("confidence", 0.0),
            "material_event_priority_match": material_priority_match,
            "material_event_priority_bonus": material_priority_bonus,
            "material_event_priority_ids": list(
                material_priority.get("priority_ids") or []
            ) if material_priority_match else [],
            "material_event_priority_grants_factual_or_numeric_authority": False,
            "material_event_priority_changes_eligibility_gates": False,
            "seo_learning_preferences": list(seo_policy.get("recommendations") or [])[:3],
            "learning_preferences_grant_factual_or_numeric_authority": False,
            "learning_preferences_change_evidence_or_publication_gates": False,
            "evidence_reachability": reachability,
            "preselection_novelty": novelty,
            "material_follow_up_context": follow_up_context,
            "preselection_occurs_before_targeted_evidence": True,
            "preselection_occurs_before_article_generation": True,
            "x_and_cc_editorial_context_grant_factual_or_numeric_authority": False,
        })
        evaluated.append(cluster)

    eligible = [
        row for row in evaluated
        if row["editorial_classification"] not in {DECISION_LOW_DELTA_REPEAT, DECISION_HOLD}
    ]
    held = [
        row for row in evaluated
        if row["editorial_classification"] in {DECISION_LOW_DELTA_REPEAT, DECISION_HOLD}
    ]
    eligible.sort(key=lambda row: (
        -float(row["preselection_score"]),
        int(row["preselection_original_rank"]),
        str(row.get("cluster_id") or ""),
    ))
    for rank, row in enumerate(eligible, start=1):
        row["rank"] = rank
    result = {
        "schema_version": SCHEMA_VERSION,
        "evaluated_at_utc": moment.isoformat().replace("+00:00", "Z"),
        "input_shortlist_count": len(clusters),
        "eligible_shortlist_count": len(eligible),
        "held_shortlist_count": len(held),
        "original_order": original_order,
        "reranked_order": [str(row.get("cluster_id") or "") for row in eligible],
        "ranking_order_changed": original_order[:len(eligible)] != [
            str(row.get("cluster_id") or "") for row in eligible
        ],
        "ranked_clusters": eligible,
        "held_clusters": held,
        "portfolio_state": portfolio,
        "published_corpus_article_count": len(published_corpus),
        "cc_catalog_store_count": int(cc_catalog.get("store_count_discovered") or 0),
        "cc_catalog_complete": cc_catalog.get("discovery_complete") is True,
        "learning_policy_version": active_policy.get("policy_version"),
        "learning_policy_consumed": bool(active_policy),
        "learning_policy_priority_bonus_cap": 6.0,
        "learning_policy_grants_factual_or_numeric_authority": False,
        "material_event_priority_consumed": bool(material_priority),
        "material_event_priority_ids": list(material_priority.get("priority_ids") or []),
        "material_event_priority_bonus_cap": 80.0,
        "material_event_priority_changes_eligibility_gates": False,
        "sourceability_observations_consumed": bool(sourceability_observations),
        "sourceability_signals_grant_authority": False,
        "occurs_before_targeted_evidence": True,
        "occurs_before_article_generation": True,
        "llm_or_provider_calls": 0,
        "publication_authority_granted": False,
    }
    result["preselection_logical_hash"] = _logical_hash({
        key: value for key, value in result.items() if key != "preselection_logical_hash"
    })
    return result
