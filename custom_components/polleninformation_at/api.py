import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class PollenAPI:
    """Class to handle API access for Polleninformation.at."""

    def __init__(self, hass, poll_id):
        """Initialize the API handler."""
        self.hass = hass
        self._poll_id = poll_id
        self._state = None
        self._poll_title = None

    async def async_update(self):
        """Query data from API."""
        latitude = self.hass.config.latitude
        longitude = self.hass.config.longitude

        if latitude is None or longitude is None:
            raise ValueError("Home location is not configured.")

        url = f"https://www.polleninformation.at/index.php?eID=appinterface&pure_json=1&lang_code=de&lang_id=0&action=getFullContaminationData&type=gps&value[latitude]={latitude}&value[longitude]={longitude}&show_polls={self._poll_id}&country_id=1&personal_contamination=false&sensitivity=0&country=AT&sessionid="
        _LOGGER.debug(f"Fetching data from URL: {url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()

                    if data.get("success") == 1:
                        contamination_data = data.get("result", {}).get("contamination", [{}])
                        if contamination_data:
                            contamination_data = contamination_data[0]
                            self._state = contamination_data.get("contamination_1", 0)
                            self._poll_title = contamination_data.get("poll_title", "Unknown")
                            _LOGGER.debug(f"Updated PollenAPI state: {self._state}, poll_title: {self._poll_title}")
                        else:
                            _LOGGER.debug("No contamination data found in the response")
                    else:
                        _LOGGER.debug(f"No data available: {data.get('message')}")
                        self._state = 0
                        self._poll_title = "No data"

        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error fetching pollen data: {e}")
            self._state = "Error"
            self._poll_title = "Error"

    @property
    def state(self):
        return self._state

    @property
    def poll_title(self):
        return self._poll_title
