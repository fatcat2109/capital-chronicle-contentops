"""The actual tool output boundary must keep image payloads out of stdout."""
import base64
import hashlib
import importlib
import io
import json
from pathlib import Path

from PIL import Image

from live_contentops.tool_output_v1 import MAX_OUTPUT_BYTES, safe_print


def test_binary_result_returns_exact_file_hash_and_dimensions(tmp_path, capsys):
    stream = io.BytesIO()
    Image.effect_noise((256, 256), 100).save(stream, format="PNG")
    data = stream.getvalue()
    assert len(data) > MAX_OUTPUT_BYTES
    safe_print(data, output_dir=tmp_path)
    observed = capsys.readouterr().out
    result = json.loads(observed)
    assert len(observed.encode()) < MAX_OUTPUT_BYTES
    assert Path(result["path"]).read_bytes() == data
    assert result["sha256"] == hashlib.sha256(data).hexdigest()
    assert (result["width"], result["height"]) == (256, 256)


def test_nested_json_base64_becomes_binary_reference_without_changing_status(tmp_path, capsys):
    data = b"image bytes" * 2000
    encoded = base64.b64encode(data).decode()
    safe_print(json.dumps({"status": "PENDING", "result": [{"image": ("data:image/" + "png;base64,") + encoded}]}), output_dir=tmp_path)
    text = capsys.readouterr().out
    result = json.loads(text)
    assert result["status"] == "PENDING"
    assert encoded not in text and "base64," not in text
    assert Path(result["result"][0]["image"]["path"]).read_bytes() == data
    assert not list(tmp_path.glob("*.txt"))


def test_large_native_request_survives_in_file_and_small_json_stays_compatible(tmp_path, capsys):
    request = {"classification": "NATIVE_DESKTOP_INPUT_REQUIRED", "prompt": "grounded source text " * 2000}
    safe_print(json.dumps(request), output_dir=tmp_path)
    result = json.loads(capsys.readouterr().out)
    assert result["classification"] == "TOOL_OUTPUT_IN_FILE"
    assert json.loads(Path(result["output"]["path"]).read_text()) == request
    original = '{"status": "OK", "count": 3}'
    safe_print(original, output_dir=tmp_path)
    assert capsys.readouterr().out == original + "\n"


def test_embedded_image_text_never_enters_saved_text_or_stdout(tmp_path, capsys):
    encoded = base64.b64encode(b"payload" * 3000).decode()
    safe_print(("screenshot data:image/" + "png;base64,") + encoded + " tail", output_dir=tmp_path)
    text = capsys.readouterr().out
    assert encoded not in text
    for path in tmp_path.iterdir():
        if path.suffix != ".bin":
            assert encoded.encode() not in path.read_bytes()


def test_live_cli_entrypoints_use_output_boundary():
    for name in ["scripts.run_native_desktop_editorial", "scripts.run_native_neo_executor", "live_contentops.cli"]:
        assert importlib.import_module(name).print is safe_print


def test_live_cli_consumer_emits_file_reference_for_large_image_result(tmp_path, monkeypatch, capsys):
    from live_contentops import cli
    import tempfile
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    data = b"retained image bytes" * 2000
    monkeypatch.setattr(cli.status, "get_status", lambda: {
        "status": "READY", "image": "data:image/" + "png;base64," + base64.b64encode(data).decode()})
    cli.print_status()
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "READY"
    assert Path(result["image"]["path"]).read_bytes() == data


def test_small_image_data_uri_is_also_kept_out_of_session(tmp_path, capsys):
    safe_print(json.dumps({"image": ("data:image/" + "png;base64,") + base64.b64encode(b"small image").decode()}), output_dir=tmp_path)
    text = capsys.readouterr().out
    assert "base64," not in text
    assert Path(json.loads(text)["image"]["path"]).read_bytes() == b"small image"
