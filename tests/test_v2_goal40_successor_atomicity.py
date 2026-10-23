"""Private successor crash boundaries; fixture media never claims AV quality."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from video.unattended_core_factory_v1 import media
from video.unattended_core_factory_v1.store import V2JobStore
from video.unattended_core_factory_v1.supervisor import DesktopSessionV2Factory


SCHEMA = "contentops.v2.platform_neutral_publication_package.v1"


def sealed_owner(tmp_path):
    store = V2JobStore(tmp_path / "jobs.sqlite3")
    store.seed_job(video_job_id="same", input_packet_path=tmp_path / "input",
                   input_packet_hash="a" * 64, target_format="SHORT")
    job = store.claim_next(worker_id="test", implementation_head="b" * 40)
    root = tmp_path / "jobs/same"
    root.mkdir(parents=True)
    def write(name, value):
        p = root / name
        p.write_text(json.dumps(value), encoding="utf-8")
        return p
    old = write("old.json", dict(schema=SCHEMA, package_id="old", source_story_id="story",
        source_film_id=job["run_id"], artifacts={}, rights_provenance_refs=[], factual_evidence_refs=[]))
    paths = {name:write(name+".json", {}) for name in ["timing_lock","seo"]}
    paths["picture"] = root / "accepted-picture.fixture"
    paths["picture"].write_bytes(b"complete picture")
    truncated = root / "truncated.fixture"
    truncated.write_bytes(b"truncated picture")
    paths["mix"] = root / "mix.fixture"
    paths["mix"].write_bytes(b"preserved audio")
    paths["bundle"] = write("bundle.json", dict(quality_acceptance={}))
    value = json.loads(old.read_text())
    value["artifacts"] = {"canonical_picture":media.artifact(truncated)}
    for kind in ["json","srt","vtt"]:
        caption = root / ("captions."+kind)
        caption.write_text("sealed caption fixture")
        value["artifacts"]["caption_"+kind] = media.artifact(caption)
    old.write_text(json.dumps(value))
    paths.update(root=root, package=old)
    def event(stage, artifacts, revision="old"):
        return store.append_event(video_job_id="same", run_id=job["run_id"], stage=stage,
            input_hashes={}, output_hashes={}, artifacts=[media.artifact(p) for p in artifacts],
            role_tool_identity="fixture", model_provenance={}, wall_time_seconds=0, safe_usage={},
            result="PASS_"+stage, retry_state={"revision":revision}, next_legal_stage=None)
    event("PICTURE_LOCKED", [paths["picture"]])
    event("FINAL_MEDIA_BUILT", [truncated])
    event("PACKAGE_QA_PASSED", [old])
    event("OWNER_REVIEW_READY", [paths["bundle"]])
    store.finalize(video_job_id="same",run_id=job["run_id"],
        result="PRIVATE_ENGINEERING_PACKAGE_REVIEW_REQUIRED",state="OWNER_REVIEW_READY")
    f = object.__new__(DesktopSessionV2Factory)
    f.store = store
    f._paths = lambda _: paths
    return f, paths, event


@pytest.mark.parametrize("stop", [1,2,3,4])
def test_package_pointer_waits_for_matching_owner_revision(tmp_path, stop):
    f, paths, _ = sealed_owner(tmp_path)
    new = paths["root"] / "new.json"
    new.write_text(json.dumps(dict(schema=SCHEMA,package_id="new")))
    stages={"AUDIO_BUILT":[paths["mix"]],"FINAL_MEDIA_BUILT":[paths["picture"]],
            "PACKAGE_QA_PASSED":[new],"OWNER_REVIEW_READY":[new]}
    append=f.store.append_event
    count=0
    def crash(**kwargs):
        nonlocal count
        value=append(**kwargs)
        if kwargs["result"].startswith("PASS"):
            count+=1
            if count==stop:
                raise RuntimeError("crash")
        return value
    spec=dict(job=f.store.job("same"), stages=stages, inputs={},role="fixture",
              result_prefix="PASS_NEW_",revision="new")
    f.store.append_event=crash
    with pytest.raises(RuntimeError,match="crash"):
        f._record_private_successor(**spec)
    assert f.current_package_path("same")== (new if stop==4 else paths["package"])
    f.store.append_event=append
    f._record_private_successor(**spec)
    assert f.current_package_path("same")==new


def repair_media(f, monkeypatch):
    from video.locale_activation_hardening_v1 import factory
    monkeypatch.setattr(factory,"inspect_picture",lambda p:dict(video_stream_sha256=Path(p).read_bytes().decode()))
    calls=[]
    def mux(*,picture,mix,output):
        calls.append("mux")
        output.write_bytes(picture.read_bytes()+mix.read_bytes())
        return dict(final_media=media.artifact(output))
    def technical(path,output):
        calls.append("technical")
        output.write_text(json.dumps(dict(result="PASS_FIXTURE")))
        return dict(report_artifact=media.artifact(output))
    def package(**kwargs):
        calls.append("package")
        p=kwargs["output"]
        p.write_text(json.dumps(dict(schema=SCHEMA,package_id="new",artifacts={
            "canonical_picture":media.artifact(kwargs["final_media"])})))
        return dict(package_id="new")
    def sheet(path,output):
        calls.append("sheet")
        output.write_bytes(b"explicit image fixture")
        return dict(artifact=media.artifact(output))
    f.media=SimpleNamespace(mux_final_media=mux,technical_media_report=technical,
        build_neutral_package=package,contact_sheet=sheet)
    return calls


@pytest.mark.parametrize("boundary", ["mkdir","mux-unsealed","mux","technical","package","sheet",
                                      "invalidate1","pass1","invalidate2","pass2","invalidate3","pass3"])
def test_mux_repair_replays_filesystem_and_ledger_crashes(tmp_path,monkeypatch,boundary):
    import video.unattended_core_factory_v1.supervisor as supervisor
    f,paths,_=sealed_owner(tmp_path)
    calls=repair_media(f,monkeypatch)
    root=paths["root"] / "revisions/repair"
    append=f.store.append_event
    write=supervisor._write_immutable_json
    counter={"invalidate":0,"pass":0}
    fired=False
    def crash_event(**kwargs):
        nonlocal fired
        v=append(**kwargs)
        kind="invalidate" if kwargs["result"].startswith("INVALIDATED") else "pass"
        counter[kind]+=1
        if boundary==kind+str(counter[kind]):
            fired=True
            raise RuntimeError("crash")
        return v
    def crash_write(path,value):
        nonlocal fired
        v=write(path,value)
        if path.name==boundary+"_step.json":
            fired=True
            raise RuntimeError("crash")
        return v
    if boundary=="mkdir":
        root.mkdir(parents=True)
    elif boundary=="mux-unsealed":
        mux=f.media.mux_final_media
        def crash_mux(**kwargs):
            nonlocal fired
            mux(**kwargs)
            fired=True
            raise RuntimeError("crash")
        f.media.mux_final_media=crash_mux
    f.store.append_event=crash_event
    monkeypatch.setattr(supervisor,"_write_immutable_json",crash_write)
    if boundary!="mkdir":
        with pytest.raises(RuntimeError,match="crash"):
            f.repair_mux_package(video_job_id="same",revision="repair")
        assert fired
        assert f.store.job("same")["state"]=="OWNER_REVIEW_READY"
        assert f.current_package_path("same")== (root/"manifest.json" if boundary=="pass3" else paths["package"])
    f.store.append_event=append
    monkeypatch.setattr(supervisor,"_write_immutable_json",write)
    if boundary=="mux-unsealed":
        f.media.mux_final_media=mux
    result=f.repair_mux_package(video_job_id="same",revision="repair")
    assert result["package_id"]=="new"
    assert f.current_package_path("same")==root/"manifest.json"
    assert f.store.job("same")["state"]=="OWNER_REVIEW_READY"
    assert calls.count("mux")== (2 if boundary=="mux-unsealed" else 1)
    assert all(calls.count(name)==1 for name in ["technical","package","sheet"])
    before=len(f.store.events("same"))
    assert f.repair_mux_package(video_job_id="same",revision="repair")["idempotent_replay"]
    assert len(f.store.events("same"))==before
    assert paths["picture"].read_bytes()==b"complete picture"
    assert paths["mix"].read_bytes()==b"preserved audio"
