DOMAIN = "polleninformation_at"
INTEGRATION_NAME = "Polleninformation.at"
INTEGRATION_AUTHOR = "Christian Kadluba"
PLATFORMS = ["sensor"]

POLLEN_TYPES = {
    "alternaria": {"pollen_id": 23, "name": "Pilzsporen (Alternaria)"},
    "ambrosia": {"pollen_id": 6, "name": "Ragweed (Ambrosia)"},
    "cupressaceae": {"pollen_id": 17, "name": "Zypressengewächse (Cupressaceae)"},
    "alnus": {"pollen_id": 1, "name": "Erle (Alnus)"},
    "corylus": {"pollen_id": 3, "name": "Hasel (Corylus)"},
    "fraxinus": {"pollen_id": 4, "name": "Esche (Fraxinus)"},
    "betula": {"pollen_id": 2, "name": "Birke (Betula)"},
    "platanus": {"pollen_id": 16, "name": "Platane (Platanus)"},
    "poaceae": {"pollen_id": 5, "name": "Gräser (Poaceae)"},
    "secale": {"pollen_id": 291, "name": "Roggen (Secale)"},
    "urticaceae": {"pollen_id": 15, "name": "Nessel- und Glaskraut (Urticaceae)"},
    "olea": {"pollen_id": 18, "name": "Ölbaum (Olea)"},
    "artemisia": {"pollen_id": 7, "name": "Beifuß (Artemisia)"}
}

DEFAULT_INTERVAL = 12  # hours, fixed polling interval

CONF_API_KEY = "api_key"

ICON_FLOWER_POLLEN = "mdi:flower-pollen"
