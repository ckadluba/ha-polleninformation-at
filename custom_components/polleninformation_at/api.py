import aiohttp
import logging


_LOGGER = logging.getLogger(__name__)


class PollenApi:
    """Class to handle API access for Polleninformation.at."""

    def __init__(self, hass, api_key):
        """Initialize the API handler."""
        self.hass = hass
        self._api_key = api_key
        self._raw_response = None

    async def async_update(self):
        """Query data from API and store the raw response."""
        latitude = self.hass.config.latitude
        longitude = self.hass.config.longitude

        if latitude is None or longitude is None:
            raise ValueError("Home location is not configured.")
        if not self._api_key:
            raise ValueError("API key is not configured.")

        url = (
            "https://www.polleninformation.at/api/forecast/public"
            f"?country=AT&lang=de&latitude={latitude}&longitude={longitude}"
            f"&apikey={self._api_key}"
        )
        _LOGGER.debug(f"Fetching data from URL: {url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()
                    self._raw_response = data
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error fetching pollen data: {e}")
