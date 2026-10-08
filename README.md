# RoadSense AI — Smart Road Management & Maintenance Platform

RoadSense AI is a complete hackathon-ready road-management system built with Python, Streamlit, SQLite, Plotly, and optional AI/weather integrations.

## Main Features

### Citizen Module
- Report potholes and road damage
- GPS coordinates and photo upload
- Road issue severity
- Traffic-impact scoring
- Accident-risk scoring
- Public road-condition view
- Blocked-road information
- Road safety assistant

### Road Worker / Contractor Module
- Worker dashboard
- Priority repair queue
- Automatic repair-cost estimation
- Work-order creation
- Work-order status updates
- Road inspections
- Road Condition Index calculation

### Road Authority Module
- Road inventory
- Authority dashboard
- Road-condition analytics
- Road issue map
- Road risk hotspots
- Maintenance planning
- Budget analytics
- Optional live weather risk
- Optional AI road-management advisor

## Smart Maintenance Priority

The system assigns a 0–100 priority score using:

- Issue type
- Severity
- Number of potholes
- Affected road length
- Traffic impact
- Accident risk
- Time since the issue was reported

High-risk issue types such as bridge damage and road collapse receive additional priority.

## Road Condition Index

Road inspection considers:

- Surface condition
- Drainage condition
- Road markings
- Shoulder / edge condition
- Safety condition

The system calculates a weighted Road Condition Index and labels each road as:

- Excellent
- Good
- Fair
- Poor
- Critical

## Repair Cost Estimation

RoadSense AI generates approximate repair estimates using:

- Issue type
- Severity
- Number of potholes
- Affected length

These estimates are intended for project/demo planning and must not replace engineering estimates or tenders.

## Road Risk Hotspots

Ward-level road risk uses:

- Open road issues
- Severe issues
- Average repair priority
- Number of poor/critical roads
- Active road blockages

## Optional AI

Add a Groq API key to `.env`:

```env
GROQ_API_KEY=your_key
```

When no key is configured, the built-in rule-based road advisor continues to work.

## Optional Weather

Add an OpenWeather key:

```env
OPENWEATHER_API_KEY=your_key
WEATHER_CITY=Guwahati
```

The Weather Risk module can display:

- Temperature
- Humidity
- Wind speed
- Rain
- Current condition

Rain detection also triggers maintenance guidance for waterlogging, drainage, shoulder erosion, and recent repairs.

## Technology Stack

- Python
- Streamlit
- SQLite
- Pandas
- Plotly
- Requests
- python-dotenv
- Local image uploads

## Project Structure

```text
roadsense_ai_road_management/
├── app.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── README.md
├── HOW_IBM_BOB_WAS_USED.md
├── run_app.bat
├── .streamlit/
│   └── config.toml
├── data/
│   └── roadsense.db
├── uploads/
└── utils/
    ├── database.py
    ├── logic.py
    └── services.py
```

## Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

Windows users can also run:

```text
run_app.bat
```

## Default Admin Password

```text
admin123
```

Change it inside `.env`.

## Problem Statement

Poor road conditions directly affect public safety, travel time, vehicle maintenance costs, emergency access, local businesses, and daily mobility. Potholes, surface cracking, waterlogging, damaged shoulders, failed drainage, missing road signs, broken streetlights, bridge damage, and road blockages are often reported through phone calls, informal messages, or manual registers. These reports may not contain accurate location data and may not be prioritized according to severity, traffic volume, accident risk, or the number of people affected.

Road authorities also face difficulty maintaining a complete road inventory, tracking inspections, identifying recurring high-risk locations, estimating maintenance costs, managing contractors, monitoring road conditions after repairs, and planning work within limited budgets. In many areas, preventive maintenance is delayed until damage becomes severe and more expensive to repair.

There is therefore a need for a centralized and intelligent road-management platform that connects citizens, field workers, contractors, inspectors, and road authorities.

## Solution Statement

RoadSense AI is a smart road-management and maintenance platform built using Python, Streamlit, and SQLite.

Citizens can report potholes and other road defects using issue type, severity, GPS coordinates, affected road length, traffic impact, accident risk, description, and optional photo evidence. Every report receives an automated maintenance-priority score so road authorities can identify urgent repairs first.

Road workers and contractors receive a priority-ranked repair queue. The application calculates an approximate repair cost and allows teams to convert issues into work orders, track work as planned, in progress, or completed, and automatically close related complaints.

Inspectors can assess road surface, drainage, markings, shoulders, and safety. The application calculates a Road Condition Index and updates the condition of the road inventory.

Authorities receive dashboards showing road condition, issue distribution, issue maps, ward-level road-risk hotspots, maintenance backlog, estimated costs, work-order budgets, and active blockages. Optional weather integration helps identify rain-related road risks, while the optional AI Road Advisor provides context-aware maintenance recommendations.

The core project works without paid APIs.

## Hackathon Pitch

"RoadSense AI transforms road maintenance from complaint-driven repair into data-driven preventive management. It combines citizen reporting, smart repair prioritization, road-condition inspections, cost estimation, contractor work orders, risk hotspots, budget tracking, and weather-aware planning in one low-cost platform."

## Suggested Demo Flow

1. Citizen reports a deep pothole on a busy road.
2. The platform calculates a high maintenance-priority score.
3. Worker dashboard places it near the top of the queue.
4. The system estimates repair cost.
5. Contractor creates a work order.
6. Work progresses from Planned to In Progress to Completed.
7. The original issue is automatically marked resolved.
8. Inspector performs a road-condition inspection.
9. The Road Condition Index updates.
10. Authority dashboard shows changed road condition and maintenance budget.
11. Weather monitor can warn about rain-related road risks.
12. AI Road Advisor recommends preventive-maintenance priorities.

## Future Improvements

- AI pothole detection from road images
- Mobile app for citizens and field engineers
- GPS vehicle tracking
- OpenStreetMap routing
- Automatic road-surface classification
- Drone inspection
- Computer-vision crack detection
- IoT vibration sensors
- Traffic-volume API integration
- GIS road layers
- Tender and contractor modules
- Public SLA tracking
- Before/after repair photos
- Road-quality scorecards
- Predictive maintenance using machine learning
