"""CC-014 desk-record export schema v1: the fixture validates and the visibility rules hold."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import pytest
from jsonschema import Draft202012Validator

from tools.product.desk_record_projection_v1 import (
    PRIVATE_ONLY_RIGHTS,
    RECORD_LISTS,
    check_clocks,
    check_public_text,
    check_references,
    iter_fields,
    project,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = (
    ROOT / "schemas" / "publication" / "CapitalChronicleDeskRecordExportV1.schema.json"
)
FIXTURE_PATH = (
    ROOT
    / "tests"
    / "fixtures"
    / "desk_record_export_v1"
    / "desk_record_export_v1.fixture.json"
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator() -> Draft202012Validator:
    schema = _load(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _errors(doc: dict[str, Any]) -> list[str]:
    return sorted(error.message for error in _validator().iter_errors(doc))


def _doc() -> dict[str, Any]:
    return copy.deepcopy(_load(FIXTURE_PATH))


def _dossier(doc: dict[str, Any], asset_id: str) -> dict[str, Any]:
    return next(item for item in doc["asset_dossiers"] if item["asset_id"] == asset_id)


def _card(doc: dict[str, Any], event_id: str) -> dict[str, Any]:
    return next(item for item in doc["event_cards"] if item["event_id"] == event_id)


def _publish(
    field: dict[str, Any], label: str = "PUBLIC_OWN_ANALYSIS_NOT_ADVICE"
) -> None:
    field["visibility"] = "public"
    field["use_label"] = label


def test_schema_is_valid_draft_2020_12() -> None:
    Draft202012Validator.check_schema(_load(SCHEMA_PATH))


def test_fixture_validates() -> None:
    assert _errors(_load(FIXTURE_PATH)) == []


def test_module_private_classes_match_the_schema() -> None:
    schema = _load(SCHEMA_PATH)
    assert set(
        schema["$defs"]["PrivateOnlyField"]["allOf"][1]["properties"]["rights_class"][
            "enum"
        ]
    ) == set(PRIVATE_ONLY_RIGHTS)


def test_integrity_hash_matches_canonical_content() -> None:
    doc = _load(FIXTURE_PATH)
    body = {key: value for key, value in doc.items() if key != "integrity"}
    canonical = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    assert doc["integrity"]["content_sha256"] == hashlib.sha256(canonical).hexdigest()


def test_references_resolve() -> None:
    assert check_references(_load(FIXTURE_PATH)) == []


def test_clocks_never_run_ahead_of_the_export_or_behind_their_inputs() -> None:
    assert check_clocks(_load(FIXTURE_PATH)) == []


def test_public_and_pro_text_carry_no_private_terms_numbers_or_vendors() -> None:
    doc = _load(FIXTURE_PATH)
    assert check_public_text(doc, ("public",)) == []
    assert check_public_text(doc, ("public", "pro")) == []


@pytest.mark.parametrize("allowed", [("public",), ("public", "pro")])
def test_projection_leaks_no_private_value(allowed: tuple[str, ...]) -> None:
    doc = _load(FIXTURE_PATH)
    projected = project(doc, allowed)
    text = json.dumps(projected, ensure_ascii=False)
    for sentinel in doc["fixture_sentinels"]:
        assert sentinel not in text
    for rights_class in PRIVATE_ONLY_RIGHTS:
        assert rights_class not in text
    assert "myfxbook" not in text
    assert all(field["visibility"] in allowed for _, field in iter_fields(projected))
    assert all("missing_cause" not in field for _, field in iter_fields(projected))
    assert all(dossier["open_plans"] == [] for dossier in projected["asset_dossiers"])
    assert all(
        dossier.get("options_positioning") is None
        for dossier in projected["asset_dossiers"]
    )
    for record in projected["decision_records"]:
        assert (
            "demo" not in record
            and "provenance" not in record
            and "rationale" not in record
        )
    assert {dossier["asset_id"] for dossier in projected["asset_dossiers"]} == {
        "NVDA",
        "SPX",
        "USDJPY",
        "XAUUSD",
    }
    assert any(card["measures"] for card in projected["event_cards"])


def test_public_projection_keeps_official_numbers_with_their_precision() -> None:
    projected = project(_load(FIXTURE_PATH), ("public",))
    eci = next(
        card
        for card in projected["event_cards"]
        if card["event_id"] == "US_ECI_20261030"
    )
    twelve_month = next(
        m
        for m in eci["measures"]
        if m["measure_id"] == "eci_civilian_compensation_12m_nsa"
    )
    assert (twelve_month["prior"]["value"], twelve_month["actual"]["value"]) == (
        3.4,
        3.4,
    )
    assert twelve_month["change_vs_prior"]["value"] == 0.0
    assert all(m["actual"]["decimals"] == 1 for m in eci["measures"])
    assert (
        "expectation" not in twelve_month
        and "surprise_vs_expectation" not in twelve_month
    )


def test_projection_drops_a_field_that_cites_a_private_source() -> None:
    doc = _doc()
    note = _card(doc, "US_ECI_20261030")["post_release_note"]
    note["source_ids"].append("src:cc068:nfp-consensus")
    projected = project(doc, ("public",))
    card = next(
        card
        for card in projected["event_cards"]
        if card["event_id"] == "US_ECI_20261030"
    )
    assert "post_release_note" not in card
    assert all(
        source["source_id"] != "src:cc068:nfp-consensus"
        for source in projected["sources"]
    )


def test_text_check_catches_a_consensus_judgement_and_a_private_number() -> None:
    doc = _doc()
    _dossier(doc, "USDJPY")["headline_analysis"]["value"] = (
        "In line with consensus; short from 999.111."
    )
    problems = check_public_text(doc)
    assert any("private term" in p for p in problems) and any(
        "private number" in p for p in problems
    )


def test_reference_check_catches_an_unsorted_series_window() -> None:
    doc = _doc()
    doc["data_series"][0]["window"]["start"] = "2025-Q1"
    assert check_references(doc)


def _set(
    path: Callable[[dict[str, Any]], dict[str, Any]], **changes: Any
) -> Callable[[dict[str, Any]], None]:
    def mutate(doc: dict[str, Any]) -> None:
        path(doc).update(changes)

    return mutate


def _plan_entry(doc):
    return _dossier(doc, "USDJPY")["open_plans"][0]["entry"]


def _nfp_expectation(doc):
    return _card(doc, "US_NFP_20261106")["measures"][0]["expectation"]


def _eci_surprise(doc):
    return _card(doc, "US_ECI_20261030")["measures"][0]["surprise_vs_expectation"]


def _headline(doc):
    return _dossier(doc, "USDJPY")["headline_analysis"]


def _decision(doc):
    return doc["decision_records"][0]


PUBLIC_OWN = {"visibility": "public", "use_label": "PUBLIC_OWN_ANALYSIS_NOT_ADVICE"}
PUBLIC_OWN_RELABELLED = {**PUBLIC_OWN, "rights_class": "CC_OWN_ANALYSIS"}


def _delete(
    path: Callable[[dict[str, Any]], dict[str, Any]], key: str
) -> Callable[[dict[str, Any]], None]:
    def mutate(doc: dict[str, Any]) -> None:
        del path(doc)[key]

    return mutate


def _top(doc):
    return doc


MUTATIONS: dict[str, Callable[[dict[str, Any]], None]] = {
    "plan entry made public": _set(_plan_entry, **PUBLIC_OWN),
    "plan entry relabelled as own analysis": _set(_plan_entry, **PUBLIC_OWN_RELABELLED),
    "consensus made public": _set(_nfp_expectation, **PUBLIC_OWN),
    "consensus relabelled as official": _set(
        _nfp_expectation,
        visibility="public",
        use_label="PUBLIC_WITH_ATTRIBUTION",
        rights_class="BLS_OFFICIAL_PUBLIC_DERIVED",
        decimals=0,
    ),
    "surprise against consensus made pro": _set(
        _eci_surprise, visibility="pro", use_label="PRO_SUBSCRIBERS_ONLY"
    ),
    "GEX made public": _set(
        lambda d: _dossier(d, "SPX")["options_positioning"]["net_gex"], **PUBLIC_OWN
    ),
    "DEMO result made public": _set(
        lambda d: _decision(d)["demo"]["order_sent"], **PUBLIC_OWN
    ),
    "decision rationale relabelled public": _set(
        lambda d: _decision(d)["rationale"], **PUBLIC_OWN_RELABELLED
    ),
    "decision invalidation relabelled public": _set(
        lambda d: _decision(d)["invalidation"], **PUBLIC_OWN_RELABELLED
    ),
    "maintained analysis made public": _set(
        lambda d: _dossier(d, "USDJPY")["maintained_analysis"],
        visibility="public",
        use_label="PUBLIC_OWN_ANALYSIS_NOT_ADVICE",
    ),
    "scenario label made public": _set(
        lambda d: _dossier(d, "USDJPY")["scenarios"][0]["label"],
        visibility="public",
        use_label="PUBLIC_OWN_ANALYSIS_NOT_ADVICE",
    ),
    "branch condition relabelled public": _set(
        lambda d: _card(d, "US_ECI_20261030")["branches"][0]["condition"],
        **PUBLIC_OWN_RELABELLED,
    ),
    "object hidden in a public value": _set(
        _headline, value={"text": "x", "entry": 157.7}
    ),
    "list hidden in a public value": _set(_headline, value=[1, 2]),
    "measure label outside a Field": lambda d: _card(d, "US_ECI_20261030")["measures"][
        0
    ].update(label="Payrolls"),
    "metric period outside a Field": lambda d: _dossier(d, "NVDA")["fundamentals"][
        0
    ].update(period="FY2026"),
    "free-text id": lambda d: _card(d, "US_ECI_20261030")["measures"][0].update(
        measure_id="nfp vs consensus 40k"
    ),
    "broker chart": _set(
        lambda d: d["data_series"][1]["observations"],
        rights_class="BROKER_PROXY_DERIVED_INTERPRETATION",
    ),
    "own-analysis chart": _set(
        lambda d: d["data_series"][1]["observations"],
        rights_class="CC_OWN_ANALYSIS",
        use_label="PUBLIC_OWN_ANALYSIS_NOT_ADVICE",
    ),
    "chart without a source": _set(
        lambda d: d["data_series"][1]["observations"], source_ids=[]
    ),
    "chart period not a period": lambda d: d["data_series"][1]["observations"]["value"][
        0
    ].update(period="Aug 14"),
    "official number without decimals": _delete(
        lambda d: _card(d, "US_ECI_20261030")["measures"][0]["actual"], "decimals"
    ),
    "contract-pending class made public": _set(
        lambda d: d["calendar_entries"][-1]["name"],
        visibility="public",
        use_label="PUBLIC_WITH_ATTRIBUTION",
    ),
    "unknown key": lambda d: _dossier(d, "NVDA").update(price_target=1.0),
    "null value without a cause": _delete(
        lambda d: _dossier(d, "NVDA")["headline_analysis"], "missing_cause"
    ),
    "cause on a present value": _set(_headline, missing_cause="NOT_A_REAL_GAP"),
    "public official value without a source": _set(
        lambda d: _card(d, "US_ECI_20261030")["measures"][0]["actual"], source_ids=[]
    ),
    "sentinels on a real export": _set(_top, fixture=False),
    "fixture without sentinels": _delete(_top, "fixture_sentinels"),
    "local-time clock": _set(_top, generated_at_utc="2026-10-30T21:59:48+07:00"),
    "pro label on a public field": _set(_headline, use_label="PRO_SUBSCRIBERS_ONLY"),
    "private label on a public field": _set(_headline, use_label="INTERNAL_ONLY"),
    "another schema version": _set(_top, schema_version="1.1.0"),
}


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_schema_refuses(name: str) -> None:
    doc = _doc()
    MUTATIONS[name](doc)
    assert _errors(doc), name


def test_record_lists_are_the_schema_record_lists() -> None:
    schema = _load(SCHEMA_PATH)
    assert set(RECORD_LISTS) <= set(schema["required"])
