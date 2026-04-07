import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    ENTITY_ID_FORMAT
)
from custom_components.polleninformation_at.const import (
    DOMAIN,
    ICON_FLOWER_POLLEN
)


_LOGGER = logging.getLogger(__name__)


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
        # Extract the contamination entry for this pollen type from the shared response
        data = self._get_contamination_entry()
        return data.get("contamination_1") if data else None

    @property
    def extra_state_attributes(self) -> dict:
        data = self._get_contamination_entry()
        return {"poll_title": data.get("poll_title") if data else None}

    @property
    def available(self) -> bool:
        return self.state is not None

    async def async_update(self):
        await self.coordinator.async_request_refresh()

    def _get_contamination_entry(self):
        response = self.coordinator.data
        if not response:
            return None
        contamination = response.get("contamination")
        if isinstance(contamination, list):
            for entry in contamination:
                if entry.get("poll_id") == self._pollen_type or str(entry.get("poll_id")) == str(self._pollen_type):
                    return entry
        # fallback for legacy/other formats
        if response.get("success") == 1:
            legacy = response.get("result", {}).get("contamination", [])
            if legacy:
                for entry in legacy:
                    if entry.get("poll_id") == self._pollen_type or str(entry.get("poll_id")) == str(self._pollen_type):
                        return entry
        return None
