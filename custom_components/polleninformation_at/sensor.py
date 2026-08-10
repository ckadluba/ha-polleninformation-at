"""
Sensors for the Polleninformation.at Home Assistant integration.

This module defines the PollenSensor entity which exposes pollen
contamination levels from the integration's coordinator data.
"""

import logging
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.polleninformation_at.const import (
    DOMAIN,
    ICON_FLOWER_POLLEN,
    INTEGRATION_DEVICE_MANUFACTURER,
    INTEGRATION_NAME,
    POLLEN_TYPES,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Polleninformation.at sensors for a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    sensors = [
        PollenSensor(coordinator, pollen_type, item["pollen_id"])
        for pollen_type, item in POLLEN_TYPES.items()
    ]

    _LOGGER.debug("Setting up PollenSensor entities: %s", sensors)

    async_add_entities(sensors)


class PollenSensor(CoordinatorEntity, SensorEntity):
    """
    Polleninformation.at sensor backed by the integration coordinator.

    param coordinator: The data update coordinator for this integration.
    param pollen_type: The type of pollen (e.g., "poaceae", "betula").
    param pollen_id: The numeric ID for the pollen type according to the API response.
    """

    def __init__(self, coordinator, pollen_type, pollen_id) -> None:  # noqa: ANN001
        """Initialize the sensor entity."""
        super().__init__(coordinator)

        self._pollen_id = pollen_id
        self._pollen_type = pollen_type

        canonical_entity_name = f"{DOMAIN}_{pollen_type}"
        self._attr_has_entity_name = True
        self._attr_unique_id = canonical_entity_name
        self._attr_icon = ICON_FLOWER_POLLEN
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "level"

        # Ensure canonical entity_id independent of friendly name
        self.entity_id = f"sensor.{canonical_entity_name}"

        self.entity_description = SensorEntityDescription(
            key=canonical_entity_name,
            translation_key=canonical_entity_name,
            icon=ICON_FLOWER_POLLEN,
            native_unit_of_measurement="level",
            state_class=SensorStateClass.MEASUREMENT,
        )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "polleninformation_at")},
            name=INTEGRATION_NAME,
            manufacturer=INTEGRATION_DEVICE_MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE,
        )

        _LOGGER.debug(
            (
                "PollenSensor initialized with _attr_unique_id: %s, "
                "_pollen_id: %s, _pollen_type: %s"
            ),
            self._attr_unique_id,
            self._pollen_id,
            self._pollen_type,
        )

    @property
    def native_value(self) -> int | None:
        """Return the current contamination level."""
        data = self._get_contamination_entry()
        return data.get("contamination_1") if data else None

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional sensor attributes."""
        data = self._get_contamination_entry()
        if not data:
            return {}

        return {
            "poll_title": data.get("poll_title"),
        }

    def _get_contamination_entry(self) -> dict | None:
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
