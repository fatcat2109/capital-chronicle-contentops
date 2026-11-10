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


def test_exact_whole_text_reflow_is_recorded_without_losing_a_word(tmp_path, monkeypatch):
    store, executor, coordinator, ids, value = composed_setup(tmp_path, monkeypatch)
    packet = pending_publish(coordinator, store, ids, value, executor)
    key = packet["request"]["request_sha256"]
    executor.begin(key)
    original = expected_posts(packet["request"])
    words = original[0].split()
    reflow = [words[0], " ".join(words[1:]), *original[1:]]
    executor.submit(key, composed_response(packet, identity=MATCHED, result=PUBLISHED,
        readback=True, pre_click_posts=reflow))
    assert executor._get(key, "response")["result"]["pre_click_verification"] == "MATCHED_REFLOWED_THREAD"


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


# 5 Nov IBM: the X return came back with composed.identity only. It had no pre_click_posts and no click
# clock, and was accepted, so nothing showed the check before the click had run.
import pytest  # noqa: E402

from test_native_neo_composed_run_cc283 import MATCHED, PUBLISHED, composed_response  # noqa: E402


def test_a_write_without_the_pre_click_texts_is_refused_before_it_is_saved(tmp_path, monkeypatch):
    store, executor, coordinator, ids, value = composed_setup(tmp_path, monkeypatch)
    packet = pending_publish(coordinator, store, ids, value, executor)
    request_hash = packet["request"]["request_sha256"]
    executor.begin(request_hash)
    with pytest.raises(ValueError, match="NATIVE_NEO_PRE_CLICK_POSTS_REQUIRED"):
        executor.submit(request_hash, composed_response(packet, identity=MATCHED, result=PUBLISHED, pre_click_posts=None))
    assert executor._get(request_hash, "response") is None  # nothing saved; the run may resubmit what it read
    executor.submit(request_hash, composed_response(packet, identity=MATCHED, result=PUBLISHED))
    stored = executor._get(request_hash, "response")["result"]
    assert stored["pre_click_verification"] == "MATCHED" and "click_clock" not in stored


def test_a_lost_return_is_read_back_never_resent(tmp_path, monkeypatch):
    store, executor, coordinator, ids, value = composed_setup(tmp_path, monkeypatch)
    packet = pending_publish(coordinator, store, ids, value, executor)
    executor.begin(packet["request"]["request_sha256"])
    # The run did not read the composer, so it submits nothing: the claim stays without a return.
    assert executor(packet["request"])["status"] == "UNKNOWN_WRITE"


def test_differing_texts_and_a_missing_click_clock_are_recorded(tmp_path, monkeypatch):
    store, executor, coordinator, ids, value = composed_setup(tmp_path, monkeypatch)
    packet = pending_publish(coordinator, store, ids, value, executor)
    request_hash = packet["request"]["request_sha256"]
    executor.begin(request_hash)
    posts = expected_posts(packet["request"])
    executor.submit(request_hash, composed_response(packet, identity=MATCHED, result=PUBLISHED, dispatched=False,
                                                    readback=True, pre_click_posts=[posts[0][:-5]] + posts[1:]))
    stored = executor._get(request_hash, "response")["result"]
    assert stored["pre_click_verification"] == "DIFFERED" and stored["click_clock"] == "NOT_RETURNED"


def test_whitespace_quotes_and_a_shortened_link_still_match():
    from live_contentops.native_neo_executor_v1 import _post_texts
    assert _post_texts(["It\u2019s here:\n\nhttps://capitalchronicle.substack.com/p/a"]) == \
        _post_texts(["It's  here: https://t.co/xyz"])
    assert _post_texts(["Readers decide."]) != _post_texts(["Readers decide whether to trade."])


# CC-199, 5 Nov IBM: X, YouTube and LinkedIn company returned without their in-run readback, so each
# waited for a separate readback turn; the last landed at 06:33:38Z, 17 min after the last click.
def test_a_write_without_its_in_run_readback_is_refused_before_it_is_saved(tmp_path, monkeypatch):
    store, executor, coordinator, ids, value = composed_setup(tmp_path, monkeypatch)
    packet = pending_publish(coordinator, store, ids, value, executor)
    request_hash = packet["request"]["request_sha256"]
    run = executor.begin(request_hash)["composed_run"]
    assert "no separate readback turn follows" in run["5_readback"]
    assert run["return"]["composed"]["readback"].startswith("REQUIRED")
    with pytest.raises(ValueError, match="NATIVE_NEO_IN_RUN_READBACK_REQUIRED"):
        executor.submit(request_hash, composed_response(packet, identity=MATCHED, result=PUBLISHED, readback=False))
    assert executor._get(request_hash, "response") is None


def test_the_in_run_readback_confirms_the_destination_even_without_a_click_clock(tmp_path, monkeypatch):
    from test_native_neo_composed_run_cc283 import OBJECT_ID, OBJECT_URL
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
    store, executor, coordinator, ids, value = composed_setup(tmp_path, monkeypatch)
    packet = pending_publish(coordinator, store, ids, value, executor)
    request_hash = packet["request"]["request_sha256"]
    executor.begin(request_hash)
    executor.submit(request_hash, composed_response(packet, identity=MATCHED, result=PUBLISHED, dispatched=False))
    assert executor._get(request_hash, "response")["result"]["click_clock"] == "NOT_RETURNED"
    reread = NeoDestinationHandoff(native_executor=executor).readback(
        destination=packet["request"]["destination"], intent=value, public_object_id=OBJECT_ID, public_object_url=OBJECT_URL)
    assert reread["verified"] is True
    assert [p for p in executor.pending() if not p.get("action_claimed")] == []  # no separate readback turn


def test_an_in_run_readback_with_its_media_check_pending_is_not_reused(tmp_path, monkeypatch):
    """5 Nov EIA: reusing it recorded X as CONTENT_INCOMPLETE and the image was never compared."""
    from test_native_neo_composed_run_cc283 import OBJECT_ID, OBJECT_URL
    from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
    store, executor, coordinator, ids, value = composed_setup(tmp_path, monkeypatch)
    packet = pending_publish(coordinator, store, ids, value, executor)
    request_hash = packet["request"]["request_sha256"]
    executor.begin(request_hash)
    response = composed_response(packet, identity=MATCHED, result=PUBLISHED)
    response["composed"]["readback"]["media_check_state"] = "PENDING_BINARY_COMPARISON"
    executor.submit(request_hash, response)
    assert executor._get(request_hash, "response")["result"]["in_run_readback_media"] == "PENDING_BINARY_COMPARISON"
    with pytest.raises(NativeNeoInputRequired):  # the full readback is requested, not decided from the pending one
        NeoDestinationHandoff(native_executor=executor).readback(
            destination=packet["request"]["destination"], intent=value, public_object_id=OBJECT_ID,
            public_object_url=OBJECT_URL)

@pytest.fixture(autouse=True)
def x_neo_bar_lifted_for_the_sample(monkeypatch):
    """These tests use X as the sample destination for the Neo publishing machinery, which Substack, LinkedIn
    company and YouTube still use. In production no X write goes through Neo (X's rules; Jim's scan answers, item 3),
    and that bar has its own tests in test_x_no_website_automation.py."""
    from live_contentops import neo_destination_handoff_v1
    monkeypatch.setattr(neo_destination_handoff_v1, "NON_API_AUTOMATION_PROHIBITED", {})
