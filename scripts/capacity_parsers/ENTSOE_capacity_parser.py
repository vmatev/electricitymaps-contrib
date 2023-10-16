import argparse
from datetime import datetime
from typing import Dict, List

from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.config import CONFIG_DIR, ZoneKey
from electricitymap.contrib.config.reading import read_zones_config
from parsers.ENTSOE import ENTSOE_DOMAIN_MAPPINGS, query_ENTSOE
from scripts.capacity_parsers.constants import AGGREGATED_ZONE_MAPPING, ENTSOE_ZONES
from scripts.utils import (
    ROOT_PATH,
    convert_datetime_str_to_isoformat,
    run_shell_command,
    update_zone,
)

"""
Update capacity configurations for ENTOS-E zones for a chosen year.
The zones included are: ["DK-DK1","DK-DK2", "NO-NO1","NO-NO2","NO-NO3","NO-NO4","NO-NO5"]

Example usage:
    poetry run python scripts/capacity_parsers/ENTSOE_capacity_parser.py
"""

SOURCE = "entsoe.eu"

ENDPOINT = "/api"
ENTSOE_HOST = "https://web-api.tp.entsoe.eu"


EU_PROXY = "https://eu-proxy-jfnx5klx2a-ew.a.run.app{endpoint}?host={host}"

ENTSOE_ENDPOINT = ENTSOE_HOST + ENDPOINT
ENTSOE_EU_PROXY_ENDPOINT = EU_PROXY.format(endpoint=ENDPOINT, host=ENTSOE_HOST)

ENTSOE_PARAMETER_TO_MODE = {
    "B01": "biomass",
    "B02": "coal",
    "B03": "coal",
    "B04": "gas",
    "B05": "coal",
    "B06": "oil",
    "B07": "coal",
    "B08": "coal",
    "B09": "geothermal",
    "B10": "hydro storage",
    "B11": "hydro",
    "B12": "hydro",
    "B13": "unknown",
    "B14": "nuclear",
    "B15": "unknown",
    "B16": "solar",
    "B17": "biomass",
    "B18": "wind",
    "B19": "wind",
    "B20": "unknown",
}


def query_capacity(
    in_domain: str, session: Session, target_datetime: datetime
) -> str | None:
    params = {
        "documentType": "A68",
        "processType": "A33",
        "in_Domain": in_domain,
        "periodStart": target_datetime.strftime("%Y01010000"),
        "periodEnd": target_datetime.strftime("%Y12312300"),
    }
    return query_ENTSOE(
        session,
        params,
        target_datetime=target_datetime,
        function_name=query_capacity.__name__,
    )


def fetch_capacity(zone_key: ZoneKey, target_datetime: datetime) -> dict:
    xml_str = query_capacity(
        ENTSOE_DOMAIN_MAPPINGS[zone_key], Session(), target_datetime
    )
    soup = BeautifulSoup(xml_str, "html.parser")
    # Each timeserie is dedicated to a different fuel type.
    capacity_dict = {}
    for timeseries in soup.find_all("timeseries"):
        fuel_code = str(
            timeseries.find_all("mktpsrtype")[0].find_all("psrtype")[0].contents[0]
        )
        end_date = datetime.strptime(
            timeseries.find_all("end")[0].contents[0], "%Y-%m-%dT%H:00Z"
        )
        if end_date.year != target_datetime.year:
            pass  # query_ENTSOE fetches data for 2 years, so we need to filter out the data for the previous year
        else:
            point = timeseries.find_all("point")
            value = float(point[0].find_all("quantity")[0].contents[0])
            if ENTSOE_PARAMETER_TO_MODE[fuel_code] in capacity_dict:
                capacity_dict[ENTSOE_PARAMETER_TO_MODE[fuel_code]]["value"] += value
            else:
                fuel_capacity_dict = {}
                fuel_capacity_dict["value"] = value
                fuel_capacity_dict["datetime"] = end_date.strftime("%Y-01-01")
                fuel_capacity_dict["source"] = SOURCE
                capacity_dict[ENTSOE_PARAMETER_TO_MODE[fuel_code]] = fuel_capacity_dict
    if capacity_dict == {}:
        raise ValueError(
            f"ENTSO-E capacity parser failed to find capacity data for {zone_key} on {target_datetime.date()}"
        )
    return capacity_dict

def fetch_all_capacity(target_datetime: datetime) -> dict:
    capacity_dict = {}
    for zone in ENTSOE_ZONES:
        try:
            zone_capacity = fetch_capacity(zone, target_datetime)
            capacity_dict[zone] = zone_capacity
            print(f"Updated capacity for {zone} on {target_datetime.date()}")
        except:
            print(f"Failed to update capacity for {zone} on {target_datetime.date()}")
            continue

    return capacity_dict

def fetch_and_update_all_entsoe_capacities(target_datetime: str) -> None:
    target_datetime = convert_datetime_str_to_isoformat(target_datetime)
    for zone in ENTSOE_ZONES:
        zone_capacity = fetch_capacity(zone, target_datetime)
        update_zone(zone, zone_capacity)
        print(f"Updated capacity for {zone} on {target_datetime.date()}")

def fetch_and_update_entsoe_capacities(zone_key:ZoneKey, target_datetime: str) -> None:
    target_datetime = convert_datetime_str_to_isoformat(target_datetime)
    zone_capacity = fetch_capacity(zone_key, target_datetime)
    update_zone(zone_key, zone_capacity)
    print(f"Updated capacity for {zone_key} on {target_datetime.date()}")

def update_aggregated_zone_capacities(zone_capacity_list:List[Dict[str,float]]):
    aggregated_zone_capacity = zone_capacity_list[0]
    for subzone_capacity in zone_capacity_list[1:]:
        for mode in subzone_capacity:
            if mode in aggregated_zone_capacity:
                aggregated_zone_capacity[mode]["value"] += subzone_capacity[mode][
                    "value"
                ]
            else:
                aggregated_zone_capacity[mode] = subzone_capacity[mode]
    return aggregated_zone_capacity

def fetch_and_update_aggregated_capacities(target_datetime: str) -> None:
    target_datetime = convert_datetime_str_to_isoformat(target_datetime)
    for zone in AGGREGATED_ZONE_MAPPING:
        zone_capacity_list = []
        for subzone in AGGREGATED_ZONE_MAPPING[zone]:
            zone_capacity_list.append(fetch_capacity(subzone, target_datetime))
        aggregated_zone_capacity = update_aggregated_zone_capacities(zone_capacity_list)
        update_zone(zone, aggregated_zone_capacity)

def update_aggregated_capacities(zone_key: ZoneKey, target_datetime: datetime) -> None:
    ZONES_CONFIG = read_zones_config(CONFIG_DIR)
    zone_capacity_list = []
    for zone in AGGREGATED_ZONE_MAPPING[zone_key]:
        zone_config_capacity = ZONES_CONFIG[zone]["capacity"]
        zone_capacity = {}
        for mode in zone_config_capacity:
            if type(zone_config_capacity[mode]) == dict:
                zone_capacity[mode] = zone_config_capacity[mode]
            elif type(zone_config_capacity[mode]) == list:
                # return item in list that has the same datetime as target_datetime
                i= 0
                while i < len(zone_config_capacity[mode]):
                    if zone_config_capacity[mode][i]["datetime"] == target_datetime:
                        zone_capacity[mode] = zone_config_capacity[mode][i]
                        break
                    i += 1
            elif (type(zone_config_capacity[mode]) == float) or (type(zone_config_capacity[mode]) == int):
                zone_capacity[mode] = {}
                zone_capacity[mode]["value"] = zone_config_capacity[mode]

        zone_capacity_list.append(zone_capacity)

    aggregated_zone_capacity = update_aggregated_zone_capacities(zone_capacity_list)
    breakpoint()
    update_zone(zone_key, aggregated_zone_capacity)




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target_datetime", help="The target_datetime to get capacity for"
    )
    parser.add_argument("--zone", help="The zone to get capacity for", default=None)
    args = parser.parse_args()
    target_datetime = args.target_datetime
    zone = args.zone

    if zone is None:
        print(f"Getting capacity for all ENTSOE zones at {target_datetime}")
        fetch_and_update_all_entsoe_capacities(target_datetime)
        for zone in AGGREGATED_ZONE_MAPPING:
            update_aggregated_capacities(zone, target_datetime)
            print(
            f"Updated aggregated zone {zone} with capacity for {target_datetime} in config/zones."
            )
    else:
        fetch_and_update_entsoe_capacities(zone, target_datetime)
        print(
            f"Updated {zone}.yaml with capacity for {target_datetime} in config/zones."
        )
        if any(zone in i for i in list(AGGREGATED_ZONE_MAPPING.values())):
            parent_zone = [item[0] for item in AGGREGATED_ZONE_MAPPING.items() if zone in item[1]]
            breakpoint()
            update_aggregated_capacities(parent_zone[0], "2022-01-01")
            print(
                f"Updated {parent_zone[0]}.yaml with capacity for {target_datetime} in config/zones."
            )
    run_shell_command(f"web/node_modules/.bin/prettier --write .", cwd=ROOT_PATH)



if __name__ == "__main__":
    main()