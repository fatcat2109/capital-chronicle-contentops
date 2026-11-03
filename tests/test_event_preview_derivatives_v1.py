"""Exact retained preview corrections keep copy, notice and link boundaries."""
from copy import deepcopy
import json
from pathlib import Path

from live_contentops.event_article_guard_v1 import CONFLICTS_NOTICE, check_publication_copy
from live_contentops.v1_simple_gemini_newsroom_v1 import _native_preview_bundle


def test_same_writer_linkless_repair_compiles_all_eight_without_placeholder_or_lost_notices():
    root = Path(__file__).resolve().parents[1] / "docs/publisher/EVENT_ARTICLES_V1/midterm-20261103"
    result = json.loads((root / "review/final-result.json").read_bytes())
    repair = json.loads((root / "media/derivative-repair-r2.json").read_bytes())
    article = deepcopy(result["article"])
    article.update(event_preview_linkless=True,
                   event_preview_root_copy={r["destination"]: r["root_text"] for r in repair["roots"]})
    bundle, _ = _native_preview_bundle(article=article, article_mode=article["resolved_article_mode"],
        article_identity=result["article_identity"], epistemic_state=article["epistemic_state"],
        media_asset_ids=[a["asset_id"] for a in result["media_assets"]], media_assets=result["media_assets"])
    assert len(bundle["packages"]) == 8
    for destination, payload in bundle["packages"].items():
        reader = payload.get("full_text") or payload["text"]
        assert "pending-publication" not in reader and "Full brief: " not in reader
        assert "Read the article:" not in reader and "Read the full brief:" not in reader
        assert CONFLICTS_NOTICE in reader
        assert check_publication_copy({"text": reader})["status"] == "PASS"
        if destination in {"x", "threads"}:
            assert payload["root_text"] == article["event_preview_root_copy"][destination]
            assert len(payload["root_text"]) <= payload["platform_limit"]
            assert CONFLICTS_NOTICE in payload["root_text"]
            assert payload["quality_metrics"]["sentence_boundary_pass"]
    assert not bundle["public_write_performed"]
