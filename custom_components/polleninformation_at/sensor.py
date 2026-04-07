
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
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    INTEGRATION_NAME,
    CONF_API_KEY,
    CONF_LOCATION,
    ICON_FLOWER_POLLEN,
    DEFAULT_INTERVAL,
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

SCAN_INTERVAL = timedelta(hours=DEFAULT_INTERVAL)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_LOCATION): cv.string,
    vol.Optional(CONF_NAME, default=INTEGRATION_NAME): cv.string
})

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Polleninformation.at sensors using DataUpdateCoordinator."""
    name = config_entry.data.get(CONF_NAME, INTEGRATION_NAME)
    location = config_entry.data.get(CONF_LOCATION)
    api_key = config_entry.options.get(CONF_API_KEY, config_entry.data.get(CONF_API_KEY))

    _LOGGER.info(f"🔄 Setup entry started: name={name}, location={location}")

    async def async_update_data():
        data = {}
        for pollen_type, item in POLLEN_TYPES.items():
            api = PollenApi(hass, item["poll_id"], api_key)
            try:
                await api.async_update()
                data[pollen_type] = {
                    "state": api.state,
                    "poll_title": api.poll_title,
                }
            except Exception as err:
                _LOGGER.error(f"Error updating pollen data for {pollen_type}: {err}")
                data[pollen_type] = {
                    "state": None,
                    "poll_title": None,
                }
        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Polleninformation.at Data",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    sensors = [
        PollenSensor(coordinator, pollen_type, item["name"])
        for pollen_type, item in POLLEN_TYPES.items()
    ]
    async_add_entities(sensors, update_before_add=True)

    _LOGGER.info(f"✅ {len(sensors)} sensor(s) added.")

    config_entry.async_on_unload(
        config_entry.add_update_listener(async_update_options)
    )



async def async_update_options(hass, config_entry):
    """React to config updates"""
    _LOGGER.info("🔄 Config entry options geändert, Integration wird neu geladen...")
    await hass.config_entries.async_reload(config_entry.entry_id)


class PollenSensor(SensorEntity):
    """Polleninformation.at Sensor using DataUpdateCoordinator."""

    def __init__(self, coordinator, pollen_type, pollen_name):
        self.coordinator = coordinator
        self._pollen_type = pollen_type
        self._attr_name = pollen_name
        self._attr_unique_id = f"{DOMAIN}_{pollen_type}"
        self._attr_entity_id = ENTITY_ID_FORMAT.format(f"{DOMAIN}_{pollen_type}")
        self._attr_icon = ICON_FLOWER_POLLEN
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "Level"

    @property
    def state(self) -> int | None:
        data = self.coordinator.data.get(self._pollen_type, {})
        return data.get("state")

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data.get(self._pollen_type, {})
        return {"poll_title": data.get("poll_title")}

    @property
    def available(self) -> bool:
        return self.state is not None

    async def async_update(self):
        await self.coordinator.async_request_refresh()
