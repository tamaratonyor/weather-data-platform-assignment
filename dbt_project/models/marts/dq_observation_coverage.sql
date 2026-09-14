-- Rolls up completeness and flag rates per station-month so quality
-- problems are visible as a queryable table, not just buried in dbt test
-- output. Good candidate to eyeball before trusting narrative output.

with daily as (

    select * from {{ ref('fct_daily_weather') }}

),

monthly as (

    select
        station_id,
        city_name,
        date_trunc('month', obs_date) as month,
        count(*)                                   as days_in_mart,
        count(tmax_c)                               as days_with_tmax,
        count(tmin_c)                                as days_with_tmin,
        count(precip_mm)                             as days_with_precip,
        sum(case when any_element_flagged then 1 else 0 end) as days_with_any_flag,
        sum(case when tmax_c is not null and tmin_c is not null and tmax_c < tmin_c then 1 else 0 end) as days_tmax_lt_tmin

    from daily
    group by 1, 2, 3

)

select
    *,
    round(days_with_tmax::double / nullif(days_in_mart, 0), 3) as tmax_completeness,
    round(days_with_tmin::double / nullif(days_in_mart, 0), 3) as tmin_completeness,
    round(days_with_any_flag::double / nullif(days_in_mart, 0), 3) as flag_rate
from monthly
