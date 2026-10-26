"""Controlled media/source boundaries; fixtures are never actual photo or model proof."""
import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from PIL import Image

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import (
    NativeDesktopTurn, DesktopInputRequired, validate_release_media,
)
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    build_source_value_comparison_chart, validate_source_value_chart,
)
from live_contentops.visual_asset_discovery_v1 import validate_contextual_photo


def controlled_release_packet(root):
    """Synthetic local source/pixels for contract tests, never a retained story."""
    root.mkdir(parents=True, exist_ok=True)
    text = "Free cash flow in Q3 was $1.53 billion. Analysts expected cash burn of $4.92 billion in Q3."
    doc = {"url": "https://example.org/controlled-source", "source_id": "SOURCE_TEST",
           "document_id": "CONTROLLED_NOT_REAL", "publisher": "Controlled fixture",
           "published_at_utc": "2026-10-21T00:00:00Z", "canonical_content_text": text,
           "canonical_content_sha256": sha256(text.encode()).hexdigest(),
           "source_reuse_constraints": {"scope": "ATTRIBUTED_REPORTED_FACTS_ONLY_INDEPENDENT_PUBLIC_PARAPHRASE",
               "attribution_required": True, "policy_capture_sha256": "a" * 64, "source_capture_sha256": "b" * 64}}
    rows = [{"label": "Free cash flow", "metric_source_text": "Free cash flow", "period": "Q3",
             "observation_kind": "ACTUAL", "unit": "USD billion", "support_excerpt": text,
             "value_context": "Free cash flow in Q3 was $1.53 billion.", "value_text": "1.53"},
            {"label": "Expected cash burn", "metric_source_text": "cash burn", "period": "Q3",
             "observation_kind": "ESTIMATE", "unit": "USD billion", "support_excerpt": text,
             "value_context": "Analysts expected cash burn of $4.92 billion in Q3.", "value_text": "4.92",
             "negative_evidence": "cash burn of $4.92 billion"}]
    chart = build_source_value_comparison_chart(doc, rows=rows, title="Controlled comparison", unit="USD billion", output_dir=root)
    chart["visual_review"] = {"asset_sha256": chart["sha256"], "pixels_inspected": True,
                              "labels_and_units_legible": True, "reviewer": "CONTROLLED_TEST_NOT_VISUAL_PROOF"}
    path = root / "controlled.jpg"
    Image.new("RGB", (100, 80), "#123456").save(path)
    digest = sha256(path.read_bytes()).hexdigest()
    photo = {"asset_id": "controlled-photo", "path": str(path), "sha256": digest,
             "width": 100, "height": 80, "modality": "documentary_photo", "rights_status": "PUBLIC_DOMAIN",
             "source_page_url": "https://commons.wikimedia.org/wiki/File:Controlled.jpg",
             "original_asset_url": "https://upload.wikimedia.org/controlled.jpg",
             "creator_publisher": "Controlled fixture", "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
             "depicted_date": "2020-01-01", "attribution": "Controlled fixture, CC0",
             "source_reuse_basis": "CC0 controlled metadata", "caption": "Controlled archive image",
             "alt_text": "Controlled test pixels", "relevance_rationale": "Controlled subject",
             "context_only": True, "corroborates_article_facts": False,
             "visual_review": {"asset_sha256": digest, "pixels_inspected": True,
                               "relevant_subject": True, "reviewer": "CONTROLLED_TEST_NOT_VISUAL_PROOF"}}
    receipt = {k: photo[k] for k in ("source_page_url", "original_asset_url", "creator_publisher",
                                    "license_url", "rights_status", "depicted_date")}
    receipt.update(license_text="CC0", original_sha256=digest, provider_metadata={"page": {"imageinfo": [{
        "descriptionurl": photo["source_page_url"], "url": photo["original_asset_url"], "extmetadata": {
            "LicenseUrl": {"value": photo["license_url"]}, "LicenseShortName": {"value": "CC0"},
            "DateTimeOriginal": {"value": photo["depicted_date"]}}}]}})
    evidence = root / "controlled-rights.json"
    evidence.write_bytes(canonical_bytes(receipt))
    photo.update(rights_evidence_path=str(evidence), rights_evidence_sha256=sha256(evidence.read_bytes()).hexdigest())
    return doc, photo, chart


def test_source_bound_negative_values_and_exact_release_packet(tmp_path):
    doc, photo, chart = controlled_release_packet(tmp_path)
    assert chart["computed_values"] == [[1.53], [-4.92]]
    validate_contextual_photo(photo)
    validate_source_value_chart(chart, [doc])
    assert validate_release_media({"media_assets": [photo, chart], "evidence": [doc]})["chart_count"] == 1
    for assets in ([], [chart], [photo], [{"modality": "document_excerpt"}]):
        with pytest.raises(ValueError, match="PHOTO_AND_QUANTITATIVE_CHART"):
            validate_release_media({"media_assets": assets, "evidence": [doc]})


@pytest.mark.parametrize("change", ["unit", "period", "value", "kind", "negative", "rights"])
def test_chart_misleading_data_labels_and_unknown_rights_fail(tmp_path, change):
    doc, _, chart = controlled_release_packet(tmp_path)
    rows = deepcopy(chart["source_value_bindings"])
    unit = "USD billion"
    if change == "unit":
        unit = "USD/share"
        for row in rows:
            row["unit"] = unit
    elif change == "period":
        rows[0]["period"] = "Q4"
    elif change == "value":
        rows[0]["value_text"] = "4.92"  # Present elsewhere, absent from the actual-value context.
    elif change == "kind":
        rows[1]["observation_kind"] = "ACTUAL"
    elif change == "negative":
        rows[1].pop("negative_evidence")
    else:
        doc["source_reuse_constraints"] = {}
    with pytest.raises(ValueError):
        build_source_value_comparison_chart(doc, rows=rows, title="Rejected", unit=unit, output_dir=tmp_path / "rejected")


def test_forecast_ranges_preserve_bounds_and_reject_inversion(tmp_path):
    doc, _, _ = controlled_release_packet(tmp_path)
    text = "The forecast for 2026 was $3.25 to $4.25 per share. The forecast for 2026 is $2.60 to $2.85 per share."
    doc["canonical_content_text"] = text
    rows = [{"label": label, "metric_source_text": "forecast", "period": "2026", "unit": "USD/share",
             "observation_kind": "FORECAST", "support_excerpt": text, "value_context": context,
             "lower_text": lo, "upper_text": hi} for label, context, lo, hi in (
                 ("Prior forecast", text.split(". The")[0] + ".", "3.25", "4.25"),
                 ("New forecast", "The forecast for 2026 is $2.60 to $2.85 per share.", "2.60", "2.85"))]
    chart = build_source_value_comparison_chart(doc, rows=rows, title="Ranges", unit="USD/share", output_dir=tmp_path)
    assert chart["computed_values"] == [[3.25, 4.25], [2.6, 2.85]]
    rows[0]["lower_text"], rows[0]["upper_text"] = "4.25", "3.25"
    with pytest.raises(ValueError, match="range_inverted"):
        build_source_value_comparison_chart(doc, rows=rows, title="Bad", unit="USD/share", output_dir=tmp_path)


def test_exact_source_pixels_license_and_render_review_cannot_drift(tmp_path):
    doc, photo, chart = controlled_release_packet(tmp_path)
    for field, value in (("rights_status", "UNKNOWN"), ("license_url", "https://example.org/not-license"),
                         ("source_page_url", "https://example.org/unrelated"), ("is_thumbnail", True)):
        changed = {**photo, field: value}
        with pytest.raises(ValueError):
            validate_contextual_photo(changed)
    changed = deepcopy(chart)
    changed["visual_review"]["asset_sha256"] = "wrong"
    with pytest.raises(ValueError, match="RENDER_REVIEW"):
        validate_release_media({"media_assets": [photo, changed], "evidence": [doc]})
    changed_doc = {**doc, "canonical_content_text": doc["canonical_content_text"] + " Changed."}
    with pytest.raises(ValueError, match="EXACT_FACT_SOURCE"):
        validate_source_value_chart(chart, [changed_doc])
    Path(photo["path"]).write_bytes(b"different pixels")
    with pytest.raises(ValueError, match="BYTES_CHANGED"):
        validate_contextual_photo(photo)


def test_writer_waits_for_media_plan_without_freezing_or_invoking(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    run = "controlled-media-wait"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)
    with pytest.raises(DesktopInputRequired) as pending:
        turn(logical_invocation_id=run + ":write", prompt="Controlled", governed_input={"source_pack": []},
             validator=lambda raw: (True, None, json.loads(raw), None))
    assert pending.value.request["stage"] == "media-plan"
    assert turn.frozen_request("write") is None
    assert turn.telemetry()["semantic_response_count"] == 0


def test_editorial_revision_retains_original_source_and_review_identity(tmp_path):
    from live_contentops.contentops_editorial_desk_v1 import record_story_editorial_revision
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    run = "controlled-prior"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    prior = {"qualified_article_count": 1, "article_identity": "a" * 64,
        "article": {"title": "Original", "story_identity": "story", "substack_body_markdown": "Original facts"},
        "simple_result": {"cutoff_utc": "2026-10-21T22:00:00Z"},
        "evidence": [{"document_id": "source", "url": "https://example.org/report", "canonical_content_sha256": "b" * 64}]}
    key = "cc-editorial-final-" + sha256_of(run)
    store.register_outbox_message(message_id=key, work_item_id=work, destination="internal:cc-report-simple-result",
                                  payload=canonical_bytes(prior).decode(), status="EDITORIAL_INTERNAL")
    review = record_story_editorial_revision(store, run_id=run, article_identity="a" * 64,
        review_operation_id="controlled-child", reason="Owner asks to refine the prose and add lawful useful media.")
    assert review["decision"] == "EDITORIAL_REVISION" and review["new_factual_evidence"] is False
    assert review["invalidates_prepared_review"] is False and review["writer_required"] is True
    assert review["prior_story"]["article_identity"] == prior["article_identity"]
    assert json.loads(store.get_outbox_message(key)["payload"]) == prior


def test_public_reader_links_replace_internal_source_identifiers():
    from live_contentops.v1_simple_gemini_newsroom_v1 import _reader_safe_native_article
    article = {"title": "Controlled", "substack_body_markdown": "Attributed fact. [[SOURCE:SOURCE_1]]",
               "public_source_bindings": [{"source_id": "SOURCE_1", "publisher": "Publisher", "url": "https://example.org/report"}]}
    body = _reader_safe_native_article(article, article_mode="STANDARD_NEWS_ANALYSIS")["substack_body_markdown"]
    assert "[Publisher](https://example.org/report)" in body and "SOURCE_1" not in body


def test_media_plan_is_bound_before_writer_and_replays_exactly(tmp_path):
    from live_contentops.native_desktop_editorial_v1 import bind_editorial_media_plan
    from live_contentops.v1_simple_gemini_newsroom_v1 import _worker_prompt
    doc, photo, _ = controlled_release_packet(tmp_path / "assets")
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    run = "controlled-planned-writer"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)
    args = dict(logical_invocation_id=run + ":write", prompt=_worker_prompt({"source_pack": [doc]}),
                governed_input={"source_pack": [doc]}, validator=lambda raw: (True, None, json.loads(raw), None))
    with pytest.raises(DesktopInputRequired) as pending:
        turn(**args)
    assert pending.value.request["stage"] == "media-plan"
    story = {"thesis": "Controlled thesis", "photo_plan": "Controlled archive", "chart_plan": "Reported comparison"}
    plan_args = dict(logical_invocation_id=run + ":media-plan", prompt="Controlled native plan",
                     governed_input={"source_pack": [doc]}, validator=lambda raw: (True, None, json.loads(raw), None))
    with pytest.raises(DesktopInputRequired) as request:
        turn(**plan_args)
    turn.submit("media-plan", {"request_sha256": request.value.request["request_sha256"], "output": {"story_plan": story},
        "invocation_observation": {"surface": "CODEX_NATIVE_SUBAGENT", "invocation_id": "CONTROLLED_NOT_MODEL_PROOF",
            "model": "gpt-6.1-sol", "reasoning_effort": "low", "observation_source": "CONTROLLED_UNIT_TEST"}})
    plan = {"native_plan_run_id": run, "native_plan_stage": "media-plan",
            "native_plan_request_sha256": request.value.request["request_sha256"], "story_plan": story}
    with pytest.raises(ValueError, match="ACTUAL_MAX_VISUAL_DECISION_REQUIRED"):
        bind_editorial_media_plan(store, run_id=run, output_dir=tmp_path, plan=plan, assets=[photo])
    with pytest.raises(DesktopInputRequired) as visual_request:
        turn.request_visual_decision(source_packet={"source_pack": [doc]}, preparation=plan)
    visual = {"reader_first_version": "DATA_JOURNALISM_V1", "story_kind": "NEWS",
              "editorial_thesis": "Controlled plan/replay fixture, not editorial acceptance.", "charts": [],
              "exception_reason": "Controlled narrow notice does not require a quantitative comparison.",
              "contextual_photo_ids": [photo["asset_id"]],
              "channel_media": {d: [photo["asset_id"]] for d in (
                  "telegram", "discord", "x", "linkedin", "facebook_page", "instagram_business", "threads", "youtube")}}
    turn.submit("visual-edit", {"request_sha256": visual_request.value.request["request_sha256"], "output": visual,
        "invocation_observation": {"surface": "CODEX_NATIVE_SUBAGENT", "invocation_id": "CONTROLLED_MAX_NOT_MODEL_PROOF",
            "model": "gpt-6.1-sol", "reasoning_effort": "max", "observation_source": "CONTROLLED_UNIT_TEST"}})
    bind_editorial_media_plan(store, run_id=run, output_dir=tmp_path, plan=plan, assets=[photo])
    with pytest.raises(DesktopInputRequired) as first:
        turn(**args)
    with pytest.raises(DesktopInputRequired) as second:
        frozen_input = first.value.request["governed_input"]
        turn(**{**args, "prompt": _worker_prompt(frozen_input), "governed_input": frozen_input})
    assert first.value.request == second.value.request
    assert first.value.request["governed_input"]["editorial_media_plan"]["plan"] == plan


@pytest.mark.parametrize("field", ["copy", "photo", "chart", "preview"])
def test_exact_review_is_invalidated_by_copy_or_media_metadata_change(tmp_path, field):
    from live_contentops.contentops_editorial_desk_v1 import record_native_article_review
    from live_contentops.native_desktop_editorial_v1 import validated_native_review
    doc, photo, chart = controlled_release_packet(tmp_path / "assets")
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    run = "controlled-review-drift"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    value = {"model_execution_state": "NATIVE_DESKTOP_REQUEST_RETURN", "qualified_article_count": 1,
        "article_identity": "a" * 64, "article": {"title": "Controlled review drift", "substack_body_markdown": "Controlled source-bound copy"},
        "simple_result": {"run_id": run, "publication_lifecycle_plan": {"plan_hash": "b" * 64}},
        "media_assets": [photo, chart], "evidence": [doc],
        "previews": [{"destination": "telegram", "payload": {"text": "Controlled original preview"}}],
        "media_preview_binding_sha256": "CONTROLLED_PREVIEW_BOUND"}
    key = "cc-editorial-final-" + sha256_of(run)
    store.register_outbox_message(message_id=key, work_item_id=work, destination="internal:cc-report-simple-result",
                                  payload=canonical_bytes(value).decode(), status="EDITORIAL_INTERNAL")
    record_native_article_review(store, run_id=run, article_identity="a" * 64, decision="KEEP",
                                 rationale="Controlled review of exact copy and both media assets.")
    validated_native_review(store, run_id=run)
    if field == "copy":
        value["article"]["substack_body_markdown"] += " Changed meaning."
    elif field == "preview":
        value["previews"][0]["payload"]["text"] = "A changed unsupported preview."
    else:
        value["media_assets"][0 if field == "photo" else 1]["caption"] = "Changed caption"
    store.finalize_outbox_payload_before_dispatch(message_id=key, payload=canonical_bytes(value).decode(), status="EDITORIAL_INTERNAL")
    with pytest.raises(ValueError, match="REVIEW_REVISION_CHANGED"):
        validated_native_review(store, run_id=run)
    from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection
    from live_contentops.contentops_editorial_desk_v1 import read_reviews
    view = report_workspace_projection(store.list_outbox_messages(), review_records=read_reviews(store))
    item = view["native_edition"][0]
    assert item["prepared_state"] == "INVALIDATED_BY_ARTICLE_OR_MEDIA_REVISION"
    assert item["publication"]["state"] == "REVIEW_REQUIRED"


def test_cleared_photo_credit_reaches_all_previews_and_exact_transport_media(tmp_path):
    from live_contentops.v1_simple_gemini_newsroom_v1 import _native_preview_bundle
    from live_contentops.neo_destination_handoff_v1 import _payload_binding
    _, photo, chart = controlled_release_packet(tmp_path / "assets")
    article = {"title": "Controlled cash-flow comparison", "dek": "The reported result differs from the estimate.",
        "substack_body_markdown": "The reported result differs from the estimate. The next release tests persistence.",
        "social_mechanism_summary": "A cash-flow difference alone does not establish durable cash generation.",
        "social_policy_summary": "The observation is a dated reported result.",
        "social_cross_asset_summary": "The next source release tests persistence."}
    bundle, _ = _native_preview_bundle(article=article, article_mode="STANDARD_NEWS_ANALYSIS",
        article_identity="a" * 64, media_asset_ids=[photo["asset_id"], chart["asset_id"]], media_assets=[photo, chart])
    for destination, payload in bundle["packages"].items():
        text = payload.get("full_text") or payload["text"]
        assert photo["license_url"] in text and photo["source_page_url"] in text
        assert "Photo: Controlled fixture." in text
        _, binding = _payload_binding({"native_payload": payload, "media_assets": [photo, chart]}, destination)
        assert [a["asset_id"] for a in binding["media_manifest"]] == [photo["asset_id"]]
        assert binding["media_manifest"][0]["license_url"] == photo["license_url"]
        assert binding["media_manifest"][0]["alt_text"] == photo["alt_text"]
    # The owned chart is a useful short-channel visual without unused photo credit.
    chart_bundle, _ = _native_preview_bundle(article=article, article_mode="STANDARD_NEWS_ANALYSIS",
        article_identity="a" * 64, media_asset_ids=[chart["asset_id"], photo["asset_id"]], media_assets=[chart, photo])
    for destination, payload in chart_bundle["packages"].items():
        assert photo["license_url"] not in (payload.get("full_text") or payload["text"])
        _, binding = _payload_binding({"native_payload": payload, "media_assets": [chart, photo]}, destination)
        assert [a["asset_id"] for a in binding["media_manifest"]] == [chart["asset_id"]]


def test_announced_policy_rates_preserve_percent_words_and_effective_date(tmp_path):
    doc, _, _ = controlled_release_packet(tmp_path)
    text = ('Effective September 17, 2026, the interest rate on reserve balances is 3.90 percent. '
            'Effective September 17, 2026, the standing repo rate is 4.0 percent.')
    doc['canonical_content_text'] = text
    rows = [{'label':label, 'metric_source_text':metric, 'period':'September 17, 2026',
             'unit':'%', 'observation_kind':'ANNOUNCED_POLICY', 'support_excerpt':sentence,
             'value_context':sentence, 'value_text':value}
            for label, metric, value, sentence in (
                ('Reserve interest','interest rate','3.90',text.split('. Effective')[0]+'.'),
                ('Repo','repo rate','4.0','Effective September 17, 2026, the standing repo rate is 4.0 percent.'))]
    chart = build_source_value_comparison_chart(doc, rows=rows, title='Controlled announced rates', unit='%', output_dir=tmp_path)
    assert chart['computed_values'] == [[3.9], [4.0]]
    rows[0]['period'] = 'September 18, 2026'
    with pytest.raises(ValueError, match='period_or_kind_unbound'):
        build_source_value_comparison_chart(doc, rows=rows, title='Wrong date', unit='%', output_dir=tmp_path)


def test_reported_percentage_declines_require_exact_negative_binding(tmp_path):
    doc, _, _ = controlled_release_packet(tmp_path)
    text = 'On October 23 gold fell 0.6%. On October 23 silver slid 1%.'
    doc['canonical_content_text'] = text
    rows = [{'label':label, 'metric_source_text':metric, 'period':'October 23', 'unit':'%',
             'observation_kind':'ACTUAL', 'support_excerpt':sentence, 'value_context':sentence,
             'value_text':value, 'negative_evidence':negative}
            for label, metric, value, sentence, negative in (
                ('Gold','gold','0.6','On October 23 gold fell 0.6%.','fell 0.6%'),
                ('Silver','silver','1','On October 23 silver slid 1%.','slid 1%'))]
    chart = build_source_value_comparison_chart(doc, rows=rows, title='Controlled declines', unit='%', output_dir=tmp_path)
    assert chart['computed_values'] == [[-0.6], [-1.0]]
    rows[0].pop('negative_evidence')
    with pytest.raises(ValueError, match='explicit_sign_binding'):
        build_source_value_comparison_chart(doc, rows=rows, title='Lost sign', unit='%', output_dir=tmp_path)


def test_commons_federal_photo_without_license_url_needs_bound_policy(tmp_path):
    _, photo, _ = controlled_release_packet(tmp_path)
    receipt_path = Path(photo['rights_evidence_path'])
    receipt = json.loads(receipt_path.read_bytes())
    meta = receipt['provider_metadata']['page']['imageinfo'][0]['extmetadata']
    meta.pop('LicenseUrl')
    meta.update(License={'value':'pd'}, LicenseShortName={'value':'Public domain'}, Copyrighted={'value':'False'})
    receipt['provider_metadata']['page']['license_wikitext'] = '{{PD-USGov}}'
    photo['license_url'] = receipt['license_url'] = 'https://commons.wikimedia.org/wiki/Template:PD-USGov'
    policy = tmp_path/'controlled-policy.json'
    policy.write_text(json.dumps({'status':'PASS','final_url':photo['license_url'],
        'retrieval_method':'READ_ONLY_BROWSEROS_NEO_PUBLIC_LICENSE',
        'canonical_content_text':'Public domain: United States Federal Government official duties under Section 105.',
        'credential_or_session_material_read':False,'public_write_performed':False}))
    receipt['public_domain_basis'] = {'policy_url':photo['license_url'], 'policy_capture_path':str(policy),
                                      'policy_capture_sha256':sha256(policy.read_bytes()).hexdigest()}
    def seal():
        receipt_path.write_text(json.dumps(receipt))
        photo['rights_evidence_sha256'] = sha256(receipt_path.read_bytes()).hexdigest()
    seal()
    validate_contextual_photo(photo)
    policy.write_text('changed')
    with pytest.raises(ValueError):
        validate_contextual_photo(photo)
    receipt['provider_metadata']['page']['license_wikitext'] = '{{Unrelated}}'
    seal()
    with pytest.raises(ValueError, match='PUBLIC_DOMAIN_BASIS'):
        validate_contextual_photo(photo)


def controlled_nasa_photo(root):
    """Controlled permission/capture/EXIF contract, never actual NASA pixel proof."""
    _, photo, _ = controlled_release_packet(root)
    photo.update(source_page_url="https://www.nasa.gov/image-article/controlled/",
                 original_asset_url="https://www.nasa.gov/wp-content/uploads/controlled.jpg",
                 creator_publisher="NASA/Controlled fixture", rights_status="FIRST_PARTY_REUSABLE",
                 license_url="https://www.nasa.gov/nasa-brand-center/images-and-media/",
                 attribution="NASA/Controlled fixture", source_reuse_basis="Factual editorial permission")
    exif = Image.Exif()
    exif[315], exif[306] = photo["creator_publisher"], "2020:01:01 12:00:00"
    Image.new("RGB", (100, 80), "#123456").save(photo["path"], exif=exif)
    photo["sha256"] = sha256(Path(photo["path"]).read_bytes()).hexdigest()
    photo["visual_review"].update(asset_sha256=photo["sha256"], identifiable_people=False,
                                  promotional_logo_focus=False)
    texts = {"source": "Photo credit: " + photo["creator_publisher"] + " " + photo["original_asset_url"],
             "policy": "News outlets, schools, and text-book authors may use NASA content without needing "
                       "explicit permission. A factual manner that does not imply endorsement. "
                       "NASA should be acknowledged as the source. Except copyright-protected material of "
                       "third parties. NASA imagery can be generally used editorially within published works "
                       "that are not promotional in nature."}
    provider = {"provider_id": "NASA_OFFICIAL"}
    for kind, url, method in (("source", photo["source_page_url"], "PUBLIC_MEDIA"),
                              ("policy", photo["license_url"], "PUBLIC_LICENSE")):
        path = root / (kind + "-capture.json")
        path.write_bytes(canonical_bytes({"final_url": url, "canonical_content_text": texts[kind],
            "retrieval_method": "READ_ONLY_BROWSEROS_NEO_" + method,
            "credential_or_session_material_read": False, "public_write_performed": False}))
        provider[kind + "_capture_path"] = str(path)
        provider[kind + "_capture_sha256"] = sha256(path.read_bytes()).hexdigest()
    receipt = {key: photo[key] for key in ("source_page_url", "original_asset_url", "creator_publisher",
                                          "license_url", "rights_status", "depicted_date")}
    receipt.update(provider_metadata=provider, license_text=texts["policy"], original_sha256=photo["sha256"],
                   use_scope="FACTUAL_EDITORIAL_NON_PROMOTIONAL")
    return photo, receipt


def write_controlled_rights(photo, receipt):
    path = Path(photo["rights_evidence_path"])
    path.write_bytes(canonical_bytes(receipt))
    photo["rights_evidence_sha256"] = sha256(path.read_bytes()).hexdigest()


def test_official_nasa_editorial_permission_with_original_exif(tmp_path):
    photo, receipt = controlled_nasa_photo(tmp_path)
    write_controlled_rights(photo, receipt)
    validate_contextual_photo(photo)


@pytest.mark.parametrize("change", ["foreign_host", "public_domain_flag", "third_party", "policy_terms",
                                   "changed_capture", "exif_credit", "exif_date", "people"])
def test_nasa_permission_cannot_be_created_by_flags_or_unbound_evidence(tmp_path, change):
    photo, receipt = controlled_nasa_photo(tmp_path)
    provider = receipt["provider_metadata"]
    if change == "foreign_host":
        photo["original_asset_url"] = receipt["original_asset_url"] = "https://www.nasa.gov.example/controlled.jpg"
    elif change == "public_domain_flag":
        photo["rights_status"] = receipt["rights_status"] = "PUBLIC_DOMAIN"
    elif change in {"third_party", "policy_terms", "changed_capture"}:
        kind = "policy" if change == "policy_terms" else "source"
        path = Path(provider[kind + "_capture_path"])
        capture = json.loads(path.read_bytes())
        if change == "policy_terms":
            capture["canonical_content_text"] = receipt["license_text"] = "NASA content, rights unknown."
        else:
            capture["canonical_content_text"] += " Copyright protected: third-party photographer."
        path.write_bytes(canonical_bytes(capture))
        if change != "changed_capture":
            provider[kind + "_capture_sha256"] = sha256(path.read_bytes()).hexdigest()
    elif change.startswith("exif_"):
        exif = Image.Exif()
        exif[315] = "Other photographer" if change == "exif_credit" else photo["creator_publisher"]
        exif[306] = "2021:01:01 12:00:00" if change == "exif_date" else "2020:01:01 12:00:00"
        Image.new("RGB", (100, 80), "#123456").save(photo["path"], exif=exif)
        photo["sha256"] = receipt["original_sha256"] = sha256(Path(photo["path"]).read_bytes()).hexdigest()
        photo["visual_review"]["asset_sha256"] = photo["sha256"]
    else:
        photo["visual_review"]["identifiable_people"] = True
    write_controlled_rights(photo, receipt)
    with pytest.raises(ValueError, match="PHOTO_NASA_"):
        validate_contextual_photo(photo)
