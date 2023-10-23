import argparse
from copy import deepcopy
from pathlib import Path

import yaml

from electricitymap.contrib.config import CONFIG_DIR
from electricitymap.contrib.config.reading import read_zones_config
from electricitymap.contrib.capacity_parsers.constants import (
    EIA_ZONES,
    EMBER_ZONES,
    ENTSOE_ZONES,
    IRENA_ZONES,
    REE_ZONES,
)
from scripts.utils import ROOT_PATH, run_shell_command

ZONES_CONFIG = read_zones_config(config_dir=CONFIG_DIR)
CAPACITY_SOURCE_TO_ZONES = {
    "EMBER": EMBER_ZONES,
    "EIA": EIA_ZONES,
    "ENTSOE": ENTSOE_ZONES,
    "IRENA": IRENA_ZONES,
    "REE": REE_ZONES,
    "OPENNEM": ["AU-VIC", "AU-NSW", "AU-QLD", "AU-SA", "AU-TAS", "AU-WA", "AU-NT"],
    "ONS": ["BR-NE", "BR-CS", "BR-N", "BR-S"],
}


def update_parser_config(zone: str, source: str):
    zone_config = ZONES_CONFIG[zone]
    if "parsers" in zone_config:
        parsers_config = zone_config["parsers"]
        parsers_config["productionCapacity"] = f"{source}.fetch_production_capacity"
        with open(
            CONFIG_DIR.joinpath(f"zones/{zone}.yaml"), "w", encoding="utf-8"
        ) as f:
            f.write(yaml.dump(zone_config, default_flow_style=False))


for source,zones in CAPACITY_SOURCE_TO_ZONES.items():
    for zone in zones:
        update_parser_config(zone,source)

print(f"Running prettier...")
run_shell_command(f"web/node_modules/.bin/prettier --write .", cwd=ROOT_PATH)