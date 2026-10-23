"""Bounded local steps of the existing native factory; no scheduler or model invoker."""

from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from .creative import hash_file, hash_value, validate_input_packet
from .desktop_session import ParentSessionProvenance, BoundedCreativeProvenance
from .store import V2JobStore
from .supervisor import DesktopSessionV2Factory, FactoryConfig, _write_immutable_json


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def factory(config_path):
    raw = load(config_path)
    repo = Path(__file__).resolve().parents[2]
    runtime = Path(raw["runtime_root"]).resolve()
    if (
        not runtime.is_relative_to(repo / ".task-runtime")
        or raw.get("mode") != "ISOLATED_MANUAL_PRIVATE_ENGINEERING"
    ):
        raise ValueError("Explicit isolated manual private runtime required")
    config = FactoryConfig(
        **{
            k: Path(raw[k])
            for k in (
                "runtime_root",
                "scaffold_root",
                "dependency_root",
                "asset_root",
                "kokoro_model",
                "kokoro_voices",
            )
        },
        implementation_head=raw["implementation_head"],
        worker_id=raw["worker_id"],
        parent_provenance=ParentSessionProvenance(session_label=raw["session_label"]),
    )
    return DesktopSessionV2Factory(
        store=V2JobStore(runtime / "v2_jobs.sqlite3"), config=config
    ), raw


def request_for(f, result):
    if result.get("result") != "AWAITING_CODEX_DESKTOP_SESSION_INPUT":
        return result
    job = f.store.job(result["video_job_id"])
    paths = f._paths(job["video_job_id"])
    kind = result["required_input"]
    kind = {"MOTION_VISUAL_AUTHORSHIP": "MOTION_VISUAL"}.get(kind, kind)
    names = {
        "EDITORIAL_NARRATION": ["input_packet"],
        "MOTION_VISUAL": ["input_packet", "editor", "timing_lock"],
        "EDITORIAL_TIMING_REVISION": [
            "input_packet",
            "editor_initial",
            "narration_overrun",
        ],
        "ACTUAL_MEDIA_REVIEW": [
            "input_packet",
            "editor",
            "timing_lock",
            "motion",
            "proxy",
            "proxy_sheet",
        ],
    }[kind]
    bindings = {}
    for name in names:
        path = Path(job["input_packet_path"]) if name == "input_packet" else paths[name]
        bindings[name] = {"path": str(path), "sha256": hash_file(path)}
    value = dict(
        schema="contentops.v2.manual_native_request.v1",
        video_job_id=job["video_job_id"],
        run_id=job["run_id"],
        kind=kind,
        requested_model="gpt-5.6-sol",
        requested_reasoning_effort="xhigh",
        bindings=bindings,
        actual_runtime_attestation="NOT_AVAILABLE",
        public_write_authority=False,
        instructions="Fresh assigned native role only. No provider/CLI bridge. Preserve exact source dates, qualifiers, free-form story-specific source. Return a JSON artifact plus self-reported native task identity; no hearing from text or playback commands.",
    )
    path = paths["session_inbox"] / ("request_" + kind.lower() + ".json")
    _write_immutable_json(path, value)
    return dict(result, native_request=str(path), request_sha256=hash_value(value))


def command(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "command", choices=["admit", "step", "submit", "status", "caption-layout"]
    )
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--packet", type=Path)
    p.add_argument("--job")
    p.add_argument("--return-file", type=Path)
    p.add_argument("--max-stages", type=int, default=1)
    p.add_argument("--revision")
    p.add_argument("--width", type=int, default=32)
    a = p.parse_args(argv)
    f, raw = factory(a.config)
    if a.command == "admit":
        if not a.packet or not a.job:
            p.error("admit needs exact packet and job")
        packet = load(a.packet)
        validate_input_packet(packet)
        result = f.store.seed_job(
            video_job_id=a.job,
            input_packet_path=a.packet,
            input_packet_hash=hash_value(packet),
            target_format="SHORT_9_16_1080X1920_30FPS",
        )
    elif a.command == "status":
        result = dict(jobs=f.store.jobs(), public_write_authority=False)
    elif a.command == "caption-layout":
        if not a.job or not re.fullmatch(r"[A-Za-z0-9_.-]+", a.revision or ""):
            p.error("caption-layout needs job and safe revision identity")
        job = f.store.job(a.job)
        if job["state"] != "OWNER_REVIEW_READY":
            raise ValueError(
                "Caption revision requires an existing sealed private package"
            )
        from .caption_revision import revise_caption_layout

        paths = f._paths(a.job)
        result = revise_caption_layout(
            paths["package"], paths["root"] / "revisions" / a.revision, width=a.width
        )
    elif a.command == "submit":
        if not a.job or not a.return_file:
            p.error("submit needs job and exact native return")
        job = f.store.job(a.job)
        value = load(a.return_file)
        kind = value["kind"]
        if kind not in {
            "EDITORIAL_NARRATION",
            "EDITORIAL_TIMING_REVISION",
            "MOTION_VISUAL",
            "ACTUAL_MEDIA_REVIEW",
        }:
            raise ValueError("Unsupported native request kind")
        request = load(
            f._paths(a.job)["session_inbox"] / ("request_" + kind.lower() + ".json")
        )
        if request["video_job_id"] != a.job or request["run_id"] != job["run_id"]:
            raise ValueError("Native request job/run mismatch")
        if value.get("request_sha256") != hash_value(request) or not value.get(
            "native_task_id"
        ):
            raise ValueError("Exact requested native return binding required")
        if (value.get("model"), value.get("reasoning_effort")) != (
            "gpt-5.6-sol",
            "xhigh",
        ) or value.get(
            "provenance_limit"
        ) != "ASSIGNED_ROLE_NOT_INDEPENDENT_RUNTIME_ATTESTATION":
            raise ValueError("Requested role and truthful provenance limit required")
        for spec in request["bindings"].values():
            if hash_file(spec["path"]) != spec["sha256"]:
                raise ValueError("Native request input drift")
        provenance = BoundedCreativeProvenance(
            parent=f.config.parent_provenance,
            execution_label=value["native_task_id"],
            native_child_task_id=value["native_task_id"],
        )
        methods = {
            "EDITORIAL_NARRATION": ("submit_editorial_narration", "editor"),
            "EDITORIAL_TIMING_REVISION": ("submit_editorial_timing_revision", "editor"),
            "MOTION_VISUAL": ("submit_motion_visual", "motion"),
            "ACTUAL_MEDIA_REVIEW": ("submit_actual_media_review", "review"),
        }
        method, arg = methods[kind]
        result = getattr(f, method)(
            video_job_id=a.job,
            run_id=job["run_id"],
            provenance=provenance,
            **{arg: value["artifact"]},
        )
    else:
        if not 1 <= a.max_stages <= 14:
            p.error("max-stages must be1..14")
        job = f.store.job(a.job) if a.job else None
        if job and job["state"] in {"OWNER_REVIEW_READY", "TERMINAL", "QUARANTINED"}:
            result = dict(result=job["terminal_result"], job=job, executed_stages=[])
        elif job and job.get("run_id") and job.get("claimed_by") == f.config.worker_id:
            result = f.resume(
                video_job_id=a.job, run_id=job["run_id"], max_new_stages=a.max_stages
            )
        else:
            # Each invocation is a new process; bounded checkpoints release their
            # claim. Reacquire through the existing store, preserving its run_id.
            result = f.run_once(max_new_stages=a.max_stages, video_job_id=a.job)
        result = request_for(f, result)
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(command())
