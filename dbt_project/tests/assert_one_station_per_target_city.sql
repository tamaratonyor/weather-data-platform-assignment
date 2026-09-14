-- Fails (returns rows) if any configured target city resolves to zero
-- stations (typo/format mismatch in match_name_pattern) or more than one
-- station (pattern too loose). This is the safety net for the whole
-- "config-driven, not hardcoded" design: a bad seed row should break the
-- build loudly, not silently produce a mart missing a city or double
-- counting one.

select
    tc.city_name,
    count(ts.station_id) as matched_station_count
from {{ ref('target_cities') }} tc
left join {{ ref('int_target_stations') }} ts
    on tc.city_name = ts.city_name
group by tc.city_name
having count(ts.station_id) != 1
