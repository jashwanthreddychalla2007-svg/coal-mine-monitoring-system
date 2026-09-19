let mines = [];
let currentDetails = null;
let refreshTimer = null;
let liveTimer = null;

const mineSelect = document.getElementById("mine-select");
const parameterSelect = document.getElementById("parameter-select");
const projectSummary = document.getElementById("project-summary");
const syncBadge = document.getElementById("sync-badge");
const valueInput = document.getElementById("value-input");
const valueSlider = document.getElementById("value-slider");
const unitLabel = document.getElementById("unit-label");
const thresholdBox = document.getElementById("threshold-box");
const riskScore = document.getElementById("risk-score");
const riskStatus = document.getElementById("risk-status");
const riskMeter = document.getElementById("risk-meter");
const hazardProbability = document.getElementById("hazard-probability");
const probabilityMeter = document.getElementById("probability-meter");
const breachList = document.getElementById("breach-list");
const solutionList = document.getElementById("solution-list");
const parameterCards = document.getElementById("parameter-cards");
const mobileAlertResult = document.getElementById("mobile-alert-result");

function isNumericReading(row) {
  return row && row.parameter !== "last_inspection_date" && row.parameter !== "safety_equipment_status";
}

function numberValue(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function statusClass(status) {
  if (status === "critical") return "status-critical";
  if (status === "warning") return "status-warning";
  return "status-normal";
}

function setSync(text, status) {
  syncBadge.textContent = text;
  syncBadge.className = `status-pill ${status ? statusClass(status) : ""}`;
}

function alertClass(severity) {
  if (severity === "DANGER") return "danger";
  if (severity === "WARNING") return "warning";
  return "resolved";
}

function showMobileAlertResult(alert, reading) {
  if (!mobileAlertResult) return;
  if (alert) {
    mobileAlertResult.className = `mobile-alert-result active ${alertClass(alert.severity)}`;
    mobileAlertResult.innerHTML = `<strong>${alert.severity} alert sent to dashboard.</strong><br>${alert.message}<br><strong>Action:</strong> ${alert.solution}`;
    return;
  }

  mobileAlertResult.className = "mobile-alert-result active resolved";
  mobileAlertResult.innerHTML = `<strong>Live value sent.</strong><br>${reading.label} status: ${reading.status}.`;
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

async function loadMines() {
  setSync("Loading", "");
  mines = await fetchJson("/api/mines");
  mineSelect.innerHTML = mines
    .map(mine => `<option value="${mine.id}">${mine.name} (${mine.id})</option>`)
    .join("");
  await loadMineDetails(mineSelect.value || (mines[0] && mines[0].id));
}

async function loadMineDetails(mineId) {
  if (!mineId) return;
  currentDetails = await fetchJson(`/api/mines/${mineId}`);
  renderMine();
  setSync("Live", "normal");
}

function selectedParameter() {
  if (!currentDetails) return null;
  return currentDetails.parameters.find(row => row.parameter === parameterSelect.value) || null;
}

function renderMine() {
  const mine = currentDetails.mine;
  const risk = currentDetails.ai_risk_report;
  const numericRows = currentDetails.parameters.filter(isNumericReading);
  const previousParameter = parameterSelect.value;

  parameterSelect.innerHTML = numericRows
    .map(row => `<option value="${row.parameter}">${row.label}</option>`)
    .join("");

  if (numericRows.some(row => row.parameter === previousParameter)) {
    parameterSelect.value = previousParameter;
  }

  projectSummary.innerHTML = [
    ["Mine type", mine.type],
    ["Subsidiary", mine.subsidiary],
    ["District / state", `${mine.district}, ${mine.state}`],
    ["Production", `${mine.current_production_tonnes} / ${mine.daily_target_tonnes} tonnes`],
  ].map(([label, value]) => `
    <div class="summary-item">
      <span>${label}</span>
      <strong>${value}</strong>
    </div>
  `).join("");

  riskScore.textContent = risk.risk_score;
  riskStatus.textContent = risk.risk_status;
  riskMeter.style.width = `${Math.min(100, risk.risk_score)}%`;
  riskMeter.style.background = risk.color_code;
  hazardProbability.textContent = `${risk.predicted_incident_probability_pct}%`;
  probabilityMeter.style.width = `${Math.min(100, risk.predicted_incident_probability_pct)}%`;
  probabilityMeter.style.background = risk.color_code;

  renderBreachAndSolution();
  renderParameterCards();
  renderSelectedParameter();
}

function renderSelectedParameter() {
  const row = selectedParameter();
  if (!row) return;

  const value = numberValue(row.value);
  const warning = numberValue(row.warning_threshold);
  const danger = numberValue(row.danger_threshold);
  const lowerIsWorse = row.warning_threshold !== null && row.danger_threshold !== null && danger < warning;
  let min = 0;
  let max = Math.max(value * 1.4, warning * 1.4, danger * 1.2, 10);

  if (lowerIsWorse) {
    min = Math.max(0, danger * 0.6);
    max = Math.max(value * 1.2, warning * 1.4, danger * 1.4);
  }

  if (row.parameter === "daily_production") {
    const target = currentDetails.mine.daily_target_tonnes || value || 1;
    min = 0;
    max = Math.max(target * 1.45, value * 1.2);
  }

  valueInput.value = value;
  valueSlider.min = min.toFixed(2);
  valueSlider.max = max.toFixed(2);
  valueSlider.step = row.parameter === "daily_production" ? 10 : 0.01;
  valueSlider.value = value;
  unitLabel.textContent = row.unit || "";

  const direction = lowerIsWorse ? "lower readings are more dangerous" : "higher readings are more dangerous";
  thresholdBox.innerHTML = `
    <strong>${row.label}</strong><br>
    Current status: <span class="parameter-status ${statusClass(row.status)}">${row.status}</span><br>
    Warning limit: ${row.warning_threshold ?? "not fixed"} ${row.unit || ""}<br>
    Danger limit: ${row.danger_threshold ?? "not fixed"} ${row.unit || ""}<br>
    For this parameter, ${direction}.
  `;
}

function renderBreachAndSolution() {
  const risk = currentDetails.ai_risk_report;
  const anomaly = currentDetails.production_anomaly;
  const breaches = [...(risk.primary_factors || [])];
  const solutions = [...(risk.ai_corrective_recommendations || [])];

  if (anomaly && anomaly.is_anomaly) {
    breaches.push(anomaly.description);
    solutions.push("Check production dispatch logs and verify shift-wise operational entries.");
  }

  breachList.innerHTML = breaches.map(item => `<li>${item}</li>`).join("");
  solutionList.innerHTML = solutions.map(item => `<li>${item}</li>`).join("");

  if (!breaches.length) {
    breachList.innerHTML = `<li>No active breach for the selected colliery project.</li>`;
  }
  if (!solutions.length) {
    solutionList.innerHTML = `<li>Continue normal monitoring and sensor calibration.</li>`;
  }
}

function renderParameterCards() {
  parameterCards.innerHTML = currentDetails.parameters.map(row => `
    <article class="parameter-card">
      <header>
        <h3>${row.label}</h3>
        <span class="parameter-status ${statusClass(row.status)}">${row.status}</span>
      </header>
      <div class="parameter-value">${row.value} ${row.unit || ""}</div>
      <div class="parameter-meta">${row.device}<br>${row.placement}</div>
    </article>
  `).join("");
}

function presetValue(kind) {
  const row = selectedParameter();
  if (!row) return 0;
  const warning = numberValue(row.warning_threshold);
  const danger = numberValue(row.danger_threshold);
  const current = numberValue(row.value);
  const lowerIsWorse = row.warning_threshold !== null && row.danger_threshold !== null && danger < warning;

  if (row.parameter === "daily_production") {
    const target = currentDetails.mine.daily_target_tonnes || current || 1;
    if (kind === "safe") return target;
    if (kind === "warning") return Math.round(target * 1.28);
    return Math.round(target * 1.45);
  }

  if (row.warning_threshold === null || row.danger_threshold === null) return current;

  if (lowerIsWorse) {
    if (kind === "safe") return warning + Math.max(0.1, warning * 0.08);
    if (kind === "warning") return (warning + danger) / 2;
    return Math.max(0, danger * 0.85);
  }

  if (kind === "safe") return Math.max(0, warning * 0.7);
  if (kind === "warning") return (warning + danger) / 2;
  return danger * 1.08;
}

async function applyCurrentValue() {
  const row = selectedParameter();
  if (!row) return;

  setSync("Applying", "warning");
  const response = await fetchJson("/api/iot/ingest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      mine_id: currentDetails.mine.id,
      parameter: row.parameter,
      value: row.parameter === "daily_production" ? Math.round(numberValue(valueInput.value)) : numberValue(valueInput.value),
      hold_minutes: 10,
    }),
  });
  showMobileAlertResult(response.alert, response.reading);
  await loadMineDetails(currentDetails.mine.id);
}

async function clearCurrentOverride() {
  const row = selectedParameter();
  if (!row) return;

  setSync("Clearing", "warning");
  await fetchJson("/api/iot/overrides/clear", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      mine_id: currentDetails.mine.id,
      parameter: row.parameter,
    }),
  });
  await loadMineDetails(currentDetails.mine.id);
}

function connectLiveUpdates() {
  if (!window.EventSource) return;
  const source = new EventSource("/api/iot/events");
  source.onmessage = event => {
    try {
      const data = JSON.parse(event.data);
      if (!currentDetails || data.version <= 0) return;
      if (!data.mine_id || data.mine_id === currentDetails.mine.id) {
        clearTimeout(liveTimer);
        liveTimer = setTimeout(() => {
          loadMineDetails(currentDetails.mine.id).catch(error => {
            console.error(error);
            setSync("Offline", "critical");
          });
        }, 80);
      }
    } catch (error) {
      console.error(error);
    }
  };
}

mineSelect.addEventListener("change", () => loadMineDetails(mineSelect.value));
parameterSelect.addEventListener("change", renderSelectedParameter);
valueInput.addEventListener("input", () => {
  valueSlider.value = valueInput.value;
});
valueSlider.addEventListener("input", () => {
  valueInput.value = valueSlider.value;
});
document.getElementById("apply-btn").addEventListener("click", applyCurrentValue);
document.getElementById("clear-btn").addEventListener("click", clearCurrentOverride);

document.querySelectorAll("[data-preset]").forEach(button => {
  button.addEventListener("click", () => {
    const value = presetValue(button.dataset.preset);
    valueInput.value = value.toFixed(value >= 100 ? 0 : 2);
    valueSlider.value = valueInput.value;
    applyCurrentValue();
  });
});

loadMines().catch(error => {
  console.error(error);
  setSync("Error", "critical");
  parameterCards.innerHTML = `<p class="empty-state">Could not load sensor data.</p>`;
});
connectLiveUpdates();

refreshTimer = setInterval(() => {
  if (currentDetails) {
    loadMineDetails(currentDetails.mine.id).catch(error => {
      console.error(error);
      setSync("Offline", "critical");
    });
  }
}, 5000);

window.addEventListener("beforeunload", () => {
  clearInterval(refreshTimer);
});
