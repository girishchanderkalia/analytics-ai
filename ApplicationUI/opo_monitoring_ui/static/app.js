const timeline = document.getElementById("timeline");
const evidencePane = document.getElementById("evidence");
const threadInput = document.getElementById("thread-input");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const interactionPanel = document.getElementById("interaction-panel");
const findingsPanel = document.getElementById("findings-panel");
const findingsContent = document.getElementById("findings-content");
const mainLayout = document.querySelector("main");
const toggleRightPanel = document.getElementById("toggle-right-panel");

let threadId = null;
let busy = false;

function setRightPanelCollapsed(collapsed) {
  mainLayout.classList.toggle("right-panel-collapsed", collapsed);
  toggleRightPanel.innerHTML = collapsed ? "&larr;" : "&rarr;";
  toggleRightPanel.title = collapsed ? "Show interaction and evidence" : "Minimize panel";
  toggleRightPanel.setAttribute(
    "aria-label",
    collapsed ? "Show interaction and evidence panel" : "Minimize interaction and evidence panel"
  );
}

const SERIES_COLOURS = ["#4c9aff", "#a371f7", "#3fb950"];
const OUTLIER_COLOUR = "#f85149";

const PLOT_LAYOUT = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { color: "#8b97a8", size: 11 },
  margin: { l: 48, r: 16, t: 10, b: 40 },
  height: 280,
  hovermode: "closest",
  xaxis: { gridcolor: "#2a3441", linecolor: "#2a3441", zeroline: false },
  yaxis: {
    gridcolor: "#2a3441",
    linecolor: "#2a3441",
    zeroline: false,
    title: "OPO KPI",
  },
  legend: { orientation: "h", y: -0.2, font: { size: 11 } },
  hoverlabel: { bgcolor: "#1e2631", bordercolor: "#2a3441", font: { color: "#e4e8ee" } },
};

const PLOT_CONFIG = { displaylogo: false, responsive: true, displayModeBar: false };

let trendSeries = null;

function drawPlot(outliers, selectedMachine) {
  if (!trendSeries) return;

  const flaggedByMachine = new Map(
    (outliers || []).map((o) => [`${o.machine}::${o.product}`, new Set(o.outlier_dates)])
  );

  const traces = trendSeries.map((s, idx) => {
    const dimmed = selectedMachine && s.machine !== selectedMachine;
    return {
      type: "scatter",
      mode: "markers",
      name: `${s.machine} / ${s.product}`,
      x: s.points.map((p) => p.date),
      y: s.points.map((p) => p.kpi_value),
      marker: { size: 8, color: SERIES_COLOURS[idx % SERIES_COLOURS.length] },
      opacity: dimmed ? 0.3 : 1,
      hovertemplate: `%{x}<br>%{y:.2f} absolute OPO KPI<extra>${s.machine} / ${s.product}</extra>`,
    };
  });

  // Points matching the analyst's request, ringed in red
  if (flaggedByMachine.size) {
    const rings = { x: [], y: [], text: [] };
    trendSeries.forEach((s) => {
      const dates = flaggedByMachine.get(`${s.machine}::${s.product}`);
      if (!dates) return;
      s.points
        .filter((p) => dates.has(p.date))
        .forEach((p) => {
          rings.x.push(p.date);
          rings.y.push(p.kpi_value);
          rings.text.push(`${s.machine} / ${s.product}`);
        });
    });

    traces.push({
      type: "scatter",
      mode: "markers",
      name: "Outlier",
      x: rings.x,
      y: rings.y,
      text: rings.text,
      marker: {
        size: 15,
        color: "rgba(0,0,0,0)",
        line: { color: OUTLIER_COLOUR, width: 2.5 },
      },
      hovertemplate: "<b>Outlier</b><br>%{text}<br>%{x} — %{y:.2f} absolute OPO KPI<extra></extra>",
    });
  }

  Plotly.react(document.getElementById("trend-plot"), traces, PLOT_LAYOUT, PLOT_CONFIG);
}

async function loadTrends() {
  try {
    const res = await fetch("/trends", { cache: "no-store" });
    if (!res.ok) throw new Error(`${res.status}`);
    trendSeries = (await res.json()).series;
    drawPlot(null, null);
    document.getElementById("chart-note").textContent =
      `${trendSeries.length} series · ${trendSeries[0].points.length} days`;
  } catch (err) {
    document.getElementById("chart-note").textContent = `Could not load trends: ${err.message}`;
  }
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

// Model output is escaped first, then a small markdown subset is re-applied.
function renderMarkdown(text) {
  const lines = escapeHtml(text).split("\n");
  let html = "";
  let inList = false;

  for (let line of lines) {
    line = line
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/`(.+?)`/g, "<code>$1</code>");

    const bullet = line.match(/^\s*[-*]\s+(.*)$/);
    const numbered = line.match(/^\s*\d+\.\s+(.*)$/);

    if (bullet || numbered) {
      if (!inList) { html += "<ul>"; inList = true; }
      html += `<li>${(bullet || numbered)[1]}</li>`;
      continue;
    }
    if (inList) { html += "</ul>"; inList = false; }

    if (/^\s*#{1,6}\s/.test(line)) {
      html += `<h3>${line.replace(/^\s*#{1,6}\s*/, "")}</h3>`;
    } else if (line.trim()) {
      html += `<p>${line}</p>`;
    }
  }
  if (inList) html += "</ul>";
  return html;
}

function renderStructuredFindings(summary) {
  const list = (items) => (items || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  const references = (summary.evidence_references || [])
    .map((item) => `<code>${escapeHtml(item)}</code>`).join(" ");
  return `<div class="structured-findings">
    <section class="finding-primary">
      <div class="finding-label">Finding</div>
      <p>${escapeHtml(summary.finding)}</p>
    </section>
    <div class="finding-meta">
      <div><span class="finding-label">Confidence</span><strong>${escapeHtml(summary.confidence)}</strong></div>
      <div><span class="finding-label">Evidence</span><span>${references || "None listed"}</span></div>
    </div>
    <section><div class="finding-label">Limitations</div><ul>${list(summary.limitations)}</ul></section>
    <section><div class="finding-label">Recommended next actions</div><ul>${list(summary.recommended_next_actions)}</ul></section>
    <section><div class="finding-label">Alternative explanations</div><ul>${list(summary.alternative_explanations)}</ul></section>
  </div>`;
}

function renderFindingsPanel(summary) {
  findingsContent.innerHTML = summary?.finding
    ? renderStructuredFindings(summary)
    : `<div class="findings">${renderMarkdown(summary || "")}</div>`;
  findingsPanel.hidden = false;
}

function clearEmptyState() {
  const empty = timeline.querySelector(".empty-state");
  if (empty) empty.remove();
}

function addNode(className, html) {
  clearEmptyState();
  const node = document.createElement("div");
  node.className = className;
  node.innerHTML = html;
  timeline.appendChild(node);
  timeline.scrollTop = timeline.scrollHeight;
  return node;
}

function setBusy(value, label) {
  busy = value;
  sendBtn.disabled = value;
  document.querySelectorAll(".gate-actions button").forEach((b) => (b.disabled = value));
  messageInput.disabled = value || !interactionPanel.hidden;

  const existing = document.getElementById("busy-node");
  if (existing) existing.remove();
  if (value) {
    addNode("msg status", `<span id="busy-inner"><span class="spinner"></span>${escapeHtml(label)}</span>`)
      .id = "busy-node";
  }
}

function renderGate(request) {
  const isConfirm = request.type === "confirm_investigation";
  const isThreshold = request.type === "clarify_absolute_threshold";

  let detail;
  let selector = "";

  if (isConfirm) {
    const c = request.candidate;
    const extreme = c.extreme_kpi_value;
    const unit = " absolute OPO KPI";
    detail = `Most extreme: <code>${escapeHtml(c.machine)}</code> /
      <code>${escapeHtml(c.product)}</code> &mdash;
      <code>${escapeHtml(extreme)}</code>${unit},
      <code>${escapeHtml(c.outlier_dates.length)}</code> marked points`;
    selector = `<select id="outlier-select">${request.all_outliers
      .map((o) => `<option value="${escapeHtml(o.machine)}">
        ${escapeHtml(o.machine)} / ${escapeHtml(o.product)} — ${escapeHtml(o.extreme_kpi_value)} absolute OPO KPI
      </option>`).join("")}</select>`;
  } else if (isThreshold) {
    detail = `<div class="threshold-reference">Reference values: P95 <code>${escapeHtml(request.p95)}</code>
      &middot; P99 <code>${escapeHtml(request.p99)}</code></div>
      <div class="threshold-recommendation">Model recommendation: use absolute cutoff
      <code>${escapeHtml(request.suggested_limit_value)}</code></div>
      <div class="threshold-rationale">${escapeHtml(request.rationale || "")}</div>`;
    selector = `<input id="threshold-input" type="number" min="0" step="0.001"
      value="${escapeHtml(request.suggested_limit_value)}" aria-label="Selected absolute OPO KPI cutoff" />`;
  } else {
    detail = `Workspace <code>${escapeHtml(request.workspace_id)}</code> &middot;
      dataset <code>${escapeHtml(request.dataset)}</code> &middot;
      filters <code>${escapeHtml(JSON.stringify(request.filters))}</code>`;
  }

  interactionPanel.hidden = false;
  interactionPanel.innerHTML = `
    <div class="gate">
      <div class="gate-label">Agent response required</div>
      <h3>${escapeHtml(request.question)}</h3>
      <div class="gate-detail">${detail}</div>
      ${selector}
      <div class="gate-actions">
        <button data-action="approve">Use selected cutoff</button>
        <button data-action="reject" class="reject">Reject</button>
      </div>
    </div>`;
  const gate = interactionPanel;

  gate.querySelector('[data-action="approve"]').onclick = () => {
    if (isThreshold) {
      const input = gate.querySelector("#threshold-input");
      const value = Number(input?.value);
      if (!Number.isFinite(value) || value < 0) {
        input?.focus();
        return;
      }
      resolveGate(gate, "Cutoff approved", { approved: true, limit_value: value });
      return;
    }
    const select = document.getElementById("outlier-select");
    const decision = { approved: true };
    if (isConfirm && select) decision.machine = select.value;
    resolveGate(gate, "Approved", decision);
  };
  gate.querySelector('[data-action="reject"]').onclick = () =>
    resolveGate(gate, "Rejected", { approved: false });
}

function resolveGate(gateNode, label, decision) {
  gateNode.querySelector(".gate").classList.add("resolved");
  gateNode.querySelector(".gate-actions").innerHTML =
    `<span class="gate-label">${escapeHtml(label)}</span>`;
  const select = gateNode.querySelector("select");
  if (select) select.disabled = true;
  const input = gateNode.querySelector("input");
  if (input) input.disabled = true;
  send("/resume", { thread_id: threadId, decision }, "Continuing investigation…");
}

function renderEvidence(evidence) {
  if (!evidence) return;
  let html = "";

  const scope = [
    ["Range", evidence.lookback_days ? `Last ${evidence.lookback_days} days` : null],
    ["Machine", evidence.machine_id],
    ["Lot", evidence.lot_id],
    ["Product", evidence.product_id],
    ["Layer", evidence.layer_id],
    ["Exposure equipment", evidence.exposure_equipment_id],
  ].filter(([, value]) => value);
  if (scope.length) {
    html += `<div class="card"><h3>Scope</h3>${scope
      .map(([label, value]) => `<div class="kv"><span>${escapeHtml(label)}</span><span>${escapeHtml(value)}</span></div>`)
      .join("")}</div>`;
  }

  if (evidence.selected_outlier) {
    const o = evidence.selected_outlier;
    html += `<div class="card"><h3>Outlier</h3>
      <div class="kv"><span>Machine</span><span>${escapeHtml(o.machine)}</span></div>
      <div class="kv"><span>Product</span><span>${escapeHtml(o.product)}</span></div>
      <div class="kv"><span>KPI deviation</span><span>${escapeHtml(o.deviation_pct)}%</span></div>
    </div>`;
  }

  if (evidence.workspace_id) {
    html += `<div class="card"><h3>Workspace</h3>
      <div class="kv"><span>ID</span><span>${escapeHtml(evidence.workspace_id)}</span></div>
      ${Object.entries(evidence.filters || {}).map(([k, v]) =>
        `<div class="kv"><span>${escapeHtml(k)}</span><span>${escapeHtml(v)}</span></div>`).join("")}
    </div>`;
  }

  if (evidence.registration_history?.length) {
    html += `<div class="card"><h3>Registration</h3>${evidence.registration_history
      .map((s) => `<div class="step">
        <span class="dot ${s.status === "READY" ? "done" : ""}"></span>
        <span>${escapeHtml(s.status)} — ${escapeHtml(s.progress_pct)}%</span>
      </div>`).join("")}</div>`;
  }

  if (evidence.wafer_rows?.length) {
    const anomalous = new Set(evidence.anomalous_wafers || []);
    html += `<div class="card"><h3>Wafers</h3><table>
      <tr><th>Wafer</th><th>Overlay X</th><th>Overlay Y</th><th>Magnitude</th></tr>
      ${evidence.wafer_rows.map((r) => `
        <tr class="${anomalous.has(r.wafer_id) ? "anomalous" : ""}">
          <td>${escapeHtml(r.wafer_id)}</td>
          <td>${escapeHtml(r.overlay_x_um)}</td>
          <td>${escapeHtml(r.overlay_y_um)}</td>
          <td>${escapeHtml(r.overlay_magnitude_um)}</td>
        </tr>`).join("")}
    </table></div>`;
  }

  if (html) evidencePane.innerHTML = html;
}

function ruleLabel(evidence) {
  const { mode, limit_value: limit, direction, baseline_deviation_pct: deviation, threshold_unit: unit } = evidence;
  return mode === "absolute"
    ? `${direction} ${limit}${unit === "percent" ? "% from baseline" : " absolute OPO KPI"}`
    : `more than ${deviation}% above each machine's own baseline`;
}

function renderTrendChart(evidence) {
  if (!evidence) return;
  const note = document.getElementById("chart-note");
  const selected = evidence.selected_outlier?.machine || null;

  drawPlot(evidence.outliers, selected);

  if (!evidence.mode) return;
  const rule = ruleLabel(evidence);

  if (!evidence.outliers?.length) {
    note.textContent = `No points ${rule}`;
    return;
  }

  const points = evidence.outliers.reduce((n, o) => n + o.outlier_dates.length, 0);
  note.innerHTML = `<span class="ring-key"></span>${points} points ${rule},
     across ${evidence.outliers.length} series`;
}

function renderWaferMap(evidence) {
  const plotEl = document.getElementById("wafer-plot");
  const noteEl = document.getElementById("wafer-note");

  if (!plotEl || !evidence) return;

  const rows = evidence.wafer_rows || [];
  if (!rows.length) {
    noteEl.textContent = "No wafer data";
    Plotly.purge(plotEl);
    return;
  }

  const anomalySet = new Set(evidence.anomalous_wafers || []);
  const waferIds = [...new Set(rows.map((row) => row.wafer_id))];
  const columns = Math.min(3, Math.max(1, waferIds.length));
  const waferRows = Math.ceil(waferIds.length / columns);
  const traces = [];
  const annotations = [];
  const shapes = [];
  const waferLayout = {};

  waferIds.forEach((waferId, index) => {
    const axisNumber = index + 1;
    const axisSuffix = axisNumber === 1 ? "" : axisNumber;
    const axisRef = `x${axisSuffix}`;
    const yAxisRef = `y${axisSuffix}`;
    const waferRowsForPanel = rows.filter((row) => row.wafer_id === waferId);
    const x = [];
    const y = [];
    const measurementX = [];
    const measurementY = [];
    const pointColors = [];
    const pointText = [];

    waferRowsForPanel.forEach((row) => {
      const px = Number(row.measureprocessjob_wafermeasureprocessjob_measurement_intrafieldposition_position_x ?? row.position_x ?? 0);
      const py = Number(row.measureprocessjob_wafermeasureprocessjob_measurement_intrafieldposition_position_y ?? row.position_y ?? 0);
      const ux = Number(row.overlay_x ?? 0);
      const uy = Number(row.overlay_y ?? 0);
      const valid = row.overlay_valid_x !== false && row.overlay_valid_y !== false;
      if (!Number.isFinite(px) || !Number.isFinite(py)) return;

      const pointColor = valid && anomalySet.has(row.wafer_id) ? "#f85149" : valid ? "#4c9aff" : "#667085";
      measurementX.push(px);
      measurementY.push(py);
      pointColors.push(pointColor);
      pointText.push(`${row.wafer_id} / ${row.machine}`);
      x.push(px, px + ux * 60, null);
      y.push(py, py + uy * 60, null);
    });

    traces.push({
      type: "scatter",
      mode: "lines",
      x,
      y,
      xaxis: axisRef,
      yaxis: yAxisRef,
      line: { color: "#4c9aff", width: 1.3 },
      hoverinfo: "none",
      showlegend: false,
    });
    traces.push({
      type: "scatter",
      mode: "markers",
      x: measurementX,
      y: measurementY,
      xaxis: axisRef,
      yaxis: yAxisRef,
      marker: {
        size: 6,
        color: pointColors,
        opacity: 0.92,
        line: {
          color: waferRowsForPanel.map((row) => anomalySet.has(row.wafer_id) ? "#f85149" : "rgba(0,0,0,0)"),
          width: waferRowsForPanel.map((row) => anomalySet.has(row.wafer_id) ? 1.5 : 0),
        },
      },
      text: pointText,
      hovertemplate: "%{text}<br>x=%{x:.2f}, y=%{y:.2f}<extra></extra>",
      showlegend: false,
    });

    const column = index % columns;
    const row = Math.floor(index / columns);
    const xStart = column / columns + 0.015;
    const xEnd = (column + 1) / columns - 0.015;
    const yEnd = 1 - row / waferRows - 0.08;
    const yStart = 1 - (row + 1) / waferRows + 0.08;
    const axisLayout = {
      domain: [xStart, xEnd],
      range: [-30, 30],
      zeroline: false,
      gridcolor: "#2a3441",
      showticklabels: false,
      fixedrange: true,
    };
    const yAxisLayout = {
      domain: [yStart, yEnd],
      range: [-30, 30],
      zeroline: false,
      gridcolor: "#2a3441",
      showticklabels: false,
      fixedrange: true,
      scaleanchor: axisRef,
      scaleratio: 1,
    };
    annotations.push({
      x: (xStart + xEnd) / 2,
      y: yEnd + 0.025,
      xref: "paper",
      yref: "paper",
      text: `<b>${waferId}</b>${anomalySet.has(waferId) ? " · anomaly" : ""}`,
      showarrow: false,
      font: { color: anomalySet.has(waferId) ? "#f85149" : "#e4e8ee", size: 11 },
    });
    shapes.push({
      type: "circle",
      xref: axisRef,
      yref: yAxisRef,
      x0: -27,
      y0: -27,
      x1: 27,
      y1: 27,
      line: { color: "#667085", width: 1 },
    });

    waferRowsForPanel.forEach((row) => {
      const px = Number(row.measureprocessjob_wafermeasureprocessjob_measurement_intrafieldposition_position_x ?? row.position_x ?? 0);
      const py = Number(row.measureprocessjob_wafermeasureprocessjob_measurement_intrafieldposition_position_y ?? row.position_y ?? 0);
      const ux = Number(row.overlay_x ?? 0);
      const uy = Number(row.overlay_y ?? 0);
      const valid = row.overlay_valid_x !== false && row.overlay_valid_y !== false;
      if (!valid || !Number.isFinite(px) || !Number.isFinite(py) || (ux === 0 && uy === 0)) return;
      annotations.push({
        x: px + ux * 60,
        y: py + uy * 60,
        ax: px,
        ay: py,
        xref: axisRef,
        yref: yAxisRef,
        axref: axisRef,
        ayref: yAxisRef,
        showarrow: true,
        arrowhead: 3,
        arrowsize: 0.8,
        arrowwidth: anomalySet.has(row.wafer_id) ? 1.5 : 1,
        arrowcolor: anomalySet.has(row.wafer_id) ? "#f85149" : "#4c9aff",
        text: "",
      });
    });

    waferLayout[`xaxis${axisSuffix}`] = axisLayout;
    waferLayout[`yaxis${axisSuffix}`] = yAxisLayout;
  });

  Object.assign(waferLayout, {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    margin: { l: 8, r: 8, t: 12, b: 8 },
    height: Math.max(260, waferRows * 250),
    showlegend: false,
    hovermode: "closest",
    annotations,
    shapes,
    font: { color: "#8b97a8", size: 11 },
  });

  noteEl.textContent = `${rows.length} point measurements across ${waferIds.length} wafers`;
  Plotly.react(plotEl, traces, waferLayout, PLOT_CONFIG);
}

function handleResponse(data) {
  threadId = data.thread_id;
  threadInput.value = threadId;
  if (data.evidence?.trend_series) trendSeries = data.evidence.trend_series;
  renderTrendChart(data.evidence);
  renderWaferMap(data.evidence);
  renderEvidence(data.evidence);

  const firstResponse =
    data.request?.type === "confirm_investigation" || data.status === "no_outliers";
  if (firstResponse && data.evidence?.mode) {
    const { mode, limit_value: used, requested_limit_value: asked, interpretation } =
      data.evidence;
    const adjusted = mode === "absolute" && data.evidence.threshold_unit === "percent" && asked != null && asked !== used;
    const badge = mode === "absolute" ? "Absolute limit" : "Per-machine baseline";
    addNode("msg status",
      `<strong>${badge}</strong>: marking points ${escapeHtml(ruleLabel(data.evidence))}` +
      (adjusted ? ` (requested <code>${escapeHtml(asked)}</code>)` : "") +
      (interpretation ? `<br><span class="interpretation">${escapeHtml(interpretation)}</span>` : ""));
  }

  if (data.status === "awaiting_human") {
    renderGate(data.request);
  } else if (data.status === "no_outliers") {
    interactionPanel.hidden = true;
    findingsPanel.hidden = true;
    addNode("msg agent", `<span class="badge ready">No outliers</span>
      <p>No points fall ${escapeHtml(ruleLabel(data.evidence))}.</p>`);
  } else if (data.status === "cancelled") {
    interactionPanel.hidden = true;
    findingsPanel.hidden = true;
    addNode("msg agent", `<span class="badge cancelled">Cancelled</span>
      <p>Investigation stopped at <code>${escapeHtml(data.cancelled_at)}</code>.
      No downstream resources were provisioned.</p>`);
  } else if (data.status === "complete") {
    interactionPanel.hidden = true;
    renderFindingsPanel(data.findings);
    addNode("msg agent", `<span class="badge ready">Complete</span>
      ${data.findings?.finding ? renderStructuredFindings(data.findings) :
        `<div class="findings">${renderMarkdown(data.findings || "")}</div>`}`);
  }
}

async function send(path, body, busyLabel) {
  setBusy(true, busyLabel);
  try {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
    handleResponse(await res.json());
  } catch (err) {
    addNode("msg agent", `<span class="badge cancelled">Error</span>
      <p>${escapeHtml(err.message)}</p>`);
  } finally {
    setBusy(false);
  }
}

document.getElementById("composer").onsubmit = (event) => {
  event.preventDefault();
  if (busy) return;
  const message = messageInput.value.trim();
  if (!message) return;
  threadId = null;
  timeline.innerHTML = "";
  interactionPanel.hidden = true;
  interactionPanel.innerHTML = "";
  findingsPanel.hidden = true;
  findingsContent.innerHTML = "";
  messageInput.disabled = false;
  evidencePane.innerHTML = '<div class="empty-state small"><p>No evidence yet.</p></div>';
  drawPlot(null, null);
  addNode("msg user", escapeHtml(message));
  send("/chat", { message }, "Analysing trends…");
};

toggleRightPanel.onclick = () => {
  setRightPanelCollapsed(!mainLayout.classList.contains("right-panel-collapsed"));
};

document.getElementById("reopen-btn").onclick = async () => {  const id = threadInput.value.trim();
  if (!id || busy) return;
  setBusy(true, "Reopening investigation…");
  try {
    const res = await fetch(`/threads/${encodeURIComponent(id)}`);
    if (!res.ok) throw new Error(`${res.status}`);
    const data = await res.json();
    threadId = id;
    timeline.innerHTML = "";
    const evidence = {
      mode: data.values?.mode,
      limit_value: data.values?.limit_value,
      direction: data.values?.direction,
      baseline_deviation_pct: data.values?.baseline_deviation_pct,
      lookback_days: data.values?.lookback_days,
      machine_id: data.values?.machine_id,
      lot_id: data.values?.lot_id,
      product_id: data.values?.product_id,
      layer_id: data.values?.layer_id,
      exposure_equipment_id: data.values?.exposure_equipment_id,
      trend_series: data.values?.trend_series,
      analysis: data.values?.analysis,
      outliers: data.values?.outliers,
      selected_outlier: data.values?.selected,
      workspace_id: data.values?.workspace_id,
      filters: data.values?.filters,
      registration_history: data.values?.registration_history,
      wafer_rows: data.values?.wafer_data?.rows,
      anomalous_wafers: data.values?.wafer_data?.anomalous_wafers,
    };
    renderEvidence(evidence);
    renderTrendChart(evidence);
    renderWaferMap(evidence);
    addNode("msg status", `Reopened thread <code>${escapeHtml(id)}</code>`);
    if (data.status === "awaiting_human") {
      renderGate(data.request);
    } else {
      addNode("msg agent", "<p>This investigation has no pending decision.</p>");
    }
  } catch (err) {
    addNode("msg agent", `<span class="badge cancelled">Error</span>
      <p>Could not reopen: ${escapeHtml(err.message)}</p>`);
  } finally {
    setBusy(false);
  }
};

loadTrends();
