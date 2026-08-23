"""
Sensors for the Polleninformation.at Home Assistant integration.

This module defines the PollenSensor entity which exposes pollen
contamination levels from the integration's coordinator data.
"""

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from custom_components.polleninformation_at.const import (
    ALLERGYRISK_HOURLY_JSON_ELEMENT_NAME,
    ALLERGYRISK_HOURLY_TYPE,
    ALLERGYRISK_JSON_ELEMENT_NAME,
    ALLERGYRISK_TYPE,
    DOMAIN,
    ICON_FLOWER_POLLEN,
    ICON_MEDICAL_BAG,
    INTEGRATION_DEVICE_MANUFACTURER,
    INTEGRATION_NAME,
    POLLEN_JSON_ELEMENT_NAME,
    POLLEN_TYPES,
)

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


class SensorAttributesMixin:
    """Provide common entity metadata for pollen sensors."""

    def _initialize_sensor_attributes(self, name_suffix: str, icon: str) -> None:
        """Initialize the common entity attributes for a pollen sensor."""
        canonical_entity_name = f"{DOMAIN}_{name_suffix}"
        self._attr_has_entity_name = True
        self._attr_unique_id = canonical_entity_name
        self._attr_icon = icon
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "level"

        # Ensure canonical entity_id independent of friendly name
        self.entity_id = f"sensor.{canonical_entity_name}"

        self.entity_description = SensorEntityDescription(
            key=canonical_entity_name,
            translation_key=canonical_entity_name,
            icon=icon,
            native_unit_of_measurement="level",
            state_class=SensorStateClass.MEASUREMENT,
        )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "polleninformation_at")},
            name=INTEGRATION_NAME,
            manufacturer=INTEGRATION_DEVICE_MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE,
        )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Polleninformation.at sensors for a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Setup pollen sensors for each pollen type defined in POLLEN_TYPES
    sensors: list[SensorEntity] = [
        PollenSensor(coordinator, pollen_type, item["pollen_id"])
        for pollen_type, item in POLLEN_TYPES.items()
    ]

    # Setup sensor for allergyrisk
    sensors.append(AllergyriskSensor(coordinator))

    # Setup sensor for hourly allergyrisk
    sensors.append(AllergyriskHourlySensor(coordinator))

    _LOGGER.debug("Setting up sensor entities: %s", sensors)

    async_add_entities(sensors)


class CoordinatorSensor(SensorAttributesMixin, CoordinatorEntity, SensorEntity):
    """
    Coordinator-backed sensor base class for contamination data.

    1. Builds the sensor name and unique ID based on the provided name suffix.
    2. Uses the passed DataExtractor to extract the relevant contamination data from
       coordinator's response and exposes the values as properties.

    param coordinator: The data update coordinator for this integration.
    param data_extractor: An instance of a DataExtractor subclass to extract the
        relevant contamination data from the coordinator's response.
    param name_suffix: The suffix for the sensor name (e.g., "poaceae", "allergyrisk").
    param icon: The icon for the sensor entity (default is ICON_FLOWER_POLLEN)
    """

    def __init__(
        self,
        coordinator,  # noqa: ANN001
        data_extractor: DataExtractor,
        name_suffix: str,
        icon: str = ICON_FLOWER_POLLEN,
    ) -> None:
        """Initialize the sensor entity."""
        super().__init__(coordinator)

        self.data_extractor = data_extractor
        self.name_suffix = name_suffix

        self._initialize_sensor_attributes(name_suffix, icon)

        _LOGGER.debug(
            ("CoordinatorSensor initialized with _attr_unique_id: %s, name_suffix: %s"),
            self._attr_unique_id,
            self.name_suffix,
        )

    @property
    def native_value(self) -> int | None:
        """Return the current contamination level."""
        return self.data_extractor.get_native_value()

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional sensor attributes."""
        return self.data_extractor.get_extra_state_attributes()


class DataExtractor:
    """Mixin base class to extract contamination data from the coordinator response."""

    def __init__(self, coordinator) -> None:  # noqa: ANN001
        """Initialize the data extractor."""
        self.coordinator = coordinator

    @abstractmethod
    def get_native_value(self) -> int | None:
        """Return the current contamination level for the given element name."""

    @abstractmethod
    def get_extra_state_attributes(self) -> dict:
        """Return additional sensor attributes."""


class PollenDataExtractor(DataExtractor):
    """
    Mixin class to extract pollen contamination data from the coordinator response.

    param coordinator: The data update coordinator for this integration.
    param pollen_id: The numeric ID for the pollen type according to the API response.
    """

    def __init__(self, coordinator, pollen_id: int) -> None:  # noqa: ANN001
        """Initialize the data extractor."""
        self.coordinator = coordinator
        self._pollen_id = pollen_id

    def get_native_value(self) -> int | None:
        """Return the current contamination level for the given element name."""
        data = self._get_contamination_entry()
        return data.get(f"{POLLEN_JSON_ELEMENT_NAME}_1") if data else None

    def get_extra_state_attributes(self) -> dict:
        """Return additional sensor attributes."""
        return {}

    def _get_contamination_entry(self) -> dict | None:
        """Extract the contamination entry for this pollen type."""
        response = self.coordinator.data
        if not response:
            return None

        contamination = response.get(POLLEN_JSON_ELEMENT_NAME)
        if isinstance(contamination, list):
            for entry in contamination:
                if str(entry.get("poll_id")) == str(self._pollen_id):
                    return entry

        _LOGGER.error(
            (
                "PollenDataExtractor element %s containing poll_id %d "
                "not found in data: %s"
            ),
            POLLEN_JSON_ELEMENT_NAME,
            self._pollen_id,
            response,
        )
        return None


class PollenSensor(CoordinatorSensor):
    """
    Sensor for the current contamination level for one specific pollen type.

    param coordinator: The data update coordinator for this integration.
    param pollen_name: The name of the pollen type (e.g., "Poaceae", "Betula").
    param pollen_id: The numeric ID for the pollen type according to the API response.
    """

    def __init__(self, coordinator, pollen_name: str, pollen_id: int) -> None:  # noqa: ANN001
        """Initialize the sensor entity."""
        super().__init__(
            coordinator, PollenDataExtractor(coordinator, pollen_id), pollen_name
        )

        self._pollen_id = pollen_id

        _LOGGER.debug(
            (
                "PollenSensor initialized with _attr_unique_id: %s, "
                "pollen_name: %s, pollen_id: %s"
            ),
            self._attr_unique_id,
            pollen_name,
            pollen_id,
        )


class AllergyriskDataExtractor(DataExtractor):
    """
    Mixin class to extract allergyrisk data from the coordinator response.

    param coordinator: The data update coordinator for this integration.
    """

    def __init__(self, coordinator) -> None:  # noqa: ANN001
        """Initialize the data extractor."""
        self.coordinator = coordinator

    def get_native_value(self) -> int | None:
        """Return the current allergyrisk level for the given element name."""
        data = self._get_contamination_entry()
        return data.get(f"{ALLERGYRISK_JSON_ELEMENT_NAME}_1") if data else None

    def get_extra_state_attributes(self) -> dict:
        """Return additional sensor attributes."""
        return {}

    def _get_contamination_entry(self) -> dict | None:
        """Extract the contamination entry for allergyrisk."""
        response = self.coordinator.data
        if not response:
            return None

        contamination = response.get(ALLERGYRISK_JSON_ELEMENT_NAME)
        if isinstance(contamination, dict):
            return contamination

        _LOGGER.error(
            "AllergyriskDataExtractor element %s not found in data: %s",
            ALLERGYRISK_JSON_ELEMENT_NAME,
            response,
        )
        return None


class AllergyriskSensor(CoordinatorSensor):
    """
    Sensor for the overall current allergyrisk level.

    param coordinator: The data update coordinator for this integration.
    """

    def __init__(self, coordinator) -> None:  # noqa: ANN001
        """Initialize the sensor entity."""
        super().__init__(
            coordinator,
            AllergyriskDataExtractor(coordinator),
            ALLERGYRISK_TYPE,
            ICON_MEDICAL_BAG,
        )

        _LOGGER.debug(
            ("AllergyriskSensor initialized with _attr_unique_id: %s"),
            self._attr_unique_id,
        )


class AllergyriskHourlyDataExtractor(DataExtractor):
    """
    Mixin class to extract hourly allergyrisk data from the coordinator response.

    param coordinator: The data update coordinator for this integration.
    """

    def __init__(self, coordinator) -> None:  # noqa: ANN001
        """Initialize the data extractor."""
        self.coordinator = coordinator

    def get_native_value(self) -> int | None:
        """Return the current hour allergyrisk level for the given element name."""
        data = self._get_contamination_entry()
        if data is None:
            return None

        element = data.get(f"{ALLERGYRISK_HOURLY_JSON_ELEMENT_NAME}_1")
        if element is None:
            _LOGGER.error(
                "AllergyriskHourlyDataExtractor element %s not found in data: %s",
                ALLERGYRISK_HOURLY_JSON_ELEMENT_NAME,
                data,
            )
            return None

        current_hour = dt_util.now().hour
        _LOGGER.debug(
            "AllergyriskHourlyDataExtractor current_hour=%d, element=%s",
            current_hour,
            element,
        )

        if not isinstance(element, list) or current_hour >= len(element):
            _LOGGER.error(
                "AllergyriskHourlyDataExtractor element is not a list "
                "or current_hour=%d is out of bounds, element=%s",
                current_hour,
                element,
            )
            return None

        allergyrisk_value = element[current_hour]
        _LOGGER.debug(
            "AllergyriskHourlyDataExtractor allergyrisk_value: %s", allergyrisk_value
        )

        return allergyrisk_value

    def get_extra_state_attributes(self) -> dict:
        """Return additional sensor attributes."""
        return {}

    def _get_contamination_entry(self) -> dict | None:
        """Extract the contamination entry for allergyrisk."""
        response = self.coordinator.data
        if not response:
            return None

        contamination = response.get(ALLERGYRISK_HOURLY_JSON_ELEMENT_NAME)
        if isinstance(contamination, dict):
            return contamination

        _LOGGER.error(
            "AllergyriskHourlyDataExtractor element %s not found in data: %s",
            ALLERGYRISK_HOURLY_JSON_ELEMENT_NAME,
            response,
        )
        return None


class AllergyriskHourlySensor(SensorAttributesMixin, SensorEntity):
    """
    Sensor for the overall current hour allergyrisk level.

    Does not use the CoordinatorEntity base class because it needs to update
    at the beginning of every hour but not when the coordinator updates.
    The coordinator is still used to fetch the data, but the sensor updates
    its state at the beginning of every hour.

    param coordinator: The data update coordinator for this integration.
    """

    def __init__(self, coordinator) -> None:  # noqa: ANN001
        """Initialize the sensor entity."""
        super().__init__()
        self.data_extractor = AllergyriskHourlyDataExtractor(coordinator)
        self.name_suffix = ALLERGYRISK_HOURLY_TYPE
        self._initialize_sensor_attributes(ALLERGYRISK_HOURLY_TYPE, ICON_MEDICAL_BAG)

        _LOGGER.debug(
            ("AllergyriskSensor initialized with _attr_unique_id: %s"),
            self._attr_unique_id,
        )

    @property
    def native_value(self) -> int | None:
        """Return the current contamination level."""
        return self.data_extractor.get_native_value()

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional sensor attributes."""
        return self.data_extractor.get_extra_state_attributes()

    async def async_added_to_hass(self) -> None:
        """Set up the hourly update listener."""
        await super().async_added_to_hass()

        self.async_on_remove(
            async_track_time_change(
                self.hass,
                self._handle_time_change,
                hour=None,
                minute=0,
                second=0,
            )
        )

    @callback
    def _handle_time_change(self, now: datetime) -> None:  # noqa: ARG002
        """Update the sensor at the beginning of every hour."""
        _LOGGER.debug(
            "AllergyriskHourlySensor updating value at the beginning of the hour."
        )
        self.async_write_ha_state()
