// Global State
let allMines = [];
let allCompliances = [];
let allInspections = [];
let gisMap = null;
let mapMarkers = [];
let chartInstance = null;

const sectionTitles = {
  'dashboard': 'Executive Overview',
  'gis': 'GIS Spatial Map',
  'statutory': 'Statutory Compliance Register',
  'inspection': 'Field Inspection & Audit',
  'ai-analytics': 'AI Risk & Anomaly Assessment',
  'contractors': 'Contractor Compliance'
};

document.addEventListener("DOMContentLoaded", () => {
  initDashboard();
  setInterval(refreshOperationalData, 30000);
});

async function initDashboard() {
  await loadOverview();
  await loadMinesData();
  await loadCompliancesData();
  await loadInspectionsData();
  await loadContractorsData();
}

async function refreshOperationalData() {
  await loadOverview();
  await loadMinesData();
  await loadInspectionsData();
}

function getStatusBadgeClass(status) {
  if (status === 'critical') return 'badge-danger';
  if (status === 'warning') return 'badge-warning';
  return 'badge-success';
}

// Tab Switching
function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));

  const targetTab = document.getElementById(`tab-${tabId}`);
  if (targetTab) targetTab.classList.add('active');

  const clickedNav = Array.from(document.querySelectorAll('.nav-link')).find(el => 
    el.getAttribute('onclick')?.includes(tabId)
  );
  if (clickedNav) clickedNav.classList.add('active');

  const titleEl = document.getElementById('current-section-name');
  if (titleEl && sectionTitles[tabId]) {
    titleEl.textContent = sectionTitles[tabId];
  }

  // If GIS tab is selected, refresh map dimensions
  if (tabId === 'gis') {
    setTimeout(() => {
      if (!gisMap) {
        initGISMap();
      } else {
        gisMap.invalidateSize();
      }
    }, 200);
  }
}

// 1. National Overview
async function loadOverview() {
  try {
    const res = await fetch('/api/overview');
    const data = await res.json();

    document.getElementById('kpi-total-mines').textContent = data.total_active_mines_monitored;
    document.getElementById('kpi-compliance-index').textContent = `${data.national_compliance_index_pct}%`;
    document.getElementById('kpi-overdue-comp').textContent = data.overdue_statutory_items;
    document.getElementById('kpi-high-risk').textContent = data.high_risk_mines_count;
    document.getElementById('kpi-active-sensors').textContent = data.active_iot_sensors;
    document.getElementById('kpi-sensor-meta').textContent = `${data.active_iot_sensors} sensors across ${data.total_active_mines_monitored} mines`;

    const syncBadge = document.getElementById('last-sync-badge');
    if (syncBadge) syncBadge.textContent = `Last synced: ${data.last_sensor_sync_seconds}s ago`;

    renderSubsidiaryChart(data.subsidiary_breakdown);
  } catch (err) {
    console.error("Failed to load overview data:", err);
  }
}

// Render Chart
function renderSubsidiaryChart(subsidiaries) {
  const ctx = document.getElementById('subsidiaryChart').getContext('2d');
  const labels = Object.keys(subsidiaries);
  const scores = labels.map(k => subsidiaries[k].avg_compliance);

  if (chartInstance) chartInstance.destroy();

  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Statutory Compliance Score (%)',
        data: scores,
        backgroundColor: scores.map(s => s >= 90 ? '#15803d' : (s >= 80 ? '#d97706' : '#dc2626')),
        borderColor: scores.map(s => s >= 90 ? '#166534' : (s >= 80 ? '#b45309' : '#b91c1c')),
        borderWidth: 1,
        borderRadius: 2
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          min: 60,
          max: 100,
          grid: { color: '#e5e7eb' },
          ticks: { color: '#4b5563', font: { size: 11 } }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#4b5563', font: { size: 11 } }
        }
      }
    }
  });
}

// 2. Mines Table & Form Dropdown
async function loadMinesData() {
  try {
    const sub = document.getElementById('subsidiary-filter').value;
    const url = sub ? `/api/mines?subsidiary=${sub}` : '/api/mines';
    const res = await fetch(url);
    allMines = await res.json();

    const tbody = document.getElementById('mines-table-body');
    tbody.innerHTML = '';

    const dropdown = document.getElementById('insp-mine-id');
    dropdown.innerHTML = '';

    allMines.forEach(mine => {
      const risk = mine.ai_risk_assessment;
      let badgeClass = 'badge-success';
      if (risk.risk_status.includes('HAZARD')) badgeClass = 'badge-danger';
      else if (risk.risk_status.includes('RISK')) badgeClass = 'badge-warning';

      const uptime = mine.equipment_uptime_pct ?? 0;
      const uptimeClass = uptime < 60 ? 'badge-danger' : (uptime < 80 ? 'badge-warning' : 'badge-success');

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="font-family: var(--font-mono); font-weight: 500;">${mine.id}</td>
        <td><strong>${mine.name}</strong><br><span style="font-size:11.5px; color:var(--text-light);">${mine.area}</span></td>
        <td><span class="badge badge-neutral">${mine.subsidiary}</span></td>
        <td>${mine.type}</td>
        <td>${mine.current_production_tonnes.toLocaleString()} MT</td>
        <td><span class="badge ${uptimeClass}">${uptime}%</span></td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="openParameterModal('${mine.id}')">View Parameters</button>
          <div style="font-size:11px; color:var(--text-light); margin-top:4px;">${mine.parameter_count} live signals</div>
        </td>
        <td><span class="badge ${badgeClass}">${risk.risk_score} - ${risk.risk_status}</span></td>
        <td>${mine.active_violations > 0 ? `<span class="badge badge-danger">${mine.active_violations} Violation(s)</span>` : '<span class="badge badge-success">Nil</span>'}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="viewMineDetails('${mine.id}')">View Details</button>
        </td>
      `;
      tbody.appendChild(tr);

      // Populate Form Dropdown
      const opt = document.createElement('option');
      opt.value = mine.id;
      opt.textContent = `${mine.name} (${mine.subsidiary})`;
      dropdown.appendChild(opt);
    });

    renderAIAnalyticsCards(allMines);
    renderComplianceOpsSummary(allMines);
  } catch (err) {
    console.error("Failed to load mines:", err);
  }
}

async function openParameterModal(mineId) {
  const modal = document.getElementById('parameter-modal');
  const content = document.getElementById('parameter-modal-content');
  const title = document.getElementById('parameter-modal-title');
  const subtitle = document.getElementById('parameter-modal-subtitle');

  content.innerHTML = '<div class="gov-alert gov-alert-info">Loading current sensor readings...</div>';
  modal.classList.add('active');
  modal.setAttribute('aria-hidden', 'false');

  try {
    const res = await fetch(`/api/mines/${mineId}/parameters`);
    const data = await res.json();
    title.textContent = `${data.mine_name} Parameters`;
    subtitle.textContent = `${data.mine_type} mine | Last synced: ${data.last_synced_seconds}s ago`;

    content.innerHTML = data.parameters.map(p => `
      <div class="parameter-card">
        <div style="display:flex; justify-content:space-between; gap:8px; align-items:flex-start;">
          <div class="parameter-card-title">${p.label}</div>
          <span class="badge ${getStatusBadgeClass(p.status)}">${p.status}</span>
        </div>
        <div class="parameter-value">${p.value} ${p.unit || ''}</div>
        <div class="parameter-meta">
          ${p.device}<br>
          ${p.placement}<br>
          ${p.warning_threshold !== null && p.warning_threshold !== undefined ? `Warning: ${p.warning_threshold} | Danger: ${p.danger_threshold}` : 'Event-driven / auto-logged'}
        </div>
      </div>
    `).join('');
  } catch (err) {
    content.innerHTML = '<div class="gov-alert gov-alert-danger">Unable to load mine parameters.</div>';
  }
}

function closeParameterModal() {
  const modal = document.getElementById('parameter-modal');
  modal.classList.remove('active');
  modal.setAttribute('aria-hidden', 'true');
}

function renderComplianceOpsSummary(mines) {
  const container = document.getElementById('compliance-ops-summary');
  if (!container) return;

  container.innerHTML = mines.map(mine => {
    const status = mine.safety_equipment_status || 'functional';
    const badgeClass = status === 'faulty' ? 'badge-danger' : (status === 'needs_calibration' ? 'badge-warning' : 'badge-success');
    return `
      <div class="mini-card">
        <div style="font-size:12px; font-weight:700; color:var(--primary-navy); margin-bottom:6px;">${mine.name}</div>
        <div style="font-size:12px; color:var(--text-muted); margin-bottom:8px;">Last inspection: <strong>${mine.last_inspection_date}</strong> <span class="badge badge-info">Auto-logged</span></div>
        <div>Safety equipment: <span class="badge ${badgeClass}">${status.replace('_', ' ')}</span></div>
      </div>
    `;
  }).join('');
}

// 3. Leaflet GIS Map (Clean Government OpenStreetMap Styling)
function initGISMap() {
  const mapElement = document.getElementById('gis-map');
  if (!mapElement) return;

  gisMap = L.map('gis-map').setView([23.5, 84.5], 6);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors | CIL GIS Portal'
  }).addTo(gisMap);

  allMines.forEach(mine => {
    const risk = mine.ai_risk_assessment;
    let markerColor = '#15803d'; // green
    if (risk.risk_status.includes('HAZARD')) markerColor = '#dc2626'; // red
    else if (risk.risk_status.includes('RISK')) markerColor = '#d97706'; // amber

    const marker = L.circleMarker([mine.lat, mine.lng], {
      radius: 9,
      fillColor: markerColor,
      color: '#ffffff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.9
    }).addTo(gisMap);

    const popupContent = `
      <div style="font-family: var(--font-sans); color: #1f2937; padding: 2px;">
        <div style="font-weight: 700; font-size: 13px; margin-bottom: 4px;">${mine.name}</div>
        <div style="font-size: 11px; margin-bottom: 4px;"><strong>Subsidiary:</strong> ${mine.subsidiary} | <strong>Type:</strong> ${mine.type}</div>
        <div style="font-size: 11px; margin-bottom: 4px;"><strong>Risk Evaluation:</strong> ${risk.risk_score} (${risk.risk_status})</div>
        <div style="font-size: 11px; background: #f3f4f6; padding: 4px 6px; border-radius: 3px;">
          ${mine.type === 'Underground' ? `Methane: ${mine.gas_status.ch4_pct}% | CO: ${mine.gas_status.co_ppm} ppm` : `Dust PM10: ${mine.gas_status.pm10_ugm3} µg/m³`}
        </div>
      </div>
    `;
    marker.bindPopup(popupContent);
    mapMarkers.push(marker);
  });
}

// 4. Statutory Compliances
async function loadCompliancesData(filterStatus = null) {
  try {
    const url = filterStatus && filterStatus !== 'ALL' ? `/api/compliances?status=${filterStatus}` : '/api/compliances';
    const res = await fetch(url);
    allCompliances = await res.json();

    const tbody = document.getElementById('compliance-table-body');
    tbody.innerHTML = '';

    allCompliances.forEach(c => {
      let badgeClass = 'badge-info';
      if (c.status === 'OVERDUE') badgeClass = 'badge-danger';
      else if (c.status === 'PENDING') badgeClass = 'badge-warning';
      else if (c.status === 'COMPLIED') badgeClass = 'badge-success';

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="font-family: var(--font-mono); font-weight: 500;">${c.id}</td>
        <td><strong>${c.mine_name}</strong></td>
        <td><span class="badge badge-neutral">${c.category}</span></td>
        <td>${c.regulation}</td>
        <td>${c.frequency}</td>
        <td style="font-weight: 600; color: ${c.status === 'OVERDUE' ? '#dc2626' : 'inherit'};">${c.due_date}</td>
        <td><span class="badge ${c.criticality.includes('Class A') ? 'badge-danger' : 'badge-warning'}">${c.criticality}</span></td>
        <td><span class="badge ${badgeClass}">${c.status}</span></td>
        <td>
          ${c.status !== 'COMPLIED' ? 
            `<button class="btn btn-secondary btn-sm" onclick="markComplied('${c.id}')">Verify</button>` : 
            `<span style="color: #15803d; font-size: 12px; font-weight: 600;">Verified</span>`
          }
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load compliances:", err);
  }
}

function filterCompliance(status) {
  loadCompliancesData(status);
}

async function markComplied(complianceId) {
  try {
    await fetch(`/api/compliances/${complianceId}/update-status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'COMPLIED', notes: 'Verified and certified by DGMS inspection' })
    });
    loadCompliancesData();
    loadOverview();
    alert(`Statutory Mandate [${complianceId}] successfully updated to COMPLIED.`);
  } catch (err) {
    alert("Error updating compliance status.");
  }
}

// 5. Field Inspections & Alerts
async function loadInspectionsData() {
  try {
    const res = await fetch('/api/inspections');
    allInspections = await res.json();

    const list = document.getElementById('inspections-list');
    list.innerHTML = '';

    const alertContainer = document.getElementById('escalation-alerts');
    alertContainer.innerHTML = '';

    allInspections.forEach(insp => {
      const item = document.createElement('div');
      item.style.cssText = "background: #ffffff; border: 1px solid var(--border-color); border-radius: var(--radius); padding: 12px;";
      item.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <strong style="font-size: 13.5px; color: var(--primary-navy);">${insp.mine_name}</strong>
          <span class="badge ${insp.violation_class === 'Class A' ? 'badge-danger' : 'badge-warning'}">${insp.violation_class}</span>
        </div>
        <div style="font-size: 12.5px; color: var(--text-main); margin-bottom: 6px;">${insp.findings}</div>
        <div style="font-size: 11px; color: var(--text-light); margin-bottom: 6px;">
          Coordinates: [${insp.lat}, ${insp.lng}] | Inspector: ${insp.inspector_name} (${insp.inspector_role}) | Logged: ${insp.date}
        </div>
        <div style="font-size: 12px; color: var(--primary-navy); font-weight: 500;">
          <strong>Remedial Action:</strong> ${insp.corrective_action_required}
        </div>
      `;
      list.appendChild(item);

      // Add to escalation panel if Class A or Escalated
      if (insp.status === 'ESCALATED_TO_GM') {
        const alertCard = document.createElement('div');
        alertCard.className = 'gov-alert gov-alert-danger';
        alertCard.innerHTML = `
          <div style="font-weight: 700; margin-bottom: 2px;">Notice: ${insp.mine_name}</div>
          <div style="margin-bottom: 4px;">${insp.findings}</div>
          <div style="font-size: 11.5px; color: #7f1d1d;">Auto-escalated to General Manager due to SLA breach.</div>
        `;
        alertContainer.appendChild(alertCard);
      }
    });

    if (alertContainer.children.length === 0) {
      alertContainer.innerHTML = `<div class="gov-alert gov-alert-info">No statutory escalations currently pending.</div>`;
    }
  } catch (err) {
    console.error("Failed to load inspections:", err);
  }
}

async function submitInspection(e) {
  e.preventDefault();
  const mineId = document.getElementById('insp-mine-id').value;
  const inspectorName = document.getElementById('insp-name').value;
  const inspectorRole = document.getElementById('insp-role').value;
  const inspType = document.getElementById('insp-type').value;
  const violationClass = document.getElementById('insp-class').value;
  const findings = document.getElementById('insp-findings').value;
  const action = document.getElementById('insp-action').value;
  const photo = document.getElementById('insp-photo').value;

  const mine = allMines.find(m => m.id === mineId);
  const lat = mine ? mine.lat : 23.7438;
  const lng = mine ? mine.lng : 86.4116;

  try {
    const res = await fetch('/api/inspections', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mine_id: mineId,
        inspector_name: inspectorName,
        inspector_role: inspectorRole,
        type: inspType,
        violation_class: violationClass,
        findings: findings,
        corrective_action_required: action,
        lat: lat,
        lng: lng,
        photo_url: photo
      })
    });

    if (res.ok) {
      alert("Inspection report submitted and logged to statutory audit trail.");
      document.getElementById('insp-findings').value = '';
      document.getElementById('insp-action').value = '';
      await loadInspectionsData();
      await loadMinesData();
      await loadOverview();
    }
  } catch (err) {
    alert("Failed to submit inspection.");
  }
}

// 6. AI Risk Diagnostics
function renderAIAnalyticsCards(mines) {
  const container = document.getElementById('ai-risk-cards');
  container.innerHTML = '';

  mines.forEach(mine => {
    const ai = mine.ai_risk_assessment;
    const anomaly = mine.production_anomaly;

    let badgeClass = 'badge-success';
    if (ai.risk_status.includes('HAZARD')) badgeClass = 'badge-danger';
    else if (ai.risk_status.includes('RISK')) badgeClass = 'badge-warning';

    const card = document.createElement('div');
    card.style.cssText = "background:#ffffff; border:1px solid var(--border-color); border-radius:var(--radius); padding:16px;";
    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px; border-bottom:1px solid var(--border-subtle); padding-bottom:8px;">
        <div>
          <div style="font-weight:700; color:var(--primary-navy); font-size:14px;">${mine.name}</div>
          <div style="font-size:12px; color:var(--text-light);">${mine.subsidiary} &bull; ${mine.type} Mine</div>
        </div>
        <span class="badge ${badgeClass}">Score: ${ai.risk_score} / 100</span>
      </div>

      <div style="font-size:12.5px; margin-bottom:10px;">
        <strong>Statistical Hazard Probability:</strong> ${ai.predicted_incident_probability_pct}%
      </div>

      <div style="font-size:12px; color:var(--text-muted); margin-bottom:10px;">
        Risk inputs include sensor status, equipment uptime, overdue compliance, active violations, and production variance.
      </div>

      <div style="margin-bottom:12px;">
        <div style="font-size:11.5px; font-weight:600; color:var(--text-muted); text-transform:uppercase; margin-bottom:4px;">Contributing Risk Factors</div>
        <ul style="padding-left:18px; font-size:12px; color:var(--text-main);">
          ${ai.primary_factors.map(f => `<li style="margin-bottom:3px;">${f}</li>`).join('')}
        </ul>
      </div>

      <div class="gov-alert gov-alert-warning" style="margin-bottom:8px; font-size:12px;">
        <strong style="display:block; margin-bottom:3px;">Prescribed Compliance Action:</strong>
        <ul style="padding-left:16px; margin:0;">
          ${ai.ai_corrective_recommendations.map(r => `<li>${r}</li>`).join('')}
        </ul>
      </div>

      ${anomaly.is_anomaly ? `
        <div class="gov-alert gov-alert-danger" style="margin:0; font-size:11.5px;">
          <strong>Operational / EC Anomaly:</strong> ${anomaly.description}
        </div>
      ` : ''}
    `;
    container.appendChild(card);
  });
}

// 7. Contractors Table
async function loadContractorsData() {
  const tbody = document.getElementById('contractors-table-body');
  tbody.innerHTML = `
    <tr>
      <td style="font-family: var(--font-mono); font-weight: 500;">CONT-301</td>
      <td><strong>BEEPC Mining Services Ltd.</strong></td>
      <td>Jharia Opencast Block IV</td>
      <td>340 Personnel</td>
      <td><span class="badge badge-success">91.0%</span></td>
      <td>98.5% Certified</td>
      <td>2027-03-31</td>
      <td><span class="badge badge-success">Approved</span></td>
      <td><span class="badge badge-success">Low Risk</span></td>
    </tr>
    <tr>
      <td style="font-family: var(--font-mono); font-weight: 500;">CONT-302</td>
      <td><strong>Vindhya Earthmovers & Haulage</strong></td>
      <td>Rajmahal OCP (Lalmatia)</td>
      <td>210 Personnel</td>
      <td><span class="badge badge-danger">72.4%</span></td>
      <td>81.0% Certified (19 Pending)</td>
      <td style="color:#dc2626; font-weight:600;">2026-10-10 (Expiring)</td>
      <td><span class="badge badge-warning">Audit Scheduled</span></td>
      <td><span class="badge badge-danger">High Risk</span></td>
    </tr>
    <tr>
      <td style="font-family: var(--font-mono); font-weight: 500;">CONT-303</td>
      <td><strong>Pragati Heavy Infra Pvt Ltd</strong></td>
      <td>Gevra Mega Opencast Project</td>
      <td>650 Personnel</td>
      <td><span class="badge badge-success">97.5%</span></td>
      <td>100.0% Certified</td>
      <td>2027-08-30</td>
      <td><span class="badge badge-success">Approved</span></td>
      <td><span class="badge badge-success">Low Risk</span></td>
    </tr>
  `;
}

function onSubsidiaryChange() {
  loadMinesData();
}

function viewMineDetails(mineId) {
  switchTab('ai-analytics');
}
