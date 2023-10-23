from datetime import datetime

from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from scripts.utils import convert_datetime_str_to_isoformat, update_zone

"""Disclaimer: Capacity for the Spanish isles is only avilable per archipelago."""

MODE_MAPPING = {
    "Hidráulica": "hydro",
    "Turbinación bombeo": "hydro storage",
    "Nuclear": "nuclear",
    "Carbón": "coal",
    "Fuel + Gas": "gas",
    "Ciclo combinado": "gas",
    "Eólica": "wind",
    "Solar fotovoltaica": "solar",
    "Solar térmica": "solar",
    "Otras renovables": "unknown",
    "Cogeneración": "gas",
    "Residuos no renovables": "unknown",
    "Residuos renovables": "biomass",
    "Motores diésel": "oil",
    "Turbina de gas": "gas",
    "Turbina de vapor": "gas",
}

GEO_LIMIT_TO_GEO_IDS = {
    "peninsular": 8741,
    "canarias": 19,
    "baleares": 18,
    "ceuta": 12,
    "melilla": 8746,
}

ZONE_KEY_TO_GEO_LIMIT = {
    "ES": "peninsular",
    "ES-IB-FO": "baleares",
    "ES-IB-IZ": "baleares",
    "ES-IB-MA": "baleares",
    "ES-IB-ME": "baleares",
    "ES-CN-FVLZ": "canarias",
    "ES-CN-GC": "canarias",
    "ES-CN-HI": "canarias",
    "ES-CN-IG": "canarias",
    "ES-CN-LP": "canarias",
    "ES-CN-TE": "canarias",
    "ES-CE": "ceuta",
    "ES-ML": "melilla",
}


def get_capacity_data(zone_key: ZoneKey, target_datetime: datetime):
    geo_limit = ZONE_KEY_TO_GEO_LIMIT[zone_key]
    geo_ids = GEO_LIMIT_TO_GEO_IDS[geo_limit]
    url = f"https://apidatos.ree.es/es/datos/generacion/potencia-instalada?start_date={target_datetime.strftime('%Y-01-01T00:00')}&end_date={target_datetime.strftime('%Y-12-31T23:59')}&time_trunc=year&geo_trunc=electric_system&geo_limit={geo_limit}&geo_ids={geo_ids}&tecno_select=all"
    r: Response = Session().get(url)
    if r.status_code == 200:
        data = r.json()["included"]
        capacity = {}
        for item in data:
            if item["type"] in MODE_MAPPING:
                mode = MODE_MAPPING[item["type"]]
                if mode in capacity:
                    capacity[mode]["value"] += round(item["attributes"]["total"], 0)
                else:
                    mode_capacity = {
                        "datetime": target_datetime.strftime("%Y-%m-%d"),
                        "value": round(item["attributes"]["total"], 0),
                        "source": "ree.es",
                    }
                    capacity[mode] = mode_capacity
        return capacity
    else:
        raise ValueError(
            f"{zone_key}: No capacity data available for year {target_datetime.year}"
        )


def fetch_production_capacity(
    zone_key: ZoneKey, target_datetime: str
) -> None:
    target_datetime = convert_datetime_str_to_isoformat(target_datetime)
    zone_capacity = get_capacity_data(zone_key, target_datetime)
    update_zone(zone_key, zone_capacity)
    print(f"Updated capacity for {zone_key} on {target_datetime.date()}")


def fetch_production_capacity_for_all_zones(
    target_datetime: str, zone_key: ZoneKey = "REE"
) -> None:
    target_datetime = convert_datetime_str_to_isoformat(target_datetime)
    for zone in ZONE_KEY_TO_GEO_LIMIT:
        zone_capacity = get_capacity_data(zone, target_datetime)
        print(zone_capacity)
        update_zone(zone, zone_capacity)
        print(f"Updated capacity for {zone} on {target_datetime.date()}")


if __name__ == "__main__":
    fetch_production_capacity_for_all_zones("2023-01-01")
