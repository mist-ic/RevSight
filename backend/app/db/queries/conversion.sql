-- Stage-to-stage conversion rates
SELECT
    psh.from_stage,
    psh.to_stage,
    COUNT(*)                                                AS transitions,
    COUNT(*) FILTER (WHERE psh.to_stage = 'Closed Won')   AS won_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE psh.to_stage NOT IN ('Closed Lost'))
        / NULLIF(COUNT(*), 0),
        1
    )                                                       AS forward_conversion_pct
FROM pipeline_stage_history psh
JOIN opportunities o ON psh.opportunity_id = o.id
WHERE
    o.scenario_id = $1
    AND o.quarter = $2
    AND o.region  = $3
    AND o.segment = $4
GROUP BY psh.from_stage, psh.to_stage
ORDER BY psh.from_stage, psh.to_stage;
