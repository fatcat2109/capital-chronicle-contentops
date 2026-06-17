"""Telegram supervised-send OPERATOR COCKPIT HTML RENDER + MANUAL GATE HANDOFF.

Task 0174UZ/VA/VB. First operator cockpit RENDERING layer for the supervised
Telegram loop. Consumes the accepted 0174UW cockpit read-model packet and emits
a calm, institutional, evidence-grade STATIC HTML cockpit surface plus a
redacted manual-gate handoff contract.

AUTHORITY MODEL (per the master plan): the deterministic LOCAL gate is the
dispatch authority. This module is purely a RENDER layer over an already-reduced
read model. It performs NO dispatch, NO network, NO Telegram call, NO ``.env`` /
env / credential read, and emits NO live-ready / auto-send affordance. The HTML
contains no form action, no fetch, no XHR, no WebSocket, and no external
script/link/font/CDN. Optional embedded JS is limited to inert local UI niceties
(density toggle + clipboard copy of already-visible redacted text).

Importing this module performs NO writes and NO side effects. Artifacts are
written ONLY when ``write_artifacts(...)`` is called explicitly and the content
passes the reused fail-closed redaction + financial-advice scanners.
"""

import os.path

# Reuse the accepted read-model module (and through it the console/ledger/adapter
# scanners + deterministic serialization/checksum + redacted vocab).
from live_contentops import telegram_operator_cockpit_read_model as readmodel

TASK_LABEL = (
    "TASK_CONTENTOPS_0174UZ_VA_VB_TELEGRAM_OPERATOR_COCKPIT_HTML_RENDER_AND_"
    "MANUAL_GATE_HANDOFF_BATCH_V0"
)
MODEL = "TELEGRAM_OPERATOR_COCKPIT_HTML_RENDER_0174UZ_VA_VB"
MODEL_VERSION = "0174UZ_VA_VB_TELEGRAM_OPERATOR_COCKPIT_HTML_RENDER_V1"

RENDER_MODEL_SCHEMA = "contentops.telegram_operator_cockpit_render_model"
RENDER_MODEL_SCHEMA_VERSION = "0174UZ_VA_VB_OPERATOR_COCKPIT_RENDER_MODEL_V1"
HANDOFF_SCHEMA = "contentops.telegram_manual_gate_handoff_contract"
HANDOFF_SCHEMA_VERSION = "0174UZ_VA_VB_MANUAL_GATE_HANDOFF_CONTRACT_V1"
RENDER_PACKET_SCHEMA = "contentops.telegram_operator_cockpit_render_packet"
RENDER_PACKET_SCHEMA_VERSION = "0174UZ_VA_VB_OPERATOR_COCKPIT_RENDER_PACKET_V1"

SOURCE_BASELINE_COMMIT = "125e286ecc5f80a269ecee8011de5c889566d8af"

DOC_REL_DIR = os.path.join("docs", "automation", "0174UZ_VA_VB")
HTML_FILENAME = "telegram_operator_cockpit.html"
PACKET_FILENAME = "telegram_operator_cockpit_render_packet.json"
DOC_FILENAME = "telegram_operator_cockpit_render.md"

# Committed source read-model packet (read-only).
READ_MODEL_PACKET_REL = os.path.join(
    "docs", "automation", "0174UW_UX_UY",
    "telegram_operator_cockpit_read_model_packet.json")

NEXT_RECOMMENDED_TASK = (
    "TASK_CONTENTOPS_0174VC_VD_VE_TELEGRAM_MANUAL_GATE_PACKET_BUILDER_AND_"
    "OPERATOR_APPROVAL_CAPTURE_BATCH_V0"
)

PROVIDER_TELEGRAM = readmodel.PROVIDER_TELEGRAM

# Primary cockpit hero state (default = no candidate selected).
COMMAND_HERO_TITLE = "Telegram Supervised Send Operator Cockpit"
COMMAND_HERO_SUBTITLE = "local replay-guarded manual send loop"
COMMAND_HERO_PRIMARY_STATE = "NO CANDIDATE SELECTED — MANUAL GATE REQUIRED"

# Inert allowed CTA labels (NO dispatch; no "send"/"publish"/"post"/"retry"/
# "schedule" labels anywhere).
CTA_PREPARE = "Prepare manual gate packet"
CTA_OPEN_EVIDENCE = "Open evidence packet"
CTA_COPY_SUMMARY = "Copy precheck summary"
ALLOWED_CTAS = (CTA_PREPARE, CTA_OPEN_EVIDENCE, CTA_COPY_SUMMARY)

# Manual-gate handoff statuses (exact names mandated by the task).
HANDOFF_WAITING = "manual_gate_handoff_waiting_for_candidate"
HANDOFF_CLEAR_NOT_DISPATCH = "manual_gate_handoff_precheck_clear_not_dispatch"
HANDOFF_BLOCKED = "manual_gate_handoff_blocked"
HANDOFF_STATUSES = (HANDOFF_WAITING, HANDOFF_CLEAR_NOT_DISPATCH, HANDOFF_BLOCKED)

# Redacted handoff requirement codes.
HANDOFF_REQUIREMENTS = (
    "candidate_required",
    "fresh_operator_gate_required",
    "credential_boundary_required",
    "destination_binding_required",
    "approved_payload_checksum_required",
    "replay_guard_must_be_clear",
)


# --------------------------------------------------------------------------- #
# Scanning / serialization (reuse the accepted scanners)
# --------------------------------------------------------------------------- #
def scan_for_leaks(obj):
    """Return redaction violations for ``obj`` (delegates)."""
    return readmodel.scan_for_leaks(obj)


def scan_for_financial_advice(obj):
    """Return financial-advice violations for ``obj`` (delegates)."""
    return readmodel.scan_for_financial_advice(obj)


def serialize(obj):
    """Deterministic JSON (delegates)."""
    return readmodel.serialize(obj)


def compute_checksum(obj):
    """SHA-256 of the deterministic serialization (delegates)."""
    return readmodel.compute_checksum(obj)


def scan_render(html, packet, doc):
    """Return combined redaction + financial-advice violations for all outputs."""
    return (scan_for_leaks(html) + scan_for_leaks(packet) + scan_for_leaks(doc)
            + scan_for_financial_advice(html)
            + scan_for_financial_advice(packet)
            + scan_for_financial_advice(doc))


def _safety_flags():
    """Hard non-live invariants attached to every 0174UZ/VA/VB object."""
    return {
        "network_performed": False,
        "platform_api_called": False,
        "telegram_api_called": False,
        "credential_hydrated": False,
        "credential_read": False,
        "env_read": False,
        "dotenv_read": False,
        "sendmessage_executed": False,
        "dispatch_performed": False,
        "scheduler_enabled": False,
        "auto_retry_allowed": False,
        "autonomous_reply_performed": False,
        "webhook_or_polling_enabled": False,
        "live_ready": False,
        "auto_send_ready": False,
        "valid_for_live_execution": False,
        "is_local_only": True,
        "is_read_only_cockpit": True,
        "is_static_render": True,
        "stores_no_token": True,
        "stores_no_raw_destination": True,
        "stores_no_raw_chat_id": True,
        "stores_no_raw_response": True,
        "stores_no_raw_url": True,
        "stores_no_headers": True,
        "stores_no_cookies": True,
        "stores_no_username": True,
        "no_external_dependency": True,
        "no_financial_advice_emitted": True,
    }


# --------------------------------------------------------------------------- #
# 1. Render model
# --------------------------------------------------------------------------- #
def build_cockpit_render_model(read_model_packet):
    """Normalize the committed 0174UW packet into a deterministic render model.

    No network / env / credentials. Produces a stable ``render_model_checksum``.
    """
    pkt = read_model_packet or {}
    rail = pkt.get("operational_truth_rail") or {}
    replay = pkt.get("replay_guard_panel") or {}
    precheck = pkt.get("next_send_precheck_panel") or {}
    evidence = pkt.get("evidence_chain_panel") or {}
    forbidden = pkt.get("forbidden_affordance_panel") or {}
    readiness = ((pkt.get("operator_cockpit_read_model") or {})
                 .get("readiness_rails")) or {
        "fresh_gate_required": precheck.get("fresh_gate_required"),
        "ledger_guard_required": precheck.get("ledger_guard_required"),
        "operator_approval_required": precheck.get("operator_approval_required"),
        "payload_preview_required": precheck.get("payload_preview_required"),
        "destination_binding_required": precheck.get(
            "destination_binding_required"),
        "credential_boundary_required": precheck.get(
            "credential_boundary_required"),
    }

    model = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "render_model_schema": RENDER_MODEL_SCHEMA,
        "render_model_schema_version": RENDER_MODEL_SCHEMA_VERSION,
        "status": readmodel.console.adapter.Status.PASS,
        "provider": pkt.get("provider") or PROVIDER_TELEGRAM,
        "source_read_model_checksum": pkt.get("cockpit_read_model_checksum"),
        "source_cockpit_packet_checksum": pkt.get("cockpit_packet_checksum"),
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        # Section 1 - CommandHero.
        "command_hero": {
            "title": COMMAND_HERO_TITLE,
            "subtitle": COMMAND_HERO_SUBTITLE,
            "primary_state": COMMAND_HERO_PRIMARY_STATE,
            "next_allowed_action": pkt.get("next_allowed_action"),
        },
        # Section 2 - OperationalTruthRail.
        "operational_truth_rail": {
            "current_ledger_count": rail.get("current_ledger_count"),
            "last_send_sequence": rail.get("last_send_sequence"),
            "last_send_succeeded": bool(rail.get("last_send_succeeded")),
            "reconciliation_status": rail.get("reconciliation_status"),
            "reconciliation_label": (
                "RECONCILED"
                if rail.get("reconciliation_status") == readmodel.console.RECON_OK
                else "UNRECONCILED"),
            "current_ledger_manifest_checksum": rail.get(
                "current_ledger_manifest_checksum"),
        },
        # Section 3 - ReplayGuardPanel.
        "replay_guard_panel": {
            "exact_replay_example_outcome": replay.get(
                "exact_replay_example_outcome"),
            "same_payload_no_gate_outcome": replay.get(
                "same_payload_no_gate_outcome"),
            "same_payload_fresh_gate_outcome": replay.get(
                "same_payload_fresh_gate_outcome"),
            "new_payload_outcome": replay.get("new_payload_outcome"),
            "current_next_allowed_action": replay.get(
                "current_next_allowed_action"),
            "clear_meaning": (
                "precheck clear only, not dispatch"),
        },
        # Section 4 - NextSendPrecheckPanel.
        "next_send_precheck_panel": {
            "candidate_status": precheck.get("candidate_status"),
            "precheck_outcome_class": precheck.get("precheck_outcome_class"),
            "blockers": list(precheck.get("blockers") or []),
            "readiness_rails": {
                "fresh_gate_required": bool(
                    readiness.get("fresh_gate_required")),
                "ledger_guard_required": bool(
                    readiness.get("ledger_guard_required")),
                "operator_approval_required": bool(
                    readiness.get("operator_approval_required")),
                "payload_preview_required": bool(
                    readiness.get("payload_preview_required")),
                "destination_binding_required": bool(
                    readiness.get("destination_binding_required")),
                "credential_boundary_required": bool(
                    readiness.get("credential_boundary_required")),
            },
        },
        # Section 5 - EvidenceChainPanel.
        "evidence_chain_panel": {
            "accepted_send_proof_checksum": evidence.get(
                "accepted_send_proof_checksum"),
            "latest_ledger_proof_checksum": evidence.get(
                "latest_ledger_proof_checksum"),
            "replay_console_checksum": evidence.get("replay_console_checksum"),
            "last_request_checksum": evidence.get("last_request_checksum"),
            "last_response_checksum": evidence.get("last_response_checksum"),
            "cockpit_read_model_checksum": pkt.get(
                "cockpit_read_model_checksum"),
            "cockpit_packet_checksum": pkt.get("cockpit_packet_checksum"),
        },
        # Section 6 - ForbiddenAffordancePanel.
        "forbidden_affordance_panel": {
            "no_auto_send": bool(forbidden.get("no_auto_send", True)),
            "no_scheduler": bool(forbidden.get("no_scheduler", True)),
            "no_retry_loop": bool(forbidden.get("no_retry_loop", True)),
            "no_autonomous_reply": bool(
                forbidden.get("no_autonomous_reply", True)),
            "no_webhook_polling": bool(
                forbidden.get("no_webhook_polling", True)),
            "no_live_ready_claim": bool(
                forbidden.get("no_live_ready_claim", True)),
        },
        # Section 7 - ManualGateHandoffPanel.
        "manual_gate_handoff_panel": {
            "requirements": list(HANDOFF_REQUIREMENTS),
            "allowed_ctas": list(ALLOWED_CTAS),
        },
        **_safety_flags(),
    }
    model["render_model_checksum"] = compute_checksum(model)
    return model


# --------------------------------------------------------------------------- #
# 3. Manual gate handoff contract
# --------------------------------------------------------------------------- #
def build_manual_gate_handoff_contract(render_model):
    """Build the deterministic, local-only, redacted manual-gate handoff object.

    Status is derived from the render model's precheck outcome:
      - no candidate selected => waiting_for_candidate;
      - precheck clear        => precheck_clear_not_dispatch (still NOT dispatch);
      - anything else         => blocked.
    Contains NO credential/token/raw destination and NO live dispatch fields.
    """
    rm = render_model or {}
    precheck = rm.get("next_send_precheck_panel") or {}
    outcome = precheck.get("precheck_outcome_class")

    if outcome == readmodel.PRECHECK_BLOCKED_MISSING_CANDIDATE:
        status = HANDOFF_WAITING
    elif outcome == readmodel.PRECHECK_CLEAR:
        status = HANDOFF_CLEAR_NOT_DISPATCH
    else:
        status = HANDOFF_BLOCKED

    contract = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "handoff_schema": HANDOFF_SCHEMA,
        "handoff_schema_version": HANDOFF_SCHEMA_VERSION,
        "provider": rm.get("provider") or PROVIDER_TELEGRAM,
        "handoff_status": status,
        "handoff_statuses": list(HANDOFF_STATUSES),
        "source_precheck_outcome_class": outcome,
        # Requirements (redacted requirement codes, all required before a gate).
        "requirements": list(HANDOFF_REQUIREMENTS),
        "candidate_required": True,
        "fresh_operator_gate_required": True,
        "credential_boundary_required": True,
        "destination_binding_required": True,
        "approved_payload_checksum_required": True,
        "replay_guard_must_be_clear": True,
        "allowed_ctas": list(ALLOWED_CTAS),
        # Explicit non-dispatch invariants.
        "is_dispatch": False,
        "requires_separate_operator_send_gate": True,
        "classified_live_ready": False,
        "classified_auto_send_ready": False,
        **_safety_flags(),
    }
    contract["handoff_contract_checksum"] = compute_checksum(contract)
    return contract


# --------------------------------------------------------------------------- #
# 2. HTML render
# --------------------------------------------------------------------------- #
def _esc(value):
    """Minimal HTML-escape for text nodes / attribute values."""
    text = "" if value is None else str(value)
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _bool_chip(value):
    return "YES" if value else "NO"


def _kv_row(label, value, mono=True):
    cls = "v mono" if mono else "v"
    return ('<div class="row"><span class="k">%s</span>'
            '<span class="%s">%s</span></div>'
            % (_esc(label), cls, _esc(value)))


def _embedded_css():
    return (
        ":root{"
        "--bg:#0f1115;--surface:#16191f;--surface-2:#1b1f27;--line:#272c36;"
        "--ink:#e7e9ee;--ink-dim:#a4abb8;--ink-faint:#727a8a;"
        "--accent:#7c8aa5;--ok:#5fb08a;--warn:#c9a36b;--block:#c97b7b;"
        "--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace;"
        "--sans:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;"
        "--radius:10px;--pad:18px;}"
        "*{box-sizing:border-box;}"
        "html,body{margin:0;padding:0;}"
        "body{background:var(--bg);color:var(--ink);font-family:var(--sans);"
        "font-size:14px;line-height:1.5;letter-spacing:.1px;"
        "-webkit-font-smoothing:antialiased;}"
        ".wrap{max-width:1180px;margin:0 auto;padding:28px 22px 64px;}"
        ".mono{font-family:var(--mono);font-size:12.5px;}"
        ".hero{border:1px solid var(--line);background:"
        "linear-gradient(180deg,#191d25,#14171d);border-radius:var(--radius);"
        "padding:24px 24px 22px;margin-bottom:20px;}"
        ".hero h1{margin:0 0 4px;font-size:20px;font-weight:650;letter-spacing:.2px;}"
        ".hero .sub{color:var(--ink-dim);font-size:13px;margin-bottom:16px;}"
        ".primary-state{display:inline-block;border:1px solid var(--block);"
        "color:#f0d9d9;background:rgba(201,123,123,.08);border-radius:8px;"
        "padding:9px 13px;font-family:var(--mono);font-size:12.5px;font-weight:600;}"
        ".grid{display:grid;grid-template-columns:"
        "repeat(auto-fit,minmax(420px,1fr));gap:16px;}"
        ".panel{border:1px solid var(--line);background:var(--surface);"
        "border-radius:var(--radius);padding:var(--pad);}"
        ".panel h2{margin:0 0 12px;font-size:12px;font-weight:650;"
        "text-transform:uppercase;letter-spacing:1.4px;color:var(--ink-dim);}"
        ".panel .note{color:var(--ink-faint);font-size:12px;margin-top:10px;}"
        ".row{display:flex;justify-content:space-between;gap:14px;padding:6px 0;"
        "border-bottom:1px solid rgba(39,44,54,.55);}"
        ".row:last-child{border-bottom:0;}"
        ".k{color:var(--ink-dim);font-size:12.5px;}"
        ".v{color:var(--ink);text-align:right;word-break:break-all;}"
        ".v.mono{font-family:var(--mono);font-size:11.5px;color:#cfd5e0;}"
        ".tag{display:inline-block;border-radius:6px;padding:2px 8px;"
        "font-family:var(--mono);font-size:11px;font-weight:600;}"
        ".tag.ok{color:#d6f0e3;background:rgba(95,176,138,.13);"
        "border:1px solid var(--ok);}"
        ".tag.block{color:#f0d9d9;background:rgba(201,123,123,.12);"
        "border:1px solid var(--block);}"
        ".tag.warn{color:#f0e4cd;background:rgba(201,163,107,.12);"
        "border:1px solid var(--warn);}"
        ".span2{grid-column:1 / -1;}"
        ".forbidden .row .v{color:#d6f0e3;}"
        ".forbidden{border-color:#3a2c2c;background:"
        "linear-gradient(180deg,#1c1718,#16191f);}"
        ".rails{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));"
        "gap:6px 16px;margin-top:6px;}"
        ".cta-row{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px;}"
        ".cta{border:1px solid var(--line);background:var(--surface-2);"
        "color:var(--ink);border-radius:8px;padding:9px 14px;font:inherit;"
        "font-size:12.5px;cursor:default;}"
        ".cta[data-copy-target]{cursor:pointer;}"
        ".reqs{margin:8px 0 0;padding-left:18px;color:var(--ink-dim);"
        "font-family:var(--mono);font-size:12px;}"
        ".reqs li{padding:2px 0;}"
        ".meta{display:flex;justify-content:space-between;align-items:center;"
        "margin-bottom:14px;color:var(--ink-faint);font-size:11.5px;}"
        ".toolbar .cta{padding:5px 11px;font-size:11.5px;cursor:pointer;}"
        "body.is-compact{font-size:13px;}"
        "body.is-compact .panel{padding:12px;}"
        "body.is-compact .hero{padding:16px;}"
    )


def _embedded_js():
    # Inert local-only UI: density toggle + clipboard copy of already-visible
    # redacted text. NO network, NO dispatch, NO env, NO API.
    return (
        "(function(){\"use strict\";"
        "var tg=document.querySelector('[data-density-toggle]');"
        "if(tg){tg.addEventListener('click',function(){"
        "document.body.classList.toggle('is-compact');});}"
        "var btns=document.querySelectorAll('[data-copy-target]');"
        "Array.prototype.forEach.call(btns,function(b){"
        "b.addEventListener('click',function(){"
        "var el=document.getElementById(b.getAttribute('data-copy-target'));"
        "if(el&&navigator.clipboard){"
        "navigator.clipboard.writeText(el.innerText);}});});"
        "})();"
    )


def render_cockpit_html(render_model):
    """Render the complete static cockpit HTML document (embedded CSS/JS only)."""
    rm = render_model or {}
    hero = rm.get("command_hero") or {}
    rail = rm.get("operational_truth_rail") or {}
    replay = rm.get("replay_guard_panel") or {}
    precheck = rm.get("next_send_precheck_panel") or {}
    rails = precheck.get("readiness_rails") or {}
    evidence = rm.get("evidence_chain_panel") or {}
    forbidden = rm.get("forbidden_affordance_panel") or {}
    handoff = rm.get("manual_gate_handoff_panel") or {}

    blockers = precheck.get("blockers") or []
    blockers_html = "".join(
        '<li>%s</li>' % _esc(b) for b in blockers) or "<li>none</li>"

    rails_html = "".join(_kv_row(
        label.replace("_", " "), _bool_chip(rails.get(label)), mono=False)
        for label in (
            "fresh_gate_required", "ledger_guard_required",
            "operator_approval_required", "payload_preview_required",
            "destination_binding_required", "credential_boundary_required"))

    reqs_html = "".join('<li>%s</li>' % _esc(r)
                        for r in (handoff.get("requirements") or []))

    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="en" data-no-dispatch="true" '
                 'data-render-model="%s">'
                 % _esc(rm.get("render_model_checksum")))
    parts.append("<head>")
    parts.append('<meta charset="utf-8">')
    parts.append('<meta name="viewport" content="width=device-width,'
                 'initial-scale=1">')
    parts.append('<meta name="robots" content="noindex,nofollow">')
    parts.append("<title>Telegram Supervised Send Operator Cockpit</title>")
    parts.append("<style>%s</style>" % _embedded_css())
    parts.append("</head>")
    parts.append('<body data-no-dispatch="true">')
    parts.append('<main class="wrap" role="main">')

    # Meta toolbar (density toggle only; inert).
    parts.append('<div class="meta">'
                 '<span class="mono">%s</span>'
                 '<span class="toolbar">'
                 '<button type="button" class="cta" data-density-toggle '
                 'id="density-toggle">Toggle density</button></span></div>'
                 % _esc(rm.get("model_version")))

    # Section 1 - CommandHero.
    parts.append('<section class="hero" aria-label="CommandHero">')
    parts.append("<h1>%s</h1>" % _esc(hero.get("title")))
    parts.append('<div class="sub">%s</div>' % _esc(hero.get("subtitle")))
    parts.append('<div class="primary-state">%s</div>'
                 % _esc(hero.get("primary_state")))
    parts.append("</section>")

    parts.append('<div class="grid">')

    # Section 2 - OperationalTruthRail.
    parts.append('<section class="panel" aria-label="OperationalTruthRail">')
    parts.append("<h2>Operational Truth Rail</h2>")
    parts.append(_kv_row("current ledger count",
                         rail.get("current_ledger_count")))
    parts.append(_kv_row("last send sequence", rail.get("last_send_sequence")))
    parts.append('<div class="row"><span class="k">last send succeeded</span>'
                 '<span class="v"><span class="tag ok">%s</span></span></div>'
                 % _bool_chip(rail.get("last_send_succeeded")))
    parts.append('<div class="row"><span class="k">reconciliation status</span>'
                 '<span class="v"><span class="tag ok">%s</span></span></div>'
                 % _esc(rail.get("reconciliation_label")))
    parts.append(_kv_row("reconciliation class",
                         rail.get("reconciliation_status")))
    parts.append(_kv_row("current ledger manifest checksum",
                         rail.get("current_ledger_manifest_checksum")))
    parts.append('<div class="note">Current ledger truth is distinct from the '
                 'replay examples shown to the right; examples are illustrative '
                 'precheck outcomes, not ledger entries.</div>')
    parts.append("</section>")

    # Section 3 - ReplayGuardPanel.
    parts.append('<section class="panel" aria-label="ReplayGuardPanel">')
    parts.append("<h2>Replay Guard Panel</h2>")
    parts.append('<div class="row"><span class="k">exact replay</span>'
                 '<span class="v"><span class="tag block">%s</span></span></div>'
                 % _esc(replay.get("exact_replay_example_outcome")))
    parts.append('<div class="row"><span class="k">same payload, no gate</span>'
                 '<span class="v"><span class="tag warn">%s</span></span></div>'
                 % _esc(replay.get("same_payload_no_gate_outcome")))
    parts.append('<div class="row"><span class="k">same payload, fresh gate'
                 '</span><span class="v"><span class="tag ok">%s</span></span>'
                 '</div>'
                 % _esc(replay.get("same_payload_fresh_gate_outcome")))
    parts.append('<div class="row"><span class="k">new payload</span>'
                 '<span class="v"><span class="tag ok">%s</span></span></div>'
                 % _esc(replay.get("new_payload_outcome")))
    parts.append('<div class="note">"Clear" means %s. It is never a dispatch '
                 'authorization.</div>' % _esc(replay.get("clear_meaning")))
    parts.append("</section>")

    # Section 4 - NextSendPrecheckPanel.
    parts.append('<section class="panel" aria-label="NextSendPrecheckPanel">')
    parts.append("<h2>Next Send Precheck Panel</h2>")
    parts.append(_kv_row("candidate status", precheck.get("candidate_status")))
    parts.append(_kv_row("precheck outcome class",
                         precheck.get("precheck_outcome_class")))
    parts.append('<div class="row"><span class="k">blockers</span>'
                 '<span class="v mono"><ul class="reqs" '
                 'style="margin:0;padding-left:16px">%s</ul></span></div>'
                 % blockers_html)
    parts.append('<div class="note">Readiness rails (all required before any '
                 'manual gate):</div>')
    parts.append('<div class="rails">%s</div>' % rails_html)
    parts.append("</section>")

    # Section 5 - EvidenceChainPanel.
    parts.append('<section class="panel" aria-label="EvidenceChainPanel" '
                 'id="evidence-chain">')
    parts.append("<h2>Evidence Chain Panel</h2>")
    parts.append(_kv_row("accepted send proof checksum",
                         evidence.get("accepted_send_proof_checksum")))
    parts.append(_kv_row("latest ledger proof checksum",
                         evidence.get("latest_ledger_proof_checksum")))
    parts.append(_kv_row("replay console checksum",
                         evidence.get("replay_console_checksum")))
    parts.append(_kv_row("last request checksum",
                         evidence.get("last_request_checksum")))
    parts.append(_kv_row("last response checksum",
                         evidence.get("last_response_checksum")))
    parts.append(_kv_row("cockpit read model checksum",
                         evidence.get("cockpit_read_model_checksum")))
    parts.append(_kv_row("cockpit packet checksum",
                         evidence.get("cockpit_packet_checksum")))
    parts.append("</section>")

    # Section 6 - ForbiddenAffordancePanel (placed early so it is visible).
    parts.append('<section class="panel forbidden span2" '
                 'aria-label="ForbiddenAffordancePanel">')
    parts.append("<h2>Forbidden Affordance Panel</h2>")
    parts.append('<div class="grid">')
    for label in ("no_auto_send", "no_scheduler", "no_retry_loop",
                  "no_autonomous_reply", "no_webhook_polling",
                  "no_live_ready_claim"):
        parts.append('<div class="row"><span class="k">%s</span>'
                     '<span class="v"><span class="tag ok">%s</span></span>'
                     '</div>'
                     % (_esc(label.replace("_", " ")),
                        _bool_chip(forbidden.get(label))))
    parts.append("</div>")
    parts.append('<div class="note">This cockpit exposes no auto-send and makes '
                 'no live-ready claim.</div>')
    parts.append("</section>")

    # Section 7 - ManualGateHandoffPanel.
    parts.append('<section class="panel span2" '
                 'aria-label="ManualGateHandoffPanel" id="manual-gate-handoff">')
    parts.append("<h2>Manual Gate Handoff Panel</h2>")
    parts.append('<div class="note">Redacted handoff contract requirements '
                 '(all must hold before an operator opens a manual gate):</div>')
    parts.append('<ul class="reqs">%s</ul>' % reqs_html)
    parts.append('<div class="cta-row">')
    parts.append('<button type="button" class="cta">%s</button>'
                 % _esc(CTA_PREPARE))
    parts.append('<button type="button" class="cta" '
                 'data-copy-target="evidence-chain">%s</button>'
                 % _esc(CTA_OPEN_EVIDENCE))
    parts.append('<button type="button" class="cta" '
                 'data-copy-target="manual-gate-handoff">%s</button>'
                 % _esc(CTA_COPY_SUMMARY))
    parts.append("</div>")
    parts.append('<div class="note">These controls are inert: they only copy '
                 'already-visible redacted text locally. No control dispatches, '
                 'and a separate operator gate is still required.</div>')
    parts.append("</section>")

    parts.append("</div>")  # .grid
    parts.append("</main>")
    parts.append("<script>%s</script>" % _embedded_js())
    parts.append("</body>")
    parts.append("</html>")
    return "".join(parts)


# --------------------------------------------------------------------------- #
# 4. Render packet
# --------------------------------------------------------------------------- #
def build_render_packet(read_model_packet, render_model, handoff_contract):
    """Build the deterministic render packet linking all redacted checksums."""
    pkt = read_model_packet or {}
    rm = render_model or {}
    html = render_cockpit_html(rm)
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "render_packet_schema": RENDER_PACKET_SCHEMA,
        "render_packet_schema_version": RENDER_PACKET_SCHEMA_VERSION,
        "status": readmodel.console.adapter.Status.PASS,
        "provider": PROVIDER_TELEGRAM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "source_read_model_checksum": pkt.get("cockpit_read_model_checksum"),
        "source_cockpit_packet_checksum": pkt.get("cockpit_packet_checksum"),
        "render_model_checksum": rm.get("render_model_checksum"),
        "html_checksum": compute_checksum(html),
        "handoff_contract_checksum": (handoff_contract or {}).get(
            "handoff_contract_checksum"),
        "handoff_status": (handoff_contract or {}).get("handoff_status"),
        "next_allowed_action": (rm.get("command_hero") or {}).get(
            "next_allowed_action"),
        "reconciliation_outcome": (rm.get("operational_truth_rail") or {}).get(
            "reconciliation_status"),
        "current_ledger_count": (rm.get("operational_truth_rail") or {}).get(
            "current_ledger_count"),
        "cockpit_sections": [
            "CommandHero", "OperationalTruthRail", "ReplayGuardPanel",
            "NextSendPrecheckPanel", "EvidenceChainPanel",
            "ForbiddenAffordancePanel", "ManualGateHandoffPanel",
        ],
        "allowed_ctas": list(ALLOWED_CTAS),
        "handoff_statuses": list(HANDOFF_STATUSES),
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
        **_safety_flags(),
    }
    packet["render_packet_checksum"] = compute_checksum(packet)
    return packet


def build_render_doc(packet):
    """Render a deterministic, scanner-safe markdown render doc."""
    sections = packet.get("cockpit_sections") or []
    sections_md = "".join("- `%s`\n" % s for s in sections)
    ctas_md = "".join("- `%s`\n" % c for c in (packet.get("allowed_ctas") or []))
    return (
        "# 0174UZ/VA/VB Telegram Operator Cockpit HTML Render + Manual Gate "
        "Handoff\n\n"
        f"Task: `{packet['task_label']}`\n\n"
        f"Model: `{packet['model']}` version `{packet['model_version']}`\n\n"
        "## Purpose\n\n"
        "First operator cockpit rendering layer for the supervised Telegram "
        "loop. Renders the accepted 0174UW read model into a calm, "
        "institutional, evidence-grade STATIC HTML surface plus a redacted "
        "manual-gate handoff contract. No live dispatch, no network, no API, no "
        "env or credential read, and no external frontend dependency.\n\n"
        "## Cockpit sections\n\n"
        f"{sections_md}\n"
        "## Source / render references\n\n"
        f"- Source baseline commit: `{packet['source_baseline_commit']}`\n"
        f"- Source read model checksum: "
        f"`{packet['source_read_model_checksum']}`\n"
        f"- Source cockpit packet checksum: "
        f"`{packet['source_cockpit_packet_checksum']}`\n"
        f"- Render model checksum: `{packet['render_model_checksum']}`\n"
        f"- HTML checksum: `{packet['html_checksum']}`\n"
        f"- Handoff contract checksum: "
        f"`{packet['handoff_contract_checksum']}`\n"
        f"- Render packet checksum: `{packet['render_packet_checksum']}`\n\n"
        "## State summary\n\n"
        f"- Reconciliation: `{packet['reconciliation_outcome']}`\n"
        f"- Current ledger count: `{packet['current_ledger_count']}`\n"
        f"- Default next allowed action: `{packet['next_allowed_action']}`\n"
        f"- Handoff status: `{packet['handoff_status']}`\n\n"
        "## Manual gate handoff CTAs (inert)\n\n"
        f"{ctas_md}\n"
        "## Safety proofs\n\n"
        f"- Network performed: `{packet['network_performed']}`\n"
        f"- Telegram API called: `{packet['telegram_api_called']}`\n"
        f"- Credential read: `{packet['credential_read']}`\n"
        f"- sendMessage executed: `{packet['sendmessage_executed']}`\n"
        f"- Static render: `{packet['is_static_render']}`\n"
        f"- No external dependency: `{packet['no_external_dependency']}`\n"
        f"- Live ready: `{packet['live_ready']}`\n"
        f"- Valid for live execution: `{packet['valid_for_live_execution']}`\n\n"
        f"## Next recommended task\n\n`{packet['next_recommended_task']}`\n")


# --------------------------------------------------------------------------- #
# Packet loading + artifact writing
# --------------------------------------------------------------------------- #
def load_packet(packet_path):
    """Load a committed JSON packet, returning ``{}`` on missing/invalid file."""
    import json
    import pathlib
    path = pathlib.Path(packet_path)
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def build_all_from_repo(repo_root):
    """Load the committed read-model packet and build (render_model, handoff,
    packet, html, doc)."""
    import pathlib
    root = pathlib.Path(repo_root)
    read_model_packet = load_packet(root / READ_MODEL_PACKET_REL)
    render_model = build_cockpit_render_model(read_model_packet)
    handoff = build_manual_gate_handoff_contract(render_model)
    packet = build_render_packet(read_model_packet, render_model, handoff)
    html = render_cockpit_html(render_model)
    doc = build_render_doc(packet)
    return render_model, handoff, packet, html, doc


def write_artifacts(base_dir, html, packet, doc):
    """Write the cockpit HTML + packet + doc under ``base_dir`` ONLY if clean.

    Returns the list of written absolute paths. Raises ``RuntimeError`` if any
    scanner flags anything, so unsafe artifacts are never persisted. This is the
    ONLY function in this module that touches the filesystem.
    """
    import pathlib
    violations = scan_render(html, packet, doc)
    if violations:
        raise RuntimeError(
            "refusing to write cockpit render artifacts: scan found %d "
            "violation(s)" % len(violations))
    out_dir = pathlib.Path(base_dir) / DOC_REL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / HTML_FILENAME
    packet_path = out_dir / PACKET_FILENAME
    doc_path = out_dir / DOC_FILENAME
    html_path.write_text(html, encoding="utf-8", newline="\n")
    packet_path.write_text(serialize(packet), encoding="utf-8", newline="\n")
    doc_path.write_text(doc, encoding="utf-8", newline="\n")
    return [str(html_path), str(packet_path), str(doc_path)]
