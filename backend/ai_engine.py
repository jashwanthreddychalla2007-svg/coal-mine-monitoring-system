"""
AI Risk Scoring & Predictive Anomaly Engine for Coal Mining Operations
Calculates composite Mine Risk Index (MRI), flags statutory non-compliance probability,
and performs automated safety anomaly detection.
"""

from typing import Dict, Any, List
import math

class MiningAIRiskEngine:
    
    @staticmethod
    def calculate_mine_risk_score(mine_data: Dict[str, Any], compliances: List[Dict[str, Any]], inspections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates a dynamic risk score between 0 (Very Safe) and 100 (Severe Danger).
        Factors:
        - Gas Telemetry & Environmental conditions (35% weight)
        - Overdue Statutory Compliances (25% weight)
        - Active Class A/B Safety Violations (25% weight)
        - Historical Compliance Baseline (15% weight)
        """
        score = 0.0
        explanations = []
        recommendations = []

        # 1. Environmental & Gas Telemetry (Max 35 pts)
        gas = mine_data.get("gas_status", {})
        ch4 = gas.get("ch4_pct", 0.0)
        co = gas.get("co_ppm", 0)
        pm10 = gas.get("pm10_ugm3", 50)

        # Methane scoring (Underground explosive range 5-15%, DGMS danger limit > 0.75%)
        if mine_data.get("type") == "Underground":
            if ch4 >= 0.75:
                score += 30
                explanations.append(f"CRITICAL: Methane concentration ({ch4}%) reached statutory action limit (DGMS CMR 169).")
                recommendations.append("Immediate cutting of electrical power in section & withdraw workforce to intake airway.")
            elif ch4 >= 0.5:
                score += 18
                explanations.append(f"WARNING: Elevated Methane ({ch4}%) approaching statutory threshold.")
                recommendations.append("Increase auxiliary ventilation air velocity to minimum 0.5 m/s.")
            elif ch4 > 0.1:
                score += 5

            # Carbon monoxide (indicator of spontaneous combustion in coal seams)
            if co > 20:
                score += 15
                explanations.append(f"CRITICAL: CO level at {co} ppm indicates spontaneous heating in goaf.")
                recommendations.append("Deploy nitrogen flushing / sealant injection in sealed off panels.")
            elif co > 10:
                score += 8
                explanations.append(f"Elevated Carbon Monoxide ({co} ppm) detected.")
        else:
            # Opencast Dust & Particulate scoring
            if pm10 > 250:
                score += 20
                explanations.append(f"CPCB Threshold Exceeded: PM10 is {pm10} ug/m3 (Limit 100 ug/m3).")
                recommendations.append("Activate high-pressure mist cannons and wet drilling protocols immediately.")
            elif pm10 > 150:
                score += 10
                explanations.append(f"Moderate Dust Alert: PM10 is {pm10} ug/m3.")
                recommendations.append("Increase water bowser spraying rounds on haul road.")

        # Parameter panel readings used for demo-time what-if changes
        parameter_rows = mine_data.get("iot_parameters", [])
        watched_parameters = {
            "ch4": "Methane",
            "co": "Carbon monoxide",
            "o2": "Oxygen",
            "ventilation_air_velocity": "Ventilation air velocity",
            "blast_vibration": "Blast vibration",
            "respirable_dust": "Respirable dust",
            "temperature": "Ambient temperature",
            "pressure": "Atmospheric pressure",
            "light_intensity": "Light intensity",
            "equipment_uptime": "Equipment uptime",
            "safety_equipment_status": "Safety equipment status",
        }
        for row in parameter_rows:
            key = row.get("parameter")
            status_value = row.get("status")
            if key not in watched_parameters or status_value == "normal":
                continue

            label = watched_parameters[key]
            value = row.get("value")
            unit = row.get("unit") or ""
            if status_value == "critical":
                score += 14 if key in ["equipment_uptime", "safety_equipment_status"] else 18
                explanations.append(f"CRITICAL: {label} reading is {value} {unit}.")
                recommendations.append(f"Take immediate corrective action for {label.lower()} and recheck the sensor reading.")
            elif status_value == "warning":
                score += 7 if key in ["equipment_uptime", "safety_equipment_status"] else 9
                explanations.append(f"WARNING: {label} reading is {value} {unit}.")
                recommendations.append(f"Monitor {label.lower()} closely and schedule correction before it becomes critical.")

        # 2. Overdue Statutory Compliances (Max 25 pts)
        mine_compliances = [c for c in compliances if c.get("mine_id") == mine_data.get("id")]
        overdue_critical = [c for c in mine_compliances if c.get("status") == "OVERDUE" and "Class A" in c.get("criticality", "")]
        overdue_other = [c for c in mine_compliances if c.get("status") == "OVERDUE" and "Class A" not in c.get("criticality", "")]

        if overdue_critical:
            score += min(25, len(overdue_critical) * 15)
            explanations.append(f"{len(overdue_critical)} Class-A Statutory requirement(s) are OVERDUE!")
            recommendations.append("Urgent DGMS clearance submission required to avoid Sec 22 closure order.")
        elif overdue_other:
            score += min(15, len(overdue_other) * 6)
            explanations.append(f"{len(overdue_other)} Statutory compliance item(s) pending beyond deadline.")

        # 3. Active Safety Violations & Escalations (Max 25 pts)
        mine_inspections = [i for i in inspections if i.get("mine_id") == mine_data.get("id")]
        open_violations = [i for i in mine_inspections if i.get("status") in ["OPEN", "ESCALATED_TO_GM"]]
        escalated = [i for i in open_violations if i.get("status") == "ESCALATED_TO_GM"]

        if escalated:
            score += 25
            explanations.append(f"CRITICAL ESCALATION: {len(escalated)} safety violation(s) escalated to General Manager level.")
            recommendations.append("Immediate compliance audit by Subsidiary Safety Director.")
        elif open_violations:
            score += min(20, len(open_violations) * 10)
            explanations.append(f"{len(open_violations)} unrectified field inspection violation(s).")

        # 4. Compliance Score Baseline Deficit (Max 15 pts)
        base_compliance = mine_data.get("statutory_compliance_score", 100.0)
        if base_compliance < 80:
            score += 15
            explanations.append(f"Poor overall statutory compliance history ({base_compliance}%).")
        elif base_compliance < 90:
            score += 8

        # Cap score between 0 and 100
        final_score = min(100.0, round(score, 1))

        if final_score >= 70:
            status = "CRITICAL HAZARD"
            color = "#ef4444" # red
        elif final_score >= 40:
            status = "ELEVATED RISK"
            color = "#f59e0b" # amber
        else:
            status = "COMPLIANT / SAFE"
            color = "#10b981" # emerald

        if not explanations:
            explanations.append("All statutory safety and environmental metrics within DGMS/CPCB limits.")
        if not recommendations:
            recommendations.append("Continue regular shift statutory inspections and sensor calibration.")

        return {
            "mine_id": mine_data.get("id"),
            "mine_name": mine_data.get("name"),
            "risk_score": final_score,
            "risk_status": status,
            "color_code": color,
            "primary_factors": explanations,
            "ai_corrective_recommendations": recommendations,
            "predicted_incident_probability_pct": min(95.0, round(final_score * 0.9, 1))
        }

    @staticmethod
    def detect_production_compliance_anomaly(mine_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects anomalies such as production outpacing approved environmental clearance (EC) limit
        or severe underproduction due to safety bottlenecks.
        """
        target = mine_data.get("daily_target_tonnes", 1)
        actual = mine_data.get("current_production_tonnes", 0)
        variance_pct = ((actual - target) / target) * 100

        is_anomaly = False
        anomaly_type = "NORMAL"
        msg = f"Production tracking normal ({actual:,} MT vs {target:,} MT target)."

        if variance_pct > 15:
            is_anomaly = True
            anomaly_type = "OVER_EXTRACTION_RISK"
            msg = f"WARNING: Production exceeds daily target by {variance_pct:.1f}%. Verify that production does not breach MoEFCC Environmental Clearance (EC) annual ceiling."
        elif variance_pct < -20:
            is_anomaly = True
            anomaly_type = "OPERATIONAL_BOTTLENECK"
            msg = f"ALERT: Significant production shortfall of {abs(variance_pct):.1f}%. Likely caused by equipment breakdown, blasting delay, or statutory stoppage."

        return {
            "is_anomaly": is_anomaly,
            "anomaly_type": anomaly_type,
            "variance_percentage": round(variance_pct, 1),
            "description": msg
        }
