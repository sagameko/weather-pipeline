-- Q5: Most common weather category in each state
WITH counts AS (
    SELECT l.state, w.category, COUNT(*) AS days
    FROM fct_daily_weather f
    JOIN dim_location l     ON f.location_key = l.location_key
    JOIN dim_weather_code w ON f.weather_code = w.weather_code
    GROUP BY l.state, w.category
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY state ORDER BY days DESC) AS rn
    FROM counts
)
SELECT state, category AS most_common_weather, days
FROM ranked
WHERE rn = 1
ORDER BY state;