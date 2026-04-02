-- Close date slippage: deals with past close dates still open
SELECT
    COUNT(*)                            AS slipped_deal_count,
    SUM(o.arr)                          AS slipped_arr,
    AVG(NOW()::date - o.close_date)     AS avg_days_past_due,
    MAX(NOW()::date - o.close_date)     AS max_days_past_due
FROM opportunities o
WHERE
    o.scenario_id = $1
    AND o.quarter = $2
    AND o.region  = $3
    AND o.segment = $4
    AND o.close_date < NOW()::date
    AND o.stage_name NOT IN ('Closed Won', 'Closed Lost');
