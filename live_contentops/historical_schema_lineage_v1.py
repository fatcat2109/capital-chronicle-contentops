"""Frozen historical Wave 02 durable-store schema lineage authority.

Values in this module were extracted by executing each originating commit's exact
migration registry against an empty SQLite database and canonicalizing the resulting
sqlite_master/table_info surface. Historical checksums are evidence, never aliases for
current migration bytes.
"""
from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

ORIGINAL_NO_GENESIS_LINEAGE_ID = "wave02.e24a449.schema_v1.no_genesis"
HARDENED_NO_GENESIS_LINEAGE_ID = "wave02.3cc531a.schema_v2.no_genesis"
ENVELOPE_SYNTHETIC_GENESIS_LINEAGE_ID = "wave02.33225d5.schema_v3.envelope_genesis"
PRESERVATION_SYNTHETIC_GENESIS_LINEAGE_ID = "wave02.615a96f.schema_v3.preservation_genesis"
CANONICAL_PRE_V4_LINEAGE_ID = "wave02.03337e8.schema_v3.canonical_pre_v4"


def _lineage(**values: Any) -> Mapping[str, Any]:
    return MappingProxyType(values)


HISTORICAL_SCHEMA_LINEAGES: Mapping[str, Mapping[str, Any]] = MappingProxyType({
    ORIGINAL_NO_GENESIS_LINEAGE_ID: _lineage(
        lineage_id=ORIGINAL_NO_GENESIS_LINEAGE_ID,
        originating_commit="e24a4492e9d72f55c704168d637b7628e49140cd",
        migration_checksums=MappingProxyType({1: "f5134796b2551a6058e5df80ae0dfc362ce8fee45e7d6b24f1aecf7a0baa36a3"}),
        schema_fingerprint="2a17c52211008c6d91de89e40fd64412a7af67809997161c5df257a02e65fcd1",
        event_semantics="NO_GENESIS; first real transition has state_version=2; artifact_hash_set contains SHA-256 source evidence",
        artifact_semantics="artifact_key/storage_path/content_hash/byte_length; no story or work-item scope authority",
        supported_upgrade_path="DIRECT_HISTORICAL_COMPATIBILITY_TO_SCHEMA_V4_WITH_LEGACY_PROJECTION_BASELINE",
        fail_closed_reason="UNKNOWN_CHECKSUM_FINGERPRINT_PAIR_OR_AMBIGUOUS_EVENT_ORDER",
        first_real_event_state_version=2,
        valid_genesis_present=False,
    ),
    HARDENED_NO_GENESIS_LINEAGE_ID: _lineage(
        lineage_id=HARDENED_NO_GENESIS_LINEAGE_ID,
        originating_commit="3cc531a3d30848f54329d25913018882f6b71bcd",
        migration_checksums=MappingProxyType({1: "727ae6e4904a2577c385f390ee798942bfb88bdcb4a0ea5642de8e631a617a6d", 2: "036bcd8b7cd82208a4bd48653cb83ce25229bc67dbcaa6301ff9f8e6e1530488"}),
        schema_fingerprint="c7acf9884c85f8b847100f6ed9968b837478b16429c4c8510598df6a320c578d",
        event_semantics="NO_GENESIS; first real transition has event_seq=1 and state_version=2; deterministic source hash chain",
        artifact_semantics="story/work-item identity and exact byte hash available; pre-scope columns",
        supported_upgrade_path="DIRECT_HISTORICAL_COMPATIBILITY_TO_SCHEMA_V4_WITH_LEGACY_PROJECTION_BASELINE",
        fail_closed_reason="UNKNOWN_CHECKSUM_FINGERPRINT_PAIR_OR_AMBIGUOUS_EVENT_ORDER",
        first_real_event_state_version=2,
        valid_genesis_present=False,
    ),
    ENVELOPE_SYNTHETIC_GENESIS_LINEAGE_ID: _lineage(
        lineage_id=ENVELOPE_SYNTHETIC_GENESIS_LINEAGE_ID,
        originating_commit="33225d5e8d79ad229ad93d203e8d2e5018bb2738",
        migration_checksums=MappingProxyType({1: "727ae6e4904a2577c385f390ee798942bfb88bdcb4a0ea5642de8e631a617a6d", 2: "036bcd8b7cd82208a4bd48653cb83ce25229bc67dbcaa6301ff9f8e6e1530488", 3: "e61387fd0f7998ef747302feb0928481998986ba056c9b5155d1e24e10d65b99"}),
        schema_fingerprint="1a8efcaf522e7581b5a192295272328421bc5938e53a398de94c0ce259875314",
        event_semantics="Canonical envelope synthetic genesis; no event_kind column",
        artifact_semantics="story/work-item identity and exact byte hash available; pre-scope columns",
        supported_upgrade_path="CANONICAL_SCHEMA_V4_COMPATIBILITY_PRESERVING_SYNTHETIC_GENESIS",
        fail_closed_reason="UNKNOWN_CHECKSUM_FINGERPRINT_PAIR_OR_INVALID_GENESIS_CHAIN",
        first_real_event_state_version=1,
        valid_genesis_present=True,
    ),
    PRESERVATION_SYNTHETIC_GENESIS_LINEAGE_ID: _lineage(
        lineage_id=PRESERVATION_SYNTHETIC_GENESIS_LINEAGE_ID,
        originating_commit="615a96fb20aa97fd76bb3343e9150daec40d9031",
        migration_checksums=MappingProxyType({1: "727ae6e4904a2577c385f390ee798942bfb88bdcb4a0ea5642de8e631a617a6d", 2: "036bcd8b7cd82208a4bd48653cb83ce25229bc67dbcaa6301ff9f8e6e1530488", 3: "cd2deb6c6bc8b45ad588f24db89e3a3aa87d5488e5d51e8d46950bf3c91d127f"}),
        schema_fingerprint="125386a2f3755bdaf33d433360728fa4d28b9b930e7581d74cff9defb9269838",
        event_semantics="Canonical envelope synthetic genesis; preservation-hardened replay",
        artifact_semantics="story/work-item identity and exact byte hash available; pre-scope columns",
        supported_upgrade_path="CANONICAL_SCHEMA_V4_COMPATIBILITY_PRESERVING_SYNTHETIC_GENESIS",
        fail_closed_reason="UNKNOWN_CHECKSUM_FINGERPRINT_PAIR_OR_INVALID_GENESIS_CHAIN",
        first_real_event_state_version=1,
        valid_genesis_present=True,
    ),
    CANONICAL_PRE_V4_LINEAGE_ID: _lineage(
        lineage_id=CANONICAL_PRE_V4_LINEAGE_ID,
        originating_commit="03337e8f82478cf578866a5a1749d96acd687d3d",
        migration_checksums=MappingProxyType({1: "b2b33da379e42c5897e419620da81b7692e64ea91269bc72976b4a1b768cb32e", 2: "de754d123416e9ef172f0ff3607c898f167971a0566c34dbae4dfa18d6a5a589", 3: "fff8a2f889cc174e8e27ee878212940c889f91eedd8e33f4a9877fdde7940697"}),
        schema_fingerprint="bb2049a64310c16654d777aca242da03f8ee79af35d831c10c1776c7ebfa65fc",
        event_semantics="Canonical event_kind envelopes, append trigger, scoped artifact receipts",
        artifact_semantics="Explicit WORK_ITEM_EXACT/STORY_EXACT/GLOBAL_REUSABLE scopes",
        supported_upgrade_path="CANONICAL_SCHEMA_V4_METADATA_COMPATIBILITY",
        fail_closed_reason="UNKNOWN_CHECKSUM_FINGERPRINT_PAIR_OR_CANONICAL_INTEGRITY_FAILURE",
        first_real_event_state_version=1,
        valid_genesis_present=True,
    ),
})

HISTORICAL_CHECKSUM_LINEAGE_INDEX = MappingProxyType({tuple(sorted(lineage["migration_checksums"].items())): lineage_id for lineage_id, lineage in HISTORICAL_SCHEMA_LINEAGES.items()})
