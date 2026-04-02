-- Coverage: pipeline ARR vs quota per stage
SELECT
    o.stage_name,
    COUNT(*)        AS deal_count,
    SUM(o.arr)      AS pipeline_arr,
    AVG(o.arr)      AS avg_deal_size
FROM opportunities o
WHERE
    o.scenario_id = $1
    AND o.quarter = $2
    AND o.region  = $3
    AND o.segment = $4
    AND o.stage_name NOT IN ('Closed Won', 'Closed Lost')
GROUP BY o.stage_name
ORDER BY
    CASE o.stage_name
        WHEN 'Discovery'   THEN 1
        WHEN 'Demo'        THEN 2
        WHEN 'Proposal'    THEN 3
        WHEN 'Negotiation' THEN 4
        ELSE 5
    END;
