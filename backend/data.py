import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

SUBSIDIARIES = [
    {"id": "BCCL", "name": "Bharat Coking Coal Limited", "state": "Jharkhand", "headquarters": "Dhanbad", "total_mines": 36},
    {"id": "ECL", "name": "Eastern Coalfields Limited", "state": "West Bengal / Jharkhand", "headquarters": "Sanctoria", "total_mines": 75},
    {"id": "CCL", "name": "Central Coalfields Limited", "state": "Jharkhand", "headquarters": "Ranchi", "total_mines": 42},
    {"id": "WCL", "name": "Western Coalfields Limited", "state": "Maharashtra / MP", "headquarters": "Nagpur", "total_mines": 58},
    {"id": "SECL", "name": "South Eastern Coalfields Limited", "state": "Chhattisgarh / MP", "headquarters": "Bilaspur", "total_mines": 67},
    {"id": "MCL", "name": "Mahanadi Coalfields Limited", "state": "Odisha", "headquarters": "Sambalpur", "total_mines": 18},
    {"id": "NCL", "name": "Northern Coalfields Limited", "state": "MP / UP", "headquarters": "Singrauli", "total_mines": 10},
    {"id": "CMPDI", "name": "Central Mine Planning & Design Institute", "state": "Pan-India", "headquarters": "Ranchi", "total_mines": 0}
]

SAMPLE_MINES = [
    {
        "id": "MINE-001",
        "name": "Jharia Opencast Block IV",
        "subsidiary": "BCCL",
        "area": "Dhanbad Area",
        "type": "Opencast",
        "lat": 23.7438,
        "lng": 86.4116,
        "daily_target_tonnes": 12500,
        "current_production_tonnes": 11800,
        "manager_name": "Rajesh K. Sharma (First Class Mgr)",
        "safety_officer": "Alok Verma",
        "statutory_compliance_score": 92.4,
        "risk_level": "Medium",
        "gas_status": {"ch4_pct": 0.02, "co_ppm": 4, "pm10_ugm3": 142, "status": "Normal"},
        "pending_compliances": 2,
        "active_violations": 1,
        "last_inspection_date": "2026-09-12"
    },
    {
        "id": "MINE-002",
        "name": "Moonidih Deep Underground",
        "subsidiary": "BCCL",
        "area": "Western Jharia",
        "type": "Underground",
        "lat": 23.7380,
        "lng": 86.3520,
        "daily_target_tonnes": 3200,
        "current_production_tonnes": 2950,
        "manager_name": "Dr. Pradeep Sengupta",
        "safety_officer": "R. C. Murmu",
        "statutory_compliance_score": 78.5,
        "risk_level": "High",
        "gas_status": {"ch4_pct": 0.65, "co_ppm": 19, "pm10_ugm3": 185, "status": "Warning - Elevated Methane"},
        "pending_compliances": 6,
        "active_violations": 3,
        "last_inspection_date": "2026-09-15"
    },
    {
        "id": "MINE-003",
        "name": "Gevra Mega Opencast Project",
        "subsidiary": "SECL",
        "area": "Korba",
        "type": "Opencast",
        "lat": 22.3512,
        "lng": 82.6841,
        "daily_target_tonnes": 150000,
        "current_production_tonnes": 152300,
        "manager_name": "S. N. Tiwari",
        "safety_officer": "Virendra Chouhan",
        "statutory_compliance_score": 96.8,
        "risk_level": "Low",
        "gas_status": {"ch4_pct": 0.0, "co_ppm": 2, "pm10_ugm3": 95, "status": "Normal"},
        "pending_compliances": 1,
        "active_violations": 0,
        "last_inspection_date": "2026-09-10"
    },
    {
        "id": "MINE-004",
        "name": "Kusmunda Colliery",
        "subsidiary": "SECL",
        "area": "Korba Area",
        "type": "Opencast",
        "lat": 22.3394,
        "lng": 82.6980,
        "daily_target_tonnes": 95000,
        "current_production_tonnes": 89000,
        "manager_name": "Anil Kumar Mishra",
        "safety_officer": "S. P. Singh",
        "statutory_compliance_score": 88.2,
        "risk_level": "Medium",
        "gas_status": {"ch4_pct": 0.01, "co_ppm": 6, "pm10_ugm3": 160, "status": "Normal"},
        "pending_compliances": 3,
        "active_violations": 1,
        "last_inspection_date": "2026-09-08"
    },
    {
        "id": "MINE-005",
        "name": "Rajmahal OCP (Lalmatia)",
        "subsidiary": "ECL",
        "area": "Rajmahal",
        "type": "Opencast",
        "lat": 25.0489,
        "lng": 87.3518,
        "daily_target_tonnes": 48000,
        "current_production_tonnes": 44500,
        "manager_name": "Debabrata Mondal",
        "safety_officer": "K. K. Hansda",
        "statutory_compliance_score": 81.0,
        "risk_level": "High",
        "gas_status": {"ch4_pct": 0.01, "co_ppm": 5, "pm10_ugm3": 210, "status": "High Slope Instability Alert"},
        "pending_compliances": 5,
        "active_violations": 2,
        "last_inspection_date": "2026-09-14"
    },
    {
        "id": "MINE-006",
        "name": "Bhubaneswari OCP",
        "subsidiary": "MCL",
        "area": "Talcher",
        "type": "Opencast",
        "lat": 20.9587,
        "lng": 85.1952,
        "daily_target_tonnes": 80000,
        "current_production_tonnes": 81200,
        "manager_name": "M. K. Nayak",
        "safety_officer": "B. B. Rout",
        "statutory_compliance_score": 94.5,
        "risk_level": "Low",
        "gas_status": {"ch4_pct": 0.0, "co_ppm": 3, "pm10_ugm3": 110, "status": "Normal"},
        "pending_compliances": 1,
        "active_violations": 0,
        "last_inspection_date": "2026-09-11"
    },
    {
        "id": "MINE-007",
        "name": "Jayant Open Cast Project",
        "subsidiary": "NCL",
        "area": "Singrauli",
        "type": "Opencast",
        "lat": 24.1206,
        "lng": 82.6450,
        "daily_target_tonnes": 70000,
        "current_production_tonnes": 68900,
        "manager_name": "P. K. Dubey",
        "safety_officer": "R. P. Tripathi",
        "statutory_compliance_score": 97.2,
        "risk_level": "Low",
        "gas_status": {"ch4_pct": 0.0, "co_ppm": 2, "pm10_ugm3": 88, "status": "Normal"},
        "pending_compliances": 0,
        "active_violations": 0,
        "last_inspection_date": "2026-09-16"
    }
]

STATUTORY_COMPLIANCES = [
    {
        "id": "COMP-101",
        "mine_id": "MINE-002",
        "mine_name": "Moonidih Deep Underground",
        "category": "DGMS Safety (CMR 2017)",
        "regulation": "Reg 169 - Continuous Multi-Gas Telemetry & Vent Monitoring",
        "frequency": "Daily / Real-Time",
        "due_date": "2026-09-17",
        "status": "OVERDUE",
        "criticality": "Class A - Critical",
        "penalty_risk": "DGMS Notice under Sec 22(3) of Mines Act",
        "responsible_officer": "Dr. Pradeep Sengupta"
    },
    {
        "id": "COMP-102",
        "mine_id": "MINE-002",
        "mine_name": "Moonidih Deep Underground",
        "category": "Mines Safety",
        "regulation": "Reg 152 - Stone Dust Barrier Maintenance and Incombustible Dust Sample Analysis",
        "frequency": "Monthly",
        "due_date": "2026-09-20",
        "status": "PENDING",
        "criticality": "Class A - Critical",
        "penalty_risk": "High Explosion Hazard",
        "responsible_officer": "R. C. Murmu"
    },
    {
        "id": "COMP-103",
        "mine_id": "MINE-005",
        "mine_name": "Rajmahal OCP (Lalmatia)",
        "category": "DGMS Safety (CMR 2017)",
        "regulation": "Reg 106 - Slope Stability Radar Monitoring & Bench Height/Width Ratio",
        "frequency": "Weekly",
        "due_date": "2026-09-15",
        "status": "OVERDUE",
        "criticality": "Class A - Critical",
        "penalty_risk": "Pit Slope Failure Risk / Work Suspension",
        "responsible_officer": "Debabrata Mondal"
    },
    {
        "id": "COMP-104",
        "mine_id": "MINE-001",
        "mine_name": "Jharia Opencast Block IV",
        "category": "CPCB / Environmental",
        "regulation": "Air & Water Consent to Operate (CTO) Continuous Ambient Air Monitoring Station (CAAQMS)",
        "frequency": "Quarterly",
        "due_date": "2026-09-30",
        "status": "IN_PROGRESS",
        "criticality": "Class B - High",
        "penalty_risk": "Pollution Control Board Environmental Compensation",
        "responsible_officer": "Alok Verma"
    },
    {
        "id": "COMP-105",
        "mine_id": "MINE-003",
        "mine_name": "Gevra Mega Opencast Project",
        "category": "Forest & Environment (MoEFCC)",
        "regulation": "Stage-II Forest Clearance Compensatory Afforestation Audit Report",
        "frequency": "Bi-Annual",
        "due_date": "2026-10-15",
        "status": "COMPLIED",
        "criticality": "Class B - High",
        "penalty_risk": "None",
        "responsible_officer": "Virendra Chouhan"
    },
    {
        "id": "COMP-106",
        "mine_id": "MINE-004",
        "mine_name": "Kusmunda Colliery",
        "category": "Labour & Welfare",
        "regulation": "Contract Labour (R&A) Act - Initial & Periodical Medical Examination (IME/PME) Compliance for 450 dumper drivers",
        "frequency": "Yearly",
        "due_date": "2026-09-22",
        "status": "PENDING",
        "criticality": "Class B - High",
        "penalty_risk": "Welfare Commissioner Notice",
        "responsible_officer": "S. P. Singh"
    }
]

INSPECTION_REPORTS = [
    {
        "id": "INSP-8091",
        "mine_id": "MINE-002",
        "mine_name": "Moonidih Deep Underground",
        "inspector_name": "S. K. Gangopadhyay",
        "inspector_role": "Director of Mines Safety (DGMS, Dhanbad Region)",
        "date": "2026-09-15 11:30:00",
        "lat": 23.7381,
        "lng": 86.3522,
        "type": "Surprise Statutory Inspection",
        "findings": "Ventilation air velocity at Longwall face #3 fell below 0.3 m/s threshold. Localized methane accumulation (0.65%) observed near return airway.",
        "violation_class": "Class A",
        "corrective_action_required": "Immediate installation of booster auxiliary fan and real-time gas sensor recalibration.",
        "sla_deadline": "2026-09-17 18:00:00",
        "status": "ESCALATED_TO_GM",
        "photo_url": "/static/evidence_ch4.jpg"
    },
    {
        "id": "INSP-8092",
        "mine_id": "MINE-005",
        "mine_name": "Rajmahal OCP (Lalmatia)",
        "inspector_name": "R. N. Prasad",
        "inspector_role": "Internal Safety Officer (CIL Safety Board)",
        "date": "2026-09-14 09:15:00",
        "lat": 25.0491,
        "lng": 87.3520,
        "type": "Bench & Haul Road Safety Audit",
        "findings": "Haul road width between bench 4 and 5 narrowed to 2.5 times dumper width (CMR 2017 mandates 3x minimum). Berm height inadequate on southern flank.",
        "violation_class": "Class B",
        "corrective_action_required": "Widening of haul road curve and construction of 2-meter rock bund berm.",
        "sla_deadline": "2026-09-18 23:59:00",
        "status": "OPEN",
        "photo_url": "/static/evidence_haulroad.jpg"
    },
    {
        "id": "INSP-8093",
        "mine_id": "MINE-001",
        "mine_name": "Jharia Opencast Block IV",
        "inspector_name": "Sunita Rawat",
        "inspector_role": "State Pollution Control Board (JSPCB)",
        "date": "2026-09-12 14:00:00",
        "lat": 23.7440,
        "lng": 86.4120,
        "type": "Environmental & Dust Suppression Check",
        "findings": "Water mist misting canon near coal handling plant conveyor belt non-functional during 2nd shift.",
        "violation_class": "Class C",
        "corrective_action_required": "Nozzle descaling and water booster pump repair.",
        "sla_deadline": "2026-09-16 12:00:00",
        "status": "RESOLVED_VERIFIED",
        "photo_url": "/static/evidence_dust.jpg"
    }
]

CONTRACTORS = [
    {
        "id": "CONT-301",
        "name": "BEEPC Mining Services Ltd.",
        "mine_id": "MINE-001",
        "active_workers": 340,
        "safety_audit_score": 91.0,
        "certified_operators_pct": 98.5,
        "insurance_valid_until": "2027-03-31",
        "vetted_by_dgms": True,
        "risk_flag": "Low"
    },
    {
        "id": "CONT-302",
        "name": "Vindhya Earthmovers & Haulage",
        "mine_id": "MINE-005",
        "active_workers": 210,
        "safety_audit_score": 72.4,
        "certified_operators_pct": 81.0,
        "insurance_valid_until": "2026-10-10",
        "vetted_by_dgms": False,
        "risk_flag": "High - Expiring Certificates"
    },
    {
        "id": "CONT-303",
        "name": "Pragati Heavy Infra Infra Pvt Ltd",
        "mine_id": "MINE-003",
        "active_workers": 650,
        "safety_audit_score": 97.5,
        "certified_operators_pct": 100.0,
        "insurance_valid_until": "2027-08-30",
        "vetted_by_dgms": True,
        "risk_flag": "Low"
    }
]
