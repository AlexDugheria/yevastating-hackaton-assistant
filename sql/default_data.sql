select amp.client_name,
       amp.journey_id,
       mp.journey_name,
       amp.mediaplan_id,
       mp.mediaplan_name,
       mp.channel_name,
       mp.channel_id,
       mp.platform_name,
       mp.platform_id,
       mp.mediarow_name,
       mp.mediarow_id,
       mp.mediarow_lifetime_budget as budget
FROM ds_active_mediaplans_main amp
JOIN ds_mediaplan_dim_main mp
    ON amp.mediaplan_id = mp.mediaplan_id
    AND amp.journey_id = mp.journey_id
WHERE mp.client_id = '{client_id}'
AND amp.client_id = '{client_id}'