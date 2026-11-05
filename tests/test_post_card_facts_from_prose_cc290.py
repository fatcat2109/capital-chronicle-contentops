"""CC-290 (IBM, 5 Nov; CC-199 timing): a data card is built only from the post's own
sentences, the set post_image_view admits, so the handoff card and the Substack image are
one card from the start.

The IBM run (cc124-next-article-20261105-c, CC-124 run-20261105-1051) wrote three sentences
for its card and bound them to a stub article made of those sentences. post_image_view binds
to the canonical prose, excluded that card and fell back to its own, and Substack waited 18
minutes. Fixture: tests/evidence/cc-290/ibm-run-20261105-1051.json, verbatim from the run.
"""
import json
from pathlib import Path

from live_contentops.post_visuals_v1 import build_post_data_card, validate_post_data_card
from live_contentops.rolling_x_grounded_article_media_builder_v1 import post_image_view

FIXTURE = Path(__file__).parent / "evidence" / "cc-290" / "ibm-run-20261105-1051.json"


def ibm():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return data["article"], data["claims"], [data["document"]], data


def publication_view(article, card, documents, tmp_path):
    return post_image_view({"article": dict(article), "evidence": documents, "media_assets": [card],
                            "accepted_evidence_sha256": "e" * 64}, output_dir=tmp_path / "publication")


def test_ibm_card_comes_from_the_canonical_prose_and_post_image_view_keeps_it(tmp_path):
    article, claims, documents, _ = ibm()
    body = article["substack_body_markdown"]
    assert not any(claim["claim_text"] in body for claim in claims)      # the run's card sentences
    card = build_post_data_card(article, claims, documents, output_dir=tmp_path)
    facts = [fact["text"] for fact in card["data_card_packet"]["facts"]]
    # The post's own sentence with the quarterly figures. The outlook sentence also carries the
    # report date, which the Reuters text does not state, so post_image_view would refuse it.
    assert facts == ["Reuters put third-quarter total revenue at $17.10 billion, with software revenue of $7.80 billion."]
    assert all(fact in body for fact in facts)
    validate_post_data_card(card, article, documents)
    policy = publication_view(article, card, documents, tmp_path)["post_image_policy"]
    assert policy["excluded_optional_assets"] == [] and policy["default_asset_id"] == card["asset_id"]
    assert {asset_id for ids in policy["channel_media"].values() for asset_id in ids} == {card["asset_id"]}


def test_the_stub_bound_handoff_card_is_the_one_post_image_view_excluded(tmp_path):
    """The handoff as the run built it: the card's own sentences standing in for the article."""
    article, claims, documents, data = ibm()
    stub = {"title": data["handoff_stub_title"],
            "substack_body_markdown": "\n\n".join(claim["claim_text"] for claim in claims)}
    card = build_post_data_card(stub, claims, documents, output_dir=tmp_path)
    assert [f["text"] for f in card["data_card_packet"]["facts"]] == [claim["claim_text"] for claim in claims]
    policy = publication_view(article, card, documents, tmp_path)["post_image_policy"]
    assert [e["cause"] for e in policy["excluded_optional_assets"]] == ["DATA_CARD_FACT_OR_NUMBER_NOT_IN_POST_AND_SOURCE"]
    assert policy["default_asset_id"] != card["asset_id"]


def test_a_claim_the_post_states_in_its_own_words_is_unchanged(tmp_path):
    article, claims, documents, _ = ibm()
    own = [{**claims[1], "claim_text": "Reuters put third-quarter total revenue at $17.10 billion, with software "
                                       "revenue of $7.80 billion."}]
    card = build_post_data_card(article, own, documents, output_dir=tmp_path)
    assert [f["text"] for f in card["data_card_packet"]["facts"]] == [own[0]["claim_text"]]
