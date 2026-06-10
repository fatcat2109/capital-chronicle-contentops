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

  }
