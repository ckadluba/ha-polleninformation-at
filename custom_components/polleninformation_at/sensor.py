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
    ALLERGYRISK_CURRENT_JSON_SUBELEMENT_NAME,
    ALLERGYRISK_FORECAST1_JSON_SUBELEMENT_NAME,
    ALLERGYRISK_FORECAST2_JSON_SUBELEMENT_NAME,
    ALLERGYRISK_FORECAST3_JSON_SUBELEMENT_NAME,
    ALLERGYRISK_HOURLY_CURRENT_JSON_SUBELEMENT_NAME,
    ALLERGYRISK_HOURLY_FORECAST1_JSON_SUBELEMENT_NAME,
    ALLERGYRISK_HOURLY_FORECAST2_JSON_SUBELEMENT_NAME,
    ALLERGYRISK_HOURLY_FORECAST3_JSON_SUBELEMENT_NAME,
    ALLERGYRISK_HOURLY_JSON_ELEMENT_NAME,
    ALLERGYRISK_HOURLY_TYPE,
    ALLERGYRISK_JSON_ELEMENT_NAME,
    ALLERGYRISK_TYPE,
    DOMAIN,
    FORECAST1_SUFFIX,
    FORECAST2_SUFFIX,
    FORECAST3_SUFFIX,
    ICON_FLOWER_POLLEN,
    ICON_MEDICAL_BAG,
    INTEGRATION_DEVICE_MANUFACTURER,
    INTEGRATION_NAME,
    POLLEN_CURRENT_JSON_SUBELEMENT_NAME,
    POLLEN_FORECAST1_JSON_SUBELEMENT_NAME,
    POLLEN_FORECAST2_JSON_SUBELEMENT_NAME,
    POLLEN_FORECAST3_JSON_SUBELEMENT_NAME,
    POLLEN_JSON_ELEMENT_NAME,
    POLLEN_TYPES,
)

if TYPE_CHECKING:
    from datetime import datetime

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

    # Setup pollen sensors for each pollen type defined in POLLEN_TYPES
    sensors: list[SensorEntity] = [
        sensor
        for pollen_type, item in POLLEN_TYPES.items()
        for sensor in (
            PollenSensor(
                coordinator=coordinator,
                pollen_name=pollen_type,
                pollen_id=item["pollen_id"],
            ),
            PollenSensor(
                coordinator=coordinator,
                pollen_name=pollen_type,
                pollen_id=item["pollen_id"],
                forecast_suffix=FORECAST1_SUFFIX,
                json_subelement_name=POLLEN_FORECAST1_JSON_SUBELEMENT_NAME,
            ),
            PollenSensor(
                coordinator=coordinator,
                pollen_name=pollen_type,
                pollen_id=item["pollen_id"],
                forecast_suffix=FORECAST2_SUFFIX,
                json_subelement_name=POLLEN_FORECAST2_JSON_SUBELEMENT_NAME,
            ),
            PollenSensor(
                coordinator=coordinator,
                pollen_name=pollen_type,
                pollen_id=item["pollen_id"],
                forecast_suffix=FORECAST3_SUFFIX,
                json_subelement_name=POLLEN_FORECAST3_JSON_SUBELEMENT_NAME,
            ),
        )
    ]

    # Setup sensors for allergy risk
    sensors.append(AllergyriskSensor(coordinator))
    sensors.append(
        AllergyriskSensor(
            coordinator=coordinator,
            forecast_suffix=FORECAST1_SUFFIX,
            json_subelement_name=ALLERGYRISK_FORECAST1_JSON_SUBELEMENT_NAME,
        )
    )
    sensors.append(
        AllergyriskSensor(
            coordinator=coordinator,
            forecast_suffix=FORECAST2_SUFFIX,
            json_subelement_name=ALLERGYRISK_FORECAST2_JSON_SUBELEMENT_NAME,
        )
    )
    sensors.append(
        AllergyriskSensor(
            coordinator=coordinator,
            forecast_suffix=FORECAST3_SUFFIX,
            json_subelement_name=ALLERGYRISK_FORECAST3_JSON_SUBELEMENT_NAME,
        )
    )

    # Setup sensors for hourly allergy risk
    sensors.append(AllergyriskHourlySensor(coordinator))
    sensors.append(
        AllergyriskHourlySensor(
            coordinator=coordinator,
            forecast_suffix=FORECAST1_SUFFIX,
            json_subelement_name=ALLERGYRISK_HOURLY_FORECAST1_JSON_SUBELEMENT_NAME,
        )
    )
    sensors.append(
        AllergyriskHourlySensor(
            coordinator=coordinator,
            forecast_suffix=FORECAST2_SUFFIX,
            json_subelement_name=ALLERGYRISK_HOURLY_FORECAST2_JSON_SUBELEMENT_NAME,
        )
    )
    sensors.append(
        AllergyriskHourlySensor(
            coordinator=coordinator,
            forecast_suffix=FORECAST3_SUFFIX,
            json_subelement_name=ALLERGYRISK_HOURLY_FORECAST3_JSON_SUBELEMENT_NAME,
        )
    )

    _LOGGER.debug("Setting up sensor entities: %s", sensors)

    async_add_entities(sensors)


class SensorAttributesMixin:
    """Provide common entity metadata for pollen sensors."""

    def _initialize_sensor_attributes(
        self, name_suffix: str, forecast_suffix: str, icon: str
    ) -> None:
        """Initialize the common entity attributes for a pollen sensor."""
        canonical_entity_name = f"{DOMAIN}_{name_suffix}"
        if forecast_suffix:
            canonical_entity_name += f"_{forecast_suffix}"
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
    param forecast_suffix: The suffix for the forecast sensor name (e.g., "forecast1").
    param icon: The icon for the sensor entity (default is ICON_FLOWER_POLLEN)
    """

    def __init__(
        self,
        coordinator,  # noqa: ANN001
        data_extractor: DataExtractor,
        name_suffix: str,
        forecast_suffix: str,
        icon: str,
    ) -> None:
        """Initialize the sensor entity."""
        super().__init__(coordinator)

        self.data_extractor = data_extractor
        self._initialize_sensor_attributes(name_suffix, forecast_suffix, icon)

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

    def __init__(self, coordinator, json_subelement_name: str) -> None:  # noqa: ANN001
        """Initialize the data extractor."""
        self.coordinator = coordinator
        self.json_subelement_name = json_subelement_name

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

    def __init__(
        self,
        coordinator,  # noqa: ANN001
        pollen_id: int,
        json_subelement_name: str,
    ) -> None:
        """Initialize the data extractor."""
        super().__init__(coordinator, json_subelement_name)
        self._pollen_id = pollen_id

    def get_native_value(self) -> int | None:
        """Return the current contamination level for the given element name."""
        data = self._get_contamination_entry()
        return data.get(self.json_subelement_name) if data else None

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
    param json_subelement_name: The JSON subelement name for the pollen type in the
        API response (e.g., "contamination_1", "contamination_2").
    """

    def __init__(
        self,
        coordinator,  # noqa: ANN001
        pollen_name: str,
        pollen_id: int,
        forecast_suffix: str = "",
        json_subelement_name: str = POLLEN_CURRENT_JSON_SUBELEMENT_NAME,
    ) -> None:
        """Initialize the sensor entity."""
        super().__init__(
            coordinator,
            PollenDataExtractor(coordinator, pollen_id, json_subelement_name),
            pollen_name,
            forecast_suffix,
            ICON_FLOWER_POLLEN,
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

    def __init__(self, coordinator, json_subelement_name: str) -> None:  # noqa: ANN001
        """Initialize the data extractor."""
        super().__init__(coordinator, json_subelement_name)

    def get_native_value(self) -> int | None:
        """Return the current allergyrisk level for the given element name."""
        data = self._get_contamination_entry()
        return data.get(self.json_subelement_name) if data else None

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

    def __init__(
        self,
        coordinator,  # noqa: ANN001
        forecast_suffix: str = "",
        json_subelement_name: str = ALLERGYRISK_CURRENT_JSON_SUBELEMENT_NAME,
    ) -> None:
        """Initialize the sensor entity."""
        super().__init__(
            coordinator,
            AllergyriskDataExtractor(coordinator, json_subelement_name),
            ALLERGYRISK_TYPE,
            forecast_suffix,
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

    def __init__(self, coordinator, json_subelement_name: str) -> None:  # noqa: ANN001
        """Initialize the data extractor."""
        self.coordinator = coordinator
        self.json_subelement_name = json_subelement_name

    def get_native_value(self) -> int | None:
        """Return the current hour allergyrisk level for the given element name."""
        element = self._get_contamination_subelement()
        if element is None:
            return None

        current_hour = dt_util.now().hour
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
            "AllergyriskHourlyDataExtractor current_hour=%d, "
            "element=%s, allergyrisk_value: %s",
            current_hour,
            element,
            allergyrisk_value,
        )

        return allergyrisk_value

    def get_extra_state_attributes(self) -> dict:
        """Return additional sensor attributes."""
        element = self._get_contamination_subelement()
        return {self.json_subelement_name: element}

    def _get_contamination_subelement(self) -> dict | None:
        """Extract the contamination entry for allergyrisk."""
        response = self.coordinator.data
        if not response:
            return None

        contamination = response.get(ALLERGYRISK_HOURLY_JSON_ELEMENT_NAME)
        if not isinstance(contamination, dict):
            _LOGGER.error(
                "AllergyriskHourlyDataExtractor element %s not found in data: %s",
                ALLERGYRISK_HOURLY_JSON_ELEMENT_NAME,
                response,
            )
            return None

        element = contamination.get(self.json_subelement_name)
        if element is None:
            _LOGGER.error(
                "AllergyriskHourlyDataExtractor element %s not found in data: %s",
                self.json_subelement_name,
                contamination,
            )
            return None

        return element


class AllergyriskHourlySensor(SensorAttributesMixin, SensorEntity):
    """
    Sensor for the overall current hour allergyrisk level.

    Does not use the CoordinatorEntity base class because it needs to update
    at the beginning of every hour but not when the coordinator updates.
    The coordinator is still used to fetch the data, but the sensor updates
    its state at the beginning of every hour.

    param coordinator: The data update coordinator for this integration.
    """

    def __init__(
        self,
        coordinator,  # noqa: ANN001
        forecast_suffix: str = "",
        json_subelement_name: str = ALLERGYRISK_HOURLY_CURRENT_JSON_SUBELEMENT_NAME,
    ) -> None:
        """Initialize the sensor entity."""
        super().__init__()
        self.data_extractor = AllergyriskHourlyDataExtractor(
            coordinator, json_subelement_name
        )
        self.name_suffix = ALLERGYRISK_HOURLY_TYPE
        self._initialize_sensor_attributes(
            ALLERGYRISK_HOURLY_TYPE, forecast_suffix, ICON_MEDICAL_BAG
        )

        _LOGGER.debug(
            "AllergyriskHourlySensor initialized with _attr_unique_id: %s",
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
        self.async_write_ha_state()
