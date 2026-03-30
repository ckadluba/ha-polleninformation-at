import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)


class PollenApi:
    """Class to handle API access for Polleninformation.at."""

    def __init__(self, hass, poll_id, api_key):
        """Initialize the API handler."""
        self.hass = hass
        self._poll_id = poll_id
        self._api_key = api_key
        self._state = None
        self._poll_title = None

    def _extract_contamination_entry(self, data):
        contamination_data = data.get("contamination")
        if isinstance(contamination_data, list):
            matching_entry = next(
                (
                    entry
                    for entry in contamination_data
                    if entry.get("poll_id") == self._poll_id
                ),
                None,
            )
            if matching_entry is not None:
                return matching_entry
            if contamination_data:
                return contamination_data[0]

        if data.get("success") == 1:
            legacy_contamination = data.get("result", {}).get("contamination", [])
            if legacy_contamination:
                return legacy_contamination[0]

        return None

    async def async_update(self):
        """Query data from API."""
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
                    contamination_entry = self._extract_contamination_entry(data)
                    if contamination_entry is None:
                        _LOGGER.debug("No contamination data found in the response")
                        return

                    self._state = contamination_entry.get("contamination_1", 0)
                    self._poll_title = contamination_entry.get("poll_title", "Unknown")
                    _LOGGER.debug(
                        f"Updated PollenApi state: {self._state}, poll_title: {self._poll_title}"
                    )

        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error fetching pollen data: {e}")

    @property
    def state(self):
        return self._state

    @property
    def poll_title(self):
        return self._poll_title
