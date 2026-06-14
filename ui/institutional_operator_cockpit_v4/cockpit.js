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

  /* --- Footer / status dock (0174AM-D) ---
     Calm, discrete status cells instead of one long repeated action line. The
     full next-action text already lives in the scan layer; the dock keeps only
     compact current-truth anchors so the bottom rail reads as quiet chrome. */
  function renderFooter() {
    var footer = document.getElementById("cockpit-footer");
    clear(footer);
    footer.classList.add("audit-footer", "status-dock");
    var sum = MODEL.truth_rail_summary || {};
    var head = (sum.product_head || "").split(" / ")[0] || "—";
    var nextShort = MODEL.truth_rail.filter(function (t) { return t.role_label === "Next Allowed Action"; })[0];
    var nextLabel = nextShort ? (nextShort.value.split(".")[0]) : "";
    var cells = [
      ["mono", "Product HEAD", head],
      [null, "Next allowed action", nextLabel],
      [null, "Safety", "live · API · scheduler disabled · kill switch active"]
    ];
    cells.forEach(function (c, i) {
      if (i > 0) footer.appendChild(el("span", "dock-divider"));
      var cell = el("span", "dock-cell");
      cell.appendChild(el("span", "dock-label", c[1]));
      cell.appendChild(el("span", "dock-value" + (c[0] === "mono" ? " mono" : ""), c[2]));
      footer.appendChild(cell);
    });
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
      var open = el("button", "command-tile-cue inspect-affordance");
      open.setAttribute("type", "button");
      open.textContent = "Inspect ›";
      open.setAttribute("aria-label", "Inspect " + t[1]);
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
  function renderDecisionSpine(s, body) {
    /* Executive decision spine (0174AJ). Composed only from existing verdict /
       blocker / counter data. Decisive operator answer, not a report grid. */
    var v = s.verdict || {};
    var top = MODEL.blocker_stack[0] || {};
    var g = MODEL.global_current_state || {};
    var spine = el("div", "decision-spine sev-" + (v.severity || "blocked"));

    var head = el("div", "decision-spine-head");
    head.appendChild(el("span", "decision-spine-eyebrow", "Decision"));
    head.appendChild(el("span", "token " + (v.status || "BLOCKED"), v.status || "BLOCKED"));
    spine.appendChild(head);
    spine.appendChild(el("div", "decision-spine-verdict", v.text || v.label || "Nothing may proceed to publishing."));
    var spineObj = inspectObject({ kind: "decision", id: "command-verdict",
      label: (v.label || "Current Verdict") + " · " + (v.status || "BLOCKED"),
      state: v.status, severity: v.severity || "blocked", reason: v.reason,
      evidence_refs: v.evidence_ref_ids, allowed_local_action: (v.allowed_actions || []).join(" · ") || "inspect",
      blocked_action: (v.blocked_actions || []).join(" · ") });
    makeSelectable(head, spineObj);

    var grid = el("div", "decision-spine-grid");
    function spineCell(label, value, sev, obj) {
      var cell = el("div", "decision-cell" + (sev ? " sev-" + sev : ""));
      cell.appendChild(el("span", "decision-cell-label", label));
      cell.appendChild(el("span", "decision-cell-value", value));
      if (obj) makeSelectable(cell, obj);
      grid.appendChild(cell);
    }
    spineCell("Top blocker", top.id + " · " + top.label,
      top.severity === "blocked" ? "blocked" : "review",
      inspectObject({ kind: "blocker", id: top.id, label: top.label, state: top.severity,
        severity: top.severity === "blocked" ? "blocked" : "review", reason: top.reason,
        evidence_refs: top.evidence_ref_ids, allowed_local_action: "Review Blocker",
        blocked_action: "publish / post / schedule" }));
    spineCell("Evidence", MODEL.evidence_refs.length + " refs · validation PASS", "safe");
    spineCell("Allowed (local)", (v.allowed_actions || ["inspect"]).join(" · "), null);
    spineCell("Disabled surfaces", "live · API · scheduler · posting · credential", "blocked");
    spineCell("Recent delta", (s.what_changed && s.what_changed[0]) || "—", null);
    spine.appendChild(grid);
    body.appendChild(spine);
  }

  function renderCommandCenter(s, body) {
    /* Executive decision spine leads the flagship; inspection command surfaces
       and the change ledger / blocker board / proof ledger follow below. */
    renderDecisionSpine(s, body);
    renderEvidenceSurfaceSummary(body);
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

    /* ReviewQueue choreography (0174AM-A): lead with the single highest-priority
       object the operator must act on, then a severity-ranked pipeline. Built
       only from existing lane data — no new capability, no market data. */
    function laneSeverity(l) { return l.status === "BLOCKED" ? 0 : (l.status === "REVIEW_REQUIRED" ? 1 : 2); }
    function laneSevClass(l) { return l.status === "BLOCKED" ? "blocked" : (l.status === "REVIEW_REQUIRED" ? "review" : "safe"); }
    var ranked = lanes.slice().sort(function (a, b) {
      var d = laneSeverity(a) - laneSeverity(b);
      return d !== 0 ? d : (a.name || "").localeCompare(b.name || "");
    });
    var primaryLane = ranked[0] || {};
    var queue = el("div", "review-queue section-gap");

    var prim = el("div", "review-queue-primary");
    prim.appendChild(el("span", "rq-eyebrow", "Top of review queue"));
    var rqTitle = el("div", "rq-title");
    rqTitle.appendChild(document.createTextNode(primaryLane.name || "Editorial lane"));
    rqTitle.appendChild(el("span", "token " + (primaryLane.status || "REVIEW_REQUIRED"), primaryLane.status || "REVIEW_REQUIRED"));
    prim.appendChild(rqTitle);
    prim.appendChild(el("div", "rq-reason readable-body-copy",
      (primaryLane.limitations || []).join("; ") || "Manual review required before this lane can proceed."));
    var rqMeta = el("div", "review-queue-meta");
    [["claim risk", primaryLane.claim_risk], ["platform", primaryLane.platform_fit],
     ["forbidden-language", primaryLane.forbidden_language]
    ].forEach(function (m) {
      if (!m[1]) return;
      rqMeta.appendChild(el("span", "rq-chip", m[0] + ": " + m[1]));
    });
    prim.appendChild(rqMeta);
    makeSelectable(prim, inspectObject({
      kind: "content lane", id: primaryLane.lane_id, label: primaryLane.name, state: primaryLane.status,
      severity: laneSevClass(primaryLane), reason: (primaryLane.limitations || []).join("; "),
      evidence_refs: primaryLane.evidence_ref_ids, allowed_local_action: "Select Lane",
      blocked_action: "publish final copy / signal language", caveat: primaryLane.forbidden_language }));
    queue.appendChild(prim);

    var pipeline = el("div", "risk-pipeline");
    ranked.forEach(function (lane, i) {
      var row = el("div", "pipeline-row sev-" + laneSevClass(lane));
      row.appendChild(el("span", "pipeline-rank", String(i + 1)));
      var main = el("div", "pipeline-main");
      main.appendChild(el("span", "pipeline-name", lane.name));
      main.appendChild(el("span", "pipeline-class", "claim risk: " + (lane.claim_risk || "n/a")));
      row.appendChild(main);
      var risk = el("div", "pipeline-risk");
      risk.appendChild(el("span", "pipeline-risk-label", "forbidden-language"));
      risk.appendChild(el("span", "pipeline-risk-value", lane.forbidden_language || "—"));
      row.appendChild(risk);
      var tok = el("div"); tok.appendChild(el("span", "token " + lane.status, lane.status));
      row.appendChild(tok);
      makeSelectable(row, inspectObject({
        kind: "content lane", id: lane.lane_id, label: lane.name, state: lane.status,
        severity: laneSevClass(lane), reason: (lane.limitations || []).join("; "),
        evidence_refs: lane.evidence_ref_ids, allowed_local_action: "Select Lane",
        blocked_action: "publish final copy / signal language", caveat: lane.forbidden_language }));
      pipeline.appendChild(row);
    });
    queue.appendChild(pipeline);
    body.appendChild(queue);

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

    renderEvidenceSurfaceNoGrant(body);
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

    /* ProvenanceChain (0174AM-B): a visible evidence -> caveat -> registry trace
       so the audit lineage is scannable before the dense drilldowns. Built only
       from existing model data; no new capability, no export. */
    var firstCav = (s.caveat_registry || [])[0] || {};
    var firstReg = (s.active_blocker_registry || [])[0] || {};
    var chainStages = [
      { step: "01", label: "Evidence source", value: (es.evidence_ref_ids || []).join(" · ") || "—", sev: "safe",
        obj: inspectObject({ kind: "evidence ref", id: "evidence-source", label: "Evidence source",
          state: es.status, severity: "safe", reason: es.reason, evidence_refs: es.evidence_ref_ids,
          allowed_local_action: "View Evidence", blocked_action: "evidence mutation / export" }) },
      { step: "02", label: "Validation", value: passN + " / " + totalN + " PASS", sev: passN === totalN ? "safe" : "review",
        obj: inspectObject({ kind: "evidence ref", id: "validation", label: "Validation state",
          state: passN + "/" + totalN + " PASS", severity: passN === totalN ? "safe" : "review",
          reason: "External-dependency, current-state, forbidden-control, and secret scans.",
          allowed_local_action: "View Evidence", blocked_action: "evidence mutation" }) },
      { step: "03", label: "Caveat", value: firstCav.caveat_id ? (firstCav.caveat_id + " · " + (firstCav.blocking ? "blocking" : "non-blocking")) : "none", sev: firstCav.blocking ? "blocked" : "review",
        obj: inspectObject({ kind: "QA caveat", id: firstCav.caveat_id, label: firstCav.caveat_id || "Caveat",
          state: "historical", severity: firstCav.blocking ? "blocked" : "review", reason: firstCav.note,
          evidence_refs: [firstCav.source_evidence], allowed_local_action: "View Evidence",
          blocked_action: "evidence mutation", posture: "historical" }) },
      { step: "04", label: "Active blocker", value: firstReg.id ? (firstReg.id + " · " + firstReg.status) : "none", sev: /LIVE_DISABLED|BLOCKED/.test(firstReg.status || "") ? "blocked" : "review",
        obj: inspectObject({ kind: "blocker", id: firstReg.id, label: firstReg.label,
          state: firstReg.status, severity: "review", reason: firstReg.label,
          allowed_local_action: "Review Blocker", blocked_action: "publish / post / schedule" }) }
    ];
    var chain = el("div", "provenance-chain section-gap");
    chainStages.forEach(function (st, i) {
      if (i > 0) chain.appendChild(el("div", "provenance-arrow", "\u2192"));
      var stage = el("div", "provenance-stage sev-" + st.sev);
      stage.appendChild(el("span", "provenance-step", st.step));
      stage.appendChild(el("span", "provenance-stage-label", st.label));
      stage.appendChild(el("span", "provenance-stage-value", st.value));
      makeSelectable(stage, st.obj);
      chain.appendChild(stage);
    });
    body.appendChild(chain);

    renderEvidenceSurfaceHost(body);

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
    /* WorkflowPriorityRail (0174AM-C): choreograph the two items that matter —
       the top blocked item and the next actionable item — above the full board.
       Manual-only; no scheduler, no auto-post. */
    var blockedItem = items.filter(function (it) { return it.state === "blocked"; })[0];
    var nextItem = items.filter(function (it) { return it.state !== "blocked"; }).sort(function (a, b) {
      var order = s.allowed_states;
      return order.indexOf(a.state) - order.indexOf(b.state);
    })[0];
    var prioRail = el("div", "workflow-priority-rail section-gap");
    function prioritySlot(kind, modifier, item) {
      var slot = el("div", "priority-slot " + modifier);
      slot.appendChild(el("span", "priority-slot-eyebrow", kind));
      if (!item) { slot.appendChild(el("div", "priority-slot-next", "None at this stage.")); return slot; }
      slot.appendChild(el("div", "priority-slot-title", item.title));
      var meta = el("div", "priority-slot-meta");
      meta.appendChild(el("span", "ps-chip", "lane: " + item.lane));
      meta.appendChild(el("span", "ps-chip", "state: " + item.state));
      meta.appendChild(el("span", "ps-chip", item.period));
      slot.appendChild(meta);
      var na = el("div", "priority-slot-next");
      na.appendChild(el("span", "data-label", "manual next "));
      na.appendChild(document.createTextNode(nextActionByState[item.state] || "manual review"));
      slot.appendChild(na);
      makeSelectable(slot, inspectObject({
        kind: "workflow item", id: item.lane, label: item.title, state: item.state,
        severity: item.state === "blocked" ? "blocked" : "review",
        reason: "Manual workflow stage: " + item.state,
        evidence_refs: [item.evidence_ref], allowed_local_action: "Inspect Workflow Item",
        blocked_action: "schedule / auto-post / dispatch" }));
      return slot;
    }
    prioRail.appendChild(prioritySlot("Blocked — resolve first", "slot-blocked", blockedItem));
    prioRail.appendChild(prioritySlot("Next manual action", "slot-next", nextItem));
    body.appendChild(prioRail);

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

    renderEvidenceSurfaceBoundary(body);
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
    var layer = el("div", "operator-scan-layer" + (screen.screen_id === "command_center" ? " scan-primary" : " scan-compact"));
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

    /* Surface-derived selection (0174BU): show evidence-surface cards instead
       of the per-screen template. Read-only; no grant, no operational control. */
    if (SELECTED_OBJECT && SELECTED_OBJECT.kind === "evidence surface") {
      var sv = surfaceIntegrity();
      var hm = surfaceField("hostile_matrix_summary", {});
      var truthHm = truthField("hostile_matrix_summary", {});
      card("Surface summary", truthField("surface_id", surfaceField("surface_id", "UNKNOWN")) + " / " +
        truthField("availability", "UNKNOWN") + " / integrity " + truthField("integrity_state", sv.state),
        sv.state === "PASS" ? "safe" : (sv.state === "BLOCKED" ? "blocked" : "review"));
      card("No-grant label", surfaceField("no_grant_label", NO_GRANT_LABEL), "safe");
      card("Bridge report", surfaceField("bridge_report_id", "UNKNOWN") + " / " +
        truthField("bridge_report_hash", surfaceField("bridge_report_hash", "UNKNOWN")), "safe", true);
      card("Readiness alignment", truthField("readiness_alignment_id", "UNKNOWN") +
        " / readiness_granted=false", "blocked", true);
      card("Audit alignment", truthField("audit_alignment_id", "UNKNOWN") +
        " / audit_event_created=false / allowlist_modified=false", "blocked", true);
      card("Required-false groups", flagGroups().map(function (g) { return g.category; }).join(" / "), "blocked", true);
      card("Hostile matrix group", "never_pass=" + (truthHm.never_pass || hm.never_pass) +
        " / cases=" + ((truthHm.cases || []).length || hm.total_cases || 0), "safe", true);
      card("Fallback/missing bridge state", truthField("fallback_reason", "") ||
        "Bridge present; missing bridge would render UNKNOWN / no-grant.", "review");
      card("No-grant matrix", "public/live/dispatch/API/credential/scheduler/audit/readiness all blocked", "blocked");
      card("Blocked actions", truthField("blocked_actions", surfaceField("blocked_actions", [])).length +
        " / publish / dispatch / credential read", "blocked", true);
      return;
    }

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

  /* =====================================================================
   * Operator Evidence Surface integration (0174BU).
   * Wires the frozen Prep02 bridge global window.CC_OPERATOR_EVIDENCE_SURFACE
   * into the cockpit as an additive, evidence-only, no-grant surface. The
   * bridge is trusted-but-verified: surfaceIntegrity() re-checks the no-grant
   * invariants locally so a missing or tampered global can never produce a
   * false grant. Local-only: no network, no storage, no operational action.
   * ===================================================================== */
  var SURFACE = window.CC_OPERATOR_EVIDENCE_SURFACE || null;
  var SURFACE_TRUTH = (MODEL && MODEL.operator_evidence_surface_truth) || {};
  var NO_GRANT_LABEL = "EVIDENCE ONLY / NO GRANT";

  var SURFACE_REQUIRED_FALSE = [
    "public_ready", "live_ready", "dispatch_ready", "executable_dispatch",
    "platform_api_allowed_now", "credential_read_allowed_now",
    "scheduler_enabled_now", "posting_enabled_now", "audit_event_created",
    "audit_allowlist_modified", "readiness_granted"
  ];
  var SURFACE_REQUIRED_TRUE = [
    "evidence_only", "non_executable", "manual_review_required",
    "local_only", "ui_surface_ready"
  ];
  var SURFACE_REQUIRED_LINEAGE = [
    "bridge_report_id", "bridge_report_hash", "compiler_output_id",
    "compile_report_id", "payload_hash_manifest_id",
    "readiness_alignment_id", "audit_alignment_id"
  ];

  function truthField(key, fallback) {
    if (!SURFACE_TRUTH || SURFACE_TRUTH[key] === undefined || SURFACE_TRUTH[key] === null) return fallback;
    return SURFACE_TRUTH[key];
  }

  function truthStateSeverity(state) {
    if (state === "PASS") return "safe";
    if (state === "BLOCKED") return "blocked";
    if (state === "REVIEW_REQUIRED") return "review";
    return "review";
  }

  function flagGroups() {
    var grouped = truthField("required_false_flags", []);
    if (grouped && grouped.length) return grouped;
    var flat = surfaceField("required_false_flag_matrix", []);
    return [{ category: "required false", flags: flat.map(function (f) {
      return { flag: f.flag, expected: false, observed: f.value, state: f.value === false ? "PASS" : "BLOCKED" };
    }) }];
  }

  function lineageRows() {
    return [
      ["Current branch", truthField("current_branch_head", "UNKNOWN"), "current"],
      ["Master baseline", truthField("master_baseline_head", "UNKNOWN"), "historical"],
      ["Source evidence baseline", truthField("source_evidence_baseline_head", "UNKNOWN"), "source"],
      ["Prep02 bridge", truthField("prep02_bridge_head", "UNKNOWN"), "bridge"],
      ["Protected truth rail", truthField("protected_truth_rail_head", "992a7d0"), "protected"]
    ];
  }

  function hostileCases() {
    var hm = truthField("hostile_matrix_summary", {});
    return hm.cases || [];
  }

  function provenanceChip(label, value, posture) {
    var chip = el("span", "provenance-chip posture-" + (posture || "current"));
    chip.appendChild(el("span", "provenance-chip-label", label));
    chip.appendChild(el("span", "provenance-chip-value", value));
    return chip;
  }

  /* Null-safe reader: a partial/absent surface never throws. */
  function surfaceField(key, fallback) {
    if (!SURFACE || SURFACE[key] === undefined || SURFACE[key] === null) return fallback;
    return SURFACE[key];
  }

  /* Recompute the no-grant verdict locally. Never trusts the declared
     validation_state alone. Fail-closed precedence: BLOCKED > UNKNOWN > PASS. */
  function surfaceIntegrity() {
    if (!SURFACE) return { state: "UNKNOWN", reasons: ["evidence surface global is absent"] };
    var reasons = [];
    var falseViolations = SURFACE_REQUIRED_FALSE.filter(function (k) { return SURFACE[k] === true; });
    var trueViolations = SURFACE_REQUIRED_TRUE.filter(function (k) { return SURFACE[k] !== true; });
    falseViolations.forEach(function (k) { reasons.push("required-false flag true: " + k); });
    trueViolations.forEach(function (k) { reasons.push("required-true flag not true: " + k); });
    if (SURFACE.no_grant_label !== NO_GRANT_LABEL) reasons.push("no_grant_label mismatch");
    if (reasons.length) return { state: "BLOCKED", reasons: reasons };
    var missing = SURFACE_REQUIRED_LINEAGE.filter(function (k) {
      return !SURFACE[k] || String(SURFACE[k]).length === 0;
    });
    if (missing.length) {
      return { state: "UNKNOWN", reasons: missing.map(function (k) { return "missing lineage id: " + k; }) };
    }
    if (SURFACE.rollup_state !== "PASS") {
      return { state: SURFACE.rollup_state || "UNKNOWN", reasons: ["rollup_state=" + (SURFACE.rollup_state || "absent")] };
    }
    return { state: "PASS", reasons: [] };
  }

  /* Canonical inspectable object for surface-derived selections. */
  function surfaceInspectObject(partial) {
    return inspectObject({
      kind: "evidence surface",
      id: partial.id || surfaceField("surface_id", "evidence-surface"),
      label: partial.label || "Operator Evidence Surface",
      state: partial.state || surfaceIntegrity().state,
      severity: partial.severity || "neutral",
      reason: partial.reason || "Evidence-only projection of the accepted 0174BT operator evidence summary. Grants nothing.",
      evidence_refs: partial.evidence_refs || [],
      allowed_local_action: "Inspect Evidence",
      blocked_action: "publish / dispatch / credential read / readiness grant",
      caveat: NO_GRANT_LABEL,
      posture: "current"
    });
  }

  /* Fail-closed banner. Shown whenever integrity is not PASS so the worst case
     is a calm unavailable/blocked readout, never a positive/grant affordance. */
  function renderSurfaceUnavailable(body, verdict) {
    var sev = verdict.state === "BLOCKED" ? "blocked" : "review";
    var banner = el("div", "evidence-surface-unavailable sev-" + sev);
    var head = el("div", "es-unavailable-head");
    var title = verdict.state === "BLOCKED"
      ? "SURFACE INTEGRITY BLOCKED"
      : "EVIDENCE SURFACE UNAVAILABLE / NO GRANT";
    head.appendChild(el("span", "es-unavailable-title", title));
    head.appendChild(el("span", "token " + (verdict.state === "BLOCKED" ? "BLOCKED" : "UNKNOWN"), verdict.state));
    banner.appendChild(head);
    banner.appendChild(el("div", "es-unavailable-reason readable-body-copy",
      "Evidence surface fail-closed; no publish / dispatch / readiness affordance is shown. " +
      (verdict.reasons[0] || "")));
    body.appendChild(banner);
    return banner;
  }

  /* Command Center — compact evidence summary near the decision spine. */
  function renderEvidenceSurfaceSummary(body) {
    var verdict = surfaceIntegrity();
    var wrap = el("div", "instrument-panel evidence-surface-summary section-gap");
    var head = el("div", "instrument-head");
    head.appendChild(el("span", "instrument-title", "Operator Evidence Surface"));
    head.appendChild(el("span", "data-label", truthField("no_grant_label", NO_GRANT_LABEL)));
    wrap.appendChild(head);
    if (verdict.state !== "PASS") { renderSurfaceUnavailable(wrap, verdict); body.appendChild(wrap); return; }
    var strip = el("div", "es-summary-grid");
    [["Model state", truthField("integrity_state", verdict.state), truthStateSeverity(truthField("integrity_state", verdict.state)), true],
     ["No-grant", truthField("no_grant_label", NO_GRANT_LABEL), "neutral", false],
     ["Surface id", truthField("surface_id", surfaceField("surface_id", "UNKNOWN")), "neutral", false],
     ["Rollup counts", "block " + surfaceField("blocker_count", 0) + " / review " +
        surfaceField("review_required_count", 0) + " / unknown " + surfaceField("unknown_count", 0), "neutral", false],
     ["Allowed local", surfaceField("allowed_local_action", "inspect evidence only"), "neutral", false],
     ["Branch status", "0174BW repair branch baseline", "neutral", false],
     ["Blocked actions", truthField("blocked_actions", []).slice(0, 4).join(" / "), "blocked", false],
     ["Impossible now", "publish / dispatch / API / credential / scheduler", "blocked", false]
    ].forEach(function (m) {
      var cell = el("div", "es-cell" + (m[2] ? " sev-" + m[2] : ""));
      cell.appendChild(el("span", "data-label", m[0]));
      if (m[3]) {
        var v = el("span", "es-value");
        v.appendChild(el("span", "token " + m[1], m[1]));
        cell.appendChild(v);
      } else {
        cell.appendChild(el("span", "es-value mono", m[1]));
      }
      strip.appendChild(cell);
    });
    wrap.appendChild(strip);
    var src = el("div", "es-source");
    src.appendChild(el("span", "data-label", "Provenance"));
    src.appendChild(provenanceChip("source", truthField("source_evidence_baseline_head", "\u2014"), "source"));
    src.appendChild(provenanceChip("branch", truthField("current_branch_head", "\u2014"), "current"));
    src.appendChild(provenanceChip("master", truthField("master_baseline_head", "\u2014"), "historical"));
    wrap.appendChild(src);
    wrap.appendChild(el("div", "es-no-action-copy",
      "Inspect evidence only. No publish, dispatch, platform/provider API, credential/env read, scheduler, audit event, scraping, reply, or DM action exists here."));
    makeSelectable(wrap, surfaceInspectObject({
      state: verdict.state, severity: "safe",
      reason: "Compact evidence-surface summary. PASS means internally consistent and UI-safe only \u2014 never publish/live/ready."
    }));
    body.appendChild(wrap);
  }

  function renderEvidenceComplianceRoom(body, verdict) {
    var room = el("div", "instrument-panel evidence-compliance-room section-gap");
    var head = el("div", "instrument-head");
    head.appendChild(el("span", "instrument-title", "Evidence Vault Compliance Room"));
    head.appendChild(el("span", "data-label", "state-before-action / no-grant proof"));
    room.appendChild(head);

    var strip = el("div", "compliance-counter-strip");
    [["Availability", truthField("availability", "UNKNOWN"), "review"],
     ["Integrity", truthField("integrity_state", verdict.state), truthStateSeverity(verdict.state)],
     ["Summary", truthField("operator_evidence_summary_id", "UNKNOWN"), "safe"],
     ["Bridge hash", truthField("bridge_report_hash", "UNKNOWN"), "safe"]
    ].forEach(function (m) {
      var cell = el("div", "compliance-counter sev-" + m[2]);
      cell.appendChild(el("span", "data-label", m[0]));
      cell.appendChild(el("span", "mono-value", m[1]));
      strip.appendChild(cell);
    });
    room.appendChild(strip);

    var chain = el("div", "compliance-chain");
    truthField("evidence_path_nodes", surfaceField("evidence_path_nodes", [])).forEach(function (node, i) {
      if (i > 0) chain.appendChild(el("span", "compliance-chain-arrow", "->"));
      var item = el("div", "compliance-chain-node");
      item.appendChild(el("span", "compliance-chain-step", String(i + 1).padStart(2, "0")));
      item.appendChild(el("span", "compliance-chain-label", node));
      chain.appendChild(item);
    });
    room.appendChild(chain);

    var lineage = el("div", "lineage-ledger");
    lineageRows().forEach(function (row) {
      var r = el("div", "lineage-row posture-" + row[2]);
      r.appendChild(el("span", "lineage-role", row[0]));
      r.appendChild(el("span", "lineage-value mono", row[1]));
      r.appendChild(el("span", "lineage-posture", row[2]));
      makeSelectable(r, surfaceInspectObject({
        id: row[0], label: row[0], state: row[2] === "current" ? "PASS" : "REFERENCE",
        severity: row[2] === "current" ? "safe" : "review",
        reason: "Lineage ledger row: " + row[0] + " is labeled " + row[2] + ".",
        evidence_refs: [row[1]]
      }));
      lineage.appendChild(r);
    });
    var lineageDd = drilldown("Lineage Ledger", "current branch / master / source / prep02 / protected truth rail");
    lineageDd.body.appendChild(lineage);
    room.appendChild(lineageDd.details);

    var proof = el("div", "no-grant-proof-panel");
    proof.appendChild(el("div", "proof-title", truthField("no_grant_label", NO_GRANT_LABEL)));
    proof.appendChild(el("div", "proof-copy readable-body-copy",
      "Evidence may support review, but cannot bypass approval, readiness gates, dispatch locks, manual operator control, or credential boundaries."));
    truthField("blocked_actions", surfaceField("blocked_actions", [])).slice(0, 12).forEach(function (action) {
      proof.appendChild(el("span", "blocked-action-chip", action));
    });
    room.appendChild(proof);

    var fallback = el("div", "fallback-proof-panel");
    fallback.appendChild(el("span", "data-label", "Fallback / degraded proof"));
    fallback.appendChild(el("div", "readable-body-copy",
      truthField("fallback_reason", "") || "Bridge present. If the bridge is absent, this model exposes UNKNOWN, degraded, no-grant state and renders no readiness affordance."));
    fallback.appendChild(el("span", "token UNKNOWN", "UNKNOWN fallback"));
    room.appendChild(fallback);

    makeSelectable(room, surfaceInspectObject({
      state: truthField("integrity_state", verdict.state), severity: truthStateSeverity(truthField("integrity_state", verdict.state)),
      reason: "Compliance-room summary: chain, lineage, no-grant proof, fallback proof, and blocked actions are all inspect-only."
    }));
    body.appendChild(room);
  }

  /* Evidence Vault — primary host: chain map, component matrix, required-false
     matrix, hostile rollup, lineage. All within drilldowns; nothing deleted. */
  function renderEvidenceSurfaceHost(body) {
    var verdict = surfaceIntegrity();
    var hostHead = el("div", "instrument-panel evidence-surface-host section-gap");
    var hh = el("div", "instrument-head");
    hh.appendChild(el("span", "instrument-title", "Operator Evidence Surface (Primary Host)"));
    hh.appendChild(el("span", "data-label", NO_GRANT_LABEL));
    hostHead.appendChild(hh);
    if (verdict.state !== "PASS") { renderSurfaceUnavailable(hostHead, verdict); body.appendChild(hostHead); return; }
    var rollup = el("div", "es-rollup");
    [["Rollup", surfaceField("rollup_state", "UNKNOWN"), true],
     ["Validation", surfaceField("validation_state", "UNKNOWN"), true],
     ["Schema", surfaceField("surface_schema_version", "\u2014"), false]
    ].forEach(function (m) {
      var cell = el("div", "es-rollup-cell");
      cell.appendChild(el("span", "data-label", m[0]));
      if (m[2]) cell.appendChild(el("span", "token " + m[1], m[1]));
      else cell.appendChild(el("span", "mono-value", m[1]));
      rollup.appendChild(cell);
    });
    hostHead.appendChild(rollup);
    makeSelectable(hostHead, surfaceInspectObject({ state: verdict.state, severity: "safe",
      reason: "Primary evidence-surface host. Evidence-only projection of the accepted 0174BT summary; grants nothing." }));
    body.appendChild(hostHead);
    renderEvidenceComplianceRoom(body, verdict);

    var nodes = surfaceField("evidence_path_nodes", []);
    if (nodes.length) {
      var chainPanel = panel("Evidence Chain Map");
      var chain = el("div", "es-chain");
      nodes.forEach(function (n, i) {
        if (i > 0) chain.appendChild(el("span", "es-chain-arrow", "\u2192"));
        var node = el("span", "es-chain-node");
        node.appendChild(el("span", "es-chain-step", String(i + 1)));
        node.appendChild(el("span", "es-chain-label", n));
        chain.appendChild(node);
      });
      chainPanel.appendChild(chain);
      var chainDd = drilldown("Evidence Chain Map", "compiler v2 \u2192 operator evidence summary 0174bt \u00b7 drilldown");
      chainDd.body.appendChild(chainPanel);
      body.appendChild(chainDd.details);
    }

    var comps = surfaceField("component_state_matrix", []);
    if (comps.length) {
      var cmPanel = panel("Component State Matrix");
      var cmWrap = el("div", "matrix-wrap");
      var cmTable = el("table", "matrix");
      var cmThead = el("thead"), cmTr = el("tr");
      ["component", "evidence id", "state"].forEach(function (c) { cmTr.appendChild(el("th", null, c)); });
      cmThead.appendChild(cmTr); cmTable.appendChild(cmThead);
      var cmBody = el("tbody");
      comps.forEach(function (r) {
        var tr = el("tr");
        tr.appendChild(el("td", "wrap", r.component));
        tr.appendChild(el("td", "mono", r.evidence_id));
        var td = el("td"); td.appendChild(el("span", "token " + r.state, r.state)); tr.appendChild(td);
        makeSelectable(tr, surfaceInspectObject({
          id: r.evidence_id, label: r.component + " \u00b7 " + r.state, state: r.state,
          severity: r.state === "PASS" ? "safe" : "review",
          reason: "Bound component " + r.component + " validated " + r.state + ".",
          evidence_refs: [r.evidence_id] }));
        cmBody.appendChild(tr);
      });
      cmTable.appendChild(cmBody); cmWrap.appendChild(cmTable); cmPanel.appendChild(cmWrap);
      var cmDd = drilldown("Component State Matrix", "component / evidence id / state \u00b7 drilldown");
      cmDd.body.appendChild(cmPanel);
      body.appendChild(cmDd.details);
    }

    var groupedFlags = flagGroups();
    if (groupedFlags.length) {
      var fPanel = panel("Required-False Flag Matrix (no-grant proof)");
      var fMat = el("div", "required-false-flag-matrix");
      groupedFlags.forEach(function (group) {
        var groupNode = el("div", "flag-group");
        groupNode.appendChild(el("div", "flag-group-title", group.category));
        group.flags.forEach(function (f) {
          var observed = f.observed === undefined ? f.value : f.observed;
          var row = el("div", "es-flag-row" + (observed === true ? " is-violation" : ""));
          row.appendChild(el("span", "es-flag-name mono", f.flag));
          row.appendChild(el("span", "es-flag-value", observed === true ? "TRUE - VIOLATION" : "false"));
          row.appendChild(el("span", "es-flag-state", f.state || (observed === false ? "PASS" : "BLOCKED")));
          makeSelectable(row, surfaceInspectObject({
            id: f.flag, label: group.category + " / " + f.flag,
            state: f.state || (observed === false ? "PASS" : "BLOCKED"),
            severity: observed === false ? "safe" : "blocked",
            reason: "Required-false flag must remain false. Category: " + group.category + ".",
            evidence_refs: [truthField("surface_id", surfaceField("surface_id", "UNKNOWN"))]
          }));
          groupNode.appendChild(row);
        });
        fMat.appendChild(groupNode);
      });
      fPanel.appendChild(fMat);
      var fDd = drilldown("Required-False Flag Matrix", "grouped by readiness / dispatch / API / credential / scheduler / audit");
      fDd.body.appendChild(fPanel);
      body.appendChild(fDd.details);
    }

    var hm = surfaceField("hostile_matrix_summary", {});
    var hostile = hostileCases();
    if (hostile.length) {
      var hPanel = panel("Hostile / Degraded Matrix Drilldown");
      var hWrap = el("div", "matrix-wrap hostile-matrix-group");
      var hTable = el("table", "matrix");
      var hHead = el("thead"), hTr = el("tr");
      ["case id", "mutation", "expected state", "rationale"].forEach(function (c) { hTr.appendChild(el("th", null, c)); });
      hHead.appendChild(hTr); hTable.appendChild(hHead);
      var hBody = el("tbody");
      hostile.forEach(function (c) {
        var tr = el("tr");
        tr.appendChild(el("td", "mono", c.case_id));
        tr.appendChild(el("td", "wrap", c.mutation));
        var td = el("td"); td.appendChild(el("span", "token " + c.expected_state, c.expected_state)); tr.appendChild(td);
        tr.appendChild(el("td", "wrap", c.rationale));
        makeSelectable(tr, surfaceInspectObject({
          id: c.case_id, label: c.case_id, state: c.expected_state,
          severity: c.expected_state === "BLOCKED" ? "blocked" : "review",
          reason: c.rationale, evidence_refs: [c.case_id]
        }));
        hBody.appendChild(tr);
      });
      hTable.appendChild(hBody); hWrap.appendChild(hTable); hPanel.appendChild(hWrap);
      var hDd = drilldown("Hostile / Degraded Matrix", "case id / mutation / expected fail-closed state");
      hDd.body.appendChild(hPanel);
      body.appendChild(hDd.details);
    }

    var lineagePanel = panel("Lineage + Hostile Matrix Rollup");
    [["never_pass", String(hm.never_pass)], ["hostile cases", String(hm.total_cases)],
     ["bridge_report_id", surfaceField("bridge_report_id", "\u2014")],
     ["bridge_report_hash", surfaceField("bridge_report_hash", "\u2014")],
     ["compiler_output_id", surfaceField("compiler_output_id", "\u2014")],
     ["compile_report_id", surfaceField("compile_report_id", "\u2014")],
     ["payload_hash_manifest_id", surfaceField("payload_hash_manifest_id", "\u2014")],
     ["readiness_alignment_id", surfaceField("readiness_alignment_id", "\u2014")],
     ["audit_alignment_id", surfaceField("audit_alignment_id", "\u2014")]
    ].forEach(function (m) {
      var row = el("div", "reg-row");
      row.appendChild(el("span", "reg-key", m[0]));
      row.appendChild(el("span", "reg-val mono", m[1]));
      lineagePanel.appendChild(row);
    });
    var lDd = drilldown("Lineage + Hostile Matrix Rollup", "lineage ids / hostile rollup \u00b7 drilldown");
    lDd.body.appendChild(lineagePanel);
    body.appendChild(lDd.details);
  }

  /* Publish Readiness Tower — no-grant communication matrix. */
  function renderEvidenceSurfaceNoGrant(body) {
    var verdict = surfaceIntegrity();
    var p = el("div", "instrument-panel es-no-grant-matrix section-gap");
    var h = el("div", "instrument-head");
    h.appendChild(el("span", "instrument-title", "No-Grant Communication Matrix"));
    h.appendChild(el("span", "data-label", NO_GRANT_LABEL));
    p.appendChild(h);
    if (verdict.state !== "PASS") { renderSurfaceUnavailable(p, verdict); body.appendChild(p); return; }
    p.appendChild(el("div", "es-no-grant-note readable-body-copy",
      "Evidence summary PASS is evidence-only. Manual review is still required; approval, readiness, dispatch, scheduler, API, credential, audit-event, and allowlist gates remain closed."));
    var blocked = surfaceField("blocked_actions", []);
    var grid = el("div", "es-blocked-grid");
    blocked.forEach(function (a) {
      var cell = el("div", "es-blocked-cell sev-blocked");
      cell.appendChild(el("span", "token BLOCKED", "BLOCKED"));
      cell.appendChild(el("span", "es-blocked-label", a));
      grid.appendChild(cell);
    });
    p.appendChild(grid);
    var noGrantRows = [
      ["evidence_summary_pass", "PASS - evidence-only"],
      ["manual_review_required", "true"],
      ["public_ready", "false"],
      ["live_ready", "false"],
      ["dispatch_ready", "false"],
      ["executable_dispatch", "false"],
      ["scheduler_enabled_now", "false"],
      ["platform_api_allowed_now", "false"],
      ["credential_read_allowed_now", "false"],
      ["audit_event_created", "false"],
      ["audit_allowlist_modified", "false"],
      ["readiness_granted", "false"]
    ];
    var fr = el("div", "gate-matrix no-grant-gate-matrix");
    var table = el("table", "matrix");
    var thead = el("thead"), htr = el("tr");
    ["gate", "observed", "meaning"].forEach(function (c) { htr.appendChild(el("th", null, c)); });
    thead.appendChild(htr); table.appendChild(thead);
    var tbody = el("tbody");
    noGrantRows.forEach(function (r) {
      var tr = el("tr");
      tr.appendChild(el("td", "mono", r[0]));
      tr.appendChild(el("td", "mono", r[1]));
      tr.appendChild(el("td", "wrap", r[0] === "evidence_summary_pass"
        ? "Internally consistent and UI-safe only; not approval or readiness."
        : "This gate cannot be bypassed by evidence surface PASS."));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody); fr.appendChild(table);
    p.appendChild(fr);
    makeSelectable(p, surfaceInspectObject({ state: verdict.state, severity: "blocked",
      reason: "No-grant communication matrix: surface grants no publish/dispatch/readiness even at PASS." }));
    body.appendChild(p);
  }

  /* Settings / Safety — evidence surface boundary policy group. */
  function renderEvidenceSurfaceBoundary(body) {
    var verdict = surfaceIntegrity();
    var p = panel("Evidence Surface Boundary");
    p.classList.add("es-boundary", "section-gap");
    if (verdict.state !== "PASS") { renderSurfaceUnavailable(p, verdict); body.appendChild(p); return; }
    [["No-grant label", surfaceField("no_grant_label", NO_GRANT_LABEL)],
     ["Allowed (local)", surfaceField("allowed_local_action", "inspect evidence only")],
     ["Surface id", surfaceField("surface_id", "\u2014")],
     ["Schema version", surfaceField("surface_schema_version", "\u2014")]
    ].forEach(function (m) {
      var row = el("div", "reg-row");
      row.appendChild(el("span", "reg-key", m[0]));
      row.appendChild(el("span", "reg-val mono", m[1]));
      p.appendChild(row);
    });
    var notes = surfaceField("truth_model_notes", []);
    if (notes.length) {
      p.appendChild(el("div", "data-label", "Truth-model notes"));
      var ul = el("ul");
      notes.forEach(function (n) { ul.appendChild(el("li", null, n)); });
      p.appendChild(ul);
    }
    var cred = truthField("credential_boundary", {});
    var boundary = el("div", "safety-boundary-ledger");
    [["Local-only static bridge", "operator_evidence_surface.js is a static local bridge"],
     ["No network", "no runtime requests, sockets, beacons, platform API, or provider API"],
     ["No storage", "no browser storage, no persisted operator state"],
     ["Known credential file path", cred.known_credential_file_path || "A:\\Capital Chronicle\\tools\\cc-live-contentops.env"],
     ["Credential/env rule", cred.policy || "do not read, do not parse, do not load, do not display values"],
     ["No live posting", "no posting, scheduler, scraping, autonomous replies, or DMs"],
     ["No audit mutation", "no audit event creation and no audit allowlist modification"],
     ["No readiness grant", "evidence supports review only and cannot grant readiness"]
    ].forEach(function (m) {
      var row = el("div", "safety-boundary-row");
      row.appendChild(el("span", "safety-boundary-key", m[0]));
      row.appendChild(el("span", "safety-boundary-val", m[1]));
      boundary.appendChild(row);
    });
    p.appendChild(boundary);
    makeSelectable(p, surfaceInspectObject({ state: verdict.state, severity: "safe",
      reason: "Evidence surface boundary: parallel/additive, evidence-only, no credential or env read." }));
    body.appendChild(p);
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
