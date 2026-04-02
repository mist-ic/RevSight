-- Deal aging: how long deals have been in their current stage
SELECT
    o.stage_name,
    o.forecast_category,
    COUNT(*)                                                                        AS deal_count,
    AVG(
        EXTRACT(EPOCH FROM (NOW() - o.updated_at)) / 86400
    )                                                                               AS avg_days_in_stage,
    COUNT(*) FILTER (
        WHERE EXTRACT(EPOCH FROM (NOW() - o.updated_at)) / 86400 > 45
    )                                                                               AS stale_count,
    SUM(o.arr) FILTER (
        WHERE EXTRACT(EPOCH FROM (NOW() - o.updated_at)) / 86400 > 45
    )                                                                               AS stale_arr
FROM opportunities o
WHERE
    o.scenario_id = $1
    AND o.quarter = $2
    AND o.region  = $3
    AND o.segment = $4
    AND o.stage_name NOT IN ('Closed Won', 'Closed Lost')
GROUP BY o.stage_name, o.forecast_category;
