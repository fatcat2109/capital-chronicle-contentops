"""Isolated fault injections; these controlled records are not draft articles."""

from copy import deepcopy
from hashlib import sha256
import json

import pytest

from live_contentops.retrospective_piece_v1 import validate_retrospective_piece
from live_contentops import rolling_x_grounded_article_media_builder_v1 as media


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    root = tmp_path_factory.mktemp("retrospective-controlled")
    text = "October 28, 2026: controlled announced rate 3.90 percent."
    url = "https://example.test/CONTROLLED-source"
    raw = json.dumps(
        {"value": {"knownAt": "2026-10-28T19:13:00Z", "url": url, "text": text}}
    ).encode()
    (root / "original.json").write_bytes(raw)
    (root / "capture.json").write_bytes(
        b"CONTROLLED representation, not a real capture"
    )
    (root / "rights.json").write_bytes(b"CONTROLLED rights fixture, not a licence")

    def digest(value):
        return sha256(value).hexdigest()

    capture_hash, policy_hash = (
        digest((root / "capture.json").read_bytes()),
        digest((root / "rights.json").read_bytes()),
    )
    doc = {
        "document_id": "CONTROLLED",
        "canonical_content_text": text,
        "published_at_utc": "2026-10-28T18:00:00Z",
        "known_at_utc": "2026-10-28T19:13:00Z",
        "raw_sha256": capture_hash,
        "source_url": url,
        "publisher": "Controlled test",
        "source_reuse_constraints": {
            "attribution_required": True,
            "policy_capture_sha256": policy_hash,
            "source_capture_sha256": capture_hash,
        },
    }
    packet = {
        "asset_id": "controlled-rate",
        "chart_type": "grouped_bar",
        "question": "Controlled numeric geometry?",
        "title": "Controlled test only",
        "unit": "percent",
        "source_caption": "Controlled test fixture; no factual evidence.",
        "series": [
            {
                "series_id": "CONTROLLED_RATE",
                "label": "Controlled rate",
                "points": [
                    {
                        "period": "28 Oct",
                        "value": 3.9,
                        "observation_kind": "ANNOUNCED_POLICY",
                        "inputs": [
                            {
                                "document_id": "CONTROLLED",
                                "support_excerpt": text,
                                "value_text": "3.90",
                                "source_period_text": "October 28, 2026",
                                "source_content_sha256": digest(text.encode()),
                                "metric": "controlled rate",
                                "unit": "percent",
                                "prepared_period": "2026-10-28",
                                "period_basis": "CONTROLLED_EXACT_SOURCE_PERIOD",
                            }
                        ],
                    }
                ],
            }
        ],
    }
    asset = media.build_editorial_data_chart(packet, [doc], output_dir=root)
    piece = {
        "schema_version": "contentops.retrospective_piece.v1",
        "piece_id": "CONTROLLED_TEST_ONLY",
        "public_write_performed": False,
        "story_kind": "POLICY",
        "event": {
            "published_at_utc": "2026-10-28T18:00:00Z",
            "knowledge_cutoff_utc": "2026-10-28T19:14:31Z",
            "main_event_handoff_sha256": "a" * 64,
        },
        "written_at_utc": "2026-11-01T05:30:00Z",
        "written_on_gmt7": "2026-11-01",
        "native_calls": [
            {
                "invocation_id": "/root/CONTROLLED_TEST_NOT_REAL",
                "request_sha256": "b" * 64,
                "invocation_recorded_at_utc": "2026-11-01T05:20:00Z",
                "model": None,
                "reasoning_effort": None,
                "configuration_status": "CONFIGURED_NOT_OBSERVED",
            }
        ],
        "sources": [
            {
                "document_id": "CONTROLLED",
                "original_known_at_utc": doc["known_at_utc"],
                "capture_sha256": capture_hash,
                "canonical_content_sha256": digest(text.encode()),
                "edition_basis": "RETAINED_CONTEMPORANEOUS_CAPTURE",
                "original_capture_path": str(root / "original.json"),
                "original_capture_sha256": digest(raw),
                "representation_capture_path": str(root / "capture.json"),
                "rights_capture_path": str(root / "rights.json"),
            }
        ],
        "charts": [
            {
                "asset_id": asset["asset_id"],
                "series_ids": ["CONTROLLED_RATE"],
                "source_capture_hashes": {"CONTROLLED": capture_hash},
                "window_start_utc": "2026-10-28T18:00:00Z",
                "window_end_utc": "2026-10-28T19:14:31Z",
                "point_times": [
                    {
                        "series_id": "CONTROLLED_RATE",
                        "point_index": 0,
                        "as_of_utc": "2026-10-28T19:13:00Z",
                        "period_end_utc": "2026-10-29T00:00:00Z",
                    }
                ],
            }
        ],
    }
    article = "Retrospective analysis, written on 1 November 2026 (GMT+7). Analysis, not financial advice."
    return piece, doc, asset, article


def check(values):
    piece, doc, asset, article = values
    return validate_retrospective_piece(
        piece, documents=[doc], chart_assets=[asset], article_text=article
    )


def test_announced_future_effective_policy_is_not_future_realized_data(prepared):
    assert check(prepared)["status"] == "PRIVATE_DATED_RECORD_VALIDATED"


def test_earlier_source_publication_is_allowed_when_known_before_cutoff(prepared):
    values = deepcopy(prepared)
    values[1]["published_at_utc"] = "2026-10-27T18:00:00Z"
    values[2]["source_links"] = media.editorial_chart_source_links(
        values[2]["editorial_data_packet"], [values[1]]
    )
    assert check(values)["status"] == "PRIVATE_DATED_RECORD_VALIDATED"


@pytest.mark.parametrize(
    "fault,expected",
    [
        ("written_date", "WRITTEN_BEFORE"),
        ("written_clock", "WRITTEN_BEFORE"),
        ("source_known", "POST_EVENT"),
        ("revision", "FACTUAL_REVISION"),
        ("rights", "RIGHTS_REQUIRED"),
        ("capture", "CHANGED_SOURCE"),
        ("window", "POST_EVENT_WINDOW"),
        ("point_time", "POST_EVENT_DATA"),
        ("point_period", "FUTURE_REALIZED"),
        ("series", "EXACT_SERIES"),
        ("chart_value", "COMPUTED_VALUE_CHANGED"),
        ("chart_capture", "CAPTURE_BINDING"),
        ("notice", "VISIBLE_NOTICE"),
        ("configured_as_observed", "CONFIGURATION_IS_NOT"),
        ("public_write", "PRIVATE_RECORD"),
    ],
)
def test_private_acceptance_rejects_material_faults(prepared, fault, expected):
    piece, doc, asset, article = values = deepcopy(prepared)
    if fault == "written_date":
        piece["written_on_gmt7"] = "2026-10-31"
    elif fault == "written_clock":
        piece["written_at_utc"] = "2026-10-31T05:30:00Z"
    elif fault == "source_known":
        piece["sources"][0]["original_known_at_utc"] = "2026-10-29T00:00:00Z"
    elif fault == "revision":
        piece["sources"][0]["factual_revision_at_utc"] = "2026-10-29T00:00:00Z"
    elif fault == "rights":
        doc["source_reuse_constraints"].pop("policy_capture_sha256")
    elif fault == "capture":
        piece["sources"][0]["capture_sha256"] = "0" * 64
    elif fault == "window":
        piece["charts"][0]["window_end_utc"] = "2026-10-29T00:00:00Z"
    elif fault == "point_time":
        piece["charts"][0]["point_times"][0]["as_of_utc"] = "2026-10-29T00:00:00Z"
    elif fault == "point_period":
        asset["editorial_data_packet"]["series"][0]["points"][0]["observation_kind"] = (
            "ACTUAL"
        )
        from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
            sha256_of,
        )

        asset["transform_sha256"] = sha256_of(asset["editorial_data_packet"])
    elif fault == "series":
        piece["charts"][0]["series_ids"] = ["UNBOUND"]
    elif fault == "chart_value":
        asset["editorial_data_packet"]["series"][0]["points"][0]["value"] = 4.1
    elif fault == "chart_capture":
        piece["charts"][0]["source_capture_hashes"]["CONTROLLED"] = "0" * 64
    elif fault == "notice":
        values = (piece, doc, asset, "No notices")
    elif fault == "configured_as_observed":
        piece["native_calls"][0]["model"] = "gpt-6.1-sol"
    elif fault == "public_write":
        piece["public_write_performed"] = True
    with pytest.raises(ValueError, match=expected):
        check(values)


def test_actual_drawn_geometry_matches_source_value(prepared):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    _, doc, asset, _ = prepared
    packet = asset["editorial_data_packet"]
    values = media._editorial_data_values(packet, [doc])
    fig = media._draw_editorial_chart(packet, values, plt, np)
    try:
        bars = fig.axes[0].patches
        assert len(bars) == 1 and bars[0].get_y() == 0
        assert bars[0].get_height() == pytest.approx(3.9)
        low = fig.axes[0].transData.transform((0, 0))[1]
        high = fig.axes[0].transData.transform((0, 3.9))[1]
        assert bars[0].get_window_extent().height == pytest.approx(high - low)
    finally:
        plt.close(fig)


def test_explicit_report_only_never_scans_live_x_and_ordinary_input_keeps_route(
    tmp_path, monkeypatch
):
    from tests.test_native_newsroom_owner_operation_v1 import entry
    from live_contentops import native_newsroom_learning_v1 as learning

    module = entry()
    monkeypatch.setattr(
        module, "load_canonical_published_memory_read_only", lambda **_: ([], {})
    )
    monkeypatch.setattr(learning, "freeze_learning", lambda *_a, **_k: None)
    observed = []

    class Feed:
        def __init__(self, *args, **kwargs):
            observed.append(kwargs)

        def opportunity(self, **kwargs):
            return {
                "classification": "CONTROLLED_ZERO_WRITE",
                "qualified_article_count": 0,
            }

    monkeypatch.setattr(module, "MainReportFeed", Feed)
    for report_only in (False, True):
        profile = {
            "schema_version": "contentops.native_desktop_operator_profile.v1",
            "editorial_output_root": str(tmp_path / "articles"),
            **{
                k: str(tmp_path / k)
                for k in (
                    "store_path",
                    "feed_pointer_path",
                    "published_memory_store",
                    "published_memory_output_root",
                )
            },
        }
        from pathlib import Path

        Path(profile["feed_pointer_path"]).write_text("{}")
        _, binding = module.resolve_owner_operation(
            profile,
            operation_id=f"controlled-report-{report_only}",
            request="Controlled no-transport test",
            report_only=report_only,
        )
        assert module.operation(binding)["classification"] == "CONTROLLED_ZERO_WRITE"
    assert "headline_paths" not in observed[0]
    assert observed[1]["headline_paths"] == []


def test_real_retained_chart_binding_and_rendered_geometry():
    """Real data are evidence; this re-renders only local deterministic figures."""
    from pathlib import Path
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    root = (
        Path(__file__).resolve().parents[1] / "docs/publisher/CC-074-private-20261101"
    )
    docs = json.loads((root / "source-packet.json").read_bytes())
    charts = json.loads((root / "chart-assets.json").read_bytes())
    for asset in charts:
        media.validate_editorial_data_chart(asset, docs)
        bound = media._retained_chart_documents(docs, asset["retained_source_binding"])
        packet = asset["editorial_data_packet"]
        values = media._editorial_data_values(packet, bound)
        fig = media._draw_editorial_chart(packet, values, plt, np)
        try:
            ax = fig.axes[0]
            if packet["chart_type"] == "horizontal_count_bar":
                assert ax.get_xlim()[0] == 0
                assert [bar.get_width() for bar in ax.patches] == [10, 2]
                assert all(bar.get_x() == 0 for bar in ax.patches)
            else:
                assert list(ax.lines[0].get_xdata()) == [3.75, 4.0]
                assert [float(c.get_offsets()[0, 0]) for c in ax.collections[1:]] == [
                    3.9,
                    3.75,
                    4.0,
                    4.0,
                ]
                assert list(ax.lines[0].get_ydata()) == [0, 0]
        finally:
            plt.close(fig)


@pytest.mark.parametrize(
    "fault", ["revision", "capture", "policy", "source_text", "fraction"]
)
def test_real_chart_cannot_rebind_source_or_rights(tmp_path, fault):
    from pathlib import Path
    import shutil

    root = (
        Path(__file__).resolve().parents[1] / "docs/publisher/CC-074-private-20261101"
    )
    docs = json.loads((root / "source-packet.json").read_bytes())
    asset = json.loads((root / "chart-assets.json").read_bytes())[1]
    binding = asset["retained_source_binding"]
    if fault == "revision":
        binding["research_revision"] = "0" * 64
    elif fault == "capture":
        binding["source_capture_hashes"][docs[0]["document_id"]] = "0" * 64
    elif fault == "policy":
        shutil.copytree(binding["research_root"], tmp_path / "source")
        binding["research_root"] = str(tmp_path / "source")
        (tmp_path / "source/fed-permission.json").write_text("CONTROLLED tamper")
    elif fault == "source_text":
        docs[0]["canonical_content_text"] += " Added later fact."
    else:
        asset["editorial_data_packet"]["series"][0]["points"][0]["value"] = 3.5
    with pytest.raises(ValueError):
        media.validate_editorial_data_chart(asset, docs)


def test_dated_writer_request_replays_exactly_but_changed_inputs_still_fail(tmp_path):
    from live_contentops.native_desktop_editorial_v1 import (
        NativeDesktopTurn,
        DesktopInputRequired,
    )
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

    turn = NativeDesktopTurn(
        ContentOpsDurableStore(tmp_path / "controlled.sqlite3"),
        run_id="CONTROLLED-dated-replay",
        output_dir=tmp_path / "article",
        owner_manual_validation=True,
    )
    turn.store.create_work_item(
        story_id=turn.work,
        work_item_id=turn.work,
        title="Controlled dated replay",
        target_surface="CONTENTOPS_EDITORIAL_ONLY",
    )
    turn.volume_policy = {"source_request_limit": 10}
    arguments = {
        "logical_invocation_id": "CONTROLLED-dated-replay:write",
        "prompt": "Controlled base prompt, not an article",
        "governed_input": {"controlled": 1},
        "validator": lambda raw: (True, None, json.loads(raw), None),
    }
    with pytest.raises(DesktopInputRequired) as first:
        turn(**arguments)
    with pytest.raises(DesktopInputRequired) as replay:
        turn(**arguments)
    assert (
        replay.value.request["request_sha256"] == first.value.request["request_sha256"]
    )
    assert first.value.request["prompt"].count("DATED J8:") == 1
    with pytest.raises(ValueError, match="IMMUTABLE_RETURN_CONFLICT"):
        turn(**{**arguments, "governed_input": {"controlled": 2}})


def test_real_retrospective_notice_and_bound_fed_attribution_survive_all_previews():
    from pathlib import Path
    from live_contentops.v1_simple_gemini_newsroom_v1 import (
        _native_preview_bundle,
        _reader_safe_native_article,
    )

    root = (
        Path(__file__).resolve().parents[1] / "docs/publisher/CC-074-private-20261101"
    )
    article = json.loads((root / "native/desktop_response_write.json").read_bytes())[
        "output"
    ]["article"]
    docs = json.loads((root / "source-packet.json").read_bytes())
    article["public_source_bindings"] = [
        {"source_id": d["source_id"], "publisher": d["publisher"], "url": d["url"]}
        for d in docs
    ]
    epistemic = {
        "reader_visible_epistemic_label": "CONFIRMED",
        "event_confirmation_state": "CONFIRMED",
        "primary_reporting_publisher": "Federal Reserve Board",
    }
    assets = json.loads((root / "chart-assets.json").read_bytes())
    bundle, _ = _native_preview_bundle(
        article=article,
        article_mode="DATA_OR_DOCUMENT_LENS",
        article_identity="a" * 64,
        epistemic_state=epistemic,
        media_asset_ids=[a["asset_id"] for a in assets],
        media_assets=assets,
    )
    assert len(bundle["packages"]) == 8
    for payload in bundle["packages"].values():
        text = payload.get("full_text") or payload["text"]
        import re

        assert re.search(r"\bFed\b", text)
        assert "Retrospective analysis, written on 1 November 2026 (GMT+7)" in " ".join(
            text.split()
        )
        assert "Analysis, not financial advice." in text
        if payload.get("posts"):
            assert all(
                len(p["text"]) <= payload["platform_limit"] for p in payload["posts"]
            )
    article["public_source_bindings"][0]["url"] = "https://wrong.example.test/"
    article["public_source_bindings"][1]["url"] = "https://wrong.example.test/"
    assert "native_source_attribution" not in _reader_safe_native_article(
        article, article_mode="DATA_OR_DOCUMENT_LENS", epistemic_state=epistemic
    )


def test_copied_manual_binding_refuses_publication_before_store_or_transport(tmp_path):
    from live_contentops.native_desktop_publication_v1 import (
        scheduled_publication_authority,
    )
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.native_desktop_workspace_v1 import workspace_snapshot

    store = ContentOpsDurableStore(tmp_path / "CONTROLLED-copy.sqlite3")
    before = workspace_snapshot(store.db_path)

    class ForbiddenStore:
        def get_outbox_message(self, *_args):
            pytest.fail(
                "Isolated copied binding reached publication state/transport preparation"
            )

    with pytest.raises(ValueError, match="OWNER_MANUAL_PUBLICATION_NOT_AUTHORIZED"):
        scheduled_publication_authority(
            ForbiddenStore(),
            {"owner_manual_validation": True, "run_id": "CONTROLLED-copy"},
            {"public_write_authority": True},
        )
    assert workspace_snapshot(store.db_path) == before


@pytest.mark.parametrize("fault", ["value", "unit", "missing_row"])
def test_accessible_table_cannot_change_source_values_or_units(fault):
    from pathlib import Path

    root = (
        Path(__file__).resolve().parents[1] / "docs/publisher/CC-074-private-20261101"
    )
    assets = json.loads((root / "repairs/v2/assets-reader-metadata.json").read_bytes())
    docs = json.loads((root / "source-packet.json").read_bytes())
    chart = next(a for a in assets if a.get("editorial_data_packet"))
    media.validate_editorial_data_chart(chart, docs)
    if fault == "value":
        chart["reader_table"]["rows"][0]["values"][0] = 100
    elif fault == "unit":
        chart["reader_table"]["unit"] = "percent"
    else:
        chart["reader_table"]["rows"].pop()
    with pytest.raises(ValueError, match="ACCESSIBLE_TABLE_VALUES_CHANGED"):
        media.validate_editorial_data_chart(chart, docs)


@pytest.mark.parametrize("fault", [None, "container", "first_call", "revised_value"])
def test_actual_private_piece_keeps_original_container_and_native_clock(
    tmp_path, fault
):
    from pathlib import Path
    import shutil

    root = (
        Path(__file__).resolve().parents[1] / "docs/publisher/CC-074-private-20261101"
    )
    piece = json.loads((root / "piece.json").read_bytes())
    docs = json.loads((root / "chart-source-documents.json").read_bytes())
    charts = [
        a
        for a in json.loads(
            (root / "repairs/v2/assets-reader-metadata.json").read_bytes()
        )
        if a.get("editorial_data_packet")
    ]
    article = (root / "article.md").read_text(encoding="utf-8")
    if fault == "container":
        source = piece["sources"][0]
        path = tmp_path / "capture.json"
        shutil.copyfile(source["representation_capture_path"], path)
        source["representation_capture_path"] = str(path)
        page = json.loads(path.read_bytes())
        page["representation_adapted_at_utc"] = "2026-11-02T00:00:00Z"
        path.write_text(json.dumps(page))
    elif fault == "first_call":
        piece["written_on_gmt7"] = "2026-10-31"
    elif fault == "revised_value":
        piece["sources"][0]["factual_revision_at_utc"] = "2026-10-29T00:00:00Z"
    if fault:
        with pytest.raises(ValueError):
            validate_retrospective_piece(
                piece, documents=docs, chart_assets=charts, article_text=article
            )
    else:
        result = validate_retrospective_piece(
            piece, documents=docs, chart_assets=charts, article_text=article
        )
        assert result["source_count"] == result["chart_count"] == 2


def test_existing_unanswered_visual_request_does_not_gain_new_owner_metadata(tmp_path):
    from pathlib import Path
    from tests.test_native_newsroom_owner_operation_v1 import entry
    from live_contentops.native_desktop_editorial_v1 import (
        NativeDesktopTurn,
        DesktopInputRequired,
    )
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.native_newsroom_volume_v1 import configure_volume_turn

    module = entry()
    profile = {
        "schema_version": "contentops.native_desktop_operator_profile.v1",
        "editorial_output_root": str(tmp_path / "articles"),
        **{
            k: str(tmp_path / k)
            for k in (
                "store_path",
                "feed_pointer_path",
                "published_memory_store",
                "published_memory_output_root",
            )
        },
    }
    _, binding = module.resolve_owner_operation(
        profile,
        operation_id="controlled-legacy-visual",
        request="Controlled retained owner question, no article proof.",
    )
    root = Path(binding["output_dir"])
    governed = {
        "source_pack": [],
        "instruction": "Controlled pre-existing packet without owner request",
    }
    (root / "editorial_media_plan_required.json").write_text(json.dumps(governed))
    pending = module.operation(binding, command="media-plan")
    turn = NativeDesktopTurn(
        ContentOpsDurableStore(binding["store_path"]),
        run_id=binding["run_id"],
        output_dir=root,
        owner_manual_validation=True,
    )
    configure_volume_turn(turn, binding)
    response = {
        "request_sha256": pending["request_sha256"],
        "output": {"story_plan": {"controlled": True}},
        "invocation_observation": {
            "surface": "CODEX_NATIVE_SUBAGENT",
            "model": "gpt-6.1-sol",
            "reasoning_effort": "low",
            "invocation_id": "/root/CONTROLLED_NOT_REAL",
            "observation_source": "Controlled test observation, not a native run",
        },
    }
    module.operation(binding, command="submit", stage="media-plan", response=response)
    preparation = {
        "native_plan_run_id": binding["run_id"],
        "native_plan_stage": "media-plan",
        "native_plan_request_sha256": pending["request_sha256"],
        "story_plan": response["output"]["story_plan"],
    }
    with pytest.raises(DesktopInputRequired) as old:
        turn.request_visual_decision(source_packet=governed, preparation=preparation)
    replay = module.operation(binding, command="media-plan")
    assert replay["request_sha256"] == old.value.request["request_sha256"]
    assert (
        "owner_editorial_request"
        not in turn.frozen_request("visual-edit")["governed_input"]["source_packet"]
    )
