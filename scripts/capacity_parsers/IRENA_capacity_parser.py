import argparse
from datetime import datetime

import pandas as pd
import pycountry
import requests
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from scripts.capacity_parsers.constants import EMBER_ZONES
from scripts.utils import (
    ROOT_PATH,
    convert_datetime_str_to_isoformat,
    run_shell_command,
    update_zone,
)


def fetch_capacity_from_csv(path:str, zone:ZoneKey, target_datetime:datetime):
    df = pd.read_excel(path, skipfooter=26)
    df = df.rename(columns={'Installed electricity capacity (MW) by Country/area, Technology, Grid connection and Year':'zone_key',
       'Unnamed: 1':'mode', 'Unnamed: 2':'category', 'Unnamed: 3':'year', 'Unnamed: 4':'value'})
    df["zone_key"] = df["zone_key"].ffill()
    df["mode"] = df["mode"].ffill()
    df=df.dropna(axis=0, how='all')