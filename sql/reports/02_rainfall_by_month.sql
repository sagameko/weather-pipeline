-- Q2: Total rainfall per city per month
SELECT d.year, d.month_name, l.city,
       ROUND(SUM(f.precipitation_mm), 1) AS total_rain_mm,
       SUM(f.is_rain_day)                AS rain_days
FROM fct_daily_weather f
JOIN dim_date d     ON f.date_key = d.date_key
JOIN dim_location l ON f.location_key = l.location_key
GROUP BY d.year, d.month, d.month_name, l.city
ORDER BY d.year, d.month, total_rain_mm DESC;