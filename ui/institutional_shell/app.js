/* Institutional Shell Prototype (0160) — static, local-only renderer. */
/* No network, no fetch, no XMLHttpRequest, no WebSocket, no EventSource. */
/* Reads window.CC_INSTITUTIONAL_SHELL_FIXTURE and renders local DOM only. */
(function () {
  "use strict";

  var F = window.CC_INSTITUTIONAL_SHELL_FIXTURE || {};
  var TONES = F.status_token_tones || {};

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) { n.className = cls; }
    if (text != null) { n.textContent = text; }
    return n;
  }

  function tokenTone(token) {
    return TONES[token] || "unknown";
  }

  /* Global safety ribbon */
  function renderRibbon() {
    var host = document.getElementById("safety-ribbon");
    if (!host) { return; }
    host.textContent = "";
    (F.global_safety_banners || []).forEach(function (b) {
      var span = el("span", "safety-banner", b.id.replace(/_/g, " "));
      span.setAttribute("data-tone", b.tone || "locked");
      host.appendChild(span);
    });
  }

  /* Top status bar */
  function statusItem(label, value, mod) {
    var wrap = el("div", "status-item");
    wrap.appendChild(el("span", "label", label));
    var v = el("span", "value" + (mod ? " " + mod : ""), value);
    wrap.appendChild(v);
    return wrap;
  }

  function renderStatusBar() {
    var host = document.getElementById("status-bar");
    if (!host) { return; }
    var g = F.global_state || {};
    host.textContent = "";
    host.appendChild(statusItem("System Mode", g.system_mode || "unknown"));
    host.appendChild(statusItem("Accepted HEAD", g.accepted_head_short || "unknown"));
    host.appendChild(statusItem("Kill Switch", (g.kill_switch_status || "unknown").toUpperCase(), "alert"));
    host.appendChild(statusItem("Current Gate", g.current_gate || "unknown"));
    host.appendChild(statusItem("Next Allowed Action", g.next_allowed_action || "unknown"));
    host.appendChild(statusItem("Evidence", String(g.evidence_count != null ? g.evidence_count : 0)));
    host.appendChild(statusItem("Active Blockers", String((g.active_blockers || []).length)));
    host.appendChild(statusItem("Live Posting", "DISABLED", "locked"));
    host.appendChild(statusItem("Platform API", "DISABLED", "locked"));
  }

  /* Left navigation */
  function renderNav(activeId) {
    var host = document.getElementById("left-nav");
    if (!host) { return; }
    host.textContent = "";
    (F.screens || []).forEach(function (s) {
      var btn = el("button", "nav-item" + (s.screen_id === activeId ? " active" : ""), s.title);
      btn.setAttribute("type", "button");
      btn.setAttribute("data-screen", s.screen_id);
      btn.addEventListener("click", function () { renderScreen(s.screen_id); });
      host.appendChild(btn);
    });
  }

  /* Helpers for building cards */
  function chipRow(tokens) {
    var row = el("div", "chip-row");
    (tokens || []).forEach(function (t) {
      var c = el("span", "chip", t.replace(/_/g, " "));
      c.setAttribute("data-tone", tokenTone(t));
      row.appendChild(c);
    });
    return row;
  }

  function bannerRow(banners) {
    var row = el("div", "banner-row");
    (banners || []).forEach(function (b) {
      var s = el("span", "safety-banner", b.replace(/_/g, " "));
      s.setAttribute("data-tone", tokenTone(b) === "unknown" ? "locked" : tokenTone(b));
      row.appendChild(s);
    });
    return row;
  }

  function listCard(title, items, mapper) {
    var card = el("div", "card");
    card.appendChild(el("h3", null, title));
    var ul = el("ul", "kv");
    (items || []).forEach(function (it) {
      ul.appendChild(mapper(it));
    });
    if (!items || !items.length) {
      ul.appendChild(el("li", null, "none"));
    }
    card.appendChild(ul);
    return card;
  }

  function blockedCard(reasons) {
    var card = el("div", "card");
    card.appendChild(el("h3", null, "Blocked Reason Stack"));
    var stack = el("div", "blocked-stack");
    (reasons || []).forEach(function (r) {
      stack.appendChild(el("div", "reason", r));
    });
    if (!reasons || !reasons.length) {
      stack.appendChild(el("div", "reason", "No active blocked reasons."));
    }
    card.appendChild(stack);
    return card;
  }

  function forbiddenCard(controls) {
    var card = el("div", "card");
    card.appendChild(el("h3", null, "Forbidden Controls (Read-Only Policy)"));
    (controls || []).forEach(function (c) {
      var btn = el("span", "disabled-control", c.replace(/_/g, " ") + " — disabled");
      btn.setAttribute("aria-disabled", "true");
      btn.setAttribute("title", "Forbidden action: disabled by safety policy.");
      card.appendChild(btn);
    });
    card.appendChild(el("div", "forbidden-note",
      "These appear only as disabled, read-only policy text. No live capability is wired."));
    return card;
  }

  function redactionCard(state) {
    var card = el("div", "card");
    card.appendChild(el("h3", null, "Credential Redaction Badge"));
    var badge = el("span", "redaction-badge", "SECRET REDACTED");
    card.appendChild(badge);
    card.appendChild(el("div", "note", "Redaction state: " + (state || "no_secrets") +
      ". No token, chat id, env path, request URL or raw response is shown."));
    return card;
  }


  /* Screenshot-safe watermark surface */
  function screenshotSafeBar() {
    var s = F.screenshot_safe_mode || {};
    var bar = el("div", "screenshot-safe");
    bar.appendChild(el("span", null, s.active_label || "SCREENSHOT-SAFE / LOCAL ONLY"));
    bar.setAttribute("data-screenshot-safe", "present");
    return bar;
  }

  /* Command Center hero band */
  function ccHero(d) {
    var h = d.hero_status_band || {};
    var band = el("div", "cc-hero");
    band.appendChild(el("div", "cc-hero-title", h.title || "Command Center"));
    var rows = [
      ["System mode", h.system_mode], ["Accepted HEAD", h.accepted_head],
      ["Kill switch", h.kill_switch], ["Public state", h.public_state],
      ["Live / API", h.live_api_state], ["Current gate", h.current_gate],
      ["Next allowed action", h.next_allowed_action]
    ];
    var wrap = el("div", "cc-hero-grid");
    rows.forEach(function (r) {
      var cell = el("div", "cc-hero-cell");
      cell.appendChild(el("span", "label", r[0]));
      cell.appendChild(el("span", "value", r[1] || "unknown"));
      wrap.appendChild(cell);
    });
    band.appendChild(wrap);
    return band;
  }

  function ccCardGrid(title, mapper, items, cls) {
    var section = el("div", "cc-section");
    section.appendChild(el("h2", "cc-section-title", title));
    var grid = el("div", cls || "card-grid");
    (items || []).forEach(function (it) { grid.appendChild(mapper(it)); });
    section.appendChild(grid);
    return section;
  }

  function ccKvSection(title, obj) {
    var section = el("div", "cc-section");
    section.appendChild(el("h2", "cc-section-title", title));
    var card = el("div", "card full");
    var ul = el("ul", "kv");
    Object.keys(obj || {}).forEach(function (k) {
      var li = el("li");
      li.appendChild(el("span", "k", k.replace(/_/g, " ") + ":"));
      li.appendChild(el("span", "v", String(obj[k])));
      ul.appendChild(li);
    });
    card.appendChild(ul);
    section.appendChild(card);
    return section;
  }

  function renderCommandCenter(main) {
    var d = F.command_center_detail || {};
    main.appendChild(screenshotSafeBar());
    main.appendChild(ccHero(d));
    main.appendChild(bannerRow((F.global_safety_banners || []).map(function (b) { return b.id; })));

    main.appendChild(ccCardGrid("Executive Status", function (c) {
      var card = el("div", "card");
      var head = el("h3", null, c.title);
      card.appendChild(head);
      var chip = el("span", "chip", String(c.state).replace(/_/g, " "));
      chip.setAttribute("data-tone", tokenTone(c.state));
      card.appendChild(chip);
      card.appendChild(el("div", "note", c.detail || ""));
      return card;
    }, d.executive_status_cards));

    main.appendChild(ccCardGrid("Gate Timeline", function (g) {
      var card = el("div", "card cc-gate");
      card.appendChild(el("h3", null, g.gate));
      var chip = el("span", "chip", String(g.state).replace(/_/g, " "));
      chip.setAttribute("data-tone", tokenTone(g.state));
      card.appendChild(chip);
      card.appendChild(el("div", "note", g.label || ""));
      return card;
    }, d.gate_timeline));

    var bam = el("div", "cc-section");
    bam.appendChild(el("h2", "cc-section-title", "Blocked Action Matrix"));
    var bcard = el("div", "card full");
    (d.blocked_action_matrix || []).forEach(function (b) {
      var item = el("span", "disabled-control", b.action.replace(/_/g, " ") + " — " + b.state);
      item.setAttribute("aria-disabled", "true");
      item.setAttribute("title", "Disabled by safety policy.");
      bcard.appendChild(item);
    });
    bcard.appendChild(el("div", "forbidden-note",
      "All actions above are disabled, read-only. No live capability is wired."));
    bam.appendChild(bcard);
    main.appendChild(bam);

    main.appendChild(ccKvSection("Evidence / Audit Summary", d.evidence_summary));
    main.appendChild(ccKvSection("Telegram Pilot Gate State (Read-Only)", d.telegram_gate_state));
    main.appendChild(ccKvSection("Publish Automation State", d.publish_automation_state));
    main.appendChild(ccKvSection("Content Studio State", d.content_studio_state));
    main.appendChild(ccKvSection("UI Rebuild State", d.ui_rebuild_state));
    main.appendChild(ccKvSection("Residual Drift (Untouched)", d.residual_drift_panel));
    main.appendChild(ccKvSection("Next Allowed Action", d.next_allowed_action_panel));
  }

  /* Content Studio hero band */
  function csHero(d) {
    var h = d.hero_status_band || {};
    var band = el("div", "cc-hero");
    band.appendChild(el("div", "cc-hero-title", h.title || "Content Studio"));
    var rows = [
      ["Content mode", h.content_mode], ["Public state", h.public_state],
      ["Generation state", h.generation_state], ["Current gate", h.current_gate],
      ["Next allowed action", h.next_allowed_action]
    ];
    var wrap = el("div", "cc-hero-grid");
    rows.forEach(function (r) {
      var cell = el("div", "cc-hero-cell");
      cell.appendChild(el("span", "label", r[0]));
      cell.appendChild(el("span", "value", r[1] || "unknown"));
      wrap.appendChild(cell);
    });
    band.appendChild(wrap);
    return band;
  }

  function csLaneCard(lane) {
    var toneMap = { allowed_review_only: "review", allowed_with_constraints: "proxy", blocked: "blocked" };
    var card = el("div", "card cs-lane");
    card.appendChild(el("h3", null, lane.title));
    var chip = el("span", "chip", String(lane.state).replace(/_/g, " "));
    chip.setAttribute("data-tone", toneMap[lane.state] || "unknown");
    card.appendChild(chip);
    card.appendChild(el("div", "note", lane.detail || ""));
    return card;
  }

  function renderContentStudio(main) {
    var d = F.content_studio_detail || {};
    main.appendChild(screenshotSafeBar());
    main.appendChild(csHero(d));
    main.appendChild(bannerRow(d.safety_banners));

    main.appendChild(ccCardGrid("Content Lane Control", csLaneCard, d.content_lanes));
    main.appendChild(ccKvSection("Lane Rules", d.lane_rules));
    main.appendChild(ccKvSection("Grounded News Rule", d.grounded_news_rule_panel));

    main.appendChild(ccCardGrid("Source / Evidence Requirements", function (s) {
      var card = el("div", "card");
      card.appendChild(el("h3", null, s.field));
      card.appendChild(el("div", "note", s.requirement || ""));
      return card;
    }, d.source_evidence_requirements));

    main.appendChild(ccKvSection("Draft Intake (Review-Only)", d.draft_review_only_panel));

    main.appendChild(ccCardGrid("Claim Risk Classifier", function (c) {
      var card = el("div", "card");
      card.appendChild(el("h3", null, c.class.replace(/_/g, " ")));
      var tone = c.handling === "allowed" ? "pass" :
        (c.handling === "blocked" || c.handling.indexOf("blocked") === 0) ? "blocked" : "review";
      var chip = el("span", "chip", c.handling.replace(/_/g, " "));
      chip.setAttribute("data-tone", tone);
      card.appendChild(chip);
      return card;
    }, d.claim_risk_classifier));

    var gr = el("div", "cc-section");
    gr.appendChild(el("h2", "cc-section-title", "Guardrail Results (Forbidden Categories)"));
    var gcard = el("div", "card full");
    (d.guardrail_results || []).forEach(function (g) {
      var item = el("span", "disabled-control", g.category.replace(/_/g, " ") + " — " + g.state);
      item.setAttribute("aria-disabled", "true");
      item.setAttribute("title", "Forbidden content category. Blocked by guardrails.");
      gcard.appendChild(item);
    });
    gr.appendChild(gcard);
    main.appendChild(gr);

    main.appendChild(ccKvSection("Limitations / Refusal Mode", d.limitations_refusal_mode));

    main.appendChild(ccCardGrid("Platform Fit Preview (Dry-Run, Read-Only)", function (p) {
      var card = el("div", "card");
      card.appendChild(el("h3", null, p.platform));
      card.appendChild(el("div", "note", p.fit + " (" + p.mode + ")"));
      return card;
    }, d.platform_fit_preview));

    main.appendChild(ccKvSection("Platform Fit Constraints", d.platform_fit_constraints));
    main.appendChild(ccKvSection("Editorial Quality State", d.editorial_quality_state));

    var bam = el("div", "cc-section");
    bam.appendChild(el("h2", "cc-section-title", "Blocked Action Matrix"));
    var bcard = el("div", "card full");
    (d.blocked_action_matrix || []).forEach(function (b) {
      var item = el("span", "disabled-control", b.action.replace(/_/g, " ") + " — " + b.state);
      item.setAttribute("aria-disabled", "true");
      item.setAttribute("title", "Disabled by safety policy.");
      bcard.appendChild(item);
    });
    bcard.appendChild(el("div", "forbidden-note",
      "All actions above are disabled, read-only. No live capability is wired."));
    bam.appendChild(bcard);
    main.appendChild(bam);

    main.appendChild(ccKvSection("Decision Ledger Handoff", d.decision_ledger_handoff));
    main.appendChild(ccKvSection("Draft Inspector Handoff", d.draft_inspector_handoff));
    main.appendChild(ccKvSection("Evidence / Audit Summary", d.evidence_summary));
    main.appendChild(ccKvSection("Next Allowed Action", d.next_allowed_action_panel));
  }

  function prtHero(d) {
    var h = d.hero_status_band || {};
    var band = el("div", "cc-hero");
    band.appendChild(el("div", "cc-hero-title", h.title || "Publish Readiness Tower"));
    var rows = [
      ["Publish mode", h.publish_mode], ["Public state", h.public_state],
      ["Live state", h.live_state], ["Platform API", h.platform_api_state],
      ["Scheduler", h.scheduler_state], ["Current gate", h.current_gate],
      ["Next allowed action", h.next_allowed_action]
    ];
    var wrap = el("div", "cc-hero-grid");
    rows.forEach(function (r) {
      var cell = el("div", "cc-hero-cell");
      cell.appendChild(el("span", "label", r[0]));
      cell.appendChild(el("span", "value", r[1] || "unknown"));
      wrap.appendChild(cell);
    });
    band.appendChild(wrap);
    return band;
  }

  function prtPlatformCard(p) {
    var card = el("div", "card");
    card.appendChild(el("h3", null, p.display_name));
    card.appendChild(el("div", "note", p.intended_use || ""));
    var chips = el("div", "chip-row");
    [["dry-run", "review"], ["live api: disabled", "blocked"],
     ["scheduling: disabled", "blocked"], ["not public-postable", "blocked"]].forEach(function (c) {
      var chip = el("span", "chip", c[0]);
      chip.setAttribute("data-tone", c[1]);
      chips.appendChild(chip);
    });
    card.appendChild(chips);
    card.appendChild(el("div", "note", "Credential: " + (p.credential_state || "") +
      " | Docs: " + (p.docs_verification || "")));
    card.appendChild(el("div", "note", "Next blocker: " + (p.next_blocker || "")));
    return card;
  }

  function prtDisabledSection(title, items, label) {
    var sec = el("div", "cc-section");
    sec.appendChild(el("h2", "cc-section-title", title));
    var card = el("div", "card full");
    (items || []).forEach(function (it) {
      var name = label(it);
      var item = el("span", "disabled-control", name);
      item.setAttribute("aria-disabled", "true");
      item.setAttribute("title", "Disabled by safety policy. No live capability is wired.");
      card.appendChild(item);
    });
    sec.appendChild(card);
    return sec;
  }

  function renderPublishReadinessTower(main) {
    var d = F.publish_readiness_tower_detail || {};
    main.appendChild(screenshotSafeBar());
    main.appendChild(prtHero(d));
    main.appendChild(bannerRow(d.safety_banners));

    main.appendChild(ccCardGrid("Platform Capability Registry (Dry-Run)",
      prtPlatformCard, d.platform_capability_registry_panel));

    main.appendChild(ccKvSection("Dry-Run Batch Manifest", d.dry_run_batch_manifest_panel));
    main.appendChild(ccKvSection("Manual Approval Gate", d.manual_approval_gate_panel));
    main.appendChild(ccKvSection("Kill Switch Gate", d.kill_switch_gate_panel));
    main.appendChild(ccKvSection("Credential & Secret State", d.credential_secret_state_panel));
    main.appendChild(ccKvSection("Redacted Audit Gate", d.redacted_audit_gate_panel));
    main.appendChild(ccKvSection("Official Docs Gate", d.official_docs_gate_panel));

    var tg = d.telegram_pilot_tower_panel || {};
    main.appendChild(ccCardGrid("Telegram Pilot Tower (Read-Only Sub-Gates)", function (g) {
      var card = el("div", "card");
      card.appendChild(el("h3", null, g.gate.replace(/_/g, " ")));
      var chip = el("span", "chip", String(g.state).replace(/_/g, " "));
      chip.setAttribute("data-tone", tokenTone(g.state));
      card.appendChild(chip);
      return card;
    }, tg.sub_gates));
    if (tg.next_step) {
      main.appendChild(el("p", "note", "Next step: " + tg.next_step));
    }

    main.appendChild(prtDisabledSection("Publish-Disabled Control Surface",
      d.publish_disabled_control_surface, function (c) {
        return c.control.replace(/_/g, " ") + " — " + c.state;
      }));

    main.appendChild(ccKvSection("Idempotency / Partial Failure", d.idempotency_partial_failure_panel));
    main.appendChild(ccKvSection("Future Live Handoff", d.future_live_handoff_panel));
    main.appendChild(ccKvSection("Evidence / Audit Summary", d.evidence_summary));
    main.appendChild(ccKvSection("Next Allowed Action", d.next_allowed_action_panel));
  }




  /* Main screen render */
  function renderScreen(screenId) {
    var screens = F.screens || [];
    var screen = null;
    for (var i = 0; i < screens.length; i++) {
      if (screens[i].screen_id === screenId) { screen = screens[i]; break; }
    }
    if (!screen) { screen = screens[0]; }
    renderNav(screen.screen_id);

    var main = document.getElementById("main");
    if (!main) { return; }
    main.textContent = "";

    if (screen.screen_id === "command_center" && F.command_center_detail) {
      renderCommandCenter(main);
      return;
    }

    if (screen.screen_id === "daily_content_studio" && F.content_studio_detail) {
      renderContentStudio(main);
      return;
    }

    if (screen.screen_id === "publish_readiness_tower" && F.publish_readiness_tower_detail) {
      renderPublishReadinessTower(main);
      return;
    }

    main.appendChild(screenshotSafeBar());
    main.appendChild(el("h1", "screen-title", screen.title));
    main.appendChild(el("p", "screen-purpose", screen.purpose || ""));
    main.appendChild(bannerRow(screen.required_banners));

    var grid = el("div", "card-grid");

    var tokenCard = el("div", "card");
    tokenCard.appendChild(el("h3", null, "Required Status Tokens"));
    tokenCard.appendChild(chipRow(screen.required_status_tokens));
    grid.appendChild(tokenCard);

    grid.appendChild(listCard("Primary Components", screen.primary_components, function (c) {
      var li = el("li");
      li.appendChild(el("span", "v", c));
      return li;
    }));

    grid.appendChild(listCard("Evidence References", screen.evidence_refs, function (e) {
      var li = el("li");
      var k = el("span", "k", "ref:");
      li.appendChild(k);
      li.appendChild(el("span", "v", e));
      return li;
    }));

    grid.appendChild(blockedCard(screen.blocked_reasons));
    grid.appendChild(redactionCard(screen.redaction_state));
    grid.appendChild(forbiddenCard(screen.forbidden_controls));

    var policyCard = el("div", "card");
    policyCard.appendChild(el("h3", null, "Policy & Behavior"));
    var ul = el("ul", "kv");
    var rows = [
      ["Blocked action policy", screen.blocked_action_policy || "n/a"],
      ["Redaction state", screen.redaction_state || "n/a"],
      ["Screenshot-safe behavior", screen.screenshot_safe_behavior || "n/a"]
    ];
    rows.forEach(function (r) {
      var li = el("li");
      li.appendChild(el("span", "k", r[0] + ":"));
      li.appendChild(el("span", "v", r[1]));
      ul.appendChild(li);
    });
    policyCard.appendChild(ul);
    grid.appendChild(policyCard);

    if (screen.gate_steps) {
      grid.appendChild(listCard("Telegram Gate Stepper (Read-Only)", screen.gate_steps, function (st) {
        var li = el("li");
        li.appendChild(el("span", "k", st.step + ":"));
        var c = el("span", "chip", st.state.replace(/_/g, " "));
        c.setAttribute("data-tone", tokenTone(st.state));
        li.appendChild(c);
        return li;
      }));
    }

    if (screen.allowed_item_states) {
      grid.appendChild(listCard("Allowed Calendar Item States", screen.allowed_item_states, function (s) {
        var li = el("li");
        li.appendChild(el("span", "v", s));
        return li;
      }));
    }

    if (screen.policy_flags) {
      grid.appendChild(listCard("Safety Policy Flags (Read-Only)", screen.policy_flags, function (p) {
        var li = el("li");
        li.appendChild(el("span", "k", p.name + ":"));
        li.appendChild(el("span", "v", String(p.state)));
        return li;
      }));
    }

    main.appendChild(grid);
  }

  /* Init */
  function init() {
    renderRibbon();
    renderStatusBar();
    var first = (F.screens && F.screens.length) ? F.screens[0].screen_id : "command_center";
    renderScreen("command_center" in indexById() ? "command_center" : first);
  }

  function indexById() {
    var map = {};
    (F.screens || []).forEach(function (s) { map[s.screen_id] = true; });
    return map;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
