import argparse
from datetime import datetime

import pandas as pd
import pycountry
import requests
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from scripts.capacity_parsers.constants import IRENA_ZONES
from scripts.utils import (
    ROOT_PATH,
    convert_datetime_str_to_isoformat,
    run_shell_command,
    update_zone,
)

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
}


def fetch_capacity_from_excel(
    path: str, zone: ZoneKey, target_datetime: datetime
) -> dict:
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

    df_filtered = df.loc[df["country"].isin(list(IRENA_ZONES.keys()))]
    df_filtered["mode"] = df_filtered["mode"].map(IRENA_MODE_MAPPING)
    df_filtered = df_filtered.dropna(axis=0, how="any")
    df_filtered = (
        df_filtered.groupby(["country", "mode", "year"])[["value"]].sum().reset_index()
    )
    capacity_dict = format_capacity(zone, target_datetime, df_filtered)

    return capacity_dict


def format_capacity(
    zone_key: ZoneKey, target_datetime: datetime, data: pd.DataFrame
) -> dict:
    df = data.copy()
    # filter by target_datetime.year
    df = df.loc[df["year"] == target_datetime.year]
    # filter by zone_key
    country = pycountry.countries.get(alpha_2=zone_key.split("-")[0]).name
    df = df.loc[df["country"].str.contains(country)]
    if df.empty:
        raise ValueError(f"No data for year {target_datetime.year} and zone {zone_key}")
    capacity = {}
    for idx, data in df.iterrows():
        mode_dict = {}
        mode_dict["value"] = float(data["value"])
        mode_dict["source"] = "IRENA"
        mode_dict["datetime"] = target_datetime.strftime("%Y-%m-%d")
        capacity[data["mode"]] = mode_dict
    return capacity


# TODO: compare renewable breakdown with Ember and merge two sources

if __name__ == "__main__":
    print(fetch_capacity_from_excel(
        "/Users/mathildedaugy/Repos/csvs/ELECCAP_20231005-122235.xlsx",
        "FR",
        datetime(2022, 1, 1),
    ))
