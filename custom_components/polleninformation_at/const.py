"""Constants for the Polleninformation.at integration."""

DOMAIN = "polleninformation_at"
INTEGRATION_NAME = "Polleninformation.at"
INTEGRATION_DEVICE_MANUFACTURER = (
    "Christian Kadluba (data provided by www.polleninformation.at)"
)
PLATFORMS = ["sensor"]

POLLEN_TYPES = {
    "poaceae": {"pollen_id": 5},
    "urticaceae": {"pollen_id": 15},
    "alternaria": {"pollen_id": 23},
    "rumex": {"pollen_id": 356},
    "castanea": {"pollen_id": 326},
    "plantago": {"pollen_id": 320},
    "artemisia": {"pollen_id": 7},
    "betula": {"pollen_id": 2},
    "alnus": {"pollen_id": 1},
    "fraxinus": {"pollen_id": 4},
    "ailanthus_altissima": {"pollen_id": 1107},
    "corylus": {"pollen_id": 3},
    "tilia": {"pollen_id": 355},
    "olea": {"pollen_id": 18},
    "platanus": {"pollen_id": 16},
    "ambrosia": {"pollen_id": 6},
    "secale": {"pollen_id": 291},
    "cupressaceae": {"pollen_id": 17},
}
POLLEN_SERIES_NAME = "contamination"

ALLERGYRISK_TYPE = "allergyrisk"
ALLERGYRISK_SERIES_NAME = "allergyrisk"

DEFAULT_INTERVAL = 6  # hours, fixed polling interval

CONF_API_KEY = "api_key"

ICON_FLOWER_POLLEN = "mdi:flower-pollen"
