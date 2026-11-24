"""Ops Product, 24 Nov 2026: CME FedWatch odds stay in words in public copy, like Kalshi's and Polymarket's.

Jim (24 Nov, 01:32Z) has Main use Kalshi, Polymarket and CME FedWatch odds fully; inside Main nothing changes.
CME's Data Terms of Use allow its website data for personal, non-commercial use only (decision 44), so a
FedWatch number is left out or refused in every public output, while words about rate pricing stay allowed.
"""
from __future__ import annotations

import re

import pytest

from live_contentops import event_article_guard_v1 as guard
from live_contentops import market_wrap_sources_v1 as wrap_sources
from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_status_posts_v1 as posts

WORDS = "Rate futures lean toward a December hold."
NUMBERS = ("CME FedWatch puts a December hold at 68%.", "FedWatch shows 68% odds of a hold.",
           "The rate-cut probability is 32% for December.")


@pytest.mark.parametrize("sentence", NUMBERS)
def test_plan_posts_drop_a_fedwatch_sentence_and_keep_the_words(sentence):
    assert posts.PRIVATE_RATIONALE.search(sentence)
    assert posts._public_reason(sentence + " " + WORDS) == WORDS
    assert not posts.PRIVATE_RATIONALE.search(WORDS)


def test_plan_pages_refuse_a_fedwatch_number_and_admit_the_words():
    with pytest.raises(ValueError, match="PLAN_ANALYSIS_PREDICTION_MARKET_NUMBERS_FORBIDDEN"):
        pages.check_reader_claim("Futures price a 68% chance of a December hold.", source_name="CME FedWatch")
    with pytest.raises(ValueError, match="PLAN_ANALYSIS_PREDICTION_MARKET_NUMBERS_FORBIDDEN"):
        pages.check_reader_claim(NUMBERS[0])
    pages.check_reader_claim(WORDS, source_name="CME FedWatch")


@pytest.mark.parametrize("sentence", NUMBERS)
def test_event_articles_refuse_a_number_beside_fedwatch(sentence):
    with pytest.raises(guard.PublicOutputError, match="PREDICTION_MARKET_NUMBER_FORBIDDEN"):
        guard.check_publication_copy({"body": sentence}, require_notice=False)


def test_event_articles_keep_fedwatch_in_words():
    guard.check_publication_copy({"body": WORDS + " CME FedWatch leans the same way."}, require_notice=False)


def test_wraps_leave_a_fedwatch_line_out_and_keep_the_words():
    for sentence in NUMBERS + ("CME FedWatch leans toward a hold.",):
        assert wrap_sources.safe_prose(sentence) is None
    assert wrap_sources.safe_prose(WORDS) == WORDS


def test_main_report_spans_refuse_a_number_beside_fedwatch():
    span = re.compile(r"(?:Kalshi|Polymarket|prediction.market|" + guard.FEDWATCH_PATTERN + r").{0,80}\d", re.I)
    assert all(span.search(sentence) for sentence in NUMBERS)
    assert not span.search(WORDS + " CME FedWatch leans the same way.")
