import argparse
from datetime import datetime

import pandas as pd
import pycountry

from electricitymap.contrib.capacity_parsers.constants import EMBER_ZONES
from electricitymap.contrib.config import ZoneKey
from scripts.utils import (
    ROOT_PATH,
    convert_datetime_str_to_isoformat,
    run_shell_command,
    update_zone,
)

EMBER_VARIABLE_TO_MODE = {
    "Bioenergy": "biomass",
    "Coal": "coal",
    "Gas": "gas",
    "Hydro": "hydro",
    "Nuclear": "nuclear",
    "Other Fossil": "unknown", # mostly oil it seems
    "Other Renewables": "unknown",
    "Solar": "solar",
    "Wind": "wind",
}

SPECIFIC_MODE_MAPPING = {
    "BD": { "Other Fossil": "oil"},
    "CO": { "Other Fossil": "oil"},
    "CY": { "Other Fossil": "oil"},
    "KR": { "Other Fossil": "oil"},
    "KW": { "Other Fossil": "oil"},
    "MN": { "Other Fossil": "coal"},
    "SG": { "Other Fossil": "coal"},
    "SV": { "Other Fossil": "oil"},
    "TR": {"Other Fossil": "oil","Other Renewables": "geothermal"},
    "TW": { "Other Fossil": "oil"},
    "ZA": { "Other Fossil": "oil"},}


def map_variable_to_mode(row: pd.Series) -> pd.DataFrame:
    zone = row["zone_key"]
    variable = row["mode"]
    if zone in SPECIFIC_MODE_MAPPING:
        if variable in SPECIFIC_MODE_MAPPING[zone]:
            row["mode"] = SPECIFIC_MODE_MAPPING[zone][variable]
        else:
            row["mode"] = EMBER_VARIABLE_TO_MODE[variable]
    else:
        row["mode"] = EMBER_VARIABLE_TO_MODE[variable]
    return row

def get_data_from_csv(path: str, year:int) -> pd.DataFrame:
    df = pd.read_csv(path)

    df_capacity = format_ember_data(df, year)
    all_capacity = get_capacity_dict_from_df(df_capacity)
    return all_capacity


def format_ember_data(df: pd.DataFrame, year: int) -> pd.DataFrame:
    df_filtered = df.loc[df["Area type"] == "Country"].copy()
    df_filtered = df_filtered.loc[df_filtered["Year"] == year]
    if df_filtered.empty:
        raise ValueError(f"No data for year {year}")
    df_filtered = df_filtered.loc[
        (df_filtered["Category"] == "Capacity") & (df_filtered["Subcategory"] == "Fuel")
    ]
    # filter out Kosovo because it is not a country in pycountry
    df_filtered = df_filtered.loc[df_filtered["Area"] != "Kosovo"]

    df_filtered["country_code_iso2"] = df_filtered["Country code"].apply(
        lambda x: pycountry.countries.get(alpha_3=x).alpha_2
    )

    df_filtered = df_filtered.loc[df_filtered["country_code_iso2"].isin(EMBER_ZONES)]

    df_capacity = df_filtered[["country_code_iso2", "Year", "Variable", "Value"]]
    df_capacity = df_capacity.rename(
        columns={
            "country_code_iso2": "zone_key",
            "Year": "datetime",
            "Variable": "mode",
            "Value": "value",
        }
    )
    df_capacity["datetime"] = df_capacity["datetime"].apply(lambda x: datetime(x, 1, 1))
    df_capacity["value"] = df_capacity["value"] * 1000

    df_capacity = df_capacity.apply(map_variable_to_mode, axis=1)

    df_capacity = (
        df_capacity.groupby(["zone_key", "datetime", "mode"])[["value"]]
        .sum()
        .reset_index()
        .set_index(["zone_key"])
    )
    return df_capacity


def get_capacity_dict_from_df(df_capacity: pd.DataFrame) -> dict:
    all_capacity = {}
    for zone in df_capacity.index.unique():
        df_zone = df_capacity.loc[zone]
        zone_capacity = {}
        for i, data in df_zone.iterrows():
            mode_capacity = {}
            mode_capacity["datetime"] = data["datetime"].strftime("%Y-%m-%d")
            mode_capacity["value"] = round(float(data["value"]),0)
            mode_capacity["source"] = "Ember, Yearly electricity data"
            zone_capacity[data["mode"]] = mode_capacity
        all_capacity[zone] = zone_capacity
    return all_capacity

def fetch_production_capacity_for_all_zones(path:str, target_datetime:str, zone_key:ZoneKey="EMBER")-> None:
    target_datetime = convert_datetime_str_to_isoformat(target_datetime)
    all_capacity = get_data_from_csv(path, target_datetime.year)
    for zone in all_capacity:
        update_zone(zone, all_capacity[zone])
        print(f"Updated capacity for {zone} in {target_datetime.year}")

def fetch_production_capacity(path:str, target_datetime:str, zone_key:ZoneKey) -> None:
    target_datetime = convert_datetime_str_to_isoformat(target_datetime)
    all_capacity = get_data_from_csv(path, target_datetime.year)
    zone_capacity = all_capacity[zone_key]
    update_zone(zone_key, zone_capacity)
    print(f"Updated capacity for {zone_key} in {target_datetime.year}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="The path to the csv file")
    parser.add_argument("--zone", help="The zone to get capacity for", default=None)
    parser.add_argument(
        "--target_datetime", help="The target_datetime to get capacity for"
    )
    args = parser.parse_args()
    path = args.path
    zone = args.zone
    target_datetime = args.target_datetime

    if zone is None:
        print(f"Getting capacity for all zones at {target_datetime}")
        fetch_production_capacity_for_all_zones(path, target_datetime)
    else:
        print(f"Getting capacity for {zone} at {target_datetime}")
        fetch_production_capacity(path, target_datetime, zone)

    print(f"Running prettier...")
    run_shell_command(f"web/node_modules/.bin/prettier --write .", cwd=ROOT_PATH)



if __name__ == "__main__":
    main()