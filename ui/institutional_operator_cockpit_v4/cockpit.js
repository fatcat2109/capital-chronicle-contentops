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

  /* --- Safety Rail ---
     Red is reserved for genuine danger (kill switch / live disabled). Every
     other governance lock renders as a neutral graphite chip so the strip reads
     as calm authority rather than an all-red alarm wall. */
  function renderSafetyRail() {
    var rail = document.getElementById("safety-rail");
    clear(rail);
    var dangerLocks = { "KILL SWITCH ACTIVE": true, "LIVE DISABLED": true };
    MODEL.safety_locks.critical.forEach(function (lbl) {
      rail.appendChild(el("span", "safety-chip" + (dangerLocks[lbl] ? " critical" : ""), lbl));
    });
    var cluster = el("span", "safety-locks-cluster",
      "SYSTEM LOCKS +" + MODEL.safety_locks.grouped_locks.length + ": " +
      MODEL.safety_locks.grouped_locks.join(" / "));
    rail.appendChild(cluster);
  }

  /* --- Truth Rail (progressive disclosure, 0174Z) ---
     Collapsed by default so first-open cognitive load stays low. The full
     current-vs-historical/provenance grid is preserved inside the disclosure
     body and reachable via the keyboard-accessible native summary control.
     No storage, no network, no auto-expand. */
  function renderTruthRail() {
    var rail = document.getElementById("truth-rail");
    clear(rail);

    var details = el("details", "truth-rail-disclosure");
    /* Collapsed on initial load: the `open` attribute is intentionally absent. */
    details.id = "truth-rail-disclosure";

    var summary = el("summary", "truth-rail-summary");
    summary.setAttribute("aria-label", "Show full operational truth metadata");

    var sum = MODEL.truth_rail_summary || {};
    var cue = el("span", "truth-summary-cue");
    cue.appendChild(el("span", "truth-summary-caret", "\u25B8"));
    cue.appendChild(el("span", "truth-summary-title", "Operational Truth"));
    summary.appendChild(cue);

    [["Product Head", sum.product_head],
     ["Gate", sum.gate],
     ["Next Action", sum.next_action],
     ["Safety / Live", sum.safety_status]
    ].forEach(function (pair) {
      if (!pair[1]) return;
      var cell = el("span", "truth-summary-cell");
      cell.appendChild(el("span", "truth-summary-label", pair[0]));
      cell.appendChild(el("span", "truth-summary-value", pair[1]));
      summary.appendChild(cell);
    });
    details.appendChild(summary);

    /* Full grid: identical content/structure to the prior rail, now nested. */
    var grid = el("div", "truth-grid");
    MODEL.truth_rail.forEach(function (cell) {
      var c = el("div", "truth-cell kind-" + cell.kind);
      c.appendChild(el("span", "role-label", cell.role_label));
      c.appendChild(el("span", "role-value", cell.value));
      grid.appendChild(c);
    });
    details.appendChild(grid);

    rail.appendChild(details);
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

  /* --- Drilldown panel (progressive disclosure, 0174AD) ---
     Reusable third-layer disclosure. Collapsed by default so dense audit
     detail (matrices, registries, provenance, dependency maps) is preserved
     and inspectable without dominating the first fold. Native details/summary,
     keyboard-accessible, no storage, no network, no auto-expand. */
  function drilldown(summaryLabel, hintText) {
    var details = el("details", "drilldown-panel section-gap");
    var summary = el("summary", "drilldown-summary");
    summary.appendChild(el("span", "drilldown-caret", "\u25B8"));
    summary.appendChild(el("span", "drilldown-title", summaryLabel));
    if (hintText) summary.appendChild(el("span", "drilldown-hint", hintText));
    details.appendChild(summary);
    var ddBody = el("div", "drilldown-body");
    details.appendChild(ddBody);
    return { details: details, body: ddBody };
  }

  /* --- Inspection command tiles (0174AF) ---
     Large, read-only command surfaces. Each tile is local UI navigation to an
     inspection screen — NOT an operational control. No publish/run/send/approve
     behavior, no network, no storage. */
  function renderInspectionCommands(body) {
    var row = el("div", "command-tile-row section-gap");
    var lanes = (MODEL.screens.filter(function (x) { return x.screen_id === "content_studio"; })[0] || {}).lanes || [];
    [["Inspect", "View Evidence Vault", "evidence_vault",
      MODEL.evidence_refs.length + " evidence refs · " + MODEL.blocker_stack.length + " blockers"],
     ["Inspect", "Inspect Publish Gate", "publish_readiness",
      "gate matrix · all platforms blocked"],
     ["Inspect", "Review Editorial Lanes", "content_studio",
      lanes.length + " lanes · review-only"]
    ].forEach(function (t) {
      var tile = el("div", "command-tile");
      tile.setAttribute("data-screen-link", t[2]);
      tile.appendChild(el("span", "command-tile-label", t[0]));
      tile.appendChild(el("span", "command-tile-title", t[1]));
      tile.appendChild(el("span", "command-tile-meta", t[3]));
      var open = el("button", "command-tile-cue");
      open.setAttribute("type", "button");
      open.textContent = "Open ›";
      open.setAttribute("aria-label", "Open " + t[1]);
      open.addEventListener("click", function (e) { e.stopPropagation(); renderScreen(t[2]); });
      tile.appendChild(open);
      makeSelectable(tile, inspectObject({
        kind: "command tile", id: t[2], label: t[1], state: "inspect-only",
        severity: "neutral", reason: t[3],
        allowed_local_action: t[0] + " (local navigation)",
        blocked_action: "publish / run / send" }));
      row.appendChild(tile);
    });
    body.appendChild(row);
  }

  /* --- Command Center --- */
  function renderCommandCenter(s, body) {
    /* Inspection command surfaces lead the executive cockpit, then the change
       ledger / blocker stack / proof ledger detail below. */
    renderInspectionCommands(body);

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
      makeSelectable(row, inspectObject({
        kind: "blocker", id: b.id, label: b.label, state: b.severity,
        severity: b.severity === "blocked" ? "blocked" : "review", reason: b.reason,
        evidence_refs: b.evidence_ref_ids, allowed_local_action: "Review Blocker",
        blocked_action: "publish / post / schedule" }));
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
    var depDd = drilldown("Evidence Dependency Map", "proof ledger · drilldown");
    depDd.body.appendChild(dep);
    body.appendChild(depDd.details);

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
    /* LaneHealthStrip (0174AE): screen-specific editorial-lane health summary.
       Computed only from existing lane data; no new capability, no market data. */
    var lanes = s.lanes || [];
    var reviewN = lanes.filter(function (l) { return l.status === "REVIEW_REQUIRED"; }).length;
    var blockedN = lanes.filter(function (l) { return l.status === "BLOCKED"; }).length;
    var citationN = lanes.filter(function (l) {
      return (l.limitations || []).some(function (x) { return /citation|source/i.test(x); });
    }).length;
    var forbiddenRiskN = lanes.filter(function (l) {
      return l.forbidden_language && !/^none detected/i.test(l.forbidden_language) && l.status !== "BLOCKED";
    }).length;
    var notPostableN = lanes.filter(function (l) { return l.not_public_postable; }).length;
    var strip = el("div", "lane-health-strip section-gap");
    [["Editorial lanes", String(lanes.length), "neutral"],
     ["Manual review", String(reviewN), "review"],
     ["Blocked / future-only", String(blockedN), "blocked"],
     ["Citation-dependent", String(citationN), "review"],
     ["Forbidden-language watch", String(forbiddenRiskN), "review"],
     ["Not public-postable", notPostableN === lanes.length ? "all" : String(notPostableN), "blocked"]
    ].forEach(function (m) {
      var cell = el("div", "lane-health-cell sev-" + m[2]);
      cell.appendChild(el("span", "lane-health-num", m[1]));
      cell.appendChild(el("span", "lane-health-label", m[0]));
      strip.appendChild(cell);
    });
    body.appendChild(strip);

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
      makeSelectable(p, inspectObject({
        kind: "content lane", id: lane.lane_id, label: lane.name, state: lane.status,
        severity: lane.status === "BLOCKED" ? "blocked" : "review",
        reason: (lane.limitations || []).join("; "), evidence_refs: lane.evidence_ref_ids,
        allowed_local_action: "Select Lane", blocked_action: "publish final copy / signal language",
        caveat: lane.forbidden_language }));
      grid.appendChild(p);
    });
    body.appendChild(grid);
  }

  /* --- Publish Readiness Tower (gate matrix first) --- */
  function renderPublishReadiness(s, body) {
    var g = MODEL.global_current_state || {};
    /* Dominant publish checkpoint (0174AE): single answer to "why can't anything
       publish?" with the hard locks, above the calm gate-summary strip. */
    var rv = s.readiness_verdict || {};
    var checkpoint = el("div", "publish-checkpoint section-gap");
    var cpHead = el("div", "publish-checkpoint-head");
    cpHead.appendChild(el("span", "publish-checkpoint-title", "No platform can publish"));
    cpHead.appendChild(el("span", "token " + (rv.status || "BLOCKED"), rv.status || "BLOCKED"));
    checkpoint.appendChild(cpHead);
    checkpoint.appendChild(el("div", "publish-checkpoint-reason readable-body-copy",
      rv.reason || "No platform has cleared the gate matrix; live adapter, scheduler, and posting are disabled."));
    var locks = el("div", "publish-lock-row");
    [["Live adapter", g.live_state], ["Scheduler", g.scheduler_state], ["Posting", g.live_state],
     ["Credential read", g.credential_read_state], ["Platform API", g.platform_api_state]
    ].forEach(function (pair) {
      var chip = el("div", "publish-lock-chip");
      chip.appendChild(el("span", "publish-lock-label", pair[0]));
      chip.appendChild(el("span", "publish-lock-state", pair[1] || "disabled"));
      makeSelectable(chip, inspectObject({
        kind: "publish gate", id: pair[0], label: pair[0], state: pair[1] || "disabled",
        severity: "blocked", reason: pair[0] + " is disabled by policy and kill switch.",
        evidence_refs: (rv.evidence_ref_ids || []), allowed_local_action: "Inspect Gate",
        blocked_action: "publish / posting / scheduler / credential read" }));
      locks.appendChild(chip);
    });
    checkpoint.appendChild(locks);
    body.appendChild(checkpoint);

    /* Composed gate-summary strip: a calm, institutional readout of the hard
       publishing locks above the dense matrix, built from canonical state. */
    var sumStrip = el("div", "gate-summary-strip section-gap");
    [["Live adapter", g.live_state || "disabled"],
     ["Scheduler", g.scheduler_state || "disabled"],
     ["Posting", g.live_state || "disabled"],
     ["Credential read", g.credential_read_state || "disabled"],
     ["Platform API", g.platform_api_state || "disabled"]
    ].forEach(function (pair) {
      var cell = el("div", "gate-summary-cell");
      cell.appendChild(el("span", "gate-summary-label", pair[0]));
      cell.appendChild(el("span", "gate-summary-value", pair[1]));
      sumStrip.appendChild(cell);
    });
    var nb = el("div", "gate-summary-cell gate-summary-blocker");
    nb.appendChild(el("span", "gate-summary-label", "Next blocker"));
    nb.appendChild(el("span", "gate-summary-value",
      s.readiness_verdict ? s.readiness_verdict.text : "Supervised publishing blocked"));
    sumStrip.appendChild(nb);
    body.appendChild(sumStrip);

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
    var gmDd = drilldown("Gate Matrix", "platform gate control · drilldown");
    gmDd.body.appendChild(mp);
    body.appendChild(gmDd.details);

    var rec = panel("Platform Readiness Records (inspect-only)");
    s.platform_records.forEach(function (p) {
      var row = el("div", "reg-row");
      row.appendChild(el("span", "reg-key", p.platform + " — allowed: " + p.allowed_now));
      row.appendChild(el("span", "reg-val", "forbidden: " + p.forbidden_now));
      rec.appendChild(row);
    });
    var recDd = drilldown("Platform Readiness Records", "inspect-only · drilldown");
    recDd.body.appendChild(rec);
    body.appendChild(recDd.details);
  }


  /* --- Evidence Vault (compliance room) --- */
  function renderEvidenceVault(s, body) {
    /* ConfidenceSurface (0174AE): institutional provenance readout above the
       detailed drilldowns. Computed from existing model data only. */
    var es = s.evidence_state || {};
    var passN = (s.validation_matrix || []).filter(function (r) { return r.status === "PASS"; }).length;
    var totalN = (s.validation_matrix || []).length;
    var blockingCav = (s.caveat_registry || []).filter(function (c) { return c.blocking; }).length;
    var currentEvents = (s.evidence_timeline || []).filter(function (e) { return e.classification === "current"; }).length;
    var surface = el("div", "confidence-surface section-gap");
    [["Evidence confidence", es.status === "PASS" ? "high (caveated)" : (es.status || "unknown"), "safe"],
     ["Lineage health", currentEvents + " current / " + (s.evidence_timeline || []).length + " tracked", "safe"],
     ["Validation state", passN + " / " + totalN + " PASS", passN === totalN ? "safe" : "review"],
     ["Recency / QA", "0174C capture · worker judgment caveat", "review"],
     ["Blocking caveats", String(blockingCav), blockingCav ? "blocked" : "safe"]
    ].forEach(function (m) {
      var cell = el("div", "confidence-cell sev-" + m[2]);
      cell.appendChild(el("span", "data-label", m[0]));
      cell.appendChild(el("span", "confidence-value", m[1]));
      makeSelectable(cell, inspectObject({
        kind: "evidence ref", id: m[0], label: m[0], state: m[1],
        severity: m[2], reason: m[0] + ": " + m[1],
        evidence_refs: (es.evidence_ref_ids || []), allowed_local_action: "View Evidence",
        blocked_action: "evidence mutation / export / upload",
        posture: /QA|Recency/i.test(m[0]) ? "historical" : "current" }));
      surface.appendChild(cell);
    });
    body.appendChild(surface);

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
    var vmDd = drilldown("Validation Matrix", "check / expected / observed · drilldown");
    vmDd.body.appendChild(mp);
    body.appendChild(vmDd.details);

    var tl = panel("Evidence Timeline");
    s.evidence_timeline.forEach(function (e) {
      var row = el("div", "reg-row");
      row.appendChild(el("span", "reg-key mono", e.commit + " — " + e.task));
      row.appendChild(el("span", "reg-val", e.classification));
      tl.appendChild(row);
    });
    var tlDd = drilldown("Evidence Timeline", "commit lineage · drilldown");
    tlDd.body.appendChild(tl);
    body.appendChild(tlDd.details);

    var grid = el("div", "grid grid-3 audit-registry audit-triad");
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
    var gridDd = drilldown("Evidence Registries", "caveat / forbidden-scope / blocker · drilldown");
    gridDd.body.appendChild(grid);
    body.appendChild(gridDd.details);

    var leg = panel("Evidence Confidence Legend");
    s.confidence_legend.forEach(function (l) { leg.appendChild(el("div", "muted", "• " + l)); });
    leg.classList.add("section-gap");
    body.appendChild(leg);

    var qa = el("div", "band sev-caution evidence-qa-caveat");
    qa.appendChild(el("span", "band-label", s.browser_qa_row.label));
    var qt = el("div", "band-text");
    qt.appendChild(el("span", "token DEGRADED", "PASS_WITH_CAVEAT"));
    qt.appendChild(document.createTextNode("  " + s.browser_qa_row.note));
    qa.appendChild(qt);
    body.appendChild(qa);
  }

  /* --- Content Calendar / Workflow --- */
  function renderContentCalendar(s, body) {

    /* Stage legend (manual states only). */
    var leg = el("div", "workflow-stage-legend section-gap");
    leg.appendChild(el("span", "data-label", "Manual stages"));
    s.allowed_states.forEach(function (st) { leg.appendChild(el("span", "stage-pill", st)); });
    body.appendChild(leg);

    /* WorkflowBoard (0174AE): kanban columns by allowed manual state.
       Items flattened from date_lanes; manual-only, no scheduler/auto-post. */
    var nextActionByState = {
      "idea": "shape angle / assign lane",
      "source-needed": "attach source + citation",
      "research-brief-ready": "draft for review",
      "draft-review": "manual editorial review",
      "blocked": "resolve blocker (no artifacts/lineage)",
      "operator-approved-for-manual": "operator manual post (off-system)",
      "manually-posted": "enter metrics manually",
      "metrics-entered": "archive / retro"
    };
    var sourceByState = {
      "idea": "not started",
      "source-needed": "missing",
      "research-brief-ready": "brief attached",
      "draft-review": "cited",
      "blocked": "unavailable"
    };
    var items = [];
    s.date_lanes.forEach(function (lane) {
      (lane.items || []).forEach(function (it) {
        items.push({ title: it.title, lane: it.lane, state: it.state, period: lane.period, evidence_ref: it.evidence_ref });
      });
    });
    var board = el("div", "manual-workflow-board workflow-board section-gap");
    s.allowed_states.forEach(function (state) {
      var colItems = items.filter(function (it) { return it.state === state; });
      var col = el("div", "workflow-column" + (state === "blocked" ? " col-blocked" : ""));
      var ch = el("div", "workflow-column-head");
      ch.appendChild(el("span", "workflow-column-title", state));
      ch.appendChild(el("span", "workflow-column-count", String(colItems.length)));
      col.appendChild(ch);
      if (!colItems.length) {
        col.appendChild(el("div", "workflow-empty", "—"));
      }
      colItems.forEach(function (it) {
        var card = el("div", "workflow-card" + (it.state === "blocked" ? " sev-blocked" : ""));
        card.appendChild(el("div", "workflow-card-title", it.title));
        var meta = el("div", "workflow-card-meta");
        meta.appendChild(el("span", "workflow-tag", "lane: " + it.lane));
        meta.appendChild(el("span", "workflow-tag", "source: " + (sourceByState[it.state] || "n/a")));
        meta.appendChild(el("span", "workflow-tag", it.period));
        card.appendChild(meta);
        var na = el("div", "workflow-card-next");
        na.appendChild(el("span", "data-label", "manual next"));
        na.appendChild(el("span", "workflow-next-value", nextActionByState[it.state] || "manual review"));
        card.appendChild(na);
        makeSelectable(card, inspectObject({
          kind: "workflow item", id: it.lane, label: it.title, state: it.state,
          severity: it.state === "blocked" ? "blocked" : "review",
          reason: "Manual workflow stage: " + it.state + " · source: " + (sourceByState[it.state] || "n/a"),
          evidence_refs: [it.evidence_ref], allowed_local_action: "Inspect Workflow Item",
          blocked_action: "schedule / auto-post / dispatch" }));
        col.appendChild(card);
      });
      board.appendChild(col);
    });
    body.appendChild(board);

    var locked = panel("Forbidden Automated States (disabled / future-only)");
    s.forbidden_states.forEach(function (f) {
      var row = el("div", "reg-row");
      row.appendChild(el("span", "reg-key muted", f.state + " — " + f.note));
      var rv = el("span", "reg-val"); rv.appendChild(el("span", "token " + f.status, f.status)); row.appendChild(rv);
      locked.appendChild(row);
    });
    var lockedDd = drilldown("Forbidden Automated States (disabled / future-only)", "policy-locked · drilldown");
    lockedDd.body.appendChild(locked);
    body.appendChild(lockedDd.details);
  }


  /* --- Visual Export / Screenshot-Safe --- */
  function renderVisualExport(s, body) {

    var cards = el("div", "grid grid-2 screenshot-prep-grid section-gap");
    s.report_cards.forEach(function (rc) {
      var p = el("div", "lane");
      p.appendChild(el("div", "lane-name", rc.surface + " — screenshot-safe report card"));
      var ul = el("ul");
      rc.labels.forEach(function (l) { ul.appendChild(el("li", null, "label: " + l)); });
      rc.redactions.forEach(function (r) { ul.appendChild(el("li", null, "redacts: " + r)); });
      p.appendChild(ul);
      p.appendChild(el("div", "token SECRET_REDACTED", "SCREENSHOT-SAFE"));
      makeSelectable(p, inspectObject({
        kind: "redaction proof", id: rc.card_id, label: rc.surface + " screenshot-safe card",
        state: "SCREENSHOT_SAFE", severity: "safe",
        reason: "Redacts: " + (rc.redactions || []).join(", ") + ". Fixture-only, no live secret.",
        allowed_local_action: "View Redaction Proof",
        blocked_action: "export / download / upload" }));
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
    var bfDd = drilldown("Blocked Forecast Explainer", "why forecasting is blocked · drilldown");
    bfDd.body.appendChild(bf);
    body.appendChild(bfDd.details);

    var ff = panel(s.failure_forensics_card.title);
    ff.appendChild(el("div", "muted", s.failure_forensics_card.note));
    var ffDd = drilldown("Failure Forensics", "post-mortem · drilldown");
    ffDd.body.appendChild(ff);
    body.appendChild(ffDd.details);
  }

  /* --- Settings / Safety Policy --- */
  function renderSettings(s, body) {

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
      makeSelectable(tr, inspectObject({
        kind: "policy group", id: r.policy, label: r.policy, state: r.value,
        severity: /disabled|prohibited/i.test(r.value) ? "blocked" : "safe",
        reason: r.enforcement + " — " + r.rationale, allowed_local_action: "Open Policy Group",
        blocked_action: "enable live / display credential" }));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody); wrap.appendChild(table); mp.appendChild(wrap);
    var pmDd = drilldown("Policy Matrix", "policy / enforcement / rationale · drilldown");
    pmDd.body.appendChild(mp);
    body.appendChild(pmDd.details);

    var reg = panel("Credential Never-Display Registry");
    s.credential_never_display_registry.forEach(function (c) {
      var row = el("div", "reg-row");
      row.appendChild(el("span", "reg-key", c.item));
      var rv = el("span", "reg-val"); rv.appendChild(el("span", "token SECRET_REDACTED", c.display)); row.appendChild(rv);
      makeSelectable(row, inspectObject({
        kind: "policy group", id: "cred-" + c.item, label: "Credential never-display: " + c.item,
        state: "SECRET_REDACTED", severity: "safe",
        reason: c.item + " is never displayed; secrets stay out-of-band.",
        allowed_local_action: "Open Policy Group", blocked_action: "display credential / read env" }));
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
    var fgDd = drilldown("Future Gate Requirements", "future-only gates · drilldown");
    fgDd.body.appendChild(fg);
    body.appendChild(fgDd.details);
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
    var layer = el("div", "operator-scan-layer" + (screen.screen_id === "command_center" ? " scan-primary" : ""));
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

    /* Primary reason: why the screen is in this state (verdict.reason). */
    if (verdict && verdict.reason) {
      var pr = el("div", "primary-reason scan-reason readable-body-copy");
      pr.appendChild(el("span", "scan-label", "Reason"));
      pr.appendChild(el("span", "scan-value", verdict.reason));
      board.appendChild(pr);
    }

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

  /* --- Density toggle (0174AF) ---
     Local-only read-only UI interaction. Switches first-fold spacing/type
     density between comfortable (default, premium readability) and compact
     (denser inspection). No storage, no network, no operational effect. */
  var currentDensity = "comfortable";
  function renderDensityToggle(body) {
    var row = el("div", "density-toggle-row");
    row.appendChild(el("span", "density-label", "Density"));
    var group = el("div", "density-toggle");
    group.setAttribute("role", "group");
    group.setAttribute("aria-label", "Inspection density (local view only)");
    [["comfortable", "Comfortable"], ["compact", "Compact"]].forEach(function (opt) {
      var b = el("button", "density-option", opt[1]);
      b.setAttribute("type", "button");
      b.setAttribute("data-density", opt[0]);
      b.setAttribute("aria-pressed", currentDensity === opt[0] ? "true" : "false");
      b.addEventListener("click", function () {
        currentDensity = opt[0];
        var sb = document.getElementById("screen-body");
        sb.classList.remove("density-comfortable", "density-compact");
        sb.classList.add("density-" + currentDensity);
        group.querySelectorAll(".density-option").forEach(function (o) {
          o.setAttribute("aria-pressed", o.getAttribute("data-density") === currentDensity ? "true" : "false");
        });
      });
      group.appendChild(b);
    });
    row.appendChild(group);
    body.appendChild(row);
  }

  /* --- Object-centric inspection registry (0174AI) ---
     Deterministic selected-object model. Normalizes existing MODEL items into a
     canonical inspectable shape. Local-only: selection updates UI state and the
     inspector rail; it performs no network, no storage, no operational action. */
  var SELECTED_OBJECT = null;   // canonical selected object (null = summary mode)
  var ACTIVE_SCREEN = null;     // current screen object
  var INSPECTOR_NODE = null;    // current inspector rail container

  /* Canonical inspectable-object factory. Only kind/label are required. */
  function inspectObject(o) {
    return {
      kind: o.kind || "object",
      id: o.id || "",
      label: o.label || "",
      state: o.state || "",
      severity: o.severity || "neutral",
      reason: o.reason || "",
      evidence_refs: o.evidence_refs || [],
      allowed_local_action: o.allowed_local_action || "Inspect",
      blocked_action: o.blocked_action || "",
      caveat: o.caveat || "",
      posture: o.posture || "current"
    };
  }

  /* Mark a DOM node as a local inspection surface for a canonical object. */
  function makeSelectable(node, obj) {
    node.classList.add("selectable-object");
    if (node.tagName !== "BUTTON") {
      node.setAttribute("role", "button");
      node.setAttribute("tabindex", "0");
    }
    node.setAttribute("aria-label", "Inspect " + obj.kind + ": " + obj.label);
    node.setAttribute("aria-pressed", "false");
    function fire(e) { if (e) e.preventDefault(); selectObject(obj, node); }
    node.addEventListener("click", fire);
    node.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " " || e.key === "Spacebar") fire(e);
    });
    return node;
  }

  /* Select an object: update state, sync selected visual state, re-render rail. */
  function selectObject(obj, node) {
    SELECTED_OBJECT = obj;
    var prior = document.querySelectorAll(".selectable-object.selected");
    for (var i = 0; i < prior.length; i++) {
      prior[i].classList.remove("selected");
      prior[i].setAttribute("aria-pressed", "false");
    }
    if (node) { node.classList.add("selected"); node.setAttribute("aria-pressed", "true"); }
    if (INSPECTOR_NODE && ACTIVE_SCREEN) {
      clear(INSPECTOR_NODE);
      renderInspectorRail(ACTIVE_SCREEN, INSPECTOR_NODE);
    }
  }

  /* Build the default selected object for a screen from existing MODEL data. */
  function defaultObjectForScreen(screen) {
    var sid = screen.screen_id;
    if (sid === "command_center") {
      var b = MODEL.blocker_stack[0] || {};
      return inspectObject({ kind: "blocker", id: b.id, label: b.label,
        state: b.severity, severity: b.severity === "blocked" ? "blocked" : "review",
        reason: b.reason, evidence_refs: b.evidence_ref_ids,
        allowed_local_action: "Review Blocker", blocked_action: "publish / post / schedule" });
    }
    if (sid === "content_studio") {
      var lanes = screen.lanes || [];
      var lane = lanes.filter(function (l) { return l.status === "BLOCKED"; })[0] || lanes[0] || {};
      return inspectObject({ kind: "content lane", id: lane.lane_id, label: lane.name,
        state: lane.status, severity: lane.status === "BLOCKED" ? "blocked" : "review",
        reason: (lane.limitations || []).join("; "), evidence_refs: lane.evidence_ref_ids,
        allowed_local_action: "Select Lane", blocked_action: "publish final copy",
        caveat: lane.forbidden_language });
    }
    if (sid === "publish_readiness") {
      var rv = screen.readiness_verdict || {};
      return inspectObject({ kind: "publish gate", id: "gate-checkpoint", label: "No platform can publish",
        state: rv.status, severity: "blocked", reason: rv.reason, evidence_refs: rv.evidence_ref_ids,
        allowed_local_action: "Inspect Gate", blocked_action: "publish / posting / scheduler" });
    }
    if (sid === "evidence_vault") {
      var cav = (screen.caveat_registry || [])[0] || {};
      return inspectObject({ kind: "QA caveat", id: cav.caveat_id, label: "0174C Browser QA caveat",
        state: "historical", severity: "review", reason: cav.note,
        evidence_refs: [cav.source_evidence], allowed_local_action: "View Evidence",
        blocked_action: "evidence mutation / export",
        caveat: "Worker visual judgment rejected; capture accepted", posture: "historical" });
    }
    if (sid === "content_calendar") {
      var items = [];
      (screen.date_lanes || []).forEach(function (l) { (l.items || []).forEach(function (it) { items.push(it); }); });
      var it = items.filter(function (x) { return x.state === "blocked"; })[0] || items[0] || {};
      return inspectObject({ kind: "workflow item", id: it.lane, label: it.title,
        state: it.state, severity: it.state === "blocked" ? "blocked" : "review",
        reason: "Manual workflow stage: " + it.state, evidence_refs: [it.evidence_ref],
        allowed_local_action: "Inspect Workflow Item", blocked_action: "schedule / auto-post" });
    }
    if (sid === "visual_export") {
      return inspectObject({ kind: "redaction proof", id: "redaction", label: "Screenshot-safe redaction proof",
        state: "SCREENSHOT_SAFE", severity: "safe",
        reason: "Secrets are SECRET_REDACTED; surface is fixture-only.",
        evidence_refs: (screen.export_state || {}).evidence_ref_ids,
        allowed_local_action: "View Redaction Proof", blocked_action: "export / download / upload" });
    }
    if (sid === "settings_safety_policy") {
      return inspectObject({ kind: "policy group", id: "credential-never-display", label: "Credential never-display",
        state: "PASS", severity: "safe",
        reason: "Credentials and env are never displayed; secrets stay out-of-band.",
        evidence_refs: (screen.policy_state || {}).evidence_ref_ids,
        allowed_local_action: "Open Policy Group", blocked_action: "display credential / enable live" });
    }
    return null;
  }

  /* Render the selected-object institutional detail + compact evidence path. */
  function renderSelectedObjectDetail(obj, rail) {
    var box = el("div", "selected-object-detail sev-" + (obj.severity || "neutral"));
    var h = el("div", "selected-object-head");
    h.appendChild(el("span", "selected-object-kind", obj.kind));
    if (obj.state) h.appendChild(el("span", "token " + obj.state, obj.state));
    box.appendChild(h);
    box.appendChild(el("div", "selected-object-label", obj.label));
    function row(label, value) {
      if (!value) return;
      var r = el("div", "selected-object-row");
      r.appendChild(el("span", "selected-object-row-label", label));
      r.appendChild(el("span", "selected-object-row-value", value));
      box.appendChild(r);
    }
    row("Why", obj.reason);
    row("Allowed (local)", obj.allowed_local_action);
    row("Blocked", obj.blocked_action);
    row("Caveat", obj.caveat);
    row("Posture", obj.posture);
    var refs = (obj.evidence_refs || []).map(evidenceRefId).filter(Boolean);
    if (refs.length) {
      var trace = el("div", "evidence-path");
      trace.appendChild(el("span", "evidence-path-label", "Evidence path"));
      var chain = el("div", "evidence-path-chain");
      chain.appendChild(el("span", "evidence-path-node", obj.kind));
      refs.forEach(function (r) {
        chain.appendChild(el("span", "evidence-path-arrow", "\u2192"));
        chain.appendChild(el("span", "evidence-chip", r));
      });
      trace.appendChild(chain);
      box.appendChild(trace);
    }
    rail.appendChild(box);
  }

  /* --- Screen-specific inspector rail (0174AH) ---
     Read-only, high-signal, purpose-built per screen. Built only from existing
     model data — no new capability, no operational control, no dump. Each screen
     answers its own institutional questions instead of a generic template. */
  function renderInspectorRail(screen, rail) {
    var head = el("div", "inspector-head");
    head.appendChild(el("span", "inspector-eyebrow", SELECTED_OBJECT ? "Selected object" : "Inspector"));
    head.appendChild(el("span", "inspector-screen", screen.screen_id));
    rail.appendChild(head);

    /* Selected-object detail mode (0174AI): lead with the selected object's
       institutional detail + evidence path, then the screen summary below. */
    if (SELECTED_OBJECT) renderSelectedObjectDetail(SELECTED_OBJECT, rail);

    function card(label, value, sevClass, mono) {
      var c = el("div", "inspector-card" + (sevClass ? " sev-" + sevClass : ""));
      c.appendChild(el("span", "inspector-card-label", label));
      c.appendChild(el("div", "inspector-card-value" + (mono ? " mono" : ""), value));
      rail.appendChild(c);
      return c;
    }
    function disabledLocks() {
      var g = MODEL.global_current_state || {};
      var lc = el("div", "inspector-card sev-blocked");
      lc.appendChild(el("span", "inspector-card-label", "Disabled (cannot run)"));
      [["Live adapter", g.live_state], ["Scheduler", g.scheduler_state],
       ["Posting", g.live_state], ["Credential read", g.credential_read_state],
       ["Platform API", g.platform_api_state]
      ].forEach(function (pair) {
        var row = el("div", "inspector-lock-row");
        row.appendChild(el("span", "lock-key", pair[0]));
        row.appendChild(el("span", "lock-val", pair[1] || "disabled"));
        lc.appendChild(row);
      });
      rail.appendChild(lc);
    }
    function evidenceRefsValue(n) {
      return MODEL.evidence_refs.slice(0, n).map(evidenceRefId).filter(Boolean).join(" · ") || "—";
    }

    var sid = screen.screen_id;

    if (sid === "command_center") {
      var v = screen.verdict || {};
      var top = MODEL.blocker_stack[0] || {};
      var cnt = screen.safety_counters || {};
      card("Active decision", (v.label || "Verdict") + " · " + (v.status || "BLOCKED"), "blocked");
      card("Priority blocker", top.id + " · " + top.label, top.severity === "blocked" ? "blocked" : "review");
      card("Evidence confidence", MODEL.evidence_refs.length + " refs · validation PASS", "safe", true);
      card("Operator next action", (v.allowed_actions || []).join(" · ") || "inspect", null);
      card("Safety locks", (cnt.locks_active || 13) + " active · live disabled", "blocked");
      card("Recent change", (screen.what_changed && screen.what_changed[0]) || "—", null);
    } else if (sid === "publish_readiness") {
      var rv = screen.readiness_verdict || {};
      card("Gate checkpoint", "No platform can publish · " + (rv.status || "BLOCKED"), "blocked");
      card("Next blocker", rv.text || "Supervised publishing blocked", "blocked");
      card("Gate matrix", (screen.gate_matrix || []).length + " platforms · all gates blocked", "blocked", true);
      disabledLocks();
    } else if (sid === "evidence_vault") {
      var es = screen.evidence_state || {};
      var vm = screen.validation_matrix || [];
      var passN = vm.filter(function (r) { return r.status === "PASS"; }).length;
      var tl = screen.evidence_timeline || [];
      var currentN = tl.filter(function (e) { return e.classification === "current"; }).length;
      var blkCav = (screen.caveat_registry || []).filter(function (c) { return c.blocking; }).length;
      card("Evidence confidence", es.status === "PASS" ? "high (caveated)" : (es.status || "unknown"), "safe");
      card("Validation state", passN + " / " + vm.length + " PASS", passN === vm.length ? "safe" : "review", true);
      card("Lineage health", currentN + " current / " + tl.length + " tracked", "safe", true);
      card("QA caveat (historical)", "0174C capture accepted; worker visual judgment rejected", "review");
      card("Blocking caveats", String(blkCav), blkCav ? "blocked" : "safe", true);
    } else if (sid === "content_studio") {
      var lanes = screen.lanes || [];
      var reviewN = lanes.filter(function (l) { return l.status === "REVIEW_REQUIRED"; }).length;
      var blockedN = lanes.filter(function (l) { return l.status === "BLOCKED"; }).length;
      var citationN = lanes.filter(function (l) {
        return (l.limitations || []).some(function (x) { return /citation|source/i.test(x); });
      }).length;
      var forbiddenN = lanes.filter(function (l) {
        return l.forbidden_language && !/^none detected/i.test(l.forbidden_language) && l.status !== "BLOCKED";
      }).length;
      card("Dominant lane state", (screen.studio_state || {}).status || "REVIEW_REQUIRED", "review");
      card("Manual review queue", reviewN + " of " + lanes.length + " lanes", "review", true);
      card("Citation-dependent", citationN + " lanes", citationN ? "review" : "safe", true);
      card("Forbidden-language watch", forbiddenN + " lanes flagged", forbiddenN ? "review" : "safe", true);
      card("Future artifact-backed", blockedN + " blocked (no artifacts)", "blocked", true);
      card("Public posture", "not public-postable", "blocked");
    } else if (sid === "content_calendar") {
      var items = [];
      (screen.date_lanes || []).forEach(function (l) { (l.items || []).forEach(function (it) { items.push(it); }); });
      var blockedItems = items.filter(function (it) { return it.state === "blocked"; }).length;
      card("Plan state", (screen.plan_state || {}).status || "REVIEW_REQUIRED", "review");
      card("Workflow items", items.length + " tracked · manual only", null, true);
      card("Blocked items", String(blockedItems), blockedItems ? "blocked" : "safe", true);
      card("Manual next", "manual review / draft (no scheduler)", null);
      card("Automation", "scheduler & auto-post disabled (future-only)", "blocked");
    } else if (sid === "visual_export") {
      var ex = screen.export_state || {};
      card("Capture state", ex.status || "SCREENSHOT_SAFE", "safe");
      card("Redaction proof", (screen.redaction_preview || []).length + " secrets SECRET_REDACTED", "safe", true);
      card("Briefing package", (screen.report_cards || []).length + " screenshot-safe cards", "safe", true);
      card("Export posture", "no export / download / upload", "blocked");
      card("Forecast / data", (screen.forecast_readiness_placeholder || {}).status || "FUTURE_ONLY", "blocked");
    } else if (sid === "settings_safety_policy") {
      var ps = screen.policy_state || {};
      card("Active policy state", ps.status || "PASS", "safe");
      card("Runtime boundaries", "network / live / scheduler / API disabled", "blocked");
      card("Content boundaries", "no advice · no signal · no targets", "review");
      card("Credential never-display", (screen.credential_never_display_registry || []).length + " items · SECRET_REDACTED", "safe", true);
      card("Platform gates", (screen.future_gate_requirements || []).length + " future-only gates", "blocked", true);
      card("Redaction posture", "secrets stay out-of-band", "safe");
    } else {
      var fb = screen.verdict || screen.policy_state || {};
      card("Current state", (fb.label || screen.title) + (fb.status ? " · " + fb.status : ""), "safe");
      card("Evidence backing", evidenceRefsValue(5), null, true);
      disabledLocks();
    }
  }

  /* --- Screen dispatcher --- */
  function renderScreen(screenId) {
    var screen = MODEL.screens.filter(function (s) { return s.screen_id === screenId; })[0];
    if (!screen) screen = MODEL.screens[0];
    renderNav(screen.screen_id);
    var body = document.getElementById("screen-body");
    clear(body);
    body.classList.remove("density-comfortable", "density-compact");
    body.classList.add("density-" + currentDensity);
    body.appendChild(el("h1", "screen-title", screen.title));
    body.appendChild(el("p", "screen-question", screen.primary_question));
    renderDensityToggle(body);

    /* Readable scan layer first (primary command zone, full width). */
    renderOperatorScanLayer(screen, body);

    /* Workspace shell: main work surface + read-only inspector rail. */
    var shell = el("div", "workspace-shell");
    var work = el("div", "work-surface");
    var inspector = el("div", "inspector-rail");
    shell.appendChild(work);
    shell.appendChild(inspector);
    body.appendChild(shell);

    /* Object-centric state (0174AI): default selected object per screen. */
    ACTIVE_SCREEN = screen;
    INSPECTOR_NODE = inspector;
    SELECTED_OBJECT = defaultObjectForScreen(screen);

    switch (screen.screen_id) {
      case "command_center": renderCommandCenter(screen, work); break;
      case "content_studio": renderContentStudio(screen, work); break;
      case "publish_readiness": renderPublishReadiness(screen, work); break;
      case "evidence_vault": renderEvidenceVault(screen, work); break;
      case "content_calendar": renderContentCalendar(screen, work); break;
      case "visual_export": renderVisualExport(screen, work); break;
      case "settings_safety_policy": renderSettings(screen, work); break;
      default: break;
    }

    /* Sparse screens get a governed summary rail to remove lower dead-zone. */
    var sparse = ["content_calendar", "visual_export", "settings_safety_policy", "publish_readiness"];
    if (sparse.indexOf(screen.screen_id) !== -1) {
      renderScreenSummaryRail(screen, work);
    }

    renderInspectorRail(screen, inspector);
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

