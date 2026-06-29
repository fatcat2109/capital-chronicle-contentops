import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from live_contentops.canonical_article_intake_v6 import (
    BLOCKED_STATUS,
    FAILED_STATUS,
    REVIEW_STATUS,
    intake_markdown_review_candidates,
    main,
    parse_markdown_review_candidate,
)


VALID_BODY = """# Required H1 Title

First paragraph becomes fallback description when metadata omits it.

## Evidence Notes
Operator-provided local draft text only.
"""


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _valid_markdown(extra_meta: str = "", body: str = VALID_BODY) -> str:
    return f"---\nsubtitle: Frontmatter Subtitle\ndescription: Frontmatter Description\n{extra_meta}---\n{body}"


def test_valid_markdown_fixture_creates_review_candidate_packet(tmp_path):
    draft = _write(tmp_path / "draft.md", _valid_markdown())

    candidate = parse_markdown_review_candidate(draft)

    assert candidate.candidate_status == REVIEW_STATUS
    assert candidate.canonical_article_review_candidate_available is True
    assert candidate.title == "Required H1 Title"
    assert candidate.subtitle == "Frontmatter Subtitle"
    assert candidate.description == "Frontmatter Description"
    assert candidate.source_file_path.endswith("draft.md")
    assert candidate.source_file_sha256 is not None


def test_required_status_flags_remain_review_only_and_dispatch_blocked(tmp_path):
    candidate = parse_markdown_review_candidate(_write(tmp_path / "draft.md", _valid_markdown()))

    assert candidate.approved_canonical_article_available is False
    assert candidate.human_review_required is True
    assert candidate.publication_ready is False
    assert candidate.dispatch_allowed is False
    assert candidate.platform_variant_generation_allowed is False
    assert candidate.outbox_creation_allowed is False
    assert candidate.public_url is None
    assert candidate.public_metrics is None
    assert candidate.review_only is True
    assert candidate.kill_switch_active is True


def test_approved_public_ready_outbox_variant_states_are_never_set(tmp_path):
    candidate = parse_markdown_review_candidate(
        _write(tmp_path / "draft.md", _valid_markdown("approved: true\npublication_ready: true\noutbox_creation_allowed: true\n"))
    )

    assert candidate.candidate_status == BLOCKED_STATUS
    assert candidate.approved_canonical_article_available is False
    assert candidate.publication_ready is False
    assert candidate.outbox_creation_allowed is False
    assert candidate.platform_variant_generation_allowed is False
    assert candidate.dispatch_allowed is False
    assert any(blocker.startswith("public_ready_or_approval_claim_detected_") for blocker in candidate.blockers)


def test_missing_h1_blocks_intake_even_with_frontmatter_title(tmp_path):
    markdown = "---\ntitle: Metadata Only Title\n---\nNo H1 here.\n"
    candidate = parse_markdown_review_candidate(_write(tmp_path / "draft.md", markdown))

    assert candidate.candidate_status == BLOCKED_STATUS
    assert candidate.title == ""
    assert "missing_h1_title" in candidate.blockers


def test_empty_markdown_blocks_intake(tmp_path):
    candidate = parse_markdown_review_candidate(_write(tmp_path / "draft.md", ""))

    assert candidate.candidate_status == BLOCKED_STATUS
    assert "empty_markdown" in candidate.blockers
    assert "missing_h1_title" in candidate.blockers


def test_non_markdown_extension_blocks_intake(tmp_path):
    candidate = parse_markdown_review_candidate(_write(tmp_path / "draft.txt", "# Title\n"))

    assert candidate.candidate_status == FAILED_STATUS
    assert "non_markdown_extension" in candidate.blockers
    assert candidate.canonical_article_review_candidate_available is False


def test_secret_like_marker_in_metadata_blocks_without_printing_raw_value(tmp_path):
    candidate = parse_markdown_review_candidate(
        _write(tmp_path / "draft.md", _valid_markdown("token: do-not-print-this-value\n"))
    )

    dumped = json.dumps(asdict(candidate), sort_keys=True)
    assert "raw_secret_marker_detected_token" in candidate.blockers
    assert candidate.redaction_applied is True
    assert candidate.redaction_reason == "secret_marker_detected"
    assert "redaction_applied_secret_marker_detected" in candidate.validation_warnings
    assert "do-not-print-this-value" not in dumped
    assert candidate.body_markdown == "[REDACTED_SECRET_MARKER_DETECTED]"
    assert candidate.detected_frontmatter["token"] == "[REDACTED_SECRET_MARKER_DETECTED]"


def test_secret_like_marker_in_body_blocks_without_printing_raw_value(tmp_path):
    body = "# Required H1 Title\n\nThis body mentions password value do-not-print-body-value.\n"
    candidate = parse_markdown_review_candidate(_write(tmp_path / "draft.md", _valid_markdown(body=body)))

    dumped = json.dumps(asdict(candidate), sort_keys=True)
    assert "raw_secret_marker_detected_password" in candidate.blockers
    assert candidate.redaction_applied is True
    assert candidate.redaction_reason == "secret_marker_detected"
    assert "redaction_applied_secret_marker_detected" in candidate.validation_warnings
    assert "do-not-print-body-value" not in dumped
    assert candidate.body_text == "[REDACTED_SECRET_MARKER_DETECTED]"


def test_advice_signal_trading_language_in_body_blocks_intake(tmp_path):
    body = "# Required H1 Title\n\nThis is a signal service with buy target and exit language.\n"
    candidate = parse_markdown_review_candidate(_write(tmp_path / "draft.md", _valid_markdown(body=body)))

    assert candidate.candidate_status == BLOCKED_STATUS
    assert "trading_or_signal_language_detected" in candidate.blockers


def test_output_packet_includes_sha256_headings_word_count_frontmatter_warnings(tmp_path):
    markdown = "---\nsubtitle: Test Subtitle\ninvalid-line\n---\n# Required H1 Title\n\nFirst paragraph words.\n\n## Section A\nMore words.\n"
    candidate = parse_markdown_review_candidate(_write(tmp_path / "draft.md", markdown))

    assert candidate.source_file_sha256
    assert candidate.headings == [
        {"level": 1, "text": "Required H1 Title"},
        {"level": 2, "text": "Section A"},
    ]
    assert candidate.word_count >= 6
    assert candidate.detected_frontmatter["subtitle"] == "Test Subtitle"
    assert "frontmatter_line_2_ignored_no_key_value_separator" in candidate.validation_warnings


def test_directory_intake_handles_multiple_md_files_deterministically(tmp_path):
    _write(tmp_path / "b.md", _valid_markdown(body="# B Title\n\nBody.\n"))
    sub = tmp_path / "nested"
    sub.mkdir()
    _write(sub / "a.md", _valid_markdown(body="# A Title\n\nBody.\n"))
    _write(tmp_path / "ignored.txt", "# Ignored\n")

    result = intake_markdown_review_candidates([tmp_path])

    assert result.candidate_count == 2
    assert [Path(candidate.source_file_path).name for candidate in result.candidates] == ["b.md", "a.md"]
    assert result.blocked_count == 0


def test_module_contains_no_getenv_environ_network_provider_browser_imports():
    source = Path("live_contentops/canonical_article_intake_v6.py").read_text(encoding="utf-8")

    forbidden = ["getenv", "environ", "requests", "urllib", "httpx", "provider_gateway", "browser", "webbrowser"]
    assert not any(marker in source for marker in forbidden)


def test_raw_bytes_sha256_is_used_for_crlf_and_bom(tmp_path):
    raw_bytes = b"\xef\xbb\xbf---\r\nsubtitle: Byte Hash\r\n---\r\n# Required H1 Title\r\n\r\nBody text.\r\n"
    draft = tmp_path / "draft.md"
    draft.write_bytes(raw_bytes)

    candidate = parse_markdown_review_candidate(draft)

    assert candidate.source_file_sha256 == hashlib.sha256(raw_bytes).hexdigest()


def test_written_packets_do_not_contain_secret_values(tmp_path):
    raw_metadata_value = "do-not-print-this-value"
    raw_body_value = "do-not-print-body-value"
    draft = _write(
        tmp_path / "draft.md",
        _valid_markdown(f"token: {raw_metadata_value}\n", body=f"# Required H1 Title\n\npassword {raw_body_value}\n"),
    )
    output_dir = tmp_path / "out"

    exit_code = main([str(draft), "--output-dir", str(output_dir)])

    assert exit_code == 1
    all_output = "\n".join(path.read_text(encoding="utf-8") for path in output_dir.glob("*.json"))
    assert raw_metadata_value not in all_output
    assert raw_body_value not in all_output
    assert "[REDACTED_SECRET_MARKER_DETECTED]" in all_output


def test_committed_docs_and_sample_are_utf8_without_bom_and_sample_loads():
    docs_dir = Path("docs/automation/V6_CANONICAL_ARTICLE_REVIEW_CANDIDATE_INTAKE_FROM_MARKDOWN")
    for path in docs_dir.glob("*"):
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    sample = docs_dir / "sample_review_candidate_packet.json"
    loaded = json.loads(sample.read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False
    assert loaded["source_file_sha256"] is None


def test_cli_writes_summary_and_candidate_packets(tmp_path):
    draft = _write(tmp_path / "draft.md", _valid_markdown())
    output_dir = tmp_path / "out"

    exit_code = main([str(draft), "--output-dir", str(output_dir)])

    assert exit_code == 0
    summary_path = output_dir / "canonical_article_review_candidate_intake_result.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["candidate_count"] == 1
    packet_paths = [
        path for path in output_dir.glob("canonical_article_review_candidate_*.json")
        if path.name != "canonical_article_review_candidate_intake_result.json"
    ]
    assert len(packet_paths) == 1
    packet = json.loads(packet_paths[0].read_text(encoding="utf-8"))
    assert packet["canonical_article_review_candidate_available"] is True
    assert packet["dispatch_allowed"] is False
