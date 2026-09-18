from datetime import datetime


PARAMETER_DEFINITIONS = {
    "ch4": {
        "label": "Methane (CH4)",
        "category": "Environmental / Safety Parameters",
        "device": "Catalytic/IR methane sensor",
        "placement": "Roadways, working faces, return airways",
        "unit": "%",
        "warning_threshold": 0.75,
        "danger_threshold": 1.25,
        "mine_types": ["Underground"],
    },
    "co": {
        "label": "Carbon Monoxide (CO)",
        "category": "Environmental / Safety Parameters",
        "device": "Electrochemical CO sensor",
        "placement": "Near blasting zones, working faces",
        "unit": "ppm",
        "warning_threshold": 50,
        "danger_threshold": 100,
        "mine_types": ["Underground", "Opencast"],
    },
    "o2": {
        "label": "Oxygen (O2)",
        "category": "Environmental / Safety Parameters",
        "device": "Electrochemical O2 sensor",
        "placement": "Working faces, refuge chambers",
        "unit": "%",
        "warning_threshold": 19.5,
        "danger_threshold": 19.0,
        "lower_is_worse": True,
        "mine_types": ["Underground"],
    },
    "ventilation_air_velocity": {
        "label": "Ventilation air velocity",
        "category": "Environmental / Safety Parameters",
        "device": "Anemometer/airflow sensor",
        "placement": "Main ventilation ducts, airways",
        "unit": "m/s",
        "warning_threshold": 0.5,
        "danger_threshold": 0.25,
        "lower_is_worse": True,
        "mine_types": ["Underground"],
    },
    "blast_vibration": {
        "label": "Blast vibration",
        "category": "Environmental / Safety Parameters",
        "device": "Geophone/accelerometer",
        "placement": "Perimeter of opencast blast zone",
        "unit": "mm/s (PPV)",
        "warning_threshold": 10,
        "danger_threshold": 20,
        "mine_types": ["Opencast"],
    },
    "respirable_dust": {
        "label": "Respirable dust",
        "category": "Environmental / Safety Parameters",
        "device": "Laser/PM sensor",
        "placement": "Working faces, haul roads",
        "unit": "mg/m3",
        "warning_threshold": 2.0,
        "danger_threshold": 3.0,
        "mine_types": ["Underground", "Opencast"],
    },
    "daily_production": {
        "label": "Daily/Monthly production",
        "category": "Operational Parameters",
        "device": "Weighbridge/conveyor load sensor",
        "placement": "Coal handling plant / weighbridge",
        "unit": "tonnes",
        "mine_types": ["Underground", "Opencast"],
    },
    "equipment_uptime": {
        "label": "Equipment uptime",
        "category": "Operational Parameters",
        "device": "Machine telematics (vibration/RPM)",
        "placement": "HEMM fleet and conveyors",
        "unit": "%",
        "warning_threshold": 80,
        "danger_threshold": 60,
        "lower_is_worse": True,
        "mine_types": ["Underground", "Opencast"],
    },
    "last_inspection_date": {
        "label": "Last inspection date",
        "category": "Compliance/Safety Parameters",
        "device": "Auto-timestamped inspection form",
        "placement": "Inspection audit trail",
        "unit": "date",
        "mine_types": ["Underground", "Opencast"],
    },
    "safety_equipment_status": {
        "label": "Safety equipment functional status",
        "category": "Compliance/Safety Parameters",
        "device": "Simulated self-check status",
        "placement": "PPE / refuge / rescue equipment store",
        "unit": "status",
        "mine_types": ["Underground", "Opencast"],
    },
}

ENVIRONMENTAL_KEYS = {"ch4", "co", "o2", "ventilation_air_velocity", "blast_vibration", "respirable_dust"}
SIMULATED_SENSOR_KEYS = [key for key in PARAMETER_DEFINITIONS if key != "last_inspection_date"]


def applicable_parameters(mine_type):
    return [
        key for key, meta in PARAMETER_DEFINITIONS.items()
        if mine_type in meta.get("mine_types", [])
    ]


def parameter_status(parameter_key, value, target_value=None, last_inspection_date=None):
    meta = PARAMETER_DEFINITIONS.get(parameter_key)
    if not meta:
        return "normal"

    if parameter_key == "safety_equipment_status":
        if value == "faulty":
            return "critical"
        if value == "needs_calibration":
            return "warning"
        return "normal"

    if parameter_key == "last_inspection_date":
        try:
            inspection_date = datetime.fromisoformat(str(last_inspection_date or value)[:10])
            return "warning" if (datetime.now() - inspection_date).days > 30 else "normal"
        except ValueError:
            return "warning"

    if parameter_key == "daily_production" and target_value:
        deviation = abs(float(value) - float(target_value)) / max(float(target_value), 1)
        return "warning" if deviation > 0.25 else "normal"

    warning = meta.get("warning_threshold")
    danger = meta.get("danger_threshold")
    if warning is None or danger is None:
        return "normal"

    reading = float(value)
    if meta.get("lower_is_worse"):
        if reading <= danger:
            return "critical"
        if reading <= warning:
            return "warning"
    else:
        if reading >= danger:
            return "critical"
        if reading >= warning:
            return "warning"
    return "normal"
