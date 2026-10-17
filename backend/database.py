import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent / "data" / "stepwise.db"
JSON_PATH = Path(__file__).resolve().parent / "data" / "patients.json"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id TEXT PRIMARY KEY,
        mrn TEXT UNIQUE,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        dob TEXT,
        education_years INTEGER,
        apoe TEXT,
        referral TEXT,
        complaint TEXT,
        patient_notes TEXT DEFAULT '',
        primary_doctor TEXT DEFAULT 'Dr. Kenneth Adams, MD',
        clinic_location TEXT DEFAULT 'GE Healthcare Precision Neuro Center, Bay 3',
        current_stage INTEGER DEFAULT 0,
        risk_score REAL DEFAULT 0.35,
        velocity TEXT DEFAULT 'Moderate',
        vitals_json TEXT,
        medical_history_json TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Migrate existing patients table to add new columns if missing
    try:
        cursor.execute("ALTER TABLE patients ADD COLUMN patient_notes TEXT DEFAULT ''")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE patients ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP")
    except:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        visit_code TEXT NOT NULL,
        visit_date TEXT,
        stage_number INTEGER DEFAULT 1,
        mmse REAL,
        moca REAL,
        cdrsb REAL,
        faq REAL,
        adas13 REAL,
        gds REAL,
        ptau217 REAL,
        ab42_40 REAL,
        nfl REAL,
        gfap REAL,
        hippocampus_cm3 REAL,
        ventricles_cm3 REAL,
        mta_grade TEXT,
        centiloids REAL,
        tau_suvr REAL,
        microbleeds INTEGER DEFAULT 0,
        risk_score REAL,
        stage_dx TEXT,
        stage_assessment_json TEXT,
        doctor_notes TEXT DEFAULT '',
        escalation_decision TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    );
    """)

    # Migrate visits table
    for col in [
        "stage_number INTEGER DEFAULT 1",
        "adas13 REAL",
        "gds REAL",
        "stage_assessment_json TEXT",
        "doctor_notes TEXT DEFAULT ''",
        "escalation_decision TEXT DEFAULT ''",
        "created_at TEXT DEFAULT CURRENT_TIMESTAMP",
    ]:
        try:
            cursor.execute(f"ALTER TABLE visits ADD COLUMN {col}")
        except:
            pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stage_escalations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        from_stage INTEGER NOT NULL,
        to_stage INTEGER NOT NULL,
        escalation_decision TEXT DEFAULT 'escalate',
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        doctor_name TEXT,
        clinical_rationale TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    );
    """)

    try:
        cursor.execute("ALTER TABLE stage_escalations ADD COLUMN escalation_decision TEXT DEFAULT 'escalate'")
    except:
        pass

    conn.commit()

    # Seed from patients.json if table is empty
    cursor.execute("SELECT COUNT(*) as count FROM patients")
    if cursor.fetchone()["count"] == 0 and JSON_PATH.exists():
        print(f"Seeding SQLite database from {JSON_PATH}...")
        with open(JSON_PATH, "r") as f:
            patients_data = json.load(f)

        for p in patients_data:
            p_id = p["id"]
            med_hist = p.get("medical_history", {
                "hypertension": True, "diabetes": False, "hyperlipidemia": True,
                "cad": False, "stroke": False, "sleep_apnea": False,
                "smoking": False, "family_history": True, "anticoagulant": False
            })

            cursor.execute("""
            INSERT OR REPLACE INTO patients (
                id, mrn, name, age, gender, dob, education_years, apoe, referral, complaint,
                patient_notes, primary_doctor, clinic_location, current_stage, risk_score,
                velocity, vitals_json, medical_history_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p_id,
                p.get("mrn", f"GE-HC-{p_id}"),
                p["name"],
                p["age"],
                p["gender"],
                p.get("dob", "1954-06-12"),
                p.get("education_years", 16),
                p.get("apoe", "ε3/ε3"),
                p.get("referral", "Memory Clinic"),
                p.get("complaint", "Progressive memory decline"),
                p.get("patient_notes", ""),
                p.get("primary_doctor", "Dr. Kenneth Adams, MD"),
                p.get("clinic_location", "GE Healthcare Precision Neuro Center, Bay 3"),
                p.get("currentStage", 1),
                p.get("riskScore", 0.5),
                p.get("velocity", "Moderate"),
                json.dumps(p.get("vitals", {"bp": "128/82 mmHg", "pulse": 72, "bmi": 24.5})),
                json.dumps(med_hist),
                p.get("created_at", "2024-09-12 09:00:00")
            ))

            s1 = p.get("stage1", {})
            s2 = p.get("stage2", {})
            s3 = p.get("stage3", {})
            s4 = p.get("stage4", {})

            cursor.execute("""
            INSERT INTO visits (
                patient_id, visit_code, visit_date, stage_number, mmse, moca, cdrsb, faq,
                ptau217, ab42_40, nfl, gfap,
                hippocampus_cm3, ventricles_cm3, mta_grade,
                centiloids, tau_suvr, microbleeds, risk_score, stage_dx, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p_id, "M00", "2024-09-12", 1,
                s1.get("mmse", 24), s1.get("moca", 22), s1.get("cdrsb", 1.5), s1.get("faq", 4.0),
                s2.get("ptau217", 0.24), s2.get("ab42_40", 0.088), s2.get("nfl", 14.2), s2.get("gfap", 187.0),
                s3.get("hippoVol", 3.82), 42.1, s3.get("mtaGrade", "MTA Grade 2"),
                s4.get("centiloids", 78.4), 1.48, 0,
                p.get("riskScore", 0.5),
                f"Stage {p.get('currentStage', 1)} Active",
                "2024-09-12 09:00:00"
            ))

            if p.get("velocity") in ["High Velocity", "Rapid Converter", "Rapid Converter (ΔMMSE -3.5/yr)"]:
                cursor.execute("""
                INSERT INTO visits (
                    patient_id, visit_code, visit_date, stage_number, mmse, moca, cdrsb, faq,
                    ptau217, ab42_40, nfl, gfap,
                    hippocampus_cm3, ventricles_cm3, mta_grade,
                    centiloids, tau_suvr, microbleeds, risk_score, stage_dx, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p_id, "M12", "2025-09-15", p.get("currentStage", 1),
                    max(10, (s1.get("mmse") or 24) - 2), max(8, (s1.get("moca") or 22) - 2),
                    (s1.get("cdrsb") or 1.5) + 0.5, (s1.get("faq") or 4.0) + 2.0,
                    round((s2.get("ptau217") or 0.24) * 1.25, 2),
                    round((s2.get("ab42_40") or 0.088) * 0.90, 3),
                    round((s2.get("nfl") or 14.2) * 1.18, 1),
                    round((s2.get("gfap") or 187.0) * 1.10, 1),
                    round((s3.get("hippoVol") or 3.82) * 0.92, 2),
                    round(42.1 * 1.10, 1), s3.get("mtaGrade", "MTA Grade 2"),
                    round((s4.get("centiloids") or 78.4) * 1.10, 1), 1.55, 0,
                    min(0.98, (p.get("riskScore") or 0.5) + 0.12),
                    "M12 Revisit: Disease Progression",
                    "2025-09-15 09:00:00"
                ))

        conn.commit()
        print(f"Successfully seeded ADNI patients into stepwise.db!")

    # Ensure every patient has complete historical stage visits up to their current_stage
    reseed_all_patient_visits_db(conn)

    conn.close()


def reseed_all_patient_visits_db(conn=None):
    """Ensures that all patients in the database have complete chronological stage visits for every stage they have reached."""
    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True

    cursor = conn.cursor()
    cursor.execute("SELECT id, mrn, name, current_stage, risk_score, velocity FROM patients")
    patients = cursor.fetchall()

    for p in patients:
        pid = p["id"]
        cs = max(1, p["current_stage"] or 1)
        base_risk = p["risk_score"] or 0.5
        is_fast = p["velocity"] in ["High Velocity", "Rapid Converter", "Rapid Converter (ΔMMSE -3.5/yr)"]

        # Check existing visits
        cursor.execute("SELECT stage_number, visit_code FROM visits WHERE patient_id IN (?, ?)", (pid, p["mrn"] or pid))
        existing = cursor.fetchall()
        existing_stages = {v["stage_number"] for v in existing}

        stage_dates = {1: "2024-09-12", 2: "2025-03-15", 3: "2025-09-15", 4: "2026-03-20"}
        stage_codes = {1: "M00", 2: "M06", 3: "M12", 4: "M24"}

        for s in range(1, cs + 1):
            if s not in existing_stages:
                # Stage-appropriate metrics
                s_date = stage_dates.get(s, "2025-01-01")
                s_code = stage_codes.get(s, f"M{(s-1)*6}")
                s_risk = min(0.98, max(0.15, base_risk - (cs - s) * 0.12))

                # Cognitive values
                mmse = max(12, 28 - (s - 1) * 3 if is_fast else 26 - (s - 1) * 1.5)
                moca = max(10, mmse - 2)
                cdrsb = min(12.0, 0.5 + (s - 1) * 1.2)
                faq = min(25.0, 1.0 + (s - 1) * 3.0)
                adas13 = min(60.0, 12.0 + (s - 1) * 8.0)
                gds = min(10.0, 1.0 + (s - 1) * 1.0)

                # Blood
                ptau = round(0.12 + (s - 1) * 0.08, 2) if s >= 2 else None
                ab42_40 = round(0.110 - (s - 1) * 0.012, 3) if s >= 2 else None
                nfl = round(10.5 + (s - 1) * 4.2, 1) if s >= 2 else None
                gfap = round(110.0 + (s - 1) * 35.0, 1) if s >= 2 else None

                # MRI
                hippo = round(4.10 - (s - 1) * 0.32, 2) if s >= 3 else None
                vent = round(32.0 + (s - 1) * 5.5, 1) if s >= 3 else None
                mta = f"MTA Grade {min(4, s - 1)}" if s >= 3 else None

                # PET
                cent = round(15.0 + (s - 1) * 22.0, 1) if s >= 4 else None
                tau = round(1.08 + (s - 1) * 0.15, 2) if s >= 4 else None
                bleeds = 0 if s >= 4 else None

                notes_map = {
                    1: "Baseline cognitive screening battery completed. Short-term memory complaints recorded.",
                    2: "Plasma proteomics panel completed. Confirms elevated p-tau217 (>0.20 pg/mL). Authorized MRI referral.",
                    3: "GE 3.0T High-Resolution MRI completed. Bilateral hippocampal atrophy noted. Authorized molecular PET.",
                    4: "Molecular 18F-Florbetapir Amyloid PET completed. Amyloid positivity (78.4 CL) confirmed. DMT eligible."
                }
                notes = notes_map.get(s, f"Stage {s} assessment completed.")

                cursor.execute("""
                INSERT INTO visits (
                    patient_id, visit_code, visit_date, stage_number,
                    mmse, moca, cdrsb, faq, adas13, gds,
                    ptau217, ab42_40, nfl, gfap,
                    hippocampus_cm3, ventricles_cm3, mta_grade,
                    centiloids, tau_suvr, microbleeds, risk_score, stage_dx,
                    doctor_notes, escalation_decision, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pid, s_code, s_date, s,
                    mmse, moca, cdrsb, faq, adas13, gds,
                    ptau, ab42_40, nfl, gfap,
                    hippo, vent, mta,
                    cent, tau, bleeds, s_risk, f"Stage {s} Assessment",
                    notes, "escalate" if s < cs else "routine",
                    f"{s_date} 09:00:00"
                ))

                if s < cs:
                    cursor.execute("""
                    INSERT INTO stage_escalations (
                        patient_id, from_stage, to_stage, escalation_decision, timestamp,
                        doctor_name, clinical_rationale
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        pid, s, s + 1, "escalate", f"{s_date} 10:00:00",
                        "Dr. Kenneth Adams, MD", f"Stage {s} gating threshold verified. Authorized Stage {s+1} referral."
                    ))

    conn.commit()
    if should_close:
        conn.close()


def _build_patient_dict(r, cursor):
    """Internal helper: build a full patient dict from a DB row (handles both old and new schema)."""
    p_dict = dict(r)

    # Handle both old schema (med_history_json, vitals_json) and new schema (medical_history_json)
    med_hist_json = p_dict.get("medical_history_json") or p_dict.get("med_history_json") or "{}"
    p_dict["vitals"] = json.loads(p_dict.get("vitals_json") or "{}")
    p_dict["medical_history"] = json.loads(med_hist_json)
    p_dict["currentStage"] = p_dict["current_stage"]
    p_dict["riskScore"] = p_dict["risk_score"]
    p_dict["patient_notes"] = p_dict.get("patient_notes") or ""

    # Get all visits ordered by date
    pid = p_dict["id"]
    mrn = p_dict.get("mrn") or pid
    cursor.execute("SELECT * FROM visits WHERE patient_id IN (?, ?) ORDER BY id ASC", (pid, mrn))
    v_rows = cursor.fetchall()
    all_visits = [dict(v) for v in v_rows]
    p_dict["visits"] = all_visits

    cs = p_dict["current_stage"] or 0

    # --- Stage data: prefer rich stageN_json columns if they exist ---
    def get_stage_json(n):
        key = f"stage{n}_json"
        raw = p_dict.get(key)
        if raw:
            try: return json.loads(raw)
            except: pass
        return None

    # Stage 1: try rich JSON first, then latest stage 1 visit
    s1_json = get_stage_json(1)
    s1v = next((x for x in reversed(all_visits) if x.get("stage_number") == 1), None)
    if s1_json:
        p_dict["stage1"] = {
            "mmse": s1_json.get("mmse"),
            "moca": s1_json.get("moca"),
            "cdrsb": s1_json.get("cdrsb"),
            "faq": s1_json.get("faq"),
            "adas13": s1_json.get("adas13"),
            "gds": s1_json.get("gds"),
            "logical_memory": s1_json.get("logical_memory"),
            "riskScorePct": s1_json.get("riskScorePct") or int(p_dict["risk_score"] * 100),
            "assessment": s1_json.get("assessment") or {}
        }
    elif s1v:
        p_dict["stage1"] = {
            "mmse": s1v.get("mmse"), "moca": s1v.get("moca"),
            "cdrsb": s1v.get("cdrsb"), "faq": s1v.get("faq"),
            "adas13": s1v.get("adas13"), "gds": s1v.get("gds"),
            "riskScorePct": int((s1v.get("risk_score") or p_dict["risk_score"]) * 100),
            "assessment": json.loads(s1v.get("stage_assessment_json") or "{}")
        }
    else:
        p_dict["stage1"] = None

    # Stage 2
    s2_json = get_stage_json(2)
    s2v = next((x for x in reversed(all_visits) if x.get("stage_number") == 2), None)
    if cs >= 2:
        if s2_json:
            p_dict["stage2"] = {
                "plasma_ptau217": s2_json.get("plasma_ptau217"),
                "plasma_ab42_40": s2_json.get("plasma_ab42_40"),
                "plasma_nfl": s2_json.get("plasma_nfl"),
                "plasma_gfap": s2_json.get("plasma_gfap"),
                "riskScorePct": s2_json.get("riskScorePct") or int(p_dict["risk_score"] * 100),
                "assessment": s2_json.get("assessment") or {}
            }
        elif s2v:
            p_dict["stage2"] = {
                "plasma_ptau217": s2v.get("ptau217"), "plasma_ab42_40": s2v.get("ab42_40"),
                "plasma_nfl": s2v.get("nfl"), "plasma_gfap": s2v.get("gfap"),
                "riskScorePct": int((s2v.get("risk_score") or p_dict["risk_score"]) * 100),
                "assessment": json.loads(s2v.get("stage_assessment_json") or "{}")
            }
        else:
            p_dict["stage2"] = None
    else:
        p_dict["stage2"] = None

    # Stage 3
    s3_json = get_stage_json(3)
    s3v = next((x for x in reversed(all_visits) if x.get("stage_number") == 3), None)
    if cs >= 3:
        if s3_json:
            p_dict["stage3"] = {
                "hippoVol": s3_json.get("hippoVol") or s3_json.get("hippocampus_cm3"),
                "ventriclesVol": s3_json.get("ventriclesVol") or s3_json.get("ventricles_cm3"),
                "mtaGrade": s3_json.get("mtaGrade") or s3_json.get("mta_grade"),
                "wmhVol": s3_json.get("wmhVol") or s3_json.get("wmh_volume_cm3"),
                "riskScorePct": s3_json.get("riskScorePct") or int(p_dict["risk_score"] * 100),
                "assessment": s3_json.get("assessment") or {}
            }
        elif s3v:
            p_dict["stage3"] = {
                "hippoVol": s3v.get("hippocampus_cm3"), "ventriclesVol": s3v.get("ventricles_cm3"),
                "mtaGrade": s3v.get("mta_grade"), "riskScorePct": int((s3v.get("risk_score") or p_dict["risk_score"]) * 100),
                "assessment": json.loads(s3v.get("stage_assessment_json") or "{}")
            }
        else:
            p_dict["stage3"] = None
    else:
        p_dict["stage3"] = None

    # Stage 4
    s4_json = get_stage_json(4)
    s4v = next((x for x in reversed(all_visits) if x.get("stage_number") == 4), None)
    if cs >= 4:
        if s4_json:
            p_dict["stage4"] = {
                "centiloids": s4_json.get("centiloids"),
                "suvr": s4_json.get("suvr") or s4_json.get("tau_suvr"),
                "tauSuvr": s4_json.get("tauSuvr") or s4_json.get("tau_suvr"),
                "microbleedsCount": s4_json.get("microbleedsCount") or s4_json.get("microbleeds", 0),
                "atnClassification": s4_json.get("atnClassification") or "A+ T+ N+",
                "dmtEligible": (s4_json.get("centiloids") or 0) >= 25.0,
                "riskScorePct": s4_json.get("riskScorePct") or int(p_dict["risk_score"] * 100),
                "assessment": s4_json.get("assessment") or {}
            }
        elif s4v:
            p_dict["stage4"] = {
                "centiloids": s4v.get("centiloids"), "suvr": s4v.get("tau_suvr"),
                "tauSuvr": s4v.get("tau_suvr"), "microbleedsCount": s4v.get("microbleeds", 0),
                "atnClassification": "A+ T+ N+",
                "dmtEligible": (s4v.get("centiloids") or 0) >= 25.0,
                "riskScorePct": int((s4v.get("risk_score") or p_dict["risk_score"]) * 100),
                "assessment": json.loads(s4v.get("stage_assessment_json") or "{}")
            }
        else:
            p_dict["stage4"] = None
    else:
        p_dict["stage4"] = None

    return p_dict


def fetch_all_patients_db(stage=None, velocity=None, search=None):
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM patients WHERE 1=1"
    params = []

    if stage is not None:
        query += " AND current_stage = ?"
        params.append(stage)
    if velocity:
        query += " AND LOWER(velocity) = ?"
        params.append(velocity.lower())
    if search:
        query += " AND (LOWER(name) LIKE ? OR LOWER(id) LIKE ? OR LOWER(mrn) LIKE ?)"
        s = f"%{search.lower()}%"
        params.extend([s, s, s])

    query += " ORDER BY risk_score DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    patients = []
    for r in rows:
        patients.append(_build_patient_dict(r, cursor))

    conn.close()
    return patients


def fetch_patient_by_id_db(patient_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE id = ? OR mrn = ?", (patient_id, patient_id))
    r = cursor.fetchone()
    if not r:
        conn.close()
        return None
    p_dict = _build_patient_dict(r, cursor)
    conn.close()
    return p_dict


def insert_new_patient_db(patient_data):
    """Registers a brand new patient with current_stage=0 (pre-screening). No visits yet."""
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now()
    p_id = patient_data.get("id") or f"P-{now.strftime('%m%d%H%M%S')}"
    mrn = patient_data.get("mrn") or f"GE-HC-{now.strftime('%H%M%S')}"

    med_hist = patient_data.get("medical_history", {
        "hypertension": patient_data.get("has_hypertension", False),
        "diabetes": patient_data.get("has_diabetes", False),
        "hyperlipidemia": patient_data.get("has_hyperlipidemia", False),
        "cad": patient_data.get("has_cad", False),
        "stroke": patient_data.get("has_stroke", False),
        "sleep_apnea": patient_data.get("has_sleep_apnea", False),
        "smoking": patient_data.get("has_smoking", False),
        "family_history": patient_data.get("has_family_history", False),
        "anticoagulant": patient_data.get("has_anticoagulant", False)
    })


    cursor.execute("""
    INSERT INTO patients (
        id, mrn, name, age, gender, dob, education_years, apoe, referral, complaint,
        patient_notes, primary_doctor, clinic_location, current_stage, risk_score,
        velocity, vitals_json, med_history_json, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        p_id, mrn,
        patient_data["name"],
        patient_data["age"],
        patient_data["gender"],
        patient_data.get("dob", "1960-01-01"),
        patient_data.get("education_years", 14),
        patient_data.get("apoe", "ε3/ε3"),
        patient_data.get("referral", "Memory Clinic Intake"),
        patient_data.get("complaint", "Cognitive evaluation"),
        patient_data.get("patient_notes", ""),
        patient_data.get("primary_doctor", "Dr. Kenneth Adams, MD"),
        patient_data.get("clinic_location", "GE Healthcare Precision Neuro Center, Bay 3"),
        0,  # Pre-screening (no stage started yet)
        0.35,
        "Moderate",
        json.dumps(patient_data.get("vitals", {"bp": "120/80 mmHg", "pulse": 72, "bmi": 24.0})),
        json.dumps(med_hist),
        now.strftime("%Y-%m-%d %H:%M:%S")
    ))


    conn.commit()
    conn.close()
    return fetch_patient_by_id_db(p_id)


def escalate_patient_stage_db(patient_id, to_stage, doctor_name="Dr. Kenneth Adams, MD",
                               rationale="Clinician verified risk escalation threshold",
                               decision="escalate"):
    """Doctor-in-the-Loop manual stage escalation gate."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT current_stage FROM patients WHERE id = ? OR mrn = ?", (patient_id, patient_id))
    r = cursor.fetchone()
    if not r:
        conn.close()
        return None
    from_stage = r["current_stage"]

    cursor.execute("UPDATE patients SET current_stage = ? WHERE id = ? OR mrn = ?",
                   (to_stage, patient_id, patient_id))

    cursor.execute("""
    INSERT INTO stage_escalations (patient_id, from_stage, to_stage, escalation_decision, doctor_name, clinical_rationale, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (patient_id, from_stage, to_stage, decision, doctor_name, rationale,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()
    return fetch_patient_by_id_db(patient_id)


def add_visit_db(patient_id, visit_data):
    """Add a new visit (stage assessment result) to the DB. Resilient to old schema."""
    conn = get_db()
    cursor = conn.cursor()

    # Check what columns exist in visits
    cursor.execute("PRAGMA table_info(visits)")
    visit_cols = {row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) as c FROM visits WHERE patient_id = ?", (patient_id,))
    cnt = cursor.fetchone()["c"]
    v_code = visit_data.get("visit_code") or f"M{cnt * 6}"
    now = datetime.now()

    # Core columns that always exist
    cols = ["patient_id", "visit_code", "visit_date", "stage_number", "mmse", "moca",
            "ptau217", "ab42_40", "hippocampus_cm3", "centiloids",
            "risk_score", "stage_dx", "adas13", "gds",
            "stage_assessment_json", "doctor_notes", "escalation_decision"]
    vals = [
        patient_id, v_code,
        visit_data.get("visit_date") or now.strftime("%Y-%m-%d"),
        visit_data.get("stage_number", 1),
        visit_data.get("mmse"), visit_data.get("moca"),
        visit_data.get("ptau217"), visit_data.get("ab42_40"),
        visit_data.get("hippocampus_cm3"), visit_data.get("centiloids"),
        visit_data.get("risk_score"),
        visit_data.get("stage_dx", "Stage Assessment"),
        visit_data.get("adas13"), visit_data.get("gds"),
        json.dumps(visit_data.get("stage_assessment_json") or {}),
        visit_data.get("doctor_notes", ""),
        visit_data.get("escalation_decision", ""),
    ]

    # Optional columns that may not exist in old schema
    optional = [
        ("cdrsb", visit_data.get("cdrsb")),
        ("faq", visit_data.get("faq")),
        ("nfl", visit_data.get("nfl")),
        ("gfap", visit_data.get("gfap")),
        ("ventricles_cm3", visit_data.get("ventricles_cm3")),
        ("mta_grade", visit_data.get("mta_grade")),
        ("tau_suvr", visit_data.get("tau_suvr")),
        ("microbleeds", visit_data.get("microbleeds", 0)),
        ("created_at", now.strftime("%Y-%m-%d %H:%M:%S")),
    ]
    for col, val in optional:
        if col in visit_cols:
            cols.append(col)
            vals.append(val)

    placeholders = ", ".join(["?"] * len(cols))
    col_names = ", ".join(cols)
    cursor.execute(f"INSERT INTO visits ({col_names}) VALUES ({placeholders})", vals)

    if "risk_score" in visit_data and visit_data["risk_score"] is not None:
        cursor.execute("UPDATE patients SET risk_score = ? WHERE id = ?",
                       (visit_data["risk_score"], patient_id))
    if "current_stage" in visit_data and visit_data["current_stage"] is not None:
        cursor.execute("UPDATE patients SET current_stage = ? WHERE id = ?",
                       (visit_data["current_stage"], patient_id))

    conn.commit()
    conn.close()
    return fetch_patient_by_id_db(patient_id)


def get_patient_timeline_db(patient_id):
    """Returns chronological timeline of all events for a patient sorted newest to oldest."""
    conn = get_db()
    cursor = conn.cursor()

    # Get patient registration event by id or mrn
    cursor.execute("SELECT id, mrn, created_at, name FROM patients WHERE id = ? OR mrn = ?", (patient_id, patient_id))
    p = cursor.fetchone()
    if not p:
        conn.close()
        return []

    canonical_id = p["id"]
    canonical_mrn = p["mrn"] or canonical_id
    reg_time = p["created_at"] or "2024-09-12 09:00:00"

    events = []
    events.append({
        "id": "reg",
        "type": "registration",
        "timestamp": reg_time,
        "display_date": str(reg_time)[:10],
        "title": "Patient Registered",
        "detail": f"{p['name']} enrolled in StepWise PRO system",
        "icon": "user-plus",
        "color": "blue",
        "can_delete": False,
    })

    # Visits matching either canonical_id or canonical_mrn
    cursor.execute("SELECT * FROM visits WHERE patient_id IN (?, ?) ORDER BY id ASC", (canonical_id, canonical_mrn))
    visits = cursor.fetchall()
    stage_labels = {1: "Cognitive Screening", 2: "Blood Biomarker Panel", 3: "Volumetric MRI", 4: "Molecular PET"}
    stage_colors = {1: "blue", 2: "purple", 3: "teal", 4: "orange"}

    for v in visits:
        vd = dict(v)
        sn = vd.get("stage_number", 1)
        v_date = vd.get("visit_date") or vd.get("created_at") or reg_time
        v_ts = f"{v_date} 10:00:00" if len(str(v_date)) == 10 else str(v_date)

        ev_obj = {**vd}
        ev_obj.update({
            "id": vd.get("id"),
            "visit_id": vd.get("id"),
            "type": "visit",
            "timestamp": v_ts,
            "display_date": str(v_date)[:10],
            "title": f"Stage {sn}: {stage_labels.get(sn, 'Assessment')} — {vd.get('visit_code', 'M00')}",
            "detail": vd.get("stage_dx") or f"Risk Score: {round((vd.get('risk_score') or 0) * 100)}%",
            "icon": "clipboard-check",
            "color": stage_colors.get(sn, "gray"),
            "risk_score": vd.get("risk_score"),
            "visit_code": vd.get("visit_code"),
            "stage_number": sn,
            "doctor_notes": vd.get("doctor_notes", ""),
            "can_delete": True,
        })
        events.append(ev_obj)

    # Escalations matching either canonical_id or canonical_mrn
    cursor.execute("SELECT * FROM stage_escalations WHERE patient_id IN (?, ?) ORDER BY id ASC", (canonical_id, canonical_mrn))
    escalations = cursor.fetchall()
    for e in escalations:
        ed = dict(e)
        dec = ed.get("escalation_decision", "escalate")
        dec_labels = {
            "escalate": f"Escalated → Stage {ed['to_stage']}",
            "routine": "Returned to Routine Care",
            "more_data": "More Data Requested",
            "revisit": "Revisit Cycle Initiated"
        }
        e_ts = ed.get("timestamp") or reg_time
        e_ts_full = f"{e_ts} 14:00:00" if len(str(e_ts)) == 10 else str(e_ts)

        events.append({
            "id": ed.get("id"),
            "escalation_id": ed.get("id"),
            "type": "escalation",
            "timestamp": e_ts_full,
            "display_date": str(e_ts)[:10],
            "title": dec_labels.get(dec, f"Clinical Decision: Stage {ed['to_stage']}"),
            "detail": ed.get("clinical_rationale", ""),
            "icon": "shield-check",
            "color": "green" if dec == "escalate" else ("yellow" if dec == "more_data" else "gray"),
            "doctor": ed.get("doctor_name", ""),
            "can_delete": True,
        })

    # Sort all events strictly newest to oldest (DESCENDING)
    def event_sort_key(ev):
        date_str = str(ev.get("timestamp") or "")[:10]
        t_rank = 3 if ev.get("type") == "escalation" else (2 if ev.get("type") == "visit" else 1)
        ev_id = ev.get("id") if isinstance(ev.get("id"), int) else 0
        return (date_str, t_rank, ev_id)

    events.sort(key=event_sort_key, reverse=True)
    conn.close()
    return events


def delete_escalation_db(patient_id: str, escalation_id: int):
    """Deletes a stage escalation log and recalculates current stage."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, mrn FROM patients WHERE id = ? OR mrn = ?", (patient_id, patient_id))
    p = cursor.fetchone()
    if not p:
        conn.close()
        return None
    actual_pid = p["id"]
    actual_mrn = p["mrn"] or actual_pid

    cursor.execute("DELETE FROM stage_escalations WHERE id = ? AND patient_id IN (?, ?)", (escalation_id, actual_pid, actual_mrn))

    # Recalculate max stage from remaining visits and escalations
    cursor.execute("SELECT MAX(stage_number) as ms FROM visits WHERE patient_id IN (?, ?)", (actual_pid, actual_mrn))
    row_v = cursor.fetchone()
    cursor.execute("SELECT MAX(to_stage) as me FROM stage_escalations WHERE patient_id IN (?, ?)", (actual_pid, actual_mrn))
    row_e = cursor.fetchone()

    max_stage = max(row_v["ms"] if row_v and row_v["ms"] else 0, row_e["me"] if row_e and row_e["me"] else 0)
    max_stage = max(1, max_stage)
    cursor.execute("UPDATE patients SET current_stage = ? WHERE id IN (?, ?)", (max_stage, actual_pid, actual_mrn))

    conn.commit()
    conn.close()
    return fetch_patient_by_id_db(actual_pid)


def delete_visit_db(patient_id: str, visit_id: int):
    """Deletes a visit event and recalculates current stage/risk score."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, mrn FROM patients WHERE id = ? OR mrn = ?", (patient_id, patient_id))
    p = cursor.fetchone()
    if not p:
        conn.close()
        return None
    actual_pid = p["id"]
    actual_mrn = p["mrn"] or actual_pid

    cursor.execute("DELETE FROM visits WHERE id = ? AND patient_id IN (?, ?)", (visit_id, actual_pid, actual_mrn))

    cursor.execute("SELECT stage_number, risk_score FROM visits WHERE patient_id IN (?, ?) ORDER BY id DESC LIMIT 1", (actual_pid, actual_mrn))
    r = cursor.fetchone()
    max_stage = r["stage_number"] if (r and r["stage_number"]) else 1
    latest_risk = r["risk_score"] if (r and r["risk_score"] is not None) else 0.35
    cursor.execute("UPDATE patients SET current_stage = ?, risk_score = ? WHERE id IN (?, ?)", (max_stage, latest_risk, actual_pid, actual_mrn))
    conn.commit()
    conn.close()
    return fetch_patient_by_id_db(actual_pid)


def update_visit_db(patient_id: str, visit_id: int, updates: dict):
    """Updates visit fields such as notes, date, or clinical diagnosis."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, mrn FROM patients WHERE id = ? OR mrn = ?", (patient_id, patient_id))
    p = cursor.fetchone()
    if not p:
        conn.close()
        return None
    actual_pid = p["id"]
    actual_mrn = p["mrn"] or actual_pid

    fields = []
    vals = []
    for k, v in updates.items():
        if k in ["visit_date", "visit_code", "doctor_notes", "stage_dx", "escalation_decision", "risk_score"]:
            fields.append(f"{k} = ?")
            vals.append(v)
    if fields:
        vals.extend([visit_id, actual_pid])
        cursor.execute(f"UPDATE visits SET {', '.join(fields)} WHERE id = ? AND patient_id = ?", vals)
        conn.commit()
    conn.close()
    return fetch_patient_by_id_db(actual_pid)


def get_analytics_db():
    """Hospital-level aggregate analytics for dashboard & analytics view."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM patients")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT current_stage, COUNT(*) as cnt FROM patients GROUP BY current_stage")
    stage_dist = {str(r["current_stage"]): r["cnt"] for r in cursor.fetchall()}

    cursor.execute("SELECT gender, COUNT(*) as cnt FROM patients GROUP BY gender")
    gender_dist = {r["gender"]: r["cnt"] for r in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) as cnt FROM patients WHERE risk_score >= 0.70")
    high_risk = cursor.fetchone()["cnt"]
    cursor.execute("SELECT COUNT(*) as cnt FROM patients WHERE risk_score >= 0.30 AND risk_score < 0.70")
    moderate_risk = cursor.fetchone()["cnt"]
    cursor.execute("SELECT COUNT(*) as cnt FROM patients WHERE risk_score < 0.30")
    low_risk = cursor.fetchone()["cnt"]

    cursor.execute("SELECT AVG(risk_score) as avg_risk FROM patients")
    avg_risk = cursor.fetchone()["avg_risk"] or 0.5

    # Age distribution buckets
    age_buckets = {}
    for bucket, label in [("< 60", "age < 60"), ("60-65", "age >= 60 AND age < 65"),
                           ("65-70", "age >= 65 AND age < 70"), ("70-75", "age >= 70 AND age < 75"),
                           ("75-80", "age >= 75 AND age < 80"), ("80+", "age >= 80")]:
        cursor.execute(f"SELECT COUNT(*) as cnt FROM patients WHERE {label}")
        age_buckets[bucket] = cursor.fetchone()["cnt"]

    # Velocity distribution
    cursor.execute("SELECT velocity, COUNT(*) as cnt FROM patients GROUP BY velocity")
    velocity_dist = {r["velocity"]: r["cnt"] for r in cursor.fetchall()}

    # Escalation funnel: patients who reached each stage
    funnel = {}
    for s in [0, 1, 2, 3, 4]:
        cursor.execute("SELECT COUNT(*) as cnt FROM patients WHERE current_stage >= ?", (s,))
        funnel[f"stage_{s}_plus"] = cursor.fetchone()["cnt"]

    # Recent high-risk patients (top 5)
    cursor.execute("SELECT id, mrn, name, age, gender, risk_score, current_stage, velocity FROM patients ORDER BY risk_score DESC LIMIT 5")
    top_patients = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "total_patients": total,
        "stage_distribution": stage_dist,
        "gender_distribution": gender_dist,
        "risk_tiers": {
            "high": high_risk,
            "moderate": moderate_risk,
            "low": low_risk
        },
        "avg_risk_score": round(avg_risk, 3),
        "age_distribution": age_buckets,
        "velocity_distribution": velocity_dist,
        "escalation_funnel": funnel,
        "top_risk_patients": top_patients
    }


if __name__ == "__main__":
    init_db()
