"""
Usage: poetry run test_parser FR production
"""

import importlib
import pprint
import time
from collections.abc import Callable
from datetime import datetime, timezone
from logging import DEBUG, basicConfig, getLogger
from typing import Any

import click

from electricitymap.contrib.lib.types import ZoneKey
from scripts.capacity_parsers.constants import (
    AGGREGATED_ZONE_MAPPING,
    EIA_ZONES,
    EMBER_ZONES,
    ENTSOE_ZONES,
    REE_ZONES,
)
from scripts.utils import (
    ROOT_PATH,
    convert_datetime_str_to_isoformat,
    run_shell_command,
    update_zone,
)

logger = getLogger(__name__)
basicConfig(level=DEBUG, format="%(asctime)s %(levelname)-8s %(name)-30s %(message)s")


def populate_capacity_parsers():
    capacity_parsers = {}

    # zone groups
    capacity_parsers["EMBER"] = getattr(
        importlib.import_module("scripts.capacity_parsers.EMBER_capacity_parser"),
        "get_and_update_capacity_for_all_zones",
    )
    capacity_parsers["ENTSOE"] = getattr(
        importlib.import_module("scripts.capacity_parsers.ENTSOE_capacity_parser"),
        "get_and_update_capacity_for_all_zones",
    )
    capacity_parsers["EIA"] = getattr(
        importlib.import_module("scripts.capacity_parsers.EIA_capacity_parser"),
        "get_and_update_capacity_for_all_zones",
    )
    capacity_parsers["REE"] = getattr(
        importlib.import_module("scripts.capacity_parsers.REE_capacity_parser"),
        "get_and_update_capacity_for_all_zones",
    )
    capacity_parsers["ONS"] = getattr(
        importlib.import_module("scripts.capacity_parsers.ONS_capacity_parser"),
        "get_and_update_capacity_for_all_zones",
    )
    capacity_parsers["OPENNEM"] = getattr(
        importlib.import_module("scripts.capacity_parsers.OPENNEM_capacity_parser"),
        "get_and_update_capacity_for_all_zones",
    )

    # individual zones
    for zone in ENTSOE_ZONES:
        capacity_parsers[zone] = getattr(
            importlib.import_module("scripts.capacity_parsers.ENTSOE_capacity_parser"),
            "get_and_update_capacity_for_one_zone",
        )
    for zone in EMBER_ZONES:
        capacity_parsers[zone] = getattr(
            importlib.import_module("scripts.capacity_parsers.EMBER_capacity_parser"),
            "get_and_update_capacity_for_one_zone",
        )
    for zone in EIA_ZONES:
        capacity_parsers[zone] = getattr(
            importlib.import_module("scripts.capacity_parsers.EIA_capacity_parser"),
            "get_and_update_capacity_for_one_zone",
        )
    for zone in REE_ZONES:
        capacity_parsers[zone] = getattr(
            importlib.import_module("scripts.capacity_parsers.REE_capacity_parser"),
            "get_and_update_capacity_for_one_zone",
        )
    for zone in AGGREGATED_ZONE_MAPPING["BR"]:
        capacity_parsers[zone] = getattr(
            importlib.import_module("scripts.capacity_parsers.ONS_capacity_parser"),
            "get_and_update_capacity_for_one_zone",
        )
    for zone in AGGREGATED_ZONE_MAPPING["AU"]:
        capacity_parsers[zone] = getattr(
            importlib.import_module("scripts.capacity_parsers.OPENNEM_capacity_parser"),
            "get_and_update_capacity_for_one_zone",
        )
    capacity_parsers["CL-SEN"] = getattr(
        importlib.import_module("scripts.capacity_parsers.CL_capacity_parser"),
        "get_and_update_capacity_for_one_zone",
    )
    capacity_parsers["CA-ON"] = getattr(
        importlib.import_module("scripts.capacity_parsers.CA_ON_capacity_parser"),
        "get_and_update_capacity_for_one_zone",
    )
    capacity_parsers["CA-QC"] = getattr(
        importlib.import_module("scripts.capacity_parsers.CA_QC_capacity_parser"),
        "get_and_update_capacity_for_one_zone",
    )
    capacity_parsers["MY-WM"] = getattr(
        importlib.import_module("scripts.capacity_parsers.MY-WM_capacity_parser"),
        "get_and_update_capacity_for_one_zone",
    )
    return capacity_parsers


CAPACITY_PARSERS = populate_capacity_parsers()


@click.command()
@click.option("--zone", show_default=True)
@click.option("--target_datetime", show_default=True)
@click.option("--data_path", default=None, show_default=True)
@click.option("--update_aggregate", default=False, show_default=True)
def capacity_parser(
    zone: ZoneKey,
    target_datetime: str,
    update_aggregate: bool = False,
    data_path: str = None,
):
    """ """
    if zone not in CAPACITY_PARSERS:
        raise ValueError(f"No capacity parser developed for {zone}")
    if zone == "EMBER" or zone in EMBER_ZONES:
        if data_path is None:
            raise ValueError("data_path must be specified for EMBER zones")
        parser = CAPACITY_PARSERS[zone]
        parser(target_datetime=target_datetime, path=data_path, zone_key=zone)
    else:
        parser = CAPACITY_PARSERS[zone]
        parser(zone_key=zone, target_datetime=target_datetime)

    print(f"Running prettier...")
    run_shell_command(f"web/node_modules/.bin/prettier --write .", cwd=ROOT_PATH)
