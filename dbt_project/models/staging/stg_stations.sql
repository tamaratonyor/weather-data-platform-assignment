with source as (

    select * from {{ source('raw', 'stations') }}

),

renamed as (

    select
        station_id,
        cast(latitude as double)   as latitude,
        cast(longitude as double)  as longitude,
        cast(elevation as double)  as elevation,
        state                      as province_or_state,
        name                       as station_name,
        gsn_flag,
        hcn_crn_flag,
        wmo_id,
        substr(station_id, 1, 2)   as country_code

    from source

)

select * from renamed
