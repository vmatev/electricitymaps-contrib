from datetime import datetime

from requests import Response, Session

from electricitymap.contrib.config import ZoneKey

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
}

GEO_LIMIT_TO_GEO_IDS = {
    "peninsular": 8741,
    "canarias": 8742,
    "baleares": 8743,
    "ceuta": 8744,
    "melilla": 8745,
}

ZONE_KEY_TO_GEO_LIMIT = {
    "ES": "peninsular",
    "ES-IB": "baleares",
    "ES-CN": "canarias",
    "ES-CE": "ceuta",
    "ES-ML": "melilla",
}


def get_capacity_data(zone_key: ZoneKey, target_datetime: datetime):
    geo_limit = ZONE_KEY_TO_GEO_LIMIT[zone_key]
    geo_ids = GEO_LIMIT_TO_GEO_IDS[geo_limit]
    url = f"https://apidatos.ree.es/es/datos/generacion/potencia-instalada?start_date={target_datetime.strftime('%Y-01-01T00:00')}&end_date={target_datetime.strftime('%Y-12-31T23:59')}&time_trunc=year&geo_trunc=electric_system&geo_limit={geo_limit}&geo_ids={geo_ids}"
    r: Response = Session().get(url)
    if r.status_code==200:
        data = r.json()["included"]
        capacity= {}
        for item in data:
            if item["type"] in MODE_MAPPING:
                mode = MODE_MAPPING[item["type"]]
                if mode in capacity:
                    capacity[mode]["value"] += round(item["attributes"]["total"],1)
                else:
                    mode_capacity = {"datetime": target_datetime.strftime("%Y-%m-%d"),"value": round(item["attributes"]["total"],1),"source": "ree.es"}
                    capacity[mode] = mode_capacity
        return capacity
    else:
        raise ValueError(f"{zone_key}: No capacity data available for year {target_datetime.year}")

if __name__=="__main__":
    print(get_capacity_data("ES",datetime(2023,1,1)))