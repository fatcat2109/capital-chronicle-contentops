"""CC-306, 5 Nov: Telegram's freeze guard allows one post per link, and every status post about a
market links the same market page. The second EUR/USD post (a new plan, 11:16Z) was frozen before
any network call, then filed as UNKNOWN_WRITE. Controlled: no network, no real ledger."""
from __future__ import annotations

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as impl
from live_contentops.public_dispatch_freeze_guard_v6 import build_public_dispatch_identity_hashes
from live_contentops.publication_coordinator_v1 import DEFINITE_NO_WRITE, normalize_dispatch_result
from live_contentops.telegram_live_adapter_v6 import _guard_non_dry_run_telegram_action

URL = "https://t.me/CapitalChronicle"  # decision 83: the status post's guard identity, never a site link
TEXT = "EUR/USD: new plan. If price trades into 1.1274–1.1284, the desk is bullish on EUR/USD."


def guard_for(monkeypatch, *, guard_url, prior):
    """Run the helper up to the adapter call and evaluate the real guard on what it passes."""
    seen = {}

    def fake_execute(**kwargs):
        context = dict(kwargs["approval_context"], prior_dispatch_hashes=prior)
        seen["guard"] = _guard_non_dry_run_telegram_action(
            action="photo", body_text=kwargs["caption"], media_url=kwargs["photo_url"], approval_context=context)
        return {"status": "PUBLIC_DISPATCH_FROZEN" if not seen["guard"]["dispatch_allowed"] else "FAILED"}

    monkeypatch.setattr("live_contentops.telegram_live_adapter_v6.execute_telegram_photo", fake_execute)
    monkeypatch.setattr(impl, "append_public_dispatch_ledger", lambda **kw: None)
    impl._publish_telegram_photo_verified(run_id="plan-status-post-b", topic_hash="t" * 64, text=TEXT,
                                          canonical_url=URL, image_path="card-b.png", guard_canonical_url=guard_url)
    return seen["guard"]


def prior_with(url):
    hashes = build_public_dispatch_identity_hashes(platform="telegram", canonical_url=url, media_url=None, topic_hash=None)
    return {"payload_hashes": [], "canonical_url_hashes": [hashes["canonical_url_hash"]],
            "media_url_hashes": [], "topic_hashes": []}


def test_a_second_status_post_on_the_same_market_page_is_allowed(monkeypatch):
    # The first post used the plain market link (as post 82 did); the second keys on itself.
    guard = guard_for(monkeypatch, guard_url=URL + "?status_post=plan-status-post-b", prior=prior_with(URL))
    assert guard["dispatch_allowed"] is True, guard


def test_the_same_status_post_is_still_refused_as_a_duplicate(monkeypatch):
    guard = guard_for(monkeypatch, guard_url=URL + "?status_post=plan-status-post-b", prior=prior_with(URL + "?status_post=plan-status-post-b"))
    assert "duplicate_canonical_url_hash" in guard["blockers"]


def test_without_the_post_identity_the_market_link_is_refused_as_before(monkeypatch):
    guard = guard_for(monkeypatch, guard_url=None, prior=prior_with(URL))
    assert "duplicate_canonical_url_hash" in guard["blockers"]


def test_a_frozen_dispatch_is_a_definite_no_write():
    result = normalize_dispatch_result({"status": "PUBLIC_DISPATCH_FROZEN", "error_class": "public_dispatch_freeze_guard"},
                                       destination="telegram", surface="TELEGRAM_CHANNEL_POST", transport_type="BOT_API")
    assert result["status"] == DEFINITE_NO_WRITE
