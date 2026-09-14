with source as (

    select * from {{ source('raw', 'inventory') }}

),

renamed as (

    select
        station_id,
        element,
        cast(first_year as integer) as first_year,
        cast(last_year as integer)  as last_year

    from source

)

select * from renamed
