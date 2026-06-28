from live_contentops import research_grounding_packet_v6 as grounding_packet

def test_missing_source_evidence_blocks():
    packet = grounding_packet.construct_research_grounding_packet(
        topic="test topic",
        source_refs=[],
        freshness_status="fresh"
    )
    assert packet["allowed_for_drafting"] is False
    assert packet["allowed_for_publication"] is False
    assert "source_evidence_missing" in packet["blocked_reasons"]

def test_unknown_freshness_blocks_publication_but_allows_drafting():
    packet = grounding_packet.construct_research_grounding_packet(
        topic="test topic",
        source_refs=["official ref"],
        official_source_refs=["official ref"],
        freshness_status="unknown"
    )
    assert packet["allowed_for_drafting"] is True
    assert packet["allowed_for_publication"] is False
    assert "source_freshness_unverified" in packet["blocked_reasons"]

def test_unsupported_claims_block_publication():
    packet = grounding_packet.construct_research_grounding_packet(
        topic="test topic",
        source_refs=["official ref"],
        official_source_refs=["official ref"],
        freshness_status="fresh",
        unsupported_claims=["invented yield numbers"]
    )
    assert packet["allowed_for_publication"] is False
    assert "unsupported_claims_present" in packet["blocked_reasons"]
