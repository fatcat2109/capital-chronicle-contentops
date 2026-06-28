from live_contentops import content_idea_packet_v6 as idea_packet

def test_content_idea_packet_construction():
    packet = idea_packet.create_content_idea_packet(
        idea_text="Analyzing Treasury Volatility",
        operator_name="Jim",
        source_context={"ref": "Fed H.15"},
        target_audience="general"
    )
    assert packet["idea_id"].startswith("idea_")
    assert packet["operator_name"] == "Jim"
    assert packet["idea_text"] == "Analyzing Treasury Volatility"
    assert packet["source_context"] == {"ref": "Fed H.15"}
    assert packet["target_audience"] == "general"
    assert packet["grounding_required"] is True
    assert packet["schema_version"] == "6.0.0"
