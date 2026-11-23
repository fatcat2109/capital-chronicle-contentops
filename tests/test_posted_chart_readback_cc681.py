"""Compare exact public chart observations with fixtures only."""
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageDraw
import pytest

from live_contentops import neo_endpoint_executor_v1 as neo
from live_contentops import posted_chart_readback_v1 as charts
from live_contentops.publication_coordinator_v1 import (
    CanonicalDestinationTransportRuntimeV1, normalize_readback_result,
)


URLS = {
    "discord": "https://cdn.discordapp.com/attachments/a/b/chart.png",
    "facebook_page": "https://scontent-a.fbcdn.net/chart.jpg",
    "instagram_business": "https://scontent-a.cdninstagram.com/chart.jpg",
    "linkedin": "https://media.licdn.com/chart.jpg",
    "linkedin_company": "https://media.licdn.com/chart.jpg",
    "threads": "https://scontent-a.cdninstagram.com/chart.jpg",
    "telegram": "https://cdn4.telegram-cdn.org/file/chart.jpg",
    "x": "https://pbs.twimg.com/media/chart.jpg",
    "substack_notes": "https://substack-post-media.s3.amazonaws.com/public/images/chart.png",
    "substack": "https://substack-post-media.s3.amazonaws.com/public/images/chart.png",
    "youtube": "https://yt3.ggpht.com/chart.jpg",
}
OBJECT = "https://example.test/post/123"


@pytest.fixture
def bound_chart(tmp_path):
    image = Image.new("RGB", (480, 300), "white")
    draw = ImageDraw.Draw(image)
    for x in range(50, 400, 40):
        draw.line((x, 60 + x // 3, x, 100 + x // 3), width=4, fill="black")
    path = tmp_path / "gold.png"
    image.save(path)
    received = BytesIO()
    image.save(received, format="JPEG", quality=97)
    asset = {"asset_id": "gold-chart", "path": str(path), "sha256": sha256(path.read_bytes()).hexdigest(),
             "modality": "tradingview_chart_snapshot", "tradingview_snapshot": {"tv_symbol": "OANDA:XAUUSD"}}
    return asset, received.getvalue()


def wrong_image(size=(480, 300)):
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    for x in range(50, 400, 40):
        draw.line((x, 220 - x // 3, x, 260 - x // 3), width=4, fill="black")
    received = BytesIO()
    image.save(received, format="PNG")
    return received.getvalue()


def image_http(monkeypatch, content):
    class ImageResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def iter_content(self, size):
            yield content

    class HTTP:
        def get(self, url, *, timeout, stream, allow_redirects):
            assert url.startswith("https://") and stream and not allow_redirects
            return ImageResponse()

    monkeypatch.setattr(neo.requests, "Session", HTTP)


@pytest.mark.parametrize("destination", sorted(URLS))
def test_each_outlets_readback_reaches_the_existing_coordinator(monkeypatch, bound_chart, destination):
    asset, received = bound_chart
    image_http(monkeypatch, received)
    result = {"status": "SUCCESS", "verified": True, "public_object_id": "123", "public_object_url": OBJECT}
    urls = [URLS[destination]]
    runtime = CanonicalDestinationTransportRuntimeV1()
    if destination in charts.API_IMAGE_ROUTES | {"telegram"}:
        runtime._strict_publish_readbacks[(destination, "123")] = {"readback": {"observed_image_urls": urls}}
    else:
        monkeypatch.setattr(runtime._neo_transport, "readback", lambda **kwargs: {**result, "public_image_urls": urls})
    if destination == "telegram":
        monkeypatch.setattr(charts, "read_telegram_images",
                            lambda object_id, **kwargs: urls if object_id == "123" else None)
    intent = {"media_assets": [asset], "native_payload": {"media_asset_ids": [asset["asset_id"]]},
              "destination_plan": {"transport_type": "BROWSEROS_NEO_MCP"}}
    if destination == "substack":
        intent["plan_analysis_page"] = "fixture-page"
    raw = runtime.readback(destination=destination, public_object_id="123", public_object_url=OBJECT, intent=intent)
    stored = normalize_readback_result(raw, public_object_id="123", destination=destination)
    assert stored["verified"]
    check, = stored["posted_chart_readback"]["assets"]
    assert check["status"] == "MATCH"
    assert check["expected_sha256"] == asset["sha256"]
    assert check["observed_sha256"] == [sha256(received).hexdigest()]
    assert "chart.jpg" not in json.dumps(stored)


@pytest.mark.parametrize(("urls", "body", "status"), [
    (["https://media.licdn.com/chart.jpg"], "wrong", "MISMATCH"),
    (["https://media.licdn.com/chart.jpg"], "wrong-aspect", "MISMATCH"),
    ([], None, "MISSING"),
    (None, None, "UNVERIFIED"),
    (["https://media.licdn.com/chart.jpg"], "undecodable", "UNVERIFIED"),
])
def test_a_wrong_chart_missing_chart_and_access_gap_are_distinct(monkeypatch, bound_chart, urls, body, status):
    asset, _ = bound_chart
    size = (350, 480) if body == "wrong-aspect" else (480, 300)
    image_http(monkeypatch, wrong_image(size) if body and body.startswith("wrong") else b"no decoded pixels")
    intent = {"media_assets": [asset], "native_payload": {"media_asset_ids": [asset["asset_id"]]}}
    raw = {"public_object_id": "123", "public_object_url": OBJECT, "write_exists": True, "public_image_urls": urls}
    assert charts.observe("linkedin", intent, raw, object_id="123")["assets"][0]["status"] == status
    assert charts.observe("linkedin", intent, raw, object_id="124") is None


@pytest.mark.parametrize("attachment", [True, False])
def test_facebook_exact_reply_reads_its_attachment_without_persisting_the_cdn_url(
        monkeypatch, bound_chart, attachment):
    from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
    from live_contentops import facebook_page_adapter_v6 as facebook
    from live_contentops.plan_call_cards_v1 import readback_own_comment

    asset, received = bound_chart
    destination = "facebook_page"
    url = URLS[destination] + "?fixture=ephemeral"
    native = {"text": "Gold update", "own_call_comment": True, "reply_to_id": "outer_100",
              "media_asset_ids": [asset["asset_id"]]}
    intent = {"plan_status_post": "fixture", "native_payload": native, "media_assets": [asset]}
    monkeypatch.setattr(pipeline, "_durable_intent_inputs", lambda intent: {
        "output_dir": Path(asset["path"]).parent, "article": {}, "canonical_url": "",
        "local_media": asset["path"], "payloads": {destination: native},
    })
    monkeypatch.setattr(facebook, "_facebook_token", lambda: "fixture")

    def get_comments(endpoint, params):
        assert endpoint.endswith("/outer_100/comments")
        row = {"id": "comment_123", "message": "Gold update"}
        if attachment and "attachment" in params["fields"]:
            row["attachment"] = {"type": "photo", "media": {"image": {"src": url}}}
        return {"data": [{"id": "other", "message": "Gold update"}, row]}

    monkeypatch.setattr(facebook, "_get_json", get_comments)
    image_http(monkeypatch, received)
    runtime = CanonicalDestinationTransportRuntimeV1()
    raw = runtime.readback(destination=destination, public_object_id="comment_123", public_object_url=None, intent=intent)
    assert raw["verified"] and raw["write_exists"]
    assert raw["posted_chart_readback"]["assets"][0]["status"] == ("MATCH" if attachment else "MISSING")
    assert url not in json.dumps(raw)
    assert "observed_image_urls" not in readback_own_comment(destination, "comment_123", "outer_100", "Gold update")


@pytest.mark.skipif(not shutil.which("node"), reason="Node is required for the Neo DOM fixture")
def test_linkedin_author_avatar_does_not_count_as_the_posts_chart():
    script = """
const fs = require('node:fs');
const author = {href:'https://www.linkedin.com/in/jimcc', innerText:'Jim'};
const image = (src, anchor) => ({
  src, getAttribute:()=>null, getClientRects:()=>[{}],
  closest:selector=>selector==='a[href]' ? anchor : null,
});
const avatar = image('https://media.licdn.com/dms/image/profile-displayphoto-shrink_100/avatar.png', author);
const chart = image('https://media.licdn.com/dms/image/feedshare-shrink_800/chart.png', null);
const post = {
  getClientRects:()=>[{}], querySelector:()=>({innerText:'Gold update'}),
  querySelectorAll:selector=>selector==='a[href]' ? [author] : [avatar, ...(process.argv[2]==='chart' ? [chart] : [])],
};
global.document = {querySelectorAll:()=>[post]};
global.location = {href:'https://www.linkedin.com/feed/update/urn:li:activity:123/'};
const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
const run = new AsyncFunction('input','page',fs.readFileSync(process.argv[1],'utf8'));
const page = {evaluateInPage:async (callback,arg)=>({value:callback(arg)})};
run({phase:'article_readback',destination:'linkedin'}, page)
  .then(result=>process.stdout.write(JSON.stringify(result.posts[0].public_image_urls)))
  .catch(error=>{console.error(error);process.exitCode=1;});
"""

    def observed_images(content):
        result = subprocess.run(["node", "-e", script, str(neo.STEPS), content],
                                capture_output=True, text=True, check=True, timeout=10)
        return json.loads(result.stdout)

    assert observed_images("avatar") == []
    assert observed_images("chart") == ["https://media.licdn.com/dms/image/feedshare-shrink_800/chart.png"]


def test_carousel_reuse_only_compares_the_requested_slot(monkeypatch, bound_chart):
    asset, _ = bound_chart
    other_url = "https://scontent-a.cdninstagram.com/wrong.png"
    correct_url = URLS["instagram_business"]

    def measure(request, observed):
        return {"observed_media_sha256": [asset["sha256"]], "media_comparisons": [
            {"source_asset_sha256": asset["sha256"], "public_object_url": OBJECT,
             "public_image_url": url, "platform_sha256": digest, "pixels_inspected": True,
             "source_pixels_match": url == correct_url}
            for url, digest in [(correct_url, asset["sha256"]), (other_url, "b" * 64)]
        ]}

    monkeypatch.setattr(neo, "compare_public_images", measure)
    intent = {"media_assets": [asset], "native_payload": {"media_asset_ids": [asset["asset_id"]],
                                                         "reuse_run_carousel": True}}
    result = {"public_object_id": "123", "public_object_url": OBJECT,
              "observed_image_urls": [other_url, correct_url], "observed_image_slots": [other_url]}
    assert charts.observe("instagram_business", intent, result)["assets"][0]["status"] == "MISMATCH"


def test_telegram_uses_the_exact_public_channels_own_image_not_quoted_media(monkeypatch):
    image_url = URLS["telegram"]
    html = f"""<div data-post="CapitalChronicle/123">
      <div class="tgme_widget_message_bubble">
        <div class="tgme_widget_message_reply">
          <a class="tgme_widget_message_photo_wrap" style="background-image:url('https://other.test/chart')"></a>
        </div>
        <a class="tgme_widget_message_photo_wrap" style="background-image:url('{image_url}')"></a>
      </div>
    </div><div data-post="CapitalChronicle/124">
      <i class="link_preview_image" style="background-image:url('{image_url}')"></i>
    </div>"""

    class PublicResponse:
        status_code = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def iter_content(self, size):
            yield html.encode()

    def read(url, *, params, timeout, allow_redirects, stream):
        assert url == "https://t.me/s/CapitalChronicle" and params == {"after": 122}
        assert stream and not allow_redirects
        return PublicResponse()

    monkeypatch.setattr(charts.requests, "get", read)
    assert charts.read_telegram_images("123") == [image_url]
    assert charts._telegram_images(html, "124") == []
    assert charts._telegram_images(html, "124", include_link_preview=True) == [image_url]
    assert charts._telegram_images(html, "125") is None
