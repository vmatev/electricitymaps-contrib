import argparse
from datetime import datetime, timezone

import pandas as pd

from electricitymap.contrib.config import ZoneKey
from scripts.utils import (
    ROOT_PATH,
    convert_datetime_str_to_isoformat,
    run_shell_command,
    update_zone,
)

"""Disclaimer: this parser does not include distributed capacity. Solar capacity is much lower than in reality because the majority is distributed."""
CAPACITY_URL = "https://ons-dl-prod-opendata.s3.amazonaws.com/dataset/capacidade-geracao/CAPACIDADE_GERACAO.csv"
MODE_MAPPING = {
    "HIDRÁULICA": "hydro",
    "ÓLEO DIESEL": "unknown",
    "ÓLEO COMBUSTÍVEL": "unknown",
    "MULTI-COMBUSTÍVEL GÁS/DIESEL": "unknown",
    "MULTI-COMBUSTÍVEL DIESEL/ÓLEO": "unknown",
    "GÁS": "unknown",
    "RESÍDUO CICLO COMBINADO": "unknown",
    "EÓLICA": "wind",
    "CARVÃO": "unknown",
    "BIOMASSA": "unknown",
    "NUCLEAR": "nuclear",
    "RESÍDUOS INDUSTRIAIS": "unknown",
    "FOTOVOLTAICA": "solar",
}

REGION_MAPPING = {
    "NORDESTE": "BR-NE",
    "NORTE": "BR-N",
    "SUDESTE": "BR-CS",
    "SUL": "BR-S",
}


def get_capacity_for_all_zones(target_datetime: str) -> pd.DataFrame:
    df = pd.read_csv(CAPACITY_URL, sep=";")
    df = df[
        [
            "nom_subsistema",
            "nom_combustivel",
            "dat_entradaoperacao",
            "dat_desativacao",
            "val_potenciaefetiva",
        ]
    ]
    df = df.rename(
        columns={
            "nom_subsistema": "zone_key",
            "nom_combustivel": "mode",
            "dat_entradaoperacao": "start",
            "dat_desativacao": "end",
            "val_potenciaefetiva": "value",
        }
    )

    df["start"] = df["start"].apply(
        lambda x: pd.to_datetime(x, utc=False).replace(day=1, month=1)
    )
    df["end"] = df["end"].apply(
        lambda x: pd.to_datetime(x, utc=False).replace(day=31, month=12)
        if x is not None
        else x
    )

    df = filter_data_by_date(df, target_datetime)
    df["mode"] = df["mode"].map(MODE_MAPPING)
    df["zone_key"] = df["zone_key"].map(REGION_MAPPING)

    df = df.groupby(["zone_key", "mode", "datetime"])[["value"]].sum().reset_index()

    capacity = {}
    for zone in df["zone_key"].unique():
        zone_capacity_df = df.loc[df["zone_key"] == zone]
        zone_capacity = {}
        for idx, data in zone_capacity_df.iterrows():
            mode_capacity = {}
            mode_capacity["datetime"] = target_datetime.strftime("%Y-%m-%d")
            mode_capacity["value"] = data["value"]
            mode_capacity["source"] = "ons.org.br"
            zone_capacity[data["mode"]] = mode_capacity
        capacity[zone] = zone_capacity
    return capacity


def get_capacity_for_one_zone(zone_key: str, target_datetime: str) -> pd.DataFrame:
    return get_capacity_for_all_zones(target_datetime)[zone_key]


def get_and_update_capacity_for_all_zones(target_datetime: str):
    target_datetime = convert_datetime_str_to_isoformat(target_datetime)
    capacity = get_capacity_for_all_zones(target_datetime)
    for zone in capacity:
        update_zone(zone, capacity[zone])


def get_and_update_capacity_for_one_zone(zone_key: ZoneKey, target_datetime: str):
    target_datetime = convert_datetime_str_to_isoformat(target_datetime)
    capacity = get_capacity_for_one_zone(zone_key, target_datetime)
    update_zone(zone_key, capacity)


def filter_data_by_date(data: pd.DataFrame, target_datetime: datetime) -> pd.DataFrame:
    df = data.copy()
    max_datetime = df["start"].max()

    if target_datetime >= max_datetime:
        df = df.copy()
        df = df.loc[df["end"].isna()]
    else:
        df = df[
            (df["start"] <= target_datetime)
            & ((df["end"] >= target_datetime) | (df["end"].isna()))
        ]

    df["datetime"] = target_datetime
    return df


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
        print(f"Getting capacity for all BR zones at {target_datetime}")
        get_and_update_capacity_for_all_zones(target_datetime)
    else:
        print(f"Getting capacity for {zone} at {target_datetime}")
        get_and_update_capacity_for_one_zone(zone, target_datetime)

    print(f"Running prettier...")
    run_shell_command(f"web/node_modules/.bin/prettier --write .", cwd=ROOT_PATH)


if __name__ == "__main__":
    main()
