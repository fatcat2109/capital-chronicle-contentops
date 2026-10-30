from __future__ import annotations

import json
from pathlib import Path
import socket

import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.local_subscriber_markdown_v1 import (
    FORMATS, RenderError, SubscriberPolicy, main, render_piece, write_local_piece,
)


FIXTURES = Path(__file__).parent / "fixtures" / "local_subscriber_markdown_v1"


@pytest.fixture
def policy():
    return SubscriberPolicy.from_source(FIXTURES / "publication_policy_fixture.py")


def fixture(kind="event_card"):
    return json.loads((FIXTURES / (kind + ".json")).read_text(encoding="utf-8"))


def causes(piece):
    return {item["cause"] for item in piece.diagnostics["omissions"]}


@pytest.mark.parametrize("kind", FORMATS)
def test_four_real_fixture_outputs_are_local_readback_verified_and_idempotent(kind, policy, tmp_path, monkeypatch):
    def deny_network(*args, **kwargs):
        raise AssertionError("offline renderer attempted a network call")
    monkeypatch.setattr(socket.socket, "connect", deny_network)
    piece = render_piece(fixture(kind), policy)
    first = write_local_piece(piece, tmp_path)
    second = write_local_piece(piece, tmp_path)
    assert first["local_readback"] == "VERIFIED"
    assert first["publication_performed"] is False
    assert not first["idempotent_replay"] and second["idempotent_replay"]
    assert Path(first["markdown_path"]).read_text(encoding="utf-8") == piece.markdown
    store = ContentOpsDurableStore(tmp_path / "local-render-outbox.sqlite3", auto_migrate=False)
    with store.get_read_only_connection() as con:
        assert con.execute("select count(*) from outbox_messages").fetchone()[0] == 1
        assert con.execute("select count(*) from readbacks").fetchone()[0] == 1
        dispatch = dict(con.execute("select * from platform_dispatches").fetchone())
        assert dispatch["platform"] == "local_file_only"
        assert dispatch["public_object_id"] is None and dispatch["public_object_url"] is None


def test_scenarios_pricing_levels_and_invalidation_keep_meaning_and_spacing(policy):
    piece = render_piece(fixture(), policy)
    assert "Probability: 50%" in piece.markdown
    assert "assumption is 160000 jobs" in piece.markdown
    assert "reference of 4.2% is a level" in piece.markdown
    assert "## What would invalidate" in piece.markdown
    assert "fictional figures" in piece.markdown


@pytest.mark.parametrize("sentence", [
    "Prior pricing was 123456 jobs even if {priced} is tagged.",
    "Reference ١٢٣ is not sourced by an unrelated {priced} field.",
    "An edition ² must also be tagged.",
])
def test_any_untagged_digit_drops_entire_sentence_not_only_the_digit(sentence, policy):
    data = fixture()
    data["content"]["priced_in"] = [{"template": sentence}]
    piece = render_piece(data, policy)
    assert "UNTAGGED_DIGIT_SENTENCE_DROPPED" in causes(piece)
    assert "No sourced priced-in estimate" in piece.markdown
    assert "Prior pricing was" not in piece.markdown


@pytest.mark.parametrize("mutation,expected", [
    ({"source": None}, "SOURCE_MISSING"),
    ({"rights_tag": None}, "SOURCE_RIGHTS_NOT_ADMITTED"),
    ({"publication_field": "private_account.balance"}, "FIELD_NOT_ALLOWLISTED"),
    ({"value": None}, "MISSING_VALUE"),
    ({"value": float("nan")}, "NONFINITE_VALUE"),
    ({"value": {"raw": 12345}}, "SCALAR_VALUE_REQUIRED"),
])
def test_a_bad_referenced_field_drops_the_whole_sentence(mutation, expected, policy):
    data = fixture()
    data["fields"]["priced"].update(mutation)
    piece = render_piece(data, policy)
    assert expected in causes(piece)
    assert "assumption is 160000" not in piece.markdown


@pytest.mark.parametrize("mutation", [
    {"subscriber_or_public_projection_allowed": False},
    {"provider": "Unlicensed private vendor"},
    {"source_ref": "https://fred.stlouisfed.org/series/PAYEMS"},
    {"dataset_family": "bls_raw_quote_table"},
    {"authority_class": "license_required"},
])
def test_input_rights_tag_cannot_override_code_owned_source_contract(mutation, policy):
    data = fixture()
    data["sources"]["model"].update(mutation)
    piece = render_piece(data, policy)
    assert "SOURCE_RIGHTS_NOT_ADMITTED" in causes(piece)
    assert "160000" not in piece.markdown


def test_unknown_private_fields_are_never_copied(policy):
    data = fixture()
    data["private_account"] = {"balance": 987654321, "note": "DO_NOT_COPY"}
    data["fields"]["unreferenced"] = {"value": "DO_NOT_COPY"}
    piece = render_piece(data, policy)
    assert "987654321" not in piece.markdown and "DO_NOT_COPY" not in piece.markdown
    assert "unreferenced" not in piece.diagnostics["used_fields"]


@pytest.mark.parametrize("instruction", ["Entry at {level}.", "Buy after the release.", "Stop-loss below the range.", "Target {level}."])
def test_event_card_cannot_render_execution_instructions(instruction, policy):
    data = fixture()
    data["content"]["levels_of_interest"] = [{"template": instruction}]
    piece = render_piece(data, policy)
    assert "UNSAFE_OR_EXECUTION_TEXT" in causes(piece)
    assert "No supported reference levels" in piece.markdown


def test_sourced_field_cannot_smuggle_execution_html_or_markdown(policy):
    data = fixture()
    data["fields"]["event"]["value"] = "<img src=remote onerror=alert()>"
    piece = render_piece(data, policy)
    assert "<img" not in piece.markdown
    data["fields"]["event"]["value"] = "[Payrolls](https://example.test/)"
    assert "\\[Payrolls\\]" in render_piece(data, policy).markdown


def test_auto_delta_requires_official_actual_source_for_official_numbers(policy):
    data = fixture("auto_delta")
    data["fields"]["actual"]["source"] = "model"
    piece = render_piece(data, policy)
    assert "OFFICIAL_ACTUAL_REQUIRED" in causes(piece)
    assert "first-print payroll change" not in piece.markdown
    assert "unemployment rate is 4.3%" in piece.markdown


def test_signed_delta_and_all_ledger_entries_survive_without_invented_r(policy):
    assert "-15000 jobs" in render_piece(fixture("auto_delta"), policy).markdown
    piece = render_piece(fixture("saturday_ledger"), policy)
    assert "1.25R" in piece.markdown and "-0.75R" in piece.markdown
    for title in ("Cooling-labour thesis", "DEMO rates expression", "DEMO currency expression", "No trade in the competing view"):
        assert title in piece.markdown
    assert "no risk was allocated" in piece.markdown
    assert "unavailable; a sourced result" in piece.markdown
    assert "0R" not in piece.markdown


@pytest.mark.parametrize("denominator", [None, 0, -10])
def test_missing_or_nonpositive_denominator_never_becomes_zero_or_profitable_r(denominator, policy):
    data = fixture("saturday_ledger")
    data["fields"]["risk"]["value"] = denominator
    piece = render_piece(data, policy)
    assert "1.25R" not in piece.markdown and "-0.75R" not in piece.markdown
    assert "R_OR_POSITIVE_RISK_DENOMINATOR_MISSING" in causes(piece)


def test_balance_or_other_positive_number_is_not_a_risk_denominator(policy):
    data = fixture("saturday_ledger")
    data["fields"]["risk"].pop("role")
    piece = render_piece(data, policy)
    assert "1.25R" not in piece.markdown


def test_no_trade_is_not_a_zero_r_result(policy):
    data = fixture("saturday_ledger")
    data["content"]["entries"][-1]["result_r"] = "zero_r"
    piece = render_piece(data, policy)
    assert "NO_TRADE_HAS_NO_REALIZED_R" in causes(piece)
    assert "0R" not in piece.markdown


def test_positive_r_cannot_be_presented_as_a_loss(policy):
    data = fixture("saturday_ledger")
    data["fields"]["loss_r"]["value"] = 0.75
    piece = render_piece(data, policy)
    assert "LOSS_SIGN_CONFLICT" in causes(piece)
    assert "Risk-unit result: 0.75R" not in piece.markdown


def test_incomplete_probabilities_are_not_renormalized(policy):
    data = fixture()
    data["fields"]["cool_probability"]["value"] = None
    piece = render_piece(data, policy)
    assert "Probability: unavailable" in piece.markdown
    assert "Probability: 30%" in piece.markdown and "Probability: 20%" in piece.markdown


@pytest.mark.parametrize("value", [-1, 101, "not a probability"])
def test_invalid_probability_is_not_published(value, policy):
    data = fixture()
    data["fields"]["cool_probability"]["value"] = value
    assert "PROBABILITY_PERCENT_INVALID" in causes(render_piece(data, policy))


def test_complete_probability_set_with_wrong_total_is_refused(policy):
    data = fixture()
    data["fields"]["cool_probability"]["value"] = 45
    with pytest.raises(RenderError, match="DO_NOT_SUM"):
        render_piece(data, policy)


def test_week_ahead_preserves_missing_pricing_and_each_event(policy):
    piece = render_piece(fixture("week_ahead"), policy)
    assert "Payrolls" in piece.markdown and "Wage and participation detail" in piece.markdown
    assert "No sourced priced-in estimate is available" in piece.markdown
    assert "Friday at 08:30 EDT" in piece.markdown


def test_interrupted_local_write_reuses_original_outbox_and_readback(policy, tmp_path, monkeypatch):
    import live_contentops.local_subscriber_markdown_v1 as renderer
    piece = render_piece(fixture(), policy)
    original = renderer._immutable
    monkeypatch.setattr(renderer, "_immutable", lambda *a: (_ for _ in ()).throw(OSError("simulated local disk interruption")))
    with pytest.raises(OSError):
        write_local_piece(piece, tmp_path)
    monkeypatch.setattr(renderer, "_immutable", original)
    resumed = write_local_piece(piece, tmp_path)
    assert resumed["idempotent_replay"] and resumed["local_readback"] == "VERIFIED"


def test_prior_local_readback_does_not_mask_modified_file_or_overwrite_it(policy, tmp_path):
    piece = render_piece(fixture(), policy)
    result = write_local_piece(piece, tmp_path)
    path = Path(result["markdown_path"])
    path.write_text("tampered", encoding="utf-8")
    with pytest.raises(RenderError, match="LOCAL_ARTIFACT_CONFLICT"):
        write_local_piece(piece, tmp_path)
    assert path.read_text(encoding="utf-8") == "tampered"


def test_disk_interruption_cannot_leave_a_partial_final_markdown(policy, tmp_path, monkeypatch):
    import live_contentops.local_subscriber_markdown_v1 as renderer
    original = renderer.os.link
    monkeypatch.setattr(renderer.os, "link", lambda *a: (_ for _ in ()).throw(OSError("interrupted before atomic file visibility")))
    piece = render_piece(fixture(), policy)
    with pytest.raises(OSError):
        write_local_piece(piece, tmp_path)
    assert not list(tmp_path.glob("*.md"))
    monkeypatch.setattr(renderer.os, "link", original)
    assert write_local_piece(piece, tmp_path)["idempotent_replay"]


def test_changed_admitted_input_creates_a_new_immutable_revision(policy, tmp_path):
    data = fixture()
    first = write_local_piece(render_piece(data, policy), tmp_path)
    data["fields"]["priced"]["value"] = 165000
    second = write_local_piece(render_piece(data, policy), tmp_path)
    assert first["idempotency_key"] != second["idempotency_key"]
    assert "160000" in Path(first["markdown_path"]).read_text(encoding="utf-8")


def test_ast_policy_reader_never_executes_main_or_fixture_code(tmp_path):
    p = tmp_path / "policy.py"
    p.write_text((FIXTURES / "publication_policy_fixture.py").read_text() + "\nraise RuntimeError('MUST_NOT_EXECUTE')\n")
    assert SubscriberPolicy.from_source(p).fields


def test_missing_contract_is_fail_closed(tmp_path):
    p = tmp_path / "policy.py"
    p.write_text("FIELD_ALLOWLIST = ('one',)\n")
    with pytest.raises(RenderError, match="CONTRACT_MISSING"):
        SubscriberPolicy.from_source(p)


def test_relocated_store_is_refused_before_any_database_migration(policy, tmp_path, monkeypatch):
    import live_contentops.native_desktop_workspace_v1 as workspace
    outside = tmp_path.parent / "must-not-create.sqlite3"
    monkeypatch.setattr(workspace, "resolve_workspace_path", lambda p: outside)
    with pytest.raises(RenderError, match="LOCAL_STORE_RELOCATION_ESCAPES_DIRECTORY"):
        write_local_piece(render_piece(fixture(), policy), tmp_path)
    assert not outside.exists()


@pytest.mark.parametrize("root", [Path("A:/Capital Chronicle/Runtime/ContentOps"), Path("C:/Users/bullw/AppData/Local/CapitalChronicle/ContentOps/new-render")])
def test_cli_cannot_target_any_existing_production_or_private_runtime_tree(root, policy):
    with pytest.raises(RenderError, match="ISOLATED_LOCAL_OUTPUT_REQUIRED"):
        write_local_piece(render_piece(fixture(), policy), root)


def test_current_main_literal_contract_matches_test_excerpt_when_available(policy):
    p = Path("A:/Capital Chronicle/Main App/tools/product/subscriber_publication_v1.py")
    if not p.is_file():
        pytest.skip("Main source is not present on this machine; portable fixture tests still apply")
    actual = SubscriberPolicy.from_source(p)
    assert actual.fields == policy.fields and actual.contracts == policy.contracts


def test_cli_writes_a_complete_offline_piece(policy, tmp_path, capsys):
    assert main(["--input", str(FIXTURES / "event_card.json"), "--output-dir", str(tmp_path), "--publication-contract", str(FIXTURES / "publication_policy_fixture.py")]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["local_readback"] == "VERIFIED" and result["publication_performed"] is False
