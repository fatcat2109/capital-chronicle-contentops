"""V6 Canonical Article Markdown Review-Candidate Intake.

Local-only parser for operator-provided canonical article Markdown drafts.
Creates review-candidate packets only; never approves, publishes, dispatches,
hydrates credentials, reads process config, starts UI sessions, or calls model services.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_CANONICAL_ARTICLE_REVIEW_CANDIDATE_INTAKE_FROM_MARKDOWN_V0"
SCHEMA_VERSION = "6.0.0"
DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_CANONICAL_ARTICLE_REVIEW_CANDIDATE_INTAKE_FROM_MARKDOWN")

REVIEW_STATUS = "REVIEW_CANDIDATE_PENDING_HUMAN_REVIEW"
BLOCKED_STATUS = "REVIEW_CANDIDATE_BLOCKED_PENDING_OPERATOR_REPAIR"
FAILED_STATUS = "INTAKE_FAILED_CLOSED"

SECRET_MARKERS = (
    "token",
    "api_key",
    "password",
    "bearer",
    "cookie",
    "webhook_url",
    "private_key",
    "secret",
    "credential",
)
PUBLIC_READY_MARKERS = (
    "approved",
    "approval_status",
    "approved_canonical_article_available",
    "publication_ready",
    "allowed_for_publication",
    "publication_allowed",
    "public_postable",
    "dispatch_allowed",
    "platform_variant_generation_allowed",
    "outbox_creation_allowed",
    "public_url",
    "public_metrics",
    "canonical_public_url",
)
TRADING_ADVICE_PATTERNS = (
    r"\bbuy\b",
    r"\bsell\b",
    r"\bhold\b",
    r"\bposition\s+sizing\b",
    r"\bentry\b",
    r"\bexit\b",
    r"\btarget\b",
    r"\bguaranteed\s+prediction\b",
    r"\bsignal\s+service\b",
    r"\btrading\s+advice\b",
)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
WORD_RE = re.compile(r"\b[\w'-]+\b")


@dataclass(frozen=True)
class ArticleReviewCandidate:
    schema_version: str
    task_label: str
    candidate_status: str
    candidate_id: str
    source_file_path: str
    source_file_sha256: str | None
    title: str
    subtitle: str
    description: str
    headings: list[dict[str, Any]]
    body_text: str
    body_markdown: str
    word_count: int
    detected_frontmatter: dict[str, Any]
    validation_warnings: list[str]
    blockers: list[str] = field(default_factory=list)
    canonical_article_review_candidate_available: bool = False
    approved_canonical_article_available: bool = False
    human_review_required: bool = True
    publication_ready: bool = False
    dispatch_allowed: bool = False
    platform_variant_generation_allowed: bool = False
    outbox_creation_allowed: bool = False
    public_url: None = None
    public_metrics: None = None
    review_only: bool = True
    kill_switch_active: bool = True
    redaction_applied: bool = False
    redaction_reason: str = ""


@dataclass(frozen=True)
class ArticleIntakeResult:
    schema_version: str
    task_label: str
    intake_status: str
    candidate_count: int
    blocked_count: int
    failed_count: int
    candidates: list[ArticleReviewCandidate]
    blockers: list[str]
    review_only: bool = True
    human_review_required: bool = True
    approved_count: int = 0
    dispatch_allowed_count: int = 0
    publication_ready_count: int = 0
    outbox_creation_allowed_count: int = 0
    platform_variant_generation_allowed_count: int = 0


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def split_frontmatter(markdown: str) -> tuple[dict[str, Any], str, list[str]]:
    markdown = markdown.replace("\r\n", "\n").replace("\r", "\n")
    warnings: list[str] = []
    if not markdown.startswith("---\n"):
        return {}, markdown, ["frontmatter_missing"]
    end = markdown.find("\n---\n", 4)
    if end == -1:
        return {}, markdown, ["frontmatter_closing_marker_missing"]
    raw_meta = markdown[4:end]
    body = markdown[end + 5:]
    metadata: dict[str, Any] = {}
    for line_no, raw_line in enumerate(raw_meta.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            warnings.append(f"frontmatter_line_{line_no}_ignored_no_key_value_separator")
            continue
        key, value = line.split(":", 1)
        normalized_key = key.strip().lower().replace("-", "_")
        if not normalized_key:
            warnings.append(f"frontmatter_line_{line_no}_ignored_empty_key")
            continue
        metadata[normalized_key] = _parse_scalar(value)
    return metadata, body, warnings


def resolve_markdown_paths(input_path: Path) -> tuple[list[Path], list[str]]:
    path = Path(input_path)
    if path.is_dir():
        return sorted((item for item in path.rglob("*.md") if item.is_file()), key=lambda p: p.as_posix()), []
    if path.suffix.lower() != ".md":
        return [path], ["non_markdown_extension"]
    return [path], []


def _plain_text(markdown: str) -> str:
    text = re.sub(r"```.*?```", " ", markdown, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[#>*_\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _first_paragraph(body_markdown: str) -> str:
    for block in re.split(r"\n\s*\n", body_markdown.strip()):
        cleaned = block.strip()
        if cleaned and not cleaned.startswith("#"):
            return _plain_text(cleaned)
    return ""


def _headings(body_markdown: str) -> list[dict[str, Any]]:
    return [
        {"level": len(match.group(1)), "text": match.group(2).strip()}
        for match in HEADING_RE.finditer(body_markdown)
    ]


def _has_marker(text: str, markers: tuple[str, ...]) -> list[str]:
    lowered = text.lower()
    return [marker for marker in markers if marker in lowered]


def _trading_blockers(text: str) -> list[str]:
    lowered = text.lower()
    blockers = []
    for pattern in TRADING_ADVICE_PATTERNS:
        if re.search(pattern, lowered):
            blockers.append("trading_or_signal_language_detected")
    return sorted(set(blockers))


def _metadata_text(metadata: dict[str, Any]) -> str:
    return " ".join(f"{key} {value}" for key, value in metadata.items())


def _secret_markers_for_content(metadata: dict[str, Any], body: str) -> list[str]:
    combined = f"{_metadata_text(metadata)} {body}"
    return _has_marker(combined, SECRET_MARKERS)


def _redacted_frontmatter(metadata: dict[str, Any]) -> dict[str, str]:
    if not metadata:
        return {"_redacted": "secret_marker_detected"}
    return {str(key): "[REDACTED_SECRET_MARKER_DETECTED]" for key in sorted(metadata)}


def _blockers_for_content(path: Path, markdown: str, metadata: dict[str, Any], body: str) -> list[str]:
    blockers: list[str] = []
    if path.suffix.lower() != ".md":
        blockers.append("non_markdown_extension")
    if not markdown.strip():
        blockers.append("empty_markdown")
    if not H1_RE.search(body):
        blockers.append("missing_h1_title")

    combined = f"{_metadata_text(metadata)} {body}"
    for marker in _secret_markers_for_content(metadata, body):
        blockers.append(f"raw_secret_marker_detected_{marker}")
    for marker in _has_marker(combined, PUBLIC_READY_MARKERS):
        blockers.append(f"public_ready_or_approval_claim_detected_{marker}")
    blockers.extend(_trading_blockers(combined))
    return sorted(set(blockers))


def _failed_candidate(path: Path, blockers: list[str]) -> ArticleReviewCandidate:
    safe_path = str(Path(path))
    digest = hashlib.sha256(safe_path.encode("utf-8")).hexdigest()
    return ArticleReviewCandidate(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        candidate_status=FAILED_STATUS,
        candidate_id=f"canonical_article_review_candidate_failed_{digest[:16]}",
        source_file_path=safe_path,
        source_file_sha256=None,
        title="",
        subtitle="",
        description="",
        headings=[],
        body_text="",
        body_markdown="",
        word_count=0,
        detected_frontmatter={},
        validation_warnings=[],
        blockers=sorted(set(blockers)),
        canonical_article_review_candidate_available=False,
        redaction_applied=False,
        redaction_reason="",
    )


def parse_markdown_review_candidate(path: Path) -> ArticleReviewCandidate:
    source_path = Path(path)
    if source_path.suffix.lower() != ".md":
        return _failed_candidate(source_path, ["non_markdown_extension"])
    raw_bytes = source_path.read_bytes()
    source_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    try:
        markdown = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        return _failed_candidate(source_path, ["markdown_utf8_decode_failed"])
    metadata, body, warnings = split_frontmatter(markdown)
    h1_match = H1_RE.search(body)
    title = h1_match.group(1).strip() if h1_match else ""
    subtitle = str(metadata.get("subtitle") or metadata.get("description") or _first_paragraph(body)).strip()
    description = str(metadata.get("description") or subtitle).strip()
    headings = _headings(body)
    body_text = _plain_text(body)
    blockers = _blockers_for_content(source_path, markdown, metadata, body)
    secret_detected = bool(_secret_markers_for_content(metadata, body))
    redaction_applied = secret_detected
    redaction_reason = "secret_marker_detected" if secret_detected else ""
    if secret_detected:
        warnings = sorted(set(warnings + ["redaction_applied_secret_marker_detected"]))
        metadata = _redacted_frontmatter(metadata)
        body = "[REDACTED_SECRET_MARKER_DETECTED]"
        body_text = "[REDACTED_SECRET_MARKER_DETECTED]"
        subtitle = ""
        description = ""
        headings = []
    status = BLOCKED_STATUS if blockers else REVIEW_STATUS
    candidate_id = f"canonical_article_review_candidate_{source_sha256[:16]}"
    return ArticleReviewCandidate(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        candidate_status=status,
        candidate_id=candidate_id,
        source_file_path=str(source_path),
        source_file_sha256=source_sha256,
        title=title,
        subtitle=subtitle,
        description=description,
        headings=headings,
        body_text=body_text,
        body_markdown=body,
        word_count=len(WORD_RE.findall(body_text)) if not redaction_applied else 0,
        detected_frontmatter=metadata,
        validation_warnings=warnings,
        blockers=blockers,
        canonical_article_review_candidate_available=(not blockers),
        redaction_applied=redaction_applied,
        redaction_reason=redaction_reason,
    )


def intake_markdown_review_candidates(paths: list[Path]) -> ArticleIntakeResult:
    candidates: list[ArticleReviewCandidate] = []
    path_blockers: list[str] = []
    for input_path in paths:
        resolved, blockers = resolve_markdown_paths(Path(input_path))
        path_blockers.extend(blockers)
        candidates.extend(parse_markdown_review_candidate(path) for path in resolved)
    blockers = sorted({blocker for candidate in candidates for blocker in candidate.blockers} | set(path_blockers))
    blocked_count = sum(1 for candidate in candidates if candidate.candidate_status == BLOCKED_STATUS)
    failed_count = sum(1 for candidate in candidates if candidate.candidate_status == FAILED_STATUS)
    status = "FAILED_WITH_BLOCKERS" if blockers else "PASSED_REVIEW_CANDIDATES_READY_FOR_HUMAN_REVIEW"
    return ArticleIntakeResult(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        intake_status=status,
        candidate_count=len(candidates),
        blocked_count=blocked_count,
        failed_count=failed_count,
        candidates=candidates,
        blockers=blockers,
    )


def write_intake_packets(result: ArticleIntakeResult, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for candidate in result.candidates:
        packet_path = output_dir / f"{candidate.candidate_id}.json"
        packet_path.write_text(json.dumps(asdict(candidate), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = asdict(result)
    summary["candidates"] = [candidate.candidate_id for candidate in result.candidates]
    (output_dir / "canonical_article_review_candidate_intake_result.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 canonical article Markdown review-candidate intake")
    parser.add_argument("paths", nargs="+", help="Markdown draft files or directories")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)
    result = intake_markdown_review_candidates([Path(value) for value in args.paths])
    write_intake_packets(result, Path(args.output_dir))
    return 1 if result.blockers else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
