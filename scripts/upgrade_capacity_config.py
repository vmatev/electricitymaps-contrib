import argparse
from copy import deepcopy
from pathlib import Path

import yaml

from electricitymap.contrib.config import CONFIG_DIR
from electricitymap.contrib.config.reading import read_zones_config

ZONES_CONFIG = read_zones_config(config_dir=CONFIG_DIR)

def update_capacity_config(zone:str):
    zone_config = ZONES_CONFIG[zone]
    if "capacity" in zone_config:
        capacity_config = zone_config["capacity"]
        for mode in capacity_config:
            mode_capacity = {"datetime":"2022-01-01",
                             "value": capacity_config[mode],
                             }
            capacity_config[mode] = mode_capacity
        zone_config["capacity"] = capacity_config

        # sort keys
        zone_config["capacity"] = {
            k: zone_config["capacity"][k] for k in sorted(zone_config["capacity"])
        }

        ZONES_CONFIG[zone] = zone_config

        with open(
            CONFIG_DIR.joinpath(f"zones/{zone}.yaml"), "w", encoding="utf-8"
        ) as f:
            f.write(yaml.dump(zone_config, default_flow_style=False))


#TODO add aggregated zones: sum capacity for zones that have subZoneName