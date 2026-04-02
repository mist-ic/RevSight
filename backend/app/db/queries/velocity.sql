-- Average deal velocity (days from created to closed/current)
SELECT
    o.stage_name,
    COUNT(*)                                                                    AS deal_count,
    AVG(EXTRACT(EPOCH FROM (COALESCE(o.close_date::timestamp, NOW()) - o.created_at)) / 86400)
                                                                                AS avg_days_in_flight,
    PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY EXTRACT(EPOCH FROM (COALESCE(o.close_date::timestamp, NOW()) - o.created_at)) / 86400
    )                                                                           AS median_days_in_flight
FROM opportunities o
WHERE
    o.scenario_id = $1
    AND o.quarter = $2
    AND o.region  = $3
    AND o.segment = $4
    AND o.stage_name NOT IN ('Closed Lost')
GROUP BY o.stage_name;
