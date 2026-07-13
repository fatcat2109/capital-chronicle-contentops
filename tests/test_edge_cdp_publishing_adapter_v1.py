from __future__ import annotations

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
    assert "existing_public_url" in source
    assert "button:has-text('Update post')" in source
    assert 'publication_write_mode": "update_existing_public_article"' in source


def test_public_substack_content_checks_require_reader_text_sources_and_captions() -> None:
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
