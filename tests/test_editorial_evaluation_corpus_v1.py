from __future__ import annotations

import copy
import json
from pathlib import Path

from live_contentops.editorial_evaluation_corpus_v1 import verify_editorial_evaluation_corpus

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "config" / "editorial_evaluation_corpus_v1.json"


def _corpus() -> dict:
    return json.loads(CORPUS.read_text(encoding="utf-8"))


def test_canonical_editorial_evaluation_corpus_passes() -> None:
    result = verify_editorial_evaluation_corpus(_corpus())
    assert result["status"] == "PASS"
    assert result["blockers"] == []
    assert result["summary"]["case_count"] == 12
    assert result["summary"]["story_type_count"] >= 5
    assert result["summary"]["accepted_count"] > 0
    assert result["summary"]["rejected_count"] > 0
    assert result["summary"]["pairwise_count"] >= 3
    assert len(result["corpus_logical_hash"]) == 64
    assert result["publication_authority"] is False


def test_corpus_verifier_fails_closed_on_missing_required_class() -> None:
    corpus = _corpus()
    for row in corpus["cases"]:
        row["coverage_labels"] = [label for label in row["coverage_labels"] if label != "proxy_misuse"]
    result = verify_editorial_evaluation_corpus(corpus)
    assert result["status"] == "BLOCKED"
    assert "required_coverage_missing:proxy_misuse" in result["blockers"]


def test_corpus_verifier_rejects_incomplete_human_rubric() -> None:
    corpus = copy.deepcopy(_corpus())
    corpus["cases"][0]["human_rubric"].pop("accuracy")
    result = verify_editorial_evaluation_corpus(corpus)
    assert result["status"] == "BLOCKED"
    assert any("rubric_fields_missing:accuracy" in blocker for blocker in result["blockers"])


def test_corpus_verifier_rejects_pair_direction_reversal() -> None:
    corpus = _corpus()
    pair = corpus["pairwise_judgments"][0]
    pair["preferred_case_id"], pair["rejected_case_id"] = pair["rejected_case_id"], pair["preferred_case_id"]
    result = verify_editorial_evaluation_corpus(corpus)
    assert result["status"] == "BLOCKED"
    assert any("pair_direction_invalid" in blocker for blocker in result["blockers"])
