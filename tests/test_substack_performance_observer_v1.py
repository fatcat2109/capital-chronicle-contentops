from __future__ import annotations

from types import SimpleNamespace

from live_contentops import substack_performance_observer_v1 as observer


VISIBLE_STATS = """
Post stats
Total views
1,234
Free subscriptions 3
Paid subscriptions
2
Recipients 900
Open rate 48.5%
Delivery rate
99%
Likes 17
Comments
4
Shares 6
Restacks 2
"""


def test_native_metric_normalization_preserves_views_and_explicit_qualified_mappings():
    result = observer.parse_substack_post_stats_visible_text(VISIBLE_STATS)

    assert result["metrics"]["total_views"] == 1234
    assert result["metrics"]["open_rate"] == 0.485
    assert result["metrics"]["delivery_rate"] == 0.99
    assert result["metrics"]["subscriber_conversions"] == 5
    assert result["metrics"]["reposts"] == 2
    assert result["availability"]["shares"] == "AVAILABLE"
    assert "meaningful_reads" not in result["metrics"]
    assert result["availability"]["meaningful_reads"] == "NOT_EXPOSED"


def test_missing_native_metric_is_not_coerced_to_zero():
    result = observer.parse_substack_post_stats_visible_text("Total views\n41\nOpen rate\n20%")

    assert result["metrics"]["total_views"] == 41
    assert "shares" not in result["metrics"]
    assert result["availability"]["shares"] == "NOT_EXPOSED"
    assert "subscriber_conversions" not in result["metrics"]
    assert result["availability"]["subscriber_conversions"] == "NOT_EXPOSED"


class _FakeLocator:
    def __init__(self, *, text="", hrefs=None):
        self._text = text
        self._hrefs = hrefs or []

    def inner_text(self, **_kwargs):
        return self._text

    def evaluate_all(self, _script):
        return list(self._hrefs)


class _FakePage:
    def __init__(self, *, text, hrefs, final_url=None):
        self.url = "about:blank"
        self._text = text
        self._hrefs = hrefs
        self._final_url = final_url
        self.closed = False
        self.navigations = []

    def goto(self, url, **_kwargs):
        self.navigations.append(url)
        self.url = self._final_url or url

    def wait_for_timeout(self, _milliseconds):
        return None

    def locator(self, selector):
        if selector == "body":
            return _FakeLocator(text=self._text)
        return _FakeLocator(hrefs=self._hrefs)

    def close(self):
        self.closed = True


def test_exact_first_party_object_url_binding_collects_and_closes_task_tab(monkeypatch):
    public_url = "https://capitalchronicle.substack.com/p/exact-article"
    page = _FakePage(text=VISIBLE_STATS, hrefs=[public_url])
    context = SimpleNamespace(new_page=lambda: page)
    browser = SimpleNamespace(contexts=[context])
    chromium = SimpleNamespace(connect_over_cdp=lambda *_args, **_kwargs: browser)
    playwright = SimpleNamespace(chromium=chromium, stop=lambda: None)
    events = []
    monkeypatch.setattr(observer, "assert_canonical_edge_cdp", lambda _port: {})
    monkeypatch.setattr(observer, "_start_playwright", lambda: playwright)
    monkeypatch.setattr(
        observer,
        "record_browser_interaction_event",
        lambda event, **kwargs: events.append((event, kwargs)),
    )

    result = observer.collect_substack_post_metrics_via_edge(
        cdp_port=9223,
        public_object_id="210915784",
        canonical_public_url=public_url,
    )

    assert result["status"] == "COLLECTED"
    assert result["metrics"]["total_views"] == 1234
    assert result["browser_write_performed"] is False
    assert result["source_identity"].startswith(observer.SOURCE_IDENTITY + "#sha256:")
    assert page.navigations == [
        "https://capitalchronicle.substack.com/publish/posts/detail/210915784"
    ]
    assert page.closed is True
    assert [event for event, _detail in events] == ["tab_created", "navigation", "tab_closed"]


def test_exact_numeric_detail_route_is_equivalent_binding_when_permalink_anchor_is_absent(
    monkeypatch,
):
    page = _FakePage(text=VISIBLE_STATS, hrefs=[])
    context = SimpleNamespace(new_page=lambda: page)
    browser = SimpleNamespace(contexts=[context])
    playwright = SimpleNamespace(
        chromium=SimpleNamespace(connect_over_cdp=lambda *_args, **_kwargs: browser),
        stop=lambda: None,
    )
    monkeypatch.setattr(observer, "assert_canonical_edge_cdp", lambda _port: {})
    monkeypatch.setattr(observer, "_start_playwright", lambda: playwright)

    result = observer.collect_substack_post_metrics_via_edge(
        cdp_port=9223,
        public_object_id="210915784",
        canonical_public_url="https://capitalchronicle.substack.com/p/exact-article",
    )

    assert result["status"] == "COLLECTED"
    assert result["metrics"]["total_views"] == 1234
    assert page.closed is True


def test_redirect_that_loses_numeric_and_canonical_binding_fails_closed(monkeypatch):
    page = _FakePage(
        text=VISIBLE_STATS,
        hrefs=["https://capitalchronicle.substack.com/p/other"],
        final_url="https://capitalchronicle.substack.com/publish/posts/published",
    )
    context = SimpleNamespace(new_page=lambda: page)
    browser = SimpleNamespace(contexts=[context])
    playwright = SimpleNamespace(
        chromium=SimpleNamespace(connect_over_cdp=lambda *_args, **_kwargs: browser),
        stop=lambda: None,
    )
    monkeypatch.setattr(observer, "assert_canonical_edge_cdp", lambda _port: {})
    monkeypatch.setattr(observer, "_start_playwright", lambda: playwright)

    result = observer.collect_substack_post_metrics_via_edge(
        cdp_port=9223,
        public_object_id="210915784",
        canonical_public_url="https://capitalchronicle.substack.com/p/exact-article",
    )

    assert result["status"] == "IDENTITY_MISMATCH"
    assert result["metrics"] == {}
    assert set(result["availability"].values()) == {"UNAVAILABLE"}
    assert page.closed is True
