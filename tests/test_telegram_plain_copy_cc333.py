"""The next authored Telegram copy reaches the Bot API as plain text."""
import json

import pytest

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
from live_contentops import telegram_live_adapter_v6 as adapter
from live_contentops.article_scenarios_v1 import validate_social_scenarios
from live_contentops.v1_simple_gemini_newsroom_v1 import _native_preview_bundle
from test_article_publication_quality_cc333 import scenario_article
from test_telegram_live_adapter_v6 import _telegram_approval_context


def test_authored_bitcoin_emphasis_is_plain_in_frozen_telegram_package():
    article, _ = scenario_article()
    article.update(title="**Bitcoin.** A conditional rates review",
                   social_hook="**Bitcoin.** Confirmation still matters.")
    bundle, _ = _native_preview_bundle(article=article, article_mode="STANDARD_NEWS_ANALYSIS",
        article_identity="c" * 64, media_asset_ids=["controlled-image"])
    payload = bundle["packages"]["telegram"]
    assert "Bitcoin." in payload["text"] and "**" not in payload["text"]
    validate_social_scenarios(article, payload)
    assert "**Bitcoin.**" in article["title"]  # The authored canonical stays intact.


def test_telegram_plain_copy_retains_urls_figures_and_uncertainty():
    text = "## **Bitcoin.**\n_If_ rates fall, `60%` remains a model estimate; **not confirmed**.\n" \
           "[Read the review](https://capitalchronicle.substack.com/p/test_case)"
    plain = pipeline._telegram_plain_text(text)
    assert plain == "Bitcoin.\nIf rates fall, 60% remains a model estimate; not confirmed.\n" \
                    "Read the review (https://capitalchronicle.substack.com/p/test_case)"


@pytest.mark.parametrize("kind", ["text", "local_photo", "remote_photo"])
def test_plain_bot_api_omits_parse_mode_and_keeps_literal_comparisons(tmp_path, monkeypatch, kind):
    sent = []
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return b'{"ok":true,"result":{"message_id":999}}'
    def send(request, **kwargs):
        sent.append(request)
        return Response()
    monkeypatch.setattr(adapter.urllib.request, "urlopen", send)
    monkeypatch.setattr("live_contentops.live_telemetry_v6.classify_and_record_dispatch", lambda **kw: None)
    monkeypatch.chdir(tmp_path)
    text = "Bitcoin: if rates < 4% & growth holds, the scenario remains a model estimate, not confirmed."
    image = tmp_path / "own-image.png"
    image.write_bytes(b"controlled-local-upload")
    photo = str(image) if kind == "local_photo" else "https://example.org/own-image.png"
    context = _telegram_approval_context(run_id="v6_pipeline_test_cc333", topic="Plain Telegram copy",
        action="post" if kind == "text" else "photo", body_text=text,
        media_url=None if kind == "text" else photo)
    kwargs = dict(bot_token="unit-token", chat_id="unit-channel", parse_mode=None, approval_context=context)
    result = (adapter.execute_telegram_post(message=text, **kwargs) if kind == "text" else
              adapter.execute_telegram_photo(photo_url=photo, caption=text, **kwargs))
    assert result["status"] == "SUCCESS" and len(sent) == 1
    data = sent[0].data
    assert b'parse_mode' not in data and text.encode() in data
    if kind != "local_photo":
        payload = json.loads(data)
        assert payload["text" if kind == "text" else "caption"] == text


@pytest.mark.parametrize("photo", [False, True])
def test_canonical_telegram_transport_selects_plain_api_mode(tmp_path, monkeypatch, photo):
    observed = []
    def send(**kwargs):
        observed.append(kwargs)
        return {"status": "CONTROLLED_NO_WRITE"}
    monkeypatch.setattr(adapter, "execute_telegram_photo" if photo else "execute_telegram_post", send)
    monkeypatch.setattr(pipeline, "load_public_dispatch_hashes", lambda *a: {})
    kwargs = dict(run_id="controlled", topic_hash="a" * 64, text="Bitcoin: a conditional market review.",
                  canonical_url="https://capitalchronicle.substack.com/p/unit-review")
    if photo:
        pipeline._publish_telegram_photo_verified(**kwargs, image_path=str(tmp_path / "own.png"))
    else:
        pipeline._publish_telegram_text_verified(**kwargs)
    assert observed[0]["parse_mode"] is None
