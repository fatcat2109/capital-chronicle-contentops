/* Daily Content Studio static frontend v0.
 * Local-only, fixture-driven, review-only.
 * No network calls. No remote URLs. No CDN. No external scripts.
 * No credentials. No localStorage/sessionStorage. No live actions.
 *
 * The UI data contract fixture is embedded via fixture_data.js so the page
 * renders by simply opening index.html in a browser (file://) with no local
 * server required.
 */

/* Embedded copy of the accepted 0145 valid UI data contract fixture. */
const FIXTURE = window.__DCS_FIXTURE__ || null;

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

function kv(parent, key, value) {
  const row = el("div", "kv");
  row.appendChild(el("span", "key", key));
  const v = el("span", "val");
  if (typeof value === "boolean") {
    const b = el("span", value ? "badge ok" : "badge block", String(value));
    v.appendChild(b);
  } else {
    v.textContent = value === undefined || value === null ? "—" : String(value);
  }
  row.appendChild(v);
  parent.appendChild(row);
}

function renderSafetyHeader(data) {
  const host = document.getElementById("safety-header");
  host.innerHTML = "";
  (data.safety_banners || []).forEach((label) => {
    host.appendChild(el("span", "safety-banner", label));
  });
}

function renderDailyRun(data) {
  const body = document.querySelector("#daily-run-overview .panel-body");
  body.innerHTML = "";
  kv(body, "packet_id", data.packet_id);
  kv(body, "created_at", data.created_at);
  kv(body, "packet_status", data.packet_status);
  kv(body, "local_fixture_only", data.local_fixture_only);
  kv(body, "not_public_postable", data.not_public_postable);
  kv(body, "manual_review_required", data.manual_review_required);
}

function findSection(data, id) {
  return (data.screen_sections || []).find((s) => s.section_id === id) || {};
}

function renderSectionFlags(panelSel, sec) {
  const body = document.querySelector(panelSel + " .panel-body");
  body.innerHTML = "";
  kv(body, "review_only", sec.review_only);
  kv(body, "manual_review_required", sec.manual_review_required);
  kv(body, "not_public_postable", sec.not_public_postable);
  kv(body, "limitations_visible", sec.limitations_visible);
  kv(body, "source_references_visible", sec.source_references_visible);
  kv(body, "blocked_actions_visible", sec.blocked_actions_visible);

function renderManualActions(data) {
  const allowedHost = document.querySelector("#manual-actions-panel .allowed-actions");
  const forbiddenHost = document.querySelector("#manual-actions-panel .forbidden-actions");
  allowedHost.innerHTML = "";
  forbiddenHost.innerHTML = "";

  allowedHost.appendChild(el("h3", null, "Allowed manual-only actions"));
  (data.allowed_operator_actions || []).forEach((a) => {
    allowedHost.appendChild(el("span", "action-allowed", a));
  });

  forbiddenHost.appendChild(el("h3", null, "Forbidden actions (disabled / blocked)"));
  (data.forbidden_operator_actions || []).forEach((a) => {
    // Rendered as a non-interactive span, never a button.
    forbiddenHost.appendChild(el("span", "action-forbidden", a));
  });
}

function renderAuditStatus(data) {
  const body = document.querySelector("#audit-status-panel .panel-body");
  body.innerHTML = "";
  kv(body, "backend_server_required", data.backend_server_required);
  kv(body, "frontend_implementation_included", data.frontend_implementation_included);
  kv(body, "live_posting_enabled_now", data.live_posting_enabled_now);
  kv(body, "platform_api_allowed_now", data.platform_api_allowed_now);
  kv(body, "provider_llm_api_allowed_now", data.provider_llm_api_allowed_now);
  kv(body, "repo_web_search_allowed_now", data.repo_web_search_allowed_now);
  kv(body, "scraping_allowed_now", data.scraping_allowed_now);
  kv(body, "scheduler_allowed_now", data.scheduler_allowed_now);
  kv(body, "newsletter_or_cms_api_allowed_now", data.newsletter_or_cms_api_allowed_now);
  kv(body, "credential_read_allowed_now", data.credential_read_allowed_now);
  kv(body, "public_ready_allowed_now", data.public_ready_allowed_now);
  kv(body, "final_social_copy_generated", data.final_social_copy_generated);
}

function renderBlockers(data) {
  const body = document.querySelector("#blockers-and-limitations-panel .panel-body");
  body.innerHTML = "";
  const reasons = data.blocked_reasons || [];
  if (reasons.length === 0) {
    body.appendChild(el("p", "note", "No blockers recorded for this fixture. Limitations and source references must remain visible in every panel."));
  } else {
    const ul = el("ul");
    reasons.forEach((r) => ul.appendChild(el("li", null, r)));
    body.appendChild(ul);
  }
  kv(body, "manual_review_required", data.manual_review_required);
  kv(body, "not_public_postable", data.not_public_postable);
}

function renderHandoff(data) {
  const body = document.querySelector("#future-frontend-handoff-panel .panel-body");
  body.innerHTML = "";
  const h = data.future_frontend_handoff || {};
  kv(body, "data_contract_only", h.data_contract_only);
  kv(body, "static_ui_planned_later", h.static_ui_planned_later);
  kv(body, "frontend_implementation_included", h.frontend_implementation_included);
}

function render(data) {
  if (!data) {
    document.querySelector(".studio").appendChild(
      el("p", "note", "Fixture not loaded. This page is fixture-only and makes no network calls.")
    );
    return;
  }
  renderSafetyHeader(data);
  renderDailyRun(data);
  renderSectionFlags("#source-context-panel", findSection(data, "source_context_panel"));
  renderSectionFlags("#angle-cards-panel", findSection(data, "angle_cards_panel"));
  renderSectionFlags("#llm-prompt-handoff-panel", findSection(data, "llm_prompt_handoff_panel"));
  renderSectionFlags("#markdown-review-export-panel", findSection(data, "markdown_review_export_panel"));
  renderSectionFlags("#external-draft-review-panel", findSection(data, "external_draft_review_panel"));
  renderSectionFlags("#operator-decision-ledger-panel", findSection(data, "operator_decision_ledger_panel"));
  renderSectionFlags("#platform-fit-panel", findSection(data, "platform_fit_panel"));
  renderBlockers(data);
  renderManualActions(data);
  renderAuditStatus(data);
  renderHandoff(data);
}

document.addEventListener("DOMContentLoaded", function () {
  render(FIXTURE);
});

}
