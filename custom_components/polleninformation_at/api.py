"""API client for Polleninformation.at."""

import logging
from typing import TYPE_CHECKING

import aiohttp
from aiohttp import ClientTimeout

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class PollenApi:
    """Class to handle API access for Polleninformation.at."""

    def __init__(self, hass: HomeAssistant, api_key: str) -> None:
        """Initialize the API handler."""
        self.hass = hass
        self._api_key = api_key
        self._raw_response = None

        self._lang = (
            self.hass.config.language
            if self.hass.config.language in ["de", "en"]
            else "en"
        )
        self._latitude = self.hass.config.latitude
        self._longitude = self.hass.config.longitude

        if self._latitude is None or self._longitude is None:
            msg = "Home location is not configured."
            raise ValueError(msg)
        if not self._api_key:
            msg = "API key is not configured."
            raise ValueError(msg)

        endpoint = (
            "https://www.polleninformation.at/api/forecast/public"
            "?country=AT&lang={lang}&latitude={latitude}&longitude={longitude}"
            "&apikey={apikey}"
        )
        self._url = endpoint.format(
            latitude=self._latitude,
            longitude=self._longitude,
            lang=self._lang,
            apikey=self._api_key,
        )
        self._redacted_url = endpoint.format(
            latitude="<REDACTED>",
            longitude="<REDACTED>",
            lang=self._lang,
            apikey="<REDACTED>",
        )

    @property
    def raw_response(self):  # noqa: ANN201
        """Return the latest raw API response."""
        return self._raw_response

    async def async_update(self):  # noqa: ANN201
        """Query data from API and store the raw response."""
        _LOGGER.debug("Fetching data from URL: %s", self._redacted_url)

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(self._url, timeout=ClientTimeout(total=10)) as response,
            ):
                response.raise_for_status()
                data = await response.json()
                self._raw_response = data
                return data
        except aiohttp.ClientError as err:
            error_msg = f"Error fetching data from URL: {self._redacted_url}"
            _LOGGER.exception(error_msg)
            raise RuntimeError(error_msg) from err
