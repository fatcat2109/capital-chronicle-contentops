from __future__ import annotations

from headline_ingestion.Data_Ingestion import recursive_tweet_extractor


def test_x_ingestion_preserves_expanded_link_binding_without_granting_authority():
    payload = {
        "legacy": {
            "id_str": "123",
            "created_at": "Sat Aug 08 10:30:00 +0000 2026",
            "full_text": "Official update https://t.co/abc",
            "entities": {
                "urls": [{
                    "url": "https://t.co/abc",
                    "expanded_url": "https://api.federalregister.gov/v1/documents/2026-12345.json",
                }]
            },
        },
        "core": {"screen_name": "OfficialAgency"},
    }

    rows = recursive_tweet_extractor(payload)

    assert len(rows) == 1
    assert rows[0]["tweet_id"] == "123"
    assert rows[0]["linked_urls"] == [
        "https://api.federalregister.gov/v1/documents/2026-12345.json"
    ]
    assert rows[0]["tweet_url"] == "https://x.com/OfficialAgency/status/123"
