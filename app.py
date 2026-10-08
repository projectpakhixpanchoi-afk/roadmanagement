import os
from pathlib import Path
from datetime import datetime, date

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from utils.database import init_db, connect
from utils.logic import (
    maintenance_priority,
    road_condition_index,
    condition_label,
    estimate_repair_cost,
    ward_road_risk
)
from utils.services import ask_ai, get_weather

load_dotenv()
init_db()

APP_NAME = os.getenv("APP_NAME", "RoadSense AI")
REGION_NAME = os.getenv("REGION_NAME", "Demo District")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
ROAD_MAINTENANCE_BUDGET = float(os.getenv("ROAD_MAINTENANCE_BUDGET", "5000000"))
CRITICAL_PRIORITY_THRESHOLD = float(os.getenv("CRITICAL_PRIORITY_THRESHOLD", "80"))
ROAD_RISK_THRESHOLD = float(os.getenv("ROAD_RISK_THRESHOLD", "70"))
OFFICE_LAT = float(os.getenv("OFFICE_LAT", "26.1445"))
OFFICE_LON = float(os.getenv("OFFICE_LON", "91.7362"))

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title=APP_NAME, page_icon="🛣️", layout="wide")


def df_query(sql, params=()):
    conn = connect()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def execute(sql, params=()):
    conn = connect()
    conn.execute(sql, params)
    conn.commit()
    conn.close()


def money(value):
    return f"₹{float(value):,.0f}"


def refresh_priorities():
    issues = df_query("SELECT * FROM issues WHERE status!='Resolved'")
    for _, row in issues.iterrows():
        score = maintenance_priority(
            row["issue_type"],
            int(row["severity"]),
            int(row["pothole_count"]),
            float(row["affected_length_m"]),
            int(row["traffic_impact"]),
            int(row["accident_risk"]),
            row["created_at"]
        )
        execute(
            "UPDATE issues SET priority_score=?, updated_at=? WHERE id=?",
            (score, datetime.now().isoformat(timespec="seconds"), int(row["id"]))
        )


refresh_priorities()

with st.sidebar:
    st.title(APP_NAME)
    st.caption(f"Smart road maintenance for {REGION_NAME}")

    role = st.selectbox("Use as", ["Citizen", "Road Worker / Contractor", "Road Authority"])

    if role == "Citizen":
        page = st.radio(
            "Navigation",
            [
                "Citizen Home",
                "Report Road Issue",
                "Road Status",
                "Blocked Roads",
                "Road Safety Assistant"
            ]
        )
    elif role == "Road Worker / Contractor":
        page = st.radio(
            "Navigation",
            [
                "Worker Dashboard",
                "Priority Repairs",
                "Work Orders",
                "Road Inspection"
            ]
        )
    else:
        page = st.radio(
            "Navigation",
            [
                "Authority Dashboard",
                "Road Risk Hotspots",
                "Road Inventory",
                "Maintenance Planning",
                "Budget Analytics",
                "Weather Risk",
                "AI Road Advisor"
            ]
        )

    st.divider()
    st.caption("SQLite • optional AI • optional weather data")


if page == "Citizen Home":
    st.title(f"🛣️ {APP_NAME}")
    st.subheader("Report problems. Prioritize repairs. Build safer roads.")

    open_issues = int(df_query("SELECT COUNT(*) c FROM issues WHERE status!='Resolved'").iloc[0]["c"])
    critical = int(df_query(
        "SELECT COUNT(*) c FROM issues WHERE status!='Resolved' AND priority_score>=?",
        (CRITICAL_PRIORITY_THRESHOLD,)
    ).iloc[0]["c"])
    blocked = int(df_query("SELECT COUNT(*) c FROM blockages WHERE status='Active'").iloc[0]["c"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Open Road Issues", open_issues)
    c2.metric("Critical Repairs", critical)
    c3.metric("Active Blockages", blocked)

    st.info(
        "Citizens can report potholes, cracks, waterlogging, shoulder damage, drainage failure, "
        "missing signage, streetlight failures, bridge damage, and other road problems."
    )


elif page == "Report Road Issue":
    st.title("Report a Road Issue")

    roads = df_query("SELECT road_name, ward FROM roads ORDER BY road_name")
    road_names = roads["road_name"].tolist() + ["Other / Unregistered Road"]

    with st.form("road_issue_form", clear_on_submit=True):
        c1, c2 = st.columns(2)

        with c1:
            reporter = st.text_input("Reporter Name")
            phone = st.text_input("Phone")
            road_name = st.selectbox("Road Name", road_names)
            ward = st.selectbox("Ward / Zone", ["Ward 1","Ward 2","Ward 3","Ward 4","Ward 5"])
            issue_type = st.selectbox(
                "Issue Type",
                [
                    "Pothole","Surface Cracking","Waterlogging","Drainage Failure",
                    "Shoulder Damage","Missing Signage","Streetlight Failure",
                    "Bridge Damage","Road Collapse","Other"
                ]
            )
            lat = st.number_input("Latitude", value=OFFICE_LAT, format="%.6f")
            lon = st.number_input("Longitude", value=OFFICE_LON, format="%.6f")

        with c2:
            severity = st.slider("Severity", 1, 5, 3)
            pothole_count = st.number_input("Number of Potholes", 0, 100, 0)
            affected_length = st.number_input("Affected Road Length (m)", 0.0, 10000.0, 20.0, step=5.0)
            traffic_impact = st.slider("Traffic Impact", 1, 5, 3)
            accident_risk = st.slider("Accident Risk", 1, 5, 3)
            description = st.text_area("Description")
            photo = st.file_uploader("Optional Photo", type=["jpg","jpeg","png"])

        if st.form_submit_button("Submit Road Report", use_container_width=True):
            if not reporter.strip():
                st.error("Reporter name is required.")
            else:
                image_path = None
                if photo:
                    name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo.name.replace(' ','_')}"
                    p = UPLOAD_DIR / name
                    p.write_bytes(photo.getbuffer())
                    image_path = str(p)

                now = datetime.now().isoformat(timespec="seconds")
                score = maintenance_priority(
                    issue_type, severity, pothole_count, affected_length,
                    traffic_impact, accident_risk, now
                )

                execute("""INSERT INTO issues
                    (reporter_name,phone,road_name,ward,issue_type,severity,pothole_count,
                     affected_length_m,traffic_impact,accident_risk,description,lat,lon,
                     image_path,status,priority_score,created_at,updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,'Open',?,?,?)""",
                    (
                        reporter,phone,road_name,ward,issue_type,severity,pothole_count,
                        affected_length,traffic_impact,accident_risk,description,lat,lon,
                        image_path,score,now,now
                    )
                )
                st.success(f"Issue reported successfully. Maintenance priority: {score}/100")


elif page == "Road Status":
    st.title("Road Status")

    roads = df_query("SELECT * FROM roads ORDER BY condition_score ASC")
    if roads.empty:
        st.info("No road records available.")
    else:
        for _, row in roads.iterrows():
            with st.container(border=True):
                st.markdown(f"### {row['road_name']} — {row['ward']}")
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Condition Score", int(row["condition_score"]))
                c2.metric("Condition", condition_label(float(row["condition_score"])))
                c3.metric("Surface", row["surface_type"])
                c4.metric("Traffic / day", int(row["avg_daily_traffic"]))
                st.caption(
                    f"Length: {row['length_km']} km | Width: {row['width_m']} m | "
                    f"Last maintenance: {row['last_maintenance'] or 'Not recorded'}"
                )


elif page == "Blocked Roads":
    st.title("Blocked / Restricted Roads")

    blocked = df_query("SELECT * FROM blockages WHERE status='Active' ORDER BY created_at DESC")
    if blocked.empty:
        st.success("No active road blockages.")
    else:
        st.dataframe(
            blocked[
                ["road_name","ward","blockage_type","location_text",
                 "expected_clearance","created_at"]
            ],
            use_container_width=True
        )

        geo = blocked[["lat","lon"]].dropna()
        if not geo.empty:
            st.map(geo)


elif page == "Road Safety Assistant":
    st.title("Road Safety & Maintenance Assistant")
    st.caption("Works without an API key; Groq is used when configured in .env.")

    question = st.text_area(
        "Ask a road-management question",
        placeholder="How should a heavily used road with repeated potholes be repaired?"
    )

    if st.button("Get Advice", use_container_width=True):
        answer, mode = ask_ai(question, f"Region: {REGION_NAME}")
        st.info(answer)
        st.caption(mode)


elif page == "Worker Dashboard":
    st.title("Road Worker / Contractor Dashboard")

    issues = df_query("SELECT * FROM issues WHERE status!='Resolved'")
    orders = df_query("SELECT * FROM work_orders WHERE status!='Completed'")

    critical = int((issues["priority_score"] >= CRITICAL_PRIORITY_THRESHOLD).sum()) if not issues.empty else 0

    c1,c2,c3 = st.columns(3)
    c1.metric("Open Issues", len(issues))
    c2.metric("Critical Repairs", critical)
    c3.metric("Open Work Orders", len(orders))

    st.subheader("Top Priority Repairs")
    if not issues.empty:
        st.dataframe(
            issues[
                ["id","road_name","ward","issue_type","severity","traffic_impact",
                 "accident_risk","priority_score","status"]
            ].sort_values("priority_score", ascending=False).head(10),
            use_container_width=True
        )


elif page == "Priority Repairs":
    st.title("Priority Repair Queue")

    issues = df_query(
        "SELECT * FROM issues WHERE status!='Resolved' ORDER BY priority_score DESC"
    )

    if issues.empty:
        st.success("No pending repairs.")
    else:
        for _, row in issues.iterrows():
            with st.container(border=True):
                st.markdown(f"### #{int(row['id'])} — {row['road_name']} — {row['issue_type']}")

                cost = estimate_repair_cost(
                    row["issue_type"],
                    int(row["severity"]),
                    int(row["pothole_count"]),
                    float(row["affected_length_m"])
                )

                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Priority", f"{float(row['priority_score']):.1f}")
                c2.metric("Severity", f"{int(row['severity'])}/5")
                c3.metric("Affected", f"{float(row['affected_length_m']):.0f} m")
                c4.metric("Est. Cost", money(cost))

                st.write(row["description"] or "No description")

                contractor = st.text_input(
                    "Contractor / Team",
                    key=f"contractor_{int(row['id'])}"
                )

                x,y = st.columns(2)
                with x:
                    if st.button("Create Work Order", key=f"order_{int(row['id'])}", use_container_width=True):
                        if not contractor.strip():
                            st.error("Enter contractor/team name.")
                        else:
                            existing = df_query(
                                "SELECT COUNT(*) c FROM work_orders WHERE issue_id=? AND status!='Completed'",
                                (int(row["id"]),)
                            ).iloc[0]["c"]

                            if existing:
                                st.warning("An active work order already exists.")
                            else:
                                execute("""INSERT INTO work_orders
                                    (issue_id,road_name,work_type,contractor,estimated_cost,status,planned_date,notes)
                                    VALUES (?,?,?,?,?,'Planned',?,?)""",
                                    (
                                        int(row["id"]),row["road_name"],row["issue_type"],
                                        contractor,cost,str(date.today()),
                                        f"Generated from road issue #{int(row['id'])}"
                                    )
                                )
                                execute(
                                    "UPDATE issues SET status='Assigned', updated_at=? WHERE id=?",
                                    (datetime.now().isoformat(timespec="seconds"), int(row["id"]))
                                )
                                st.rerun()

                with y:
                    if st.button("Mark Directly Resolved", key=f"resolved_{int(row['id'])}", use_container_width=True):
                        execute(
                            "UPDATE issues SET status='Resolved', updated_at=? WHERE id=?",
                            (datetime.now().isoformat(timespec="seconds"), int(row["id"]))
                        )
                        st.rerun()


elif page == "Work Orders":
    st.title("Maintenance Work Orders")

    orders = df_query("SELECT * FROM work_orders ORDER BY id DESC")

    if orders.empty:
        st.info("No work orders created yet.")
    else:
        st.dataframe(orders, use_container_width=True)

        active = orders[orders["status"] != "Completed"]

        if not active.empty:
            order_id = st.selectbox("Select Work Order", active["id"].astype(int).tolist())
            selected = active[active["id"] == order_id].iloc[0]

            new_status = st.selectbox(
                "Update Status",
                ["Planned","In Progress","Completed"],
                index=["Planned","In Progress","Completed"].index(selected["status"])
                if selected["status"] in ["Planned","In Progress","Completed"] else 0
            )

            approved = st.number_input(
                "Approved / Actual Cost (₹)",
                min_value=0.0,
                value=float(selected["approved_cost"] or selected["estimated_cost"]),
                step=1000.0
            )

            if st.button("Update Work Order", use_container_width=True):
                started = selected["started_at"]
                completed = selected["completed_at"]

                if new_status == "In Progress" and not started:
                    started = datetime.now().isoformat(timespec="seconds")
                if new_status == "Completed":
                    completed = datetime.now().isoformat(timespec="seconds")

                execute(
                    """UPDATE work_orders
                       SET status=?, approved_cost=?, started_at=?, completed_at=?
                       WHERE id=?""",
                    (new_status, approved, started, completed, int(order_id))
                )

                if new_status == "Completed" and pd.notna(selected["issue_id"]):
                    execute(
                        "UPDATE issues SET status='Resolved', updated_at=? WHERE id=?",
                        (datetime.now().isoformat(timespec="seconds"), int(selected["issue_id"]))
                    )

                st.rerun()


elif page == "Road Inspection":
    st.title("Road Inspection & Condition Index")

    roads = df_query("SELECT * FROM roads ORDER BY road_name")
    selected_name = st.selectbox("Road", roads["road_name"].tolist())
    road = roads[roads["road_name"] == selected_name].iloc[0]

    with st.form("inspection_form"):
        inspector = st.text_input("Inspector Name")
        st.caption("Score each component from 0 (worst) to 100 (best).")

        surface = st.slider("Surface Condition", 0, 100, int(road["condition_score"]))
        drainage = st.slider("Drainage Condition", 0, 100, 70)
        marking = st.slider("Road Markings", 0, 100, 70)
        shoulder = st.slider("Shoulder / Edge Condition", 0, 100, 65)
        safety = st.slider("Overall Safety", 0, 100, 70)
        notes = st.text_area("Inspection Notes")

        if st.form_submit_button("Save Inspection", use_container_width=True):
            if not inspector.strip():
                st.error("Inspector name is required.")
            else:
                overall = road_condition_index(surface, drainage, marking, shoulder, safety)

                execute("""INSERT INTO inspections
                    (road_id,road_name,inspector,surface_score,drainage_score,marking_score,
                     shoulder_score,safety_score,overall_score,notes,inspected_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        int(road["id"]),road["road_name"],inspector,surface,drainage,marking,
                        shoulder,safety,overall,notes,datetime.now().isoformat(timespec="seconds")
                    )
                )

                execute(
                    "UPDATE roads SET condition_score=? WHERE id=?",
                    (int(round(overall)), int(road["id"]))
                )

                st.success(f"Inspection saved. New Road Condition Index: {overall}/100 ({condition_label(overall)})")


elif page == "Authority Dashboard":
    st.title("Road Authority Dashboard")

    password = st.text_input("Admin Password", type="password")
    if password != ADMIN_PASSWORD:
        st.warning("Enter the admin password configured in .env.")
        st.stop()

    roads = df_query("SELECT * FROM roads")
    issues = df_query("SELECT * FROM issues")
    open_issues = issues[issues["status"] != "Resolved"].copy() if not issues.empty else issues
    orders = df_query("SELECT * FROM work_orders")

    avg_condition = roads["condition_score"].mean() if not roads.empty else 0
    critical = int((open_issues["priority_score"] >= CRITICAL_PRIORITY_THRESHOLD).sum()) if not open_issues.empty else 0
    committed = float(orders["approved_cost"].fillna(0).sum()) if not orders.empty else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Roads Tracked", len(roads))
    c2.metric("Avg. Condition", f"{avg_condition:.1f}/100")
    c3.metric("Critical Issues", critical)
    c4.metric("Committed Cost", money(committed))

    if not roads.empty:
        st.subheader("Road Condition")
        fig = px.bar(
            roads.sort_values("condition_score"),
            x="road_name",
            y="condition_score",
            color="ward",
            text_auto=True
        )
        fig.update_layout(yaxis_range=[0,100], xaxis_title="", yaxis_title="Condition Score")
        st.plotly_chart(fig, use_container_width=True)

    if not open_issues.empty:
        st.subheader("Issue Map")
        geo = open_issues[["lat","lon"]].dropna()
        if not geo.empty:
            st.map(geo)

        st.subheader("Issue Type Distribution")
        summary = open_issues.groupby("issue_type", as_index=False).size()
        st.plotly_chart(
            px.pie(summary, names="issue_type", values="size", hole=0.4),
            use_container_width=True
        )


elif page == "Road Risk Hotspots":
    st.title("Road Risk Hotspots")

    password = st.text_input("Admin Password", type="password", key="riskpass")
    if password != ADMIN_PASSWORD:
        st.warning("Enter admin password.")
        st.stop()

    roads = df_query("SELECT * FROM roads")
    issues = df_query("SELECT * FROM issues WHERE status!='Resolved'")
    blockages = df_query("SELECT * FROM blockages WHERE status='Active'")

    wards = sorted(set(roads["ward"].tolist()) | set(issues["ward"].tolist()) | set(blockages["ward"].tolist()))
    rows = []

    for ward in wards:
        ward_issues = issues[issues["ward"] == ward]
        ward_roads = roads[roads["ward"] == ward]
        ward_blocks = blockages[blockages["ward"] == ward]

        open_count = len(ward_issues)
        severe = int((ward_issues["severity"] >= 4).sum()) if not ward_issues.empty else 0
        avg_priority = float(ward_issues["priority_score"].mean()) if not ward_issues.empty else 0
        low_condition = int((ward_roads["condition_score"] < 55).sum()) if not ward_roads.empty else 0

        score = ward_road_risk(open_count, severe, avg_priority, low_condition, len(ward_blocks))

        rows.append({
            "ward": ward,
            "open_issues": open_count,
            "severe_issues": severe,
            "avg_priority": round(avg_priority,1),
            "poor_or_critical_roads": low_condition,
            "active_blockages": len(ward_blocks),
            "risk_score": score,
            "risk_level": "HIGH" if score >= ROAD_RISK_THRESHOLD else "WATCH"
        })

    risk = pd.DataFrame(rows).sort_values("risk_score", ascending=False)
    st.dataframe(risk, use_container_width=True)
    st.plotly_chart(
        px.bar(risk, x="ward", y="risk_score", color="risk_level", text_auto=True),
        use_container_width=True
    )


elif page == "Road Inventory":
    st.title("Road Inventory")

    password = st.text_input("Admin Password", type="password", key="inventorypass")
    if password != ADMIN_PASSWORD:
        st.warning("Enter admin password.")
        st.stop()

    roads = df_query("SELECT * FROM roads ORDER BY ward, road_name")
    st.dataframe(roads, use_container_width=True)

    with st.form("add_road", clear_on_submit=True):
        st.subheader("Add Road")
        c1,c2 = st.columns(2)

        with c1:
            name = st.text_input("Road Name")
            ward = st.selectbox("Ward", ["Ward 1","Ward 2","Ward 3","Ward 4","Ward 5"])
            road_type = st.selectbox("Road Type", ["Urban Main Road","Local Road","Rural Connector","Rural Road","Other"])
            surface = st.selectbox("Surface", ["Bituminous","Concrete","Gravel","Earthen","Other"])
            length = st.number_input("Length (km)", 0.1, 100.0, 1.0, step=0.1)

        with c2:
            width = st.number_input("Width (m)", 1.0, 30.0, 5.0, step=0.5)
            traffic = st.number_input("Average Daily Traffic", 0, 100000, 1000)
            condition = st.slider("Initial Condition Score", 0, 100, 70)
            lat = st.number_input("Latitude", value=OFFICE_LAT, format="%.6f")
            lon = st.number_input("Longitude", value=OFFICE_LON, format="%.6f")

        if st.form_submit_button("Add Road", use_container_width=True):
            if not name.strip():
                st.error("Road name is required.")
            else:
                execute("""INSERT INTO roads
                    (road_name,ward,road_type,length_km,width_m,surface_type,avg_daily_traffic,
                     condition_score,last_maintenance,lat,lon,status)
                    VALUES (?,?,?,?,?,?,?,?,NULL,?,?,'Open')""",
                    (name,ward,road_type,length,width,surface,traffic,condition,lat,lon)
                )
                st.rerun()


elif page == "Maintenance Planning":
    st.title("Maintenance Planning")

    password = st.text_input("Admin Password", type="password", key="planpass")
    if password != ADMIN_PASSWORD:
        st.warning("Enter admin password.")
        st.stop()

    issues = df_query("SELECT * FROM issues WHERE status!='Resolved' ORDER BY priority_score DESC")

    if issues.empty:
        st.success("No pending maintenance issues.")
    else:
        plan = issues.copy()
        plan["estimated_cost"] = plan.apply(
            lambda r: estimate_repair_cost(
                r["issue_type"], int(r["severity"]), int(r["pothole_count"]), float(r["affected_length_m"])
            ),
            axis=1
        )

        plan["recommended_action"] = plan["priority_score"].apply(
            lambda x: "Immediate" if x >= 80 else "Within 7 days" if x >= 60 else "Schedule"
        )

        st.dataframe(
            plan[
                ["id","road_name","issue_type","priority_score","estimated_cost",
                 "recommended_action","status"]
            ],
            use_container_width=True
        )

        total_est = float(plan["estimated_cost"].sum())
        st.metric("Estimated Cost to Clear Current Backlog", money(total_est))

        if total_est > ROAD_MAINTENANCE_BUDGET:
            st.error(
                f"Estimated backlog exceeds the configured maintenance budget by "
                f"{money(total_est - ROAD_MAINTENANCE_BUDGET)}."
            )
        else:
            st.success(
                f"Current estimated backlog is within budget. Remaining theoretical allocation: "
                f"{money(ROAD_MAINTENANCE_BUDGET - total_est)}."
            )


elif page == "Budget Analytics":
    st.title("Road Maintenance Budget Analytics")

    password = st.text_input("Admin Password", type="password", key="budgetpass")
    if password != ADMIN_PASSWORD:
        st.warning("Enter admin password.")
        st.stop()

    orders = df_query("SELECT * FROM work_orders")
    spent = float(
        orders.loc[orders["status"]=="Completed","approved_cost"].fillna(0).sum()
    ) if not orders.empty else 0
    committed = float(
        orders.loc[orders["status"]!="Completed","approved_cost"].fillna(0).sum()
    ) if not orders.empty else 0

    c1,c2,c3 = st.columns(3)
    c1.metric("Configured Budget", money(ROAD_MAINTENANCE_BUDGET))
    c2.metric("Completed Work Cost", money(spent))
    c3.metric("Active Commitment", money(committed))

    used = spent + committed
    ratio = used / ROAD_MAINTENANCE_BUDGET if ROAD_MAINTENANCE_BUDGET else 0
    st.progress(min(ratio,1.0))
    st.caption(f"{ratio*100:.1f}% of configured maintenance budget committed/used")

    if not orders.empty:
        summary = orders.groupby("road_name", as_index=False)["estimated_cost"].sum()
        st.plotly_chart(
            px.bar(summary, x="road_name", y="estimated_cost", text_auto=".2s"),
            use_container_width=True
        )


elif page == "Weather Risk":
    st.title("Weather Risk Monitor")

    password = st.text_input("Admin Password", type="password", key="weatherpass")
    if password != ADMIN_PASSWORD:
        st.warning("Enter admin password.")
        st.stop()

    weather = get_weather()

    if not weather.get("available"):
        st.info(weather["message"])
        st.caption("Set OPENWEATHER_API_KEY and WEATHER_CITY in .env to enable live data.")
    else:
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("City", weather["city"])
        c2.metric("Temperature", f"{weather['temperature']:.1f} °C")
        c3.metric("Humidity", f"{weather['humidity']}%")
        c4.metric("Wind", f"{weather['wind_speed']} m/s")

        st.success(f"Condition: {weather['condition']}")

        if float(weather.get("rain_1h",0)) > 0:
            st.warning(
                "Rain detected. Inspect known waterlogging locations, drainage failures, "
                "road shoulders, and recently patched potholes."
            )


elif page == "AI Road Advisor":
    st.title("AI Road Management Advisor")

    password = st.text_input("Admin Password", type="password", key="aipass")
    if password != ADMIN_PASSWORD:
        st.warning("Enter admin password.")
        st.stop()

    roads = df_query("SELECT * FROM roads")
    issues = df_query("SELECT * FROM issues WHERE status!='Resolved'")

    context = (
        f"Region: {REGION_NAME}. Roads tracked: {len(roads)}. "
        f"Average road condition: {float(roads['condition_score'].mean()) if not roads.empty else 0:.1f}. "
        f"Open issues: {len(issues)}. "
        f"Critical issues: {int((issues['priority_score']>=CRITICAL_PRIORITY_THRESHOLD).sum()) if not issues.empty else 0}."
    )

    st.caption("Uses Groq when configured in .env; otherwise uses built-in road-maintenance logic.")

    question = st.text_area(
        "Ask the advisor",
        placeholder="Which roads should be prioritized for preventive maintenance this month?"
    )

    if st.button("Generate Recommendation", use_container_width=True):
        answer, mode = ask_ai(question, context)
        st.info(answer)
        st.caption(mode)
