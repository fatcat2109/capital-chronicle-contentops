"""Ops Product, 23 Nov (with CC-683): a platform that resizes and re-encodes our chart still matches.

Telegram 229 served our 1600x900 chart as an 800x450 JPEG and the pixel rule called it a mismatch.
"""
from hashlib import sha256
from io import BytesIO
import random

from PIL import Image, ImageDraw
import pytest

from live_contentops import neo_endpoint_executor_v1 as neo


def chart(seed, label="3,722.0", level_y=300):
    """A TradingView-like 16:9 chart: grid, candles, a level line and price labels."""
    rng = random.Random(seed)
    image = Image.new("RGB", (1600, 900), (19, 23, 34))
    draw = ImageDraw.Draw(image)
    for x in range(0, 1600, 100):
        draw.line((x, 0, x, 900), fill=(42, 46, 57))
    for y in range(0, 900, 90):
        draw.line((0, y, 1600, y), fill=(42, 46, 57))
    price = 450
    for x in range(20, 1460, 18):
        step = rng.randint(-30, 30)
        top, bottom = sorted((price, price + step))
        color = (38, 166, 154) if step < 0 else (239, 83, 80)
        draw.line((x + 5, top - rng.randint(5, 25), x + 5, bottom + rng.randint(5, 25)), fill=color, width=2)
        draw.rectangle((x, top, x + 10, max(bottom, top + 2)), fill=color)
        price = min(800, max(100, price + step))
    draw.line((0, level_y, 1460, level_y), fill=(41, 98, 255), width=3)
    for i, y in enumerate(range(60, 900, 90)):
        draw.text((1475, y), f"{3800 - 20 * i:,}.0", fill=(209, 212, 220), font_size=22)
    draw.rectangle((1465, level_y - 12, 1600, level_y + 14), fill=(41, 98, 255))
    draw.text((1475, level_y - 10), label, fill="white", font_size=22)
    return image


def served(image):
    """What a platform serves: half size, its own resampling, JPEG."""
    buffer = BytesIO()
    image.resize((image.width // 2, image.height // 2), Image.Resampling.BICUBIC).save(buffer, "JPEG", quality=80)
    return buffer.getvalue()


def compare(tmp_path, source, public_bytes):
    path = tmp_path / "chart.png"
    source.save(path)
    request = {"destination": "telegram", "content_binding": {"media_manifest": [
        {"path": str(path), "sha256": sha256(path.read_bytes()).hexdigest()}]}}
    observed = {"public_object_url": "https://t.me/CapitalChronicle/229",
                "public_image_urls": ["https://cdn4.telegram-cdn.org/file/chart.jpg"]}

    class Http:
        def get(self, *args, **kwargs):
            class Response:
                status_code = 200
                def raise_for_status(self):
                    pass
                def iter_content(self, size):
                    yield public_bytes
            return Response()
    return neo.compare_public_images(request, observed, http=Http())["media_comparisons"][0]


def test_the_same_chart_served_at_half_size_as_jpeg_matches(tmp_path):
    result = compare(tmp_path, chart(1), served(chart(1)))
    assert result["source_pixels_match"] is True, result
    assert result["comparison_method"] == "RGB_RESIZED_HALF_BLUR15_TILE32_LUMA60_V1"


@pytest.mark.parametrize("public", ["other_chart", "moved_level"])
def test_a_different_chart_or_a_moved_level_still_fails(tmp_path, public):
    # A one-digit label change in a 22-pixel font is below what a half-size re-encoded copy
    # can resolve (Telegram's own re-encoding of 229 differs from ours by more); a moved
    # level line and its label are not.
    delivered = chart(2) if public == "other_chart" else chart(1, label="3,782.0", level_y=360)
    result = compare(tmp_path, chart(1), served(delivered))
    assert result["source_pixels_match"] is False, result
