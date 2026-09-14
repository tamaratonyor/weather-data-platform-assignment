-- This is the model that makes station selection config-driven.
-- Adding a 6th city means adding one row to seeds/target_cities.csv --
-- nothing here changes. We resolve station_id by matching station metadata
-- (name + country) rather than ever writing a station_id literal in SQL.
--
-- Three defensive layers, each learned from checking real GHCN data rather
-- than assuming:
--
-- 1. Punctuation is stripped from both sides before comparing. GHCN station
--    names sourced from Environment Canada are inconsistent about "INTL" vs
--    "INT'L" vs "INT-L" -- stripping non-alphanumerics collapses all of
--    those to "INTL" so the seed doesn't need to guess NOAA's spelling.
--
-- 2. Matching is "contains ALL of these keywords ANYWHERE", not "contains
--    this exact phrase". Real airport names have infix qualifiers a simple
--    phrase match doesn't survive -- e.g. "OTTAWA MACDONALD-CARTIER INT'L".
--    Requiring each keyword to independently appear survives infix
--    qualifiers we haven't seen yet.
--
-- 3. Keyword matching alone is NOT sufficient to uniquely resolve a city.
--    Real GHCN data has multiple stations per major city: historical
--    records, renamed airports, secondary airports (Montreal has Mirabel
--    as well as the main airport), and duplicate entries for the same
--    airport under a different network code (Calgary has three "INTL"-ish
--    records). Requiring the matched station to actually have downloaded
--    observation data resolves this without guessing at naming
--    conventions like "shortest name wins" or "most recent wins" (recency
--    alone is NOT reliable -- one of Calgary's duplicate/historical
--    records has *more recent* data than the intended station). This
--    couples station resolution to ingestion/download_data.py's station
--    list, which is the one place this project already accepts a
--    hardcoded station list (see that file's docstring) -- so this isn't
--    a new exception, it's reusing the existing one as a disambiguator.

with target_cities as (

    select
        *,
        string_split(match_keywords, ';') as keywords
    from {{ ref('target_cities') }}

),

stations as (

    select
        *,
        regexp_replace(upper(station_name), '[^A-Z0-9/]', '', 'g') as normalized_name
    from {{ ref('stg_stations') }}

),

stations_with_data as (

    select s.*
    from stations s
    where exists (
        select 1
        from {{ source('raw', 'observations') }} o
        where o.station_id = s.station_id
    )

),

matched as (

    select
        tc.city_name,
        tc.notes,
        s.station_id,
        s.station_name,
        s.province_or_state,
        s.latitude,
        s.longitude,
        s.elevation,
        s.country_code

    from target_cities tc
    inner join stations_with_data s
        on s.country_code = tc.country_code
    where list_bool_and(
        list_transform(
            tc.keywords,
            kw -> s.normalized_name like '%' || regexp_replace(upper(trim(kw)), '[^A-Z0-9/]', '', 'g') || '%'
        )
    )

)

select * from matched