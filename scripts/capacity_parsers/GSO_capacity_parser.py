import argparse
import json
from datetime import datetime

import pandas as pd
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from scripts.utils import (
    ROOT_PATH,
    convert_datetime_str_to_isoformat,
    run_shell_command,
    update_zone,
)

"""Disclaimer: only valid for real-time data, historical capacity is not available"""

MODE_MAPPING = {"Gas": "gas", "Water": "hydro", "Coal": "coal", "Solar": "solar"}


def get_capacity_data(target_datetime: datetime) -> dict:
    url = "https://www.gso.org.my/SystemData/PowerStation.aspx/GetDataSource"

    headers = {
        "Content-Type": "application/json",
        "Origin": "https://www.gso.org.my",
        "Referer": "https://www.gso.org.my/SystemData/PowerStation.aspx",
    }

    r: Response = Session().post(url, headers=headers)

    if r.status_code == 200:
        data = pd.DataFrame(json.loads(r.json()["d"]))
        data = data[["PPAExpiry", "Fuel", "Capacity (MW)"]]
        data = data.rename(
            columns={
                "PPAExpiry": "expiry_datetime",
                "Fuel": "mode",
                "Capacity (MW)": "value",
            }
        )
        data["mode"] = data["mode"].apply(lambda x: x.strip())
        data["mode"] = data["mode"].apply(lambda x: MODE_MAPPING[x])
        data["expiry_datetime"] = data["expiry_datetime"].apply(
            lambda x: pd.to_datetime(x).replace(day=31, month=12)
        )

        filtered_data = data.loc[data["expiry_datetime"] > target_datetime]
        filtered_data = filtered_data.groupby(["mode"])[["value"]].sum().reset_index()

        capacity_dict = {}
        for idx, data in filtered_data.iterrows():
            capacity_dict[data["mode"]] = {
                "value": data["value"],
                "source": "gso.org.my",
                "datetime": target_datetime.strftime("%Y-%m-%d"),
            }
        return capacity_dict
    else:
        raise ValueError(f"Failed to fetch capacity data for GSO at {target_datetime.strftime('%Y-%m')}")

def get_and_update_capacity_for_one_zone(zone_key:ZoneKey, target_datetime: str) -> None:
    target_datetime = convert_datetime_str_to_isoformat(target_datetime)
    zone_capacity = get_capacity_data(target_datetime)
    update_zone(zone_key, zone_capacity)
    print(f"Updated capacity for {zone_key} on {target_datetime.date()}")

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
        zone = "MY-WM"

    print(f"Getting capacity for {zone} at {target_datetime}")
    get_and_update_capacity_for_one_zone(zone, target_datetime)

    print(f"Running prettier...")
    run_shell_command(f"web/node_modules/.bin/prettier --write .", cwd=ROOT_PATH)

if __name__ == "__main__":
    main()