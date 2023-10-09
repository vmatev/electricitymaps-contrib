import argparse
from datetime import datetime

from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.config import ZoneKey
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

def fetch_all_capacity( target_datetime: datetime) -> dict:
    capacity_dict = {}
    for zone in ENTSOE_ZONES:
        try:
            zone_capacity = fetch_capacity(zone, target_datetime)
            capacity_dict[zone] = zone_capacity
            print(zone + "done")
        except:
            print(zone + "failed")
            continue
    import pandas as pd
    all_capacity = pd.DataFrame()
    for zone in capacity_dict:
        df = pd.DataFrame.from_dict(capacity_dict[zone], orient='index')
        df["zone"] = zone
        all_capacity = pd.concat([all_capacity, df])
    breakpoint()
    return capacity_dict

def fetch_and_update_entsoe_capacities(target_datetime: str) -> None:
    target_datetime = convert_datetime_str_to_isoformat(target_datetime)
    for zone in ENTSOE_ZONES:
        zone_capacity = fetch_capacity(zone, target_datetime)
        update_zone(zone, zone_capacity)
        print(f"Updated capacity for {zone} on {target_datetime.date()}")


def update_aggregated_capacities(target_datetime: datetime) -> None:
    target_datetime = convert_datetime_str_to_isoformat(target_datetime)
    for zone in AGGREGATED_ZONE_MAPPING:
        zone_capacity_list = []
        for subzone in AGGREGATED_ZONE_MAPPING[zone]:
            zone_capacity_list.append(fetch_capacity(subzone, target_datetime))
        aggregated_zone_capacity = zone_capacity_list[0]
        for subzone_capacity in zone_capacity_list[1:]:
            for mode in subzone_capacity:
                if mode in aggregated_zone_capacity:
                    aggregated_zone_capacity[mode]["value"] += subzone_capacity[mode][
                        "value"
                    ]
                else:
                    aggregated_zone_capacity[mode] = subzone_capacity[mode]
        update_zone(zone, aggregated_zone_capacity)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "target_datetime", help="The target_datetime to get capacity for"
    )
    args = parser.parse_args()
    target_datetime = args.target_datetime

    print(f"Getting capacity for all ENTSOE zones at {target_datetime}")
    fetch_and_update_entsoe_capacities(target_datetime)
    update_aggregated_capacities(target_datetime)

    run_shell_command(f"web/node_modules/.bin/prettier --write .", cwd=ROOT_PATH)

    for zone in ENTSOE_ZONES:
        print(
            f"Updated {zone}.yaml with capacity for {target_datetime} in config/zones."
        )
    print(
        f"Updated aggregated zones with capacity for {target_datetime} in config/zones."
    )


if __name__ == "__main__":
    fetch_all_capacity(datetime(2022,1,1))
