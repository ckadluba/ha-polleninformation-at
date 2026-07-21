DOMAIN = "polleninformation_at"
INTEGRATION_NAME = "Polleninformation.at"
INTEGRATION_DEVICE_MANUFACTURER = (
    "Christian Kadluba (data provided by www.polleninformation.at)"
)
PLATFORMS = ["sensor"]

POLLEN_TYPES = {
    "poaceae": {"pollen_id": 5, "name": "Gräser (Poaceae)"},
    "urticaceae": {"pollen_id": 15, "name": "Nessel- und Glaskraut (Urticaceae)"},
    "alternaria": {"pollen_id": 23, "name": "Pilzsporen (Alternaria)"},
    "rumex": {"pollen_id": 356, "name": "Ampfer (Rumex)"},
    "castanea": {"pollen_id": 326, "name": "Edelkastanie (Castanea)"},
    "plantago": {"pollen_id": 320, "name": "Wegerichgewächse (Plantago)"},
    "artemisia": {"pollen_id": 7, "name": "Beifuß (Artemisia)"},
    "betula": {"pollen_id": 2, "name": "Birke (Betula)"},
    "alnus": {"pollen_id": 1, "name": "Erle (Alnus)"},
    "fraxinus": {"pollen_id": 4, "name": "Esche (Fraxinus)"},
    "ailanthus_altissima": {
        "pollen_id": 1107,
        "name": "Götterbaum (Ailanthus altissima)",
    },
    "corylus": {"pollen_id": 3, "name": "Hasel (Corylus)"},
    "tilia": {"pollen_id": 355, "name": "Linde (Tilia)"},
    "olea": {"pollen_id": 18, "name": "Ölbaum (Olea)"},
    "platanus": {"pollen_id": 16, "name": "Platane (Platanus)"},
    "ambrosia": {"pollen_id": 6, "name": "Ragweed (Ambrosia)"},
    "secale": {"pollen_id": 291, "name": "Roggen (Secale)"},
    "cupressaceae": {"pollen_id": 17, "name": "Zypressengewächse (Cupressaceae)"},
}

DEFAULT_INTERVAL = 6  # hours, fixed polling interval

CONF_API_KEY = "api_key"

ICON_FLOWER_POLLEN = "mdi:flower-pollen"
