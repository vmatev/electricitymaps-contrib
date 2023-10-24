from electricitymap.contrib.config import ZONES_CONFIG

EMBER_ZONES = [
    "AR",
    "AW",
    "BA",
    "BD",
    "BO",
    "BY",
    "CO",
    "CR",
    "CY",
    "DO",
    "GE",
    "GT",
    "HN",
    "KR",
    "KW",
    "MD",
    "MN",
    "MT",
    "MX",
    "NG",
    "PA",
    "PE",
    "RU",
    "SG",
    "SV",
    "TH",
    "TR",
    "TW",
    "UY",
    "ZA",
]


ENTSOE_ZONES = [
    "AL",
    "AT",
    "BA",
    "BE",
    "BG",
    "CZ",
    "DE",
    "DK-DK1",
    "DK-DK2",
    "EE",
    "ES",
    "FI",
    "FR",
    "GR",
    "HR",
    "HU",
    "IE",
    "LT",
    "LU",
    "LV",
    "ME",
    "MK",
    "NL",
    "NO-NO1",
    "NO-NO2",
    "NO-NO3",
    "NO-NO4",
    "NO-NO5",
    "PL",
    "PT",
    "RO",
    "SI",
    "SK",
    "RS",
    "XK",
    "UA",
]
AGGREGATED_ZONE_MAPPING = {
    "DK": ZONES_CONFIG["DK"]["subZoneNames"],
    "NO": ZONES_CONFIG["NO"]["subZoneNames"],
    "BR": ZONES_CONFIG["BR"]["subZoneNames"],
    "AU": ZONES_CONFIG["AU"]["subZoneNames"],
    "US": ZONES_CONFIG["US"]["subZoneNames"],
}

IRENA_ZONES = ["IL", "IS", "LK", "NI", "GF", "PF"]

EIA_ZONES = [
    zone
    for zone in ZONES_CONFIG
    if zone.startswith("US-") and "parsers" in ZONES_CONFIG[zone]
]

REE_ZONES = [
    zone
    for zone in ZONES_CONFIG
    if zone.startswith("ES") and "parsers" in ZONES_CONFIG[zone]
]


# Get productionCapacity source to zones mapping
CAPACITY_PARSER_SOURCE_TO_ZONES = {}
for zone_id, zone_config in ZONES_CONFIG.items():
    if zone_config.get("parsers", {}).get("productionCapacity") is not None:
        source = zone_config.get("parsers", {}).get("productionCapacity").split(".")[0]
        if source in CAPACITY_PARSER_SOURCE_TO_ZONES:
            CAPACITY_PARSER_SOURCE_TO_ZONES[source].append(zone_id)
        else:
            CAPACITY_PARSER_SOURCE_TO_ZONES[source] = [zone_id]
