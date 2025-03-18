import logging
import voluptuous as vol
from datetime import timedelta

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity, SensorStateClass
from homeassistant.const import CONF_NAME, STATE_UNKNOWN
import homeassistant.helpers.config_validation as cv
from .const import DOMAIN, INTEGRATION_NAME, DEFAULT_INTERVAL, CONF_INTERVAL, CONF_LOCATION, ICON_FLOWER_POLLEN
from .api import PollenAPI

POLLEN_TYPES={
    "alternaria": 23,
    "ambrosia": 6,
    "cupressaceae": 17,
    "alnus": 1,
    "corylus": 3,
    "fraxinus": 4,
    "betula": 2,
    "platanus": 16,
    "poaceae": 5,
    "secale": 291,
    "urticaceae": 15,
    "olea": 18,
    "artemisia": 7
}

SCAN_INTERVAL=timedelta(minutes=DEFAULT_INTERVAL)

PLATFORM_SCHEMA=PLATFORM_SCHEMA.extend({
    vol.Required(CONF_LOCATION): cv.string,
    vol.Optional(CONF_NAME, default=INTEGRATION_NAME): cv.string
})

_LOGGER=logging.getLogger(__name__)

async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up platform."""

    name=config[CONF_NAME]
    location=config[CONF_LOCATION]

    _LOGGER.debug(f"Setup platform: name={name}, location={location}")

    sensors=[]
    for pollen_type, poll_id in POLLEN_TYPES.items():
        sensors.append(PollenSensor(hass, name, location, poll_id, f"{name}_{pollen_type}"))

    add_entities(sensors, True)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensor."""
    
    name=config_entry.data.get(CONF_NAME, INTEGRATION_NAME)
    location=config_entry.data.get(CONF_LOCATION)

    _LOGGER.debug(f"Setup entry: name={name}, location={location}")

    sensors=[]
    for pollen_type, poll_id in POLLEN_TYPES.items():
        sensors.append(PollenSensor(hass, name, location, poll_id, f"{DOMAIN}_{pollen_type}"))

    async_add_entities(sensors, True)
    
    # Set up config change listener
    config_entry.async_on_unload(
        config_entry.add_update_listener(async_update_options)
    )

async def async_update_options(hass, config_entry):
    """React to config updates"""
    _LOGGER.info("Config entry options changed, reloading integration...")
    await hass.config_entries.async_reload(config_entry.entry_id)

class PollenSensor(SensorEntity):
    """Polleninformation.at Sensor."""

    def __init__(self, hass, name, location, poll_id, sensor_name):
        """Initialize the sensor."""
        self.hass=hass
        self._name=name
        self._location=location
        self._state=STATE_UNKNOWN
        self._poll_title=None
        self._poll_id=poll_id
        self._sensor_name=sensor_name
        self.api=PollenAPI(hass, poll_id)
        self._attr_icon=ICON_FLOWER_POLLEN
        self._attr_state_class=SensorStateClass.MEASUREMENT
        self.entity_id=f"sensor.{self._sensor_name}"
        _LOGGER.debug(f"Initialized PollenSensor: name={self._sensor_name}, poll_id={self._poll_id}")

    async def async_update(self, _=None):
        """Query data from API."""
        await self.api.async_update()
        self._state=self.api.state
        self._poll_title=self.api.poll_title
        self.async_write_ha_state()
        _LOGGER.debug(f"Update PollenSensor: name={self._sensor_name}, state={self._state}")

    @property
    def name(self):
        return self._sensor_name

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return self._sensor_name

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        return SensorStateClass.MEASUREMENT

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return {
            "poll_title": self._poll_title
        }

    @property
    def should_poll(self):
        return True
