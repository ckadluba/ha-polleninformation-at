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
POLLEN_JSON_ELEMENT_NAME = "contamination"
POLLEN_CURRENT_JSON_SUBELEMENT_NAME = "contamination_1"
POLLEN_FORECAST1_JSON_SUBELEMENT_NAME = "contamination_2"
POLLEN_FORECAST2_JSON_SUBELEMENT_NAME = "contamination_3"
POLLEN_FORECAST3_JSON_SUBELEMENT_NAME = "contamination_4"

ALLERGYRISK_TYPE = "allergyrisk"
ALLERGYRISK_JSON_ELEMENT_NAME = "allergyrisk"
ALLERGYRISK_CURRENT_JSON_SUBELEMENT_NAME = "allergyrisk_1"
ALLERGYRISK_FORECAST1_JSON_SUBELEMENT_NAME = "allergyrisk_2"
ALLERGYRISK_FORECAST2_JSON_SUBELEMENT_NAME = "allergyrisk_3"
ALLERGYRISK_FORECAST3_JSON_SUBELEMENT_NAME = "allergyrisk_4"

ALLERGYRISK_HOURLY_TYPE = "allergyrisk_hourly"
ALLERGYRISK_HOURLY_JSON_ELEMENT_NAME = "allergyrisk_hourly"
ALLERGYRISK_HOURLY_CURRENT_JSON_SUBELEMENT_NAME = "allergyrisk_hourly_1"
ALLERGYRISK_HOURLY_FORECAST1_JSON_SUBELEMENT_NAME = "allergyrisk_hourly_2"
ALLERGYRISK_HOURLY_FORECAST2_JSON_SUBELEMENT_NAME = "allergyrisk_hourly_3"
ALLERGYRISK_HOURLY_FORECAST3_JSON_SUBELEMENT_NAME = "allergyrisk_hourly_4"

FORECAST1_SUFFIX = "forecast1"
FORECAST2_SUFFIX = "forecast2"
FORECAST3_SUFFIX = "forecast3"

DEFAULT_INTERVAL = 6  # hours, fixed polling interval

CONF_API_KEY = "api_key"

ICON_FLOWER_POLLEN = "mdi:flower-pollen"
ICON_MEDICAL_BAG = "mdi:medical-bag"
