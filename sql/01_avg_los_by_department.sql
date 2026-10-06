-- Q1: How long do patients stay, by department?
-- LOS = length of stay in days (discharge - admission).
SELECT
    d.name AS department,
    COUNT(*) AS admissions,
    ROUND(AVG(julianday(a.discharge_ts) - julianday(a.admit_ts)), 2) AS avg_los_days
FROM admissions a
JOIN departments d ON d.dept_id = a.dept_id
WHERE a.admit_ts >= '2025-01-01' AND a.admit_ts < '2026-01-01'
GROUP BY d.name
ORDER BY avg_los_days DESC;
