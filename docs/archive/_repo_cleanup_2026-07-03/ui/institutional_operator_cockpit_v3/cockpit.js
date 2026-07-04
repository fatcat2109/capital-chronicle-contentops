/*
 * Capital Chronicle ContentOps — Operator Cockpit V3 renderer.
 *
 * Local static only. No runtime network of any kind: no remote requests,
 * sockets, or event streams; no remote dependency. Renders entirely from the
 * local canonical view model (window.CC_COCKPIT_V3_VIEW_MODEL) using safe DOM
 * text nodes. The only interactive control is left-nav screen switching.
 */
(function () {
  "use strict";

  var VM = window.CC_COCKPIT_V3_VIEW_MODEL || {};
  var GS = VM.global_state || {};

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  function severityClass(sev) {
    switch (sev) {
      case "ok": return "sev-ok";
      case "review": return "sev-review";
      case "block": return "sev-block";
      default: return "sev-info";
    }
  }

  function kv(label, value, mod) {
    var wrap = el("div", "kv" + (mod ? " " + mod : ""));
    wrap.appendChild(el("div", "kv-label", label));
    wrap.appendChild(el("div", "kv-value", value));
    return wrap;
  }

  function hdrField(host, label, value, mod) {
    var f = el("div", "hdr-field");
    f.appendChild(el("div", "hdr-label", label));
    f.appendChild(el("div", "hdr-value" + (mod ? " " + mod : ""), value));
    host.appendChild(f);
  }

  function hdrDivider(host) { host.appendChild(el("div", "hdr-divider")); }

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
    hdrField(host, "System Mode", GS.current_mode, "mono-strong");
    hdrDivider(host);
    hdrField(host, "Current Repo Baseline", GS.current_repo_baseline, "mono-strong");
    hdrDivider(host);
    hdrField(host, "V2 Build Candidate", GS.v2_build_candidate);
    hdrDivider(host);
    hdrField(host, "Kill Switch", String(GS.kill_switch).toUpperCase(), "is-block");
    hdrDivider(host);
    hdrField(host, "Current Gate", GS.current_gate);
  }

  // --- left navigation ---
  var state = { active: "command_center" };

  function renderNav() {
    var host = document.getElementById("left-nav");
    if (!host) return;
    host.textContent = "";
    var brand = el("div", "nav-brand");
    brand.appendChild(el("div", "nav-title", "Capital Chronicle"));
    brand.appendChild(el("div", "nav-sub", "ContentOps Operator Cockpit V3"));
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

  // --- directive bar ---
  function renderDirective() {
    var host = document.getElementById("directive-bar");
    if (!host) return;
    host.textContent = "";
    var left = el("div");
    left.appendChild(el("div", "dir-label", "Next Allowed Action"));
    left.appendChild(el("div", "dir-value", GS.next_allowed_action));
    host.appendChild(left);
  }

  // --- shared panel builders ---
  function screenStatePanel(screen) {
    var ss = screen.screen_state || {};
    var sec = el("section", "section");
    sec.appendChild(el("div", "section-head", "Screen State"));
    var panel = el("div", "panel");
    panel.appendChild(kv("Purpose", ss.what_for || screen.purpose));
    panel.appendChild(kv("Mode", "static / local / fixture-driven"));
    panel.appendChild(kv("Runtime authority", "no"));
    sec.appendChild(panel);
    return sec;
  }

  function gateCard(gate) {
    var card = el("div", "st-card " + severityClass(gate.severity));
    var head = el("div", "st-head");
    head.appendChild(el("div", "st-title", gate.label));
    head.appendChild(el("span", "chip " + severityClass(gate.severity), gate.status));
    card.appendChild(head);
    card.appendChild(el("div", "st-reason", gate.reason));
    var meta = el("div", "st-meta");
    meta.appendChild(el("span", null, "Evidence: " + (gate.evidence_ref_ids || []).join(", ")));
    if (gate.next_allowed_action) meta.appendChild(el("span", null, "Next: " + gate.next_allowed_action));
    card.appendChild(meta);
    if (gate.caveat) card.appendChild(el("div", "st-caveat", gate.caveat));
    return card;
  }

  function primaryGateSection(screen) {
    if (!screen.primary_gate) return null;
    var sec = el("section", "section");
    sec.appendChild(el("div", "section-head", "Primary Blocker / Gate"));
    sec.appendChild(gateCard(screen.primary_gate));
    return sec;
  }

  function statusTokensSection(screen) {
    var sec = el("section", "section");
    sec.appendChild(el("div", "section-head", "Status Tokens (evidence-backed)"));
    var grid = el("div", "grid grid-2");
    (screen.status_tokens || []).forEach(function (t) {
      var card = el("div", "st-card " + severityClass(t.severity));
      var head = el("div", "st-head");
      head.appendChild(el("div", "st-title", t.label));
      head.appendChild(el("span", "chip " + severityClass(t.severity), t.status));
      card.appendChild(head);
      card.appendChild(el("div", "st-reason", t.reason));
      var meta = el("div", "st-meta");
      meta.appendChild(el("span", null, "Evidence: " + (t.evidence_ref_ids || []).join(", ")));
      meta.appendChild(el("span", null, "Allowed: " + (t.allowed_actions || []).join(", ")));
      meta.appendChild(el("span", null, "Blocked: " + (t.blocked_actions || []).join(", ")));
      meta.appendChild(el("span", null, "Current truth: " + (t.current_truth ? "yes" : "no")));
      meta.appendChild(el("span", null, "Historical: " + (t.historical_provenance ? "yes" : "no")));
      card.appendChild(meta);
      if (t.caveat) card.appendChild(el("div", "st-caveat", t.caveat));
      grid.appendChild(card);
    });
    sec.appendChild(grid);
    return sec;
  }

  function provenanceSection(screen) {
    var bp = screen.build_provenance || {};
    var sec = el("section", "section");
    sec.appendChild(el("div", "section-head", "Historical Provenance"));
    var panel = el("div", "inset");
    panel.appendChild(kv("Screen build task", bp.screen_build_task || "0174B"));
    panel.appendChild(kv("Label", bp.label || "Historical Screen Provenance"));
    panel.appendChild(kv("Runtime authority", "no — Not Runtime Authority"));
    sec.appendChild(panel);
    return sec;
  }

  function disabledMatrixSection() {
    var sec = el("section", "section");
    sec.appendChild(el("div", "section-head", "Disabled / Forbidden / Future-Only"));
    var grid = el("div", "lock-grid");
    [
      "publish — forbidden", "post — forbidden", "send — forbidden",
      "schedule — forbidden", "dispatch — forbidden", "platform API — disabled",
      "provider/LLM API — disabled", "Telegram API — disabled",
      "credential read — disabled", "credential validation — disabled",
      "env read — disabled", "scrape — forbidden", "autonomous reply/DM — forbidden",
      "export/upload/download — forbidden", "evidence mutation — forbidden"
    ].forEach(function (label) {
      grid.appendChild(el("div", "lock-item", label));
    });
    sec.appendChild(grid);
    return sec;
  }


  // --- screen bodies ---
  function bodyCommandCenter(screen) {
    var frag = document.createDocumentFragment();
    var dp = screen.decision_panel || {};

    var hero = el("div", "hero");
    var dec = el("div", "hero-decision");
    dec.appendChild(el("div", "hero-q", dp.question));
    dec.appendChild(el("div", "hero-a", dp.answer));
    dec.appendChild(el("div", "hero-reason", dp.reason));
    hero.appendChild(dec);

    var side = el("div", "hero-side");
    if (screen.primary_gate) side.appendChild(gateCard(screen.primary_gate));
    hero.appendChild(side);
    frag.appendChild(hero);

    var cs = el("section", "section");
    cs.appendChild(el("div", "section-head", "Safety Counters"));
    var grid = el("div", "grid grid-4");
    (screen.safety_counters || []).forEach(function (c) {
      grid.appendChild(kv(c.label, c.value, "is-info"));
    });
    cs.appendChild(grid);
    frag.appendChild(cs);

    frag.appendChild(lineageSection());
    return frag;
  }

  function lineageSection() {
    var ev = (VM.screens && VM.screens.evidence_vault) || {};
    var sec = el("section", "section");
    sec.appendChild(el("div", "section-head", "Lineage Strip"));
    var panel = el("div", "panel");
    var lin = el("div", "lineage");
    (ev.commit_timeline || []).forEach(function (c) {
      var row = el("div", "lin-row kind-" + (c.kind || "historical"));
      row.appendChild(el("div", "lin-head", c.head));
      var mid = el("div");
      mid.appendChild(el("div", "lin-label", c.label));
      mid.appendChild(el("div", "lin-note", c.note));
      row.appendChild(mid);
      row.appendChild(el("span", "chip " + (c.current_truth ? "sev-info" : (c.historical_provenance ? "sev-review" : "sev-ok")),
        c.current_truth ? "CURRENT" : (c.historical_provenance ? "HISTORICAL" : c.kind.toUpperCase())));
      lin.appendChild(row);
    });
    panel.appendChild(lin);
    sec.appendChild(panel);
    return sec;
  }

  function bodyContentStudio(screen) {
    var frag = document.createDocumentFragment();
    var sec = el("section", "section");
    sec.appendChild(el("div", "section-head", "Content Lanes (Separated)"));
    var grid = el("div", "grid grid-3");
    (screen.lanes || []).forEach(function (lane) {
      var card = el("div", "st-card " + severityClass(lane.status));
      var head = el("div", "st-head");
      head.appendChild(el("div", "st-title", lane.label));
      head.appendChild(el("span", "chip " + severityClass(lane.status), lane.status.toUpperCase()));
      card.appendChild(head);
      card.appendChild(el("div", "st-reason", lane.description));
      var meta = el("div", "st-meta");
      meta.appendChild(el("span", null, "Claim risk: " + lane.claim_risk));
      meta.appendChild(el("span", null, "Requires: " + lane.requires));
      card.appendChild(meta);
      grid.appendChild(card);
    });
    sec.appendChild(grid);
    frag.appendChild(sec);
    return frag;
  }

  function bodyPublishReadiness(screen) {
    var frag = document.createDocumentFragment();
    var ps = el("section", "section");
    ps.appendChild(el("div", "section-head", "Platform Readiness Records (Dry-Run)"));
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
      var st = el("td");
      st.appendChild(el("span", "chip " + severityClass(row.state === "PASS" ? "ok" : row.state), row.state));
      tr.appendChild(st);
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
    frag.appendChild(lineageSection());

    var idx = el("section", "section");
    idx.appendChild(el("div", "section-head", "Task Evidence Packet Index"));
    var wrap = el("div", "table-wrap");
    var table = el("table", "data-table");
    var thead = el("thead");
    var htr = el("tr");
    ["ID", "Task", "Classification", "HEAD", "Artifact"].forEach(function (h) { htr.appendChild(el("th", null, h)); });
    thead.appendChild(htr);
    table.appendChild(thead);
    var tbody = el("tbody");
    (screen.evidence_index || []).forEach(function (r) {
      var tr = el("tr");
      if (r.head === GS.current_repo_baseline) tr.className = "is-current";
      tr.appendChild(el("td", null, r.id));
      tr.appendChild(el("td", null, r.task));
      tr.appendChild(el("td", null, r.classification));
      tr.appendChild(el("td", null, r.head));
      tr.appendChild(el("td", null, r.artifact));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    idx.appendChild(wrap);
    frag.appendChild(idx);

    var vm = el("section", "section");
    vm.appendChild(el("div", "section-head", "Validation Matrix"));
    var vgrid = el("div", "grid grid-2");
    (screen.validation_matrix || []).forEach(function (v) {
      vgrid.appendChild(kv(v.check, v.expected));
    });
    vm.appendChild(vgrid);
    frag.appendChild(vm);

    var cr = el("section", "section");
    cr.appendChild(el("div", "section-head", "Caveat Registry"));
    var clist = el("ul", "plain-list");
    (screen.caveat_registry || []).forEach(function (c) { clist.appendChild(el("li", null, c)); });
    cr.appendChild(clist);
    frag.appendChild(cr);

    var fs = el("section", "section");
    fs.appendChild(el("div", "section-head", "Forbidden-Scope Registry"));
    var fgrid = el("div", "lock-grid");
    (screen.forbidden_scope_matrix || []).forEach(function (f) { fgrid.appendChild(el("div", "lock-item", f)); });
    fs.appendChild(fgrid);
    frag.appendChild(fs);

    var ab = el("section", "section");
    ab.appendChild(el("div", "section-head", "Active Blockers"));
    (screen.active_blockers || []).forEach(function (b) {
      var card = el("div", "st-card sev-block");
      var head = el("div", "st-head");
      head.appendChild(el("div", "st-title", b.label));
      head.appendChild(el("span", "chip sev-block", "BLOCKED"));
      card.appendChild(head);
      ab.appendChild(card);
    });
    ab.appendChild(kv("Next-task discipline", screen.next_task_discipline));
    frag.appendChild(ab);
    return frag;
  }

  function bodyContentCalendar(screen) {
    var frag = document.createDocumentFragment();
    var bs = el("section", "section");
    bs.appendChild(el("div", "section-head", "Manual Workflow Board"));
    var board = el("div", "board");
    (screen.cards || []).forEach(function (c) {
      var card = el("div", "board-card");
      card.appendChild(el("div", "bc-title", c.title));
      card.appendChild(el("div", "bc-state", c.state));
      board.appendChild(card);
    });
    bs.appendChild(board);
    frag.appendChild(bs);

    var as = el("section", "section");
    as.appendChild(el("div", "section-head", "Allowed States"));
    var ag = el("div", "tag-strip");
    (screen.allowed_states || []).forEach(function (s) { ag.appendChild(el("span", "chip sev-info", s)); });
    as.appendChild(ag);
    frag.appendChild(as);

    var fsx = el("section", "section");
    fsx.appendChild(el("div", "section-head", "Forbidden / Unavailable States"));
    var fg = el("div", "lock-grid");
    (screen.forbidden_states || []).forEach(function (s) { fg.appendChild(el("div", "lock-item", s)); });
    fsx.appendChild(fg);
    frag.appendChild(fsx);
    return frag;
  }


  function bodyVisualExport(screen) {
    var frag = document.createDocumentFragment();
    var cs = el("section", "section");
    cs.appendChild(el("div", "section-head", "Screenshot-Safe Checklist"));
    var grid = el("div", "grid grid-2");
    (screen.checklist || []).forEach(function (c) {
      var card = el("div", "st-card sev-ok");
      var head = el("div", "st-head");
      head.appendChild(el("div", "st-title", c.item));
      head.appendChild(el("span", "chip sev-ok", c.state));
      card.appendChild(head);
      grid.appendChild(card);
    });
    cs.appendChild(grid);
    frag.appendChild(cs);

    var fs = el("section", "section");
    fs.appendChild(el("div", "section-head", "Forbidden (no export automation)"));
    var fg = el("div", "lock-grid");
    (screen.forbidden || []).forEach(function (f) { fg.appendChild(el("div", "lock-item", f)); });
    fs.appendChild(fg);
    frag.appendChild(fs);

    var ln = el("section", "section");
    ln.appendChild(el("div", "section-head", "Limitation Notes"));
    var list = el("ul", "plain-list");
    (screen.limitation_notes || []).forEach(function (n) { list.appendChild(el("li", null, n)); });
    ln.appendChild(list);
    frag.appendChild(ln);
    return frag;
  }

  function bodySettings(screen) {
    var frag = document.createDocumentFragment();
    var hb = el("section", "section");
    hb.appendChild(el("div", "section-head", "Active Hard Boundaries"));
    var hlist = el("ul", "plain-list");
    (screen.hard_boundaries || []).forEach(function (b) { hlist.appendChild(el("li", null, b)); });
    hb.appendChild(hlist);
    frag.appendChild(hb);

    var ps = el("section", "section");
    ps.appendChild(el("div", "section-head", "Policies"));
    var pgrid = el("div", "grid grid-2");
    (screen.policies || []).forEach(function (p) { pgrid.appendChild(kv(p.name, p.value)); });
    ps.appendChild(pgrid);
    frag.appendChild(ps);

    var nd = el("section", "section");
    nd.appendChild(el("div", "section-head", "Never Displayed"));
    var ng = el("div", "lock-grid");
    (screen.never_display || []).forEach(function (n) { ng.appendChild(el("div", "lock-item", n)); });
    nd.appendChild(ng);
    frag.appendChild(nd);
    return frag;
  }


  // --- main render dispatcher ---
  var BODIES = {
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
    var inner = el("div", "main-inner");

    var screen = (VM.screens || {})[state.active] || {};

    inner.appendChild(el("div", "note-banner",
      "SCREENSHOT-SAFE / LOCAL ONLY / NOT PUBLIC-POSTABLE / LIVE DISABLED / MANUAL REVIEW REQUIRED / NO FINANCIAL ADVICE / NO SIGNAL LANGUAGE / KILL SWITCH ACTIVE"));
    inner.appendChild(el("h1", "screen-title", screen.title || ""));
    inner.appendChild(el("p", "screen-purpose", screen.purpose || ""));

    inner.appendChild(screenStatePanel(screen));
    var pg = primaryGateSection(screen);
    if (pg) inner.appendChild(pg);

    var body = BODIES[state.active];
    if (body) inner.appendChild(body(screen));

    inner.appendChild(statusTokensSection(screen));
    inner.appendChild(disabledMatrixSection());
    inner.appendChild(provenanceSection(screen));

    host.appendChild(inner);
  }

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
