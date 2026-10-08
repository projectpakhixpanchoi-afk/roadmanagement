import os
import requests
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are RoadSense AI, a road-maintenance and road-safety planning assistant.
Give short, practical recommendations about road defects, inspection,
maintenance planning, traffic safety, drainage, potholes, prioritization,
repair scheduling and preventive maintenance.

Do not claim that your advice replaces a licensed civil engineer or official
road-safety inspection. Recommend professional inspection for major structural
damage, bridge damage, collapse, or immediate public danger.
"""

def rule_based_answer(question):
    q = question.lower()

    if "pothole" in q:
        return (
            "Prioritize potholes by depth, size, traffic volume and accident risk. "
            "Use temporary barricading for dangerous locations, then perform proper patch repair "
            "with edge cutting, cleaning, tack coat, compacted patch material and final level checking."
        )
    if "waterlog" in q or "drain" in q:
        return (
            "Inspect side drains, culverts, road camber and blocked outlets. Remove obstructions first, "
            "then repair drainage defects before resurfacing so the road does not fail again."
        )
    if "crack" in q:
        return (
            "Classify cracks before repair. Small isolated cracks may be sealed, while widespread cracking "
            "can indicate base or drainage failure and may require deeper rehabilitation."
        )
    if "bridge" in q or "collapse" in q:
        return (
            "Treat structural or bridge damage as high priority. Restrict traffic immediately if safety is uncertain "
            "and request inspection by qualified civil/structural engineers before reopening."
        )
    if "maintenance" in q:
        return (
            "Use preventive maintenance: routine inspection, drain cleaning, crack sealing, shoulder repair, "
            "road-marking renewal, and early pothole patching. Preventive work is usually cheaper than full reconstruction."
        )
    return (
        "Record the exact defect, GPS location, severity, affected length, traffic impact and accident risk. "
        "Use these factors to rank repairs, inspect high-risk sites first and track every work order to completion."
    )

def ask_ai(question, context=""):
    key = os.getenv("GROQ_API_KEY","").strip()
    model = os.getenv("GROQ_MODEL","llama-3.1-8b-instant").strip()

    if not key:
        return rule_based_answer(question), "Rule-based road advisor"

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role":"system","content":SYSTEM_PROMPT},
                    {"role":"user","content":f"Road network context:\n{context}\n\nQuestion:\n{question}"}
                ],
                "temperature":0.2,
                "max_tokens":500
            },
            timeout=25
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"], f"AI mode: {model}"
    except Exception:
        return rule_based_answer(question), "Fallback rule-based advisor"

def get_weather():
    key = os.getenv("OPENWEATHER_API_KEY","").strip()
    city = os.getenv("WEATHER_CITY","Guwahati").strip()

    if not key:
        return {"available":False,"message":"Add OPENWEATHER_API_KEY to .env to enable live weather.","city":city}

    try:
        r=requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q":city,"appid":key,"units":"metric"},
            timeout=20
        )
        r.raise_for_status()
        d=r.json()
        return {
            "available":True,
            "city":city,
            "temperature":d["main"]["temp"],
            "humidity":d["main"]["humidity"],
            "wind_speed":d["wind"]["speed"],
            "rain_1h":d.get("rain",{}).get("1h",0),
            "condition":d["weather"][0]["description"].title()
        }
    except Exception:
        return {"available":False,"message":"Weather service is currently unavailable.","city":city}
