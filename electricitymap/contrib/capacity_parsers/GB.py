from datetime import datetime

from bs4 import BeautifulSoup
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from scripts.utils import convert_datetime_str_to_isoformat, update_zone

MODE_MAPPING = {
    '"Wind Onshore"': "wind",
    '"Wind Offshore"': "wind",
    '"Solar"': "solar",
    '"Other renewable"': "unknown",
    '"Other"': "unknown",
    '"Nuclear"': "nuclear",
    '"Hydro Run-of-river and poundage"': "hydro",
    '"Fossil Hard coal"': "coal",
    '"Fossil Gas"': "gas",
    '"Biomass"': "biomass",
    '"Hydro Pumped Storage"': "hydro storage",
}


def get_capacity_data(target_datetime: datetime) -> dict:
    url = f"https://www.bmreports.com/bmrs/?q=ajax/year/B1410/{target_datetime.year}/"
    r: Response = Session().get(url)

    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "lxml")
        items = soup.find_all("item")
        capacity = {}
        for item in items:
            mode = item.find("powersystemresourcetype").string
            mode = MODE_MAPPING[mode]
            if mode in capacity:
                capacity[mode]["value"] += int(item.find("quantity").string)
            else:
                capacity[mode] = {
                    "datetime": target_datetime.strftime("%Y-%m-%d"),
                    "value": int(item.find("quantity").string),
                    "source": "bmreports.com",
                }
        return capacity
    else:
        raise ValueError(
            f"GB: No capacity data available for year {target_datetime.year}"
        )


def fetch_production_capacity(
    target_datetime: str, zone_key: ZoneKey = "GB"
) -> None:
    target_datetime = convert_datetime_str_to_isoformat(target_datetime)
    zone_capacity = get_capacity_data(target_datetime)
    update_zone(zone_key, zone_capacity)
    print(f"Updated capacity for {zone_key} on {target_datetime.date()}")
