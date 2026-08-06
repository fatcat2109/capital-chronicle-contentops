"""Focused tests for the dual-lane CORE V0 shadow newsroom (SHADOW_ONLY)."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.dual_lane_core_v0_shadow_newsroom_v1 import (
    NO_AUTHORIZED_CHART_SERIES,
    OPERATING_MODE,
    REVIEW_BLOCKED_VISUAL,
    SUPPORTED_PLATFORM_IDS,
    TIER1_DESTINATIONS,
    DualLaneShadowError,
    assert_zero_live_action,
    build_package,
    review_package,
    run_capital_chronicle_lane,
    run_newsroom_lane,
    verify_durable_replay,
)
from live_contentops.dual_lane_core_v0_shadow_demo_runner_v1 import (
    DEFAULT_ANALYSIS_INPUT,
    DEFAULT_NEWS_INPUT,
    DEFAULT_SCHEDULE_DATE,
    DEFAULT_WINDOW,
    _newsroom_v3_packet,
    core_v0_shadow_demo_command,
    run_core_v0_shadow_demo,
)
from live_contentops.editorial_review_orchestrator_v2 import ROLE_ORDER
from live_contentops.multi_story_platform_native_operator_packages_v1 import (
    build_platform_native_variant,
)
from live_contentops.universal_news_candidate_fabric_v2 import validate_pool
from live_contentops.dual_lane_core_v0_shadow_newsroom_v1 import _persist_lane

ROOT = Path(__file__).resolve().parents[1]
NEWS_INPUT = ROOT / DEFAULT_NEWS_INPUT
ANALYSIS_INPUT = ROOT / DEFAULT_ANALYSIS_INPUT


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


@pytest.fixture(scope="module")
def pool():
    return _load(NEWS_INPUT)


@pytest.fixture(scope="module")
def packet():
    return _load(ANALYSIS_INPUT)["packets"][0]


def _news_packet():
    """The canonical V3 packet the newsroom lane reviews, via the same adapter."""
    pool = _load(NEWS_INPUT)
    candidate = next(row for row in pool["candidates"] if row["reporting_allowed"])
    return _newsroom_v3_packet(candidate)[0]


@pytest.fixture(scope="module")
def demo(tmp_path_factory):
    out = tmp_path_factory.mktemp("core_v0_demo")
    summary = run_core_v0_shadow_demo(
        news_input=NEWS_INPUT,
        analysis_input=ANALYSIS_INPUT,
        store_path=out / "store.sqlite",
        output_dir=out / "output",
    )
    return summary, out


# --- Governed inputs ------------------------------------------------------


def test_both_governed_inputs_are_committed_repo_artifacts():
    assert NEWS_INPUT.is_file(), "news lane must consume a committed governed artifact"
    assert ANALYSIS_INPUT.is_file(), "analysis lane must consume a committed governed artifact"


def test_newsroom_lane_covers_multiple_business_domains(pool):
    lane = run_newsroom_lane(pool=pool, schedule_date=DEFAULT_SCHEDULE_DATE, window=DEFAULT_WINDOW)
    assert len(lane["domains_covered"]) >= 4
    assert lane["candidate_count"] == len(pool["candidates"])


def test_newsroom_lane_rejects_invalid_pool(pool):
    broken = copy.deepcopy(pool)
    broken["logical_hash"] = "0" * 64
    with pytest.raises(DualLaneShadowError, match="governed_pool_invalid"):
        run_newsroom_lane(pool=broken, schedule_date=DEFAULT_SCHEDULE_DATE, window=DEFAULT_WINDOW)


# --- Clustering, ranking, selection ---------------------------------------


def test_clustering_and_update_chains_recorded(pool):
    lane = run_newsroom_lane(pool=pool, schedule_date=DEFAULT_SCHEDULE_DATE, window=DEFAULT_WINDOW)
    assert lane["cluster_count"] >= 1
    for cluster in lane["clusters"]:
        assert cluster["cluster_id"] and cluster["update_chain_id"]
        assert cluster["candidate_ids"]
        for relationship in cluster["relationships"]:
            assert relationship["relationship"]


def test_ranking_reasons_are_deterministic_and_explained(pool):
    first = run_newsroom_lane(pool=pool, schedule_date=DEFAULT_SCHEDULE_DATE, window=DEFAULT_WINDOW)
    second = run_newsroom_lane(pool=pool, schedule_date=DEFAULT_SCHEDULE_DATE, window=DEFAULT_WINDOW)
    assert first["ranking"] == second["ranking"]
    assert first["lane_logical_hash"] == second["lane_logical_hash"]
    for reasons in first["ranking"].values():
        assert reasons["calibration_state"]
        assert reasons["available_dimension_count"] + reasons["unavailable_dimension_count"] == 14


def test_eligible_candidate_is_selected_with_reason(pool):
    lane = run_newsroom_lane(pool=pool, schedule_date=DEFAULT_SCHEDULE_DATE, window=DEFAULT_WINDOW)
    assert lane["outcome"] == "SELECTED"
    assert lane["selected_candidate_id"]
    assert lane["selection_reason"]["why_selected"]
    assert lane["selection_reason"]["reporting_allowed"] is True
    assert lane["held_count"] == len(pool["candidates"]) - 1


def test_explicit_abstention_when_no_candidate_is_eligible(pool):
    """NO_PUBLICATION must remain a valid, explicit newsroom outcome.

    Uses the real governed duplicate-suppression path: the one eligible candidate's
    cluster is already assigned, so every remaining candidate is held.
    """
    eligible = next(row for row in pool["candidates"] if row["reporting_allowed"])
    lane = run_newsroom_lane(
        pool=pool,
        schedule_date=DEFAULT_SCHEDULE_DATE,
        window=DEFAULT_WINDOW,
        previously_assigned=[
            {
                "cluster_id": eligible["cluster_id"],
                "update_chain_id": eligible["update_chain_id"],
            }
        ],
    )
    assert lane["outcome"] == "ABSTAINED"
    assert lane["decision"] == "NO_ASSIGNMENT_ALL_CANDIDATES_HELD"
    assert lane["selected_candidate_id"] is None
    assert lane["selection_reason"]["abstention"] == "NO_PUBLICATION"
    assert lane["no_publication_valid"] is True
    assert lane["held_count"] >= 1


def test_abstention_produces_no_package_and_deferred_state(pool, tmp_path):
    """An abstaining newsroom lane must persist a terminal DEFERRED item, not a package."""
    news_package = None
    newsroom = run_newsroom_lane(
        pool=pool,
        schedule_date=DEFAULT_SCHEDULE_DATE,
        window=DEFAULT_WINDOW,
        previously_assigned=[
            {
                "cluster_id": row["cluster_id"],
                "update_chain_id": row["update_chain_id"],
            }
            for row in pool["candidates"]
            if row["reporting_allowed"]
        ],
    )
    assert newsroom["outcome"] == "ABSTAINED"

    store = ContentOpsDurableStore(tmp_path / "abstain.sqlite", auto_migrate=True)
    record = _persist_lane(
        store,
        lane="newsroom",
        story_id=str(newsroom["pool_id"]),
        title="CORE V0 newsroom lane abstention",
        source_payload={"pool_id": newsroom["pool_id"]},
        lane_payload=newsroom,
        package=news_package,
        review=None,
        outcome=str(newsroom["outcome"]),
    )
    assert record.terminal_state == "DEFERRED"
    replay = verify_durable_replay(store, [record.work_item_id])
    assert replay["all_replays_valid"] is True


# --- Capital Chronicle fidelity -------------------------------------------


def test_capital_chronicle_lane_preserves_analytical_substance(packet):
    lane = run_capital_chronicle_lane(packet=packet)
    fidelity = lane["analytical_fidelity"]
    assert fidelity["result"] == "PASS_PRESENTATION_ONLY_TRANSFORMATION"
    assert fidelity["recalculation_performed"] is False
    assert fidelity["reinterpretation_performed"] is False
    assert fidelity["widened_permission"] is False
    assert fidelity["numeric_truth_originated"] is False
    assert fidelity["packet_logical_hash"] == packet["logical_hash"]
    graph_claims = {row["claim_id"]: row for row in packet["governed_claim_graph"]["claims"]}
    for preserved in fidelity["preserved_claims"]:
        source = graph_claims[preserved["claim_id"]]
        assert preserved["claim_logical_hash"] == source["logical_hash"]
        assert preserved["numeric"] == source["numeric"]
        assert preserved["limitations"] == list(source["limitations"])


def test_capital_chronicle_lane_binds_lineage_and_permissions(packet):
    lane = run_capital_chronicle_lane(packet=packet)
    assert lane["packet_id"] == packet["packet_id"]
    assert lane["lineage"]["evidence_refs"]
    assert lane["lineage"]["candidate_logical_hash"]
    assert lane["authorized_claim_ids"] == list(packet["governed_claim_graph"]["approved_claim_ids"])
    assert lane["claim_permissions"]
    assert lane["citations"]


def test_no_authorized_chart_series_is_explicit_not_fabricated(packet):
    lane = run_capital_chronicle_lane(packet=packet)
    chart = lane["chart_series"]
    assert chart["status"] == NO_AUTHORIZED_CHART_SERIES
    assert chart["series"] == []
    assert chart["series_count"] == 0
    assert chart["reason"]


def test_capital_chronicle_lane_rejects_invalid_packet(packet):
    broken = copy.deepcopy(packet)
    broken["logical_hash"] = "0" * 64
    with pytest.raises(DualLaneShadowError, match="governed_packet_invalid"):
        run_capital_chronicle_lane(packet=broken)


# --- Package + SEO --------------------------------------------------------


def test_package_contains_required_seo_and_platform_fields(demo):
    _, out = demo
    lane = json.loads((out / "output" / "newsroom_lane.json").read_text(encoding="utf-8"))
    package = lane["package"]

    article = package["article"]
    for field in ("headline", "answer_first_summary", "body", "claim_ids_used",
                  "citations", "known_unknowns", "limitations"):
        assert article[field], f"missing article field {field}"

    seo = package["seo"]
    for field in ("primary_search_intent", "secondary_search_intent", "seo_title", "slug",
                  "meta_description", "h1", "h2_structure", "internal_link_suggestions",
                  "social_preview"):
        assert seo[field], f"missing seo field {field}"

    visual = package["visual"]
    assert visual["strategy"]
    assert visual["image_absent_reason"]

    platform = package["platform"]
    assert platform["tier1_destination_count"] == len(TIER1_DESTINATIONS)
    assert platform["supported_count"] == len(SUPPORTED_PLATFORM_IDS)
    assert {row["platform_id"] for row in platform["payloads"]} == set(SUPPORTED_PLATFORM_IDS)
    for payload in platform["payloads"]:
        assert payload["payload_hash"]
        assert payload["character_count"] <= payload["character_limit_max"]


def test_supported_payloads_use_the_canonical_package_fabric(demo):
    """CORE V0 must not carry a second platform-package implementation."""
    _, out = demo
    for filename in ("newsroom_lane.json", "capital_chronicle_lane.json"):
        platform = json.loads(
            (out / "output" / filename).read_text(encoding="utf-8")
        )["package"]["platform"]
        assert platform["package_fabric"] == (
            "multi_story_platform_native_operator_packages_v1.build_platform_native_variant"
        )
        for payload in platform["payloads"]:
            assert payload["schema_version"] == "contentops.platform_native_operator_variant.v1"


def test_platform_payloads_are_genuinely_platform_native(demo):
    """Each supported destination gets its own shape and copy treatment."""
    _, out = demo
    for filename in ("newsroom_lane.json", "capital_chronicle_lane.json"):
        platform = json.loads(
            (out / "output" / filename).read_text(encoding="utf-8")
        )["package"]["platform"]
        texts = [row["text"] for row in platform["payloads"]]
        shapes = [row["payload_shape"] for row in platform["payloads"]]
        surfaces = [row["content_surface"] for row in platform["payloads"]]
        hashes = [row["payload_hash"] for row in platform["payloads"]]

        assert len(set(texts)) == len(texts), "platform copy must not be identical"
        assert platform["distinct_payload_text_count"] == len(SUPPORTED_PLATFORM_IDS)
        assert len(set(shapes)) == len(shapes), "payload shapes must differ per contract"
        assert len(set(surfaces)) == len(surfaces)
        assert len(set(hashes)) == len(hashes)
        # Truncation alone would leave a shared prefix; genuine platform copy does not.
        assert len({text[:40] for text in texts}) > 1


def test_canonical_variant_builder_is_shared_with_pinned_story_path():
    """The pinned three-story replay path and CORE V0 use one implementation."""
    variant = build_platform_native_variant(
        platform_id="telegram",
        subject_id="subject-1",
        candidate_id="cand-1",
        authority_logical_hash="a" * 64,
        authorized_claim_ids=["claim-1"],
        headline="Official record headline",
        summary="Official record summary.",
        source_label="Example Agency",
        citation_urls=["https://example.test/doc"],
        limitations=["limitation"],
    )
    assert variant["schema_version"] == "contentops.platform_native_operator_variant.v1"
    assert variant["payload_hash"]
    assert variant["valid_for_dispatch"] is False
    assert variant["public_ready"] is False
    # Raw URLs must never reach the hashed inputs.
    assert "https://" not in json.dumps(
        {key: value for key, value in variant.items() if key != "citation_urls"}
    )


def test_unsupported_tier1_destinations_are_reported_not_omitted(demo):
    _, out = demo
    lane = json.loads((out / "output" / "capital_chronicle_lane.json").read_text(encoding="utf-8"))
    platform = lane["package"]["platform"]
    reported = {row["platform_id"] for row in platform["payloads"]}
    reported |= {row["platform_id"] for row in platform["unsupported_destinations"]}
    assert reported == set(TIER1_DESTINATIONS), "every Tier-1 destination needs an explicit result"
    for row in platform["unsupported_destinations"]:
        assert row["reason"]
        assert row["capability"] == "UNSUPPORTED_NO_CANONICAL_PACKAGE_CONTRACT"


# --- Review ---------------------------------------------------------------


def test_review_runs_all_eight_canonical_roles(demo):
    _, out = demo
    for filename in ("newsroom_lane.json", "capital_chronicle_lane.json"):
        lane = json.loads((out / "output" / filename).read_text(encoding="utf-8"))
        review = lane["review"]
        assert [row["role"] for row in review["roles"]] == list(ROLE_ORDER)
        assert review["role_count"] == 8
        assert review["deterministic_blockers_authoritative"] is True
        assert review["model_review_can_override_deterministic_blockers"] is False
        assert review["evidence_packet_hash"]
        for row in review["roles"]:
            assert row["model_assisted"] is False
            assert row["checks_run"], f"{row['role']} must run substantive checks"


def test_review_uses_canonical_engine_and_shared_reviewer(demo):
    """CORE V0 must not carry a second review implementation."""
    _, out = demo
    for filename in ("newsroom_lane.json", "capital_chronicle_lane.json"):
        review = json.loads((out / "output" / filename).read_text(encoding="utf-8"))["review"]
        assert review["review_engine"] == "editorial_review_orchestrator_v2.run_editorial_review"
        assert review["structured_reviewer"] == (
            "window_incremental_editorial_shadow_v1._shadow_structured_role_reviewer"
        )
        assert review["governed_claim_contract"] == "V3_GENERIC_CLAIM_GRAPH"


def test_visual_block_cannot_become_review_pass(demo):
    """A BLOCK visual decision must block the visual role and the final review."""
    _, out = demo
    for filename in ("newsroom_lane.json", "capital_chronicle_lane.json"):
        lane = json.loads((out / "output" / filename).read_text(encoding="utf-8"))
        review = lane["review"]
        if review["visual_decision_status"] != "BLOCK":
            continue
        assert review["result"] == "BLOCK"
        assert review["outcome"] == REVIEW_BLOCKED_VISUAL
        assert "visual_editor" in review["blocked_roles"]
        assert "adversarial_final_reviewer" in review["blocked_roles"]
        assert review["visual_blockers"]


def test_no_text_only_exception_was_manufactured(demo):
    """The visual policy must be applied as-is, with no invented editorial exception."""
    _, out = demo
    for filename in ("newsroom_lane.json", "capital_chronicle_lane.json"):
        lane = json.loads((out / "output" / filename).read_text(encoding="utf-8"))
        assert lane["package"]["visual"]["decision"]["editorial_exception"] is None


def test_unevidenced_numeric_token_is_blocked_by_canonical_review(demo):
    """A numeric token with no governed claim behind it must fail canonical review."""
    _, out = demo
    lane = json.loads((out / "output" / "newsroom_lane.json").read_text(encoding="utf-8"))
    package = json.loads(json.dumps(lane["package"]))
    package["article"]["body"].append(
        {"heading": "Unevidenced", "text": "The rate moved to 99.9 percent."}
    )
    review = review_package(
        package=package,
        lane_result=lane,
        evidence_packet=_news_packet(),
        request={
            "story_type": "data_release",
            "article_mode": "evidence_bound_shadow_draft",
            "workflow_mode": "evidence_bound_shadow_draft",
            "market_sensitive": False,
            "market_snapshot_required": False,
            "fresh_material_delta": False,
        },
        freshness_decision={"decision": "PASS", "blockers": []},
    )
    assert review["result"] == "BLOCK"
    assert any("unevidenced_numeric_token" in check for check in review["failed_checks"])


def test_unauthorized_claim_use_is_blocked_by_canonical_review(packet):
    """A claim outside the governed approved set must fail canonical review."""
    lane = run_capital_chronicle_lane(packet=packet)
    package = build_package(
        package_id="pkg-test-unauthorized",
        lane="capital_chronicle",
        story_id=lane["packet_id"],
        headline="Headline",
        answer_first_summary="Summary",
        body_sections=[{"heading": "H", "text": "Text without numbers."}],
        claim_ids=["claim-not-authorized"],
        citations=[{"source_document_id": "doc:1", "url": "https://example.test/doc"}],
        limitations=["limitation"],
        known_unknowns=["unknown"],
        primary_intent="intent",
        secondary_intent="intent2",
        story_type="official_action",
        source_label="Example Source",
        authority_logical_hash=str(lane["packet_logical_hash"]),
    )
    review = review_package(
        package=package,
        lane_result=lane,
        evidence_packet=packet,
        request={
            "story_type": "official_action",
            "article_mode": "evidence_bound_shadow_draft",
            "workflow_mode": "evidence_bound_shadow_draft",
            "market_sensitive": False,
            "market_snapshot_required": False,
            "fresh_material_delta": False,
        },
        freshness_decision={"decision": "PASS", "blockers": []},
    )
    assert review["result"] == "BLOCK"
    assert review["claims_reviewed"] == ["claim-not-authorized"]
    assert review["failed_checks"]


# --- Zero live authority --------------------------------------------------


def test_all_live_authority_flags_are_false(demo):
    summary, out = demo
    for filename in ("run_summary.json", "newsroom_lane.json",
                     "capital_chronicle_lane.json", "shadow_readback.json"):
        document = json.loads((out / "output" / filename).read_text(encoding="utf-8"))
        assert document["publication_authority"] is False
        assert document["dispatch_authority"] is False
        assert document["public_write_authority"] is False
        assert document["network_call_performed"] is False
        assert document["provider_call_performed"] is False
        assert document["credential_read_performed"] is False
        assert document["browser_or_cdp_action_performed"] is False
        assert document["public_write_performed"] is False
        assert_zero_live_action(document)
    assert summary["operating_mode"] == OPERATING_MODE


def test_shadow_readback_creates_no_public_object(demo):
    _, out = demo
    readback = json.loads((out / "output" / "shadow_readback.json").read_text(encoding="utf-8"))
    assert readback["public_objects_created"] == 0
    assert readback["public_urls"] == []
    assert readback["destinations_contacted"] == []
    assert readback["readback_kind"] == "SHADOW_SIMULATED_NO_PUBLIC_OBJECT"


def test_assert_zero_live_action_rejects_true_flag():
    with pytest.raises(DualLaneShadowError, match="live_authority_flag_not_false"):
        assert_zero_live_action({"nested": {"publication_authority": True}})


# --- Durable persistence and replay ---------------------------------------


def test_durable_state_records_both_lanes(demo):
    summary, _ = demo
    assert len(summary["durable_work_item_ids"]) == 2
    assert summary["replay_verification"]["all_replays_valid"] is True
    assert summary["replay_verification"]["work_items_replayed"] == 2


def test_durable_store_reopen_and_replay(demo):
    summary, out = demo
    reopened = ContentOpsDurableStore(out / "store.sqlite", auto_migrate=False)
    replay = verify_durable_replay(reopened, summary["durable_work_item_ids"])
    assert replay["all_replays_valid"] is True
    for row in replay["replays"]:
        assert row["verification_status"] == "PASS"
        assert row["event_count"] >= 4
        assert row["replayed_state"] == row["current_state"]

    reconstruction = reopened.reconstruct_in_flight_state()
    assert reconstruction["restart_reconstruction_status"] == "PASS"
    assert reconstruction["verified_work_items_count"] == 2


def test_durable_terminal_states_are_not_live_authority_states(demo):
    summary, _ = demo
    for state in summary["durable_terminal_states"].values():
        assert state in {"REVIEW_READY", "REVIEW_BLOCKED", "DEFERRED"}


def test_artifacts_are_registered_with_content_hashes(demo):
    summary, out = demo
    readback = json.loads((out / "output" / "shadow_readback.json").read_text(encoding="utf-8"))
    store = ContentOpsDurableStore(out / "store.sqlite", auto_migrate=False)
    for item in readback["work_items"]:
        assert item["artifact_ids"]
        for artifact_id in item["artifact_ids"]:
            artifact = store.get_artifact(artifact_id)
            assert artifact["sha256_hash"]
            assert artifact["byte_length"] > 0


# --- Determinism and end-to-end -------------------------------------------


def test_repeated_runs_are_byte_identical(tmp_path):
    outputs = []
    for index in range(2):
        target = tmp_path / f"run{index}"
        run_core_v0_shadow_demo(
            news_input=NEWS_INPUT,
            analysis_input=ANALYSIS_INPUT,
            store_path=tmp_path / f"store{index}.sqlite",
            output_dir=target,
        )
        outputs.append(
            {
                name: (target / name).read_bytes()
                for name in ("newsroom_lane.json", "capital_chronicle_lane.json")
            }
        )
    assert outputs[0] == outputs[1], "lane output must be deterministic across runs"


def test_cli_command_runs_end_to_end(tmp_path, capsys):
    exit_code = core_v0_shadow_demo_command(
        [
            "--news-input", str(NEWS_INPUT),
            "--analysis-input", str(ANALYSIS_INPUT),
            "--store", str(tmp_path / "cli.sqlite"),
            "--output", str(tmp_path / "cli_out"),
        ]
    )
    assert exit_code == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["operating_mode"] == OPERATING_MODE
    assert summary["newsroom_lane"]["outcome"] == "SELECTED"
    # Truthful canonical outcome: the current visual policy blocks text-only output.
    assert summary["capital_chronicle_lane"]["review_outcome"] == REVIEW_BLOCKED_VISUAL
    assert summary["review_engine"] == "editorial_review_orchestrator_v2.run_editorial_review"
    assert summary["elapsed_seconds"] >= 0
    for name in ("run_summary.json", "newsroom_lane.json",
                 "capital_chronicle_lane.json", "shadow_readback.json"):
        assert (tmp_path / "cli_out" / name).is_file()


def test_cli_reports_blocked_on_missing_input(tmp_path, capsys):
    exit_code = core_v0_shadow_demo_command(
        [
            "--news-input", str(tmp_path / "absent.json"),
            "--analysis-input", str(ANALYSIS_INPUT),
            "--store", str(tmp_path / "b.sqlite"),
            "--output", str(tmp_path / "b_out"),
        ]
    )
    assert exit_code == 1
    assert json.loads(capsys.readouterr().out)["status"] == "BLOCKED"
