"""Owner-authorized shadow selection calibration policy.

``CONTENTOPS_CORE_V0_SHADOW_SELECTION_CALIBRATION_V1`` — ``SHADOW_ONLY``.

This module is the single authority for the numeric constants that order and defer
already-eligible CORE V0 candidates. Before it existed, those numbers lived as anonymous
module-local constants inside the portfolio window and runner modules, where nothing bound
them to an owner, a version, a scope, or a prohibition. An independent audit correctly read
that as invented selection authority.

What this policy is
-------------------

An *editorial product-selection calibration* authorized by the product owner for shadow
evaluation. It decides only the relative ordering of candidates that have already cleared
every governed hard gate, and the floor below which such a candidate defers.

What this policy is emphatically not
------------------------------------

It is not factual, analytical, market, economic, forecasting, or Capital Chronicle numeric
authority. No value here may be read as a claim about the world, and no score produced from
it may be published, quoted, or presented as an editorial judgement of newsworthiness to a
reader. The values are provisional: they were chosen to preserve already-tested shadow
behavior, not because they are calibrated against an outcome measure.

Live use is prohibited. ``authorized_for_live_publication`` is ``False`` and
``operating_mode_ceiling`` is ``SHADOW_ONLY``; promoting this policy to live publication or
public-write eligibility requires a later explicit owner decision, which means a new policy
version, not an edit to this one.

Changing a value here is a policy change, not a code change: issue a new ``policy_id`` and
``policy_version`` under fresh owner authority. Work Package E may recommend recalibration
from its sensitivity sweep, but it must not silently mutate these values — that is exactly
the anonymous-constant failure this module exists to prevent.
"""
from __future__ import annotations

import json
from hashlib import sha256
from typing import Any, Mapping

SCHEMA_VERSION = "contentops.core_v0_shadow_selection_calibration.v1"

POLICY_ID = "CONTENTOPS_CORE_V0_SHADOW_SELECTION_CALIBRATION_V1"
POLICY_VERSION = "v1"
POLICY_OWNER = "Jim (product owner)"
POLICY_AUTHORITY_DATE = "2026-08-06"
OPERATING_MODE_CEILING = "SHADOW_ONLY"

#: Calibration state recorded on every score derived from this policy. It names the
#: authority explicitly rather than describing the score as merely uncalibrated.
CALIBRATION_STATE = "OWNER_AUTHORIZED_PROVISIONAL_SHADOW_CALIBRATION_V1"


class ShadowCalibrationPolicyError(RuntimeError):
    """Fail-closed error for calibration policy misuse."""


def _logical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
            "utf-8"
        )
    ).hexdigest()


#: The exact owner-authorized provisional values. Each preserves the behavior already
#: exercised by the committed Work Package D tests; none is empirically calibrated.
_POLICY: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "policy_id": POLICY_ID,
    "policy_version": POLICY_VERSION,
    "owner": POLICY_OWNER,
    "authority_date": POLICY_AUTHORITY_DATE,
    "operating_mode_ceiling": OPERATING_MODE_CEILING,
    "policy_class": "EDITORIAL_PRODUCT_SELECTION_CALIBRATION",
    "calibration_state": CALIBRATION_STATE,
    "values": {
        "packet_authorized_claim_weight": 15.0,
        "packet_numeric_claim_weight": 10.0,
        "packet_score_cap": 100.0,
        "rolling_concentration_threshold": 0.34,
        "concentration_penalty_per_concentrated_value": 12.0,
        "portfolio_balance_floor": 0.0,
    },
    "intended_evaluation_scope": [
        "SHADOW_ONLY",
        "COMMITTED_CORE_V0_EVALUATION_CORPUS",
        "WORK_PACKAGE_D_ACCEPTANCE_TESTING",
        "WORK_PACKAGE_E_REPEATED_SHADOW_SOAK_AND_SENSITIVITY_EVALUATION",
    ],
    "limitations": [
        "NOT_FACTUAL_AUTHORITY",
        "NOT_ANALYTICAL_AUTHORITY",
        "NOT_MARKET_AUTHORITY",
        "NOT_ECONOMIC_AUTHORITY",
        "NOT_FORECASTING_AUTHORITY",
        "NOT_CAPITAL_CHRONICLE_NUMERIC_AUTHORITY",
        "PROVISIONAL_VALUES_CHOSEN_TO_PRESERVE_TESTED_SHADOW_BEHAVIOR",
        "NOT_EMPIRICALLY_CALIBRATED_AGAINST_AN_OUTCOME_MEASURE",
        "ORDERS_ONLY_CANDIDATES_THAT_ALREADY_CLEARED_EVERY_GOVERNED_HARD_GATE",
        "RECALIBRATION_REQUIRES_A_NEW_POLICY_VERSION_AND_EXPLICIT_OWNER_AUTHORITY",
    ],
    "authorized_for_live_publication": False,
    "authorized_for_public_write_eligibility": False,
    "live_use_prohibition": (
        "This calibration is authorized for shadow evaluation only. It must not decide "
        "live publication or public-write eligibility without a later explicit owner "
        "decision issued as a new policy version."
    ),
    "supersedes": "ANONYMOUS_MODULE_LOCAL_SELECTION_CONSTANTS",
}

_POLICY["policy_logical_hash"] = _logical_hash(_POLICY)

#: Frozen, hashed policy record. Read it through :func:`get_policy`.
SHADOW_SELECTION_CALIBRATION_POLICY: Mapping[str, Any] = _POLICY
POLICY_LOGICAL_HASH: str = _POLICY["policy_logical_hash"]


def get_policy() -> dict[str, Any]:
    """Return a deep copy of the policy so no caller can mutate shared authority."""
    return json.loads(json.dumps(SHADOW_SELECTION_CALIBRATION_POLICY))


def policy_value(name: str) -> float:
    """Return one authorized calibration value, failing closed on an unknown name."""
    values = SHADOW_SELECTION_CALIBRATION_POLICY["values"]
    if name not in values:
        raise ShadowCalibrationPolicyError(
            f"unauthorized_calibration_value:{name}:authorized={sorted(values)}"
        )
    return float(values[name])


def policy_binding() -> dict[str, Any]:
    """The identity every derived score, penalty, and disposition must carry.

    Binding the hash as well as the ID means a reader can prove which exact values produced
    a committed decision, and a later policy version cannot be mistaken for this one.
    """
    return {
        "calibration_policy_id": POLICY_ID,
        "calibration_policy_version": POLICY_VERSION,
        "calibration_policy_logical_hash": POLICY_LOGICAL_HASH,
        "calibration_policy_operating_mode_ceiling": OPERATING_MODE_CEILING,
        "calibration_policy_authorized_for_live_publication": False,
    }


def verify_policy_integrity() -> dict[str, Any]:
    """Recompute the policy hash and fail closed if the committed values drifted."""
    recomputed = _logical_hash(
        {k: v for k, v in SHADOW_SELECTION_CALIBRATION_POLICY.items() if k != "policy_logical_hash"}
    )
    if recomputed != POLICY_LOGICAL_HASH:
        raise ShadowCalibrationPolicyError(
            f"calibration_policy_hash_mismatch:expected={POLICY_LOGICAL_HASH}:got={recomputed}"
        )
    return {
        "policy_id": POLICY_ID,
        "policy_logical_hash": POLICY_LOGICAL_HASH,
        "integrity_verified": True,
    }
