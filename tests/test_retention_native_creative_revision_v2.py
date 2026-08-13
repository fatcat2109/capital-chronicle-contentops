from __future__ import annotations

import json

from live_contentops.retention_native_creative_revision_v2 import (
    SCHEMA_VERSION,
    apply_revision_packet,
    internal_source_label_ids,
    revision_validator,
)


def _component(shot_id: str, body: str) -> str:
    return (
        f"const Shot_{shot_id}: React.FC<AuthoredShotProps> = "
        "({sourceLabel}) => { return <AbsoluteFill>"
        f"{body}</AbsoluteFill>; }};"
    )


def test_revision_packet_applies_exact_component_and_policy() -> None:
    source = (
        _component("s04", "<div>{sourceLabel}</div>") + "\n\n"
        + _component("s08", "<div>{sourceLabel}</div>SUPPLY INVENTORIES DEMAND") + "\n\n"
        + "export const authoredShots = {};\n"
    )
    replacement = _component(
        "s08", "<div>SUPPLY</div><div>INVENTORIES</div><div>DEMAND</div>" + "x" * 500
    )
    packet = {
        "shot_replacements": [{
            "shot_id": "s08", "component_name": "Shot_s08",
            "component_source": replacement,
        }],
        "retain_internal_source_label_shot_ids": ["s04"],
    }
    revised = apply_revision_packet(source, packet)
    assert replacement in revised
    assert 'new Set<string>(["s04"])' in revised
    assert internal_source_label_ids(source) == ("s04", "s08")


def test_revision_validator_rejects_internal_source_render() -> None:
    component = _component(
        "s08", "<div>SUPPLY</div><div>INVENTORIES</div><div>DEMAND</div>" + "x" * 500
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "shot_replacements": [{
            "shot_id": "s08", "component_name": "Shot_s08",
            "component_source": component,
        }],
        "suppress_internal_source_label_shot_ids": ["s08"],
        "retain_internal_source_label_shot_ids": ["s04"],
        "revision_rationale": "Separate the three concepts into stable zones.",
        "public_write": False,
        "publication_authority": False,
        "factual_authority": False,
    }
    ok, *_ = revision_validator(suppress_ids=("s08",), retain_ids=("s04",))(
        json.dumps(payload)
    )
    assert ok is True
    payload["shot_replacements"][0]["component_source"] = component.replace(
        "</AbsoluteFill>", "{sourceLabel}</AbsoluteFill>"
    )
    ok, *_ = revision_validator(suppress_ids=("s08",), retain_ids=("s04",))(
        json.dumps(payload)
    )
    assert ok is False
