"""Incremental read-only Main feed over the existing ContentOps durable owners.

The configured pointer pins immutable Git blobs. This module never fetches, changes Main,
starts a scheduler, publishes, or creates another database. A routine slot invokes this
adapter in place of its usual Simple call, preserving one selector/writer budget.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence
from uuid import uuid4

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    LatestReportDeliveryTracker,
    LatestReportConsumerError,
    canonical_bytes,
    sha256_of,
    validate_latest_report_bytes,
    _private,
    _time,
)
from live_contentops.capital_chronicle_report_editorial_workspace_v1 import (
    CURRENT,
    run_report_editorial_cycle,
)

SCHEMA = "contentops.main_report_feed.v1"
POINTER_SCHEMA = "contentops.main_report_feed_pointer.v1"
FEED = "internal:cc-report-feed"
OPPORTUNITY = "internal:cc-report-opportunity"
POINTER_ENV = "CONTENTOPS_MAIN_REPORT_FEED_POINTER"
MAIN_REPOSITORY = "https://github.com/fatcat2109/Headline-Raw-data-json"


def configured_pointer() -> dict[str, Any] | None:
    path = os.environ.get(POINTER_ENV)
    return json.loads(Path(path).read_bytes()) if path else None


class PinnedMainGitSource:
    def __init__(self, pointer: Mapping[str, Any]):
        self.pointer = dict(pointer)
        self.root = Path(pointer["checkout"])
        self.commit = str(pointer["producer_commit"])
        if (
            pointer.get("schema_version") != POINTER_SCHEMA
            or pointer.get("producer_repository") != MAIN_REPOSITORY
            or not re.fullmatch(r"[0-9a-f]{40}", self.commit)
        ):
            raise LatestReportConsumerError("MAIN_FEED_POINTER_IDENTITY_INVALID")
        remote = (
            subprocess.check_output(
                ["git", "-C", str(self.root), "remote", "get-url", "origin"], text=True
            )
            .strip()
            .removesuffix(".git")
        )
        if remote != MAIN_REPOSITORY:
            raise LatestReportConsumerError("MAIN_FEED_CHECKOUT_REMOTE_MISMATCH")

    def read(self, path: str) -> bytes:
        normalized = PurePosixPath(path)
        if (
            normalized.is_absolute()
            or ".." in normalized.parts
            or "\\" in path
            or ":" in path
            or not path.startswith(
                ("docs/research/analysis_reporting/", "schemas/analysis_reporting/")
            )
        ):
            raise LatestReportConsumerError("MAIN_FEED_PATH_OUTSIDE_REPORT_EXPORT")
        size = int(
            subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(self.root),
                    "cat-file",
                    "-s",
                    self.commit + ":" + path,
                ]
            )
        )
        if size > 4_000_000:
            raise LatestReportConsumerError("MAIN_FEED_BLOB_OVERSIZED")
        return subprocess.check_output(
            ["git", "-C", str(self.root), "show", self.commit + ":" + path]
        )

    def bundle(self, spec: Mapping[str, str]) -> dict[str, Any]:
        names = {
            "envelope.json": "envelope",
            "report.json": "report",
            "CapitalChronicleAssetAnalysisReportV1.schema.json": "report_schema",
            "CapitalChronicleLatestAnalysisReportEnvelopeV1.schema.json": "envelope_schema",
        }
        raw = {key: self.read(spec[key]) for key in names.values()}
        envelope = json.loads(raw["envelope"])
        files = {
            name: {
                "path": spec[key],
                "sha256": hashlib.sha256(raw[key]).hexdigest(),
                "bytes": len(raw[key]),
            }
            for name, key in names.items()
        }
        binding = {
            "producer_repository": MAIN_REPOSITORY,
            "producer_commit": self.commit,
            "producer_revision": self.commit,
            "contract_revision": envelope.get("contract_revision"),
            "envelope_schema_sha256": files[
                "CapitalChronicleLatestAnalysisReportEnvelopeV1.schema.json"
            ]["sha256"],
            "report_schema_sha256": files[
                "CapitalChronicleAssetAnalysisReportV1.schema.json"
            ]["sha256"],
            "files": files,
        }
        return {**raw, "binding": binding}


def _persist(store, key: str, value: Mapping[str, Any], destination: str) -> None:
    if _private(value):
        raise LatestReportConsumerError("PRIVATE_FEED_PROJECTION_EXCLUDED")
    work = "cc-feed-" + sha256_of([destination, key])
    store.create_work_item(
        story_id=work,
        title="Governed intelligence feed",
        target_surface="CONTENTOPS_EDITORIAL_ONLY",
        work_item_id=work,
    )
    store.register_outbox_message(
        message_id=key,
        work_item_id=work,
        destination=destination,
        payload=canonical_bytes(value).decode(),
        status="EDITORIAL_INTERNAL",
    )


class MainReportFeed:
    def __init__(
        self,
        tracker: LatestReportDeliveryTracker,
        pointer: Mapping[str, Any],
        *,
        source=None,
        headline_paths=None,
        pointer_loader=None,
    ):
        self.tracker = tracker
        self.pointer = dict(pointer)
        self.source = source or PinnedMainGitSource(pointer)
        self.headline_paths = headline_paths
        self.pointer_loader = pointer_loader
        if not 0 < len(pointer.get("bundles", [])) <= 64:
            raise LatestReportConsumerError("MAIN_FEED_BUNDLE_BOUND_INVALID")

    def poll(self, *, cutoff_utc: str) -> dict[str, Any]:
        owner = "cc-feed-" + uuid4().hex
        lease = self.tracker.store.acquire_lease(
            "internal:cc-report-feed", owner, ttl_seconds=120
        )
        try:
            bundles, gaps = [], []
            if self.pointer_loader is not None:
                try:
                    current = self.pointer_loader()
                    if current != self.pointer:
                        if not current or not 0 < len(current.get("bundles", [])) <= 64:
                            raise LatestReportConsumerError(
                                "MAIN_FEED_BUNDLE_BOUND_INVALID"
                            )
                        source = PinnedMainGitSource(current)
                        self.pointer, self.source = dict(current), source
                except (
                    OSError,
                    ValueError,
                    KeyError,
                    TypeError,
                    subprocess.CalledProcessError,
                ):
                    summary = {
                        "schema_version": SCHEMA,
                        "producer_commit": self.pointer["producer_commit"],
                        "observed_at_utc": cutoff_utc,
                        "configured_bundle_count": 0,
                        "new_events": 0,
                        "events": [],
                        "gaps": [{"state": "MAIN_FEED_POINTER_UNAVAILABLE_OR_INVALID"}],
                        "coverage": "CONFIGURED_IMMUTABLE_EXPORTS_ONLY",
                        "public_write_performed": False,
                    }
                    _persist(
                        self.tracker.store,
                        "cc-feed-scan-" + sha256_of(summary),
                        summary,
                        FEED,
                    )
                    return summary
            for spec in self.pointer["bundles"]:
                try:
                    b = self.source.bundle(spec)
                    e = json.loads(b["envelope"])
                    if _private(e):
                        gaps.append({"state": "PRIVATE_CONTEXT_EXCLUDED"})
                        continue
                    if (
                        not isinstance(e.get("report_id"), str)
                        or type(e.get("report_version")) is not int
                    ):
                        raise LatestReportConsumerError("MAIN_REPORT_IDENTITY_INVALID")
                    if any(
                        _time(e[key]) > _time(cutoff_utc)
                        for key in (
                            "known_at_cutoff_utc",
                            "generated_at_utc",
                            "as_of_utc",
                        )
                    ):
                        gaps.append(
                            {
                                "state": "FUTURE_REPORT_DEFERRED",
                                "report_id": e["report_id"],
                            }
                        )
                        continue
                    bundles.append((e, b))
                except (
                    OSError,
                    ValueError,
                    KeyError,
                    TypeError,
                    AttributeError,
                    subprocess.CalledProcessError,
                ):
                    gaps.append({"state": "MAIN_EXPORT_UNAVAILABLE_OR_INVALID"})
            events, new = [], 0
            for e, b in sorted(
                bundles,
                key=lambda pair: (pair[0]["report_id"], pair[0]["report_version"]),
            ):
                raw_hash = hashlib.sha256(b["envelope"]).hexdigest()
                existing = next(
                    (
                        r
                        for r in self.tracker.receipts()
                        if r["raw_sha256"] == raw_hash and r["status"] in CURRENT
                    ),
                    None,
                )
                if existing:
                    events.append(
                        {
                            "report_id": existing["report_id"],
                            "report_version": existing["report_version"],
                            "receipt_id": existing["receipt_id"],
                            "state": "DUPLICATE_NOOP",
                        }
                    )
                    continue
                try:
                    validation = validate_latest_report_bytes(
                        b["envelope"],
                        report_bytes=[b["report"]],
                        expected_cutoff_utc=cutoff_utc,
                        envelope_schema_bytes=b["envelope_schema"],
                        report_schema_bytes=b["report_schema"],
                        producer_binding=b["binding"],
                        allow_lineage_only=True,
                    )
                except (ValueError, KeyError, TypeError):
                    gaps.append(
                        {
                            "state": "MAIN_EXPORT_UNAVAILABLE_OR_INVALID",
                            "envelope_raw_sha256": raw_hash,
                        }
                    )
                    continue
                parent_received = any(
                    r["status"] in CURRENT
                    and r.get("source_report_sha256") == e.get("parent_report_sha256")
                    for r in self.tracker.receipts()
                )
                receipt_id = "main-feed-" + sha256_of(
                    [raw_hash, parent_received, b["binding"], validation["status"]]
                )
                was_seen = any(
                    r["receipt_id"] == receipt_id for r in self.tracker.receipts()
                )
                record = self.tracker.consume(validation, receipt_id=receipt_id)
                new += int(not was_seen)
                events.append(
                    {
                        "report_id": record.get("report_id"),
                        "report_version": record.get("report_version"),
                        "receipt_id": receipt_id,
                        "state": record["status"],
                        "blockers": record.get("blockers", []),
                    }
                )
            summary = {
                "schema_version": SCHEMA,
                "producer_commit": self.pointer["producer_commit"],
                "observed_at_utc": cutoff_utc,
                "configured_bundle_count": len(self.pointer["bundles"]),
                "new_events": new,
                "events": events,
                "gaps": gaps,
                "coverage": "CONFIGURED_IMMUTABLE_EXPORTS_ONLY",
                "public_write_performed": False,
            }
            _persist(
                self.tracker.store, "cc-feed-scan-" + sha256_of(summary), summary, FEED
            )
            return summary
        finally:
            self.tracker.store.release_lease(
                lease["lease_id"], owner, lease["fencing_token"]
            )

    def pending(self, *, include_controlled: bool = True) -> list[dict[str, Any]]:
        latest = {}
        for record in self.tracker.receipts():
            if record["status"] not in CURRENT:
                continue
            if record["status"] == "NO_MATERIAL_CHANGE_NOOP":
                continue
            old = latest.get(record["report_id"])
            if old is None or record["report_version"] > old["report_version"]:
                latest[record["report_id"]] = record
        results = [
            json.loads(r["payload"])
            for r in self.tracker.store.list_outbox_messages()
            if r["destination"] == "internal:cc-report-simple-result"
        ]
        return [
            r
            for r in sorted(
                latest.values(),
                key=lambda v: (v["known_at_cutoff_utc"], v["report_id"]),
                reverse=True,
            )
            if r["status"] == "ADMITTED"
            and not any(
                v.get("report_id") == r["report_id"]
                and v.get("report_version") == r["report_version"]
                and v.get("classification") == "DRAFT_READY"
                and (
                    include_controlled
                    or v.get("model_execution_state") == "EXISTING_SIMPLE_PROVIDER"
                )
                for v in results
            )
        ]

    def opportunity(
        self,
        *,
        output_dir: str | Path,
        cutoff_utc: str,
        run_id: str,
        published_memory: Sequence[Any] = (),
        rolling_input=None,
        llm_invoke=None,
        source_route_health=None,
        attempted_candidate_ids=(),
    ) -> dict[str, Any]:
        """One existing newsroom slot; all reports compete with normal news in one Simple call."""
        scan = self.poll(cutoff_utc=cutoff_utc)
        from live_contentops.contentops_main_headline_projection_v1 import (
            MainHeadlineExporter,
            permitted_report_headlines,
        )
        from live_contentops.headline_data_root_v1 import canonical_headline_sidecar_dir

        export = MainHeadlineExporter(self.tracker.store).export(
            batch_id=run_id,
            paths=(
                self.headline_paths
                if self.headline_paths is not None
                else sorted(
                    canonical_headline_sidecar_dir().glob(
                        "step1_headline_sidecar_*.jsonl"
                    )
                )[-4:]
            ),
            cutoff_utc=cutoff_utc,
            permitted_rows=permitted_report_headlines(self.tracker),
        )
        export_root = Path(output_dir)
        export_root.mkdir(parents=True, exist_ok=True)
        (export_root / "main_headline_projection.json").write_bytes(
            canonical_bytes(export)
        )
        (export_root / "main_headline_rows.jsonl").write_bytes(
            b"".join(canonical_bytes(row) + b"\n" for row in export["rows"])
        )
        pending = self.pending(include_controlled=llm_invoke is not None)
        previous = self.tracker.store.get_outbox_message(
            "cc-editorial-final-" + sha256_of(run_id)
        )
        if previous:
            cached = json.loads(previous["payload"])
            record = next(
                r
                for r in self.tracker.receipts()
                if r["receipt_id"] == cached["receipt_id"]
            )
            cached = run_report_editorial_cycle(
                self.tracker,
                receipt_id=record["receipt_id"],
                admission=record,
                output_dir=output_dir,
                cutoff_utc=cutoff_utc,
                opportunity_id=run_id,
            )
            semantic = cached.get("simple_result", cached)
            if cached["classification"] not in {
                "DRAFT_READY",
                "INDEPENDENT_NEWS_DRAFT",
            }:
                semantic = {
                    **semantic,
                    "qualified_article_count": 0,
                    "derivative_intent_count": 0,
                    "classification": cached["classification"],
                }
            return {**semantic, "report_workspace_result": cached}
        pool = self.tracker.store.get_outbox_message(
            "cc-editorial-pool-" + sha256_of(run_id)
        )
        if pool:
            # A restarted slot must resume its frozen selection/source/writer pool even if
            # new reports or successful outputs have changed the live pending inventory.
            pending = json.loads(pool["payload"])["reports"]
        if rolling_input is None:
            from live_contentops.newsroom_assignment_scheduler_v1 import (
                load_rolling_x_headline_sidecars,
            )

            rolling_input = load_rolling_x_headline_sidecars(cutoff_utc=cutoff_utc)
        if not pending:
            from live_contentops.production_orchestrator_v1 import (
                ContentOpsProductionOrchestrator,
            )

            return dict(
                ContentOpsProductionOrchestrator().execute(
                    "run_v1_simple_gemini_newsroom",
                    output_dir=output_dir,
                    cutoff_utc=cutoff_utc,
                    run_id=run_id,
                    published_memory=published_memory,
                    rolling_input=rolling_input,
                    llm_invoke=llm_invoke,
                    source_route_health=source_route_health,
                    attempted_candidate_ids=attempted_candidate_ids,
                )
            )
        result = run_report_editorial_cycle(
            self.tracker,
            receipt_id=pending[0]["receipt_id"],
            admission=pending[0],
            output_dir=output_dir,
            cutoff_utc=cutoff_utc,
            rolling_input=rolling_input,
            published_memory=published_memory,
            llm_invoke=llm_invoke,
            run_id=run_id,
            additional_reports=pending[1:],
            opportunity_id=run_id,
            source_route_health=source_route_health,
            attempted_candidate_ids=attempted_candidate_ids,
        )
        disposition = {
            "schema_version": SCHEMA,
            "opportunity_id": run_id,
            "observed_at_utc": cutoff_utc,
            "report_candidates": [
                {
                    "report_id": r["report_id"],
                    "report_version": r["report_version"],
                    "state": "SELECTED"
                    if result.get("report_id") == r["report_id"]
                    and result.get("draft_count")
                    else "DEFERRED",
                    "receipt_id": r["receipt_id"],
                }
                for r in pending
            ],
            "classification": result["classification"],
            "exact_next_blocker": result.get("exact_next_blocker"),
            "fresh_model_calls": 0
            if llm_invoke
            or result.get("model_execution_state") == "PAUSED_BEFORE_PROVIDER_CALL"
            else result.get("logical_model_invocation_count", 0),
            "feed_scan_new_events": scan["new_events"],
            "public_write_performed": False,
        }
        _persist(
            self.tracker.store,
            "cc-opportunity-" + sha256_of(disposition),
            disposition,
            OPPORTUNITY,
        )
        semantic = result.get("simple_result", result)
        if result["classification"] not in {"DRAFT_READY", "INDEPENDENT_NEWS_DRAFT"}:
            semantic = {
                **semantic,
                "qualified_article_count": 0,
                "derivative_intent_count": 0,
                "classification": result["classification"],
            }
        return {
            **semantic,
            "report_workspace_result": result,
            "exact_next_blocker": result.get("exact_next_blocker"),
        }

    def can_resume(self, run_id: str) -> bool:
        return (
            self.tracker.store.get_outbox_message(
                "cc-editorial-pool-" + sha256_of(run_id)
            )
            is not None
        )
