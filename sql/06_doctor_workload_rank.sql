-- Q6: Doctor workload, ranked within each department (window function).
WITH per_doctor AS (
    SELECT
        d.name AS department,
        doc.name AS doctor,
        COUNT(*) AS admissions
    FROM admissions a
    JOIN doctors doc ON doc.doctor_id = a.doctor_id
    JOIN departments d ON d.dept_id = a.dept_id
    WHERE a.admit_ts >= '2025-01-01' AND a.admit_ts < '2026-01-01'
    GROUP BY d.name, doc.name
)
SELECT
    department,
    doctor,
    admissions,
    RANK() OVER (PARTITION BY department ORDER BY admissions DESC) AS rank_in_department
FROM per_doctor
ORDER BY department, rank_in_department;
