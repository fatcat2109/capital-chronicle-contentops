"""CC-406 product path: exact Main/official inputs -> native copy -> CC-418 files."""
from copy import deepcopy
from datetime import date, datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from live_contentops import vietnamese_gold_note_v1 as gold
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes

NOW = datetime(2026, 11, 13, 0, 0, tzinfo=timezone.utc)  # 07:00 GMT+7
TEXT = ("Vàng còn chịu áp lực từ lãi suất\n\n"
        "Tôi nghiêng về kịch bản vàng còn yếu nếu đô la giữ đà mạnh. "
        "Theo BLS, CPI chung tăng 0.4% và CPI lõi tăng 0.3% theo tháng, đã điều chỉnh mùa vụ. "
        "Lạm phát dai dẳng có thể giữ lãi suất cao, gây bất lợi cho vàng. "
        "Ngược lại, đô la hạ nhiệt sẽ làm nhận định này yếu đi.\n\n" + gold.NOTICE)


def fixture_context(tmp_path, monkeypatch):
    from live_contentops import main_report_projection_source_v1 as projection
    root = tmp_path / "requests"
    folder = root / "request-current"
    folder.mkdir(parents=True)
    monkeypatch.setattr(projection, "NATIVE_MAIN_REPORT_ROOT", root)
    stamp = "2026-11-12T22:00:00Z"
    report = {"candidates": [{"candidate_id": "cand_macro_" + aliases[0],
        "rationale": "Base case: a dated market view. Mechanism: rates.\nPriced: private detail.\nPlan: private detail."}
        for aliases in gold.MARKETS.values()]}
    path = folder / "owner-native.json"
    path.write_bytes(canonical_bytes(report))
    os.utime(path, (NOW.timestamp() - 3600, NOW.timestamp() - 3600))
    (folder / "capture.json").write_bytes(canonical_bytes({"known_at_utc": stamp}))
    official_text = ("The Consumer Price Index for All Urban Consumers (CPI-U) increased 0.4 percent on a seasonally adjusted basis. "
                     "The index for all items less food and energy rose 0.3 percent in October.")
    evidence = [{"key": "unrelated-private-row", "content": ["not a release"]},
        {"key": "bls-cpi-test", "known_at_utc": "2026-11-10T13:30:00Z",
         "rights_state": {"rights_state": "PUBLIC_DOMAIN_ATTRIBUTION_REQUIRED"},
         "content": {"source_url": "https://www.bls.gov/news.release/cpi.nr0.htm", "reference_period": "2026-M10",
                     "official_text": official_text}}]
    (folder / "role-evidence.json").write_bytes(canonical_bytes(evidence))
    return gold.source_context(now=NOW, report_root=root), root


def test_context_uses_latest_capture_and_exact_public_spans_without_private_rows(tmp_path, monkeypatch):
    context, root = fixture_context(tmp_path, monkeypatch)
    assert len(context["six_market_table"]) == 6
    assert context["data_cutoff_utc"] == "2026-11-12T22:00:00+00:00"
    assert context["source_age_seconds"] == 7200  # usable dated context, not an invented fresh clock
    assert "private detail" not in json.dumps(context)
    assert [f["display"] for f in context["official_facts"]] == ["0.4%", "0.3%"]
    evidence = json.loads((root / "request-current/role-evidence.json").read_bytes())
    for fact in context["official_facts"]:
        text = evidence[1]["content"]["official_text"]
        a, b = fact["source_span"]
        assert text[a:b] == fact["source_excerpt"]
        assert sha256(text.encode()).hexdigest() == fact["official_text_sha256"]
    # A newer mtime over an older capture cannot replace the latest Main view.
    old = root / "request-older"
    old.mkdir()
    (old / "owner-native.json").write_bytes((root / "request-current/owner-native.json").read_bytes())
    (old / "capture.json").write_bytes(canonical_bytes({"known_at_utc": "2026-11-01T00:00:00Z"}))
    assert gold._latest_report(root, NOW).parent.name == "request-current"


@pytest.mark.parametrize("change,cause", [
    ("future_official", "HELD_OFFICIAL_CPI_RELEASE_ABSENT"),
    ("private_rights", "HELD_OFFICIAL_CPI_RELEASE_ABSENT"),
    ("absent_gold", "MAIN_GOLD_VIEW_ABSENT"),
])
def test_source_failure_names_the_actual_fact_right_or_gold_gap(tmp_path, monkeypatch, change, cause):
    _, root = fixture_context(tmp_path, monkeypatch)
    folder = root / "request-current"
    if change == "absent_gold":
        path = folder / "owner-native.json"
        value = json.loads(path.read_bytes())
        value["candidates"] = value["candidates"][1:]
    else:
        path = folder / "role-evidence.json"
        value = json.loads(path.read_bytes())
        if change == "future_official":
            value[1]["known_at_utc"] = "2026-11-13T01:00:00Z"
        else:
            value[1]["rights_state"]["rights_state"] = "PUBLIC_REDISTRIBUTION_NOT_LICENSED"
    path.write_bytes(canonical_bytes(value))
    if change == "absent_gold":
        os.utime(path, (NOW.timestamp() - 3600, NOW.timestamp() - 3600))
    with pytest.raises(ValueError, match=cause):
        gold.source_context(now=NOW, report_root=root)


@pytest.mark.parametrize("change,cause", [
    (lambda x: x.update(text="word " * 151 + gold.NOTICE), "150_WORD"),
    (lambda x: x.update(text=x["text"].replace(gold.NOTICE, "")), "FINAL_NOTICE"),
    (lambda x: x.update(text="Capital Chronicle\n" + x["text"]), "BRAND"),
    (lambda x: x.update(text=x["text"].replace("0.4%", "0.9%")), "NUMBER_NOT"),
    (lambda x: x.update(fact_ids=["invented"]), "FACT_BINDINGS"),
    (lambda x: x.update(text="Bạn nên mua vàng.\n" + x["text"]), "PERSONAL_ADVICE"),
    (lambda x: x.update(text=x["text"].replace("BLS", "nguồn tin")), "ATTRIBUTION"),
])
def test_copy_rejects_measured_numeric_privacy_and_contract_failures(tmp_path, monkeypatch, change, cause):
    context, _ = fixture_context(tmp_path, monkeypatch)
    output = {"text": TEXT, "fact_ids": ["headline", "core"]}
    assert gold.validate_note(output, context) == output
    change(output)
    with pytest.raises(ValueError, match=cause):
        gold.validate_note(output, context)


def native_note(tmp_path, monkeypatch):
    context, root = fixture_context(tmp_path, monkeypatch)
    monkeypatch.setattr(gold, "source_context", lambda **kw: context)
    monkeypatch.setattr("live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled", lambda: None)
    store = ContentOpsDurableStore(tmp_path / "test.sqlite3")
    args = {"output_root": tmp_path / "output", "notes_root": tmp_path / "gold-notes", "now": NOW, "report_root": root}
    pending = gold.prepare(store, **args)
    assert pending["state"] == "GOLD_NOTE_NATIVE_INPUT_REQUIRED"
    turn = gold._turn(store, args["output_root"], NOW.astimezone(gold.LOCAL).date())
    request = turn.frozen_request("gold-note")
    assert request["requested_model"] == "gpt-6.1-sol" and request["requested_reasoning_effort"] == "max"
    assert "separate from the Capital Chronicle brand" in request["prompt"]
    observation = {"surface": "CODEX_EXEC", "model": None, "reasoning_effort": None,
        "configured_model": "gpt-6.1-sol", "configured_reasoning_effort": "max",
        "configuration_status": "CONFIGURED_NOT_OBSERVED", "invocation_id": "controlled-test-context",
        "observation_source": "TEST_FIXTURE"}
    response = {"request_sha256": request["request_sha256"], "output": {"text": TEXT, "fact_ids": ["headline", "core"]},
                "invocation_observation": observation}
    turn.submit("gold-note", response)
    preview = gold.prepare(store, **args)
    assert preview["state"] == "GOLD_NOTE_RENDER_REVIEW_REQUIRED"
    return store, args, preview, request, response


def test_native_note_replays_exact_input_and_installs_both_desk_files_after_review(tmp_path, monkeypatch):
    store, args, preview, request, response = native_note(tmp_path, monkeypatch)
    from PIL import Image
    with Image.open(preview["chart_path"]) as image:
        assert image.size == (1500, 900)
    assert not list(args["notes_root"].glob("*.md"))
    monkeypatch.setattr(gold, "source_context", lambda **kw: pytest.fail("must reuse the exact issued Main view"))
    assert gold.prepare(store, **args)["source_pack_sha256"] == preview["source_pack_sha256"]
    review = {"text_sha256": preview["text_sha256"], "chart_sha256": preview["chart_sha256"],
              "accepted": True, "findings": "Controlled fixture: correct official bars, units and source; readable."}
    result = gold.accept(store, output_root=args["output_root"], review=review, now=NOW, notes_root=args["notes_root"])
    assert result["ready_by_0730"] and result["acceptance_morning"]
    # This is CC-418's installed filename contract, including its paired chart.
    path = sorted(args["notes_root"].glob("20??-??-??*.md"), reverse=True)[0]
    assert path.read_text(encoding="utf-8").strip() == TEXT
    assert path.with_suffix(".png").is_file()
    saved = json.loads(path.with_suffix(".json").read_bytes())
    assert saved["native_request_sha256"] == request["request_sha256"]
    assert saved["invocation_observation"] == response["invocation_observation"]
    assert saved["public_write_performed"] is False
    first_clock = saved["prepared_at_utc"]
    gold.accept(store, output_root=args["output_root"], review=review, now=NOW.replace(hour=1), notes_root=args["notes_root"])
    assert json.loads(path.with_suffix(".json").read_bytes())["prepared_at_utc"] == first_clock
    path.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="BYTES_CHANGED"):
        gold.status(notes_root=args["notes_root"], day=NOW.date())


def test_a_review_must_bind_the_exact_text_and_png_before_desk_delivery(tmp_path, monkeypatch):
    store, args, preview, _, _ = native_note(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="EXACT_RENDER_INSPECTION"):
        gold.accept(store, output_root=args["output_root"], review={"accepted": True, "findings": "unbound"},
                    now=NOW, notes_root=args["notes_root"])
    assert not list(args["notes_root"].glob("*.md"))


def test_calendar_never_backdates_a_late_note_or_creates_a_future_morning(tmp_path, monkeypatch):
    store, args, preview, _, _ = native_note(tmp_path, monkeypatch)
    review = {"text_sha256": preview["text_sha256"], "chart_sha256": preview["chart_sha256"],
              "accepted": True, "findings": "Controlled render inspection."}
    result = gold.accept(store, output_root=args["output_root"], review=review, now=NOW.replace(hour=1), notes_root=args["notes_root"])
    assert result["ready_by_0730"] is False
    with pytest.raises(ValueError, match="FUTURE_DAY"):
        gold.prepare(store, **args, day=date(2026, 11, 16))
    assert gold.prepare(store, **{**args, "now": datetime(2026, 11, 14, tzinfo=timezone.utc)})["state"] == "NO_TRADING_DAY_NOTE_DUE"


def test_the_existing_native_entry_prepares_gold_even_when_digest_fails(tmp_path, monkeypatch):
    import importlib.util
    path = Path(__file__).resolve().parents[1] / "scripts/run_native_desktop_editorial.py"
    spec = importlib.util.spec_from_file_location("cc406_native_cli", path)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    from types import SimpleNamespace
    monkeypatch.setattr(cli, "ContentOpsDurableStore", lambda *a, **kw: SimpleNamespace())
    def unavailable(*a, **kw):
        raise ValueError("controlled digest gap")
    monkeypatch.setattr("live_contentops.substack_daily_digest_v1.production_digest_housekeeping", unavailable)
    calls = []
    monkeypatch.setattr(gold, "command", lambda rollout, action: calls.append((rollout, action)) or {"state": "GOLD_NOTE_NATIVE_INPUT_REQUIRED"})
    rollout = tmp_path / "rollout.json"
    rollout.write_text(json.dumps({"store_path": "isolated-test-only"}), encoding="utf-8")
    result = cli.with_due_digest({"classification": "CURRENT_EDITION_STATE"}, rollout)
    assert result["classification"] == "CURRENT_EDITION_STATE"
    assert result["daily_email_digest"]["state"] == "DIGEST_PREPARATION_FAILED"
    assert result["vietnamese_gold_note"]["state"] == "GOLD_NOTE_NATIVE_INPUT_REQUIRED"
    assert calls == [({"store_path": "isolated-test-only"}, "gold-note")]
