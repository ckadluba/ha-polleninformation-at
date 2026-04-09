import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.polleninformation_at.const import (
    DOMAIN,
    INTEGRATION_NAME,
    INTEGRATION_AUTHOR,
    ICON_FLOWER_POLLEN,
)

_LOGGER = logging.getLogger(__name__)


class PollenSensor(CoordinatorEntity, SensorEntity):
    """Polleninformation.at Sensor using DataUpdateCoordinator."""

    def __init__(self, coordinator, pollen_type, pollen_id, pollen_name):
        super().__init__(coordinator)

        self._pollen_id = pollen_id
        self._pollen_type = pollen_type

        # Grouping all sensors under a single device in Home Assistant
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "polleninformation_at")},
            name=INTEGRATION_NAME,
            manufacturer=INTEGRATION_AUTHOR,
            entry_type=DeviceEntryType.SERVICE
        )

        self._attr_has_entity_name = True
        self._attr_name = pollen_name

        self._attr_unique_id = f"{DOMAIN}_{pollen_type}"

        self._attr_icon = ICON_FLOWER_POLLEN
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "level"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        data = self._get_contamination_entry()
        return data.get("contamination_1") if data else None

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        data = self._get_contamination_entry()
        if not data:
            return {}
        return {
            "poll_title": data.get("poll_title"),
        }

    def _get_contamination_entry(self):
        """Extract the contamination entry for this pollen type."""
        response = self.coordinator.data
        if not response:
            return None

        contamination = response.get("contamination")

        if isinstance(contamination, list):
            for entry in contamination:
                if str(entry.get("poll_id")) == str(self._pollen_id):
                    return entry

        return None