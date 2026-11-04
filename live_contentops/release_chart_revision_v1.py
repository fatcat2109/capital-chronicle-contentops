"""Decision 41 chart correction within the existing reader-revision owner.

No public action, new store or new editorial pipeline. Original sent artifacts
remain immutable; the existing coordinator edits the exact confirmed canonical.
"""
from copy import deepcopy
import json
from pathlib import Path

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of, _private

POLICY = "JIM_DECISION_41_RELEASE_CHART_EDIT"
DERIVATIVE_POLICY = "JIM_CC179_REVIEWED_CPI_DERIVATIVE_MEDIA"
MEDIA_REPAIR_POLICY = "JIM_CC247_REVIEWED_MEDIA_REPAIR"
MEDIA_REPAIR_RUN_IDS = frozenset({"cc124-prepare-20261103-a", "cc124-next-article-20261103-b"})
SOCIAL_DESTINATIONS = {"telegram", "discord", "x", "linkedin", "facebook_page",
                       "instagram_business", "threads", "youtube"}


def _writer(revision):
    from hashlib import sha256
    from live_contentops.native_desktop_editorial_v1 import validate_native_configuration, ROLE_ASSIGNMENTS
    record = revision["amendment_writer"]
    for kind in ("request", "response"):
        raw = Path(record[kind + "_path"]).read_bytes()
        if sha256(raw).hexdigest() != record[kind + "_sha256"]:
            raise ValueError("CHART_REVISION_NATIVE_WRITER_BYTES_CHANGED")
    output = json.loads(Path(record["response_path"]).read_bytes())
    if (output["request_sha256"] != record["request_sha256"]
            or output["revised_article_markdown"].split("\n\n", 1)[-1].strip()
                != revision["article"]["substack_body_markdown"].strip()):
        raise ValueError("CHART_REVISION_EXACT_NATIVE_COPY_REQUIRED")
    if revision.get("policy") in {DERIVATIVE_POLICY, MEDIA_REPAIR_POLICY} and output.get("channel_media") != revision.get("channel_media"):
        raise ValueError("DERIVATIVE_REVISION_NATIVE_MEDIA_SELECTION_REQUIRED")
    observation = record["invocation_observation"]
    validate_native_configuration(observation, ROLE_ASSIGNMENTS["write"])
    if observation.get("surface") not in {"CODEX_NATIVE_SUBAGENT", "CODEX_EXEC"} or not observation.get("invocation_id"):
        raise ValueError("CHART_REVISION_NATIVE_WRITER_REQUIRED")
    return {"invocation_observation": observation}


def build_revision(store, *, run_id, proposal, owner_authority_ref, result):
    from live_contentops.native_desktop_editorial_v1 import native_review_revision
    if proposal.get("policy") in {DERIVATIVE_POLICY, MEDIA_REPAIR_POLICY}:
        revision = {**proposal, "owner_authority_ref": owner_authority_ref,
            "base_result_sha256": sha256_of(result), "source_sha256": sha256_of(result.get("evidence", [])),
            "prior_revision": native_review_revision(result), "body_before": result["article"]["substack_body_markdown"]}
        revision_view(store, run_id=run_id, result=result, revision=revision)
        return revision
    if (owner_authority_ref != "human:JIM_DECISIONS_20261030_DECISION_41_CC142"
            or proposal.get("run_id") != run_id or proposal.get("article_identity") != result.get("article_identity")
            or not result.get("qualified_article_count")):
        raise ValueError("CHART_REVISION_EXACT_ITEM_AUTHORITY_REQUIRED")
    revision = {**proposal, "policy": POLICY, "owner_authority_ref": owner_authority_ref,
        "base_result_sha256": sha256_of(result), "source_sha256": sha256_of(result.get("evidence", [])),
        "prior_revision": native_review_revision(result), "body_before": result["article"]["substack_body_markdown"],
        "payloads": {}, "original_intent_sha256": {}}
    revision_view(store, run_id=run_id, result=result, revision=revision)
    return revision


def revision_view(store, *, run_id, result, revision):
    if revision.get("policy") == MEDIA_REPAIR_POLICY:
        return media_repair_view(store, run_id=run_id, result=result, revision=revision)
    if revision.get("policy") == DERIVATIVE_POLICY:
        return derivative_revision_view(store, run_id=run_id, result=result, revision=revision)
    from live_contentops.native_desktop_editorial_v1 import native_review_revision, validate_release_media
    from live_contentops.official_release_history_v1 import load_cc010_history, history_documents
    if (_private(revision) or revision.get("policy") != POLICY or revision.get("run_id") != run_id
            or revision.get("owner_authority_ref") != "human:JIM_DECISIONS_20261030_DECISION_41_CC142"
            or revision["base_result_sha256"] != sha256_of(result)
            or revision["source_sha256"] != sha256_of(result.get("evidence", []))
            or revision["prior_revision"] != native_review_revision(result)
            or set(revision.get("objects", {})) != {"substack"}):
        raise ValueError("CHART_REVISION_ORIGINAL_RESULT_CHANGED")
    identity = revision["objects"]["substack"]
    dispatch = store.get_platform_dispatch(identity["dispatch_id"]) or {}
    if (dispatch.get("status") != "DISPATCH_CONFIRMED" or dispatch.get("platform") != "substack"
            or any(dispatch.get(k) != identity.get(k) for k in
                ("message_id", "platform", "public_object_id", "public_object_url"))):
        raise ValueError("CHART_REVISION_EXACT_CONFIRMED_OBJECT_REQUIRED")
    article = revision["article"]
    if (article["title"] != result["article"]["title"] or article.get("news_item_kind") != "ANALYSIS"
            or not article["substack_body_markdown"].strip()
            or "Analysis, not financial advice. Readers decide whether to trade." not in article["substack_body_markdown"]):
        raise ValueError("CHART_REVISION_SAME_ARTICLE_AND_PUBLIC_SCOPE_REQUIRED")
    history = revision["official_history"]
    observed = load_cc010_history(history["archive_root"],
        series=[s["name"] for s in history["series"]], end_period=history["window"][-1],
        cutoff_utc=history["cutoff_utc"], months=len(history["periods"]))
    if history != observed or revision["additional_evidence"] != history_documents(observed):
        raise ValueError("CHART_REVISION_EVENT_HISTORY_CHANGED")
    charts = [a for a in revision["media_assets"] if a.get("modality") == "source_backed_chart"]
    bound_series = set()
    for chart in charts:
        packet = chart.get("editorial_data_packet", {})
        if lineage := packet.get("history_lineage"):
            if (lineage.get("dataset_sha256") != history["dataset_sha256"]
                    or lineage.get("window") != history["window"] or lineage.get("cutoff_utc") != history["cutoff_utc"]
                    or any(s != {k:original[k] for k in
                        ("name", "official_series_id", "seasonal_adjustment", "observations")}
                        for s in lineage.get("series", [])
                        for original in [next((v for v in history["series"] if v["name"] == s.get("name")), {})])):
                raise ValueError("CHART_REVISION_ASSET_HISTORY_UNBOUND")
            bound_series.update(s["name"] for s in lineage["series"])
    if (bound_series != {"CPI_HEADLINE_MOM", "CPI_CORE_MOM", "CPI_HEADLINE_YOY", "CPI_CORE_YOY"}
            or not history.get("components")
            or not any(c.get("editorial_data_packet", {}).get("component_lineage") == history["components"] for c in charts)):
        raise ValueError("CHART_REVISION_COMPLETE_CPI_HISTORY_AND_EFFECTS_REQUIRED")
    _writer(revision)
    view = deepcopy(result)
    view["article"] = deepcopy(article)
    view["evidence"] = [*result.get("evidence", []), *revision["additional_evidence"]]
    view["media_assets"] = deepcopy(revision["media_assets"])
    view["visual_editorial_decision"] = deepcopy(revision["visual_editorial_decision"])
    validate_release_media(view)
    return view


def amendment_writer(revision):
    return _writer(revision) if revision and revision.get("policy") in {POLICY, DERIVATIVE_POLICY, MEDIA_REPAIR_POLICY} else None


def media_repair_view(store, *, run_id, result, revision):
    """CC-247: unchanged facts/copy with source-identical media and an exact native review."""
    from live_contentops.native_desktop_editorial_v1 import native_review_revision, reader_presentation_acceptance, validate_release_media
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    if (_private(revision) or revision.get("owner_authority_ref") != "human:BACKLOG_CC247"
            or run_id not in MEDIA_REPAIR_RUN_IDS
            or revision.get("run_id") != run_id or revision.get("article_identity") != result.get("article_identity")
            or revision.get("base_result_sha256") != sha256_of(result)
            or revision.get("source_sha256") != sha256_of(result.get("evidence", []))
            or revision.get("prior_revision") != native_review_revision(result)
            or set(revision.get("objects", {})) != SOCIAL_DESTINATIONS | {"substack"}
            or set(revision.get("channel_media", {})) != SOCIAL_DESTINATIONS):
        raise ValueError("MEDIA_REPAIR_EXACT_CC247_SCOPE_REQUIRED")
    base = result
    if revision.get("canonical_review_reference"):
        _parent, base, _acceptance = reader_presentation_acceptance(store, run_id=run_id,
            reference=revision["canonical_review_reference"])
    canonical_id = revision["objects"]["substack"]
    canonical = store.get_platform_dispatch(canonical_id["dispatch_id"]) or {}
    if (canonical.get("status") != "DISPATCH_CONFIRMED" or any(canonical.get(k) != canonical_id.get(k)
            for k in ("message_id", "platform", "public_object_id", "public_object_url"))):
        raise ValueError("MEDIA_REPAIR_CONFIRMED_CANONICAL_REQUIRED")
    view = deepcopy(base)
    assets = revision.get("media_assets", [])
    originals = {a["asset_id"]: a for a in base.get("media_assets", [])}
    replaced = {}
    for asset in assets:
        if asset == originals.get(asset["asset_id"]):
            replaced[asset["asset_id"]] = asset["asset_id"]
            continue
        old = originals.get(asset.get("supersedes_asset_id"), {})
        if (not old or asset.get("supersedes_sha256") != old.get("sha256")
                or not old.get("fact_card_packet") or asset.get("fact_card_packet") != old["fact_card_packet"]
                or any(asset.get(k) != old.get(k) for k in
                    ("source_content_sha256", "source_page_url", "underlying_source_rights_status"))):
            raise ValueError("MEDIA_REPAIR_SOURCE_IDENTICAL_ASSET_REQUIRED")
        replaced[old["asset_id"]] = asset["asset_id"]
    if set(replaced) != set(originals) or len(assets) != len(originals):
        raise ValueError("MEDIA_REPAIR_EXACT_EXISTING_ASSET_SET_REQUIRED")
    decision = deepcopy(base["visual_editorial_decision"])
    for chart in decision.get("charts", []):
        chart["asset_id"] = replaced[chart["asset_id"]]
    decision["channel_media"] = deepcopy(revision["channel_media"])
    article = {**base["article"], "visual_editorial_decision": decision}
    if revision.get("article") != article:
        raise ValueError("MEDIA_REPAIR_UNCHANGED_ARTICLE_REQUIRED")
    canonical_intent = json.loads(store.get_outbox_message(canonical_id["message_id"])["payload"])
    canonical_intent["canonical_url"] = canonical_id["public_object_url"]
    if revision.get("plan_hash") != canonical_intent["plan_hash"]:
        raise ValueError("MEDIA_REPAIR_ORIGINAL_PLAN_REQUIRED")
    payloads = derivative_base_payloads(store, run_id=run_id, accepted=base, canonical_intent=canonical_intent)
    for preview in view["previews"]:
        d = preview["destination"]
        ids = DurablePublicationCoordinator._ids(run_id, canonical_intent["plan_hash"], d)
        target = revision["objects"][d]
        message = store.get_outbox_message(ids["message_id"])
        if (not message or revision["original_intent_sha256"].get(d) != sha256_of(json.loads(message["payload"]))
                or any(target.get(k) != v for k,v in {"message_id": ids["message_id"],
                    "dispatch_id": ids["dispatch_id"], "platform": d}.items())):
            raise ValueError("MEDIA_REPAIR_ORIGINAL_INTENT_AND_TARGET_REQUIRED")
        dispatch = store.get_platform_dispatch(ids["dispatch_id"]) or {}
        if target.get("public_object_id") and any(dispatch.get(k) != target.get(k)
                for k in ("message_id", "platform", "public_object_id", "public_object_url")):
            raise ValueError("MEDIA_REPAIR_PUBLIC_IDENTITY_CHANGED")
        chosen = revision["channel_media"][d]
        if not chosen or len(chosen) != len(set(chosen)) or not set(chosen) <= {a["asset_id"] for a in assets}:
            raise ValueError("MEDIA_REPAIR_BOUND_VISUAL_REQUIRED")
        payload = deepcopy(payloads[d]); payload["media_asset_ids"] = chosen
        for i, post in enumerate(payload.get("posts", [])):
            if isinstance(post, dict): post["media_asset_ids"] = chosen if i == 0 else []
        if revision["payloads"].get(d) != payload:
            raise ValueError("MEDIA_REPAIR_UNCHANGED_SOCIAL_COPY_REQUIRED")
        preview["payload"] = payload
    view.update(article=article, media_assets=deepcopy(assets), visual_editorial_decision=decision)
    validate_release_media(view)
    _writer(revision)
    return view


def derivative_revision_view(store, *, run_id, result, revision):
    """Select accepted canonical media without changing source facts or sent intents.

    The amendment has its own MAX editor in the current run. Its canonical parent
    remains the exact accepted chart correction, including its original clocks.
    """
    from live_contentops.native_desktop_editorial_v1 import native_review_revision, reader_presentation_acceptance
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    if (_private(revision) or revision.get("policy") != DERIVATIVE_POLICY
            or revision.get("owner_authority_ref") != "human:BACKLOG_CC179"
            or revision.get("run_id") != run_id or revision.get("article_identity") != result.get("article_identity")
            or revision.get("base_result_sha256") != sha256_of(result)
            or revision.get("source_sha256") != sha256_of(result.get("evidence", []))
            or revision.get("prior_revision") != native_review_revision(result)
            or set(revision.get("channel_media", {})) != SOCIAL_DESTINATIONS
            or set(revision.get("objects", {})) != SOCIAL_DESTINATIONS | {"substack"}
            or set(revision.get("original_intent_sha256", {})) != SOCIAL_DESTINATIONS):
        raise ValueError("DERIVATIVE_REVISION_EXACT_EXISTING_SCOPE_REQUIRED")
    parent, accepted, acceptance = reader_presentation_acceptance(store, run_id=run_id,
        reference=revision["canonical_review_reference"])
    if (parent.get("policy") != POLICY or revision.get("accepted_canonical_revision") != acceptance["article_revision"]
            or revision["article"] != accepted["article"]
            or revision["objects"]["substack"] != parent["objects"]["substack"]):
        raise ValueError("DERIVATIVE_REVISION_ACCEPTED_CANONICAL_REQUIRED")
    canonical = store.get_outbox_message(parent["objects"]["substack"]["message_id"])
    canonical_intent = json.loads(canonical["payload"])
    canonical_intent["canonical_url"] = parent["objects"]["substack"]["public_object_url"]
    if revision.get("plan_hash") != canonical_intent["plan_hash"]:
        raise ValueError("DERIVATIVE_REVISION_ORIGINAL_PLAN_REQUIRED")
    base_payloads = derivative_base_payloads(store, run_id=run_id, accepted=accepted, canonical_intent=canonical_intent)
    assets = {a["asset_id"]: a for a in accepted["media_assets"]}
    view = deepcopy(accepted)
    for preview in view["previews"]:
        destination = preview["destination"]
        identity = revision["objects"][destination]
        ids = DurablePublicationCoordinator._ids(run_id, canonical_intent["plan_hash"], destination)
        if (identity.get("message_id") != ids["message_id"] or identity.get("dispatch_id") != ids["dispatch_id"]
                or identity.get("platform") != destination):
            raise ValueError("DERIVATIVE_REVISION_EXACT_TARGET_REQUIRED")
        original = store.get_outbox_message(ids["message_id"])
        expected_hash = revision["original_intent_sha256"][destination]
        if expected_hash is None:
            # Missing intents are derived from the sealed plan by the coordinator,
            # never from writer-supplied transport or account fields.
            expected = derivative_missing_intent(canonical_intent, destination, base_payloads[destination])
            if revision.get("missing_intents", {}).get(destination) != expected:
                raise ValueError("DERIVATIVE_REVISION_MISSING_INTENT_UNBOUND")
            if original and json.loads(original["payload"]) != expected:
                raise ValueError("DERIVATIVE_REVISION_ORIGINAL_INTENT_CHANGED")
        elif not original or sha256_of(json.loads(original["payload"])) != expected_hash:
            raise ValueError("DERIVATIVE_REVISION_ORIGINAL_INTENT_CHANGED")
        if identity.get("public_object_id"):
            dispatch = store.get_platform_dispatch(ids["dispatch_id"]) or {}
            removed = (dispatch.get("status") == "EXTERNAL_REMOVAL_REPORTED_NO_RETRY" and any(
                r["readback_id"].startswith("owner-removal-")
                and json.loads(r["readback_data"]).get("exact_object_absence_independently_verified") is True
                for r in store.list_readbacks_for_dispatch(ids["dispatch_id"])))
            if ((dispatch.get("status") != "DISPATCH_CONFIRMED" and not removed) or any(dispatch.get(k) != identity.get(k)
                    for k in ("message_id", "platform", "public_object_id", "public_object_url"))):
                raise ValueError("DERIVATIVE_REVISION_EXISTING_OBJECT_CHANGED")
        chosen = revision["channel_media"][destination]
        if (not isinstance(chosen, list) or len(chosen) != len(set(chosen)) or not set(chosen) <= set(assets)):
            raise ValueError("DERIVATIVE_REVISION_ACCEPTED_MEDIA_ONLY")
        payload = deepcopy(base_payloads[destination])
        payload["media_asset_ids"] = chosen
        for i, post in enumerate(payload.get("posts", [])):
            if isinstance(post, dict):
                post["media_asset_ids"] = chosen if i == 0 else []
        if revision.get("payloads", {}).get(destination) != payload:
            raise ValueError("DERIVATIVE_REVISION_UNCHANGED_COPY_REQUIRED")
        preview["payload"] = payload
    view["visual_editorial_decision"] = {**accepted["visual_editorial_decision"],
        "channel_media": deepcopy(revision["channel_media"])}
    view["article"]["visual_editorial_decision"] = deepcopy(view["visual_editorial_decision"])
    _writer(revision)
    return view


def derivative_missing_intent(canonical_intent, destination, payload):
    """Recover a never-created social obligation from its original sealed plan."""
    from live_contentops.destination_transport_registry_v1 import registration_for_destination
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _read_json
    plan = _read_json(Path(canonical_intent["output_dir"]) / "publication_lifecycle_plan_v1.json")
    if plan.get("plan_hash") != canonical_intent["plan_hash"] or destination not in SOCIAL_DESTINATIONS:
        raise ValueError("DERIVATIVE_REVISION_SEALED_PLAN_REQUIRED")
    item = next((p for p in plan["destinations"] if p["destination"] == destination), None)
    registration = registration_for_destination(destination)
    if item is None:
        # A previously skipped visual destination becomes an obligation only in
        # this explicit reviewed amendment. Account and transport remain pinned.
        item = {"destination": destination, "surface": registration.surface,
            "transport_type": registration.transport_type, "readiness_state": "NOT_VERIFIED"}
    if item.get("surface") != registration.surface or item.get("transport_type") != registration.transport_type:
        raise ValueError("DERIVATIVE_REVISION_REGISTERED_DESTINATION_REQUIRED")
    value = deepcopy(canonical_intent)
    ids = DurablePublicationCoordinator._ids(value["work_item_id"], value["plan_hash"], destination)
    value.update(destination_plan={**item, "payload_hash": sha256_of(payload), "payload_hash_kind": "NATIVE_REVIEWED_PAYLOAD"},
        native_payload=deepcopy(payload), payload=payload["text"], attempt_identity=ids["dispatch_id"])
    return value


def derivative_base_payloads(store, *, run_id, accepted, canonical_intent):
    """Use final canonical-bound copy; a private placeholder can never reach a send."""
    import re
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
    url = canonical_intent.get("canonical_url") or ""
    if not re.fullmatch(r"https://capitalchronicle\.substack\.com/p/(?!pending-publication)[^/?#\s]+", url):
        raise ValueError("DERIVATIVE_REVISION_REAL_CANONICAL_URL_REQUIRED")
    def replace(value):
        if isinstance(value, str):
            return re.sub(r"https://capitalchronicle\.substack\.com/p/pending-publication[^\s)\]<>]*", url, value)
        if isinstance(value, list):
            return [replace(v) for v in value]
        if isinstance(value, dict):
            return {k: replace(v) for k, v in value.items()}
        return value
    payloads = {p["destination"]: replace(deepcopy(p["payload"])) for p in accepted["previews"]}
    co = DurablePublicationCoordinator(store=store, transport_runtime=None)
    for destination in SOCIAL_DESTINATIONS:
        ids = co._ids(run_id, canonical_intent["plan_hash"], destination)
        original = store.get_outbox_message(ids["message_id"])
        if original:
            effective = json.loads(co._dated_distribution_message(original)["payload"])
            frozen = effective.get("native_payload")
            # The coordinator froze this copy before dispatch. Delivery rendering
            # may select media later; that cannot rewrite the original intent.
            payloads[destination] = replace(deepcopy(frozen) if isinstance(frozen, dict)
                else _durable_intent_inputs(effective)["payloads"][destination])
    if not payloads["instagram_business"].get("text"):
        # Reuse exact reviewed Facebook prose, with no new factual sentence.
        payloads["instagram_business"] = {"text": payloads["facebook_page"]["text"],
            "format": "CAPTION", "platform_limit": 2200, "hard_truncation_used": False, "media_asset_ids": []}
        if len(payloads["instagram_business"]["text"]) > 2200:
            raise ValueError("DERIVATIVE_REVISION_INSTAGRAM_EDITOR_COPY_REQUIRED")
    return payloads
