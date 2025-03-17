import logging
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity, SensorStateClass
from homeassistant.const import CONF_NAME, STATE_UNKNOWN
import homeassistant.helpers.config_validation as cv
from .const import DOMAIN, CONF_INTERVAL, ICON_FLOWER_POLLEN
from .api import PollenAPI

_LOGGER = logging.getLogger(__name__)

CONF_LOCATION = "location"

DEFAULT_NAME = "Polleninformation.at"
DEFAULT_INTERVAL = 21600  # 6 Hours

POLLEN_TYPES = {
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

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_LOCATION): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_INTERVAL, default=DEFAULT_INTERVAL): cv.positive_int,
})

async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup sensor platform for Polleninformation.at."""
    location = config[CONF_LOCATION]
    name = config[CONF_NAME]
    interval = config[CONF_INTERVAL]

    sensors = []
    for pollen_type, poll_id in POLLEN_TYPES.items():
        sensors.append(PollenSensor(hass, name, location, interval, poll_id, f"{name}_{pollen_type}"))

    add_entities(sensors, True)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Polleninformation.at sensor from a config entry."""
    _LOGGER.debug("Setting up Polleninformation.at sensor from config entry")
    interval = config_entry.data[CONF_INTERVAL]

    sensors = []
    for pollen_type, poll_id in POLLEN_TYPES.items():
        sensors.append(PollenSensor(hass, "Polleninformation.at", "home", interval, poll_id, f"polleninformation_at_{pollen_type}"))

    async_add_entities(sensors, True)

class PollenSensor(SensorEntity):
    """Polleninformation.at Sensor."""

    def __init__(self, hass, name, location, interval, poll_id, sensor_name):
        """Initialize the sensor."""
        self.hass = hass
        self._name = name
        self._location = location
        self._state = STATE_UNKNOWN
        self._poll_title = None
        self._interval = interval
        self._poll_id = poll_id
        self._sensor_name = sensor_name
        self.api = PollenAPI(hass, poll_id)
        self._attr_icon = ICON_FLOWER_POLLEN
        self._attr_state_class = SensorStateClass.MEASUREMENT
        _LOGGER.debug(f"Initialized PollenSensor: {name}, {location}, {interval}, {poll_id}")

    async def async_update(self):
        """Query data from API."""
        await self.api.async_update()
        self._state = self.api.state
        self._poll_title = self.api.poll_title

    @property
    def name(self):
        return self._sensor_name

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return f"{self._name}_{self._sensor_name}"

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
