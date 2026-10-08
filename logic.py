from datetime import datetime

ISSUE_BONUS = {
    "Bridge Damage": 25,
    "Road Collapse": 25,
    "Pothole": 14,
    "Waterlogging": 14,
    "Drainage Failure": 13,
    "Surface Cracking": 9,
    "Shoulder Damage": 8,
    "Missing Signage": 7,
    "Streetlight Failure": 5,
    "Other": 5
}

def maintenance_priority(issue_type, severity, pothole_count, affected_length_m,
                         traffic_impact, accident_risk, created_at):
    try:
        created = datetime.fromisoformat(created_at)
    except Exception:
        created = datetime.now()

    age_hours = max(0, (datetime.now()-created).total_seconds()/3600)

    score = (
        severity*10
        + min(pothole_count,50)*1.5
        + min(affected_length_m,1000)*0.035
        + traffic_impact*6
        + accident_risk*7
        + min(age_hours,96)*0.3
        + ISSUE_BONUS.get(issue_type,5)
    )
    return round(min(score,100),1)

def road_condition_index(surface, drainage, marking, shoulder, safety):
    score = (
        surface*0.35
        + drainage*0.20
        + marking*0.10
        + shoulder*0.15
        + safety*0.20
    )
    return round(score,1)

def condition_label(score):
    if score >= 85: return "Excellent"
    if score >= 70: return "Good"
    if score >= 55: return "Fair"
    if score >= 40: return "Poor"
    return "Critical"

def estimate_repair_cost(issue_type, severity, pothole_count, affected_length_m):
    base = {
        "Pothole": 2500,
        "Surface Cracking": 1800,
        "Waterlogging": 4500,
        "Drainage Failure": 6000,
        "Shoulder Damage": 2200,
        "Bridge Damage": 25000,
        "Road Collapse": 30000,
        "Missing Signage": 3500,
        "Streetlight Failure": 4000,
        "Other": 3000
    }.get(issue_type,3000)

    multiplier = 1 + (severity-1)*0.35
    pothole_component = pothole_count * 1200
    length_component = affected_length_m * {
        "Pothole": 90,
        "Surface Cracking": 140,
        "Waterlogging": 220,
        "Drainage Failure": 280,
        "Shoulder Damage": 160,
        "Bridge Damage": 900,
        "Road Collapse": 1100,
        "Missing Signage": 20,
        "Streetlight Failure": 25,
        "Other": 120
    }.get(issue_type,120)

    return round(base*multiplier + pothole_component + length_component, -2)

def ward_road_risk(open_issues, severe_issues, avg_priority, low_condition_roads, blockages):
    score = (
        open_issues*8
        + severe_issues*12
        + avg_priority*0.35
        + low_condition_roads*10
        + blockages*15
    )
    return round(min(score,100),1)
