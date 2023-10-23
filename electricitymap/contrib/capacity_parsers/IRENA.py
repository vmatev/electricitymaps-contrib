from datetime import datetime

import pandas as pd

from electricitymap.contrib.capacity_parsers.constants import IRENA_ZONES_MAPPING
from electricitymap.contrib.config import ZoneKey
from scripts.utils import convert_datetime_str_to_isoformat, update_zone

IRENA_MODE_MAPPING = {
    "Biogas": "biomass",
    "Geothermal energy": "geothermal",
    "Liquid biofuels": "biomass",
    "Marine energy": "unknown",
    "Mixed Hydro Plants": "hydro",
    "Offshore wind energy": "wind",
    "Onshore wind energy": "wind",
    "Other non-renewable energy": "unknown",
    "Pumped storage": "hydro storage",
    "Renewable hydropower": "hydro",
    "Renewable municipal waste": "biomass",
    "Solar photovoltaic": "solar",
    "Solar thermal energy": "solar",
    "Solid biofuels": "biomass",
    "Coal and peat": "coal",
    "Fossil fuels n.e.s.": "unknown",
    "Natural gas": "gas",
    "Nuclear": "nuclear",
    "Oil": "oil",
    "Other non-renewable energy": "unknown",
}


SPECIFIC_MODE_MAPPING = {"IS": {"Fossil fuels n.e.s.": "oil"}}


def map_variable_to_mode(row: pd.Series) -> pd.DataFrame:
    zone = row["country"]
    variable = row["mode"]
    if zone in SPECIFIC_MODE_MAPPING:
        if variable in SPECIFIC_MODE_MAPPING[zone]:
            row["mode"] = SPECIFIC_MODE_MAPPING[zone][variable]
        else:
            row["mode"] = IRENA_MODE_MAPPING[variable]
    else:
        row["mode"] = IRENA_MODE_MAPPING[variable]
    return row


def get_capacity_data(path: str, target_datetime: datetime) -> dict:
    df = pd.read_excel(path, skipfooter=26)
    df = df.rename(
        columns={
            "Installed electricity capacity (MW) by Country/area, Technology, Grid connection and Year": "country",
            "Unnamed: 1": "mode",
            "Unnamed: 2": "category",
            "Unnamed: 3": "year",
            "Unnamed: 4": "value",
        }
    )
    df["country"] = df["country"].ffill()
    df["mode"] = df["mode"].ffill()
    df = df.dropna(axis=0, how="all")

    df_filtered = df.loc[df["country"].isin(list(IRENA_ZONES_MAPPING.keys()))]
    df_filtered["country"] = df_filtered["country"].map(IRENA_ZONES_MAPPING)

    df_filtered = df_filtered.apply(map_variable_to_mode, axis=1)
    df_filtered = df_filtered.dropna(axis=0, how="any")
    df_filtered = (
        df_filtered.groupby(["country", "mode", "year"])[["value"]].sum().reset_index()
    )
    capacity_dict = format_capacity(target_datetime, df_filtered)
    return capacity_dict


def format_capacity(target_datetime: datetime, data: pd.DataFrame) -> dict:
    df = data.copy()
    # filter by target_datetime.year
    df = df.loc[df["year"] == target_datetime.year]

    all_capacity = {}

    for zone in df["country"].unique():
        df_zone = df.loc[df["country"] == zone]
        zone_capacity = {}
        for idx, data in df_zone.iterrows():
            zone_capacity[data["mode"]] = {
                "value": round(float(data["value"]), 0),
                "source": "IRENA",
                "datetime": target_datetime.strftime("%Y-%m-%d"),
            }
        all_capacity[zone] = zone_capacity
    return all_capacity


def fetch_production_capacity_for_all_zones(
    path: str, target_datetime: str, zone_key: ZoneKey = "IRENA"
) -> None:
    target_datetime = convert_datetime_str_to_isoformat(target_datetime)
    all_capacity = get_capacity_data(path, target_datetime.year)
    for zone in all_capacity:
        update_zone(zone, all_capacity[zone])
        print(f"Updated capacity for {zone} in {target_datetime.year}")


def fetch_production_capacity(
    path: str, target_datetime: str, zone_key: ZoneKey
) -> None:
    target_datetime = convert_datetime_str_to_isoformat(target_datetime)
    all_capacity = get_capacity_data(path, target_datetime)
    zone_capacity = all_capacity[zone_key]
    update_zone(zone_key, zone_capacity)
    print(f"Updated capacity for {zone_key} in {target_datetime.year}")
