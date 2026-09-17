// Global State
let allMines = [];
let allCompliances = [];
let allInspections = [];
let gisMap = null;
let mapMarkers = [];
let chartInstance = null;

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  initDashboard();
});

async function initDashboard() {
  await loadOverview();
  await loadMinesData();
  await loadCompliancesData();
  await loadInspectionsData();
  await loadContractorsData();
}

// Navigation Tabs
function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

  const targetTab = document.getElementById(`tab-${tabId}`);
  if (targetTab) targetTab.classList.add('active');

  const clickedNav = Array.from(document.querySelectorAll('.nav-item')).find(el => 
    el.getAttribute('onclick')?.includes(tabId)
  );
  if (clickedNav) clickedNav.classList.add('active');

  // If GIS map tab is activated, invalidate Leaflet map size to prevent rendering glitch
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

    renderSubsidiaryChart(data.subsidiary_breakdown);
  } catch (err) {
    console.error("Failed to load overview:", err);
  }
}

// Render Chart.js
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
        backgroundColor: scores.map(s => s >= 90 ? 'rgba(16, 185, 129, 0.7)' : (s >= 80 ? 'rgba(245, 158, 11, 0.7)' : 'rgba(239, 68, 68, 0.7)')),
        borderColor: scores.map(s => s >= 90 ? '#10b981' : (s >= 80 ? '#f59e0b' : '#ef4444')),
        borderWidth: 1,
        borderRadius: 6
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
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9ca3af' }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#9ca3af' }
        }
      }
    }
  });
}

// 2. Mines Table & Mine Dropdown
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
      const riskBadge = `<span class="badge" style="background:${risk.color_code}22; color:${risk.color_code}; border:1px solid ${risk.color_code}44;">
        ${risk.risk_status} (${risk.risk_score})
      </span>`;

      // Telemetry badge
      let gasBadge = '';
      if (mine.type === 'Underground') {
        gasBadge = `CH4: <b>${mine.gas_status.ch4_pct}%</b> | CO: <b>${mine.gas_status.co_ppm}ppm</b>`;
      } else {
        gasBadge = `PM10: <b>${mine.gas_status.pm10_ugm3} µg/m³</b>`;
      }

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="font-family: var(--font-mono); color: var(--accent);">${mine.id}</td>
        <td><b>${mine.name}</b><br><small style="color:var(--text-muted);">${mine.area}</small></td>
        <td><span class="badge badge-info">${mine.subsidiary}</span></td>
        <td>${mine.type}</td>
        <td>${mine.current_production_tonnes.toLocaleString()} / ${mine.daily_target_tonnes.toLocaleString()} MT</td>
        <td>${gasBadge}</td>
        <td>${riskBadge}</td>
        <td>${mine.active_violations > 0 ? `<span class="badge badge-danger">${mine.active_violations} Violation(s)</span>` : '<span class="badge badge-success">Clean</span>'}</td>
        <td>
          <button class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;" onclick="viewMineDetails('${mine.id}')">Inspect</button>
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
  } catch (err) {
    console.error("Failed to load mines:", err);
  }
}

// 3. Leaflet GIS Map
function initGISMap() {
  const mapElement = document.getElementById('gis-map');
  if (!mapElement) return;

  // Center on Central/Eastern India Coalfields (Jharkhand/Chhattisgarh)
  gisMap = L.map('gis-map').setView([23.5, 84.5], 6);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors | KhananRakshak GIS'
  }).addTo(gisMap);

  // Plot Mines
  allMines.forEach(mine => {
    const risk = mine.ai_risk_assessment;
    const marker = L.circleMarker([mine.lat, mine.lng], {
      radius: 12,
      fillColor: risk.color_code,
      color: '#fff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.85
    }).addTo(gisMap);

    const popupContent = `
      <div style="font-family: sans-serif; color: #111;">
        <h4 style="margin:0 0 4px 0;">${mine.name}</h4>
        <div style="font-size: 12px; margin-bottom: 6px;"><b>Subsidiary:</b> ${mine.subsidiary} | <b>Type:</b> ${mine.type}</div>
        <div style="font-size: 12px; margin-bottom: 6px;"><b>AI Risk Score:</b> <span style="color:${risk.color_code}; font-weight:bold;">${risk.risk_score} - ${risk.risk_status}</span></div>
        <div style="font-size: 11px; background:#f3f4f6; padding:6px; border-radius:4px;">
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
        <td style="font-family: var(--font-mono); color: var(--accent);">${c.id}</td>
        <td><b>${c.mine_name}</b></td>
        <td><span class="badge badge-info">${c.category}</span></td>
        <td>${c.regulation}</td>
        <td>${c.frequency}</td>
        <td style="color: ${c.status === 'OVERDUE' ? 'var(--danger)' : 'inherit'}; font-weight: 600;">${c.due_date}</td>
        <td><span class="badge ${c.criticality.includes('Class A') ? 'badge-danger' : 'badge-warning'}">${c.criticality}</span></td>
        <td><span class="badge ${badgeClass}">${c.status}</span></td>
        <td>
          ${c.status !== 'COMPLIED' ? 
            `<button class="btn btn-outline" style="padding: 3px 8px; font-size: 11px; color: var(--success);" onclick="markComplied('${c.id}')">Verify</button>` : 
            `<span style="color: var(--success); font-size: 12px;">Verified ✓</span>`
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
      body: JSON.stringify({ status: 'COMPLIED', notes: 'Verified via statutory inspection log' })
    });
    loadCompliancesData();
    loadOverview();
    alert(`Statutory Mandate ${complianceId} status updated to COMPLIED.`);
  } catch (err) {
    alert("Error updating compliance status.");
  }
}

// 5. Field Inspections
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
      item.style.cssText = "background: #0d1424; border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 14px;";
      item.innerHTML = `
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
          <b>${insp.mine_name}</b>
          <span class="badge ${insp.violation_class === 'Class A' ? 'badge-danger' : 'badge-warning'}">${insp.violation_class}</span>
        </div>
        <div style="font-size: 13px; color: #fff; margin-bottom: 6px;">${insp.findings}</div>
        <div style="font-size: 11px; color: var(--text-dim);">
          📍 [${insp.lat}, ${insp.lng}] | Inspector: ${insp.inspector_name} (${insp.inspector_role}) | ${insp.date}
        </div>
        <div style="font-size: 12px; color: var(--primary); margin-top: 6px;">
          🛠️ <b>Action:</b> ${insp.corrective_action_required}
        </div>
      `;
      list.appendChild(item);

      // Add to escalation alert widget on dashboard if Class A or Escalated
      if (insp.status === 'ESCALATED_TO_GM') {
        const alertCard = document.createElement('div');
        alertCard.style.cssText = "background: rgba(239, 68, 68, 0.1); border-left: 3px solid #ef4444; padding: 12px; border-radius: 4px; font-size: 12px;";
        alertCard.innerHTML = `
          <div style="font-weight: bold; color: #ef4444; margin-bottom: 2px;">⚠️ ESCALATION: ${insp.mine_name}</div>
          <div style="color: var(--text-main); margin-bottom: 4px;">${insp.findings}</div>
          <div style="color: var(--text-dim);">Auto-escalated to General Manager (SLA Expired).</div>
        `;
        alertContainer.appendChild(alertCard);
      }
    });
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
      alert("✅ Geo-tagged inspection logged and real-time risk score updated!");
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

// 6. AI Analytics & Diagnostics View
function renderAIAnalyticsCards(mines) {
  const container = document.getElementById('ai-risk-cards');
  container.innerHTML = '';

  mines.forEach(mine => {
    const ai = mine.ai_risk_assessment;
    const anomaly = mine.production_anomaly;

    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <div class="card-header">
        <div>
          <h4 style="color:#fff; font-size:15px;">${mine.name}</h4>
          <span style="font-size:12px; color:var(--text-muted);">${mine.subsidiary} • ${mine.type}</span>
        </div>
        <span class="badge" style="background:${ai.color_code}22; color:${ai.color_code}; border:1px solid ${ai.color_code}55; font-size:13px;">
          MRI: ${ai.risk_score} / 100
        </span>
      </div>

      <div style="font-size: 13px; margin-bottom: 12px;">
        <b>Predicted Incident Probability:</b> <span style="color:${ai.color_code}; font-weight:bold;">${ai.predicted_incident_probability_pct}%</span>
      </div>

      <div style="background: rgba(255,255,255,0.02); border-radius: var(--radius-sm); padding: 12px; margin-bottom: 12px;">
        <div style="font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px;">AI Identified Risk Vectors</div>
        <ul style="padding-left: 18px; font-size: 12px; color: #e5e7eb;">
          ${ai.primary_factors.map(f => `<li style="margin-bottom: 4px;">${f}</li>`).join('')}
        </ul>
      </div>

      <div class="ai-recommendation-box">
        <h4>⚡ AI Prescribed Interventions</h4>
        <ul>
          ${ai.ai_corrective_recommendations.map(r => `<li>${r}</li>`).join('')}
        </ul>
      </div>

      ${anomaly.is_anomaly ? `
        <div style="margin-top: 12px; background: rgba(239, 68, 68, 0.1); border: 1px dashed #ef4444; border-radius: 6px; padding: 10px; font-size: 12px; color: #fca5a5;">
          <b>Production / EC Anomaly:</b> ${anomaly.description}
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
      <td style="font-family: var(--font-mono); color: var(--accent);">CONT-301</td>
      <td><b>BEEPC Mining Services Ltd.</b></td>
      <td>Jharia Opencast Block IV</td>
      <td>340 Drivers / Rig Operators</td>
      <td><span class="badge badge-success">91.0%</span></td>
      <td>98.5% Complied</td>
      <td style="color:var(--success);">2027-03-31 (Active)</td>
      <td><span class="badge badge-success">Vetted</span></td>
      <td><span class="badge badge-success">Low Risk</span></td>
    </tr>
    <tr>
      <td style="font-family: var(--font-mono); color: var(--accent);">CONT-302</td>
      <td><b>Vindhya Earthmovers & Haulage</b></td>
      <td>Rajmahal OCP (Lalmatia)</td>
      <td>210 Dumper Operators</td>
      <td><span class="badge badge-danger">72.4%</span></td>
      <td>81.0% Complied (19 Uncertified)</td>
      <td style="color:var(--danger); font-weight:bold;">2026-10-10 (Expiring in 23 days)</td>
      <td><span class="badge badge-warning">Audit Pending</span></td>
      <td><span class="badge badge-danger">High Risk</span></td>
    </tr>
    <tr>
      <td style="font-family: var(--font-mono); color: var(--accent);">CONT-303</td>
      <td><b>Pragati Heavy Infra Pvt Ltd</b></td>
      <td>Gevra Mega Opencast Project</td>
      <td>650 Heavy Earth Moving Machinery Crew</td>
      <td><span class="badge badge-success">97.5%</span></td>
      <td>100.0% Complied</td>
      <td style="color:var(--success);">2027-08-30 (Active)</td>
      <td><span class="badge badge-success">Vetted</span></td>
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
