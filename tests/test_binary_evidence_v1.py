"""Prevent another large image-text diff without exposing fixture bytes."""
import subprocess
from pathlib import Path

from PIL import Image

from scripts.check_binary_evidence import check


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def test_binary_screenshot_and_metadata_allowed_base64_sidecars_and_embeds_rejected(tmp_path):
    git(tmp_path, "init", "-q")
    Image.new("RGB", (4, 4)).save(tmp_path / "capture.png")
    (tmp_path / "capture.json").write_text('{"path":"capture.png","sha256":"metadata-only"}')
    git(tmp_path, "add", "capture.png", "capture.json")
    assert check(tmp_path) == []
    (tmp_path / "capture.png.b64").write_text("forbidden sidecar")
    (tmp_path / "embedded.json").write_text('{"image":"data:image/' + 'png;base64,' + 'A' * 200 + '"}')
    git(tmp_path, "add", "capture.png.b64", "embedded.json")
    assert set(check(tmp_path)) == {
        ("capture.png.b64", "BASE64_IMAGE_SIDECAR_FORBIDDEN"),
        ("embedded.json", "EMBEDDED_BASE64_IMAGE_FORBIDDEN"),
    }


def test_image_extension_cannot_hide_base64_text(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "fake.png").write_text("iVBORw0KGgo" + "A" * 200)
    (tmp_path / "fake.webp").write_text("image text is not a binary WebP")
    git(tmp_path, "add", "fake.png", "fake.webp")
    assert set(check(tmp_path)) == {
        ("fake.png", "BINARY_IMAGE_MAGIC_REQUIRED"),
        ("fake.webp", "BINARY_IMAGE_MAGIC_REQUIRED"),
    }


def test_root_git_rules_hide_transient_captures_and_mark_images_binary():
    root = Path(__file__).resolve().parents[1]
    paths = ["docs/publisher/CC-172/captures/page.png", "tests/evidence/cc-172/captures/page.png",
        "docs/publisher/EVENT_ARTICLES_V1/test/substack-draft-review/view.png", "unused.png.b64"]
    assert len(git(root, "check-ignore", *paths).decode().splitlines()) == len(paths)
    attrs = git(root, "check-attr", "diff", "text", "--", "unused.png", "unused.jpg", "unused.webp").decode()
    assert attrs.count(": diff: unset") == 3 and attrs.count(": text: unset") == 3
