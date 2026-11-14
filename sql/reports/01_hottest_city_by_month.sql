-- Q1: Which city is the hottest each month (by average daily max temperature)?
WITH monthly AS (
    SELECT d.year, d.month, d.month_name, l.city,
           ROUND(AVG(f.temp_max_c), 1) AS avg_max_temp_c
    FROM fct_daily_weather f
    JOIN dim_date d     ON f.date_key = d.date_key
    JOIN dim_location l ON f.location_key = l.location_key
    GROUP BY d.year, d.month, d.month_name, l.city
),
ranked AS (
    SELECT *, RANK() OVER (PARTITION BY year, month ORDER BY avg_max_temp_c DESC) AS rnk
    FROM monthly
)
SELECT year, month_name, city, avg_max_temp_c
FROM ranked
WHERE rnk = 1
ORDER BY year, month;