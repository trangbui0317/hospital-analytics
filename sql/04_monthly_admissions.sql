-- Q4: Is there a seasonal pattern in admissions?
SELECT
    strftime('%Y-%m', admit_ts) AS month,
    COUNT(*) AS admissions
FROM admissions
WHERE admit_ts >= '2025-01-01' AND admit_ts < '2026-01-01'
GROUP BY month
ORDER BY month;
