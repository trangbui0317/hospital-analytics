-- Q2: Which departments are close to or over bed capacity?
-- A recursive CTE builds one row per calendar day of 2025, then each day is
-- joined to the admissions that were "in bed" on that day.
WITH RECURSIVE days(d) AS (
    SELECT date('2025-01-01')
    UNION ALL
    SELECT date(d, '+1 day') FROM days WHERE d < '2025-12-31'
),
daily AS (
    SELECT
        dep.dept_id,
        dep.name,
        dep.bed_capacity,
        days.d,
        COUNT(a.admission_id) AS occupied
    FROM days
    CROSS JOIN departments dep
    LEFT JOIN admissions a
           ON a.dept_id = dep.dept_id
          AND date(a.admit_ts) <= days.d
          AND date(a.discharge_ts) > days.d
    GROUP BY dep.dept_id, days.d
)
SELECT
    name AS department,
    bed_capacity,
    ROUND(AVG(occupied), 1) AS avg_occupied_beds,
    ROUND(100.0 * AVG(occupied) / bed_capacity, 1) AS avg_occupancy_pct,
    ROUND(100.0 * SUM(CASE WHEN occupied >= 0.9 * bed_capacity THEN 1 ELSE 0 END)
          / COUNT(*), 1) AS pct_days_at_90pct_or_more
FROM daily
GROUP BY dept_id
ORDER BY avg_occupancy_pct DESC;
