"""Local advisory platform official-docs verification pack (Task 0081).

This module ONLY validates operator-supplied verification records/packs. It does
NOT fetch official docs, call any network/platform/provider API, read
credentials, post, schedule, scrape, reply, or DM. The pack is advisory only and
never grants runtime authority: `docs_runtime_authority` must stay false and
`live_posting_enabled` must stay false. Where official-doc evidence is absent,
fields stay UNKNOWN / NOT_VERIFIED rather than being invented.
"""

import json
import os

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")
RECORD_SCHEMA_PATH = os.path.join(
    SCHEMA_DIR, "platform_official_docs_verification_record.schema.json"
)
PACK_SCHEMA_PATH = os.path.join(
    SCHEMA_DIR, "platform_official_docs_verification_pack.schema.json"
)

# Canonical platform set this pack covers (order preserved).
PLATFORMS = ["x", "linkedin", "telegram", "facebook_page", "instagram", "tiktok"]


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_record_schema():
    return _load(RECORD_SCHEMA_PATH)


def load_pack_schema():
    return _load(PACK_SCHEMA_PATH)


# ---------------------------------------------------------------------------
# Record validation
# ---------------------------------------------------------------------------

def validate_record(record):
    """Validate a single platform verification record. Fail closed on any
    attempt to grant runtime authority or imply network/credential/live access.
    """
    errors = []
    if not isinstance(record, dict):
        return {"valid": False, "errors": ["record_not_object"]}

    pid = record.get("platform_id")
    if not pid:
        errors.append("missing:platform_id")

    status = record.get("verification_status")
    if status not in (
        "not_verified", "partially_verified",
        "verified_from_operator_supplied_docs",
    ):
        errors.append("invalid:verification_status")

    # Authority / safety invariants must never flip.
    if record.get("docs_runtime_authority") is not False:
        errors.append("docs_runtime_authority_must_be_false")
    if record.get("network_accessed_by_repo") is not False:
        errors.append("network_accessed_by_repo_must_be_false")
    if record.get("credential_accessed_by_repo") is not False:
        errors.append("credential_accessed_by_repo_must_be_false")
    if record.get("live_posting_enabled") is not False:
        errors.append("live_posting_enabled_must_be_false")

    # Unknowns are required unless fully verified.
    if status in ("not_verified", "partially_verified"):
        if not record.get("unknowns"):
            errors.append("unknowns_required_when_not_fully_verified")

    # Verified status requires source documents.
    if status == "verified_from_operator_supplied_docs":
        if not record.get("source_documents"):
            errors.append("source_documents_required_when_verified")

    return {"valid": not errors, "errors": errors}


# ---------------------------------------------------------------------------
# Pack validation
# ---------------------------------------------------------------------------

def validate_pack(pack):
    """Validate a verification pack and every record it contains."""
    errors = []
    if not isinstance(pack, dict):
        return {"valid": False, "errors": ["pack_not_object"]}

    for field in ("pack_id", "generated_at_utc", "scope"):
        if not pack.get(field):
            errors.append("missing:%s" % field)

    if pack.get("no_runtime_capability_added") is not True:
        errors.append("no_runtime_capability_added_must_be_true")

    platforms = pack.get("platforms")
    if not isinstance(platforms, list) or not platforms:
        errors.append("missing:platforms")
        platforms = []

    seen = []
    for rec in platforms:
        res = validate_record(rec)
        if not res["valid"]:
            errors.extend(
                "platform[%s]:%s" % (rec.get("platform_id", "?"), e)
                for e in res["errors"]
            )
        seen.append(rec.get("platform_id"))

    return {"valid": not errors, "errors": errors, "platform_ids": seen}


def validate_pack_file(path):
    return validate_pack(_load(path))

