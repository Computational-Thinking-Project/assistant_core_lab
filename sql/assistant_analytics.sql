-- Lab 05 Part F and H2.
-- Move these queries to sql/my_queries.sql once PR #41 supplies that file.

-- F1. How many requests does each intent receive?
SELECT intent, COUNT(*) AS requests
FROM interaction
GROUP BY intent
ORDER BY requests DESC, intent;

-- F2. What is the average response time in milliseconds for each intent?
SELECT intent, ROUND(AVG(latency_ms), 1) AS avg_ms
FROM interaction
GROUP BY intent
ORDER BY intent;

-- F3. Which known topics receive the most thumbs-down ratings?
SELECT i.topic, COUNT(*) AS thumbs_down
FROM feedback AS f
JOIN interaction AS i ON i.request_id = f.request_id
WHERE f.rating = -1 AND i.topic IS NOT NULL
GROUP BY i.topic
ORDER BY thumbs_down DESC, i.topic;

-- H2. What percentage of requests used a fallback answer for each intent?
-- The denominator includes every request recorded for the intent.
SELECT
    intent,
    COUNT(*) AS requests,
    SUM(CASE WHEN degraded = 1 THEN 1 ELSE 0 END) AS fallback_requests,
    ROUND(100.0 * AVG(CASE WHEN degraded = 1 THEN 1 ELSE 0 END), 1) AS fallback_pct
FROM interaction
GROUP BY intent
ORDER BY fallback_pct DESC, intent;

-- Results from a fresh database migrated and seeded with 300 synthetic
-- interactions using the PR #41 scaffold at b70c385 (96 feedback rows).
-- F1 (requests): rule 140, fee 61, office 47, greeting 26, unknown 26.
-- F2 (avg_ms): fee 5.1, greeting 2.4, office 3.4, rule 76.2, unknown 8.1.
-- F3 (thumbs_down): H26-4.2 8, H26-5.3 8, H26-7.2 2.
-- H2:
-- intent   | requests | fallback_requests | fallback_pct
-- rule     |      140 |                34 |         24.3
-- greeting |       26 |                 2 |          7.7
-- office   |       47 |                 1 |          2.1
-- fee      |       61 |                 1 |          1.6
-- unknown  |       26 |                 0 |          0.0
