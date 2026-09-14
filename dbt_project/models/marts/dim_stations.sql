select
    station_id,
    city_name,
    station_name,
    province_or_state,
    country_code,
    latitude,
    longitude,
    elevation
from {{ ref('int_target_stations') }}
