from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json
import os
import random
import uuid

from backend.data import SUBSIDIARIES, SAMPLE_MINES, STATUTORY_COMPLIANCES, INSPECTION_REPORTS, CONTRACTORS
from backend.ai_engine import MiningAIRiskEngine
from backend.parameters import (
    ENVIRONMENTAL_KEYS,
    PARAMETER_DEFINITIONS,
    SIMULATED_SENSOR_KEYS,
    applicable_parameters,
    parameter_status,
)

app = FastAPI(
    title="CoalGuard AI / KhananRakshak",
    description="AI-Based Smart Governance and Compliance Monitoring System for Coal Mines (SIH)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory working stores initialized with sample datasets
mines_db = list(SAMPLE_MINES)
compliances_db = list(STATUTORY_COMPLIANCES)
inspections_db = list(INSPECTION_REPORTS)
contractors_db = list(CONTRACTORS)
iot_readings_db: Dict[str, Dict[str, Dict[str, Any]]] = {}
manual_sensor_overrides_db: Dict[str, datetime] = {}
sensor_alerts_db: List[Dict[str, Any]] = []
sensor_status_db: Dict[str, str] = {}
simulator_task = None
last_sensor_sync = datetime.now()
live_update_version = 0
last_sensor_event: Dict[str, Any] = {
    "version": 0,
    "mine_id": None,
    "parameter": None,
    "alert": None,
    "timestamp": last_sensor_sync.isoformat(),
}

SAFETY_STATUSES = ["functional", "functional", "functional", "functional"]


def _mine_by_id(mine_id: str):
    return next((m for m in mines_db if m["id"] == mine_id), None)


def _override_key(mine_id: str, parameter: str):
    return f"{mine_id}:{parameter}"


def _publish_sensor_update(mine_id: Optional[str] = None, parameter: Optional[str] = None, alert: Optional[Dict[str, Any]] = None):
    global live_update_version, last_sensor_event
    live_update_version += 1
    last_sensor_event = {
        "version": live_update_version,
        "mine_id": mine_id,
        "parameter": parameter,
        "alert": alert,
        "timestamp": datetime.now().isoformat(),
    }


def _alert_solution(reading: Dict[str, Any]):
    parameter = reading["parameter"]
    if parameter == "ch4":
        return "Stop electrical equipment in the affected section, improve ventilation, and evacuate workers if the value keeps rising."
    if parameter == "co":
        return "Check for spontaneous heating or fire, increase ventilation, and inspect the goaf/blasting zone immediately."
    if parameter == "o2":
        return "Move workers away from the affected area and restore fresh air supply before work continues."
    if parameter == "ventilation_air_velocity":
        return "Increase auxiliary ventilation and inspect ducts, stoppings, and fan output."
    if parameter == "blast_vibration":
        return "Hold the next blast, review charge pattern, and inspect nearby benches or structures."
    if parameter == "respirable_dust":
        return "Start water spraying or mist cannons, reduce dust-generating movement, and issue respiratory protection."
    if parameter == "temperature":
        return "Improve ventilation and hydration breaks, then inspect nearby equipment for heat build-up."
    if parameter == "pressure":
        return "Inspect ventilation pressure balance, check stoppings and doors, and verify barometer calibration."
    if parameter == "light_intensity":
        return "Restore lighting in the affected zone and stop movement of workers or vehicles until visibility is safe."
    if parameter == "equipment_uptime":
        return "Inspect critical equipment, assign maintenance, and arrange standby machinery if needed."
    if parameter == "safety_equipment_status":
        return "Replace or recalibrate faulty safety equipment before the next shift."
    if parameter == "daily_production":
        return "Verify production entry against dispatch records and approved operating limit."
    return "Verify the sensor reading, inspect the location, and take corrective action."


def _reading_threshold_text(reading: Dict[str, Any]):
    warning = reading.get("warning_threshold")
    danger = reading.get("danger_threshold")
    unit = reading.get("unit") or ""
    if warning is None or danger is None:
        return "threshold monitored by operating rule"
    return f"warning {warning} {unit}, danger {danger} {unit}".strip()


def _record_sensor_alert(mine: Dict[str, Any], reading: Dict[str, Any]):
    key = _override_key(mine["id"], reading["parameter"])
    previous_status = sensor_status_db.get(key)
    current_status = reading["status"]
    sensor_status_db[key] = current_status

    if previous_status is None or previous_status == current_status:
        return None
    if current_status == "normal" and previous_status not in ["warning", "critical"]:
        return None
    if current_status not in ["warning", "critical", "normal"]:
        return None

    severity = "RESOLVED"
    title = "Sensor returned to safe range"
    if current_status == "warning":
        severity = "WARNING"
        title = "Sensor crossed warning limit"
    elif current_status == "critical":
        severity = "DANGER"
        title = "Sensor crossed danger limit"

    alert = {
        "id": f"ALERT-{uuid.uuid4().hex[:7].upper()}",
        "mine_id": mine["id"],
        "mine_name": mine["name"],
        "parameter": reading["parameter"],
        "label": reading["label"],
        "severity": severity,
        "status": current_status,
        "previous_status": previous_status,
        "value": reading["value"],
        "unit": reading.get("unit") or "",
        "threshold": _reading_threshold_text(reading),
        "title": title,
        "message": f"{reading['label']} at {mine['name']} changed from {previous_status} to {current_status}. Current value: {reading['value']} {reading.get('unit') or ''}.",
        "solution": "Reading is back in safe range. Continue monitoring and keep the last corrective action note in the shift log." if severity == "RESOLVED" else _alert_solution(reading),
        "timestamp": datetime.now().isoformat(),
        "acknowledged": severity == "RESOLVED",
    }
    sensor_alerts_db.insert(0, alert)
    del sensor_alerts_db[80:]
    return alert


def _initial_parameter_value(mine: Dict[str, Any], parameter: str):
    gas = mine.get("gas_status", {})
    if parameter == "ch4":
        return min(gas.get("ch4_pct", 0.04), 0.55)
    if parameter == "co":
        return min(gas.get("co_ppm", 5), 25)
    if parameter == "o2":
        return 20.8 if mine.get("type") == "Underground" else 20.9
    if parameter == "ventilation_air_velocity":
        return 0.72 if mine.get("type") == "Underground" else 0.9
    if parameter == "blast_vibration":
        return 4.5
    if parameter == "respirable_dust":
        return min(round(gas.get("pm10_ugm3", 120) / 100, 2), 1.65)
    if parameter == "temperature":
        return 31.5 if mine.get("type") == "Underground" else 34.0
    if parameter == "pressure":
        return 100.8 if mine.get("type") == "Underground" else 101.1
    if parameter == "light_intensity":
        return 165 if mine.get("type") == "Underground" else 320
    if parameter == "daily_production":
        return mine.get("current_production_tonnes", 0)
    if parameter == "equipment_uptime":
        return 88 if mine.get("risk_level") != "High" else 84
    if parameter == "safety_equipment_status":
        return "functional"
    return None


def _record_for(mine: Dict[str, Any], parameter: str, value, timestamp=None):
    meta = PARAMETER_DEFINITIONS[parameter]
    status = parameter_status(
        parameter,
        value,
        target_value=mine.get("daily_target_tonnes"),
        last_inspection_date=mine.get("last_inspection_date"),
    )
    return {
        "mine_id": mine["id"],
        "parameter": parameter,
        "label": meta["label"],
        "category": meta["category"],
        "device": meta["device"],
        "placement": meta["placement"],
        "unit": meta["unit"],
        "value": value,
        "status": status,
        "timestamp": timestamp or datetime.now().isoformat(),
        "warning_threshold": meta.get("warning_threshold"),
        "danger_threshold": meta.get("danger_threshold"),
        "auto_logged": parameter in ["last_inspection_date", "safety_equipment_status"],
    }


def _sync_mine_from_sensor(mine: Dict[str, Any], parameter: str, value):
    gas = mine.setdefault("gas_status", {})
    if parameter == "ch4":
        gas["ch4_pct"] = round(float(value), 2)
    elif parameter == "co":
        gas["co_ppm"] = round(float(value), 1)
    elif parameter == "respirable_dust":
        gas["pm10_ugm3"] = round(float(value) * 100, 1)
    elif parameter == "temperature":
        mine["temperature_c"] = round(float(value), 1)
    elif parameter == "pressure":
        mine["pressure_kpa"] = round(float(value), 1)
    elif parameter == "light_intensity":
        mine["light_lux"] = round(float(value), 1)
    elif parameter == "daily_production":
        mine["current_production_tonnes"] = int(float(value))
    elif parameter == "equipment_uptime":
        mine["equipment_uptime_pct"] = round(float(value), 1)
    elif parameter == "safety_equipment_status":
        mine["safety_equipment_status"] = value


def _create_iot_escalation(mine: Dict[str, Any], reading: Dict[str, Any]):
    alert_tag = f"IoT danger alert: {reading['label']}"
    already_open = any(
        i.get("mine_id") == mine["id"]
        and i.get("status") == "ESCALATED_TO_GM"
        and alert_tag in i.get("findings", "")
        for i in inspections_db
    )
    if already_open:
        return

    record = {
        "id": f"IOT-{uuid.uuid4().hex[:6].upper()}",
        "mine_id": mine["id"],
        "mine_name": mine["name"],
        "inspector_name": "KhananRakshak IoT Gateway",
        "inspector_role": "Automated Sensor Logger",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "lat": mine["lat"],
        "lng": mine["lng"],
        "type": "Automatic IoT Threshold Breach",
        "findings": f"{alert_tag} reached {reading['value']} {reading['unit']} at {mine['name']}.",
        "violation_class": "Class A",
        "corrective_action_required": "Dispatch safety officer, isolate affected zone, and verify sensor calibration.",
        "sla_deadline": datetime.now().strftime("%Y-%m-%d 18:00:00"),
        "status": "ESCALATED_TO_GM",
        "photo_url": "/static/iot_sensor_alert.jpg"
    }
    inspections_db.insert(0, record)
    mine["active_violations"] = mine.get("active_violations", 0) + 1
    mine["risk_level"] = "High"


def ingest_sensor_reading(mine_id: str, parameter: str, value, timestamp: Optional[str] = None):
    global last_sensor_sync
    mine = _mine_by_id(mine_id)
    if not mine:
        raise HTTPException(status_code=404, detail="Mine not found")
    if parameter not in applicable_parameters(mine.get("type")):
        raise HTTPException(status_code=400, detail="Parameter is not applicable for this mine type")

    reading = _record_for(mine, parameter, value, timestamp)
    iot_readings_db.setdefault(mine_id, {})[parameter] = reading
    _sync_mine_from_sensor(mine, parameter, value)
    last_sensor_sync = datetime.now()
    alert = _record_sensor_alert(mine, reading)

    if parameter in ENVIRONMENTAL_KEYS and reading["status"] == "critical":
        _create_iot_escalation(mine, reading)
    _publish_sensor_update(mine_id, parameter, alert)
    return reading


def init_iot_state():
    for mine in mines_db:
        for parameter in applicable_parameters(mine.get("type")):
            value = mine.get("last_inspection_date") if parameter == "last_inspection_date" else _initial_parameter_value(mine, parameter)
            ingest_sensor_reading(mine["id"], parameter, value)


def get_mine_parameter_snapshot(mine: Dict[str, Any]):
    existing = iot_readings_db.setdefault(mine["id"], {})
    rows = []
    for parameter in applicable_parameters(mine.get("type")):
        if parameter == "last_inspection_date":
            existing[parameter] = _record_for(mine, parameter, mine.get("last_inspection_date"))
        elif parameter not in existing:
            ingest_sensor_reading(mine["id"], parameter, _initial_parameter_value(mine, parameter))
        rows.append(existing[parameter])
    return rows


init_iot_state()

# Models
class NewInspection(BaseModel):
    mine_id: str
    inspector_name: str
    inspector_role: str
    type: str
    findings: str
    violation_class: str
    corrective_action_required: str
    lat: float
    lng: float
    photo_url: Optional[str] = None

class ComplianceStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

class SensorReading(BaseModel):
    mine_id: str
    parameter: str
    value: Any
    timestamp: Optional[str] = None
    hold_minutes: Optional[int] = 10

class SensorOverrideClear(BaseModel):
    mine_id: Optional[str] = None
    parameter: Optional[str] = None

class AlertAcknowledge(BaseModel):
    acknowledged: Optional[bool] = True


def _next_simulated_value(mine: Dict[str, Any], parameter: str):
    current = iot_readings_db.get(mine["id"], {}).get(parameter, {}).get("value")
    if current is None:
        current = _initial_parameter_value(mine, parameter)

    if parameter == "safety_equipment_status":
        return random.choice(SAFETY_STATUSES) if random.randint(1, 40) == 1 else current
    if parameter == "daily_production":
        target = mine.get("daily_target_tonnes", current or 1)
        return max(0, int(float(current) + random.uniform(-0.02, 0.02) * target))

    drift = {
        "ch4": 0.03,
        "co": 2.5,
        "o2": 0.06,
        "ventilation_air_velocity": 0.05,
        "blast_vibration": 1.0,
        "respirable_dust": 0.12,
        "temperature": 0.8,
        "pressure": 0.25,
        "light_intensity": 12,
        "equipment_uptime": 1.8,
    }.get(parameter, 1)
    value = float(current) + random.uniform(-drift, drift)
    if parameter == "ch4":
        return round(min(0.62, max(0.02, value)), 2)
    if parameter == "co":
        return round(min(35, max(2, value)), 1)
    if parameter == "o2":
        return round(min(21.0, max(19.6, value)), 2)
    if parameter == "ventilation_air_velocity":
        return round(min(1.3, max(0.58, value)), 2)
    if parameter == "blast_vibration":
        return round(min(8.5, max(1.5, value)), 2)
    if parameter == "respirable_dust":
        return round(min(1.75, max(0.4, value)), 2)
    if parameter == "temperature":
        return round(min(37.0, max(26.0, value)), 1)
    if parameter == "pressure":
        return round(min(102.5, max(97.0, value)), 1)
    if parameter == "light_intensity":
        return round(min(420, max(80, value)), 1)
    if parameter == "equipment_uptime":
        return round(min(98, max(82, value)), 1)
    return round(max(0, value), 2)


async def iot_simulator_loop():
    await asyncio.sleep(2)
    while True:
        try:
            for mine in mines_db:
                keys = [
                    p for p in applicable_parameters(mine.get("type"))
                    if p in SIMULATED_SENSOR_KEYS
                ]
                for parameter in keys:
                    expiry = manual_sensor_overrides_db.get(_override_key(mine["id"], parameter))
                    if expiry and expiry > datetime.now():
                        continue
                    if expiry and expiry <= datetime.now():
                        manual_sensor_overrides_db.pop(_override_key(mine["id"], parameter), None)
                    value = _next_simulated_value(mine, parameter)
                    ingest_sensor_reading(mine["id"], parameter, value)
        except Exception as exc:
            print("IoT simulator tick failed:", exc)
        await asyncio.sleep(20)


@app.on_event("startup")
async def start_iot_simulator():
    global simulator_task
    if simulator_task is None or simulator_task.done():
        simulator_task = asyncio.create_task(iot_simulator_loop())

# --- API Endpoints ---

@app.get("/api/overview")
def get_national_overview():
    """National-level summary for Corporate HQ (CIL / Ministry of Coal)"""
    total_mines = len(mines_db)
    high_risk_mines = [m for m in mines_db if m.get("risk_level") == "High"]
    overdue_compliances = [c for c in compliances_db if c.get("status") == "OVERDUE"]
    open_violations = [i for i in inspections_db if i.get("status") in ["OPEN", "ESCALATED_TO_GM"]]
    
    avg_compliance = round(sum(m.get("statutory_compliance_score", 0) for m in mines_db) / max(1, total_mines), 1)

    # Subsidiary breakdown
    sub_stats = {}
    for sub in SUBSIDIARIES:
        sub_id = sub["id"]
        sub_mines = [m for m in mines_db if m.get("subsidiary") == sub_id]
        if sub_mines:
            avg_sub_score = round(sum(m["statutory_compliance_score"] for m in sub_mines) / len(sub_mines), 1)
            high_risk_cnt = len([m for m in sub_mines if m.get("risk_level") == "High"])
        else:
            avg_sub_score = 92.0 # baseline
            high_risk_cnt = 0
            
        sub_stats[sub_id] = {
            "name": sub["name"],
            "state": sub["state"],
            "headquarters": sub["headquarters"],
            "mines_count": len(sub_mines) or sub["total_mines"],
            "avg_compliance": avg_sub_score,
            "high_risk_count": high_risk_cnt
        }

    return {
        "timestamp": datetime.now().isoformat(),
        "total_active_mines_monitored": total_mines,
        "national_compliance_index_pct": avg_compliance,
        "high_risk_mines_count": len(high_risk_mines),
        "overdue_statutory_items": len(overdue_compliances),
        "active_safety_violations": len(open_violations),
        "active_iot_sensors": sum(
            len([p for p in applicable_parameters(m.get("type")) if p in SIMULATED_SENSOR_KEYS])
            for m in mines_db
        ),
        "last_sensor_sync_seconds": max(0, int((datetime.now() - last_sensor_sync).total_seconds())),
        "subsidiary_breakdown": sub_stats
    }

@app.get("/api/mines")
def list_mines(subsidiary: Optional[str] = None, risk_filter: Optional[str] = None):
    """List mines with computed real-time AI risk evaluation"""
    results = []
    for mine in mines_db:
        params = get_mine_parameter_snapshot(mine)
        mine_for_ai = {**mine, "iot_parameters": params}
        if subsidiary and mine.get("subsidiary") != subsidiary:
            continue
        if risk_filter and mine.get("risk_level") != risk_filter:
            continue
            
        ai_assessment = MiningAIRiskEngine.calculate_mine_risk_score(mine_for_ai, compliances_db, inspections_db)
        anomaly = MiningAIRiskEngine.detect_production_compliance_anomaly(mine_for_ai)
        uptime = next((p for p in params if p["parameter"] == "equipment_uptime"), None)
        safety_status = next((p for p in params if p["parameter"] == "safety_equipment_status"), None)
        
        results.append({
            **mine,
            "ai_risk_assessment": ai_assessment,
            "production_anomaly": anomaly,
            "equipment_uptime_pct": uptime["value"] if uptime else None,
            "safety_equipment_status": safety_status["value"] if safety_status else "functional",
            "parameter_count": len(params)
        })
    return results

@app.get("/api/mines/{mine_id}")
def get_mine_details(mine_id: str):
    """Deep-dive for colliery manager & DGMS inspector"""
    mine = next((m for m in mines_db if m["id"] == mine_id), None)
    if not mine:
        raise HTTPException(status_code=404, detail="Mine not found")

    mine_compliances = [c for c in compliances_db if c.get("mine_id") == mine_id]
    mine_inspections = [i for i in inspections_db if i.get("mine_id") == mine_id]
    mine_contractors = [c for c in contractors_db if c.get("mine_id") == mine_id]
    
    params = get_mine_parameter_snapshot(mine)
    mine_for_ai = {**mine, "iot_parameters": params}
    ai_risk = MiningAIRiskEngine.calculate_mine_risk_score(mine_for_ai, compliances_db, inspections_db)
    anomaly = MiningAIRiskEngine.detect_production_compliance_anomaly(mine_for_ai)

    return {
        "mine": mine,
        "compliances": mine_compliances,
        "inspections": mine_inspections,
        "contractors": mine_contractors,
        "parameters": params,
        "ai_risk_report": ai_risk,
        "production_anomaly": anomaly
    }

@app.post("/iot/ingest")
@app.post("/api/iot/ingest")
def ingest_iot_reading(payload: SensorReading):
    """Accept a real or simulated IoT sensor reading."""
    before_alert_count = len(sensor_alerts_db)
    reading = ingest_sensor_reading(payload.mine_id, payload.parameter, payload.value, payload.timestamp)
    minutes = max(1, min(payload.hold_minutes or 10, 60))
    manual_sensor_overrides_db[_override_key(payload.mine_id, payload.parameter)] = datetime.now() + timedelta(minutes=minutes)
    alert = sensor_alerts_db[0] if len(sensor_alerts_db) > before_alert_count else None
    return {"message": "IoT reading logged", "reading": reading, "alert": alert}

@app.post("/api/iot/overrides/clear")
def clear_sensor_override(payload: SensorOverrideClear):
    removed = 0
    for key in list(manual_sensor_overrides_db.keys()):
        mine_match = payload.mine_id is None or key.startswith(f"{payload.mine_id}:")
        parameter_match = payload.parameter is None or key.endswith(f":{payload.parameter}")
        if mine_match and parameter_match:
            manual_sensor_overrides_db.pop(key, None)
            removed += 1
    _publish_sensor_update(payload.mine_id, payload.parameter)
    return {"message": "Manual sensor hold cleared", "removed": removed}

@app.get("/api/alerts")
def get_sensor_alerts(include_acknowledged: bool = False):
    if include_acknowledged:
        return sensor_alerts_db
    return [
        alert for alert in sensor_alerts_db
        if not alert.get("acknowledged") and alert.get("severity") in ["WARNING", "DANGER"]
    ]

@app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_sensor_alert(alert_id: str, payload: AlertAcknowledge = Body(default=AlertAcknowledge())):
    alert = next((item for item in sensor_alerts_db if item["id"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert["acknowledged"] = bool(payload.acknowledged)
    _publish_sensor_update(alert["mine_id"], alert["parameter"], alert)
    return {"message": "Alert updated", "alert": alert}

@app.get("/api/iot/events")
async def sensor_event_stream():
    async def event_generator():
        seen_version = -1
        while True:
            if last_sensor_event["version"] != seen_version:
                seen_version = last_sensor_event["version"]
                yield f"data: {json.dumps(last_sensor_event)}\n\n"
            await asyncio.sleep(0.2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/mines/{mine_id}/parameters")
@app.get("/api/mines/{mine_id}/parameters")
def get_mine_parameters(mine_id: str):
    """Current parameter values for one mine, grouped for the UI panel."""
    mine = _mine_by_id(mine_id)
    if not mine:
        raise HTTPException(status_code=404, detail="Mine not found")
    rows = get_mine_parameter_snapshot(mine)
    return {
        "mine_id": mine["id"],
        "mine_name": mine["name"],
        "mine_type": mine["type"],
        "last_synced_seconds": max(0, int((datetime.now() - last_sensor_sync).total_seconds())),
        "parameters": rows
    }

@app.get("/api/compliances")
def get_all_compliances(status: Optional[str] = None):
    """Get statutory compliance register"""
    if status:
        return [c for c in compliances_db if c.get("status") == status]
    return compliances_db

@app.post("/api/compliances/{compliance_id}/update-status")
def update_compliance_status(compliance_id: str, update: ComplianceStatusUpdate):
    """Update compliance state (e.g. COMPLIED, IN_PROGRESS, OVERDUE)"""
    comp = next((c for c in compliances_db if c["id"] == compliance_id), None)
    if not comp:
        raise HTTPException(status_code=404, detail="Compliance item not found")
    
    comp["status"] = update.status
    if update.notes:
        comp["closure_notes"] = update.notes
    comp["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"message": "Compliance updated successfully", "compliance": comp}

@app.get("/api/inspections")
def get_inspections():
    """List all field inspections and audits"""
    return inspections_db

@app.post("/api/inspections")
def submit_field_inspection(insp: NewInspection):
    """Submit geo-tagged and time-stamped mobile inspection"""
    new_id = f"INSP-{uuid.uuid4().hex[:6].upper()}"
    sla = datetime.now().strftime("%Y-%m-%d 18:00:00")
    
    # Check automated escalation rule: Class A violations are escalated if not closed immediately
    status = "OPEN"
    if insp.violation_class == "Class A":
        status = "ESCALATED_TO_GM"

    mine = next((m for m in mines_db if m["id"] == insp.mine_id), None)
    mine_name = mine["name"] if mine else "Unknown Mine"

    record = {
        "id": new_id,
        "mine_id": insp.mine_id,
        "mine_name": mine_name,
        "inspector_name": insp.inspector_name,
        "inspector_role": insp.inspector_role,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "lat": insp.lat,
        "lng": insp.lng,
        "type": insp.type,
        "findings": insp.findings,
        "violation_class": insp.violation_class,
        "corrective_action_required": insp.corrective_action_required,
        "sla_deadline": sla,
        "status": status,
        "photo_url": insp.photo_url or "/static/evidence_placeholder.jpg"
    }
    
    inspections_db.insert(0, record)
    
    # Recalculate mine risk level if Class A
    if mine:
        mine["active_violations"] = mine.get("active_violations", 0) + 1
        mine["last_inspection_date"] = record["date"][:10]
        ingest_sensor_reading(mine["id"], "last_inspection_date", mine["last_inspection_date"])
        if insp.violation_class == "Class A":
            mine["risk_level"] = "High"

    return {
        "message": "Field Inspection logged & geo-tagged successfully",
        "inspection": record
    }

@app.get("/api/gis/map-data")
def get_gis_layers():
    """Returns geo-features for Leaflet GIS mapping"""
    features = []
    for mine in mines_db:
        ai_risk = MiningAIRiskEngine.calculate_mine_risk_score(mine, compliances_db, inspections_db)
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [mine["lng"], mine["lat"]]
            },
            "properties": {
                "id": mine["id"],
                "name": mine["name"],
                "subsidiary": mine["subsidiary"],
                "area": mine["area"],
                "type": mine["type"],
                "risk_score": ai_risk["risk_score"],
                "risk_status": ai_risk["risk_status"],
                "color_code": ai_risk["color_code"],
                "ch4": mine["gas_status"].get("ch4_pct", 0),
                "co": mine["gas_status"].get("co_ppm", 0),
                "pm10": mine["gas_status"].get("pm10_ugm3", 0),
                "pending_compliances": mine["pending_compliances"],
                "active_violations": mine["active_violations"]
            }
        })
    return {
        "type": "FeatureCollection",
        "features": features
    }

# Mount static frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
