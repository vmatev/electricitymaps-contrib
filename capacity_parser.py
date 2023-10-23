"""
Usage: poetry run test_parser FR production
"""

import importlib
from logging import DEBUG, basicConfig, getLogger

import click

from electricitymap.contrib.capacity_parsers.constants import (
    CAPACITY_PARSER_SOURCE_TO_ZONES,
)
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.parsers import PARSER_KEY_TO_DICT
from scripts.utils import ROOT_PATH, run_shell_command

logger = getLogger(__name__)
basicConfig(level=DEBUG, format="%(asctime)s %(levelname)-8s %(name)-30s %(message)s")


CAPACITY_PARSERS = PARSER_KEY_TO_DICT["productionCapacity"]


# TODO create source to key mapping eg {"EMBER": [....]}


@click.command()
@click.option("--zone", default=None)
@click.option("--source", default=None)
@click.option("--target_datetime")
@click.option("--path", default=None, show_default=True)
@click.option("--update_aggregate", default=False, show_default=True)
def capacity_parser(
    zone: ZoneKey,
    source: str,
    target_datetime: str,
    update_aggregate: bool = False,
    path: str = None,
):
    """Parameters
    ----------
    zone: a two letter zone from the map or a zone group (EIA, ENTSOE, EMBER, IRENA)
    target_datetime: ISO 8601 string, such as 2018-05-30 15:00
    path: path to the data file for EMBER or IRENA zones, must be specified if zone is EMBER or IRENA. The data is collected from a spreadsheet or csv previously downloaded
    \n
    Examples
    -------
    >>> poetry run capacity_parser FR "2022-01-01"
    >>> poetry run capacity_parser None EMBER "2022-01-01" --path="/../data.csv"
    >>> poetry run capacity_parser None ENTSOE "2022-01-01"
    """
    # TODO add source argument to update zone groups (can be source or zone)
    assert zone is not None or source is not None
    assert not (zone is None and source is None)
    if source is not None:
        if source not in CAPACITY_PARSER_SOURCE_TO_ZONES:
            raise ValueError(f"No capacity parser developed for {source}")
        parser = getattr(
            importlib.import_module(f"capacity_parsers.{source}"),
            "fetch_production_capacity_for_all_zones",
        )
        if source in ["EMBER", "IRENA"]:
            if path is None:
                raise ValueError("path must be specified for EMBER or IRENA zones")
            parser(target_datetime=target_datetime, path=path)
        else:
            parser(target_datetime=target_datetime)

    elif zone is not None:
        if zone not in CAPACITY_PARSERS:
            raise ValueError(f"No capacity parser developed for {zone}")
        parser = CAPACITY_PARSERS[zone]
        if (
            zone
            in CAPACITY_PARSER_SOURCE_TO_ZONES["EMBER"]
            + CAPACITY_PARSER_SOURCE_TO_ZONES["IRENA"]
        ):
            if path is None:
                raise ValueError("path must be specified for EMBER or IRENA zones")
            parser(target_datetime=target_datetime, path=path, zone_key=zone)
        else:
            parser(zone_key=zone, target_datetime=target_datetime)

    print(f"Running prettier...")
    run_shell_command(f"web/node_modules/.bin/prettier --write .", cwd=ROOT_PATH)
