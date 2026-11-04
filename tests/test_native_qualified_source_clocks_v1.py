"""The qualified consumer retains an absent optional source-clock spelling."""
import live_contentops.v1_simple_gemini_newsroom_v1 as newsroom
from tests.test_native_text_first_v1 import brief_packet


def test_qualified_native_consumer_uses_utc_clock_without_inventing_source_spelling(tmp_path, monkeypatch):
    original = newsroom._source_pack

    def without_optional_spelling(*args, **kwargs):
        docs = original(*args, **kwargs)
        for doc in docs:
            doc.pop("published_at_source", None)
        return docs

    monkeypatch.setattr(newsroom, "_source_pack", without_optional_spelling)
    _, _, _, result, stages, _ = brief_packet(tmp_path, monkeypatch)
    assert result["qualified_article_count"] == 1
    assert stages == ["select", "write"]
    plan = result["simple_result"]["publication_lifecycle_plan"]
    assert plan["accepted_evidence_sha256"]
    assert result["evidence"][0]["published_at_utc"]
    assert "published_at_source" not in result["evidence"][0]
