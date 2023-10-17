import argparse
from datetime import datetime
from logging import Logger, getLogger

import pandas as pd
from requests import Response, Session

from electricitymap.contrib.config import ZONES_CONFIG, ZoneKey
from parsers.EIA import REGIONS
from parsers.lib.utils import get_token
from scripts.utils import (
    ROOT_PATH,
    convert_datetime_str_to_isoformat,
    run_shell_command,
    update_zone,
)

CAPACITY_URL = "https://api.eia.gov/v2/electricity/operating-generator-capacity/data/?frequency=monthly&data[0]=nameplate-capacity-mw&facets[balancing_authority_code][]={}"
API_KEY = get_token("EIA_KEY")
US_ZONES = {key: value for key, value in REGIONS.items() if key.startswith("US-")}
TECHNOLOGY_TO_MODE = {
    "All Other": "unknown",
    "Batteries": "battery storage",
    "Coal Integrated Gasification Combined Cycle": "coal",
    "Conventional Hydroelectric": "hydro",
    "Conventional Steam Coal": "coal",
    "Flywheels": "battery storage",
    "Geothermal": "geothermal",
    "Hydroelectric Pumped Storage": "hydro storage",
    "Landfill Gas": "biomass",
    "Municipal Solid Waste": "biomass",  # or unknown?
    "Natural Gas Fired Combined Cycle": "gas",
    "Natural Gas Fired Combustion Turbine": "gas",
    "Natural Gas Internal Combustion Engine": "gas",
    "Natural Gas Steam Turbine": "gas",
    "Natural Gas with Compressed Air Storage": "gas",
    "Nuclear": "nuclear",
    "Offshore Wind Turbine": "wind",
    "Onshore Wind Turbine": "wind",
    "Other Gases": "unknown",
    "Other Natural Gas": "gas",
    "Other Waste Biomass": "biomass",
    "Petroleum Coke": "coal",
    "Petroleum Liquids": "oil",
    "Solar Photovoltaic": "solar",
    "Solar Thermal with Energy Storage": "solar",
    "Solar Thermal without Energy Storage": "solar",
    "Wood/Wood Waste Biomass": "biomass",
}


def fetch_capacity(
    zone_key: str,
    target_datetime: datetime,
    logger: Logger = getLogger(__name__),
) -> pd.DataFrame:
    url_prefix = CAPACITY_URL.format(REGIONS[zone_key])
    url = f'{url_prefix}&api_key={API_KEY}&start={target_datetime.strftime("%Y-%m")}-01&end={target_datetime.strftime("%Y-%m")}-12&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5000'
    r: Response = Session().get(url)
    json_data = r.json()
    if json_data.get("response", {}).get("data", []) == []:
        logger.warning(
            f"Failed to fetch capacity data for {zone_key} at {target_datetime.strftime('%Y-%m')}"
        )
        return pd.DataFrame()
    else:
        data = pd.DataFrame(json_data["response"]["data"])
        capacity_dict = format_capacity(data, target_datetime)
        return capacity_dict


def format_capacity(df: pd.DataFrame, target_datetime: datetime) -> dict:
    df = df.copy()
    df = df.loc[df["statusDescription"] == "Operating"]
    df["mode"] = df["technology"].map(TECHNOLOGY_TO_MODE)
    df_aggregated = df.groupby(["mode"])[["nameplate-capacity-mw"]].sum().reset_index()
    capacity_dict = {}
    for mode in df_aggregated["mode"].unique():
        mode_dict = {}
        mode_dict["value"] = float(
            df_aggregated.loc[df_aggregated["mode"] == mode][
                "nameplate-capacity-mw"
            ].sum()
        )
        mode_dict["source"] = "EIA"
        mode_dict["datetime"] = target_datetime.strftime("%Y-%m-%d")
        capacity_dict[mode] = mode_dict
    return capacity_dict


def get_and_update_capacity_for_one_zone(
    zone_key: ZoneKey, target_datetime: str
) -> None:
    target_datetime = convert_datetime_str_to_isoformat(target_datetime)
    zone_capacity = fetch_capacity(zone_key, target_datetime)
    if zone_key in ZONES_CONFIG:
        update_zone(zone_key, zone_capacity)


def get_and_update_capacity_for_all_zones(target_datetime: str) -> pd.DataFrame:
    target_datetime = convert_datetime_str_to_isoformat(target_datetime)
    for zone in US_ZONES:
        zone_capacity = fetch_capacity(zone, target_datetime)
        if zone in ZONES_CONFIG:
            update_zone(zone, zone_capacity)
            print(
                f"Fetched and updated capacity data for {zone} at {target_datetime.strftime('%Y-%m')}"
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zone", help="The zone to get capacity for", default=None)
    parser.add_argument(
        "--target_datetime", help="The target_datetime to get capacity for"
    )
    args = parser.parse_args()
    zone = args.zone
    target_datetime = args.target_datetime

    print(f"Getting capacity for {zone} at {target_datetime}")
    if zone is None:
        get_and_update_capacity_for_all_zones(target_datetime)
    else:
        get_and_update_capacity_for_one_zone(zone, target_datetime)

    run_shell_command(f"web/node_modules/.bin/prettier --write .", cwd=ROOT_PATH)

    print(
        f"Updated yaml configuration for {zone} with capacity for {target_datetime} in config/zones."
    )


if __name__ == "__main__":
    main()
