from __future__ import annotations

from contextlib import contextmanager
import inspect
from pathlib import Path

from live_contentops import edge_cdp_publishing_adapter_v1 as adapter
from live_contentops.edge_cdp_publishing_adapter_v1 import (
    _activate_file_upload,
    _file_input_snapshot,
    _meaningful_image_dimensions,
    _newest_activated_media_input,
    _public_substack_content_checks,
    _split_substack_body,
    validate_youtube_community_payload,
)


def test_substack_update_mode_preserves_public_url_and_confirms_update() -> None:
    source = inspect.getsource(adapter.publish_substack_article_via_edge)
    transition_source = inspect.getsource(
        adapter._complete_substack_editor_publication_transition
    )
    assert "existing_public_url" in source
    assert "_complete_substack_editor_publication_transition" in source
    assert 'labels=("Update",)' in transition_source
    assert 'labels=("Update post", "Update now", "Confirm update")' in transition_source
    assert 'publication_write_mode": "update_existing_public_article"' in source


def test_public_substack_url_is_pinned_to_exact_tenant_without_authority_extras() -> None:
    assert adapter._is_public_substack_url(
        "https://capitalchronicle.substack.com/p/exact-story"
    )
    assert adapter._is_public_substack_url(
        "https://CAPITALCHRONICLE.SUBSTACK.COM/p/exact-story?utm_source=test"
    )
    for invalid in (
        "http://capitalchronicle.substack.com/p/exact-story",
        "https://other-publication.substack.com/p/exact-story",
        "https://capitalchronicle.substack.com.evil.example/p/exact-story",
        "https://capitalchronicle.substack.com@evil.example/p/exact-story",
        "https://user@capitalchronicle.substack.com/p/exact-story",
        "https://capitalchronicle.substack.com:443/p/exact-story",
        "https://capitalchronicle.substack.com/p/",
        "https://capitalchronicle.substack.com/publish/post/210796285",
    ):
        assert adapter._is_public_substack_url(invalid) is False


class _TransitionButton:
    def __init__(
        self,
        page,
        label: str,
        *,
        test_id: str | None = None,
        disabled: bool = False,
    ) -> None:
        self.page = page
        self.label = label
        self.test_id = test_id
        self.disabled = disabled

    def is_visible(self, timeout=None):
        del timeout
        return True

    def is_disabled(self, timeout=None):
        del timeout
        return self.disabled

    def inner_text(self, timeout=None):
        del timeout
        return self.label

    def get_attribute(self, name):
        if name == "data-testid":
            return self.test_id
        if name == "aria-label":
            return None
        return None

    def scroll_into_view_if_needed(self, timeout=None):
        del timeout

    def click(self, timeout=None, trial=False):
        del timeout
        if trial:
            if getattr(self.page, "raise_on_trial", None) == self.label:
                raise TimeoutError("simulated non-actionable control")
            return
        self.page.clicks.append(self.label)
        if self.page.raise_on_click == self.label:
            raise TimeoutError("simulated ambiguous click response")
        self.page.handle_click(self.label)


class _TransitionButtonList:
    def __init__(self, rows) -> None:
        self.rows = rows

    def count(self):
        return len(self.rows)

    def nth(self, index):
        return self.rows[index]


class _TransitionPage:
    def __init__(
        self,
        *,
        confirmation_after_polls: int | None,
        public_after_confirmation: bool = True,
        raise_on_click: str | None = None,
        raise_on_trial: str | None = None,
    ) -> None:
        self.mode = "editor"
        self.url = "https://capitalchronicle.substack.com/publish/post/210796285"
        self.confirmation_after_polls = confirmation_after_polls
        self.public_after_confirmation = public_after_confirmation
        self.raise_on_click = raise_on_click
        self.raise_on_trial = raise_on_trial
        self.confirmation_polls = 0
        self.public_url = None
        self.clicks: list[str] = []
        self.navigations: list[str] = []

    def _buttons(self):
        if self.mode == "editor":
            return [
                _TransitionButton(self, "Continue editing", test_id="decoy"),
                _TransitionButton(self, "Continue", test_id="publish-button"),
            ]
        if self.mode == "settings":
            return [
                _TransitionButton(self, "Publish settings"),
                _TransitionButton(self, "Send to everyone now"),
            ]
        if self.mode == "confirmation":
            self.confirmation_polls += 1
            if (
                self.confirmation_after_polls is not None
                and self.confirmation_polls >= self.confirmation_after_polls
            ):
                return [_TransitionButton(self, "Publish without buttons")]
        return []

    def locator(self, selector):
        assert selector == "button, [role='button']"
        return _TransitionButtonList(self._buttons())

    def handle_click(self, label):
        if label == "Continue":
            self.mode = "settings"
        elif label == "Send to everyone now":
            self.mode = "confirmation"
        elif label == "Publish without buttons":
            self.mode = "public"
            if self.public_after_confirmation:
                self.public_url = "https://capitalchronicle.substack.com/p/exact-story"

    def goto(self, url, **_kwargs):
        self.navigations.append(url)
        self.mode = "published_listing"


def test_substack_publish_transition_requires_exact_draft_id_before_any_click() -> None:
    page = _TransitionPage(confirmation_after_polls=None)

    result = adapter._complete_substack_publish_transition(
        page,
        draft_id=None,
        expected_title="Exact story",
        transition_timeout_seconds=0.01,
        listing_timeout_seconds=0.01,
        poll_interval_seconds=0.01,
    )

    assert result["status"] == (
        "BLOCKED_SUBSTACK_DRAFT_ID_NOT_BOUND_BEFORE_PUBLIC_WRITE"
    )
    assert result["definite_no_write"] is True
    assert result["public_write_attempted"] is False
    assert result["browser_write_performed"] is False
    assert page.clicks == []


def test_substack_publish_transition_requires_exact_editor_draft_identity_before_click() -> None:
    page = _TransitionPage(confirmation_after_polls=None)
    page.url = "https://capitalchronicle.substack.com/publish/post/999999999"

    result = adapter._complete_substack_publish_transition(
        page,
        draft_id="210796285",
        expected_title="Exact story",
        transition_timeout_seconds=0.01,
        listing_timeout_seconds=0.01,
        poll_interval_seconds=0.01,
    )

    assert result["status"] == (
        "BLOCKED_SUBSTACK_EDITOR_DRAFT_ID_MISMATCH_BEFORE_PUBLIC_WRITE"
    )
    assert result["definite_no_write"] is True
    assert result["public_write_attempted"] is False
    assert result["browser_write_performed"] is False
    assert page.clicks == []


def test_substack_publish_transition_waits_for_delayed_exact_confirmation_then_reconciles(
    monkeypatch,
) -> None:
    page = _TransitionPage(confirmation_after_polls=3)
    monkeypatch.setattr(adapter, "_extract_substack_public_url", lambda value: value.public_url)

    result = adapter._complete_substack_publish_transition(
        page,
        draft_id="210796285",
        expected_title="Exact story",
        transition_timeout_seconds=0.4,
        listing_timeout_seconds=0.01,
        poll_interval_seconds=0.01,
    )

    assert result["status"] == (
        "UNKNOWN_SUBSTACK_PUBLICATION_REQUIRES_DRAFT_ID_RECONCILIATION"
    )
    assert "public_url" not in result
    assert page.clicks == [
        "Continue",
        "Send to everyone now",
        "Publish without buttons",
    ]
    assert [row["outcome"] for row in result["transition_stages"]] == [
        "CLICKED_ONCE",
        "PUBLIC_WRITE_CLICKED_ONCE",
        "PUBLIC_WRITE_CLICKED_ONCE",
        "OBSERVED_UNBOUND_TO_EXACT_DRAFT_ID",
    ]


def test_substack_partial_exact_draft_reconciles_public_write_absent(monkeypatch):
    from contextlib import contextmanager
    from live_contentops import edge_cdp_publishing_adapter_v1 as adapter

    title = "U.S. Energy Information Administration Updates Short-Term Energy Outlook"
    subtitle = "An attributed update from accepted evidence."
    body = "The U.S. Energy Information Administration updated its Short-Term Energy Outlook with a new official release."

    class Input:
        def __init__(self, value):
            self.value = value

        def input_value(self, timeout=None):
            return self.value

    class Editor:
        def inner_text(self, timeout=None):
            return "Only a partial body fragment survived the interrupted editor construction."

    class Page:
        url = "https://capitalchronicle.substack.com/publish/post/210915784"

        def goto(self, _url, **_kwargs):
            return None

    page = Page()

    @contextmanager
    def edge_page(_port):
        yield page

    def first_visible(_page, selectors):
        if selectors[0] == "#post-title":
            return Input(title), selectors[0]
        if selectors[0].startswith("textarea"):
            return Input(subtitle), selectors[0]
        return Editor(), selectors[0]

    monkeypatch.setattr(adapter, "canonical_edge_page", edge_page)
    monkeypatch.setattr(adapter, "_first_visible", first_visible)
    monkeypatch.setattr(adapter, "_editor_image_count", lambda _page: 1)
    monkeypatch.setattr(
        adapter,
        "_substack_exact_enabled_button",
        lambda _page, *, labels, **_kwargs: (
            (object(), "Continue") if "Continue" in labels else (None, None)
        ),
    )

    result = adapter.reconcile_substack_publication_by_draft_id_via_edge(
        cdp_port=9223,
        draft_id="210915784",
        expected_title=title,
        expected_subtitle=subtitle,
        expected_body_markdown=body,
        expected_image_assets=[{"asset_id": "a"}, {"asset_id": "b"}, {"asset_id": "c"}],
    )

    assert result["status"] == "SUBSTACK_PARTIAL_DRAFT_CONFIRMED_NOT_PUBLIC"
    assert result["write_absent"] is True
    assert result["draft_binding_verified"] is True
    assert result["draft_media_incomplete"] is True
    assert result["exact_editor_route_verified"] is True
    assert result["body_anchor_verified"] is False
    assert result["observed_editor_image_count"] == 1
    assert result["expected_image_count"] == 3


def test_substack_published_detail_view_post_resolves_one_public_permalink(monkeypatch):
    from live_contentops import edge_cdp_publishing_adapter_v1 as adapter

    class PublicPage:
        url = "https://capitalchronicle.substack.com/p/exact-public-article"

        def close(self):
            return None

    class Context:
        def __init__(self):
            self.pages = []

    class Button:
        def __init__(self, context):
            self.context = context

        def click(self, timeout=None):
            self.context.pages.append(PublicPage())

    class DetailPage:
        url = "https://capitalchronicle.substack.com/publish/posts/detail/210915784"

        def __init__(self):
            self.context = Context()
            self.context.pages.append(self)

        def wait_for_timeout(self, _milliseconds):
            return None

    page = DetailPage()
    monkeypatch.setattr(
        adapter,
        "_substack_exact_enabled_button",
        lambda _page, *, labels, **_kwargs: (Button(page.context), "View post"),
    )

    assert adapter._public_substack_url_from_view_post(page) == (
        "https://capitalchronicle.substack.com/p/exact-public-article"
    )


def test_substack_publish_transition_without_public_state_stays_ambiguous(
    monkeypatch,
) -> None:
    page = _TransitionPage(confirmation_after_polls=None)
    monkeypatch.setattr(adapter, "_extract_substack_public_url", lambda _page: None)
    monkeypatch.setattr(adapter, "_substack_listing_matches", lambda *_args, **_kwargs: [])

    result = adapter._complete_substack_publish_transition(
        page,
        draft_id="210796285",
        expected_title="Exact story",
        transition_timeout_seconds=0.01,
        listing_timeout_seconds=0.01,
        poll_interval_seconds=0.01,
    )

    assert result["status"] == (
        "UNKNOWN_SUBSTACK_PUBLICATION_REQUIRES_DRAFT_ID_RECONCILIATION"
    )
    assert result["draft_id"] == "210796285"
    assert result["public_write_attempted"] is True
    assert result["browser_write_performed"] is True
    assert result["published_listing_match_count"] == 0
    assert page.clicks == ["Continue", "Send to everyone now"]
    assert page.clicks.count("Send to everyone now") == 1


def test_substack_pre_public_control_failure_is_definite_no_write(
    monkeypatch,
) -> None:
    page = _TransitionPage(confirmation_after_polls=None)
    monkeypatch.setattr(
        adapter,
        "_wait_for_substack_exact_button",
        lambda *_args, **_kwargs: (None, None),
    )

    result = adapter._complete_substack_publish_transition(
        page,
        draft_id="210796285",
        expected_title="Exact story",
        transition_timeout_seconds=0.01,
        listing_timeout_seconds=0.01,
        poll_interval_seconds=0.01,
    )

    assert result["status"] == "BLOCKED_SUBSTACK_CONTINUE_CONTROL_NOT_FOUND"
    assert result["definite_no_write"] is True
    assert result["public_write_attempted"] is False
    assert page.clicks == []


def test_substack_publish_transition_click_timeout_is_unknown_write(
    monkeypatch,
) -> None:
    page = _TransitionPage(
        confirmation_after_polls=None,
        raise_on_click="Send to everyone now",
    )
    monkeypatch.setattr(adapter, "_extract_substack_public_url", lambda _page: None)

    result = adapter._complete_substack_publish_transition(
        page,
        draft_id="210796285",
        expected_title="Exact story",
        transition_timeout_seconds=0.01,
        listing_timeout_seconds=0.01,
        poll_interval_seconds=0.01,
    )

    assert result["status"] == "UNKNOWN_SUBSTACK_PUBLISH_CONTROL_CLICK_FAILED"
    assert result["public_write_attempted"] is True
    assert result["browser_write_performed"] is True
    assert result["transition_stages"][-1]["error_class"] == "TimeoutError"
    assert page.clicks == ["Continue", "Send to everyone now"]
    assert page.navigations == []


def test_substack_publish_transition_non_actionable_final_control_is_definite_no_write(
    monkeypatch,
) -> None:
    page = _TransitionPage(
        confirmation_after_polls=None,
        raise_on_trial="Send to everyone now",
    )
    page.url = "https://capitalchronicle.substack.com/publish/post/210865567"
    monkeypatch.setattr(adapter, "_extract_substack_public_url", lambda _page: None)

    result = adapter._complete_substack_publish_transition(
        page,
        draft_id="210865567",
        expected_title="Exact story",
        transition_timeout_seconds=0.01,
        listing_timeout_seconds=0.01,
        poll_interval_seconds=0.01,
    )

    assert result["status"] == "BLOCKED_SUBSTACK_PUBLISH_CONTROL_NOT_ACTIONABLE"
    assert result["definite_no_write"] is True
    assert result["public_write_attempted"] is False
    assert result["browser_write_performed"] is False
    assert result["transition_stages"][-1]["outcome"] == "CONTROL_NOT_ACTIONABLE"
    assert page.clicks == ["Continue"]
    assert page.navigations == []


def test_substack_publish_transition_never_accepts_listing_only_public_match(
    monkeypatch,
) -> None:
    page = _TransitionPage(confirmation_after_polls=None)
    monkeypatch.setattr(adapter, "_extract_substack_public_url", lambda _page: None)
    monkeypatch.setattr(
        adapter,
        "_substack_listing_matches",
        lambda *_args, **_kwargs: [
            {
                "href": "/p/exact-story",
                "title": "Exact story",
            }
        ],
    )

    result = adapter._complete_substack_publish_transition(
        page,
        draft_id="210796285",
        expected_title="Exact story",
        transition_timeout_seconds=0.01,
        listing_timeout_seconds=0.01,
        poll_interval_seconds=0.01,
    )

    assert result["status"] == (
        "UNKNOWN_SUBSTACK_PUBLICATION_REQUIRES_DRAFT_ID_RECONCILIATION"
    )
    assert "public_url" not in result
    assert "public_url_source" not in result
    assert result["published_listing_match_count"] == 1
    assert result["transition_stages"][-1]["outcome"] == (
        "UNBOUND_UNIQUE_PUBLIC_MATCH"
    )
    assert page.navigations == [
        "https://capitalchronicle.substack.com/publish/posts/published"
    ]


def test_substack_publish_transition_rejects_multiple_exact_published_matches(
    monkeypatch,
) -> None:
    page = _TransitionPage(confirmation_after_polls=None)
    monkeypatch.setattr(adapter, "_extract_substack_public_url", lambda _page: None)
    monkeypatch.setattr(
        adapter,
        "_substack_listing_matches",
        lambda *_args, **_kwargs: [
            {"href": "/p/exact-story-a", "title": "Exact story"},
            {"href": "/p/exact-story-b", "title": "Exact story"},
        ],
    )

    result = adapter._complete_substack_publish_transition(
        page,
        draft_id="210796285",
        expected_title="Exact story",
        transition_timeout_seconds=0.01,
        listing_timeout_seconds=0.01,
        poll_interval_seconds=0.01,
    )

    assert result["status"] == (
        "UNKNOWN_SUBSTACK_PUBLICATION_REQUIRES_DRAFT_ID_RECONCILIATION"
    )
    assert result["published_listing_match_count"] == 2
    assert "public_url" not in result
    assert page.clicks == ["Continue", "Send to everyone now"]


def test_substack_listing_match_is_exact_and_deduplicates_query_variants(
    monkeypatch,
) -> None:
    class Link:
        def __init__(self, href, text) -> None:
            self.href = href
            self.text = text

        def get_attribute(self, name):
            assert name == "href"
            return self.href

        def inner_text(self, timeout=None):
            del timeout
            return self.text

    class Links:
        def all(self):
            return [
                Link("/p/exact-story?utm_source=one", "Exact story"),
                Link("/p/exact-story?utm_source=two", "Exact story"),
                Link("/p/near-story", "Exact storytelling"),
            ]

    class Page:
        def locator(self, selector):
            assert selector == "a[href]"
            return Links()

    monkeypatch.setattr(adapter, "_first_visible", lambda *_args, **_kwargs: (None, None))
    matches = adapter._substack_listing_matches(
        Page(),
        expected_title="Exact story",
        href_predicate=lambda href: adapter._is_public_substack_url(
            adapter._absolute_substack_url(href)
        ),
    )

    assert matches == [
        {"href": "/p/exact-story?utm_source=one", "title": "Exact story"}
    ]


def test_substack_listing_title_preserves_punctuation_while_collapsing_whitespace(
    monkeypatch,
) -> None:
    class Link:
        def __init__(self, href, text) -> None:
            self.href = href
            self.text = text

        def get_attribute(self, name):
            assert name == "href"
            return self.href

        def inner_text(self, timeout=None):
            del timeout
            return self.text

    class Links:
        def all(self):
            return [
                Link("/p/exact", "Markets: Oil's   Reset"),
                Link("/p/colon-changed", "Markets - Oil's Reset"),
                Link("/p/apostrophe-missing", "Markets: Oils Reset"),
                Link("/p/case-changed", "Markets: oil's Reset"),
            ]

    class Page:
        def locator(self, selector):
            assert selector == "a[href]"
            return Links()

    monkeypatch.setattr(adapter, "_first_visible", lambda *_args, **_kwargs: (None, None))
    matches = adapter._substack_listing_matches(
        Page(),
        expected_title="Markets: Oil's Reset",
        href_predicate=lambda href: adapter._is_public_substack_url(
            adapter._absolute_substack_url(href)
        ),
    )

    assert matches == [{"href": "/p/exact", "title": "Markets: Oil's Reset"}]


def test_substack_update_click_timeout_is_unknown_and_never_falls_into_create(
    monkeypatch,
) -> None:
    page = _TransitionPage(
        confirmation_after_polls=None,
        raise_on_click="Update",
    )
    update_button = _TransitionButton(page, "Update")
    create_calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        adapter,
        "_substack_exact_enabled_button",
        lambda *_args, **_kwargs: (update_button, "Update"),
    )
    monkeypatch.setattr(
        adapter,
        "_complete_substack_publish_transition",
        lambda *_args, **kwargs: create_calls.append(dict(kwargs)) or {"status": "SUCCESS"},
    )

    result = adapter._complete_substack_editor_publication_transition(
        page,
        draft_id="210796285",
        expected_title="Exact story",
        transition_timeout_seconds=0.01,
        listing_timeout_seconds=0.01,
        poll_interval_seconds=0.01,
    )

    assert result["status"] == "UNKNOWN_SUBSTACK_UPDATE_CONTROL_CLICK_FAILED"
    assert result["publication_write_mode"] == "update_existing_public_article"
    assert result["public_write_attempted"] is True
    assert result["browser_write_performed"] is True
    assert result["transition_stages"][-1]["error_class"] == "TimeoutError"
    assert page.clicks == ["Update"]
    assert create_calls == []


def test_targeted_substack_editorial_repair_is_exact_and_preserves_three_images() -> None:
    source = inspect.getsource(adapter.repair_substack_editorial_paragraphs_via_edge)
    assert 'visible == row["old"]' in source
    assert "len(row_matches) != 1" in source
    assert "len(images_before) == 3" in source
    assert "images_after == images_before" in source
    assert "page.keyboard.insert_text" in source
    assert "Control+A" not in source


def test_public_substack_content_checks_gate_identity_body_and_hard_process_safety() -> None:
    source_url = "https://www.eia.gov/pressroom/releases/press590.php"
    body = f"""## Supply Reset

EIA raised its global oil forecast as Hormuz traffic resumed, changing the inventory and inflation test for markets.

[[VISUAL:primary]]

WTI current market signal. [Source]({source_url})
"""
    visible = (
        "EIA Sees Oil Supply Nearing Pre-War Levels\n"
        "The supply path is changing.\n"
        "Supply Reset\nEIA raised its global oil forecast as Hormuz traffic resumed, changing the inventory and inflation test for markets.\n"
        "WTI current market signal. Source"
    )
    checks = _public_substack_content_checks(
        visible_text=visible,
        hrefs=[source_url],
        meta_description="EIA oil supply analysis with market and inflation context.",
        expected_title="EIA Sees Oil Supply Nearing Pre-War Levels",
        expected_subtitle="The supply path is changing.",
        expected_body_markdown=body,
        expected_image_assets=[{"caption": "WTI current market signal."}],
    )
    assert checks["content_readback_verified"] is True

    failed = _public_substack_content_checks(
        visible_text=visible + " The newsroom standard determines publication.",
        hrefs=[source_url],
        meta_description="EIA oil supply analysis with market and inflation context.",
        expected_title="EIA Sees Oil Supply Nearing Pre-War Levels",
        expected_subtitle="The supply path is changing.",
        expected_body_markdown=body,
        expected_image_assets=[{"caption": "WTI current market signal."}],
    )
    assert failed["content_readback_verified"] is False
    assert failed["editorial_process_language_absent"] is False

    for internal_phrase in ("packet timestamp", "evidence packet", "public claim permission", "manifest-bound"):
        failed = _public_substack_content_checks(
            visible_text=visible + f" Internal phrase: {internal_phrase}.",
            hrefs=[source_url],
            meta_description="EIA oil supply analysis with market and inflation context.",
            expected_title="EIA Sees Oil Supply Nearing Pre-War Levels",
            expected_subtitle="The supply path is changing.",
            expected_body_markdown=body,
            expected_image_assets=[{"caption": "WTI current market signal."}],
        )
        assert failed["content_readback_verified"] is False
        assert failed["editorial_process_language_absent"] is False


def test_public_substack_content_checks_allow_a_source_backed_article_without_visuals() -> None:
    source_url = "https://www.ft.com/content/example-banking-update"
    body = (
        "Deutsche became a European clearing bank for renminbi transactions, "
        "according to the Financial Times.\n\n"
        f"Read the original report. [Source]({source_url})"
    )
    visible = (
        "Deutsche becomes European clearing bank for RMB\n"
        "A source-backed banking update.\n"
        "Deutsche became a European clearing bank for renminbi transactions, "
        "according to the Financial Times.\n"
        "Read the original report. Source"
    )

    checks = _public_substack_content_checks(
        visible_text=visible,
        hrefs=[source_url],
        meta_description="A source-backed update on European RMB clearing.",
        expected_title="Deutsche becomes European clearing bank for RMB",
        expected_subtitle="A source-backed banking update.",
        expected_body_markdown=body,
        expected_image_assets=[],
    )

    assert checks["caption_count_expected"] == 0
    assert checks["captions_visible"] is True
    assert checks["content_readback_verified"] is True

    soft_mismatches = _public_substack_content_checks(
        visible_text=visible,
        hrefs=[],
        meta_description="",
        expected_title="Deutsche becomes European clearing bank for RMB",
        expected_subtitle="A different optional subtitle.",
        expected_body_markdown=body,
        expected_image_assets=[{"caption": "A different optional caption."}],
    )
    assert soft_mismatches["subtitle_visible"] is False
    assert soft_mismatches["captions_visible"] is False
    assert soft_mismatches["source_links_visible"] is False
    assert soft_mismatches["public_meta_description_present"] is False
    assert soft_mismatches["content_readback_verified"] is True


def test_substack_resume_index_preserves_exact_sequential_visual_prefix() -> None:
    from live_contentops.edge_cdp_publishing_adapter_v1 import (
        _segment_index_after_visual_prefix,
        _split_substack_body,
    )

    segments = _split_substack_body(
        "Intro\n\n[[VISUAL:first]]\n\n[[VISUAL:second]]\n\n[[VISUAL:third]]"
    )

    assert _segment_index_after_visual_prefix(segments, 0) == 0
    assert segments[_segment_index_after_visual_prefix(segments, 1)][0] == "text"
    assert segments[_segment_index_after_visual_prefix(segments, 1) + 1] == (
        "visual",
        "second",
    )
    assert _segment_index_after_visual_prefix(segments, 3) == len(segments)


def test_substack_draft_reconciliation_waits_for_exact_hydrated_binding(monkeypatch) -> None:
    expected_title = "Deutsche becomes European clearing bank for RMB"
    expected_subtitle = "A source-backed banking update."
    expected_body = (
        "## What happened\n\n"
        "Financial Times reported that Deutsche became a European clearing bank "
        "for renminbi transactions."
    )
    state = {"mode": "", "poll": 0, "navigations": [], "listing_calls": 0}

    class FakeLink:
        def get_attribute(self, name):
            assert name == "href"
            return "/publish/post/210796285?back=%2Fpublish%2Fposts%2Fdrafts"

        def inner_text(self, timeout=None):
            return expected_title

    class FakeLinks:
        def all(self):
            return [FakeLink()] if state["mode"] == "drafts" else []

    class FakePage:
        url = ""

        def goto(self, url, **_kwargs):
            state["navigations"].append(url)
            self.url = url
            state["mode"] = (
                "published"
                if url.endswith("/published")
                else "drafts"
                if url.endswith("/drafts")
                else "editor"
            )

        def locator(self, selector):
            assert selector == "a[href]"
            return FakeLinks()

    class FakeTitle:
        def input_value(self, timeout=None):
            state["poll"] += 1
            return "" if state["poll"] == 1 else expected_title

    class FakeSubtitle:
        def input_value(self, timeout=None):
            return "" if state["poll"] == 1 else expected_subtitle

    class FakeEditor:
        def inner_text(self, timeout=None):
            return "" if state["poll"] == 1 else expected_body

    page = FakePage()

    @contextmanager
    def fake_edge_page(_cdp_port):
        yield page

    def fake_first_visible(_page, selectors):
        if state["mode"] != "editor":
            return None, None
        first = selectors[0]
        if first == "#post-title":
            return FakeTitle(), first
        if first.startswith("textarea"):
            return FakeSubtitle(), first
        return FakeEditor(), first

    monkeypatch.setattr(adapter, "canonical_edge_page", fake_edge_page)
    monkeypatch.setattr(adapter, "_first_visible", fake_first_visible)
    monkeypatch.setattr(
        adapter,
        "_substack_exact_enabled_button",
        lambda _page, *, labels, **_kwargs: (
            (object(), "Continue") if "Continue" in labels else (None, None)
        ),
    )
    def older_identical_public_listing(*_args, **_kwargs):
        state["listing_calls"] += 1
        return [{"href": "/p/older-identical-story", "title": expected_title}]

    monkeypatch.setattr(adapter, "_substack_listing_matches", older_identical_public_listing)
    monkeypatch.setattr(adapter.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        adapter, "_editor_image_count", lambda _page: 0 if state["poll"] == 1 else 3
    )

    result = adapter.reconcile_substack_publication_by_draft_id_via_edge(
        cdp_port=9223,
        draft_id="210796285",
        expected_title=expected_title,
        expected_subtitle=expected_subtitle,
        expected_body_markdown=expected_body,
        expected_image_assets=[
            {"asset_id": "source"},
            {"asset_id": "facts"},
            {"asset_id": "metadata"},
        ],
    )

    assert result["status"] == "SUBSTACK_DRAFT_CONFIRMED_NOT_PUBLIC"
    assert result["draft_binding_verified"] is True
    assert result["write_absent"] is True
    assert result["browser_write_performed"] is False
    assert state["poll"] == 2
    assert not any(url.endswith("/published") for url in state["navigations"])
    assert not any(url.endswith("/drafts") for url in state["navigations"])
    assert any("/publish/post/210796285?" in url for url in state["navigations"])
    assert state["listing_calls"] == 0
    assert "public_url" not in result


class _FakeInput:
    def __init__(self, accept: str, *, disabled: bool = False) -> None:
        self.accept = accept
        self.disabled = disabled
        self.connected = True
        self.files: list[str] = []

    def get_attribute(self, name: str):
        return self.accept if name == "accept" else None

    def is_disabled(self, timeout: int = 0) -> bool:
        del timeout
        return self.disabled

    def evaluate(self, script: str):
        del script
        return self.connected

    def set_input_files(self, value, timeout: int = 0) -> None:
        del timeout
        self.files = list(value) if isinstance(value, list) else [str(value)]


class _FakeInputCollection:
    def __init__(self, page: "_FakePage") -> None:
        self.page = page

    def all(self):
        return list(self.page.inputs)


class _FakeChooser:
    def __init__(self) -> None:
        self.files: list[str] = []

    def set_files(self, value) -> None:
        self.files = list(value) if isinstance(value, list) else [str(value)]


class _ChooserContext:
    def __init__(self, chooser: _FakeChooser | None, *, missed: bool) -> None:
        self._chooser = chooser
        self.missed = missed

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        del exc_type, exc, traceback
        if self.missed:
            raise TimeoutError("file chooser event missed")

    @property
    def value(self):
        return self._chooser


class _FakeTrigger:
    def __init__(self, callback=None) -> None:
        self.callback = callback
        self.clicked = False

    def click(self, timeout: int = 0) -> None:
        del timeout
        self.clicked = True
        if self.callback:
            self.callback()


class _FakePage:
    def __init__(self, *, inputs=None, chooser: _FakeChooser | None = None, chooser_missed: bool = False) -> None:
        self.inputs = list(inputs or [])
        self.chooser = chooser
        self.chooser_missed = chooser_missed

    def locator(self, selector: str):
        assert selector == "input[type='file']"
        return _FakeInputCollection(self)

    def expect_file_chooser(self, timeout: int = 0):
        assert timeout > 0
        return _ChooserContext(self.chooser, missed=self.chooser_missed)


def test_filechooser_interception_sets_file_without_native_dialog(tmp_path: Path):
    media = tmp_path / "chart.png"
    media.write_bytes(b"png")
    chooser = _FakeChooser()
    page = _FakePage(chooser=chooser)
    trigger = _FakeTrigger()

    result = _activate_file_upload(
        page,
        trigger=trigger,
        file_path=media,
        media_kind="image",
        exclusive=True,
    )

    assert result["status"] == "file_set"
    assert result["upload_transport"] == "playwright_file_chooser"
    assert result["native_dialog_automation_used"] is False
    assert trigger.clicked is True
    assert chooser.files == [str(media.resolve())]


def test_missed_chooser_uses_newest_new_image_input_once(tmp_path: Path):
    media = tmp_path / "chart.png"
    media.write_bytes(b"png")
    stale = _FakeInput("image/*")
    newest = _FakeInput("image/*,.heic,.heif")
    page = _FakePage(inputs=[stale], chooser_missed=True)
    trigger = _FakeTrigger(lambda: page.inputs.append(newest))

    result = _activate_file_upload(
        page,
        trigger=trigger,
        file_path=media,
        media_kind="image",
        exclusive=True,
    )

    assert result["status"] == "file_set"
    assert result["upload_transport"] == "newest_activated_file_input"
    assert result["input_index"] == 1
    assert stale.files == []
    assert newest.files == [str(media.resolve())]


def test_stale_hidden_input_is_rejected_when_no_input_was_activated():
    page = _FakePage(inputs=[_FakeInput("image/*")])
    before = _file_input_snapshot(page)

    locator, meta = _newest_activated_media_input(
        page,
        before=before,
        media_kind="image",
        exclusive=True,
        timeout_seconds=0.01,
    )

    assert locator is None
    assert meta["activation"] == "no_new_or_newly_enabled_matching_input"


def test_public_image_threshold_excludes_avatar_and_accepts_chart():
    assert not _meaningful_image_dimensions(
        rendered_width=36,
        rendered_height=36,
        natural_width=2500,
        natural_height=2500,
    )
    assert _meaningful_image_dimensions(
        rendered_width=728,
        rendered_height=391,
        natural_width=1681,
        natural_height=902,
    )


def test_visual_markers_define_sequential_three_image_insertion_order():
    body = (
        "Opening\n\n[[VISUAL:primary]]\n\n"
        "Policy\n\n[[VISUAL:policy_corridor]]\n\n"
        "Curve\n\n[[VISUAL:sofr_context]]\n\nClose"
    )
    visual_ids = [value for kind, value in _split_substack_body(body) if kind == "visual"]

    assert visual_ids == ["primary", "policy_corridor", "sofr_context"]


def test_youtube_community_payload_requires_text_image_and_canonical_url(tmp_path: Path):
    image = tmp_path / "chart.png"
    image.write_bytes(b"chart")
    canonical_url = "https://capitalchronicle.substack.com/p/example"

    valid = validate_youtube_community_payload(
        text=f"Policy transmission remains in focus. {canonical_url}",
        image_path=image,
        canonical_url=canonical_url,
    )
    missing = validate_youtube_community_payload(
        text="",
        image_path=tmp_path / "missing.png",
        canonical_url=canonical_url,
    )

    assert valid["status"] == "VALID"
    assert missing["status"] == "INVALID"
    assert set(missing["blockers"]) == {
        "non_empty_text_required",
        "canonical_substack_url_required",
        "source_backed_image_required",
    }


def test_youtube_community_payload_rejects_technical_run_identifiers(tmp_path: Path):
    image = tmp_path / "chart.png"
    image.write_bytes(b"chart")
    canonical_url = "https://capitalchronicle.substack.com/p/example"

    invalid = validate_youtube_community_payload(
        text=f"eight_platform_live_20260710_recovery1 {canonical_url}",
        image_path=image,
        canonical_url=canonical_url,
    )

    assert invalid["status"] == "INVALID"
    assert "technical_run_identifier_forbidden" in invalid["blockers"]


def test_threads_edge_delete_rejects_non_allowlisted_target():
    result = adapter.delete_threads_post_via_edge_exact(
        cdp_port=9222,
        public_url="https://www.threads.com/@official.capitalchronicle/post/example",
        post_id="unrelated",
        expected_text="text",
        allowed_post_ids={"approved"},
    )
    assert result["status"] == "BLOCKED_THREADS_EDGE_DELETE_TARGET_MISMATCH"
