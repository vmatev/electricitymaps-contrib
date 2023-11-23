from copy import deepcopy
from typing import Any

from electricitymap.contrib.config import CONFIG_DIR, ZONE_PARENT
from electricitymap.contrib.config.constants import PRODUCTION_MODES, STORAGE_MODES
from electricitymap.contrib.config.reading import read_zones_config
from electricitymap.contrib.lib.types import ZoneKey
from scripts.utils import write_zone_config

ZONES_CONFIG = read_zones_config(CONFIG_DIR)
CAPACITY_MODES = PRODUCTION_MODES + [f"{mode} storage" for mode in STORAGE_MODES]


def update_zone_capacity_config(zone_key: ZoneKey, data: dict) -> None:
    if zone_key not in ZONES_CONFIG:
        raise ValueError(f"Zone {zone_key} does not exist in the zones config")

    _new_zone_config = deepcopy(ZONES_CONFIG[zone_key])
    if "capacity" in _new_zone_config:
        capacity = _new_zone_config["capacity"]

        if all(isinstance(capacity[m], float | int) for m in capacity.keys()):
            capacity = data
        else:
            capacity = update_capacity_config(capacity, data)
    else:
        capacity = data

    _new_zone_config["capacity"] = capacity

    # sort keys
    _new_zone_config["capacity"] = {
        k: _new_zone_config["capacity"][k] for k in sorted(_new_zone_config["capacity"])
    }

    ZONES_CONFIG[zone_key] = _new_zone_config
    write_zone_config(zone_key, _new_zone_config)


def update_capacity_config(
    capacity_config: dict[str, Any], data: dict[str, Any]
) -> dict[str, Any]:
    """Update capacity config depending on the type of the existing capacity data.
    If the existing capacity is simply a value, it will be overwritten with the new format.
    If the existing capacity is a list, the new data will be appended to the list.
    If the existing capacity is a dict, the new data will be add to create list if the datetime is different else the datapoint is overwritten.
    """
    existing_capacity_modes = [mode for mode in data if mode in capacity_config]
    updated_capacity_config = deepcopy(capacity_config)
    for mode in existing_capacity_modes:
        if isinstance(capacity_config[mode], float | int):
            updated_capacity_config[mode] = data[mode]
        elif isinstance(capacity_config[mode], dict):
            updated_capacity_config[mode] = update_capacity_dict(
                mode, capacity_config, data
            )
        elif isinstance(capacity_config[mode], list):
            updated_capacity_config[mode] = update_capacity_list(
                mode, capacity_config, data
            )

    new_modes = [m for m in data if m not in capacity_config]
    for mode in new_modes:
        updated_capacity_config[mode] = data[mode]
    return updated_capacity_config


def update_capacity_dict(
    mode: str, capacity_config: dict[str, Any], data: [str, Any]
) -> dict[str, Any]:
    existing_capacity = capacity_config[mode]
    if existing_capacity["datetime"] != data[mode]["datetime"]:
        return [existing_capacity] + [data[mode]]
    else:
        return data[mode]


def update_capacity_list(
    mode: str, capacity_config: dict[str, Any], data: [str, Any]
) -> dict[str, Any]:
    if data[mode]["datetime"] not in [d["datetime"] for d in capacity_config[mode]]:
        return capacity_config[mode] + [data[mode]]
    else:
        # replace the capacity data point with the same datetime by the most recent update (from data)
        return [
            data[mode] if item["datetime"] == data[mode]["datetime"] else item
            for item in capacity_config[mode]
        ]


def check_capacity_config_type(capacity_config: list, config_type: type) -> None:
    """Check that the capacity config is of the specified type"""
    return (
        True
        if all(isinstance(item, config_type) for item in capacity_config)
        else False
    )


def update_aggregated_capacity_config(parent_zone: ZoneKey) -> dict[str, Any]:
    zone_keys = [zone for zone in ZONE_PARENT if ZONE_PARENT[zone] == parent_zone]
    parent_capacity_config = ZONES_CONFIG[parent_zone]["capacity"]

    all_capacity_configs = [ZONES_CONFIG[zone]["capacity"] for zone in zone_keys]

    for mode in CAPACITY_MODES:
        mode_capacity_configs = [
            capacity_config[mode] for capacity_config in all_capacity_configs
        ]
        if not check_capacity_config_type(
            mode_capacity_configs, mode_capacity_configs[0]
        ):
            raise ValueError(
                f"{parent_zone} capacity could not be updated because all capacity configs must have the same type"
            )
        datetime_values = set(
            [capacity_config["datetime"] for capacity_config in mode_capacity_configs]
        )
        sources = set(
            [capacity_config["source"] for capacity_config in mode_capacity_configs]
        )
        if check_capacity_config_type(mode_capacity_configs, dict):
            if len(datetime_values) != 1:
                raise ValueError(
                    f"{parent_zone} capacity could not be updated because all capacity configs must have the same datetime values"
                )
            else:
                aggregated_capacity_value = sum(
                    [
                        0
                        if capacity_config["value"] is None
                        else capacity_config["value"]
                        for capacity_config in mode_capacity_configs
                    ]
                )
                parent_capacity_config[mode]["value"] = aggregated_capacity_value
                parent_capacity_config[mode]["datetime"] = list(datetime_values)[0]
                parent_capacity_config[mode]["source"] = ", ".join(
                    [elem for elem in sources if elem is not None]
                )
        elif check_capacity_config_type(mode_capacity_configs, list):
            pass
            # extract values for the same datetime
