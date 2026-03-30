import logging
import voluptuous as vol
from datetime import timedelta

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA, 
    SensorEntity, 
    SensorStateClass,
    ENTITY_ID_FORMAT
)
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    INTEGRATION_NAME,
    DEFAULT_INTERVAL,
    CONF_API_KEY,
    CONF_INTERVAL,
    CONF_LOCATION,
    ICON_FLOWER_POLLEN,
)
from .api import PollenApi

POLLEN_TYPES = {
    "alternaria": {"poll_id": 23, "name": "Pilzsporen (Alternaria)"}#,
    # "ambrosia": {"poll_id": 6, "name": "Ragweed (Ambrosia)"},
    # "cupressaceae": {"poll_id": 17, "name": "Zypressengewächse (Cupressaceae)"},
    # "alnus": {"poll_id": 1, "name": "Erle (Alnus)"},
    # "corylus": {"poll_id": 3, "name": "Hasel (Corylus)"},
    # "fraxinus": {"poll_id": 4, "name": "Esche (Fraxinus)"},
    # "betula": {"poll_id": 2, "name": "Birke (Betula)"},
    # "platanus": {"poll_id": 16, "name": "Platane (Platanus)"},
    # "poaceae": {"poll_id": 5, "name": "Gräser (Poaceae)"},
    # "secale": {"poll_id": 291, "name": "Roggen (Secale)"},
    # "urticaceae": {"poll_id": 15, "name": "Nessel- und Glaskraut (Urticaceae)"},
    # "olea": {"poll_id": 18, "name": "Ölbaum (Olea)"},
    # "artemisia": {"poll_id": 7, "name": "Beifuß (Artemisia)"}
}

SCAN_INTERVAL = timedelta(minutes=DEFAULT_INTERVAL)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_LOCATION): cv.string,
    vol.Optional(CONF_NAME, default=INTEGRATION_NAME): cv.string
})

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setzt die Sensor-Integration über die UI (Config Flow) auf."""
    
    name = config_entry.data.get(CONF_NAME, INTEGRATION_NAME)
    location = config_entry.data.get(CONF_LOCATION)
    api_key = config_entry.options.get(CONF_API_KEY, config_entry.data.get(CONF_API_KEY))

    _LOGGER.info(f"🔄 Setup entry gestartet: name={name}, location={location}")

    sensors = create_sensors(hass, name, location, api_key)
    async_add_entities(sensors, update_before_add=True)

    _LOGGER.info(f"✅ {len(sensors)} Sensor(en) hinzugefügt.")

    # Set up config change listener
    config_entry.async_on_unload(
        config_entry.add_update_listener(async_update_options)
    )

def create_sensors(hass, name, location, api_key):
    """Erstellt eine Liste von PollenSensoren und prüft, ob sie bereits existieren."""
    sensors = []

    for pollen_type, item in POLLEN_TYPES.items():
        sensors.append(PollenSensor(hass, item["poll_id"], pollen_type, item["name"], api_key))

    return sensors

async def async_update_options(hass, config_entry):
    """React to config updates"""
    _LOGGER.info("🔄 Config entry options geändert, Integration wird neu geladen...")
    await hass.config_entries.async_reload(config_entry.entry_id)

class PollenSensor(SensorEntity):
    """Polleninformation.at Sensor."""

    def __init__(self, hass, poll_id, pollen_type, pollen_name, api_key):
        """Initialize the sensor."""
        
        self._api = PollenApi(hass, poll_id, api_key)
        self._name = f"{DOMAIN}_{pollen_type}"
        self._sensor_name = ENTITY_ID_FORMAT.format(self._name)
        self._available = True

        self._attr_name = pollen_name
        self._attr_unique_id = f"{DOMAIN}_{pollen_type}"
        self._attr_entity_id = self._sensor_name
        self._available = True        
        self._attr_native_value: int | float | None = 0
        self._attr_icon = ICON_FLOWER_POLLEN
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "Level"

        _LOGGER.debug(f"✅ Initialisiert PollenSensor: name={self._sensor_name}")

    # @property
    # def name(self) -> str:
    #     return self._name

    @property
    def entity_id(self) -> str:
        return self._attr_entity_id
    @property.setter
    def entity_id(self, new_entity_id) -> str:
        return self._attr_entity_id = new_entity_id

    # @property
    # def unique_id(self) -> str:
    #     """Return a unique ID for the sensor."""
    #     return self._name
    
    @property
    def state(self) -> int | None:
        return self._state

    @property
    def extra_state_attributes(self) -> dict:
        return {"poll_title": self._poll_title}

    # @property
    # def available(self) -> bool:
    #     return self._available

    async def async_update(self, _=None):
        """Query data from API."""
        await self._api.async_update()

        self._state = self._api.state
        self._poll_title = self._api.poll_title

        self.async_write_ha_state()
        
        _LOGGER.debug(f"🔄 Update PollenSensor: {self._sensor_name}")
