from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import uuid

from backend.data import SUBSIDIARIES, SAMPLE_MINES, STATUTORY_COMPLIANCES, INSPECTION_REPORTS, CONTRACTORS
from backend.ai_engine import MiningAIRiskEngine

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
        "subsidiary_breakdown": sub_stats
    }

@app.get("/api/mines")
def list_mines(subsidiary: Optional[str] = None, risk_filter: Optional[str] = None):
    """List mines with computed real-time AI risk evaluation"""
    results = []
    for mine in mines_db:
        if subsidiary and mine.get("subsidiary") != subsidiary:
            continue
        if risk_filter and mine.get("risk_level") != risk_filter:
            continue
            
        ai_assessment = MiningAIRiskEngine.calculate_mine_risk_score(mine, compliances_db, inspections_db)
        anomaly = MiningAIRiskEngine.detect_production_compliance_anomaly(mine)
        
        results.append({
            **mine,
            "ai_risk_assessment": ai_assessment,
            "production_anomaly": anomaly
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
    
    ai_risk = MiningAIRiskEngine.calculate_mine_risk_score(mine, compliances_db, inspections_db)
    anomaly = MiningAIRiskEngine.detect_production_compliance_anomaly(mine)

    return {
        "mine": mine,
        "compliances": mine_compliances,
        "inspections": mine_inspections,
        "contractors": mine_contractors,
        "ai_risk_report": ai_risk,
        "production_anomaly": anomaly
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
