"""Contains utility functions, e.g. for patching JSON files."""

import json
import pathlib
import subprocess
from copy import deepcopy
from datetime import datetime
from os import PathLike, listdir, path

import yaml

from electricitymap.contrib.config import CONFIG_DIR
from electricitymap.contrib.config.reading import read_zones_config
from electricitymap.contrib.lib.types import ZoneKey

ROOT_PATH = pathlib.Path(__file__).parent.parent
LOCALES_FOLDER_PATH = ROOT_PATH / "web/public/locales/"
LOCALE_FILE_PATHS = [
    LOCALES_FOLDER_PATH / f
    for f in listdir(LOCALES_FOLDER_PATH)
    if path.isfile(LOCALES_FOLDER_PATH / f) and f.endswith(".json")
]

ZONES_CONFIG = read_zones_config(CONFIG_DIR)


def run_shell_command(cmd: str, cwd: PathLike | str = "") -> str:
    return subprocess.check_output(cmd, shell=True, encoding="utf8", cwd=cwd).rstrip(
        "\n"
    )


class JsonFilePatcher:
    """
    A helping hand to patch JSON files.

    Example:

    with JsonFilePatcher(ROOT_PATH / "web/geo/world.geojson") as f:
        if zone in f.content:
            del f.content[zone]
    """

    def __init__(self, file_path: PathLike | str, indent=2):
        self.file_path = file_path
        self.indent = indent

    def __enter__(self):
        with open(self.file_path) as f:
            self.content: dict = json.load(f)

        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            raise

        with open(self.file_path, "w") as f:
            json.dump(
                self.content,
                f,
                indent=self.indent,
                ensure_ascii=False,
            )
            # TODO: enable sort_keys=True
            f.write("\n")

        print(f"🧹 Patched {self.file_path.relative_to(ROOT_PATH)}")


def update_zone(zone_key: ZoneKey, data: dict) -> None:
    if zone_key not in ZONES_CONFIG:
        raise ValueError(f"Zone {zone_key} does not exist in the zones config")

    _new_zone_config = deepcopy(ZONES_CONFIG[zone_key])
    if "capacity" in _new_zone_config:
        capacity = _new_zone_config["capacity"]

        if all(
            isinstance(capacity[m], float) or isinstance(capacity[m], int)
            for m in capacity.keys()
        ):
            capacity = data
        else:
            for mode in capacity:
                if isinstance(capacity[mode], float) or isinstance(capacity[mode], int):
                    if mode in data:
                        capacity[mode] = data[mode]
                elif isinstance(capacity[mode], dict):
                    existing_capacity = capacity[mode]
                    if mode in data:
                        if existing_capacity["datetime"] != data[mode]["datetime"]:
                            capacity[mode] = [existing_capacity] + [data[mode]]
                elif isinstance(capacity[mode], list):
                    if mode in data:
                        if data[mode]["datetime"] not in [
                            d["datetime"] for d in capacity[mode]
                        ]:
                            capacity[mode].append(data[mode])
            new_modes = [m for m in data if m not in capacity]
            for mode in new_modes:
                capacity[mode] = data[mode]
    else:
        capacity = data

    _new_zone_config["capacity"] = capacity

    # sort keys
    _new_zone_config["capacity"] = {
        k: _new_zone_config["capacity"][k] for k in sorted(_new_zone_config["capacity"])
    }

    ZONES_CONFIG[zone_key] = _new_zone_config

    with open(
        CONFIG_DIR.joinpath(f"zones/{zone_key}.yaml"), "w", encoding="utf-8"
    ) as f:
        f.write(yaml.dump(_new_zone_config, default_flow_style=False))
    print(f"Updated {zone_key}.yaml with new capacity data")

