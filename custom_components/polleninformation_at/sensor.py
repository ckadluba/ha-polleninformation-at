
import logging
import voluptuous as vol
from datetime import timedelta

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.polleninformation_at.const import (
    INTEGRATION_NAME,
    CONF_API_KEY,
    CONF_LOCATION,
    DEFAULT_INTERVAL,
    POLLEN_TYPES
)

from custom_components.polleninformation_at.api import PollenApi
from custom_components.polleninformation_at.sensor_entity import PollenSensor

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
        try:
            api = PollenApi(hass, api_key)
            await api.async_update()
            # Store the full API response in the coordinator
            return getattr(api, '_raw_response', {})
        except Exception as err:
            _LOGGER.error(f"Error updating pollen data: {err}")
            return {}

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Polleninformation.at Data",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    sensors = [
        PollenSensor(coordinator, pollen_type, item["poll_id"], item["name"])
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



