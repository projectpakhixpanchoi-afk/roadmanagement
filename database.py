import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path("data/roadsense.db")

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS roads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        road_name TEXT NOT NULL,
        ward TEXT NOT NULL,
        road_type TEXT NOT NULL,
        length_km REAL NOT NULL,
        width_m REAL NOT NULL,
        surface_type TEXT NOT NULL,
        avg_daily_traffic INTEGER DEFAULT 0,
        condition_score INTEGER DEFAULT 70,
        last_maintenance TEXT,
        lat REAL,
        lon REAL,
        status TEXT DEFAULT 'Open'
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reporter_name TEXT NOT NULL,
        phone TEXT,
        road_name TEXT NOT NULL,
        ward TEXT NOT NULL,
        issue_type TEXT NOT NULL,
        severity INTEGER NOT NULL,
        pothole_count INTEGER DEFAULT 0,
        affected_length_m REAL DEFAULT 0,
        traffic_impact INTEGER DEFAULT 1,
        accident_risk INTEGER DEFAULT 1,
        description TEXT,
        lat REAL,
        lon REAL,
        image_path TEXT,
        status TEXT DEFAULT 'Open',
        priority_score REAL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS work_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id INTEGER,
        road_name TEXT NOT NULL,
        work_type TEXT NOT NULL,
        contractor TEXT,
        estimated_cost REAL DEFAULT 0,
        approved_cost REAL DEFAULT 0,
        status TEXT DEFAULT 'Planned',
        planned_date TEXT,
        started_at TEXT,
        completed_at TEXT,
        notes TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        road_id INTEGER,
        road_name TEXT NOT NULL,
        inspector TEXT NOT NULL,
        surface_score INTEGER NOT NULL,
        drainage_score INTEGER NOT NULL,
        marking_score INTEGER NOT NULL,
        shoulder_score INTEGER NOT NULL,
        safety_score INTEGER NOT NULL,
        overall_score REAL NOT NULL,
        notes TEXT,
        inspected_at TEXT NOT NULL
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS blockages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        road_name TEXT NOT NULL,
        ward TEXT NOT NULL,
        blockage_type TEXT NOT NULL,
        location_text TEXT NOT NULL,
        lat REAL,
        lon REAL,
        expected_clearance TEXT,
        status TEXT DEFAULT 'Active',
        created_at TEXT NOT NULL
    )""")

    conn.commit()

    if cur.execute("SELECT COUNT(*) FROM roads").fetchone()[0] == 0:
        seed_demo_data(conn)

    conn.close()

def seed_demo_data(conn):
    cur = conn.cursor()
    now = datetime.now()

    roads = [
        ("Station Road","Ward 1","Urban Main Road",2.8,7.0,"Bituminous",8200,62,"2026-04-12",26.1451,91.7352,"Open"),
        ("Market Link Road","Ward 2","Local Road",1.7,5.5,"Bituminous",4200,48,"2025-11-20",26.1438,91.7380,"Open"),
        ("School Road","Ward 3","Local Road",1.2,5.0,"Concrete",3100,76,"2026-02-10",26.1475,91.7390,"Open"),
        ("Village Connector","Ward 4","Rural Connector",4.5,4.5,"Bituminous",1800,55,"2025-08-15",26.1490,91.7338,"Open"),
        ("River Embankment Road","Ward 5","Rural Road",3.4,4.0,"Gravel",900,43,"2025-06-21",26.1425,91.7329,"Open")
    ]
    cur.executemany("""INSERT INTO roads
        (road_name,ward,road_type,length_km,width_m,surface_type,avg_daily_traffic,
         condition_score,last_maintenance,lat,lon,status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", roads)

    issues = [
        ("Rina","9000000011","Market Link Road","Ward 2","Pothole",5,7,35,5,5,"Multiple deep potholes near market entrance.",26.1439,91.7381),
        ("Amit","9000000012","Station Road","Ward 1","Surface Cracking",4,0,120,4,4,"Long cracks and broken edge near bus stand.",26.1453,91.7350),
        ("Puja","9000000013","Village Connector","Ward 4","Waterlogging",4,0,85,4,4,"Drainage overflow causes standing water.",26.1492,91.7336),
        ("Nayan","9000000014","River Embankment Road","Ward 5","Shoulder Damage",3,0,160,3,4,"Road shoulder eroded after rain.",26.1427,91.7328)
    ]
    for i,row in enumerate(issues):
        created = now - timedelta(hours=(i+1)*9)
        sev=row[5]; potholes=row[6]; affected=row[7]; traffic=row[8]; risk=row[9]
        age=(now-created).total_seconds()/3600
        priority=min(100, sev*11 + potholes*2 + min(affected,500)*0.05 + traffic*6 + risk*7 + min(age,72)*0.35)
        cur.execute("""INSERT INTO issues
            (reporter_name,phone,road_name,ward,issue_type,severity,pothole_count,
             affected_length_m,traffic_impact,accident_risk,description,lat,lon,image_path,
             status,priority_score,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,NULL,'Open',?,?,?)""",
            (*row, priority, created.isoformat(timespec="seconds"), created.isoformat(timespec="seconds")))

    cur.execute("""INSERT INTO blockages
        (road_name,ward,blockage_type,location_text,lat,lon,expected_clearance,status,created_at)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        ("Village Connector","Ward 4","Fallen Tree","Near km 2.1",26.1491,91.7337,
         (now+timedelta(hours=5)).isoformat(timespec="minutes"),"Active",now.isoformat(timespec="seconds")))

    conn.commit()
