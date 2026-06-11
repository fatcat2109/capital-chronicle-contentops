/*
 * Operator Cockpit V4 — Renderer.
 * Local-only, static. Nav switching + inspect rendering only.
 * No runtime network calls, no remote requests, no realtime sockets, no beacons.
 * No browser storage. No forms, no submit, no platform/credential controls.
 */
(function () {
  "use strict";

  var MODEL = window.CC_OPERATOR_COCKPIT_V4_MODEL;

  /* --- tiny DOM helpers --- */
  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }
  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

  /* Normalize an evidence ref (object or string) to a stable display id. */
  function evidenceRefId(ref) {
    if (typeof ref === "string") return ref;
    if (ref && ref.evidence_id) return ref.evidence_id;
    if (ref && ref.id) return ref.id;
    return "";
  }

  /* --- Safety Rail --- */
  function renderSafetyRail() {
    var rail = document.getElementById("safety-rail");
    clear(rail);
    MODEL.safety_locks.critical.forEach(function (lbl) {
      rail.appendChild(el("span", "safety-chip critical", lbl));
    });
    var cluster = el("span", "safety-locks-cluster",
      "SYSTEM LOCKS +" + MODEL.safety_locks.grouped_locks.length + ": " +
      MODEL.safety_locks.grouped_locks.join(" / "));
    rail.appendChild(cluster);
  }

  /* --- Truth Rail --- */
  function renderTruthRail() {
    var rail = document.getElementById("truth-rail");
    clear(rail);
    MODEL.truth_rail.forEach(function (cell) {
      var c = el("div", "truth-cell kind-" + cell.kind);
      c.appendChild(el("span", "role-label", cell.role_label));
      c.appendChild(el("span", "role-value", cell.value));
      rail.appendChild(c);
    });
  }

  /* --- Navigation --- */
  function renderNav(activeId) {
    var nav = document.getElementById("screen-nav");
    clear(nav);
    MODEL.screens.forEach(function (screen) {
      var btn = el("button", "nav-item" + (screen.screen_id === activeId ? " active" : ""), screen.nav_label);
      btn.setAttribute("type", "button");
      btn.setAttribute("data-screen", screen.screen_id);
      btn.addEventListener("click", function () { renderScreen(screen.screen_id); });
      nav.appendChild(btn);
    });
  }

  /* --- Footer (in-flow next allowed action) --- */
  function renderFooter() {
    var footer = document.getElementById("cockpit-footer");
    clear(footer);
    footer.classList.add("audit-footer");
    var next = MODEL.truth_rail.filter(function (t) { return t.role_label === "Next Allowed Action"; })[0];
    footer.appendChild(el("span", "footer-label", "next allowed action"));
    footer.appendChild(el("span", "footer-action", next ? next.value : ""));
  }

  /* --- shared band renderer for evidence-backed status objects --- */
  function renderBand(status) {
    var b = el("div", "band sev-" + (status.severity || "info"));
    b.appendChild(el("span", "band-label", status.label || "Status"));
    var t = el("div", "band-text");
    t.appendChild(el("span", "token " + status.status, status.status));
    t.appendChild(document.createTextNode("  " + (status.text || "")));
    b.appendChild(t);
    if (status.reason) b.appendChild(el("div", "band-reason", "Reason: " + status.reason));
    if (status.evidence_ref_ids && status.evidence_ref_ids.length) {
      b.appendChild(el("div", "band-reason", "Evidence: " + status.evidence_ref_ids.join(", ")));
    }
    if (status.caveat) b.appendChild(el("div", "band-reason", "Caveat: " + status.caveat));
    return b;
  }

  function panel(headText) {
    var p = el("div", "panel");
    if (headText) p.appendChild(el("div", "panel-head", headText));
    return p;
  }

  /* --- Command Center --- */
  function renderCommandCenter(s, body) {
    body.appendChild(renderBand(s.verdict));

    /* Integrated mission-control decision band: verdict token + next action +
       blocker count + evidence count in one scan-fast grid. */
    var mission = el("div", "mission-grid primary-command-board section-gap");
    var nextAction = MODEL.truth_rail.filter(function (t) { return t.role_label === "Next Allowed Action"; })[0];
    var cells = [
      ["Current Verdict", s.verdict.status, "verdict"],
      ["Next Allowed Action", nextAction ? nextAction.value : "", "next"],
      ["Active Blockers", String(MODEL.blocker_stack.length), "count"],
      ["Evidence Refs", String(MODEL.evidence_refs.length), "count"],
      ["Provenance", "current vs historical (labeled)", "prov"]
    ];
    cells.forEach(function (cdef) {
      var cell = el("div", "decision-stack kind-" + cdef[2]);
      cell.appendChild(el("div", "data-label", cdef[0]));
      if (cdef[2] === "verdict") {
        cell.appendChild(el("span", "token " + cdef[1], cdef[1]));
      } else {
        cell.appendChild(el("div", "decision-value", cdef[1]));
      }
      mission.appendChild(cell);
    });
    body.appendChild(mission);

    var changed = el("div", "instrument-panel section-gap");
    var chHead = el("div", "instrument-head");
    chHead.appendChild(el("span", "instrument-title", "What Changed Since Last Accepted State"));
    chHead.appendChild(el("span", "data-label", "change ledger"));
    changed.appendChild(chHead);
    var ledger = el("div", "change-ledger");
    s.what_changed.forEach(function (c) {
      var row = el("div", "ledger-entry");
      row.appendChild(el("span", "ledger-mark", "Δ"));
      row.appendChild(el("span", "ledger-text", c));
      ledger.appendChild(row);
    });
    changed.appendChild(ledger);
    body.appendChild(changed);

    var blk = el("div", "instrument-panel incident-board section-gap");
    var blkHead = el("div", "instrument-head");
    blkHead.appendChild(el("span", "instrument-title", "Active Blocker Stack"));
    blkHead.appendChild(el("span", "data-label", "ordered by severity"));
    blk.appendChild(blkHead);
    var rail = el("div", "blocker-rail");
    MODEL.blocker_stack.forEach(function (b) {
      var row = el("div", "rail-item sev-" + b.severity);
      row.appendChild(el("div", "blocker-label", b.label));
      row.appendChild(el("div", "blocker-reason", b.reason));
      row.appendChild(el("div", "evref", "evidence: " + b.evidence_ref_ids.join(", ")));
      rail.appendChild(row);
    });
    blk.appendChild(rail);
    body.appendChild(blk);

    var dep = el("div", "instrument-panel proof-graph proof-ledger-board section-gap");
    var depHead = el("div", "instrument-head");
    depHead.appendChild(el("span", "instrument-title", "Evidence Dependency Map"));
    depHead.appendChild(el("span", "data-label", "proof ledger"));
    dep.appendChild(depHead);
    var proof = el("div", "proof-strip");
    s.evidence_dependency_map.forEach(function (n) {
      var row = el("div", "proof-row");
      row.appendChild(el("span", "proof-node", n.node));
      row.appendChild(el("span", "proof-dep", "<- " + n.depends_on.join(", ")));
      proof.appendChild(row);
    });
    dep.appendChild(proof);
    body.appendChild(dep);

    var counters = panel("Safety Counters");
    var wrap = el("div", "counters counter-strip");
    var c = s.safety_counters;
    [["locks active", c.locks_active], ["gates open", c.gates_open], ["blockers", c.blockers], ["review items", c.review_items]].forEach(function (pair) {
      var cc = el("div", "counter");
      cc.appendChild(el("div", "num", String(pair[1])));
      cc.appendChild(el("div", "lbl", pair[0]));
      wrap.appendChild(cc);
    });
    counters.appendChild(wrap);
    body.appendChild(counters);
  }

  /* --- Content Studio --- */
  function renderContentStudio(s, body) {
    body.appendChild(renderBand(s.studio_state));
    var grid = el("div", "grid grid-2 lane-control-grid");
    s.lanes.forEach(function (lane) {
      var p = el("div", "lane lane-control-board" + (lane.status === "BLOCKED" ? " blocked" : ""));
      var head = el("div", "lane-name");
      head.appendChild(document.createTextNode(lane.name + " "));
      head.appendChild(el("span", "token " + lane.status, lane.status));
      p.appendChild(head);

      var gate = el("div", "lane-gate-rail");
      var verdict = el("div", "lane-verdict-cell sev-" + (lane.status === "BLOCKED" ? "blocked" : "review"));
      verdict.appendChild(el("span", "data-label", "Lane Verdict"));
      verdict.appendChild(el("span", "token " + lane.status, lane.status));
      gate.appendChild(verdict);
      var ready = el("div", "lane-readiness-strip");
      ready.appendChild(el("span", "data-label", "Readiness"));
      ready.appendChild(el("span", "mono-value", lane.status === "BLOCKED" ? "blocked / future-only" : "review-only / not public-postable"));
      gate.appendChild(ready);
      p.appendChild(gate);

      var ig = el("div", "lane-instrument-grid");
      [["lane-metric lane-metric-risk", "Claim Risk", lane.claim_risk],
       ["lane-metric lane-metric-forbidden", "Forbidden-Language", lane.forbidden_language],
       ["lane-metric lane-metric-platform", "Platform Fit", lane.platform_fit]
      ].forEach(function (m) {
        var cell = el("div", m[0]);
        cell.appendChild(el("div", "data-label", m[1]));
        cell.appendChild(el("div", "lane-metric-value", m[2]));
        ig.appendChild(cell);
      });
      p.appendChild(ig);

      var lim = el("div", "lane-limits");
      lim.appendChild(el("div", "data-label", "Limitations"));
      var limUl = el("ul");
      lane.limitations.forEach(function (l) { limUl.appendChild(el("li", null, l)); });
      lim.appendChild(limUl);
      p.appendChild(lim);

      var chk = el("div", "lane-checklist");
      chk.appendChild(el("div", "data-label", "Manual Checklist"));
      var chkUl = el("ul");
      lane.checklist.forEach(function (l) { chkUl.appendChild(el("li", null, l)); });
      chk.appendChild(chkUl);
      p.appendChild(chk);

      var ev = el("div", "lane-evidence-strip");
      ev.appendChild(el("span", "data-label", "Evidence"));
      ev.appendChild(el("span", "mono-value", lane.evidence_ref_ids.join(", ")));
      p.appendChild(ev);

      p.appendChild(el("div", "token NOT_PUBLIC_POSTABLE", "NOT_PUBLIC_POSTABLE"));
      grid.appendChild(p);
    });
    body.appendChild(grid);
  }

  /* --- Publish Readiness Tower (gate matrix first) --- */
  function renderPublishReadiness(s, body) {
    body.appendChild(renderBand(s.readiness_verdict));
    var mp = panel("Gate Matrix");
    var wrap = el("div", "gate-matrix gate-control-surface");
    var table = el("table", "matrix");
    var thead = el("thead"), htr = el("tr");
    s.gate_columns.forEach(function (col) { htr.appendChild(el("th", null, col)); });
    thead.appendChild(htr); table.appendChild(thead);
    var tbody = el("tbody");
    s.gate_matrix.forEach(function (r) {
      var tr = el("tr");
      tr.appendChild(el("td", "mono", r.platform));
      ["official_docs", "dry_run_renderer", "approval_ledger", "credential_slot", "credential_read", "credential_validation", "redacted_audit", "kill_switch", "live_adapter", "scheduler", "posting"].forEach(function (k) {
        var td = el("td");
        td.appendChild(el("span", "token " + r[k], r[k]));
        tr.appendChild(td);
      });
      tr.appendChild(el("td", "wrap", r.next_blocker));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    mp.appendChild(wrap);
    mp.classList.add("section-gap");
    body.appendChild(mp);

    var rec = panel("Platform Readiness Records (inspect-only)");
    s.platform_records.forEach(function (p) {
      var row = el("div", "reg-row");
      row.appendChild(el("span", "reg-key", p.platform + " — allowed: " + p.allowed_now));
      row.appendChild(el("span", "reg-val", "forbidden: " + p.forbidden_now));
      rec.appendChild(row);
    });
    body.appendChild(rec);
  }


  /* --- Evidence Vault (compliance room) --- */
  function renderEvidenceVault(s, body) {
    body.appendChild(renderBand(s.evidence_state));

    var mp = panel("Validation Matrix");
    var wrap = el("div", "matrix-wrap audit-room-grid");
    var table = el("table", "matrix");
    var thead = el("thead"), htr = el("tr");
    ["check", "expected", "observed", "status", "evidence ref"].forEach(function (c) { htr.appendChild(el("th", null, c)); });
    thead.appendChild(htr); table.appendChild(thead);
    var tbody = el("tbody");
    s.validation_matrix.forEach(function (r) {
      var tr = el("tr");
      tr.appendChild(el("td", "wrap", r.check));
      tr.appendChild(el("td", "wrap", r.expected));
      tr.appendChild(el("td", "wrap", r.observed));
      var td = el("td"); td.appendChild(el("span", "token " + r.status, r.status)); tr.appendChild(td);
      tr.appendChild(el("td", "mono", r.evidence_ref));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody); wrap.appendChild(table); mp.appendChild(wrap);
    mp.classList.add("section-gap");
    body.appendChild(mp);

    var tl = panel("Evidence Timeline");
    s.evidence_timeline.forEach(function (e) {
      var row = el("div", "reg-row");
      row.appendChild(el("span", "reg-key mono", e.commit + " — " + e.task));
      row.appendChild(el("span", "reg-val", e.classification));
      tl.appendChild(row);
    });
    tl.classList.add("section-gap");
    body.appendChild(tl);

    var grid = el("div", "grid grid-3 audit-registry audit-triad section-gap");
    var cav = panel("Caveat Registry");
    s.caveat_registry.forEach(function (c) {
      cav.appendChild(el("div", "reg-row", null));
      var r = cav.lastChild;
      r.appendChild(el("span", "reg-key", c.caveat_id + " (" + c.severity + ")"));
      r.appendChild(el("span", "reg-val", c.blocking ? "blocking" : "non-blocking"));
      cav.appendChild(el("div", "muted", c.note));
    });
    grid.appendChild(cav);
    var fsr = panel("Forbidden-Scope Registry");
    s.forbidden_scope_registry.forEach(function (f) { fsr.appendChild(el("div", "muted", "• " + f)); });
    grid.appendChild(fsr);
    var abr = panel("Active Blocker Registry");
    s.active_blocker_registry.forEach(function (b) {
      var row = el("div", "reg-row");
      row.appendChild(el("span", "reg-key", b.id));
      var rv = el("span", "reg-val"); rv.appendChild(el("span", "token " + b.status, b.status)); row.appendChild(rv);
      abr.appendChild(row);
    });
    grid.appendChild(abr);
    body.appendChild(grid);

    var leg = panel("Evidence Confidence Legend");
    s.confidence_legend.forEach(function (l) { leg.appendChild(el("div", "muted", "• " + l)); });
    leg.classList.add("section-gap");
    body.appendChild(leg);

    var qa = el("div", "band sev-caution");
    qa.appendChild(el("span", "band-label", s.browser_qa_row.label));
    var qt = el("div", "band-text");
    qt.appendChild(el("span", "token DEGRADED", "PASS_WITH_CAVEAT"));
    qt.appendChild(document.createTextNode("  " + s.browser_qa_row.note));
    qa.appendChild(qt);
    body.appendChild(qa);
  }

  /* --- Content Calendar / Workflow --- */
  function renderContentCalendar(s, body) {
    body.appendChild(renderBand(s.plan_state));

    var leg = panel("Allowed Manual States");
    s.allowed_states.forEach(function (st) { leg.appendChild(el("span", "token PASS", st)); leg.appendChild(document.createTextNode(" ")); });
    leg.classList.add("section-gap");
    body.appendChild(leg);

    var grid = el("div", "grid grid-2 manual-workflow-board section-gap");
    s.date_lanes.forEach(function (lane) {
      var p = el("div", "lane");
      p.appendChild(el("div", "lane-name", lane.period));
      lane.items.forEach(function (it) {
        var row = el("div", "reg-row");
        row.appendChild(el("span", "reg-key", it.title + " (" + it.lane + ")"));
        row.appendChild(el("span", "reg-val", it.state));
        p.appendChild(row);
      });
      grid.appendChild(p);
    });
    body.appendChild(grid);

    var locked = panel("Forbidden Automated States (disabled / future-only)");
    s.forbidden_states.forEach(function (f) {
      var row = el("div", "reg-row");
      row.appendChild(el("span", "reg-key muted", f.state + " — " + f.note));
      var rv = el("span", "reg-val"); rv.appendChild(el("span", "token " + f.status, f.status)); row.appendChild(rv);
      locked.appendChild(row);
    });
    body.appendChild(locked);
  }


  /* --- Visual Export / Screenshot-Safe --- */
  function renderVisualExport(s, body) {
    body.appendChild(renderBand(s.export_state));

    var cards = el("div", "grid grid-2 screenshot-prep-grid section-gap");
    s.report_cards.forEach(function (rc) {
      var p = el("div", "lane");
      p.appendChild(el("div", "lane-name", rc.surface + " — screenshot-safe report card"));
      var ul = el("ul");
      rc.labels.forEach(function (l) { ul.appendChild(el("li", null, "label: " + l)); });
      rc.redactions.forEach(function (r) { ul.appendChild(el("li", null, "redacts: " + r)); });
      p.appendChild(ul);
      p.appendChild(el("div", "token SECRET_REDACTED", "SCREENSHOT-SAFE"));
      cards.appendChild(p);
    });
    body.appendChild(cards);

    var grid = el("div", "grid grid-2 section-gap");
    var rp = panel("Redaction Preview");
    s.redaction_preview.forEach(function (r) { rp.appendChild(el("div", "mono", r)); });
    grid.appendChild(rp);
    var lp = panel("Limitation Strip");
    s.limitation_strip.forEach(function (l) { lp.appendChild(el("div", "muted", "• " + l)); });
    grid.appendChild(lp);
    body.appendChild(grid);

    var ph = el("div", "grid grid-2 section-gap");
    var ds = panel("Data Sufficiency");
    ds.appendChild(el("span", "token " + s.data_sufficiency_placeholder.status, s.data_sufficiency_placeholder.status));
    ds.appendChild(el("div", "muted", s.data_sufficiency_placeholder.note));
    ph.appendChild(ds);
    var fr = panel("Forecast Readiness");
    fr.appendChild(el("span", "token " + s.forecast_readiness_placeholder.status, s.forecast_readiness_placeholder.status));
    fr.appendChild(el("div", "muted", s.forecast_readiness_placeholder.note));
    ph.appendChild(fr);
    body.appendChild(ph);

    var bf = panel("Blocked Forecast Explainer");
    bf.appendChild(el("div", "muted", s.blocked_forecast_explainer));
    bf.classList.add("section-gap");
    body.appendChild(bf);

    var ff = panel(s.failure_forensics_card.title);
    ff.appendChild(el("div", "muted", s.failure_forensics_card.note));
    body.appendChild(ff);
  }

  /* --- Settings / Safety Policy --- */
  function renderSettings(s, body) {
    body.appendChild(renderBand(s.policy_state));

    var mp = panel("Policy Matrix");
    var wrap = el("div", "matrix-wrap policy-inspection-grid");
    var table = el("table", "matrix");
    var thead = el("thead"), htr = el("tr");
    ["policy", "value", "enforcement", "rationale"].forEach(function (c) { htr.appendChild(el("th", null, c)); });
    thead.appendChild(htr); table.appendChild(thead);
    var tbody = el("tbody");
    s.policy_matrix.forEach(function (r) {
      var tr = el("tr");
      tr.appendChild(el("td", "wrap", r.policy));
      tr.appendChild(el("td", "wrap", r.value));
      tr.appendChild(el("td", "wrap", r.enforcement));
      tr.appendChild(el("td", "wrap", r.rationale));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody); wrap.appendChild(table); mp.appendChild(wrap);
    mp.classList.add("section-gap");
    body.appendChild(mp);

    var reg = panel("Credential Never-Display Registry");
    s.credential_never_display_registry.forEach(function (c) {
      var row = el("div", "reg-row");
      row.appendChild(el("span", "reg-key", c.item));
      var rv = el("span", "reg-val"); rv.appendChild(el("span", "token SECRET_REDACTED", c.display)); row.appendChild(rv);
      reg.appendChild(row);
    });
    reg.classList.add("section-gap");
    body.appendChild(reg);

    var gp = panel("Platform Gate Policy");
    gp.appendChild(el("div", "muted", s.platform_gate_policy));
    gp.classList.add("section-gap");
    body.appendChild(gp);

    var fg = panel("Future Gate Requirements");
    s.future_gate_requirements.forEach(function (g) {
      var row = el("div", "reg-row");
      row.appendChild(el("span", "reg-key", g.gate));
      var rv = el("span", "reg-val"); rv.appendChild(el("span", "token " + g.status, g.status)); row.appendChild(rv);
      fg.appendChild(row);
    });
    body.appendChild(fg);
  }


  /* --- Secondary inspection / screen summary rail (sparse-screen governor) ---
     Uses only existing model data. No fake metrics, no market data, no
     public-ready content. Fills lower dead-zone with governed inspection. */
  function renderScreenSummaryRail(screen, body) {
    var rail = el("div", "secondary-inspection-rail screen-summary-rail empty-space-governor section-gap");

    var purpose = el("div", "summary-cell");
    purpose.appendChild(el("div", "data-label", "Screen Purpose"));
    purpose.appendChild(el("div", "summary-text", screen.primary_question || screen.title));
    rail.appendChild(purpose);

    var blk = el("div", "summary-cell");
    blk.appendChild(el("div", "data-label", "Current Blockers"));
    var bl = el("div", "summary-text mono-value",
      MODEL.blocker_stack.map(function (b) { return b.id; }).join(" / "));
    blk.appendChild(bl);
    rail.appendChild(blk);

    var ev = el("div", "summary-cell");
    ev.appendChild(el("div", "data-label", "Evidence Refs"));
    ev.appendChild(el("div", "summary-text mono-value",
      MODEL.evidence_refs.slice(0, 6).map(evidenceRefId).filter(Boolean).join(" / ")));
    rail.appendChild(ev);

    var nextAction = MODEL.truth_rail.filter(function (t) { return t.role_label === "Next Allowed Action"; })[0];
    var na = el("div", "summary-cell");
    na.appendChild(el("div", "data-label", "Manual Next Action"));
    na.appendChild(el("div", "summary-text", nextAction ? nextAction.value : ""));
    rail.appendChild(na);

    var caveat = el("div", "summary-cell");
    caveat.appendChild(el("div", "data-label", "Safety Caveat"));
    caveat.appendChild(el("div", "summary-text", "Local-only, review-only, not public-postable. Live posting, scheduler, and platform API disabled."));
    rail.appendChild(caveat);

    body.appendChild(rail);
  }

  /* --- Readable operator scan layer (0174S) ---
     First-open readable summary for every screen. Uses only model data.
     Detailed audit sections still render below, fully present. */
  function renderOperatorScanLayer(screen, body) {
    var layer = el("div", "operator-scan-layer");
    var board = el("div", "operator-summary-board");

    var intent = el("div", "scan-intent readable-body-copy");
    intent.textContent = screen.primary_question || screen.title;
    board.appendChild(intent);

    /* Primary answer: the screen's headline status verdict. */
    var verdict = screen.verdict || screen.studio_state || screen.readiness_verdict
      || screen.evidence_state || screen.plan_state || screen.export_state || screen.policy_state;
    var pa = el("div", "primary-answer");
    pa.appendChild(document.createTextNode(verdict && verdict.label ? verdict.label : screen.title));
    if (verdict && verdict.status) pa.appendChild(el("span", "token " + verdict.status, verdict.status));
    board.appendChild(pa);

    /* Next action card. */
    var nextAction = MODEL.truth_rail.filter(function (t) { return t.role_label === "Next Allowed Action"; })[0];
    var na = el("div", "next-action-card");
    na.appendChild(el("div", "scan-label", "Next Allowed Action"));
    na.appendChild(el("div", "scan-value", nextAction ? nextAction.value : (verdict && verdict.reason ? verdict.reason : "")));
    board.appendChild(na);

    /* Top blockers: max 3 cards, ordered by severity. */
    var cards = el("div", "top-blocker-cards");
    MODEL.blocker_stack.slice(0, 3).forEach(function (b) {
      var card = el("div", "blocker-card sev-" + b.severity);
      card.appendChild(el("span", "scan-label", b.id + " · " + b.severity));
      card.appendChild(el("div", "blocker-card-text", b.label));
      cards.appendChild(card);
    });
    board.appendChild(cards);

    /* Confidence summary: evidence families as chips + counts. */
    var conf = el("div", "confidence-summary");
    conf.appendChild(el("span", "scan-label", "Evidence (" + MODEL.evidence_refs.length + ")"));
    MODEL.evidence_refs.slice(0, 5).forEach(function (ref) {
      conf.appendChild(el("span", "evidence-chip", evidenceRefId(ref)));
    });
    conf.appendChild(el("span", "scan-label", "Blockers: " + MODEL.blocker_stack.length));
    board.appendChild(conf);

    layer.appendChild(board);
    body.appendChild(layer);
  }

  /* --- Screen dispatcher --- */
  function renderScreen(screenId) {
    var screen = MODEL.screens.filter(function (s) { return s.screen_id === screenId; })[0];
    if (!screen) screen = MODEL.screens[0];
    renderNav(screen.screen_id);
    var body = document.getElementById("screen-body");
    clear(body);
    body.appendChild(el("h1", "screen-title", screen.title));
    body.appendChild(el("p", "screen-question", screen.primary_question));

    /* Readable scan layer first; detailed audit sections render below it. */
    renderOperatorScanLayer(screen, body);

    switch (screen.screen_id) {
      case "command_center": renderCommandCenter(screen, body); break;
      case "content_studio": renderContentStudio(screen, body); break;
      case "publish_readiness": renderPublishReadiness(screen, body); break;
      case "evidence_vault": renderEvidenceVault(screen, body); break;
      case "content_calendar": renderContentCalendar(screen, body); break;
      case "visual_export": renderVisualExport(screen, body); break;
      case "settings_safety_policy": renderSettings(screen, body); break;
      default: break;
    }

    /* Sparse screens get a governed summary rail to remove lower dead-zone
       without inventing content. */
    var sparse = ["content_calendar", "visual_export", "settings_safety_policy", "publish_readiness"];
    if (sparse.indexOf(screen.screen_id) !== -1) {
      renderScreenSummaryRail(screen, body);
    }
  }

  /* --- Bootstrap --- */
  function init() {
    if (!MODEL) return;
    renderSafetyRail();
    renderTruthRail();
    renderFooter();
    renderScreen(MODEL.screens[0].screen_id);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

