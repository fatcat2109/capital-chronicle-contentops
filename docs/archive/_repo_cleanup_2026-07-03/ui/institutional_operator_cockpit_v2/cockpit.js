/*
 * Capital Chronicle ContentOps — Operator Cockpit V2 renderer.
 *
 * Local static only. No runtime network of any kind: no remote requests,
 * sockets, or event streams; no remote dependency. Renders entirely from the local
 * canonical view model (window.CC_COCKPIT_V2_VIEW_MODEL).
 *
 * Single source of truth: every header/screen reads global_state from the
 * view model. No component hardcodes current baseline / gate / kill switch /
 * public state independently.
 */
(function () {
  "use strict";

  var VM = window.CC_COCKPIT_V2_VIEW_MODEL || {};
  var GS = VM.global_state || {};

  // --- small DOM helpers (no innerHTML for dynamic text; safe text nodes) ---
  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  function field(parent, labelText, valueText, valueClass) {
    var wrap = el("div", "hdr-field");
    wrap.appendChild(el("span", "hdr-label", labelText));
    wrap.appendChild(el("span", "hdr-value " + (valueClass || ""), valueText));
    parent.appendChild(wrap);
    return wrap;
  }

  function divider(parent) {
    parent.appendChild(el("div", "hdr-divider"));
  }

  function kv(labelText, valueText, valueClass) {
    var wrap = el("div");
    wrap.appendChild(el("div", "kv-label", labelText));
    wrap.appendChild(el("div", "kv-value " + (valueClass || ""), valueText));
    return wrap;
  }

  function severityClass(sev) {
    switch (sev) {
      case "ok": return "sev-ok";
      case "review": return "sev-review";
      case "block": return "sev-block";
      default: return "sev-info";
    }
  }

  // --- top safety ribbon ---
  function renderRibbon() {
    var host = document.getElementById("safety-ribbon");
    if (!host) return;
    host.textContent = "";
    host.appendChild(el("span", "ribbon-brand", VM.meta ? VM.meta.product_name : "ContentOps"));
    (VM.safety_ribbon || []).forEach(function (chip) {
      host.appendChild(el("span", "ribbon-chip " + severityClass(chip.severity), chip.label));
    });
  }

  // --- system header (canonical current truth) ---
  function renderHeader() {
    var host = document.getElementById("system-header");
    if (!host) return;
    host.textContent = "";
    field(host, "System Mode", GS.current_mode, "mono-strong");
    divider(host);
    field(host, "Current Repo Baseline", GS.current_repo_baseline, "mono-strong");
    divider(host);
    field(host, "Last Product Code Baseline", GS.last_product_code_baseline);
    divider(host);
    field(host, "Kill Switch", String(GS.kill_switch).toUpperCase(), "is-block");
    divider(host);
    field(host, "Public State", GS.public_state);
    divider(host);
    field(host, "Current Gate", GS.current_gate);
  }

  // --- left navigation ---
  var state = { active: "command_center" };

  function renderNav() {
    var host = document.getElementById("left-nav");
    if (!host) return;
    host.textContent = "";
    var brand = el("div", "nav-brand");
    brand.appendChild(el("div", "nav-title", "Capital Chronicle"));
    brand.appendChild(el("div", "nav-sub", "ContentOps Operator Cockpit V2"));
    host.appendChild(brand);

    (VM.nav || []).forEach(function (item) {
      var btn = el("button", "nav-item" + (item.id === state.active ? " active" : ""), item.label);
      btn.setAttribute("type", "button");
      btn.addEventListener("click", function () {
        state.active = item.id;
        renderNav();
        renderMain();
      });
      host.appendChild(btn);
    });
  }

  // --- directive bar (next allowed action) ---
  function renderDirective() {
    var host = document.getElementById("directive-bar");
    if (!host) return;
    host.textContent = "";
    var left = el("div");
    left.appendChild(el("div", "dir-label", "Next Allowed Action"));
    left.appendChild(el("div", "dir-value", GS.next_allowed_action));
    host.appendChild(left);
  }

  // --- shared screen grammar blocks ---
  function screenStatePanel(screen) {
    var sec = el("section", "section");
    sec.appendChild(el("div", "section-head", "Screen State"));
    var panel = el("div", "panel");
    panel.appendChild(kv("What this screen is for", screen.screen_state.what_for));
    var g = el("div", "grid grid-3");
    g.appendChild(kv("Mode", "static / local / fixture-driven"));
    g.appendChild(kv("Runtime Authority", "no"));
    g.appendChild(kv("Current Product State", GS.current_product_state));
    panel.appendChild(g);
    sec.appendChild(panel);
    return sec;
  }

  function primaryGatePanel(screen) {
    var gate = screen.primary_gate || {};
    var sec = el("section", "section");
    sec.appendChild(el("div", "section-head", "Primary Blocker / Gate"));
    var panel = el("div", "inset");
    var head = el("div", "st-head");
    head.appendChild(el("div", "st-title", gate.label || ""));
    head.appendChild(el("span", "chip s-" + gate.status, gate.status));
    panel.appendChild(head);
    panel.appendChild(el("div", "st-reason", gate.reason || ""));
    var g = el("div", "grid grid-2");
    g.appendChild(kv("Evidence Reference", (gate.evidence_ref_ids || []).join(", ")));
    g.appendChild(kv("Next Allowed Action", gate.next_allowed_action || ""));
    panel.appendChild(g);
    if (gate.caveat) panel.appendChild(el("div", "st-caveat", "Caveat: " + gate.caveat));
    sec.appendChild(panel);
    return sec;
  }

  function statusToken(tok) {
    var card = el("div", "status-token");
    var head = el("div", "st-head");
    head.appendChild(el("div", "st-title", tok.label || ""));
    head.appendChild(el("span", "chip s-" + tok.status, tok.status));
    card.appendChild(head);
    card.appendChild(el("div", "st-reason", tok.reason || ""));

    var meta = el("div", "st-meta");
    appendMetaLine(meta, "Evidence", (tok.evidence_ref_ids || []).join(", "));
    appendMetaLine(meta, "Allowed", (tok.allowed_actions || []).join(", "));
    appendMetaLine(meta, "Blocked", (tok.blocked_actions || []).join(", "));
    appendMetaLine(meta, "Current truth", String(!!tok.current_truth));
    appendMetaLine(meta, "Historical provenance", String(!!tok.historical_provenance));
    card.appendChild(meta);
    if (tok.caveat) card.appendChild(el("div", "st-caveat", "Caveat: " + tok.caveat));
    return card;
  }

  function appendMetaLine(meta, label, value) {
    var line = el("div");
    var b = el("b", null, label + ": ");
    line.appendChild(b);
    line.appendChild(document.createTextNode(value));
    meta.appendChild(line);
  }

  function statusTokensSection(screen) {
    var sec = el("section", "section");
    sec.appendChild(el("div", "section-head", "Critical Status (Evidence-Backed)"));
    var grid = el("div", "grid grid-2");
    (screen.status_tokens || []).forEach(function (tok) {
      grid.appendChild(statusToken(tok));
    });
    sec.appendChild(grid);
    return sec;
  }

  function provenanceSection(screen) {
    var prov = screen.build_provenance || {};
    var sec = el("section", "section");
    sec.appendChild(el("div", "section-head", "Historical Provenance"));
    var card = el("div", "provenance");
    var l1 = el("div");
    l1.appendChild(el("b", null, "Screen build task: "));
    l1.appendChild(document.createTextNode(prov.screen_build_task || ""));
    card.appendChild(l1);
    card.appendChild(el("div", null, prov.label + " — Not Runtime Authority"));
    sec.appendChild(card);
    return sec;
  }

  function disabledMatrixSection() {
    var sec = el("section", "section");
    sec.appendChild(el("div", "section-head", "Disabled / Forbidden / Future-Only Action Matrix"));
    var grid = el("div", "lock-grid");
    var ev = (VM.screens && VM.screens.evidence_vault) || {};
    (ev.forbidden_scope_matrix || []).forEach(function (item) {
      grid.appendChild(el("div", "lock-item", item + " — disabled"));
    });
    sec.appendChild(grid);
    return sec;
  }


  // --- screen-specific bodies ---
  function bodyCommandCenter(screen) {
    var frag = document.createDocumentFragment();
    var dp = screen.decision_panel || {};
    var sec = el("section", "section");
    sec.appendChild(el("div", "section-head", "Primary Decision"));
    var panel = el("div", "panel");
    panel.appendChild(kv("Question", dp.question));
    panel.appendChild(kv("Answer", dp.answer));
    panel.appendChild(kv("Reason", dp.reason));
    sec.appendChild(panel);
    frag.appendChild(sec);

    var cs = el("section", "section");
    cs.appendChild(el("div", "section-head", "Safety Counters"));
    var grid = el("div", "grid grid-4");
    (screen.safety_counters || []).forEach(function (c) {
      grid.appendChild(kv(c.label, c.value, "is-info"));
    });
    cs.appendChild(grid);
    frag.appendChild(cs);
    return frag;
  }

  function bodyContentStudio(screen) {
    var frag = document.createDocumentFragment();
    var sec = el("section", "section");
    sec.appendChild(el("div", "section-head", "Content Lanes (Separated)"));
    var grid = el("div", "grid grid-3");
    (screen.lanes || []).forEach(function (lane) {
      var card = el("div", "panel");
      var head = el("div", "st-head");
      head.appendChild(el("div", "st-title", lane.label));
      head.appendChild(el("span", "chip s-" + lane.status, lane.status));
      card.appendChild(head);
      card.appendChild(el("div", "st-reason", lane.description));
      grid.appendChild(card);
    });
    sec.appendChild(grid);
    frag.appendChild(sec);

    var ls = el("section", "section");
    ls.appendChild(el("div", "section-head", "Source / Brief / Lineage (Placeholder)"));
    var p = el("div", "inset");
    var sl = screen.source_lineage_placeholder || {};
    p.appendChild(kv("Source", sl.source));
    p.appendChild(kv("Brief", sl.brief));
    p.appendChild(kv("Lineage", sl.lineage));
    ls.appendChild(p);
    frag.appendChild(ls);
    return frag;
  }

  function bodyPublishReadiness(screen) {
    var frag = document.createDocumentFragment();
    var ps = el("section", "section");
    ps.appendChild(el("div", "section-head", "Platform Capability Registry (Dry-Run)"));
    var pg = el("div", "grid grid-4");
    (screen.platforms || []).forEach(function (pf) {
      var card = el("div", "panel");
      card.appendChild(el("div", "st-title", pf.name));
      card.appendChild(el("div", "kv-value", pf.note));
      pg.appendChild(card);
    });
    ps.appendChild(pg);
    frag.appendChild(ps);

    var gs = el("section", "section");
    gs.appendChild(el("div", "section-head", "Gate Matrix"));
    var wrap = el("div", "table-wrap");
    var table = el("table", "data-table");
    var thead = el("thead");
    var htr = el("tr");
    ["Gate", "State", "Operator Affordance"].forEach(function (h) { htr.appendChild(el("th", null, h)); });
    thead.appendChild(htr);
    table.appendChild(thead);
    var tbody = el("tbody");
    (screen.gate_rows || []).forEach(function (row) {
      var tr = el("tr");
      tr.appendChild(el("td", null, row.gate));
      var stateTd = el("td");
      stateTd.appendChild(el("span", "chip s-" + row.state, row.state));
      tr.appendChild(stateTd);
      tr.appendChild(el("td", null, row.label));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    gs.appendChild(wrap);
    gs.appendChild(kv("Next blocker", screen.next_blocker, "is-block"));
    frag.appendChild(gs);
    return frag;
  }

  function bodyEvidenceVault(screen) {
    var frag = document.createDocumentFragment();

    var idx = el("section", "section");
    idx.appendChild(el("div", "section-head", "Task Evidence Packet Index"));
    var wrap = el("div", "table-wrap");
    var table = el("table", "data-table");
    var thead = el("thead");
    var htr = el("tr");
    ["Evidence ID", "Task", "Classification", "HEAD", "Artifact"].forEach(function (h) { htr.appendChild(el("th", null, h)); });
    thead.appendChild(htr);
    table.appendChild(thead);
    var tbody = el("tbody");
    (screen.evidence_index || []).forEach(function (r) {
      var tr = el("tr");
      [r.id, r.task, r.classification, r.head, r.artifact].forEach(function (c) { tr.appendChild(el("td", null, c)); });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    idx.appendChild(wrap);
    frag.appendChild(idx);

    var tl = el("section", "section");
    tl.appendChild(el("div", "section-head", "Commit / Evidence Timeline"));
    var tg = el("div", "grid grid-2");
    (screen.commit_timeline || []).forEach(function (c) {
      var card = el("div", "panel");
      var head = el("div", "st-head");
      head.appendChild(el("div", "st-title", c.head));
      head.appendChild(el("span", "chip " + (c.current_truth ? "sev-info" : "sev-review"),
        c.current_truth ? "CURRENT TRUTH" : "HISTORICAL"));
      card.appendChild(head);
      card.appendChild(el("div", "kv-label", c.label));
      card.appendChild(el("div", "st-reason", c.note));
      tg.appendChild(card);
    });
    tl.appendChild(tg);
    frag.appendChild(tl);

    var vm = el("section", "section");
    vm.appendChild(el("div", "section-head", "Validation Matrix"));
    var vg = el("div", "grid grid-2");
    (screen.validation_matrix || []).forEach(function (v) {
      vg.appendChild(kv(v.check, v.expected));
    });
    vm.appendChild(vg);
    frag.appendChild(vm);

    var cr = el("section", "section");
    cr.appendChild(el("div", "section-head", "Caveat Registry"));
    var crp = el("div", "panel");
    var ul = el("ul", "plain-list");
    (screen.caveat_registry || []).forEach(function (c) { ul.appendChild(el("li", null, c)); });
    crp.appendChild(ul);
    cr.appendChild(crp);
    frag.appendChild(cr);

    var bl = el("section", "section");
    bl.appendChild(el("div", "section-head", "Active Blocker Registry"));
    var blp = el("div", "inset");
    (screen.active_blockers || []).forEach(function (b) {
      var line = el("div", "st-head");
      line.appendChild(el("div", "st-title", b.label));
      line.appendChild(el("span", "chip sev-block", "BLOCKED"));
      blp.appendChild(line);
    });
    blp.appendChild(kv("Next task discipline", screen.next_task_discipline));
    bl.appendChild(blp);
    frag.appendChild(bl);
    return frag;
  }


  function bodyContentCalendar(screen) {
    var frag = document.createDocumentFragment();

    var as = el("section", "section");
    as.appendChild(el("div", "section-head", "Allowed Manual States"));
    var ag = el("div", "tag-strip");
    (screen.allowed_states || []).forEach(function (s) {
      ag.appendChild(el("span", "chip sev-info", s));
    });
    as.appendChild(ag);
    frag.appendChild(as);

    var fs = el("section", "section");
    fs.appendChild(el("div", "section-head", "Forbidden States (Not Available)"));
    var fg = el("div", "lock-grid");
    (screen.forbidden_states || []).forEach(function (s) {
      fg.appendChild(el("div", "lock-item", s + " — forbidden"));
    });
    fs.appendChild(fg);
    frag.appendChild(fs);

    var bs = el("section", "section");
    bs.appendChild(el("div", "section-head", "Workflow Board (Manual Only)"));
    var board = el("div", "board");
    (screen.cards || []).forEach(function (c) {
      var card = el("div", "board-card");
      card.appendChild(el("div", "bc-title", c.title));
      card.appendChild(el("div", "bc-state", c.state));
      board.appendChild(card);
    });
    bs.appendChild(board);
    frag.appendChild(bs);
    return frag;
  }

  function bodyVisualExport(screen) {
    var frag = document.createDocumentFragment();

    var cs = el("section", "section");
    cs.appendChild(el("div", "section-head", "Screenshot-Safe Preparation Checklist"));
    var grid = el("div", "grid grid-2");
    (screen.checklist || []).forEach(function (c) {
      var card = el("div", "panel");
      var head = el("div", "st-head");
      head.appendChild(el("div", "st-title", c.item));
      head.appendChild(el("span", "chip s-" + c.state, c.state));
      card.appendChild(head);
      grid.appendChild(card);
    });
    cs.appendChild(grid);
    frag.appendChild(cs);

    var fs = el("section", "section");
    fs.appendChild(el("div", "section-head", "Forbidden (No Export Engine)"));
    var fg = el("div", "lock-grid");
    (screen.forbidden || []).forEach(function (f) {
      fg.appendChild(el("div", "lock-item", f + " — forbidden"));
    });
    fs.appendChild(fg);
    frag.appendChild(fs);

    var ls = el("section", "section");
    ls.appendChild(el("div", "section-head", "Limitation Notes"));
    var lp = el("div", "panel");
    var ul = el("ul", "plain-list");
    (screen.limitation_notes || []).forEach(function (n) { ul.appendChild(el("li", null, n)); });
    lp.appendChild(ul);
    ls.appendChild(lp);
    frag.appendChild(ls);
    return frag;
  }

  function bodySettings(screen) {
    var frag = document.createDocumentFragment();

    var hs = el("section", "section");
    hs.appendChild(el("div", "section-head", "Active Hard Boundaries"));
    var hp = el("div", "panel");
    var ul = el("ul", "plain-list");
    (screen.hard_boundaries || []).forEach(function (b) { ul.appendChild(el("li", null, b)); });
    hp.appendChild(ul);
    hs.appendChild(hp);
    frag.appendChild(hs);

    var ps = el("section", "section");
    ps.appendChild(el("div", "section-head", "Policies"));
    var pg = el("div", "grid grid-2");
    (screen.policies || []).forEach(function (p) {
      pg.appendChild(kv(p.name, p.value));
    });
    ps.appendChild(pg);
    frag.appendChild(ps);

    var ns = el("section", "section");
    ns.appendChild(el("div", "section-head", "Never Displayed"));
    var ng = el("div", "lock-grid");
    (screen.never_display || []).forEach(function (n) {
      ng.appendChild(el("div", "lock-item", n + " — never shown"));
    });
    ns.appendChild(ng);
    frag.appendChild(ns);
    return frag;
  }


  // --- main render dispatch ---
  var BODY_BUILDERS = {
    command_center: bodyCommandCenter,
    content_studio: bodyContentStudio,
    publish_readiness: bodyPublishReadiness,
    evidence_vault: bodyEvidenceVault,
    content_calendar: bodyContentCalendar,
    visual_export: bodyVisualExport,
    settings: bodySettings
  };

  function renderMain() {
    var host = document.getElementById("main");
    if (!host) return;
    host.textContent = "";

    var screens = VM.screens || {};
    var screen = screens[state.active];
    if (!screen) {
      host.appendChild(el("div", "panel", "Unknown screen."));
      return;
    }

    host.appendChild(el("div", "note-banner",
      "LOCAL ONLY / FIXTURE DRIVEN / NOT PUBLIC POSTABLE / RUNTIME AUTHORITY: NO"));
    host.appendChild(el("h1", "screen-title", screen.title));
    host.appendChild(el("p", "screen-purpose", screen.purpose));

    host.appendChild(screenStatePanel(screen));
    host.appendChild(primaryGatePanel(screen));

    var bodyBuilder = BODY_BUILDERS[state.active];
    if (bodyBuilder) {
      var bodySec = el("section", "section");
      bodySec.appendChild(el("div", "section-head", "Screen Body"));
      bodySec.appendChild(bodyBuilder(screen));
      host.appendChild(bodySec);
    }

    if (screen.status_tokens && screen.status_tokens.length) {
      host.appendChild(statusTokensSection(screen));
    }

    host.appendChild(evidenceReferenceSection(screen));
    host.appendChild(disabledMatrixSection());
    host.appendChild(provenanceSection(screen));
  }

  function evidenceReferenceSection(screen) {
    var sec = el("section", "section");
    sec.appendChild(el("div", "section-head", "Evidence Reference"));
    var panel = el("div", "panel");
    var ids = {};
    (screen.status_tokens || []).forEach(function (t) {
      (t.evidence_ref_ids || []).forEach(function (id) { ids[id] = true; });
    });
    if (screen.primary_gate) {
      (screen.primary_gate.evidence_ref_ids || []).forEach(function (id) { ids[id] = true; });
    }
    panel.appendChild(kv("Evidence IDs (this screen)", Object.keys(ids).join(", ") || "see Evidence Vault"));
    panel.appendChild(kv("Source of truth", "All current state reads from the canonical global state model. Historical and Stitch reference provenance are not runtime authority."));
    sec.appendChild(panel);
    return sec;
  }

  // --- init ---
  function init() {
    renderRibbon();
    renderHeader();
    renderNav();
    renderDirective();
    renderMain();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();


