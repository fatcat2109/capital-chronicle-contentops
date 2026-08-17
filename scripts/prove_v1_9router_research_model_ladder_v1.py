"""Tiny bounded zero-public-write capability proof for the owner V1 research ladder."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from live_contentops.nine_router_ordered_model_router_v2 import (
    GATEWAY,
    V1_GROUNDED_RESEARCH_MODEL_LADDER,
)
from live_contentops.nine_router_provider_adapter_v2 import call_nine_router

NONCE = "CC_V1_9ROUTER_RESEARCH_LADDER_NONCE_20260817"
PROMPT = f"Return exactly this token and nothing else: {NONCE}"


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run_proof() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for position, route in enumerate(V1_GROUNDED_RESEARCH_MODEL_LADDER, start=1):
        started = time.monotonic()
        try:
            result = call_nine_router(
                PROMPT,
                route,
                60.0,
                max_tokens=32,
                temperature=0.0,
            )
            text = str(result.text or "").strip()
            success = result.failure_class is None and bool(text)
            row = {
                "provider": GATEWAY,
                "requested_route": route,
                "ladder_position": position,
                "request_classification": "PASS_PROVIDER_ROUTE_AVAILABLE" if success else "BLOCKED_PROVIDER_ROUTE",
                "failure_class": result.failure_class,
                "returned_model_identifier": result.resolved_model,
                "response_sha256": _hash_text(text) if text else None,
                "nonce_exact_match": text == NONCE,
                "latency_seconds": round(time.monotonic() - started, 4),
            }
        except Exception as exc:  # safe class-only capability blocker; never serialize message
            row = {
                "provider": GATEWAY,
                "requested_route": route,
                "ladder_position": position,
                "request_classification": "BLOCKED_LOCAL_OR_PROVIDER_CONFIGURATION",
                "failure_class": type(exc).__name__,
                "returned_model_identifier": None,
                "response_sha256": None,
                "nonce_exact_match": False,
                "latency_seconds": round(time.monotonic() - started, 4),
            }
        rows.append(row)
    available_count = sum(
        row["request_classification"] == "PASS_PROVIDER_ROUTE_AVAILABLE" for row in rows
    )
    return {
        "schema_version": "contentops.v1_9router_research_model_ladder_capability_proof.v1",
        "task_id": "TASK_CONTENTOPS_V1_9ROUTER_RESEARCH_MODEL_LADDER_OWNER_ALIGNMENT_V1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "classification": (
            "PASS_ALL_THREE_9ROUTER_RESEARCH_ROUTES_AVAILABLE"
            if available_count == len(V1_GROUNDED_RESEARCH_MODEL_LADDER)
            else "PARTIAL_9ROUTER_RESEARCH_ROUTE_AVAILABILITY"
            if available_count
            else "BLOCKED_ALL_9ROUTER_RESEARCH_ROUTES_UNAVAILABLE"
        ),
        "provider": GATEWAY,
        "exact_ladder": list(V1_GROUNDED_RESEARCH_MODEL_LADDER),
        "route_results": rows,
        "available_route_count": available_count,
        "article_generation_calls": 0,
        "xhigh_editorial_worker_calls": 0,
        "public_write_calls": 0,
        "capital_chronicle_mutations": 0,
        "v2_mutations": 0,
        "factual_or_numeric_authority_granted": False,
        "publication_authority_granted": False,
        "secrets_persisted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    proof = run_proof()
    rendered = json.dumps(proof, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if proof["available_route_count"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
