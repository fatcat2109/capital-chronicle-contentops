"""Decision 41 chart correction within the existing reader-revision owner.

No public action, new store or new editorial pipeline. Original sent artifacts
remain immutable; the existing coordinator edits the exact confirmed canonical.
"""
from copy import deepcopy
import json
from pathlib import Path

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of, _private

POLICY = "JIM_DECISION_41_RELEASE_CHART_EDIT"


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
    observation = record["invocation_observation"]
    validate_native_configuration(observation, ROLE_ASSIGNMENTS["write"])
    if observation.get("surface") != "CODEX_NATIVE_SUBAGENT" or not observation.get("invocation_id"):
        raise ValueError("CHART_REVISION_NATIVE_WRITER_REQUIRED")
    return {"invocation_observation": observation}


def build_revision(store, *, run_id, proposal, owner_authority_ref, result):
    from live_contentops.native_desktop_editorial_v1 import native_review_revision
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
    return _writer(revision) if revision and revision.get("policy") == POLICY else None
