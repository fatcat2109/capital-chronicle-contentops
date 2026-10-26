"""Materialize exact retained BrowserOS research captures through the existing verifier.

No network/provider/runtime action. The curated plan selects bounded agency-authored
spans; BrowserOS captures remain rendered evidence and never raw HTTP evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.browser_rendered_source_recovery_v1 import _canonical_rendered_text
from live_contentops.contentops_source_research_v1 import POLICIES, SCHEMA, RetainedSourceResearch


def _dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build(root: Path):
    root = root.resolve()
    plan = json.loads((root / "research_plan.json").read_bytes())
    output = root / "retained_research"
    output.mkdir(exist_ok=True)

    def capture(name):
        path = (root / "acquisition" / name).resolve()
        if not path.is_relative_to(root / "acquisition"):
            raise ValueError("CAPTURE_OUTSIDE_RESEARCH_ROOT")
        raw = path.read_bytes()
        value = json.loads(raw)
        text = value["text"]
        if not 0 < len(text) < 100_000 or "Page not Found" in value["title"]:
            raise ValueError("CAPTURE_UNUSABLE")
        envelope = {"status": "PASS", "final_url": value["url"],
                    "retrieval_method": "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE",
                    "capture_operation": "EDITORIAL_READ_ONLY_VISIBLE_TEXT",
                    "rendered_markdown": text, "rendered_page_sha256": _sha(text.encode()),
                    "canonical_content_text": _canonical_rendered_text(text),
                    "canonical_content_sha256": _sha(_canonical_rendered_text(text).encode()),
                    "retrieved_at_utc": value["captured_at_utc"], "content_truncated": False,
                    "credential_or_session_material_read": False, "public_write_performed": False,
                    "original_capture_sha256": _sha(raw)}
        target = name.replace("-content.json", "-rendered.json")
        _dump(output / target, envelope)
        return value, envelope, target

    records = []
    for item in plan["items"]:
        value, c, target = capture(item["capture"])
        host = urlsplit(value["url"]).hostname
        if item["policy"] == "REUSE_GOAL20_EIA_POLICY":
            old = root.parent / "goal20/retained_research/goal20-eia-smallscale-solar-policy.html"
            policy_name = "eia-policy-retained.html"
            shutil.copyfile(old, output / policy_name)
            policy_sha = _sha(old.read_bytes())
            policy_time = "2026-10-19T05:47:50.347840Z"
            policy_class = "RETAINED_RAW_HTTP_POLICY"
        else:
            _, p, policy_name = capture(item["policy"])
            if p["final_url"] != POLICIES[host][0]:
                raise ValueError("POLICY_FINAL_URL_MISMATCH")
            policy_sha = _sha((output / policy_name).read_bytes())
            policy_time = p["retrieved_at_utc"]
            policy_class = "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE"
        text = c["canonical_content_text"]
        start = text.index(item["start"])
        end = text.index(item["end"], start) + len(item["end"])
        if end - start > 2000:
            raise ValueError("PROPOSITION_TOO_LARGE")
        published = item["published"]
        family = {"www.federalreserve.gov": "official_policy", "www.sec.gov": "sec_regulatory",
                  "www.cftc.gov": "official_regulatory_fiscal", "www.eia.gov": "official_macro"}[host]
        doc = {"document_id": "goal21-" + item["id"], "title": value["title"],
               "source_url": value["url"], "publisher": host, "source_identity": host,
               "raw_sha256": c["rendered_page_sha256"], "canonical_content_text": text,
               "canonical_content_sha256": c["canonical_content_sha256"],
               "source_adapter_family": family, "source_authority_class": "official_public_primary_source",
               "published_at_utc": published, "publication_time_precision": "DATE_ONLY" if published and published.endswith("T00:00:00Z") else "SOURCE_RECORDED" if published else "NOT_VERIFIED",
               "published_at_source": "RETAINED_SOURCE_VISIBLE_DATE" if published else "SOURCE_UNDATED_NOT_INFERRED_FROM_CAPTURE",
               "source_modified_at_utc": item.get("source_modified_at_utc"),
               "content_truncated": False, "retrieval_method": c["retrieval_method"]}
        loader_name = item["id"] + "-retained-admission.json"
        _dump(output / loader_name, {"status": "PASS", "official_source_documents": [doc],
                                    "provenance": {"retrieved_at_utc": c["retrieved_at_utc"],
                                                   "capture_operation": c["capture_operation"], "network_calls_by_materializer": 0}})
        records.append({"headline_id": "goal21-" + item["id"], "headline_text": text[start:end],
                        "capture_path": target, "capture_class": c["retrieval_method"],
                        "source_capture_sha256": c["rendered_page_sha256"], "loader_result_path": loader_name,
                        "policy_capture_path": policy_name, "policy_capture_class": policy_class,
                        "policy_url": POLICIES[host][0], "policy_capture_sha256": policy_sha,
                        "policy_retrieved_at_utc": policy_time,
                        "revision_at_utc": max(c["retrieved_at_utc"], policy_time),
                        "proposition_span": [start, end], "candidate_catalyst_tags": [item["family"].lower()],
                        "research_metadata": {"family": item["family"], "assets": item["assets"],
                                              "context_kind": item["context_kind"], "horizons": ["short", "swing", "long"],
                                              "source_modified_at_utc": item.get("source_modified_at_utc"),
                                              "horizon_semantics": "EDITORIAL_QUESTIONS_NOT_MAIN_FORECASTS",
                                              "next_editorial_question": item["question"],
                                              "authorship_scope": "AGENCY_AUTHORED_PROSE_ONLY_NO_THIRD_PARTY_SERIES_OR_ARTWORK"}})
    _dump(output / "index.json", {"schema_version": SCHEMA, "records": records})
    research = RetainedSourceResearch(output)
    receipt = {"status": "PASS" if len(research.records) == len(records) else "GAPS",
               "independent_items": len(research.records), "families": sorted({r["research_metadata"]["family"] for r in research.records.values()}),
               "gaps": research.gaps, "raw_http_sources_claimed": 0, "fresh_provider_calls": 0,
               "private_main_reads": 0, "public_writes": 0}
    _dump(root / "research_admission.json", receipt)
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path)
    print(json.dumps(build(p.parse_args().root)))
