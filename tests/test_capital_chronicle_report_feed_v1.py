"""Pinned real producer contracts plus explicit controlled-output integration."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    LatestReportDeliveryTracker,
    validate_latest_report_bytes,
    canonical_bytes,
    sha256_of,
)
from live_contentops.capital_chronicle_report_feed_v1 import MainReportFeed
from live_contentops.capital_chronicle_report_editorial_workspace_v1 import (
    report_workspace_projection,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from tests.test_capital_chronicle_report_editorial_workspace_v1 import controlled_writer

NOW = "2026-10-18T17:00:00Z"
ROOT = Path(__file__).parent / "fixtures"


def test_pending_native_opportunity_restores_frozen_interval_without_feed_or_loader(tmp_path, monkeypatch):
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, DesktopInputRequired
    f = feed(tmp_path)
    turn = NativeDesktopTurn(f.tracker.store, run_id="freeze-current", output_dir=tmp_path / "out", owner_manual_validation=True)
    intake = {"headlines": [], "complete_input_coverage": True, "canonical_input_hash": "a" * 64}
    with pytest.raises(DesktopInputRequired) as first:
        f.opportunity(output_dir=tmp_path / "out", cutoff_utc=NOW, run_id="freeze-current", rolling_input=intake, llm_invoke=turn)
    def forbidden(*a, **kw):
        raise AssertionError("Frozen input must not poll or reload current interval")
    monkeypatch.setattr(f, "poll", forbidden)
    monkeypatch.setattr("live_contentops.newsroom_assignment_scheduler_v1.load_rolling_x_headline_sidecars", forbidden)
    with pytest.raises(DesktopInputRequired) as again:
        f.opportunity(output_dir=tmp_path / "out", cutoff_utc=NOW, run_id="freeze-current", llm_invoke=turn)
    assert first.value.request["request_sha256"] == again.value.request["request_sha256"]


class FixtureSource:
    def bundle(self, spec):
        if spec["name"].startswith("gas"):
            root = ROOT / "main_goal17_report/producer_v2"
            prefix = "parent_" if spec["name"] == "gas1" else ""
        else:
            root = (
                ROOT
                / "main_goal19_report"
                / ("usoil_parent_v1" if spec["name"] == "oil1" else "usoil_v1_1")
            )
            prefix = ""
        return {
            "envelope": (root / (prefix + "envelope.json")).read_bytes(),
            "report": (root / (prefix + "report.json")).read_bytes(),
            "envelope_schema": (
                root / "CapitalChronicleLatestAnalysisReportEnvelopeV1.schema.json"
            ).read_bytes(),
            "report_schema": (
                root / "CapitalChronicleAssetAnalysisReportV1.schema.json"
            ).read_bytes(),
            "binding": json.loads((root / "producer_binding.json").read_bytes()),
        }


def feed(tmp_path, source=None):
    store = ContentOpsDurableStore(tmp_path / "isolated.sqlite3")
    pointer = {
        "producer_commit": "c8477a035bcb04b3d13bc4f8e26bd651dd9d957d",
        "bundles": [{"name": n} for n in ("gas2", "oil2", "oil1", "gas1")],
    }
    return MainReportFeed(
        LatestReportDeliveryTracker(store),
        pointer,
        source=source or FixtureSource(),
        headline_paths=[],
    )


def validate(bundle, **kwargs):
    return validate_latest_report_bytes(
        bundle["envelope"],
        report_bytes=[bundle["report"]],
        expected_cutoff_utc=NOW,
        now_utc=NOW,
        envelope_schema_bytes=bundle["envelope_schema"],
        report_schema_bytes=bundle["report_schema"],
        producer_binding=bundle["binding"],
        **kwargs,
    )


def reseal(bundle, mutate):
    b = deepcopy(bundle)
    r, e = json.loads(b["report"]), json.loads(b["envelope"])
    mutate(r, e)
    r["report_sha256"] = sha256_of({k: v for k, v in r.items() if k != "report_sha256"})
    e["report_sha256"] = r["report_sha256"]
    e["event_id"] = "report-event:" + sha256_of(
        {
            k: e[k]
            for k in (
                "report_id",
                "report_version",
                "report_sha256",
                "change_kind",
                "changed_claim_ids",
            )
        }
    )
    e["envelope_sha256"] = sha256_of(
        {k: v for k, v in e.items() if k != "envelope_sha256"}
    )
    b["report"], b["envelope"] = canonical_bytes(r), canonical_bytes(e)
    return b


def test_exact_versions_and_real_oil_gas_sequences_resume_incrementally(tmp_path):
    f = feed(tmp_path)
    scan = f.poll(cutoff_utc=NOW)
    assert scan["new_events"] == 4
    assert [r["report_id"] for r in f.pending()] == [
        "asset-report:USOIL",
        "asset-report:XNGUSD",
    ]
    oil = f.pending()[0]
    assert (
        oil["contract_version"] == "1.1.0"
        and oil["horizon_blocks"][-1]["trading_sessions"] == 252
    )
    assert scan["events"][0]["state"] == "LINEAGE_ONLY_NOOP"
    restarted = MainReportFeed(
        LatestReportDeliveryTracker(f.tracker.store),
        f.pointer,
        source=FixtureSource(),
        headline_paths=[],
    )
    again = restarted.poll(cutoff_utc=NOW)
    assert again["new_events"] == 0
    assert len(restarted.tracker.receipts()) == 4
    assert {r["state"] for r in again["events"]} == {"DUPLICATE_NOOP"}
    assert (
        len(
            report_workspace_projection(f.tracker.store.list_outbox_messages())[
                "workspaces"
            ]
        )
        == 2
    )


def test_unknown_and_mismatched_schema_revision_never_accepted():
    b = FixtureSource().bundle({"name": "oil2"})
    bad = reseal(b, lambda r, e: e.update(version="9.0.0", contract_revision="unknown"))
    assert validate(bad)["status"] == "BLOCKED"
    bad = deepcopy(b)
    bad["envelope_schema"] = FixtureSource().bundle({"name": "gas2"})["envelope_schema"]
    bad["binding"]["envelope_schema_sha256"] = hashlib.sha256(
        bad["envelope_schema"]
    ).hexdigest()
    assert "MAIN_CONTRACT_SCHEMA_REVISION_MISMATCH" in validate(bad)["blockers"]


def test_resealed_long_policy_and_body_clock_poison_fail_closed():
    b = FixtureSource().bundle({"name": "oil2"})
    bad = reseal(b, lambda r, e: r["horizon_policy"]["horizons"].update(long=21))
    assert "MAIN_HORIZON_POLICY_BINDING_INVALID" in validate(bad)["blockers"]
    bad = reseal(b, lambda r, e: e.update(known_at_cutoff_utc="2026-10-18T16:00:00Z"))
    assert (
        "REPORT_BODY_BINDING_MISMATCH:known_at_cutoff_utc" in validate(bad)["blockers"]
    )


def output_control(calls):
    donor = controlled_writer(calls)

    def invoke(**kwargs):
        value, receipt = donor(**kwargs)
        if "article" in value:
            identity = kwargs["governed_input"]["source_pack"][0]["source_identity"]
            if "USOIL" in identity:
                for key in (
                    "title",
                    "dek",
                    "search_title",
                    "meta_description",
                    "social_hook",
                ):
                    value["article"][key] = (
                        value["article"][key]
                        .replace("weekly gas injection", "oil inventory change")
                        .replace("weekly injection", "inventory change")
                        .replace("gas stocks", "oil balances")
                        .replace("weekly refill", "inventory decline")
                    )
                for binding in value["material_claim_bindings"]:
                    if binding["claim_id"].startswith("metadata-"):
                        binding["claim_text"] = value["article"][
                            binding["claim_id"].removeprefix("metadata-")
                        ]
        return value, receipt

    return invoke


def test_multi_asset_existing_simple_writer_previews_and_restart_no_double_work(
    tmp_path,
):
    f = feed(tmp_path)
    calls = []
    first = f.opportunity(
        output_dir=tmp_path / "slot1",
        cutoff_utc=NOW,
        run_id="slot1",
        rolling_input={"headlines": []},
        llm_invoke=output_control(calls),
    )
    assert first["qualified_article_count"] == 1, first
    selected = first["report_workspace_result"]["report_id"]
    assert len(first["report_workspace_result"]["previews"]) == 8
    assert len(calls) == 2
    again = f.opportunity(
        output_dir=tmp_path / "slot1",
        cutoff_utc=NOW,
        run_id="slot1",
        rolling_input={"headlines": []},
        llm_invoke=output_control(calls),
    )
    assert (
        again["report_workspace_result"]["article_identity"]
        == first["report_workspace_result"]["article_identity"]
    )
    assert len(calls) == 2
    second = f.opportunity(
        output_dir=tmp_path / "slot2",
        cutoff_utc=NOW,
        run_id="slot2",
        rolling_input={"headlines": []},
        llm_invoke=output_control(calls),
    )
    assert second["qualified_article_count"] == 1, second
    assert second["report_workspace_result"]["report_id"] != selected
    assert len(calls) == 4 and f.pending() == []
    view = report_workspace_projection(f.tracker.store.list_outbox_messages())
    assert sum(len(w["previews"]) for w in view["workspaces"]) == 16
    assert len(view["opportunities"]) == 2
    assert view["feed"]["new_events"] == 0


def test_pause_permits_all_independent_feed_work_without_a_provider(
    tmp_path, monkeypatch
):
    import live_contentops.capital_chronicle_report_editorial_workspace_v1 as workspace

    monkeypatch.setattr(workspace, "llm_operator_pause_active", lambda: True)
    f = feed(tmp_path)
    result = f.opportunity(
        output_dir=tmp_path / "paused",
        cutoff_utc=NOW,
        run_id="paused",
        rolling_input={"headlines": []},
    )
    assert result["exact_next_blocker"] == "LLM_OPERATOR_PAUSED"
    assert len(f.pending()) == 2
    assert f.tracker.counts()["editorial_inputs"] == 2


def test_thesis_delta_requires_its_exact_parent_before_admission(tmp_path):
    f = feed(tmp_path)
    f.pointer["bundles"] = [{"name": "oil2"}]
    assert f.poll(cutoff_utc=NOW)["events"][0]["state"] == "LINEAGE_PARENT_NOT_RECEIVED"
    f.pointer["bundles"] = [{"name": "oil1"}, {"name": "oil2"}]
    assert f.poll(cutoff_utc=NOW)["events"][-1]["state"] == "ADMITTED"


def test_no_change_keeps_pending_content_and_controlled_output_does_not_suppress_provider(
    tmp_path,
):
    from tests.test_capital_chronicle_report_editorial_workspace_v1 import delta

    f = feed(tmp_path)
    f.poll(cutoff_utc=NOW)
    f.tracker.consume(delta("NO_MATERIAL_CHANGE"), receipt_id="no-change-control")
    assert len(f.pending()) == 2
    for i in range(2):
        f.opportunity(
            output_dir=tmp_path / str(i),
            cutoff_utc=NOW,
            run_id=str(i),
            rolling_input={"headlines": []},
            llm_invoke=output_control([]),
        )
    assert not f.pending()
    assert len(f.pending(include_controlled=False)) == 2


def test_latest_provider_blocker_remains_visible_beside_controlled_output(
    tmp_path, monkeypatch
):
    import live_contentops.capital_chronicle_report_editorial_workspace_v1 as workspace

    f = feed(tmp_path)
    controlled = f.opportunity(
        output_dir=tmp_path / "control",
        cutoff_utc=NOW,
        run_id="control",
        rolling_input={"headlines": []},
        llm_invoke=output_control([]),
    )
    monkeypatch.setattr(workspace, "llm_operator_pause_active", lambda: True)
    f.opportunity(
        output_dir=tmp_path / "provider",
        cutoff_utc=NOW,
        run_id="provider",
        rolling_input={"headlines": []},
    )
    view = report_workspace_projection(f.tracker.store.list_outbox_messages())
    selected = next(
        w
        for w in view["workspaces"]
        if w["latest_report"]["report_id"]
        == controlled["report_workspace_result"]["report_id"]
    )
    assert len(selected["previews"]) == 8
    assert (
        selected["latest_simple_result"]["model_execution_state"]
        == "INJECTED_REPLAY_ONLY"
    )
    assert (
        selected["latest_attempt"]["model_execution_state"]
        == "PAUSED_BEFORE_PROVIDER_CALL"
    )
    assert selected["named_blocker"] == "LLM_OPERATOR_PAUSED"


def test_pointer_revision_reloads_each_poll_without_a_new_scheduler(
    tmp_path, monkeypatch
):
    import live_contentops.capital_chronicle_report_feed_v1 as module

    f = feed(tmp_path)
    pointer = {**f.pointer, "producer_commit": "f" * 40}
    f.pointer_loader = lambda: pointer
    monkeypatch.setattr(module, "PinnedMainGitSource", lambda p: FixtureSource())
    scan = f.poll(cutoff_utc=NOW)
    assert scan["producer_commit"] == "f" * 40 and scan["new_events"] == 4
    f.pointer_loader = lambda: None
    assert f.poll(cutoff_utc=NOW)["gaps"] == [
        {"state": "MAIN_FEED_POINTER_UNAVAILABLE_OR_INVALID"}
    ]


def test_bad_export_does_not_hide_healthy_other_asset(tmp_path):
    class MixedSource(FixtureSource):
        def bundle(self, spec):
            b = super().bundle(spec)
            if spec["name"] == "oil2":
                b["report"] = b"invalid report bytes"
            return b

    f = feed(tmp_path, source=MixedSource())
    scan = f.poll(cutoff_utc=NOW)
    assert scan["gaps"][0]["state"] == "MAIN_EXPORT_UNAVAILABLE_OR_INVALID"
    assert [r["report_id"] for r in f.pending()] == ["asset-report:XNGUSD"]


def test_completed_multiasset_output_withdrawal_keeps_other_asset_and_history(tmp_path):
    from tests.test_capital_chronicle_report_editorial_workspace_v1 import delta

    f = feed(tmp_path)
    calls = []
    outputs = [
        f.opportunity(
            output_dir=tmp_path / str(i),
            cutoff_utc=NOW,
            run_id=str(i),
            rolling_input={"headlines": []},
            llm_invoke=output_control(calls),
        )
        for i in range(2)
    ]
    withdrawal = delta("INVALIDATION", withdraw=True)
    f.tracker.consume(withdrawal, receipt_id="gas-v3-withdrawal-control")
    view = report_workspace_projection(f.tracker.store.list_outbox_messages())
    gas = next(
        w
        for w in view["workspaces"]
        if w["latest_report"]["report_id"] == "asset-report:XNGUSD"
    )
    oil = next(
        w
        for w in view["workspaces"]
        if w["latest_report"]["report_id"] == "asset-report:USOIL"
    )
    assert gas["named_blocker"] == "CLAIMS_WITHDRAWN" and not gas["article"]
    assert gas["history"][0]["state"] == "WITHDRAWN"
    assert len(oil["previews"]) == 8
    slot = next(
        str(i)
        for i, r in enumerate(outputs)
        if r["report_workspace_result"]["report_id"] == "asset-report:XNGUSD"
    )
    replay = f.opportunity(
        output_dir=tmp_path / slot,
        cutoff_utc=NOW,
        run_id=slot,
        llm_invoke=output_control(calls),
    )
    assert replay["qualified_article_count"] == 0
    assert replay["report_workspace_result"]["classification"] == "DRAFT_WITHDRAWN"
    assert len(calls) == 4


def test_real_private_internal_main_body_never_enters_consumer_projection():
    b = FixtureSource().bundle({"name": "oil2"})
    bad = reseal(
        b,
        lambda r, e: r["analysis"].update(
            private_context={
                "account_id": "PRIVATE_DEMO_DO_NOT_COPY",
                "fills": ["PRIVATE_FILL"],
            }
        ),
    )
    admitted = validate(bad)
    assert "PRIVATE_DEMO_DO_NOT_COPY" not in json.dumps(admitted)
    assert "PRIVATE_FILL" not in json.dumps(admitted)


def test_existing_four_window_hook_and_interrupted_slot_reuse_successful_stages(
    tmp_path, monkeypatch
):
    from live_contentops.v1_simple_gemini_scheduler_v1 import SimpleGeminiLocalScheduler
    from live_contentops import eight_platform_substack_first_pipeline_v1 as compiler
    from tests.test_v1_simple_gemini_scheduler_v1 import _memory_loader

    f = feed(tmp_path)
    calls = []

    class Hook:
        def can_resume(self, slot_id):
            return f.can_resume(slot_id)

        def opportunity(self, **kwargs):
            return f.opportunity(
                **kwargs,
                rolling_input={"headlines": []},
                llm_invoke=output_control(calls),
            )

    scheduler = SimpleGeminiLocalScheduler(
        scheduler_root=tmp_path / "scheduler",
        main_report_feed=Hook(),
        published_memory_loader=_memory_loader(),
    )
    assert len(scheduler.policy.core_windows) == 4
    original = compiler.build_native_derivative_payloads

    def crash(**kwargs):
        raise SystemExit("simulated-process-exit")

    monkeypatch.setattr(compiler, "build_native_derivative_payloads", crash)
    with pytest.raises(SystemExit, match="simulated-process-exit"):
        scheduler.tick(now="2026-10-19T10:00:00Z")
    assert len(calls) == 2
    monkeypatch.setattr(compiler, "build_native_derivative_payloads", original)
    restarted = SimpleGeminiLocalScheduler(
        scheduler_root=tmp_path / "scheduler",
        main_report_feed=Hook(),
        published_memory_loader=_memory_loader(),
    )
    result = restarted.tick(now="2026-10-19T10:00:00Z")
    assert result["classification"] == "TERMINAL_QUALIFIED", result
    assert (
        len(calls) == 4
    )  # resumed first article, then one new article for the second asset
    duplicate = restarted.tick(now="2026-10-19T10:00:00Z")
    assert duplicate["simple_operation_invocation_count"] == 0
    assert len(calls) == 4
