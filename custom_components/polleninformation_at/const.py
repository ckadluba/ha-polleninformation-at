DOMAIN = "polleninformation_at"
INTEGRATION_NAME = "Polleninformation.at"

POLLEN_TYPES = {
    "alternaria": {"poll_id": 23, "name": "Pilzsporen (Alternaria)"},
    "ambrosia": {"poll_id": 6, "name": "Ragweed (Ambrosia)"},
    "cupressaceae": {"poll_id": 17, "name": "Zypressengewächse (Cupressaceae)"},
    "alnus": {"poll_id": 1, "name": "Erle (Alnus)"},
    "corylus": {"poll_id": 3, "name": "Hasel (Corylus)"},
    "fraxinus": {"poll_id": 4, "name": "Esche (Fraxinus)"},
    "betula": {"poll_id": 2, "name": "Birke (Betula)"},
    "platanus": {"poll_id": 16, "name": "Platane (Platanus)"},
    "poaceae": {"poll_id": 5, "name": "Gräser (Poaceae)"},
    "secale": {"poll_id": 291, "name": "Roggen (Secale)"},
    "urticaceae": {"poll_id": 15, "name": "Nessel- und Glaskraut (Urticaceae)"},
    "olea": {"poll_id": 18, "name": "Ölbaum (Olea)"},
    "artemisia": {"poll_id": 7, "name": "Beifuß (Artemisia)"}
}

DEFAULT_INTERVAL = 12  # hours, fixed polling interval

CONF_LOCATION = "location"
CONF_API_KEY = "api_key"

ICON_FLOWER_POLLEN = "mdi:flower-pollen"
