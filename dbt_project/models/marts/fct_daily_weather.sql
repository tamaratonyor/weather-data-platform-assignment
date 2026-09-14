select
    o.station_id,
    o.city_name,
    o.obs_date,
    o.tmax                as tmax_c,
    o.tmin                as tmin_c,
    o.prcp                as precip_mm,
    o.snow                as snow_mm,
    o.snwd                as snow_depth_mm,
    o.awnd                as avg_wind_ms,
    -- rolled-up data quality signal for this row: did ANY reported
    -- element carry a QC flag from NOAA's own quality control?
    (
        coalesce(o.tmax_flagged, false) or coalesce(o.tmin_flagged, false)
        or coalesce(o.prcp_flagged, false) or coalesce(o.snow_flagged, false)
        or coalesce(o.snwd_flagged, false) or coalesce(o.awnd_flagged, false)
    ) as any_element_flagged
from {{ ref('int_observations_pivoted') }} o
