"""Render editor-authored research through existing validation/media/native compiler owners.

This offline path never invokes a model and never creates a qualified Simple result.
Its output is inspectable editorial research awaiting substantive review and fresh data.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker, sha256_of
from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection
from live_contentops.contentops_foundation_library_v1 import persist_library, persist_research_package
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.eight_platform_substack_first_pipeline_v1 import build_native_derivative_payloads
from live_contentops.llm_operator_control_v1 import llm_operator_pause_active
from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_source_backed_media_assets, build_source_comparison_card, validate_generated_article


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def render(root, output, store_path):
    if output.exists() or store_path.exists():
        raise ValueError("NEW_ISOLATED_OUTPUT_AND_STORE_REQUIRED")
    if not llm_operator_pause_active():
        raise ValueError("EXPECTED_LLM_PAUSE_NOT_ACTIVE")
    output.mkdir(parents=True)
    research = RetainedSourceResearch(root / "retained_research")
    briefs = json.loads((root / "editorial_briefs.json").read_bytes())["briefs"]
    tracker = LatestReportDeliveryTracker(ContentOpsDurableStore(store_path))
    cutoff = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    library = persist_library(tracker, research, cutoff_utc=cutoff, briefs=briefs)
    packages = []
    for brief in library["briefs"]:
        folder = output / brief["brief_id"]
        folder.mkdir()
        records = [research.records[i] for i in brief["source_item_ids"]]
        docs = [{**r["document"], "document_id": r["headline_id"], "canonical_content_text": r["permitted_source_text"],
                 "rights_evidence_sha256": r["rights_evidence_sha256"], "known_at_utc": r["known_at_utc"],
                 "underlying_reuse_classification": "governed_government_public_domain",
                 "render_excerpt_text": r["headline_text"]} for r in records]
        for doc in docs:
            date = doc.get("published_at_utc")
            doc["source_date_display"] = (str(doc["source_modified_at_utc"])[:10] + " (last modified; publication date unknown)"
                if doc.get("source_modified_at_utc") else str(date)[:10] + " (date only)"
                if doc.get("publication_time_precision") == "DATE_ONLY" else date or "Publication date not verified")
            if len(doc["render_excerpt_text"]) > 480:
                sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", doc["render_excerpt_text"])
                excerpt = ""
                for sentence in sentences:
                    if len(excerpt + " " + sentence) > 480:
                        break
                    excerpt = (excerpt + " " + sentence).strip()
                    if len(excerpt) > 260:
                        break
                if not excerpt:
                    raise ValueError("COMPLETE_MEDIA_EXCERPT_TOO_LONG")
                doc["render_excerpt_text"] = excerpt
        body = ["## Phạm vi\n\nBản nghiên cứu nền do biên tập soạn. Không phải kết quả Simple mới, dự báo Core, bài đã duyệt hay bản tin giá hiện tại."]
        lineage = []
        for n, r in enumerate(records, 1):
            marker = "SOURCE_" + str(n)
            body.append("## Dữ kiện từ nguồn\n\n" + r["headline_text"] + " [[SOURCE:" + marker + "]]" +
                        "\n\nNgày nguồn: " + str(r["source_timestamp_utc"] or "chưa xác minh") +
                        ". Tình trạng: " + r["research_metadata"]["context_kind"] + ".")
            if r["document"].get("source_modified_at_utc"):
                body.append("Ngày sửa nguồn được ghi: " + r["document"]["source_modified_at_utc"][:10] + ". Ngày xuất bản chưa xác minh.")
            lineage.append({"item_id": r["headline_id"], "source_id": marker, "source_url": r["source_url"],
                            "text_sha256": r["text_sha256"], "source_capture_sha256": r["source_capture_sha256"],
                            "permission_sha256": r["source_permission_record_sha256"], "claim_kind": "ATTRIBUTED_OFFICIAL_SOURCE_TEXT"})
        for title, value in [("Vì sao đáng đọc", brief["audience_value"]), ("Cơ chế cần kiểm tra", brief["mechanism"]),
                             ("Giải thích cạnh tranh", brief["competing_explanation"]),
                             ("Kịch bản điều kiện", "\n".join(brief["scenarios"])),
                             ("Điều kiện bác bỏ", "\n".join(brief["falsifiers"])),
                             ("Còn thiếu", "; ".join(brief["missing_inputs"])), ("Câu hỏi tiếp", brief["next_question"])]:
            body.append("## " + title + "\n\n" + value)
        body.append("## Nguồn\n\n" + "\n".join("[" + str(n) + "] " + r["source_url"] for n, r in enumerate(records, 1)))
        article = {"title": "Nghiên cứu: " + brief["title"], "dek": brief["audience_value"], "subtitle": brief["audience_value"],
                   "market_mechanism": brief["mechanism"], "policy_context": "Nghiên cứu biên tập chưa duyệt. " + brief["competing_explanation"],
                   "cross_asset_implications": brief["next_question"],
                   "substack_body_markdown": "\n\n".join(body), "authoring_origin": "EDITOR_AUTHORED_RESEARCH",
                   "article_mode": "DATA_OR_DOCUMENT_LENS", "cluster_id": brief["brief_id"],
                   "headline_ids": brief["source_item_ids"], "evidence_document_ids": [d["document_id"] for d in docs],
                   "x_content_grants_factual_authority": False, "publication_authority": False,
                   "editorial_scope_notice": "Nghiên cứu biên tập chưa xuất bản; dữ liệu có ngày riêng; không phải khuyến nghị giao dịch."}
        context = {"cluster_id": brief["brief_id"], "headline_ids": brief["source_item_ids"],
                   "evidence_documents": docs, "provided_evidence_capabilities": ["official_document"],
                   "effective_article_mode": "DATA_OR_DOCUMENT_LENS", "story_type": "FOUNDATION_RESEARCH"}
        blockers = validate_generated_article(article, context=context, visual_asset_ids=[])
        # Exact spans and permissions were independently verified by RetainedSourceResearch.
        # This deterministic gate does not assess the quality of qualitative inference.
        validation = {"status": "PASS" if not blockers else "BLOCKED", "blockers": blockers,
                      "validator": "existing_grounded_article_validator", "material_claim_lineage": lineage,
                      "semantic_editorial_review": "REQUIRED", "qualified_simple_article": False}
        media = ([build_source_comparison_card([docs[0], docs[-1]], output_dir=folder,
                    title="Policy rates and custody proposals answer different questions")]
                 if brief["brief_id"] == "cross-asset-price-versus-custody"
                 else build_source_backed_media_assets(context, output_dir=folder, required_asset_count=1))
        for asset in media:
            raw = Path(asset["path"]).read_bytes()
            if len(raw) <= 1_500_000 and hashlib.sha256(raw).hexdigest() == asset["sha256"]:
                asset["preview_data_url"] = "data:image/png;base64," + base64.b64encode(raw).decode()
        previews = build_native_derivative_payloads(article=article, selection={},
            canonical_url="https://capitalchronicle.substack.com/p/pending-publication-" + sha256_of(article)[:16],
            media_asset_ids=())
        dump(folder / "article.json", article)
        dump(folder / "validation.json", validation)
        dump(folder / "native_previews.json", previews)
        dump(folder / "media.json", media)
        packages.append({"brief_id": brief["brief_id"], "brief_sha256": brief["brief_sha256"], "article_identity": sha256_of(article),
                         "stage": "EDITOR_AUTHORED_RESEARCH_PACKAGE", "article": article,
                         "validation": validation, "media_assets": media, "previews": previews,
                         "qualified": False, "published": False, "fresh_provider_draft": False})
        persist_research_package(tracker, packages[-1], research_revision=research.revision)
    from live_contentops.contentops_main_headline_projection_v1 import MainHeadlineExporter
    exported = MainHeadlineExporter(tracker.store, research=research).export(
        batch_id="goal21-library-independent-research", paths=[], cutoff_utc=cutoff)
    dump(output / "independent_main_context_projection.json", exported)
    dump(output / "packages.json", packages)
    dump(output / "workspace.json", report_workspace_projection(tracker.store.list_outbox_messages()))
    receipt = {"status": "RENDERED_EDITORIAL_RESEARCH_REVIEW_REQUIRED", "observed_at_utc": cutoff,
               "useful_families": library["counts"]["useful_families"], "independent_items": library["counts"]["independent_items"],
               "independent_documents": library["counts"]["independent_documents"],
               "main_context_projections_prepared": exported["eligible_rows"],
               "main_context_projection_gaps": exported["gaps"],
               "main_context_received_by_Main": "NOT_VERIFIED_THIS_GOAL",
               "briefs": len(library["briefs"]), "editor_authored_packages": len(packages),
               "native_previews": sum(len(p["previews"]) for p in packages),
               "media": sum(len(p["media_assets"]) for p in packages),
               "deterministic_validation_blockers": {p["brief_id"]: p["validation"]["blockers"] for p in packages if p["validation"]["blockers"]},
               "fresh_provider_calls": 0, "injected_model_callbacks": 0, "qualified_simple_articles": 0,
               "public_writes": 0, "runtime_started": False, "schedule_started": False,
               "actual_render_inspection": "PENDING", "main_multi_asset_readback": "PENDING_MAIN_IMMUTABLE_BATCH"}
    dump(output / "receipt.json", receipt)
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--store", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(render(a.root, a.output_dir, a.store)))
