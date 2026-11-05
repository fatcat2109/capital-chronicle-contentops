"""CC-283, 5 Nov PPI: the composed run checks every composer box against the payload before the click.

The X thread's third reply went out without its first paragraph, and only a public correction reply
completed it; nothing compared the composer with the approved posts before the click. X also waited
14 min 40 s between its claim and its click, behind LinkedIn evidence work; its own run took 1 min 42 s.
Controlled protocol checks only; these fixtures do not prove a browser action.
"""
from live_contentops.native_neo_executor_v1 import expected_posts
from test_native_neo_composed_run_cc283 import composed_setup, pending_publish

PPI_THREAD = {"text": "September PPI: energy drove the goods surge as services rose",
              "posts": [{"text": "September PPI: energy drove the goods surge as services rose", "media_asset_ids": ["c"]},
                        {"text": "Watch: a lasting signal would require repeated gains outside energy.", "media_asset_ids": []},
                        {"text": "Retrospective analysis, written on 5 November 2026 (GMT+7) Analysis, not financial "
                                 "advice.\n\nReaders decide whether to trade.", "media_asset_ids": []}]}


def test_the_run_checks_every_post_before_the_click(tmp_path, monkeypatch):
    store, executor, coordinator, ids, value = composed_setup(tmp_path, monkeypatch)
    packet = pending_publish(coordinator, store, ids, value, executor)
    run = executor.begin(packet["request"]["request_sha256"])["composed_run"]
    assert [key for key in run if key[0].isdigit()] == [
        "1_identity", "2_compose", "3_verify_before_click", "4_publish", "5_readback"]
    verify = run["3_verify_before_click"]
    assert verify["posts"] == expected_posts(packet["request"]) and verify["posts"]
    for words in ("Before the click", "FAILED_BEFORE_WRITE", "definite_no_write true",
                  "BEFORE_PUBLISH_CLICK", "no click", "no box missing or extra"):
        assert words in verify["rule"], words
    assert "pre_click_posts" in run["return"]["composed"]
    assert "whole text in one operation" in run["2_compose"] and "has focus" in run["2_compose"]
    assert "replaces the request's steps list" in run["one_run"]
    assert "at once" in run["after_run"] and "wait until every destination has gone out" in run["after_run"]


def test_a_thread_is_checked_post_by_post_with_its_paragraphs():
    posts = expected_posts({"native_payload": PPI_THREAD})
    assert posts == [post["text"] for post in PPI_THREAD["posts"]]
    assert posts[2].startswith("Retrospective analysis")  # the paragraph X lost on 5 Nov
    assert posts[2].endswith("Readers decide whether to trade.")


def test_a_single_text_payload_is_one_post():
    assert expected_posts({"native_payload": {"text": "One LinkedIn company post"}}) == ["One LinkedIn company post"]
    assert expected_posts({"native_payload": "A plain post"}) == ["A plain post"]
    assert expected_posts({"payload": {"text": "From the plan payload"}}) == ["From the plan payload"]
    assert expected_posts({"native_payload": {}}) == []
