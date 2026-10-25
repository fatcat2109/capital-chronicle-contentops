"""Controlled regression evidence; these tests never stand in for editorial judgment."""

from copy import deepcopy
from hashlib import sha256
import json
import pytest

from live_contentops.native_desktop_editorial_v1 import (
    NativeDesktopTurn,
    DesktopInputRequired,
    validate_visual_decision,
    validate_release_media,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    _reader_safe_native_article,
    _worker_prompt,
    SimpleGeminiNewsroomError,
    _selected_news_peg_blockers,
    reader_photo_caption,
)
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    _editorial_data_values,
    build_editorial_data_chart,
)
from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import (
    build_native_derivative_payloads,
)


def decision(kind="ANALYSIS", count=2):
    return {
        "reader_first_version": "DATA_JOURNALISM_V1",
        "story_kind": kind,
        "editorial_thesis": "Controlled argument, never actual story acceptance.",
        "channel_media": {d: ["controlled-distinct-0"] if count else [] for d in (
            "telegram", "discord", "x", "linkedin", "facebook_page", "instagram_business", "threads", "youtube")},
        "charts": [
            {
                "asset_id": f"controlled-distinct-{i}",
                "question": f"Distinct question {i}",
                "why_useful": "Controlled contract",
                "placement_after": f"Section {i}",
                "data_spec": {"controlled": True},
            }
            for i in range(count)
        ],
    }


def chart_packet():
    text = "Comparable 2025 revenue 100 USD million; 2026 revenue 120 USD million."
    doc = {
        "document_id": "controlled",
        "url": "https://example.org/source",
        "publisher": "Controlled fixture",
        "canonical_content_text": text,
        "source_reuse_constraints": {
            "attribution_required": True,
            "policy_capture_sha256": "a" * 64,
            "source_capture_sha256": "b" * 64,
        },
    }
    points = []
    for i, (period, value) in enumerate((("2025", 100), ("2026", 120))):
        points.append(
            {
                "period": period,
                "value": value,
                "observation_kind": "REPORTED_ACTUAL",
                "inputs": [
                    {
                        "document_id": "controlled",
                        "support_excerpt": text,
                        "value_text": str(value),
                        "source_period_text": period,
                        "source_content_sha256": sha256(text.encode()).hexdigest(),
                        "metric": "Revenue",
                        "unit": "USD million",
                        "prepared_period": period,
                        "binding_basis": "ACTUAL_LIGHT_EXACT_SERIES_AND_PERIOD_INDEX",
                        "period_basis": {
                            "series_periods": ["2025", "2026"],
                            "period_index": i,
                            "prepared_value": value,
                            "series_sha256": "c" * 64,
                        },
                    }
                ],
            }
        )
    return {
        "asset_id": "controlled-dj-chart-r1",
        "chart_type": "grouped_bar",
        "question": "Controlled persistence question",
        "title": "Controlled fixture, no editorial acceptance",
        "unit": "USD million",
        "series": [{"name": "Revenue", "points": points}],
        "source_caption": "Source: controlled fixture, not real data.",
        "missingness": [],
    }, [doc]


def test_analytical_one_chart_holds_and_explicit_news_zero_is_valid():
    with pytest.raises(ValueError, match="TWO_TO_FIVE"):
        validate_visual_decision(decision(count=1))
    news = decision("NEWS", 0)
    with pytest.raises(ValueError, match="EXCEPTION_REASON"):
        validate_visual_decision(news)
    news["exception_reason"] = (
        "A narrow attributed announcement has no defensible useful quantitative comparison."
    )
    with pytest.raises(ValueError, match="INSTAGRAM_REQUIRES_EDITOR_SELECTED_IMAGE"):
        validate_visual_decision(news)
    news["contextual_photo_ids"] = ["controlled-photo"]
    news["channel_media"]["instagram_business"] = ["controlled-photo"]
    assert validate_visual_decision(news) == news
    duplicate = decision()
    duplicate["charts"][1]["asset_id"] = duplicate["charts"][0]["asset_id"]
    with pytest.raises(ValueError, match="DISTINCT"):
        validate_visual_decision(duplicate)
    with pytest.raises(ValueError, match="MAX_VISUAL"):
        validate_release_media(
            {"article": {"reader_first_version": "DATA_JOURNALISM_V1"}}
        )


def test_original_chart_values_units_periods_and_source_hash_fail_closed(tmp_path):
    packet, docs = chart_packet()
    assert _editorial_data_values(packet, docs) == [[100, 120]]
    for field, value, error in (
        ("unit", "GBP million", "DIMENSION"),
        ("value_text", "20", "EXACT_VALUE"),
        ("prepared_period", "2024", "PREPARED_PERIOD"),
        ("source_content_sha256", "d" * 64, "HASH"),
    ):
        bad = deepcopy(packet)
        bad["series"][0]["points"][1]["inputs"][0][field] = value
        with pytest.raises(ValueError, match=error):
            _editorial_data_values(bad, docs)
    asset = build_editorial_data_chart(packet, docs, output_dir=tmp_path)
    changed = deepcopy(packet)
    changed["title"] = "Changed packet must use distinct identity"
    with pytest.raises(ValueError, match="ID_ALREADY_BOUND"):
        build_editorial_data_chart(changed, docs, output_dir=tmp_path)
    other = deepcopy(packet)
    other["asset_id"] = "controlled-second-chart-r1"
    second = build_editorial_data_chart(other, docs, output_dir=tmp_path)
    assert asset["path"] != second["path"]


def test_compact_authored_links_retain_distinct_sources_and_internal_markers():
    article = {
        "reader_first_version": "DATA_JOURNALISM_V1",
        "title": "Controlled title",
        "dek": "Controlled dek",
        "source_date_notice": "Source date internal. Interpretation remains analysis.",
        "substack_body_markdown": "First [[CITE:SOURCE_1|company release]] says a fact. [[SOURCE:SOURCE_1]]\n\n### Cash\n\nSecond source-bound paragraph. [[SOURCE:SOURCE_1]]\n\nPrior comparison. [[SOURCE:SOURCE_2]]",
        "public_source_bindings": [
            {
                "source_id": f"SOURCE_{i}",
                "url": f"https://example.org/{i}",
                "publisher": "Company",
                "reader_label": f"Company Q{i}",
            }
            for i in (1, 2)
        ],
    }
    before = deepcopy(article)
    public = _reader_safe_native_article(article, article_mode="DATA_OR_DOCUMENT_LENS")
    assert article == before
    body = public["substack_body_markdown"]
    assert body.count("https://example.org/1") == 2
    assert "[company release]" in body and "### Cash" in body and "### Sources" in body
    assert (
        "[[SOURCE:" not in body
        and "[[CITE:" not in body
        and "Interpretation remains" not in body
    )
    assert "Source date" not in public["editorial_scope_notice"]
    bad = deepcopy(article)
    bad["substack_body_markdown"] = "[[CITE:SOURCE_8|unbound phrase]]"
    with pytest.raises(SimpleGeminiNewsroomError):
        _reader_safe_native_article(bad, article_mode="DATA_OR_DOCUMENT_LENS")
    with_notes = {**article, "substack_body_markdown": article["substack_body_markdown"]
        + "\n\n## Sources and notes\n\nCompany-defined cash measure. [[SOURCE:SOURCE_1]]"}
    notes_body = _reader_safe_native_article(with_notes, article_mode="DATA_OR_DOCUMENT_LENS")["substack_body_markdown"]
    assert notes_body.count("Sources") == 1
    assert "Company-defined cash measure." in notes_body
    assert "Company Q1" in notes_body and "Company Q2" in notes_body
    linked_notes = {**article, "substack_body_markdown": article["substack_body_markdown"]
        + "\n\n## Sources and notes\n\n[[CITE:SOURCE_1|Current results]] and [[CITE:SOURCE_2|Prior results]]. [[SOURCE:SOURCE_1]] [[SOURCE:SOURCE_2]]"}
    linked_body = _reader_safe_native_article(linked_notes, article_mode="DATA_OR_DOCUMENT_LENS")["substack_body_markdown"]
    assert linked_body.count("Sources") == 1
    assert "Company Q1" not in linked_body and "Company Q2" not in linked_body
    assert "[Current results](https://example.org/1)" in linked_body
    data_notes = {**linked_notes, "substack_body_markdown": linked_notes["substack_body_markdown"].replace(
        "## Sources and notes", "## Sources and data notes")}
    data_body = _reader_safe_native_article(data_notes, article_mode="DATA_OR_DOCUMENT_LENS")["substack_body_markdown"]
    assert data_body.count("Sources") == 1
    assert "Company Q1" not in data_body and "Company Q2" not in data_body


def test_reader_photo_caption_retains_archive_date_and_original_evidence():
    asset = {"caption": "Company headquarters. Archive context image; Commons DateTimeOriginal records 2022-03-27 17:48:57."}
    before = deepcopy(asset)
    assert reader_photo_caption(asset) == "Company headquarters. Archival photograph dated 2022-03-27."
    assert asset == before
    caption = "Archive context, not a photograph of current trading."
    assert reader_photo_caption({"caption": caption}) == caption


@pytest.mark.parametrize("publisher,source_url,short_name", [
    ("Federal Reserve Bank of New York", "https://www.newyorkfed.org/markets/reference-rates/effr", "New York Fed"),
    ("U.S. Energy Information Administration", "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx", "EIA"),
])
def test_native_packages_keep_bound_short_publisher_attribution_without_machine_labels(publisher, source_url, short_name):
    from live_contentops.v1_simple_gemini_newsroom_v1 import _native_preview_bundle

    article = {"title": "Controlled overnight comparison", "dek": "The New York Fed reports a steady median.",
        "social_hook": "The New York Fed reports a steady median.",
        "social_mechanism_summary": "A median does not describe every transaction.",
        "social_policy_summary": "A funding observation does not forecast policy.",
        "social_cross_asset_summary": "The next observation tests persistence.",
        "substack_body_markdown": "The New York Fed reports a steady median. [[SOURCE:SOURCE_1]]",
        "reader_first_version": "DATA_JOURNALISM_V1", "visual_editorial_decision": decision(),
        "public_source_bindings": [{"source_id": "SOURCE_1", "publisher": "Federal Reserve Bank of New York",
            "url": "https://www.newyorkfed.org/markets/reference-rates/effr"}]}
    state = {"primary_reporting_publisher": "Federal Reserve Bank of New York",
        "reader_visible_epistemic_label": "CONFIRMED", "event_confirmation_state": "CONFIRMED"}
    article["public_source_bindings"][0].update(publisher=publisher, url=source_url)
    for key in ("dek", "social_hook", "substack_body_markdown"):
        article[key] = article[key].replace("New York Fed", short_name)
    state["primary_reporting_publisher"] = publisher
    before = deepcopy(article)
    bundle, intents = _native_preview_bundle(article=article, article_mode="DATA_OR_DOCUMENT_LENS",
        article_identity="controlled-not-dispatched", epistemic_state=state,
        media_asset_ids=["controlled-distinct-0", "controlled-distinct-1"])
    assert article == before
    assert len(intents) == bundle["package_count"] == 8
    for destination, payload in bundle["packages"].items():
        text = "\n".join(str(v) for k, v in payload.items() if k in {"text", "full_text", "root_text"})
        assert short_name in text and "CONFIRMED" not in text
        assert payload["media_asset_ids"] == ["controlled-distinct-0"]
        if destination in {"linkedin", "threads"}:
            assert f"Source: {short_name}." in text
    canonical_input = _reader_safe_native_article(article, article_mode="DATA_OR_DOCUMENT_LENS", epistemic_state=state)
    for canonical_url in ("https://example.org/p/pending", "https://example.org/p/read-back"):
        rematerialized = build_native_derivative_payloads(article=canonical_input, selection={},
            canonical_url=canonical_url, media_asset_ids=["controlled-distinct-0", "controlled-distinct-1"])
        for destination in ("linkedin", "threads"):
            visible = rematerialized[destination].get("full_text") or rematerialized[destination]["text"]
            assert f"Source: {short_name}." in visible
            assert rematerialized[destination]["media_asset_ids"] == ["controlled-distinct-0"]
    unbound = {**article, "public_source_bindings": []}
    with pytest.raises(SimpleGeminiNewsroomError, match="epistemic_state_missing"):
        _native_preview_bundle(article=unbound, article_mode="DATA_OR_DOCUMENT_LENS",
            article_identity="controlled-not-dispatched", epistemic_state=state,
            media_asset_ids=["controlled-distinct-0", "controlled-distinct-1"])
    inflated = {**article, "social_policy_summary": "Confirmed funding stress has arrived."}
    with pytest.raises(SimpleGeminiNewsroomError, match="epistemic_certainty_inflation"):
        _native_preview_bundle(article=inflated, article_mode="DATA_OR_DOCUMENT_LENS",
            article_identity="controlled-not-dispatched", epistemic_state={**state, "event_confirmation_state": "UNCONFIRMED"},
            media_asset_ids=["controlled-distinct-0", "controlled-distinct-1"])


def test_review_binds_actual_public_conversion_and_all_reader_first_previews(monkeypatch):
    from live_contentops.native_desktop_editorial_v1 import native_review_revision
    import live_contentops.v1_simple_gemini_newsroom_v1 as newsroom
    result = {"article_identity": "controlled-article", "article": {
        "title": "Controlled", "reader_first_version": "DATA_JOURNALISM_V1",
        "substack_body_markdown": "Controlled original text.", "visual_editorial_decision": decision()},
        "previews": [{"destination": "x", "payload": {"text": "Controlled preview"}}],
        "simple_result": {"publication_lifecycle_plan": {"plan_hash": "controlled-plan"}}}
    initial = native_review_revision(result)
    changed = deepcopy(result)
    changed["previews"][0]["payload"]["text"] = "Changed after review"
    assert native_review_revision(changed) != initial
    converter = newsroom._reader_safe_native_article
    monkeypatch.setattr(newsroom, "_reader_safe_native_article", lambda *a, **kw: {
        **converter(*a, **kw), "substack_body_markdown": "Different public conversion"})
    assert native_review_revision(result) != initial


def test_native_max_visual_return_restart_and_same_writer_binding(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "controlled.sqlite3")
    run = "controlled-reader-first"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(
        story_id=work,
        work_item_id=work,
        title="Controlled",
        target_surface="CONTENTOPS_EDITORIAL_ONLY",
    )
    turn = NativeDesktopTurn(
        store, run_id=run, output_dir=tmp_path, owner_manual_validation=True
    )
    with pytest.raises(DesktopInputRequired) as pending:
        turn(
            logical_invocation_id=run + ":visual-edit",
            governed_input={},
            prompt="Controlled visual input",
            validator=lambda raw: (True, None, json.loads(raw), None),
        )
    observation = {
        "surface": "CODEX_NATIVE_SUBAGENT",
        "model": "gpt-6.1-sol",
        "reasoning_effort": "max",
        "invocation_id": "controlled-context",
        "observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF",
    }
    envelope = {
        "request_sha256": pending.value.request["request_sha256"],
        "output": decision(),
        "invocation_observation": observation,
    }
    turn.submit("visual-edit", envelope)
    restarted = NativeDesktopTurn(
        store, run_id=run, output_dir=tmp_path, owner_manual_validation=True
    )
    assert restarted._get("visual-edit", "response")["output"] == decision()
    turn._put(
        "write",
        "request",
        {
            "request_sha256": "controlled-write",
            "governed_input": {},
            "prompt": "controlled",
        },
    )
    with pytest.raises(ValueError, match="SAME_VISUAL_EDITOR_WRITER"):
        turn.submit(
            "write",
            {
                "request_sha256": "controlled-write",
                "output": {},
                "invocation_observation": {
                    **observation,
                    "invocation_id": "different-context",
                },
            },
        )
    assert "READER_FIRST_DATA_JOURNALISM" in _worker_prompt(
        {"reader_first_version": "DATA_JOURNALISM_V1"}
    )
    assert "READER_FIRST_DATA_JOURNALISM" not in _worker_prompt({})


def test_actual_native_compiler_retains_distinct_subsets_after_canonical_readback():
    destinations = [
        "telegram",
        "discord",
        "x",
        "linkedin",
        "facebook_page",
        "instagram_business",
        "threads",
        "youtube",
    ]
    choices = {
        d: ["chart-a"] if i % 2 == 0 else ["chart-b", "chart-c"]
        for i, d in enumerate(destinations)
    }
    article = {
        "title": "Controlled cash comparison",
        "subtitle": "Cash conversion differs from profitability.",
        "social_hook": "Investment absorbed the cash inflow.",
        "social_mechanism_summary": "Investment absorbed the cash inflow.",
        "social_policy_summary": "The next comparable quarter tests persistence.",
        "social_cross_asset_summary": "Compare spending with operating cash.",
        "substack_body_markdown": "A source-bound controlled comparison, never a real article.",
        "native_brief_layout": True,
        "reader_first_version": "DATA_JOURNALISM_V1",
        "native_destination_media": choices,
        "native_destination_credits": {},
    }
    pending = build_native_derivative_payloads(
        article=article,
        selection={},
        canonical_url="https://capitalchronicle.substack.com/p/pending-publication-control",
        media_asset_ids=["chart-a", "chart-b", "chart-c"],
    )
    observed = build_native_derivative_payloads(
        article=article,
        selection={},
        canonical_url="https://capitalchronicle.substack.com/p/actual-controlled-readback",
        media_asset_ids=["chart-a", "chart-b", "chart-c"],
    )
    assert len(pending) == len(observed) == 8
    for destination in destinations:
        assert (
            pending[destination]["media_asset_ids"]
            == observed[destination]["media_asset_ids"]
            == choices[destination]
        )
        posts = observed[destination].get("posts", [])
        if posts:
            assert posts[0]["media_asset_ids"] == choices[destination]
            assert all(not p["media_asset_ids"] for p in posts[1:])
    bad = deepcopy(article)
    bad["native_destination_media"]["x"] = ["unbound-chart"]
    with pytest.raises(ValueError, match="SUBSET_UNBOUND"):
        build_native_derivative_payloads(
            article=bad,
            selection={},
            canonical_url="https://example.org/actual",
            media_asset_ids=["chart-a"],
        )
    empty_instagram = deepcopy(article)
    empty_instagram["native_destination_media"]["instagram_business"] = []
    with pytest.raises(ValueError, match="INSTAGRAM_IMAGE_REQUIRED"):
        build_native_derivative_payloads(article=empty_instagram, selection={},
            canonical_url="https://example.org/actual", media_asset_ids=["chart-a", "chart-b", "chart-c"])


def test_one_prewrite_visual_amendment_preserves_original_and_same_editor(tmp_path, monkeypatch):
    import live_contentops.visual_asset_discovery_v1 as photos
    monkeypatch.setattr(photos, "validate_contextual_photo", lambda asset: None)
    store = ContentOpsDurableStore(tmp_path / "controlled.sqlite3")
    run = "controlled-visual-amendment"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)
    with pytest.raises(DesktopInputRequired) as pending:
        turn(logical_invocation_id=run + ":visual-edit", governed_input={}, prompt="Controlled",
            validator=lambda raw: (True, None, json.loads(raw), None))
    observation = {"surface": "CODEX_NATIVE_SUBAGENT", "model": "gpt-6.1-sol", "reasoning_effort": "max",
        "invocation_id": "controlled-same-editor", "observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF"}
    turn.submit("visual-edit", {"request_sha256": pending.value.request["request_sha256"],
        "output": decision(), "invocation_observation": observation})
    original = turn._get("visual-edit", "response")
    with pytest.raises(DesktopInputRequired) as amended_request:
        turn.request_visual_amendment(reason="Instagram requires a suitable exact selected image.",
            contextual_assets=[{"asset_id": "controlled-photo"}])
    with pytest.raises(DesktopInputRequired):
        turn(logical_invocation_id=run + ":write", governed_input={}, prompt="Controlled",
            validator=lambda raw: (True, None, json.loads(raw), None))
    amended = decision("NEWS", 0)
    amended["exception_reason"] = "Controlled genuine news needs no quantitative comparison."
    amended["contextual_photo_ids"] = ["controlled-photo"]
    amended["channel_media"]["instagram_business"] = ["controlled-photo"]
    envelope = {"request_sha256": amended_request.value.request["request_sha256"], "output": amended,
        "invocation_observation": {**observation, "invocation_id": "different-editor"}}
    with pytest.raises(ValueError, match="SAME_PREWRITER_VISUAL_EDITOR"):
        turn.submit("visual-edit-amend", envelope)
    turn.submit("visual-edit-amend", {**envelope, "invocation_observation": observation})
    restarted = NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)
    assert restarted.visual_response()["output"] == amended
    assert restarted._get("visual-edit", "response") == original
    turn._put("write", "request", {"request_sha256": "controlled-write", "governed_input": {}, "prompt": "Controlled"})
    with pytest.raises(ValueError, match="UNBOUND_PREWRITER_VISUAL_AMENDMENT"):
        turn.request_visual_amendment(reason="A later amendment cannot replace frozen writer evidence.",
            contextual_assets=[{"asset_id": "controlled-photo"}])


def test_light_proposal_requires_actual_bound_return_before_max_visual_request(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "controlled.sqlite3")
    run = "controlled-light-then-max"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)
    with pytest.raises(DesktopInputRequired) as pending:
        turn(logical_invocation_id=run + ":media-plan", governed_input={}, prompt="Controlled Light",
            validator=lambda raw: (True, None, json.loads(raw), None))
    preparation = {"native_plan_run_id": run, "native_plan_stage": "media-plan",
        "native_plan_request_sha256": pending.value.request["request_sha256"],
        "story_plan": {"thesis": "Controlled proposal", "exact_series": []}}
    with pytest.raises(ValueError, match="COMPLETED_LIGHT_PREPARATION"):
        turn.request_visual_decision(source_packet={"controlled": True}, preparation=preparation)
    turn.submit("media-plan", {"request_sha256": preparation["native_plan_request_sha256"],
        "output": {"story_plan": preparation["story_plan"]}, "invocation_observation": {
            "surface": "CODEX_NATIVE_SUBAGENT", "model": "gpt-6.1-sol", "reasoning_effort": "low",
            "invocation_id": "controlled-light", "observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF"}})
    with pytest.raises(DesktopInputRequired) as visual:
        turn.request_visual_decision(source_packet={"controlled": True}, preparation=preparation)
    assert visual.value.request["stage"] == "visual-edit"
    assert visual.value.request["requested_reasoning_effort"] == "max"
    assert visual.value.request["governed_input"]["actual_light_preparation"] == preparation
    altered = deepcopy(preparation)
    altered["story_plan"]["thesis"] = "Unreturned replacement"
    with pytest.raises(ValueError, match="COMPLETED_LIGHT_PREPARATION"):
        turn.request_visual_decision(source_packet={}, preparation=altered)


def test_normal_media_entry_resumes_completed_light_and_same_max_without_refreezing(tmp_path):
    from scripts.run_native_desktop_editorial import operation, BINDING_SCHEMA

    root = tmp_path / "reader"
    root.mkdir()
    binding = {"schema_version": BINDING_SCHEMA, "run_id": "controlled-normal-media-entry",
        "store_path": str(tmp_path / "controlled.sqlite3"), "output_dir": str(root),
        "feed_pointer_path": str(tmp_path / "unused-feed.json"),
        "published_memory_store": str(tmp_path / "unused-memory.sqlite3"),
        "published_memory_output_root": str(tmp_path / "unused-memory"), "owner_manual_validation": True}
    (root / "editorial_media_plan_required.json").write_text(json.dumps({"source_pack": []}))
    light_pending = operation(binding, command="media-plan")
    assert light_pending["stage"] == "media-plan"
    store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
    turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=root, owner_manual_validation=True)
    frozen_light = turn.frozen_request("media-plan")
    turn.submit("media-plan", {"request_sha256": light_pending["request_sha256"],
        "output": {"story_plan": {"thesis": "Controlled proposal", "exact_series": []}},
        "invocation_observation": {"surface": "CODEX_NATIVE_SUBAGENT", "model": "gpt-6.1-sol",
            "reasoning_effort": "low", "invocation_id": "controlled-light",
            "observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF"}})
    visual_pending = operation(binding, command="media-plan")
    assert visual_pending["stage"] == "visual-edit"
    assert turn.frozen_request("visual-edit")["requested_reasoning_effort"] == "max"
    turn.submit("visual-edit", {"request_sha256": visual_pending["request_sha256"], "output": decision(),
        "invocation_observation": {"surface": "CODEX_NATIVE_SUBAGENT", "model": "gpt-6.1-sol",
            "reasoning_effort": "max", "invocation_id": "controlled-same-max",
            "observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF"}})
    # The existing writer may now emit a richer pending media request. That is not new Light input.
    (root / "editorial_media_plan_required.json").write_text(json.dumps({
        "source_pack": [], "visual_editorial_decision": decision(), "visual_request_sha256": visual_pending["request_sha256"]}))
    resumed = operation(binding, command="media-plan")
    assert resumed["classification"] == "NATIVE_VISUAL_PLAN_RETURNED_ASSETS_REQUIRED"
    assert turn.frozen_request("media-plan") == frozen_light
    assert turn._get("visual-edit", "response")["output"] == decision()


def _save_json(path, value):
    raw = json.dumps(value, ensure_ascii=False).encode()
    path.write_bytes(raw)
    return sha256(raw).hexdigest()


def _controlled_primaries(root):
    """Portable synthetic captures, never admitted evidence for the real edition."""
    root.mkdir(parents=True, exist_ok=True)
    policy_text = ("Copyright does not protect facts, but may protect the way these things are expressed.")
    policy = {"status": "PASS", "final_url": "https://www.copyright.gov/help/faq/faq-protect.html",
        "retrieval_method": "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE", "content_truncated": False,
        "rendered_markdown": policy_text, "rendered_page_sha256": sha256(policy_text.encode()).hexdigest(),
        "canonical_content_text": policy_text, "canonical_content_sha256": sha256(policy_text.encode()).hexdigest(),
        "credential_or_session_material_read": False, "public_write_performed": False,
        "fixture_only": "CONTROLLED_TEST_NOT_REAL_SOURCE"}
    policy_hash = _save_json(root / "policy.json", policy)
    sources = [
        ("controlled-effr", "https://www.newyorkfed.org/markets/reference-rates/controlled-fixture",
         "Controlled overnight rate observations", "Federal Reserve Bank of New York", "ORIGINAL_DATA_PRODUCER"),
        ("controlled-eia", "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?controlled-fixture",
         "Controlled commercial crude-stock observations", "U.S. Energy Information Administration", "ORIGINAL_DATA_PRODUCER"),
        ("controlled-binary", "https://ir.tesla.com/_flysystem/s3/sec/controlled-fixture.pdf",
         "Controlled quarterly filing facts", "Tesla", "ISSUER"),
        ("controlled-issuer", "https://investors.southwest.com/news-events/press-releases/detail/controlled-fixture",
         "SOUTHWEST CONTROLLED RESULTS: STRATEGY DRIVES MARGIN EXPANSION", "Southwest Airlines", "ISSUER"),
    ]
    records = []
    for identity, url, title, publisher, role in sources:
        text = title + "\nControlled fixture only: reported revenue 100 in 2025 and 120 in 2026, USD million."
        original = {"url": url, "text": text, "observed": "2026-10-24T12:00:00Z"}
        if identity == "controlled-binary":
            binary = b"CONTROLLED_BINARY_FIXTURE_NOT_A_REAL_FILING"
            (root / "controlled.bin").write_bytes(binary)
            original["binary_capture"] = {"path": "controlled.bin", "sha256": sha256(binary).hexdigest(),
                "extracted_text_sha256": sha256(text.encode()).hexdigest()}
        original_path = identity + "-original.json"
        original_hash = _save_json(root / original_path, original)
        capture_path = identity + "-capture.json"
        capture = {"status": "PASS", "url": url, "canonical_content_text": text,
            "source_capture_sha256": original_hash, "public_write_performed": False,
            "credential_or_session_material_read": False, "observed_at_utc": original["observed"],
            "excerpts": [{"start": 0, "end": len(text), "text": text}]}
        capture_hash = _save_json(root / capture_path, capture)
        document = {"document_id": identity, "title": title, "publisher": publisher, "source_url": url,
            "source_interest_role": role, "source_adapter_family": "original_public_facts",
            "source_authority_class": "first_party_public_source" if role == "ISSUER" else "official_public_primary_source",
            "canonical_content_text": text, "canonical_content_sha256": sha256(text.encode()).hexdigest(),
            "raw_sha256": capture_hash, "content_truncated": False, "published_at_utc": "2026-10-23T12:00:00Z"}
        loader_path = identity + "-loader.json"
        _save_json(root / loader_path, {"status": "PASS", "official_source_documents": [document],
            "provenance": {"retrieved_at_utc": original["observed"]}})
        spec = {"headline_id": identity, "headline_text": title, "capture_path": capture_path,
            "loader_result_path": loader_path, "original_capture_path": original_path,
            "original_capture_sha256": original_hash, "source_capture_sha256": capture_hash,
            "authorship_class": "ORIGINAL_PUBLIC_FACTS_ONLY", "public_expression_reuse_allowed": False,
            "policy_url": policy["final_url"], "policy_capture_path": "policy.json",
            "policy_capture_sha256": policy_hash, "policy_retrieved_at_utc": "2026-10-24T12:00:00Z",
            "revision_at_utc": "2026-10-24T13:00:00Z", "proposition_span": [0, len(title)]}
        if identity in {"controlled-effr", "controlled-eia"}:
            terms_path = identity + "-terms.json"
            if identity == "controlled-effr":
                terms_url = "https://www.newyorkfed.org/privacy/termsofuse"
                terms_hash = _save_json(root / terms_path, {"url": terms_url, "text":
                    "Controlled terms: personal or business purposes; modify and create derivative works; "
                    "must include any copyright notice."})
            else:
                terms_url = "https://www.eia.gov/about/copyrights_reuse.php"
                raw = b"Controlled terms: public domain; you may use and/or distribute; protected materials excluded."
                (root / terms_path).write_bytes(raw)
                terms_hash = sha256(raw).hexdigest()
            spec["data_terms"] = {"capture_path": terms_path, "sha256": terms_hash, "url": terms_url}
        records.append(spec)
    index = {"schema_version": "contentops.retained_source_research.v1", "records": records}
    _save_json(root / "index.json", index)
    return index


def test_original_primary_admission_preserves_exact_sources_and_facts_only_scope(tmp_path):
    _controlled_primaries(tmp_path)
    result = RetainedSourceResearch(tmp_path)
    assert len(result.records) == 4 and not result.gaps
    for record in result.records.values():
        permissions = record["source_permissions"]
        assert permissions["public_expression_reuse_allowed"] is False
        assert permissions["images_logos_exhibits_reuse_allowed"] is False
        assert permissions["attribution_required"] is True
    assert result.records["controlled-effr"]["source_permissions"]["data_terms"]["endorsement_granted"] is False


def _isolated_primary(root, headline_id):
    index = _controlled_primaries(root)
    spec = next(r for r in index["records"] if r["headline_id"] == headline_id)
    index["records"] = [spec]
    return index, spec


@pytest.mark.parametrize("mutation,expected", [
    ("expression", "ORIGINAL_FACTS_CAPTURE_INVALID"),
    ("canonical_hash", "ORIGINAL_FACTS_CAPTURE_INVALID"),
    ("source_identity", "ORIGINAL_FACTS_SOURCE_IDENTITY_CHANGED"),
    ("original_bytes", "ORIGINAL_FACTS_SOURCE_BYTES_CHANGED"),
    ("future_clock", "RESEARCH_CLOCK_ORDER_INVALID"),
    ("restricted_terms", "ORIGINAL_DATA_TERMS_NOT_VERIFIED"),
    ("binary_bytes", "ORIGINAL_FACTS_BINARY_OR_EXTRACTION_CHANGED"),
    ("third_party_series", "ORIGINAL_DATA_PRODUCER_IS_THIRD_PARTY_RIGHTS_NOT_ADMITTED"),
])
def test_original_primary_admission_rejects_material_boundary_tampering(tmp_path, mutation, expected):
    headline = "controlled-binary" if mutation == "binary_bytes" else "controlled-eia" if mutation == "third_party_series" else "controlled-effr"
    index, spec = _isolated_primary(tmp_path, headline)
    capture_path = tmp_path / spec["capture_path"]
    loader_path = tmp_path / spec["loader_result_path"]
    original_path = tmp_path / spec["original_capture_path"]
    capture = json.loads(capture_path.read_bytes())
    loader = json.loads(loader_path.read_bytes())
    original = json.loads(original_path.read_bytes())
    if mutation == "expression":
        spec["public_expression_reuse_allowed"] = True
    elif mutation == "canonical_hash":
        loader["official_source_documents"][0]["canonical_content_sha256"] = "0" * 64
        _save_json(loader_path, loader)
    elif mutation == "original_bytes":
        original_path.write_bytes(original_path.read_bytes() + b" ")
    elif mutation == "future_clock":
        loader["provenance"]["retrieved_at_utc"] = "2026-10-26T00:00:00Z"
        _save_json(loader_path, loader)
    elif mutation == "restricted_terms":
        terms_path = tmp_path / spec["data_terms"]["capture_path"]
        terms = json.loads(terms_path.read_bytes())
        terms["text"] = "No commercial use or derivatives allowed."
        spec["data_terms"]["sha256"] = _save_json(terms_path, terms)
    elif mutation == "binary_bytes":
        binary = tmp_path / original["binary_capture"]["path"]
        binary.write_bytes(binary.read_bytes() + b"tampered")
    elif mutation in {"source_identity", "third_party_series"}:
        if mutation == "source_identity":
            original["url"] = "https://www.newyorkfed.org/markets/different-source"
        else:
            original["text"] += " Data Source: Thomson Reuters"
        spec["original_capture_sha256"] = _save_json(original_path, original)
        capture["source_capture_sha256"] = spec["original_capture_sha256"]
        spec["source_capture_sha256"] = _save_json(capture_path, capture)
        loader["official_source_documents"][0]["raw_sha256"] = spec["source_capture_sha256"]
        _save_json(loader_path, loader)
    _save_json(tmp_path / "index.json", index)
    result = RetainedSourceResearch(tmp_path)
    assert not result.records
    assert [g["state"] for g in result.gaps] == [expected]


def test_reference_rate_chart_cannot_drop_required_credit_or_notices():
    packet, sources = chart_packet()
    url = "https://www.newyorkfed.org/markets/reference-rates/effr"
    sources[0]["url"] = url
    sources[0]["source_reuse_constraints"]["data_terms"] = {
        "required_attribution": "Controlled required credit", "url": "https://www.newyorkfed.org/privacy/termsofuse"}
    packet["required_attribution"] = {"attribution": "Controlled required credit",
        "source_url": url, "terms_url": "https://www.newyorkfed.org/privacy/termsofuse",
        "reference_rates_notice": "Controlled reference-rate notice", "non_affiliation_notice": "Controlled no affiliation"}
    assert _editorial_data_values(packet, sources)
    for key in ("attribution", "terms_url", "reference_rates_notice", "non_affiliation_notice"):
        altered = deepcopy(packet)
        altered["required_attribution"].pop(key)
        with pytest.raises(ValueError, match="EDITORIAL_CHART_(DATA_CREDIT|REFERENCE_RATE_NOTICES)_REQUIRED"):
            _editorial_data_values(altered, sources)


def test_short_document_peg_keeps_exact_period_and_issuer_without_title_padding():
    selected = {"headline_text": "Q3 2026 Update", "source_account": "Tesla"}
    article = {"title": "Tesla's cash recovery faces a durability test",
        "dek": "Investment and operating cash moved in different directions.",
        "substack_body_markdown": "Tesla's Q3 2026 Update reports the comparison."}
    assert not _selected_news_peg_blockers(article, selected)
    for changed in (
        {"title": "Another issuer's cash recovery faces a durability test"},
        {"substack_body_markdown": "Tesla's Q2 2026 Update reports the comparison."},
        {"substack_body_markdown": "An unrelated dated article."},
    ):
        assert _selected_news_peg_blockers({**article, **changed}, selected)


def test_issuer_promotional_title_proves_publication_without_proving_its_cause(tmp_path):
    from live_contentops.v1_simple_epistemic_state_v1 import build_epistemic_state

    _controlled_primaries(tmp_path)
    research = RetainedSourceResearch(tmp_path)
    record = research.records["controlled-issuer"]
    title = record["headline_text"]
    request = {"story_context": {"report_provenance": {"event_proposition": title}}}
    result = research.evidence({**request, "headline_ids": [record["headline_id"]]},
        cutoff_utc=record["revision_at_utc"])
    assert result["status"] == "PASS"
    state = result["epistemic_state"]
    assert state["event_proposition_scope"] == "PUBLICATION_OF_EXACT_ISSUER_DOCUMENT_ONLY"
    assert state["issuer_causal_explanation_independently_verified"] is False
    assert 'published a release titled "' in state["event_proposition"]
    doc = result["official_source_documents"][0]
    changed_title, _ = build_epistemic_state(request=request,
        documents=[{**doc, "title": "Different title"}], selected_route="OFFICIAL_PRIMARY")
    assert not (changed_title or {}).get("event_proposition_scope")
    for mutation in (
        {"source_interest_role": "ADVOCATE"},
        {"source_reuse_constraints": {}},
    ):
        altered, blockers = build_epistemic_state(request=request,
            documents=[{**doc, **mutation}], selected_route="OFFICIAL_PRIMARY")
        assert altered is None and "epistemic_selected_event_not_supported_by_route" in blockers
    other_request = {"story_context": {"report_provenance": {
        "event_proposition": "Southwest revenue drives gains across the whole economy in 2026"}}}
    altered, blockers = build_epistemic_state(request=other_request,
        documents=[doc], selected_route="OFFICIAL_PRIMARY")
    assert altered is None and blockers
