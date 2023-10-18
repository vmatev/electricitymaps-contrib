import argparse
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from scripts.utils import (
    ROOT_PATH,
    convert_datetime_str_to_isoformat,
    run_shell_command,
    update_zone,
)

MODE_MAPPING = {
    "Hídrico":"hydro",
    "Carbón": "unknown",
    "Diésel":"unknown",
    "Gas Natural":"unknown",
    "Eólico":"wind",
    "Solar":"solar",
    "Termosolar":"solar",
    "Geotérmico":"geothermal",
    "Otros*":"unknown",
}


def get_capacity_data(target_datetime: datetime):
    url = "https://www.coordinador.cl/reportes-y-estadisticas/#Estadisticas"
    r: Response = Session().get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    links = soup.find_all("a", string="[por tecnología (desde 2000)]")
    for link in links:
        if "hist_cap" in link["href"]:
            capacity_link = link["href"]

    df = pd.read_excel(
        capacity_link, sheet_name="Capacidad por Tecnología", header=2, skipfooter=2
    )
    df = df.drop(columns=["Unnamed: 0", "TOTAL"])
    df = df.rename(columns={"Año": "datetime"})
    df = df.melt(id_vars=["datetime"], var_name="mode", value_name="value")
    df["mode"] = df["mode"].apply(lambda x:MODE_MAPPING[x.strip()])

    df = df.groupby(["datetime", "mode"])[["value"]].sum().reset_index()
    if target_datetime.year in df["datetime"].unique():
        df = df.loc[df["datetime"] == target_datetime.year]
        capacity = {}
        for idx, data in df.iterrows():
            mode_capacity = {}
            mode_capacity["datetime"] = target_datetime.strftime("%Y-%m-%d")
            mode_capacity["value"] = round(data["value"],0)
            mode_capacity["source"] = "coordinador.cl"
            capacity[data["mode"]] = mode_capacity
        return capacity
    else:
        raise ValueError(f"CL: No capacity data available for year {target_datetime.year}")


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

    if zone is None or zone == "CL-SEN":
        print(f"Getting capacity for {zone} at {target_datetime}")
        get_and_update_capacity_for_one_zone(zone, target_datetime)

    print(f"Running prettier...")
    run_shell_command(f"web/node_modules/.bin/prettier --write .", cwd=ROOT_PATH)


if __name__ == "__main__":
    main()
