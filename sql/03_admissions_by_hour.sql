-- Q3: At what hour of the day do admissions arrive? (staffing question)
SELECT
    CAST(strftime('%H', admit_ts) AS INTEGER) AS hour_of_day,
    COUNT(*) AS admissions
FROM admissions
WHERE admit_ts >= '2025-01-01' AND admit_ts < '2026-01-01'
GROUP BY hour_of_day
ORDER BY hour_of_day;
