with source as (

    select * from {{ source('raw', 'observations') }}

),

renamed as (

    select
        station_id,
        strptime(date_raw, '%Y%m%d')::date as obs_date,
        element,
        try_cast(value as double)          as raw_value,
        nullif(mflag, '')                  as mflag,
        nullif(qflag, '')                  as qflag,
        nullif(sflag, '')                  as sflag,
        nullif(obs_time, '')               as obs_time

    from source

),

typed as (

    select
        *,
        -- GHCN uses -9999 as a missing-value sentinel
        case when raw_value = -9999 then null else raw_value end as clean_value,
        -- everything in the spec is stored in tenths of a unit
        case when raw_value = -9999 then null else raw_value / 10.0 end as value_scaled,
        -- a row is "quality flagged" if any QC flag fired -- used downstream
        -- for data-quality reporting, not silently dropped here
        (qflag is not null and qflag != '') as has_quality_flag

    from renamed

)

select
    station_id,
    obs_date,
    element,
    clean_value,
    value_scaled,
    mflag,
    qflag,
    sflag,
    obs_time,
    has_quality_flag
from typed
where obs_date between '{{ var("start_date") }}' and '{{ var("end_date") }}'
