"""For Ops: import the exact accepted CC-074 packet, then prepare the existing publisher.

The default is read-only. --apply requires the hash of a fresh dry-run plan. This
does not publish, acquire sources, invoke models, change controls or schedules.
The private operation and its original binding/returns/review remain unchanged.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from hashlib import sha256
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    sha256_of,
)
from live_contentops.native_desktop_editorial_v1 import native_review_revision
from live_contentops.native_desktop_publication_v1 import prepare_native_publication
from live_contentops.native_desktop_workspace_v1 import resolve_workspace_path
from live_contentops.native_publication_promotion_v1 import (
    ReadOnlyStore, _snapshot, _write_exact as _write_exact, promote as _promote,
)
from live_contentops.retrospective_piece_v1 import validate_retrospective_piece

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/publisher/CC-074-private-20261101"
MANIFEST = ROOT / "docs/publisher/CC-074-live-20261102/promotion-manifest.json"
MANIFEST_SHA256 = "3297d335b23d7ac64bfd403a301b276f64307bfde52545ebbf635802a202a185"
ORIGINAL_PACKAGE = Path(
    r"A:\Capital Chronicle\Worktrees\ContentOps\codex-publisher-backlog"
    r"\docs\publisher\CC-074-private-20261101"
)
SOURCE_BINDING = Path(
    r"A:\Capital Chronicle\Worktrees\ContentOps\codex-publisher-backlog"
    r"\.task-runtime\cc-074\private-20261101\articles"
    r"\cc074-retro-fomc-20261028-v1\binding.json"
)
PROMOTION_DESTINATION = "internal:native-retrospective-promotion"


def _digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def _json(path):
    return json.loads(Path(path).read_bytes())


def _relocate(value, root):
    """Read-only validation view; never serialize relocated historical records."""
    if isinstance(value, dict):
        return {k: _relocate(v, root) for k, v in value.items()}
    if isinstance(value, list):
        return [_relocate(v, root) for v in value]
    if isinstance(value, str) and value.startswith(str(ORIGINAL_PACKAGE) + "\\"):
        return str(root / Path(value[len(str(ORIGINAL_PACKAGE)) + 1 :]))
    return value


def verify_source(*, package_root=PACKAGE, binding_path=SOURCE_BINDING):
    """Pin the one granted FOMC packet; no arbitrary private-example promotion."""
    if _digest(MANIFEST) != MANIFEST_SHA256:
        raise ValueError("CC074_PROMOTION_MANIFEST_CHANGED")
    pin = _json(MANIFEST)
    root, binding_path = Path(package_root).resolve(), Path(binding_path).resolve()
    if _digest(root / "artifact-sha256.json") != pin["retained_seals_sha256"]:
        raise ValueError("CC074_ACCEPTED_SEALS_CHANGED")
    artifacts = _json(root / "artifact-sha256.json")["artifacts"]
    if len(artifacts) != 207:
        raise ValueError("CC074_EXACT_ACCEPTED_PACKAGE_REQUIRED")
    files = []
    original = resolve_workspace_path(ORIGINAL_PACKAGE)
    for artifact in artifacts:
        relative = Path(artifact["path"])
        source, target = (root / relative).resolve(), (original / relative).resolve()
        if (
            relative.is_absolute()
            or not source.is_relative_to(root)
            or not target.is_relative_to(original)
        ):
            raise ValueError("CC074_SEALED_PATH_OUTSIDE_PACKAGE")
        if (
            _digest(source) != artifact["sha256"]
            or source.stat().st_size != artifact["bytes"]
        ):
            raise ValueError("CC074_SEALED_BYTES_CHANGED:" + str(relative))
        if target.exists() and (
            not target.is_file() or _digest(target) != artifact["sha256"]
        ):
            raise ValueError("CC074_EXISTING_ARTIFACT_CONFLICT:" + str(target))
        files.append(
            {"source": str(source), "target": str(target), "sha256": artifact["sha256"]}
        )
    if _digest(binding_path) != pin["source_binding_sha256"]:
        raise ValueError("CC074_ORIGINAL_BINDING_CHANGED")
    binding = _json(binding_path)
    if (
        binding.get("owner_manual_validation") is not True
        or binding.get("run_id") != pin["run_id"]
        or resolve_workspace_path(binding["output_dir"]) != binding_path.parent
    ):
        raise ValueError("CC074_EXACT_PRIVATE_OPERATION_REQUIRED")
    source = ReadOnlyStore(binding["store_path"])
    rows, reviews, item = _snapshot(source, binding["run_id"])
    if {r["message_id"]: sha256_of(r) for r in rows} != pin["source_outbox_rows"] or {
        r["review_id"]: sha256_of(r) for r in reviews
    } != pin["source_reviews"]:
        raise ValueError("CC074_ACCEPTED_NATIVE_HISTORY_CHANGED")
    by_id = {r["message_id"]: r for r in rows}
    registered = by_id["native-operation-binding-" + sha256_of(binding["run_id"])]
    if json.loads(registered["payload"]) != binding:
        raise ValueError("CC074_EXACT_SOURCE_BINDING_REQUIRED")
    result = json.loads(
        by_id["cc-editorial-final-" + sha256_of(binding["run_id"])]["payload"]
    )
    if (
        result["article_identity"] != pin["article_identity"]
        or native_review_revision(result) != pin["package_revision"]
    ):
        raise ValueError("CC074_ACCEPTED_ARTICLE_REVISION_CHANGED")
    record = binding_path.parent / "qualified_article_record_v1.json"
    if _digest(record) != pin["qualified_record_sha256"]:
        raise ValueError("CC074_QUALIFIED_RECORD_CHANGED")
    piece = _relocate(_json(root / "piece.json"), root)
    check = validate_retrospective_piece(
        piece,
        documents=_relocate(_json(root / "chart-source-documents.json"), root),
        chart_assets=_relocate(_json(root / "chart-assets.json"), root),
        article_text=(root / "article.md").read_text(encoding="utf-8"),
    )
    final = _json(
        root
        / ("native/desktop_request_" + piece["final_visual_review"]["stage"] + ".json")
    )
    for name, digest in final["governed_input"]["binding"]["renderer_sha256"].items():
        if _digest(ROOT / name) != digest:
            raise ValueError("CC074_RENDERER_CHANGED_REVIEW_REQUIRED:" + name)
    return {
        "pin": pin,
        "binding": binding,
        "rows": rows,
        "reviews": reviews,
        "item": item,
        "files": files,
        "qualified_record": str(record),
        "artifact_root": str(ORIGINAL_PACKAGE),
        "source_check": check,
    }


def promote(operation, rollout, *, apply=False, expected_plan_sha256=None):
    """Keep the exact CC-074 interface over the shared import owner."""
    return _promote(operation, rollout, apply=apply,
        expected_plan_sha256=expected_plan_sha256, prepare=prepare_native_publication)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rollout", type=Path, default=ROOT / "config/native_desktop_rollout_v1.json"
    )
    parser.add_argument("--package-root", type=Path, default=PACKAGE)
    parser.add_argument("--source-binding", type=Path, default=SOURCE_BINDING)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="For Ops only: import and prepare; never dispatch",
    )
    parser.add_argument("--expected-plan-sha256")
    args = parser.parse_args(argv)
    try:
        rollout = _json(args.rollout)
        live_root = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
        for name, expected in (
            ("store_path", live_root / "contentops_daily_app_v1.sqlite3"),
            ("editorial_output_root", live_root / "daily_app_outputs"),
            ("published_output_root", live_root / "daily_app_outputs"),
        ):
            if resolve_workspace_path(rollout[name]) != expected.resolve():
                raise ValueError("CC074_EXISTING_LIVE_OWNER_PATHS_REQUIRED:" + name)
        operation = verify_source(
            package_root=args.package_root, binding_path=args.source_binding
        )
        result = promote(
            operation,
            rollout,
            apply=args.apply,
            expected_plan_sha256=args.expected_plan_sha256,
        )
    except (ValueError, OSError, sqlite3.Error, KeyError) as error:
        print(
            json.dumps(
                {
                    "classification": "CC074_PROMOTION_BLOCKED",
                    "blocker": str(error),
                    "public_write_performed": False,
                },
                indent=2,
            )
        )
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
