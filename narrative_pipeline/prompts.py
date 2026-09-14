"""Prompt construction for daily weather narratives."""

SYSTEM_INSTRUCTION = (
    "You are a concise local weather reporter. Given structured daily "
    "observation data for a Canadian city, write a natural-sounding "
    "2-3 sentence weather summary for that specific day. "
    "Only state facts present in the data -- if a field is missing, "
    "do not mention or guess at it. Do not invent forecasts; this is a "
    "recap of a day that already happened. Avoid generic filler."
)


def build_prompt(row: dict) -> str:
    """row is one record from fct_daily_weather (as a dict)."""
    facts = []
    if row.get("tmax_c") is not None:
        facts.append(f"high of {row['tmax_c']:.1f}°C")
    if row.get("tmin_c") is not None:
        facts.append(f"low of {row['tmin_c']:.1f}°C")
    if row.get("precip_mm") is not None:
        facts.append(f"{row['precip_mm']:.1f}mm of precipitation")
    if row.get("snow_mm") is not None and row["snow_mm"] > 0:
        facts.append(f"{row['snow_mm']:.1f}mm of new snow")
    if row.get("avg_wind_ms") is not None:
        facts.append(f"average wind speed of {row['avg_wind_ms']:.1f} m/s")

    facts_str = "; ".join(facts) if facts else "no observations recorded"

    return (
        f"City: {row['city_name']}\n"
        f"Date: {row['obs_date']}\n"
        f"Observations: {facts_str}\n\n"
        "Write the narrative now."
    )
