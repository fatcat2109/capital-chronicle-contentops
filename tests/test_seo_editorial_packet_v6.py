from live_contentops import seo_editorial_packet_v6 as seo_packet

def test_seo_packet_creation():
    article = {
        "article_id": "art_123"
    }
    seo = seo_packet.create_seo_editorial_packet(
        article_packet=article,
        primary_keyword="treasury volatility",
        secondary_keywords=["yields"],
        title_candidates=["Analyzing Treasury Volatility", "Study of Treasury Yields"],
        meta_description="A historical yield volatility study.",
        limitations_preserved=True
    )
    assert seo["seo_packet_id"].startswith("seo_")
    assert seo["article_id"] == "art_123"
    assert "Analyzing Treasury Volatility" in seo["title_candidates"]
    assert seo["limitations_preserved"] is True
    assert seo["blockers"] == []

def test_seo_cannot_remove_caveats():
    article = {
        "article_id": "art_123"
    }
    seo = seo_packet.create_seo_editorial_packet(
        article_packet=article,
        primary_keyword="treasury volatility",
        secondary_keywords=["yields"],
        title_candidates=["Analyzing Treasury Volatility"],
        meta_description="A historical yield volatility study.",
        limitations_preserved=False # removed caveats
    )
    assert "limitations_must_be_preserved" in seo["blockers"]

def test_clickbait_titles_are_rejected():
    article = {
        "article_id": "art_123"
    }
    seo = seo_packet.create_seo_editorial_packet(
        article_packet=article,
        primary_keyword="treasury volatility",
        secondary_keywords=["yields"],
        title_candidates=["10x your money", "Treasury yields to the moon", "Vol Study"],
        meta_description="A historical yield volatility study.",
        limitations_preserved=True
    )
    assert "10x your money" in seo["rejected_clickbait"]
    assert "Treasury yields to the moon" in seo["rejected_clickbait"]
    assert "Vol Study" in seo["title_candidates"]

def test_trade_call_meta_description_is_blocked():
    article = {
        "article_id": "art_123"
    }
    seo = seo_packet.create_seo_editorial_packet(
        article_packet=article,
        primary_keyword="treasury volatility",
        secondary_keywords=["yields"],
        title_candidates=["Analyzing Volatility"],
        meta_description="Here is our price target buy signal for treasury bills.",
        limitations_preserved=True
    )
    assert "trade_call_phrasing_detected_in_seo" in seo["blockers"]
