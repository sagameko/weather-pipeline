-- Q3: "Nice days" per city per month: no rain day and max temperature between 18 and 28 C
SELECT d.year, d.month_name, l.city,
       SUM(CASE WHEN f.is_rain_day = 0
                 AND f.temp_max_c BETWEEN 18 AND 28 THEN 1 ELSE 0 END) AS nice_days,
       COUNT(*)                                                       AS total_days
FROM fct_daily_weather f
JOIN dim_date d     ON f.date_key = d.date_key
JOIN dim_location l ON f.location_key = l.location_key
GROUP BY d.year, d.month, d.month_name, l.city
ORDER BY d.year, d.month, nice_days DESC;