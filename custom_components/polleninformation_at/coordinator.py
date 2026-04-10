import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PollenApi
from .const import CONF_API_KEY, DEFAULT_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PollenDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinate data updates for the Polleninformation.at integration."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.config_entry = config_entry
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=DEFAULT_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from the upstream API."""
        api_key = self.config_entry.options.get(
            CONF_API_KEY,
            self.config_entry.data.get(CONF_API_KEY),
        )
        api = PollenApi(self.hass, api_key)

        try:
            await api.async_update()
        except Exception as err:
            raise UpdateFailed(f"Error fetching pollen data: {err}") from err

        return api.raw_response or {}