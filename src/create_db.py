"""Create a synthetic hospital database (SQLite).

All data is randomly generated with a fixed seed, so results are reproducible.
No real patient data is used.

Run:  python src/create_db.py
"""
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "hospital.db"
SEED = 42

# Data is generated from mid-Nov 2024 so that beds are already "warm" on
# 1 Jan 2025 (otherwise occupancy would look artificially low in January).
START = datetime(2024, 11, 15)
END = datetime(2025, 12, 31)

# name: (bed_capacity, admissions_per_year, mean_los_days, readmit_probability)
DEPARTMENTS = {
    "Emergency":        (30, 4000, 1.5, 0.03),
    "ICU":              (12,  900, 4.5, 0.04),
    "Cardiology":       (25, 1300, 4.0, 0.12),
    "Orthopaedics":     (25,  900, 5.0, 0.04),
    "Paediatrics":      (20, 1100, 3.0, 0.05),
    "General Medicine": (40, 2400, 5.5, 0.10),
}
DOCTORS_PER_DEPT = 4
N_PATIENTS = 12000
DIAGNOSIS_GROUPS = ["Cardiac", "Respiratory", "Orthopaedic", "Infectious",
                    "Neurological", "Digestive", "Other"]

SCHEMA = """
DROP TABLE IF EXISTS admissions;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    dept_id      INTEGER PRIMARY KEY,
    name         TEXT NOT NULL UNIQUE,
    bed_capacity INTEGER NOT NULL
);
CREATE TABLE doctors (
    doctor_id INTEGER PRIMARY KEY,
    name      TEXT NOT NULL,
    dept_id   INTEGER NOT NULL REFERENCES departments(dept_id)
);
CREATE TABLE patients (
    patient_id INTEGER PRIMARY KEY,
    age        INTEGER NOT NULL,
    gender     TEXT NOT NULL
);
CREATE TABLE admissions (
    admission_id    INTEGER PRIMARY KEY,
    patient_id      INTEGER NOT NULL REFERENCES patients(patient_id),
    dept_id         INTEGER NOT NULL REFERENCES departments(dept_id),
    doctor_id       INTEGER NOT NULL REFERENCES doctors(doctor_id),
    admit_ts        TEXT NOT NULL,      -- 'YYYY-MM-DD HH:MM:SS'
    discharge_ts    TEXT NOT NULL,
    diagnosis_group TEXT NOT NULL
);
CREATE INDEX idx_adm_dept    ON admissions(dept_id);
CREATE INDEX idx_adm_patient ON admissions(patient_id);
CREATE INDEX idx_adm_admit   ON admissions(admit_ts);
"""


def hour_weights(dept):
    """Relative chance of an admission at each hour (0-23)."""
    if dept == "Emergency":      # busy late morning to night
        return [2, 1, 1, 1, 1, 2, 3, 5, 7, 8, 9, 9, 9, 8, 8, 8, 8, 9, 9, 8, 7, 5, 4, 3]
    # planned admissions: mostly office hours
    return [1, 1, 1, 1, 1, 1, 2, 5, 9, 10, 9, 8, 6, 6, 5, 4, 3, 3, 2, 2, 1, 1, 1, 1]


def month_weight(day, dept):
    """Winter (Jun-Aug in Australia) is busier for respiratory-heavy departments."""
    winter = day.month in (6, 7, 8)
    if dept in ("Emergency", "General Medicine", "Paediatrics", "ICU"):
        return 1.35 if winter else 1.0
    return 1.0


def main():
    random.seed(SEED)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    # --- departments and doctors
    dept_ids, doctor_ids = {}, {}
    doc_counter = 1
    for i, (name, (beds, *_)) in enumerate(DEPARTMENTS.items(), start=1):
        conn.execute("INSERT INTO departments VALUES (?,?,?)", (i, name, beds))
        dept_ids[name] = i
        doctor_ids[name] = []
        for _ in range(DOCTORS_PER_DEPT):
            conn.execute("INSERT INTO doctors VALUES (?,?,?)",
                         (doc_counter, f"Dr. {name.split()[0]}-{doc_counter:02d}", i))
            doctor_ids[name].append(doc_counter)
            doc_counter += 1

    # --- patients
    for pid in range(1, N_PATIENTS + 1):
        age = min(95, max(0, int(random.gauss(48, 24))))
        conn.execute("INSERT INTO patients VALUES (?,?,?)",
                     (pid, age, random.choice(["F", "M"])))

    # --- admissions
    all_days = [START + timedelta(days=i) for i in range((END - START).days + 1)]
    rows = []
    n_years = (END - START).days / 365.0
    for name, (_, per_year, mean_los, p_readmit) in DEPARTMENTS.items():
        weights = [month_weight(d, name) for d in all_days]
        n = int(per_year * n_years)
        days = random.choices(all_days, weights=weights, k=n)
        hours = random.choices(range(24), weights=hour_weights(name), k=n)
        for day, hour in zip(days, hours):
            admit = day.replace(hour=hour, minute=random.randint(0, 59))
            # gamma distribution = right-skewed stay length, like real LOS data
            los = max(0.1, random.gammavariate(2, mean_los / 2))
            discharge = admit + timedelta(days=los)
            patient = random.randint(1, N_PATIENTS)
            doctor = random.choice(doctor_ids[name])
            diag = random.choice(DIAGNOSIS_GROUPS)
            rows.append((patient, dept_ids[name], doctor, admit, discharge, diag))

            # some patients come back within 30 days (a "readmission")
            if random.random() < p_readmit:
                back = discharge + timedelta(days=random.uniform(3, 28))
                if back <= END:
                    los2 = max(0.1, random.gammavariate(2, mean_los / 2))
                    rows.append((patient, dept_ids[name], doctor, back,
                                 back + timedelta(days=los2), diag))

    rows.sort(key=lambda r: r[3])
    fmt = "%Y-%m-%d %H:%M:%S"
    conn.executemany(
        "INSERT INTO admissions (patient_id, dept_id, doctor_id, admit_ts, discharge_ts, diagnosis_group) "
        "VALUES (?,?,?,?,?,?)",
        [(p, d, doc, a.strftime(fmt), dc.strftime(fmt), dg) for p, d, doc, a, dc, dg in rows],
    )
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM admissions").fetchone()[0]
    conn.close()
    print(f"Created {DB_PATH} with {total} admissions.")


if __name__ == "__main__":
    main()
