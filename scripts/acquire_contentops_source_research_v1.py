"""Bounded manual official research, using the existing source acquisition owner.

Retains exact bytes, loader result and policy captures. No model/runtime/public write.
The source plan is explicit and text-only; unknown/restricted authorship is rejected
by RetainedSourceResearch before any text can enter the return feed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.official_primary_evidence_loader_v1 import (
    BoundedOfficialPrimaryEvidenceLoader,
    _default_http_get,
)
from live_contentops.contentops_source_research_v1 import (
    SCHEMA,
    POLICIES,
    RetainedSourceResearch,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error("Use a new immutable acquisition directory")
    plan = json.loads(args.plan.read_bytes())
    if not 1 <= len(plan) <= 3:
        parser.error("At most three exact official documents per bounded acquisition")
    args.output_dir.mkdir(parents=True)
    captures, gaps, records, used = {}, [], [], 0

    def get(url, timeout, max_bytes):
        nonlocal used
        if used >= 6:
            raise ValueError("SHARED_SIX_GET_ACQUISITION_BUDGET_EXHAUSTED")
        used += 1
        result = _default_http_get(url, timeout, max_bytes)
        captures[url] = result
        return result

    loader = BoundedOfficialPrimaryEvidenceLoader(
        evaluation_as_of_utc=datetime.now(timezone.utc).isoformat(),
        max_requests=3,
        http_get=get,
    )
    for item in plan:
        key = item["headline_id"]
        if not key.replace("-", "").isalnum():
            raise ValueError("PLAN_ID_INVALID")
        result = loader(
            {
                "headline_ids": [key],
                "cluster_id": key,
                "source_adapter_families": ["official_macro"],
                "required_evidence_capabilities": [],
                "story_context": {
                    "official_source_url_bindings": [
                        {
                            "headline_id": key,
                            "url": item["url"],
                            "published_at_utc": item["published_at_utc"],
                        }
                    ]
                },
            }
        )
        (args.output_dir / (key + "-loader.json")).write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        if result["status"] != "PASS":
            gaps.append(
                {
                    "headline_id": key,
                    "state": "SOURCE_ACQUISITION_BLOCKED",
                    "blockers": result["blockers"],
                }
            )
            continue
        doc = result["official_source_documents"][0]
        from urllib.parse import urlsplit

        policy_url = POLICIES[urlsplit(doc["source_url"]).hostname][0]
        if policy_url not in captures:
            get(policy_url, 12, 2_000_000)
        policy = captures[policy_url]
        if (
            policy["status"] != 200
            or policy.get("content_truncated")
            or policy["final_url"] != policy_url
        ):
            gaps.append(
                {"headline_id": key, "state": "SOURCE_PERMISSION_CAPTURE_BLOCKED"}
            )
            continue
        policy_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        raw = captures[item["url"]]["body"]
        (args.output_dir / (key + "-source.html")).write_bytes(raw)
        (args.output_dir / (key + "-policy.html")).write_bytes(policy["body"])
        text = doc["canonical_content_text"]
        start = text.index(item["proposition_start"])
        end = text.index(item["proposition_end"], start) + len(item["proposition_end"])
        records.append(
            {
                "headline_id": key,
                "capture_path": key + "-source.html",
                "loader_result_path": key + "-loader.json",
                "policy_capture_path": key + "-policy.html",
                "policy_url": policy_url,
                "policy_capture_sha256": hashlib.sha256(policy["body"]).hexdigest(),
                "policy_retrieved_at_utc": policy_time,
                "source_capture_sha256": hashlib.sha256(raw).hexdigest(),
                "revision_at_utc": policy_time,
                "proposition_span": [start, end],
                "headline_text": " ".join(text[start:end].split()),
                "candidate_catalyst_tags": item.get("candidate_catalyst_tags", []),
            }
        )
    (args.output_dir / "index.json").write_text(
        json.dumps({"schema_version": SCHEMA, "records": records}, indent=2) + "\n",
        encoding="utf-8",
    )
    verified = RetainedSourceResearch(args.output_dir)
    receipt = {
        "network_gets": used,
        "acquired_documents": len(records),
        "admitted_independent_items": len(verified.records),
        "gaps": gaps + verified.gaps,
        "fresh_model_calls": 0,
        "public_writes": 0,
    }
    (args.output_dir / "acquisition_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
