{%- set supported_elements = var('supported_elements') -%}

-- Element selection is driven by ghcnd-inventory.txt (does this station
-- actually report this element, in this year?) intersected with the
-- `supported_elements` var (elements we know how to narrate). Neither
-- side hardcodes a station. The Jinja loop below just turns N config
-- values into N pivoted columns -- add an element to the var, not to
-- the SQL logic, and it flows through automatically.

with target_stations as (

    select station_id, city_name from {{ ref('int_target_stations') }}

),

inventory as (

    select station_id, element, first_year, last_year
    from {{ ref('stg_inventory') }}
    where element in ({{ "'" ~ supported_elements|join("','") ~ "'" }})

),

observations as (

    select o.*
    from {{ ref('stg_observations') }} o
    inner join target_stations t
        on o.station_id = t.station_id
    inner join inventory i
        on o.station_id = i.station_id
        and o.element = i.element
        and extract(year from o.obs_date) between i.first_year and i.last_year

),

pivoted as (

    select
        station_id,
        obs_date,
        {% for elem in supported_elements -%}
        max(case when element = '{{ elem }}' then value_scaled end) as {{ elem|lower }},
        max(case when element = '{{ elem }}' then has_quality_flag end) as {{ elem|lower }}_flagged{% if not loop.last %},{% endif %}
        {% endfor %}
    from observations
    group by station_id, obs_date

)

select
    p.*,
    t.city_name
from pivoted p
inner join target_stations t
    on p.station_id = t.station_id
