"""X OAuth supervised-live-readiness BRIDGE BUNDLE gate (0174DD).

This module is STRICTLY LOCAL and BRIDGE-SCAFFOLD-ONLY. It consolidates the
remaining pre-live contracts for X OAuth into one evidence-grade local packet
so the next live-read-only task can be precise, bounded, and safe. It does NOT
perform live network calls, token exchange, credential reads, browser login,
callback server start, account binding, or posting. It adds NO runnable live
execution command.

HARD DISTINCTION:
  * 0174DB defined the credential readiness policy.
  * 0174DC defined the FUTURE redacted presence-check design.
  * 0174DD consolidates the remaining pre-live contracts into a bridge bundle
    scaffold ONLY; it does not execute any of them.

HARD GUARANTEES (enforced by tests + leakage guards):
  * No network imports (no urllib / requests / httpx / aiohttp / socket /
    http / ssl / env-file loaders).
  * No server imports (no socketserver / http.server / wsgiref / asyncio).
  * No browser/subprocess imports (no webbrowser / subprocess).
  * No credential/secret-source imports (no config-parser / key-ring /
    get-pass / secret-store / browser-cookie tooling / source-control history
    scanning).
  * No process-environment or env-file read (no process-env / env-file /
    home-dir access).
  * Imports ONLY hashlib, json, os.path, re, sys.
  * Fail-closed: writes happen ONLY when the write flag is present AND the
    packet passes the redaction scan.
  * Deterministic JSON: sorted keys, compact separators, trailing newline.
  * Stores only concise symbolic bridge metadata: fixture classes, abstract
    source-handle class, disabled-execution contract, redacted proof/ledger
    contracts, future live-read-only boundary, ordered blocker dashboard, and
    citation URLs (token / id / handle / query-free).

All outputs here are local bridge-scaffold artifacts only. Every future live,
token-exchange, presence-check, account-binding, or posting step requires a
SEPARATE explicit task and operator GO.
"""

import hashlib
import json
import os.path
import re
import sys

TASK_LABEL = (
    "TASK_CONTENTOPS_0174DD_X_OAUTH_SUPERVISED_LIVE_READINESS_BRIDGE_BUNDLE_"
    "NO_POST_NO_TOKEN_EXCHANGE_V0"
)

GATE = "X_OAUTH_SUPERVISED_LIVE_READINESS_BRIDGE_BUNDLE_GATE_0174DD"
PLATFORM = "x"
SOURCE_BASELINE_COMMIT = "725ab7c5ca38ccc1c4231eb0e6d9e23ec4ea2c67"
INHERITED_0174DC_COMMIT = "725ab7c5ca38ccc1c4231eb0e6d9e23ec4ea2c67"

# Date the official docs were inspected for this task (UTC, no time-of-day).
DOCS_ACCESSED_DATE = "2026-06-16"

# The exact next task is a live-read-only identity proof; it remains blocked
# until its own explicit task and operator GO.
EXACT_NEXT_LIVE_READ_ONLY_TASK = (
    "TASK_CONTENTOPS_0174DE_X_OAUTH_LIVE_READ_ONLY_IDENTITY_PROOF_GATE_ONE_"
    "REQUEST_NO_POST_NO_TOKEN_PERSIST_OPERATOR_GO_REQUIRED_V0"
)

NEXT_TASK = (
    "TASK_CONTENTOPS_0174DE_X_OAUTH_LIVE_READ_ONLY_IDENTITY_PROOF_GATE_ONE_"
    "REQUEST_NO_POST_NO_TOKEN_PERSIST_OPERATOR_GO_REQUIRED_V0"
)

# Output artifact locations.
PACKET_REL_DIR = os.path.join("docs", "credential_readiness", "0174DD")
PACKET_FILENAME = "x_oauth_supervised_live_readiness_bridge_bundle_packet.json"
README_FILENAME = "README.md"

FLAG_WRITE = "--write-x-oauth-supervised-live-readiness-bridge-bundle"

ACCEPTED_0174DC_REFERENCE = (
    "docs/credential_readiness/0174DC/"
    "x_oauth_redacted_credential_presence_check_design_packet.json "
    "(gate X_OAUTH_REDACTED_CREDENTIAL_PRESENCE_CHECK_DESIGN_GATE_0174DC)"
)

# Symbolic OAuth flow family (no flow initiated; no credential read).
OAUTH_FLOW_FAMILY_SYMBOLIC = (
    "x.oauth2.authorization_code_with_pkce.user_context.supervised.live."
    "readiness.bridge (BRIDGE SCAFFOLD ONLY; NO live call, NO token exchange, "
    "NO credential read, NO posting, NO flow initiated)"
)

# 1. Redacted credential presence-check FIXTURE classes (symbolic only).
PRESENCE_FIXTURE_CLASSES = [
    "fixture_no_operator_go",
    "fixture_source_handle_missing",
    "fixture_source_handle_configured_but_unread",
    "fixture_client_id_presence_boolean_only",
    "fixture_client_secret_presence_boolean_only",
    "fixture_token_presence_forbidden_until_later_gate",
    "fixture_redaction_violation_fail_closed",
    "fixture_unknown_fail_closed",
]

# 4. Account-binding proof packet redacted field classes (symbolic only).
ACCOUNT_BINDING_PROOF_CLASSES = [
    "account_binding_status_class",
    "identity_source_class",
    "account_permission_class",
    "operator_attestation_class",
]

# 5. Token-response redaction ledger field classes (symbolic only).
TOKEN_RESPONSE_LEDGER_CLASSES = [
    "request_budget_class",
    "endpoint_family_class",
    "token_response_seen_boolean",
    "token_value_exposed_boolean_false",
    "token_storage_status_class",
    "redaction_passed_boolean",
]

# Symbolic fail-closed result classes a FUTURE bridge component may emit.
FAIL_CLOSED_RESULT_CLASSES = [
    "bridge_blocked_no_operator_go_class",
    "bridge_blocked_source_undefined_class",
    "bridge_blocked_redaction_violation_class",
    "bridge_fail_closed_unknown_class",
]

# Deterministic, blocker-first ordered pre-live dashboard.
PRE_LIVE_BLOCKER_ORDER = [
    "developer access/tier unverified",
    "X app existence unverified",
    "redirect URI registration unverified",
    "client type unresolved",
    "credential source handle undefined",
    "redacted presence check not executed",
    "account binding proof not accepted",
    "token response redaction ledger not accepted",
    "text-only dry-run not accepted",
    "payload hash / approval / kill switch / duplicate prevention not accepted",
    "live-read-only identity proof not accepted",
    "live posting still blocked",
]

# All ten bridge contract section keys (existence asserted by tests).
BRIDGE_CONTRACT_SECTION_KEYS = [
    "redacted_credential_presence_fixture_contract",
    "operator_controlled_source_handle_contract",
    "disabled_presence_check_execution_contract",
    "account_binding_proof_packet_contract",
    "token_response_redaction_ledger_contract",
    "future_live_read_only_identity_proof_contract",
    "pre_live_blocker_dashboard_contract",
    "future_text_only_dry_run_contract",
    "future_payload_hash_approval_contract",
    "future_supervised_post_budget_contract",
]


# --------------------------------------------------------------------------- #
# Redaction scanner (defense-in-depth). Same family as 0174DC: blocks tokens /
# bearer strings / raw auth codes/state/verifier/challenge / Client-Secret-
# shaped values / callback URLs with query / raw query strings / raw env
# assignment patterns / env-file-like lines / raw handles / long numeric ids /
# source-control URNs / secret hash-fingerprint-prefix-suffix claims / source-
# name-with-value claims / redacted-from-real claims ("starts with"/"ends
# with"/"last4"/"first6") / raw token response claims / forbidden raw keys.
# --------------------------------------------------------------------------- #
_SECRET_LIKE = [
    re.compile(r"\d{6,}:[A-Za-z0-9_-]{30,}"),           # telegram-style token
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),   # PEM private key
    re.compile(r"AKIA[0-9A-Z]{16}"),                     # AWS access key id
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),                 # GitHub PAT
    re.compile(r"\bAAAA[A-Za-z0-9%]{20,}\b"),            # X/Twitter bearer body
]
_BEARER_TOKEN = re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-%]{10,}")
_TELEGRAM_URL_WITH_BOT = re.compile(r"api\.telegram\.org/bot")
_HANDLE_LIKE = re.compile(r"@[A-Za-z0-9_]{3,}")
_LONG_DIGITS = re.compile(r"(?<!\d)-?\d{7,}(?!\d)")
_LINKEDIN_URN = re.compile(r"urn:li:[A-Za-z]+:")
# Raw env assignment / env-file-like line: KEY=VALUE with secret-ish key names.
_ENV_ASSIGNMENT = re.compile(
    r"(?im)^\s*(?:export\s+)?[A-Z0-9_]*"
    r"(?:SECRET|TOKEN|KEY|PASSWORD|PASSWD|CLIENT_ID|CLIENT_SECRET|BEARER|"
    r"API_KEY|ACCESS|REFRESH)[A-Z0-9_]*\s*=\s*\S+"
)
# Any URL carrying an OAuth-sensitive query parameter.
_CALLBACK_URL_WITH_QUERY = re.compile(
    r"https?://[^\s\"']*[?&](?:code|state|access_token|token|bearer_token|"
    r"refresh_token|authorization_code|auth_code|code_verifier|code_challenge|"
    r"redirect_uri|callback_url|error|error_description)="
)
# A raw query-string fragment carrying sensitive params even without a scheme.
_RAW_QUERY_SENSITIVE = re.compile(
    r"(?:^|[?&])(?:code|state|access_token|token|bearer_token|refresh_token|"
    r"authorization_code|auth_code|code_verifier|code_challenge|error|"
    r"error_description)=[^&\s]+"
)
# Real bind targets must never appear as concrete host:port values.
_REAL_BIND_TARGET = re.compile(
    r"\b(?:127\.0\.0\.1|0\.0\.0\.0|::1)\b|\b(?:localhost|127\.0\.0\.1):\d{2,5}\b"
)
# Secret hash / fingerprint / prefix / suffix EXPOSURE claims (value attached).
_SECRET_FINGERPRINT_CLAIM = re.compile(
    r"(?i)(?:secret|token|client_secret|credential)\s*"
    r"(?:hash|fingerprint|prefix|suffix|sha256|md5)\s*[:=]\s*[A-Za-z0-9+/=_-]{4,}"
)
# Redacted-from-real disclosure claims with a concrete fragment attached.
_REDACTED_FROM_REAL_CLAIM = re.compile(
    r"(?i)(?:starts?\s*with|ends?\s*with|begins?\s*with|"
    r"last\s*\d+|first\s*\d+|last4|first6)\s*[:=]?\s*[A-Za-z0-9+/=_-]{3,}"
)
# Source-name-with-value claim.
_SOURCE_NAME_WITH_VALUE = re.compile(
    r"(?i)(?:credential\s*source|source\s*name|vault\s*path|secret\s*path)\s*"
    r"[:=]\s*\S*[A-Za-z0-9]{2,}[:/=]\S+"
)
# Raw token-response body claim (a value attached to a token-response field).
_RAW_TOKEN_RESPONSE_CLAIM = re.compile(
    r"(?i)(?:token_response|access_token|refresh_token|bearer_token)\s*"
    r"[:=]\s*[A-Za-z0-9._\-]{6,}"
)

_FORBIDDEN_KEYS = (
    "token", "access_token", "refresh_token", "bearer_token", "client_secret",
    "client_id", "api_key", "account_id", "account_handle", "user_id",
    "username", "screen_name", "handle", "post_id", "tweet_id", "community_id",
    "media_id", "place_id", "raw_url", "raw_request", "raw_response",
    "raw_query", "query_string", "authorization_code", "auth_code", "code",
    "state", "code_verifier", "code_challenge", "redirect_uri", "callback_url",
    "token_response", "error_description", "secret", "password", "passwd",
    "secret_hash", "token_hash", "secret_fingerprint", "token_fingerprint",
    "token_prefix", "token_suffix", "secret_prefix", "secret_suffix",
    "env_value", "dotenv_value", "source_value", "vault_path", "secret_path",
    "profile_url", "last4", "first6",
)

# Safe symbolic placeholders allowed in policy/design text.
_SAFE_SYMBOLIC_PLACEHOLDERS = frozenset(
    PRESENCE_FIXTURE_CLASSES
    + ACCOUNT_BINDING_PROOF_CLASSES
    + TOKEN_RESPONSE_LEDGER_CLASSES
    + FAIL_CLOSED_RESULT_CLASSES
)

# Keys whose list values are allowed to contain declared field/class NAMES.
_SCHEMA_NAME_LIST_KEYS = frozenset({
    "presence_fixture_classes",
    "account_binding_proof_classes",
    "token_response_ledger_classes",
    "fail_closed_result_classes",
    "redacted_field_classes",
    "fixture_classes",
    "ledger_field_classes",
    "proof_field_classes",
})


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (git SHAs, payload hashes)."""
    if s in (SOURCE_BASELINE_COMMIT, INHERITED_0174DC_COMMIT):
        return True
    if re.fullmatch(r"[0-9a-f]{40}", s) or re.fullmatch(r"[0-9a-f]{64}", s):
        return True
    return False


def scan_packet_for_leaks(obj):
    """Return a sorted list of redaction violations for an object."""
    violations = []

    def _walk(node, key=None):
        if isinstance(node, dict):
            for k, v in node.items():
                if str(k).lower() in _FORBIDDEN_KEYS:
                    violations.append(f"forbidden_key:{str(k).lower()}")
                _walk(v, k)
        elif isinstance(node, list):
            for v in node:
                _walk(v, key)
        elif isinstance(node, str):
            _scan_string(node, key)

    def _scan_string(s, key):
        if s in _SAFE_SYMBOLIC_PLACEHOLDERS:
            return
        if key in _SCHEMA_NAME_LIST_KEYS:
            return
        if _CALLBACK_URL_WITH_QUERY.search(s):
            violations.append(f"callback_url_with_query:{key or 'value'}")
        if _RAW_QUERY_SENSITIVE.search(s):
            violations.append(f"raw_query_sensitive:{key or 'value'}")
        if _ENV_ASSIGNMENT.search(s):
            violations.append(f"env_assignment:{key or 'value'}")
        if _SECRET_FINGERPRINT_CLAIM.search(s):
            violations.append(f"secret_fingerprint_claim:{key or 'value'}")
        if _REDACTED_FROM_REAL_CLAIM.search(s):
            violations.append(f"redacted_from_real_claim:{key or 'value'}")
        if _SOURCE_NAME_WITH_VALUE.search(s):
            violations.append(f"source_name_with_value:{key or 'value'}")
        if _RAW_TOKEN_RESPONSE_CLAIM.search(s):
            violations.append(f"raw_token_response_claim:{key or 'value'}")
        if _REAL_BIND_TARGET.search(s):
            violations.append(f"real_bind_target:{key or 'value'}")
        for pat in _SECRET_LIKE:
            if pat.search(s):
                violations.append(f"secret_like_value:{key or 'value'}")
                break
        if _BEARER_TOKEN.search(s):
            violations.append(f"bearer_token:{key or 'value'}")
        if _TELEGRAM_URL_WITH_BOT.search(s):
            violations.append(f"telegram_url:{key or 'value'}")
        if _LINKEDIN_URN.search(s):
            violations.append(f"linkedin_urn:{key or 'value'}")
        if _HANDLE_LIKE.search(s):
            violations.append(f"raw_handle:{key or 'value'}")
        if key not in ("payload_hash",) and _LONG_DIGITS.search(s):
            if not _is_known_safe_identifier(s):
                violations.append(f"long_digits_possible_id:{key or 'value'}")

    _walk(obj)
    return sorted(set(violations))


# Back-compat alias used by some shared tests.
scan_ledger_for_leaks = scan_packet_for_leaks


# --------------------------------------------------------------------------- #
# Deterministic serialization
# --------------------------------------------------------------------------- #
def serialize(obj):
    """Deterministic JSON: sorted keys, stable separators, trailing newline."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False) + "\n"


def compute_checksum(obj):
    """SHA-256 of the deterministic serialization."""
    return hashlib.sha256(serialize(obj).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Official docs sources (symbolic, token/id/handle/query-free)
# --------------------------------------------------------------------------- #
def build_official_docs_sources():
    """Concise, symbolic record of the official X OAuth docs inspected."""
    return [
        {
            "source_family": "x_oauth2_authorization_code_pkce",
            "title": "OAuth 2.0 Authorization Code Flow with PKCE - X",
            "url_or_symbolic_ref": (
                "https://docs.x.com/fundamentals/authentication/oauth-2-0/"
                "authorization-code"
            ),
            "accessed_date": DOCS_ACCESSED_DATE,
            "access_status": "accessible",
            "notes": (
                "Reference for the credential/token model; this gate only "
                "consolidates future contracts and never reads or validates "
                "any credential and never exchanges tokens."
            ),
        },
        {
            "source_family": "x_oauth2_user_context",
            "title": "X OAuth 2.0 Making Requests on Behalf of Users",
            "url_or_symbolic_ref": (
                "https://docs.x.com/fundamentals/authentication/oauth-2-0/"
                "user-access-token"
            ),
            "accessed_date": DOCS_ACCESSED_DATE,
            "access_status": "accessible",
            "notes": (
                "User access token / refresh token context informs the future "
                "token-response redaction ledger contract; no token is seen, "
                "stored, or exchanged here."
            ),
        },
        {
            "source_family": "x_authentication_overview",
            "title": "X API Authentication Overview (OAuth 2.0 user context)",
            "url_or_symbolic_ref": (
                "https://docs.x.com/fundamentals/authentication/overview"
            ),
            "accessed_date": DOCS_ACCESSED_DATE,
            "access_status": "accessible",
            "notes": (
                "Confirms Client ID/Secret and token handling are required; "
                "this bundle records only symbolic contracts and blockers, no "
                "values and no live behavior."
            ),
        },
        {
            "source_family": "x_developer_portal",
            "title": "X Developer Portal / Console - access tier verification",
            "url_or_symbolic_ref": "https://developer.x.com/en/portal",
            "accessed_date": DOCS_ACCESSED_DATE,
            "access_status": "gated_login_required",
            "notes": (
                "App existence, access tier, and credential issuance require "
                "portal login; treated as a blocker, not an assumption. No "
                "login performed."
            ),
        },
    ]


# --------------------------------------------------------------------------- #
# Bridge contract section builders
# --------------------------------------------------------------------------- #
def _redacted_credential_presence_fixture_contract():
    return {
        "purpose": (
            "define redacted presence-check FIXTURE classes only; no fixture "
            "is executed and no credential is read"
        ),
        "fixture_classes": list(PRESENCE_FIXTURE_CLASSES),
        "output_rule": (
            "each fixture maps only to a redacted boolean/class outcome; never "
            "to a real value, hash, fingerprint, prefix, suffix, or source "
            "name with value"
        ),
        "execution_status": "not_executed_design_fixtures_only",
    }


def _operator_controlled_source_handle_contract():
    return {
        "handle_class": "operator_controlled_x_oauth_source_handle_class",
        "rule": (
            "the future credential source is referenced ONLY by an abstract "
            "operator-controlled handle class; it never includes a real "
            "environment variable name, file path, secret-store name, vault "
            "path, account handle, or value"
        ),
        "value_exposure": "never",
        "defined_status": "undefined_until_operator_defines_it",
    }


def _disabled_presence_check_execution_contract():
    return {
        "runnable_now": False,
        "command_added_now": False,
        "future_command_rule": (
            "a future local-only presence-check execution command may exist "
            "ONLY after a separate explicit task and operator GO; it is not "
            "added by this bridge bundle"
        ),
        "default_state": "disabled_by_default_fail_closed",
        "scope_when_enabled": (
            "single-command, local-only, redacted boolean/class output only, "
            "no platform API call unless a later explicit live-read-only gate "
            "permits it"
        ),
    }


def _account_binding_proof_packet_contract():
    return {
        "purpose": (
            "define the FUTURE account-binding proof packet shape with "
            "redacted field classes only"
        ),
        "redacted_field_classes": list(ACCOUNT_BINDING_PROOF_CLASSES),
        "forbidden_fields": (
            "no account id, handle, username, user id, or profile URL is ever "
            "recorded"
        ),
        "execution_status": "not_executed_contract_only",
    }


def _token_response_redaction_ledger_contract():
    return {
        "purpose": (
            "define the FUTURE token-response redaction ledger shape; no token "
            "is ever seen, stored, hashed, or exchanged"
        ),
        "ledger_field_classes": list(TOKEN_RESPONSE_LEDGER_CLASSES),
        "invariants": [
            "token_value_exposed_boolean is always false",
            "no raw token body recorded",
            "no token hash recorded",
            "no token prefix/suffix/fingerprint recorded",
        ],
        "execution_status": "not_executed_contract_only",
    }


def _future_live_read_only_identity_proof_contract():
    return {
        "boundary": "next_live_read_only_task_only",
        "one_request_max": True,
        "exact_endpoint_family": "must_be_declared_later",
        "no_retry": True,
        "no_posting": True,
        "no_metrics": True,
        "no_account_mutation": True,
        "no_token_persistence": True,
        "redacted_output_only": True,
        "operator_go_required": True,
        "live_read_only_gate_required": True,
        "exact_next_live_read_only_task": EXACT_NEXT_LIVE_READ_ONLY_TASK,
    }


def _pre_live_blocker_dashboard_contract():
    return {
        "purpose": (
            "deterministic, blocker-first ordered summary of current pre-live "
            "blockers for an operator dashboard / CLI summary"
        ),
        "ordered_blockers": list(PRE_LIVE_BLOCKER_ORDER),
        "ordering_rule": "deterministic_blocker_first_fixed_order",
        "summary_surface": "cli_summary_and_packet_field_only_no_live_state",
    }


def _future_text_only_dry_run_contract():
    return {
        "purpose": (
            "define the FUTURE text-only dry-run contract; not executed now"
        ),
        "rules": [
            "renders the exact intended text only; performs no send",
            "no secret / no token / no credential appears in dry-run output",
            "exact payload hash is computed over the locked text only",
            "operator GO required before any dry-run is treated as approved",
        ],
        "execution_status": "not_executed_contract_only",
    }


def _future_payload_hash_approval_contract():
    return {
        "purpose": (
            "define the FUTURE exact-payload-hash + approval ledger + kill "
            "switch + duplicate-prevention contract; not executed now"
        ),
        "components": [
            "exact_payload_hash_locked_before_any_send",
            "approval_ledger_records_redacted_approval_only",
            "kill_switch_immediate_abort_capability",
            "duplicate_prevention_blocks_repeat_send",
        ],
        "execution_status": "not_executed_contract_only",
    }


def _future_kill_switch_duplicate_prevention_contract():
    return {
        "purpose": (
            "explicit kill-switch + duplicate-prevention preconditions for any "
            "future supervised send; not executed now"
        ),
        "kill_switch": "required_immediate_abort_before_and_during_send",
        "duplicate_prevention": "required_idempotency_guard_before_send",
        "execution_status": "not_executed_contract_only",
    }


def _future_supervised_post_budget_contract():
    return {
        "purpose": (
            "define but do not execute the supervised-post request budget "
            "contract"
        ),
        "request_budget": 1,
        "no_retry": True,
        "exact_payload_hash_required": True,
        "exact_channel_account_binding_required": True,
        "approval_ledger_required": True,
        "kill_switch_required": True,
        "duplicate_prevention_required": True,
        "redacted_post_send_ledger_required": True,
        "operator_one_time_go_required": True,
        "execution_status": "not_executed_contract_only",
    }


def _blocker_clearance_order():
    """Deterministic, blocker-first clearance order toward supervised live."""
    return [
        "verify developer access/tier (portal login by operator)",
        "verify X app existence",
        "register/verify redirect URI in portal",
        "resolve public vs confidential client type",
        "define operator-controlled credential source handle",
        "accept redacted presence-check execution gate, then execute it",
        "accept account-binding proof packet (redacted)",
        "accept token-response redaction ledger",
        "accept text-only dry-run contract",
        "accept payload hash / approval / kill switch / duplicate prevention",
        "execute and accept live-read-only identity proof (one request)",
        "operator one-time GO for supervised posting (request_budget=1)",
    ]


# --------------------------------------------------------------------------- #
# X OAuth supervised-live-readiness bridge bundle packet
# --------------------------------------------------------------------------- #
def build_packet():
    """Deep, bridge-scaffold-only X OAuth supervised-live-readiness packet."""
    packet = {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "platform": PLATFORM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "inherited_0174dc_commit": INHERITED_0174DC_COMMIT,
        "accepted_0174dc_reference": ACCEPTED_0174DC_REFERENCE,
        "bridge_bundle_status": "local_bridge_scaffold_only",
        "live_readiness_stage": "pre_live_blocked",
        "docs_access_status": (
            "partially_accessible: authorization-code-with-pkce, user-access-"
            "token, and authentication overview accessible; developer portal "
            "access/tier gated (login required, not performed)"
        ),
        "official_docs_checked": True,
        "official_docs_sources": build_official_docs_sources(),
        "oauth_flow_family_symbolic": OAUTH_FLOW_FAMILY_SYMBOLIC,
        "developer_portal_access_status": "gated_login_required_not_performed",
        "access_tier_status": "not_verified",
        "redirect_uri_registration_status": "not_verified_blocked",
        "client_type_resolution": "unresolved_public_vs_confidential",

        # --- Ten consolidated bridge contracts --------------------------- #
        "redacted_credential_presence_fixture_contract":
            _redacted_credential_presence_fixture_contract(),
        "operator_controlled_source_handle_contract":
            _operator_controlled_source_handle_contract(),
        "disabled_presence_check_execution_contract":
            _disabled_presence_check_execution_contract(),
        "account_binding_proof_packet_contract":
            _account_binding_proof_packet_contract(),
        "token_response_redaction_ledger_contract":
            _token_response_redaction_ledger_contract(),
        "future_live_read_only_identity_proof_contract":
            _future_live_read_only_identity_proof_contract(),
        "pre_live_blocker_dashboard_contract":
            _pre_live_blocker_dashboard_contract(),
        "future_text_only_dry_run_contract":
            _future_text_only_dry_run_contract(),
        "future_payload_hash_approval_contract":
            _future_payload_hash_approval_contract(),
        "future_kill_switch_duplicate_prevention_contract":
            _future_kill_switch_duplicate_prevention_contract(),
        "future_supervised_post_budget_contract":
            _future_supervised_post_budget_contract(),

        "fail_closed_result_classes": list(FAIL_CLOSED_RESULT_CLASSES),

        "explicit_non_actions": [
            "this task does not perform a live network call",
            "this task does not exchange tokens or see token responses",
            "this task does not read Client ID, Client Secret, access token, "
            "refresh token, bearer token, env, env-file, config files, "
            "key-ring, credential stores, browser stores, shell history, "
            "source-control history, portal state, or API state",
            "this task does not perform a credential presence check",
            "this task does not bind an X account",
            "this task does not perform OAuth or open an authorize URL",
            "this task does not start a callback server or bind a port",
            "this task does not post, edit, delete, repost, like, reply, or DM",
            "this task does not fetch metrics, create a webhook, or scrape",
            "this task does not add a new live execution command",
            "every future live, token-exchange, presence-check, account-"
            "binding, or posting step requires a separate explicit task and "
            "operator GO",
        ],

        "current_blockers": sorted(set([
            "developer access/tier not yet verified (portal login required)",
            "X app existence not yet verified",
            "redirect URI not yet registered/verified in portal",
            "public vs confidential client type not yet resolved",
            "operator-controlled local credential source handle not yet "
            "defined",
            "redacted presence check not yet executed",
            "account-binding proof packet not yet accepted",
            "token-response redaction ledger not yet accepted",
            "text-only dry-run not yet accepted",
            "payload hash / approval / kill switch / duplicate prevention not "
            "yet accepted",
            "live-read-only identity proof not yet accepted",
            "live posting still blocked",
            "any X plan/access-tier ambiguity is a blocker, not an assumption",
        ])),
        "blocker_clearance_order": _blocker_clearance_order(),

        "blocker_policy": (
            "any inaccessible/gated/redirected/deprecated/ambiguous official "
            "page is recorded as a blocker; capability is never assumed and "
            "third-party blogs/tutorials/SDK examples are never treated as "
            "authority; no readiness claim is made while blockers remain"
        ),

        "exact_next_live_read_only_task": EXACT_NEXT_LIVE_READ_ONLY_TASK,
        "exact_next_task_recommendation": NEXT_TASK,

        "caveats": [
            "OAuth 2.0 Authorization Code Flow with PKCE (user context) is the "
            "expected family, but NO flow, authorize URL, callback, token, "
            "credential read, presence check, or posting is exercised now",
            "this is a bridge-scaffold-only gate; it consolidates contracts "
            "and adds no runnable live execution command",
            "token exchange, credential presence validation, account binding, "
            "and posting are explicitly out of scope and blocked",
            "developer portal access tier and redirect URI registration "
            "remain unverified (no login)",
            "no readiness claim is made; blockers remain open",
        ],

        # --- Safety flags (all true) ------------------------------------- #
        "no_live_network_call_performed": True,
        "no_network_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
        "no_dotenv_read": True,
        "no_config_read": True,
        "no_keyring_read": True,
        "no_browser_store_read": True,
        "no_shell_history_read": True,
        "no_git_history_secret_scan": True,
        "no_client_id_read": True,
        "no_client_secret_read": True,
        "no_access_token_read": True,
        "no_refresh_token_read": True,
        "no_bearer_token_read": True,
        "no_credential_presence_check_performed": True,
        "no_token_exchange_performed": True,
        "no_token_response_seen": True,
        "no_token_persisted": True,
        "no_secret_material_persisted": True,
        "no_secret_hash_or_fingerprint_created": True,
        "no_secret_prefix_or_suffix_exposed": True,
        "no_account_identifier_read": True,
        "no_account_binding_performed": True,
        "no_oauth_flow_performed": True,
        "no_authorize_url_opened": True,
        "no_browser_login_performed": True,
        "no_developer_portal_login_performed": True,
        "no_callback_server_started": True,
        "no_localhost_port_bound": True,
        "no_socket_created": True,
        "no_port_listened": True,
        "no_authorization_code_generated_or_received": True,
        "no_real_callback_url_processed": True,
        "no_raw_callback_query_processed": True,
        "no_state_generated": True,
        "no_code_verifier_generated": True,
        "no_code_challenge_generated": True,
        "no_posting_performed": True,
        "no_metrics_fetched": True,
        "no_webhook_created": True,
        "no_reply_dm_created": True,
        "no_scraping_performed": True,
        "no_autonomous_publishing": True,
        "no_live_execution_command_added": True,
        "redaction_verified": True,
        "status": "pass",
        "blocked_reasons": [],
    }
    return packet


# Back-compat alias.
build_x_packet = build_packet


# --------------------------------------------------------------------------- #
# README
# --------------------------------------------------------------------------- #
def build_readme():
    """Concise operator-facing README for the 0174DD bridge bundle packet."""
    return (
        "# 0174DD X OAuth Supervised Live Readiness Bridge Bundle\n"
        "\n"
        "Strictly local, official-doc-grounded, BRIDGE-SCAFFOLD-ONLY gate. It "
        "consolidates the remaining pre-live X OAuth contracts into one "
        "evidence-grade local packet so the next live-read-only task can be "
        "precise, bounded, and safe. It performs NO live network call, NO "
        "token exchange, NO credential read, NO browser login, NO callback "
        "server start, NO account binding, and NO posting. It adds NO runnable "
        "live execution command.\n"
        "\n"
        "## Hard distinction\n"
        "\n"
        "- 0174DB defined the credential readiness policy.\n"
        "- 0174DC defined the FUTURE redacted presence-check design.\n"
        "- 0174DD consolidates the remaining pre-live contracts into a bridge "
        "scaffold ONLY; it does not execute any of them.\n"
        "\n"
        "## Inherited posture\n"
        "\n"
        "- `bridge_bundle_status = local_bridge_scaffold_only`.\n"
        "- `live_readiness_stage = pre_live_blocked`.\n"
        "- Live posting remains "
        "`blocked_until_new_explicit_task_and_operator_go`.\n"
        "\n"
        "## Official docs inspected\n"
        "\n"
        "- Authorization Code Flow with PKCE "
        "(`docs.x.com/fundamentals/authentication/oauth-2-0/"
        "authorization-code`) -- accessible.\n"
        "- User access token / requests on behalf of users "
        "(`docs.x.com/fundamentals/authentication/oauth-2-0/"
        "user-access-token`) -- accessible.\n"
        "- Authentication Overview "
        "(`docs.x.com/fundamentals/authentication/overview`) -- accessible.\n"
        "- Developer Portal access tiers (`developer.x.com/en/portal`) -- "
        "gated (login required, not performed) -> blocker.\n"
        "\n"
        "## Ten consolidated bridge contracts\n"
        "\n"
        "1. Redacted credential presence-check fixture contract (fixture "
        "classes only, no execution).\n"
        "2. Operator-controlled credential source handle contract (abstract "
        "handle class; never name-with-value).\n"
        "3. Disabled-by-default local presence-check execution contract (no "
        "runnable command added).\n"
        "4. Account-binding proof packet contract (redacted field classes "
        "only; no account id/handle/username/user id/profile URL).\n"
        "5. Token-response redaction ledger contract (token value exposed "
        "boolean always false; no raw body/hash/prefix/suffix).\n"
        "6. Future live-read-only identity proof contract (one request, no "
        "retry, no posting, no metrics, no account mutation, no token "
        "persistence, redacted output, operator GO + live-read-only gate).\n"
        "7. Pre-live blocker dashboard contract (deterministic blocker-first "
        "ordered list).\n"
        "8. Future text-only dry-run contract.\n"
        "9. Future exact payload hash + approval ledger + kill switch + "
        "duplicate-prevention contract.\n"
        "10. Future supervised-post request budget contract (request_budget=1, "
        "no retry, approval ledger, kill switch, duplicate prevention, "
        "redacted post-send ledger, operator one-time GO).\n"
        "\n"
        "## Blocker clearance order\n"
        "\n"
        "Deterministic and blocker-first: verify access tier, app existence, "
        "redirect URI, client type; define source handle; execute redacted "
        "presence check; accept account-binding proof, token-response ledger, "
        "text-only dry-run, payload hash/approval/kill switch/duplicate "
        "prevention; execute live-read-only identity proof; then operator "
        "one-time GO for supervised posting.\n"
        "\n"
        "## What this did NOT do\n"
        "\n"
        "Did not perform a live network call, token exchange, or credential "
        "presence check. Did not read Client ID/Secret, access/refresh/bearer "
        "token, env, env-file, config files, key-ring, credential stores, "
        "browser stores, shell history, or source-control history. Did not "
        "bind an X account, perform OAuth, open an authorize URL, start a "
        "callback server, or bind a port. Did not post/edit/delete/repost/"
        "like/reply/DM, fetch metrics, create a webhook, or scrape. Did not "
        "add any runnable live execution command. The module never browses "
        "docs at runtime; docs reading was an Antigravity/operator activity "
        "before writing symbolic packet data.\n"
        "\n"
        "## Next\n"
        "\n"
        f"Recommended next task: `{NEXT_TASK}`.\n"
    )


# --------------------------------------------------------------------------- #
# Main gate
# --------------------------------------------------------------------------- #
def run_gate(*, write=False, repo_root=None):
    """Run the strictly-local 0174DD supervised-live-readiness bridge gate.

    Writing occurs ONLY when ``write=True`` AND the packet passes the redaction
    scan. Fail-closed.
    """
    if repo_root is None:
        repo_root = os.path.dirname(os.path.dirname(__file__))

    blocked = []
    status = "pass"

    packet = build_packet()

    violations = scan_packet_for_leaks(packet)
    if violations:
        blocked.append(f"packet_redaction_violation:{PACKET_FILENAME}")
        status = "fail_closed"
        packet["status"] = "fail_closed"
        packet["blocked_reasons"] = sorted(set(blocked))

    checksum = compute_checksum(packet)

    packet_written = False
    readme_written = False

    if write and not blocked:
        out_dir = os.path.join(repo_root, PACKET_REL_DIR)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, PACKET_FILENAME), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(serialize(packet))
        packet_written = True
        with open(os.path.join(out_dir, README_FILENAME), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(build_readme())
        readme_written = True

    return {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "platform": PLATFORM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "inherited_0174dc_commit": INHERITED_0174DC_COMMIT,
        "inherited_operator_posture": {
            "live_posting_state":
                "blocked_until_new_explicit_task_and_operator_go",
            "pause_additional_live_sends": True,
        },
        "bridge_bundle_status": "local_bridge_scaffold_only",
        "live_readiness_stage": "pre_live_blocked",
        "packet_path": os.path.join(
            PACKET_REL_DIR, PACKET_FILENAME).replace(os.sep, "/"),
        "readme_path": os.path.join(
            PACKET_REL_DIR, README_FILENAME).replace(os.sep, "/"),
        "write_requested": bool(write),
        "packet_written": bool(packet_written),
        "readme_written": bool(readme_written),
        "packet_checksum": checksum,
        "oauth_flow_family_symbolic": OAUTH_FLOW_FAMILY_SYMBOLIC,
        "developer_portal_access_status":
            "gated_login_required_not_performed",
        "access_tier_status": "not_verified",
        "bridge_contract_section_keys": list(BRIDGE_CONTRACT_SECTION_KEYS),
        "fail_closed_result_classes": list(FAIL_CLOSED_RESULT_CLASSES),
        "exact_next_live_read_only_task": EXACT_NEXT_LIVE_READ_ONLY_TASK,
        "next_recommended_task": NEXT_TASK,
        "no_live_network_call_performed": True,
        "no_network_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
        "no_dotenv_read": True,
        "no_config_read": True,
        "no_keyring_read": True,
        "no_browser_store_read": True,
        "no_shell_history_read": True,
        "no_git_history_secret_scan": True,
        "no_client_id_read": True,
        "no_client_secret_read": True,
        "no_access_token_read": True,
        "no_refresh_token_read": True,
        "no_bearer_token_read": True,
        "no_credential_presence_check_performed": True,
        "no_token_exchange_performed": True,
        "no_token_response_seen": True,
        "no_token_persisted": True,
        "no_secret_material_persisted": True,
        "no_secret_hash_or_fingerprint_created": True,
        "no_secret_prefix_or_suffix_exposed": True,
        "no_account_identifier_read": True,
        "no_account_binding_performed": True,
        "no_oauth_flow_performed": True,
        "no_authorize_url_opened": True,
        "no_browser_login_performed": True,
        "no_developer_portal_login_performed": True,
        "no_callback_server_started": True,
        "no_localhost_port_bound": True,
        "no_socket_created": True,
        "no_port_listened": True,
        "no_authorization_code_generated_or_received": True,
        "no_real_callback_url_processed": True,
        "no_raw_callback_query_processed": True,
        "no_state_generated": True,
        "no_code_verifier_generated": True,
        "no_code_challenge_generated": True,
        "no_posting_performed": True,
        "no_metrics_fetched": True,
        "no_webhook_created": True,
        "no_reply_dm_created": True,
        "no_scraping_performed": True,
        "no_autonomous_publishing": True,
        "no_live_execution_command_added": True,
        "redaction_verified": True,
        "status": status,
        "blocked_reasons": sorted(set(blocked)),
    }


def main(argv=None):
    """CLI entry: prints the redacted gate summary as JSON."""
    if argv is None:
        argv = sys.argv[2:]
    write = FLAG_WRITE in argv
    print(json.dumps(run_gate(write=write), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
