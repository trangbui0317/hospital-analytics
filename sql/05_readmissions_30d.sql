-- Q5: What share of discharged patients return within 30 days (same department)?
-- A correlated subquery (EXISTS) checks for a later admission of the same patient.
WITH flagged AS (
    SELECT
        a.dept_id,
        EXISTS (
            SELECT 1
            FROM admissions r
            WHERE r.patient_id = a.patient_id
              AND r.dept_id = a.dept_id
              AND r.admit_ts > a.discharge_ts
              AND julianday(r.admit_ts) - julianday(a.discharge_ts) <= 30
        ) AS readmitted
    FROM admissions a
    WHERE a.admit_ts >= '2025-01-01'
      AND a.discharge_ts < '2025-12-01'   -- leave a 30-day follow-up window
)
SELECT
    d.name AS department,
    COUNT(*) AS discharges,
    SUM(f.readmitted) AS readmitted_within_30d,
    ROUND(100.0 * SUM(f.readmitted) / COUNT(*), 1) AS readmission_rate_pct
FROM flagged f
JOIN departments d ON d.dept_id = f.dept_id
GROUP BY d.name
ORDER BY readmission_rate_pct DESC;
