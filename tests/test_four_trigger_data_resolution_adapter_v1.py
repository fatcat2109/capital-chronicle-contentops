from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.four_trigger_data_resolution_adapter_v1 import (
    ANALYSIS_RUN_RECEIPT_SCHEMA,
    CONSUMER_ROUTE,
    DATA_NEED_PLAN_SCHEMA,
    DATA_RESOLUTION_RECEIPT_SCHEMA,
    DESTINATIONS,
    EDITORIAL_OPERATION,
    EDITORIAL_OWNER,
    EPISTEMIC_LAYERS,
    FourTriggerAdapterError,
    MAIN_MODEL_SHA256,
    PUBLICATION_OWNER,
    SERVING_COVERAGE_PROJECTION_SCHEMA,
    TRIGGER_REQUEST_SCHEMA,
    build_analysis_run_receipt,
    build_data_need_plan,
    build_editorial_consumer_packet,
    build_epistemic_derivative_manifest,
    build_existing_contentops_source_layers,
    build_existing_eight_derivative_epistemic_manifest,
    build_serving_coverage_projection,
    build_trigger_request,
    contract_bindings,
    deduplicate_trigger_request,
    existing_owner_bindings,
    load_resolution_checkpoint,
    prepare_simple_gemini_handoff,
    resolve_data_need_plan,
    validate_adapter_artifact,
    write_resolution_checkpoint,
)


ROOT = Path(__file__).parents[1]
FIXTURE = json.loads(
    (
        ROOT / "tests" / "fixtures" / "four_trigger_data_resolution_cases_v1.json"
    ).read_text(encoding="utf-8")
)
RECEIPTS = json.loads(
    (
        ROOT / "tests" / "fixtures" / "four_trigger_data_resolution_receipts_v1.json"
    ).read_text(encoding="utf-8")
)
NOW = "2026-10-18T09:00:00Z"


def _case(name: str) -> dict:
    return next(row for row in FIXTURE["request_cases"] if row["case_id"] == name)


def _request(case_name: str, *, requested_at: str = NOW) -> dict:
    row = _case(case_name)
    return build_trigger_request(
        request_id=row["request_id"],
        idempotency_key=row["idempotency_key"],
        trigger_kind=row["trigger_kind"],
        requester=row["requester"],
        target_assets=row.get("target_assets", []),
        exact_exness_symbols=row.get("exact_exness_symbols", []),
        portfolio_scope=row.get("portfolio_scope"),
        decision_purpose=row["decision_purpose"],
        requested_at_utc=requested_at,
        editorial_mode="STANDARD_NEWS_ANALYSIS",
        publication_intent="RESEARCH_ONLY",
        required_epistemic_state="OBSERVED_FACT",
    )


def _plan(case_name: str, *, needs=None) -> tuple[dict, dict]:
    request = _request(case_name)
    rows = needs if needs is not None else _case(case_name)["needs"]
    return request, build_data_need_plan(request, rows, as_of_utc=NOW)


def _layers() -> dict:
    return {
        "sidecars": FIXTURE["source_rows"]["sidecars"],
        "published_memory": FIXTURE["source_rows"]["published_memory"],
        "admitted_records": FIXTURE["source_rows"]["admitted_records"],
        "read_models": FIXTURE["source_rows"]["read_models"],
    }


def test_contract_bindings_are_exact_and_main_owned():
    bindings = contract_bindings()
    assert bindings["design_target"]["pr"] == 81
    assert bindings["design_target"]["state"] == "OPEN_DESIGN_TARGET"
    assert bindings["main_model"]["sha256"] == MAIN_MODEL_SHA256
    assert (
        bindings["contracts"]["trigger_request"] == "CapitalChronicleTriggerRequestV1"
    )
    assert bindings["contracts"]["data_need_plan"] == "CapitalChronicleDataNeedPlanV1"
    assert (
        bindings["contracts"]["data_resolution_receipt"]
        == "CapitalChronicleDataResolutionReceiptV1"
    )
    assert (
        bindings["contracts"]["analysis_run_receipt"]
        == "CapitalChronicleAnalysisRunReceiptV1"
    )
    assert (
        bindings["contracts"]["serving_coverage_projection"]
        == "CapitalChronicleServingCoverageProjectionV1"
    )
    assert FIXTURE["metadata"]["authority"] is False


def test_receipt_fixture_is_shadow_only_and_covers_resolved_fallback_blocked_paths():
    assert RECEIPTS["metadata"]["authority"] is False
    assert RECEIPTS["metadata"]["no_write"] is True
    assert RECEIPTS["metadata"]["case_count"] == 7
    assert (
        RECEIPTS["cases"]["foundation"]["resolution"]["resolution_state"] == "RESOLVED"
    )
    assert (
        RECEIPTS["cases"]["browser-fallback"]["resolution"]["resolutions"][0]["route"]
        == "BROWSEROS_READ_ONLY"
    )
    assert (
        RECEIPTS["cases"]["contradiction"]["resolution"]["resolution_state"]
        == "DATA_BLOCKED"
    )
    assert (
        RECEIPTS["cases"]["data-blocked"]["analysis"]["output_class"] == "DATA_BLOCKED"
    )
    assert RECEIPTS["derivative_manifest"]["derivative_count"] == 8


def test_all_four_trigger_kinds_use_one_consumer_route_and_no_new_scheduler():
    expected = {
        "foundation": ("FOUNDATION_COVERAGE_SERVING", False),
        "latest-intelligence": ("SCHEDULED_LATEST_INTELLIGENCE", True),
        "portfolio-context": ("SCHEDULED_PORTFOLIO_CONTEXT", True),
        "jim-manual": ("JIM_MANUAL_CODEX_DESKTOP", False),
    }
    for name, (kind, routine_window) in expected.items():
        request = _request(name)
        assert request["schema_version"] == TRIGGER_REQUEST_SCHEMA
        assert request["consumer_route"] == CONSUMER_ROUTE
        assert request["trigger_kind"] == kind
        assert request["route"]["routine_window"] is routine_window
        assert request["route"]["creates_scheduler"] is False
        assert request["no_write"] is True


def test_existing_owner_bindings_are_explicit_and_reused():
    owners = existing_owner_bindings()
    assert owners["routine_editorial_owner"] == EDITORIAL_OWNER
    assert owners["publication_owner"] == PUBLICATION_OWNER
    assert owners["routine_windows_reused"] == ["17:00", "21:00", "23:00", "01:00"]
    assert owners["creates_scheduler"] is False
    assert "load_rolling_x_headline_sidecars" in owners["bindings"]["sidecars"]
    assert (
        "load_canonical_published_memory_read_only"
        in owners["bindings"]["published_memory"]
    )
    assert (
        "build_native_derivative_payloads"
        in owners["bindings"]["eight_derivative_compiler"]
    )


def test_request_hard_boundaries_reject_wrong_manual_owner_private_scope_and_write():
    with pytest.raises(FourTriggerAdapterError, match="manual_request_requires_jim"):
        build_trigger_request(
            request_id="bad-manual",
            idempotency_key="bad-manual",
            trigger_kind="JIM_MANUAL_CODEX_DESKTOP",
            requester="operator",
            decision_purpose="research",
            requested_at_utc=NOW,
        )
    with pytest.raises(FourTriggerAdapterError, match="portfolio_scope_required"):
        build_trigger_request(
            request_id="bad-portfolio",
            idempotency_key="bad-portfolio",
            trigger_kind="SCHEDULED_PORTFOLIO_CONTEXT",
            requester="MAIN_APP_PORTFOLIO_CONTROL_PLANE",
            decision_purpose="context",
            requested_at_utc=NOW,
        )
    with pytest.raises(FourTriggerAdapterError, match="requires_no_write"):
        build_trigger_request(
            request_id="bad-write",
            idempotency_key="bad-write",
            trigger_kind="FOUNDATION_COVERAGE_SERVING",
            requester="system",
            decision_purpose="coverage",
            requested_at_utc=NOW,
            no_write=False,
        )


def test_idempotency_reuses_terminal_request_and_rejects_payload_conflict():
    request = _request("latest-intelligence")
    fresh = deduplicate_trigger_request(request, {})
    assert fresh["disposition"] == "NEW"
    reused = deduplicate_trigger_request(request, {request["idempotency_key"]: request})
    assert reused["disposition"] == "TERMINAL_REUSED"
    conflicting = dict(request)
    conflicting["decision_purpose"] = "changed"
    conflicting["request_hash"] = (
        __import__("hashlib")
        .sha256(
            __import__("json")
            .dumps(
                {
                    key: value
                    for key, value in conflicting.items()
                    if key != "request_hash"
                },
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            )
            .encode("utf-8")
        )
        .hexdigest()
    )
    with pytest.raises(
        FourTriggerAdapterError, match="idempotency_key_payload_conflict"
    ):
        deduplicate_trigger_request(conflicting, {request["idempotency_key"]: request})


def test_plan_hash_binds_fields_clocks_rights_and_database_first_order():
    _request_value, plan = _plan("latest-intelligence")
    assert plan["schema_version"] == DATA_NEED_PLAN_SCHEMA
    assert plan["consumer_route"] == CONSUMER_ROUTE
    assert plan["no_write"] is True
    assert plan["database_first_order"] == [
        "RETAINED_HEADLINE_SIDECAR",
        "PUBLISHED_MEMORY",
        "ADMITTED_OFFICIAL_FILING_PROVIDER",
        "EXISTING_MARKET_READ_MODEL",
        "BROWSEROS_READ_ONLY",
        "UNAVAILABLE",
    ]
    assert len(plan["plan_hash"]) == 64
    assert plan["needs"][0]["as_of_utc"] == NOW


def test_existing_sidecar_reader_projection_keeps_existing_ingestion_shape():
    rolling = {
        "headlines": [
            {
                "headline_id": "headline-1",
                "source_timestamp_utc": "2026-10-18T08:00:00Z",
                "external_content": {
                    "headline_text": "A retained sidecar headline",
                    "source_platform": "x_cdp_list_latest_tweets_timeline",
                    "url_or_source_ref": "https://x.com/example/status/1",
                },
            }
        ]
    }
    layers = build_existing_contentops_source_layers(
        rolling_input=rolling,
        published_memory=[
            {"need_id": "memory-1", "source_identity": "published-memory"}
        ],
    )
    assert layers["sidecars"][0]["source_class"] == "RETAINED_HEADLINE_SIDECAR"
    assert (
        layers["sidecars"][0]["values"]["headline_text"]
        == "A retained sidecar headline"
    )
    assert layers["published_memory"][0]["source_identity"] == "published-memory"


def test_database_first_prefers_retained_sidecar_before_lower_layers():
    request, plan = _plan("latest-intelligence")
    lower = {
        "need_id": "latest-headline",
        "source_identity": "admitted.lower.priority",
        "source_hash": "9" * 64,
        "freshness_state": "FRESH",
        "rights_state": "ALLOWED",
        "pit_state": "PASS",
        "epistemic_state": "OBSERVED_FACT",
        "exact_or_proxy": "EXACT",
        "values": {"headline_text": "Lower layer must not win."},
    }
    layers = {**_layers(), "admitted_records": [lower]}
    receipt = resolve_data_need_plan(plan, source_layers=layers)
    row = receipt["resolutions"][0]
    assert receipt["schema_version"] == DATA_RESOLUTION_RECEIPT_SCHEMA
    assert row["route"] == "RETAINED_HEADLINE_SIDECAR"
    assert row["source_identity"] == "x.sidecar.headline-001"
    assert [attempt["route"] for attempt in row["attempts"]] == [
        "RETAINED_HEADLINE_SIDECAR"
    ]
    assert receipt["resolution_state"] == "RESOLVED"
    assert receipt["public_write_performed"] is False


def test_browseros_fallback_records_visible_hash_clocks_and_read_only_policy():
    request, plan = _plan("latest-intelligence")
    recovery_calls = []

    def recover(need):
        recovery_calls.append(need["need_id"])
        return FIXTURE["browser_recovery"]

    stale = dict(FIXTURE["source_rows"]["sidecars"][0])
    stale["freshness_state"] = "STALE"
    receipt = resolve_data_need_plan(
        plan,
        source_layers={
            "sidecars": [stale],
            "published_memory": [],
            "admitted_records": [],
            "read_models": [],
        },
        browser_recovery=recover,
    )
    row = receipt["resolutions"][0]
    assert recovery_calls == ["latest-headline"]
    assert row["route"] == "BROWSEROS_READ_ONLY"
    assert row["source_hash"] == "a" * 64
    assert row["fallback_reason"] == "database_missing_or_stale_required_field"
    assert [attempt["route"] for attempt in row["attempts"]] == [
        "RETAINED_HEADLINE_SIDECAR",
        "BROWSEROS_READ_ONLY",
    ]
    assert row["tool_policy"]["allowed_tools_used"] == ["name_session", "tabs", "read"]
    assert receipt["resolution_state"] == "RESOLVED"


@pytest.mark.parametrize(
    ("mutation", "expected_state"),
    [
        ("stale", "STALE"),
        ("rights", "DATA_BLOCKED"),
        ("pit", "DATA_BLOCKED"),
    ],
)
def test_stale_rights_and_pit_missingness_remain_explicit(mutation, expected_state):
    request, plan = _plan("latest-intelligence")
    row = dict(FIXTURE["source_rows"]["sidecars"][0])
    if mutation == "stale":
        row["freshness_state"] = "STALE"
    elif mutation == "rights":
        row["rights_state"] = "DENIED"
    else:
        row["pit_state"] = "MISSING"
    receipt = resolve_data_need_plan(
        plan,
        source_layers={
            "sidecars": [row],
            "published_memory": [],
            "admitted_records": [],
            "read_models": [],
        },
    )
    result = receipt["resolutions"][0]
    assert receipt["resolution_state"] == expected_state
    assert result["route"] == "UNAVAILABLE"
    assert result["missing_fields"] == ["headline_text"]
    if mutation == "stale":
        assert result["stale_fields"] == ["stale"]
    if mutation == "rights":
        assert result["rights_blocked_fields"] == ["rights_denied"]
    assert "database_no_admissible_record" not in result["fallback_reason"]


def test_contradictory_records_fail_closed_and_preserve_source_hashes():
    request, plan = _plan("latest-intelligence")
    first = dict(FIXTURE["source_rows"]["sidecars"][0])
    second = dict(first)
    second["source_identity"] = "x.sidecar.headline-002"
    second["source_hash"] = "8" * 64
    second["values"] = {"headline_text": "A contradictory report."}
    receipt = resolve_data_need_plan(
        plan,
        source_layers={
            "sidecars": [first, second],
            "published_memory": [],
            "admitted_records": [],
            "read_models": [],
        },
    )
    row = receipt["resolutions"][0]
    assert receipt["resolution_state"] == "DATA_BLOCKED"
    assert row["contradiction"]["state"] == "UNRESOLVED"
    assert set(row["contradiction"]["source_hashes"]) == {"1" * 64, "8" * 64}
    assert row["epistemic_state"] == "SCENARIO_OR_UNCERTAINTY"


def test_browser_fallback_write_or_session_violation_is_rejected():
    _request_value, plan = _plan("latest-intelligence")
    bad = dict(FIXTURE["browser_recovery"])
    bad["public_write_performed"] = True
    with pytest.raises(FourTriggerAdapterError, match="write_or_secret_violation"):
        resolve_data_need_plan(
            plan,
            source_layers={
                "sidecars": [],
                "published_memory": [],
                "admitted_records": [],
                "read_models": [],
            },
            browser_recovery=lambda _need: bad,
        )


def test_terminal_checkpoint_resume_is_idempotent_and_durable(tmp_path):
    _request_value, plan = _plan("latest-intelligence")
    first = resolve_data_need_plan(
        plan,
        source_layers=_layers(),
    )
    checkpoint_path = tmp_path / "resolution.json"
    digest = write_resolution_checkpoint(checkpoint_path, first)
    assert (
        digest == __import__("hashlib").sha256(checkpoint_path.read_bytes()).hexdigest()
    )
    loaded = load_resolution_checkpoint(checkpoint_path)
    replay = resolve_data_need_plan(
        plan,
        source_layers={
            "sidecars": [],
            "published_memory": [],
            "admitted_records": [],
            "read_models": [],
        },
        checkpoint=loaded,
    )
    assert replay["idempotency_replayed"] is True
    assert replay["receipt_hash"] == first["receipt_hash"]
    assert replay["resolutions"] == first["resolutions"]


def test_analysis_receipt_consumes_resolution_and_keeps_authority_separate():
    request, plan = _plan("portfolio-context")
    resolution = resolve_data_need_plan(plan, source_layers=_layers())
    receipt = build_analysis_run_receipt(
        request,
        plan,
        resolution,
        analysis_context={"thesis": "proxy context only", "exact_or_proxy": "PROXY"},
        output_class="ANALYSIS_ONLY",
        decision_version="shadow-v1",
    )
    assert receipt["schema_version"] == ANALYSIS_RUN_RECEIPT_SCHEMA
    assert receipt["output_class"] == "ANALYSIS_ONLY"
    assert receipt["terminal_state"] == "COMPLETE_SHADOW"
    assert receipt["authority"]["core_numeric_truth"] is False
    assert receipt["authority"]["portfolio_authority"] is False
    assert receipt["broker_write_performed"] is False


def test_blocked_analysis_receipt_cannot_be_promoted_to_publishable():
    request, plan = _plan("latest-intelligence")
    resolution = resolve_data_need_plan(
        plan,
        source_layers={
            "sidecars": [],
            "published_memory": [],
            "admitted_records": [],
            "read_models": [],
        },
    )
    receipt = build_analysis_run_receipt(
        request, plan, resolution, output_class="EDITORIAL_PUBLISHABLE"
    )
    assert receipt["output_class"] == "DATA_BLOCKED"
    assert receipt["terminal_state"] == "DATA_BLOCKED"
    assert receipt["deferred_needs"] == ["latest-headline"]


def test_serving_projection_keeps_unknown_denominators_null_and_private_fields_out():
    projection = build_serving_coverage_projection(
        [
            {
                "capability_id": "macro.fed.rate",
                "asset_class": "macro",
                "query_reference": "macro.fed.v1",
                "implemented": True,
                "queryable": True,
                "admissible": True,
                "freshness_state": "FRESH",
                "pit_state": "PASS",
                "rights_state": "ALLOWED",
                "exact_or_proxy": "EXACT",
                "naturally_demonstrated": False,
                "missing_dimensions": ["revision_vintage"],
            }
        ],
        snapshot_id="coverage-shadow-1",
        as_of_utc=NOW,
    )
    assert projection["schema_version"] == SERVING_COVERAGE_PROJECTION_SCHEMA
    assert projection["unknown_denominators"] is None
    assert projection["private_portfolio_fields_included"] is False
    assert projection["rows"][0]["naturally_demonstrated"] is False


def test_editorial_packet_reuses_existing_owners_and_blocks_public_write():
    request, plan = _plan("latest-intelligence")
    resolution = resolve_data_need_plan(plan, source_layers=_layers())
    packet = build_editorial_consumer_packet(request, plan, resolution)
    assert packet["editorial_owner"] == EDITORIAL_OWNER
    assert packet["editorial_operation"] == EDITORIAL_OPERATION
    assert packet["publication_owner"] == PUBLICATION_OWNER
    assert packet["derivative_destinations"] == list(DESTINATIONS)
    assert packet["cdp_boundaries"] == {
        "ingestion_only": 9222,
        "publication_media_readback": 9223,
    }
    assert packet["creates_scheduler"] is False
    assert packet["creates_store"] is False
    assert packet["creates_publisher"] is False
    assert packet["public_write_performed"] is False
    assert packet["editorial_disposition"] == "READY_FOR_EXISTING_OWNER"


def test_simple_gemini_handoff_is_prepared_without_runtime_invocation(tmp_path):
    request, plan = _plan("latest-intelligence")
    resolution = resolve_data_need_plan(plan, source_layers=_layers())
    packet = build_editorial_consumer_packet(request, plan, resolution)
    handoff = prepare_simple_gemini_handoff(packet, output_dir=tmp_path, cutoff_utc=NOW)
    assert handoff["operation"] == EDITORIAL_OPERATION
    assert handoff["invoked"] is False
    assert (
        handoff["runner_arguments"]["capital_chronicle_context"]["consumer_route"]
        == CONSUMER_ROUTE
    )
    assert (
        handoff["runner_arguments"]["capital_chronicle_context"][
            "grants_capital_chronicle_numeric_authority"
        ]
        is False
    )
    assert handoff["public_write_performed"] is False


def test_editorial_packet_is_data_blocked_without_invoking_builder():
    request, plan = _plan("latest-intelligence")
    resolution = resolve_data_need_plan(
        plan,
        source_layers={
            "sidecars": [],
            "published_memory": [],
            "admitted_records": [],
            "read_models": [],
        },
    )
    calls = []
    packet = build_editorial_consumer_packet(
        request,
        plan,
        resolution,
        article_builder=lambda _packet: calls.append("called"),
    )
    assert packet["editorial_disposition"] == "DATA_BLOCKED"
    assert calls == []


def test_epistemic_layers_survive_all_eight_existing_derivative_intents():
    manifest = build_epistemic_derivative_manifest(
        FIXTURE["article"],
        FIXTURE["derivative_payloads"],
        canonical_url="https://capitalchronicle.example/p/source-bound",
    )
    assert manifest["derivative_count"] == 8
    assert manifest["all_layers_preserved"] is True
    for destination in DESTINATIONS:
        row = manifest["derivatives"][destination]
        assert row["epistemic_layers"] == sorted(EPISTEMIC_LAYERS)
        assert row["public_write_performed"] is False
        assert row["unknown_write"] is False
        assert row["canonical_url_state"] == "RECONCILED_CANONICAL_URL_REQUIRED"


def test_existing_eight_compiler_is_reused_before_epistemic_manifest():
    article = {
        "title": "A concise source-bound update",
        "subtitle": "The report leaves the outcome open.",
        "social_hook": "The report leaves the outcome open.",
        "social_lede": "The report leaves the outcome open.",
        "substack_body_markdown": "The official record describes a change. The next outcome remains uncertain.",
        "article_mode": "BREAKING_BRIEF",
        "epistemic_claims": FIXTURE["article"]["epistemic_claims"],
    }
    selection = {"dek": article["subtitle"]}
    manifest = build_existing_eight_derivative_epistemic_manifest(
        article=article,
        selection=selection,
        canonical_url="https://capitalchronicle.example/p/compiler-reuse",
        media_asset_ids=(),
    )
    assert manifest["derivative_count"] == 8
    assert manifest["all_layers_preserved"] is True


def test_epistemic_manifest_rejects_missing_derivative_or_invalid_layer():
    payloads = dict(FIXTURE["derivative_payloads"])
    payloads.pop("youtube")
    with pytest.raises(
        FourTriggerAdapterError, match="derivative_destination_missing:youtube"
    ):
        build_epistemic_derivative_manifest(
            FIXTURE["article"], payloads, canonical_url="https://example.com/p/1"
        )
    article = json.loads(json.dumps(FIXTURE["article"]))
    article["epistemic_claims"][0]["layer"] = "OBSERVED_PROXY"
    with pytest.raises(
        FourTriggerAdapterError, match="article_epistemic_claim_layer_invalid"
    ):
        build_epistemic_derivative_manifest(
            article,
            FIXTURE["derivative_payloads"],
            canonical_url="https://example.com/p/1",
        )


def test_validation_catches_secret_write_and_hash_drift():
    request = _request("foundation")
    assert validate_adapter_artifact(request, "request_hash") == []
    secret = dict(request)
    secret["api_key"] = "fixture-secret-must-never-be-accepted"
    assert "secret_or_session_material" in validate_adapter_artifact(
        secret, "request_hash"
    )
    written = dict(request)
    written["public_write_performed"] = True
    assert "write_performed" in validate_adapter_artifact(written, "request_hash")
    tampered = dict(request)
    tampered["decision_purpose"] = "tampered"
    assert "request_hash_mismatch" in validate_adapter_artifact(
        tampered, "request_hash"
    )


def test_adapter_source_has_no_parallel_runtime_authority():
    source = (
        ROOT / "live_contentops" / "four_trigger_data_resolution_adapter_v1.py"
    ).read_text(encoding="utf-8")
    assert "sqlite3" not in source
    assert "subprocess" not in source
    assert "import requests" not in source
    assert "creates_scheduler" in source
    assert "DurablePublicationCoordinator" in source
    assert "SIMPLE_GEMINI_RUNTIME" in source
