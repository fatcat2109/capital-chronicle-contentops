"""CLI boundary for one zero-write simple Gemini V1 newsroom opportunity.

The script is intentionally not a scheduler and never crosses a public-write boundary. A
future local scheduler may call this exact entrypoint only after the zero-write host canary
is accepted. Until then it is a manual/proof runner over the canonical production
orchestrator operation.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

# Direct-file execution sets sys.path[0] to ``scripts/`` rather than the repository root.
# Bootstrap only the repository import root so the documented ``python scripts/...`` entrypoint
# behaves the same as an installed/package invocation without changing runtime authority.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_repo_root_text = str(_REPO_ROOT)
if _repo_root_text not in sys.path:
    sys.path.insert(0, _repo_root_text)

from live_contentops.production_orchestrator_v1 import ContentOpsProductionOrchestrator
from live_contentops.daily_app_launcher_v1 import (
    CANONICAL_PRODUCTION_OUTPUT_ROOT,
    CANONICAL_PRODUCTION_STORE_PATH,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.published_corpus_read_model_v1 import load_published_corpus


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_canonical_published_memory_read_only(
    *, store_path: str | Path, output_root: str | Path
) -> tuple[list[object], dict[str, object]]:
    """Project canonical reconciled publication memory without migration or mutation."""
    path = Path(store_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"canonical_production_store_missing:{path}")
    before = path.stat()
    store = ContentOpsDurableStore(path, auto_migrate=False)
    corpus = load_published_corpus(store, output_root=Path(output_root).resolve())
    after = path.stat()
    unchanged = (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    if not unchanged:
        raise RuntimeError("canonical_production_store_changed_during_read_only_projection")
    articles = list(corpus.get("articles") or [])
    proof: dict[str, object] = {
        "schema_version": "contentops.v1_simple_published_memory_access.v1",
        "corpus_schema_version": corpus.get("schema_version"),
        "canonical_reconciled_article_count": len(articles),
        "store_access_mode": "SQLITE_MODE_RO_QUERY_ONLY",
        "auto_migrate": False,
        "production_store_unchanged_during_projection": True,
        "second_publication_store_created": False,
    }
    return articles, proof


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one zero-write V1 simple Gemini newsroom opportunity."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Explicit isolated output directory for the opportunity.",
    )
    parser.add_argument(
        "--cutoff-utc",
        default=None,
        help="ISO-8601 UTC cutoff. Defaults to the current UTC instant.",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional stable run identity. Defaults to the output directory name.",
    )
    parser.add_argument(
        "--published-memory-store",
        default=str(CANONICAL_PRODUCTION_STORE_PATH),
        help="Canonical production store opened read-only with migrations disabled.",
    )
    parser.add_argument(
        "--published-memory-output-root",
        default=str(CANONICAL_PRODUCTION_OUTPUT_ROOT),
        help="Canonical publication artifact root used by the existing corpus read model.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    cutoff_utc = str(args.cutoff_utc or _utc_now())
    published_memory, memory_proof = load_canonical_published_memory_read_only(
        store_path=args.published_memory_store,
        output_root=args.published_memory_output_root,
    )
    result = ContentOpsProductionOrchestrator().execute(
        "run_v1_simple_gemini_newsroom",
        output_dir=output_dir,
        cutoff_utc=cutoff_utc,
        run_id=args.run_id or output_dir.name,
        published_memory=published_memory,
    )
    memory_path = output_dir / "published_memory_access_v1.json"
    memory_path.write_text(
        json.dumps(memory_proof, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    result = {
        **dict(result),
        "published_memory_access": memory_proof,
        "published_memory_access_path": str(memory_path),
    }
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if str(result.get("classification") or "").startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
