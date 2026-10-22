"""Coordinator for the Polleninformation.at integration."""

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PollenApi
from .const import CONF_API_KEY, DEFAULT_INTERVAL, DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class PollenDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinate data updates for the Polleninformation.at integration."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=DEFAULT_INTERVAL),
        )

        # Initialize the API handler with the API key from the config entry
        self.config_entry = config_entry
        api_key = self.config_entry.options.get(
            CONF_API_KEY,
            self.config_entry.data.get(CONF_API_KEY),
        )
        self._api = PollenApi(self.hass, api_key)

    async def _async_update_data(self) -> dict:
        """Fetch data from the upstream API."""
        try:
            return await self._api.async_update()
        except RuntimeError as err:
            raise UpdateFailed(str(err)) from err
