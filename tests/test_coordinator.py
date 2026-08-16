"""Tests for the PollenDataUpdateCoordinator class."""

import importlib
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

ha_mock = types.ModuleType("homeassistant")
ha_components_mock = types.ModuleType("homeassistant.components")
ha_components_sensor_mock = types.ModuleType("homeassistant.components.sensor")
ha_helpers_mock = types.ModuleType("homeassistant.helpers")
ha_helpers_cv_mock = types.ModuleType("homeassistant.helpers.config_validation")
ha_helpers_update_coordinator_mock = types.ModuleType(
    "homeassistant.helpers.update_coordinator"
)
ha_helpers_device_registry_mock = types.ModuleType(
    "homeassistant.helpers.device_registry"
)
ha_helpers_entity_platform_mock = types.ModuleType(
    "homeassistant.helpers.entity_platform"
)
ha_config_entries_mock = types.ModuleType("homeassistant.config_entries")
ha_core_mock = types.ModuleType("homeassistant.core")

for module in [
    ha_mock,
    ha_components_mock,
    ha_components_sensor_mock,
    ha_helpers_mock,
    ha_helpers_cv_mock,
    ha_helpers_update_coordinator_mock,
    ha_helpers_device_registry_mock,
    ha_helpers_entity_platform_mock,
    ha_config_entries_mock,
    ha_core_mock,
]:
    module.__package__ = module.__name__
    module.__spec__ = None


class MockDataUpdateCoordinator:
    """Mock DataUpdateCoordinator for testing."""

    def __init__(self, hass, logger, name, update_interval) -> None:  # noqa: ANN001
        """Initialize mock coordinator with hass, logger, name, and update_interval."""
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval


class MockUpdateFailedError(Exception):
    """Mock UpdateFailed exception for testing."""


class MockCoordinatorEntity:
    """Mock CoordinatorEntity for sensor compatibility."""

    def __init__(self, coordinator: object, *_args: object, **_kwargs: object) -> None:
        self.coordinator = coordinator


class MockSensorStateClass:
    """Mock sensor state class constants."""

    MEASUREMENT = "measurement"


class MockSensorEntity:
    """Mock sensor entity class."""

    @property
    def state(self) -> object:
        native_value = getattr(self, "native_value", None)
        return native_value() if callable(native_value) else native_value


class MockSensorEntityDescription:
    """Mock sensor entity description class."""

    def __init__(self, *args: object, **kwargs: object) -> None:  # noqa: ANN002, ANN003, ARG002
        for key, value in kwargs.items():
            setattr(self, key, value)


ha_components_sensor_mock.SensorEntity = MockSensorEntity  # type: ignore[attr-defined]
ha_components_sensor_mock.SensorEntityDescription = MockSensorEntityDescription  # type: ignore[attr-defined]
ha_components_sensor_mock.SensorStateClass = MockSensorStateClass  # type: ignore[attr-defined]
ha_helpers_cv_mock.config_entry_only_config_schema = staticmethod(lambda domain: None)  # type: ignore[attr-defined]  # noqa: ARG005
ha_helpers_update_coordinator_mock.DataUpdateCoordinator = MockDataUpdateCoordinator  # type: ignore[attr-defined]
ha_helpers_update_coordinator_mock.CoordinatorEntity = MockCoordinatorEntity  # type: ignore[attr-defined]
ha_helpers_update_coordinator_mock.UpdateFailed = MockUpdateFailedError  # type: ignore[attr-defined]
ha_helpers_device_registry_mock.DeviceEntryType = type(  # type: ignore[attr-defined]
    "DeviceEntryType",
    (),
    {"SERVICE": "service"},
)
ha_helpers_device_registry_mock.DeviceInfo = type(  # type: ignore[attr-defined]
    "DeviceInfo",
    (),
    {"__init__": lambda self, *args, **kwargs: None},
)
ha_helpers_entity_platform_mock.AddEntitiesCallback = object  # type: ignore[attr-defined]
ha_config_entries_mock.ConfigEntry = object  # type: ignore[attr-defined]
ha_core_mock.HomeAssistant = object  # type: ignore[attr-defined]

ha_mock.__path__ = []
ha_components_mock.__path__ = []
ha_helpers_mock.__path__ = []
ha_mock.components = ha_components_mock
ha_mock.helpers = ha_helpers_mock
ha_mock.config_entries = ha_config_entries_mock
ha_mock.core = ha_core_mock
ha_components_mock.sensor = ha_components_sensor_mock
ha_helpers_mock.config_validation = ha_helpers_cv_mock
ha_helpers_mock.update_coordinator = ha_helpers_update_coordinator_mock
ha_helpers_mock.device_registry = ha_helpers_device_registry_mock
ha_helpers_mock.entity_platform = ha_helpers_entity_platform_mock
ha_helpers_update_coordinator_mock.__package__ = (
    "homeassistant.helpers.update_coordinator"
)
ha_components_sensor_mock.__package__ = "homeassistant.components.sensor"
ha_helpers_cv_mock.__package__ = "homeassistant.helpers.config_validation"

sys.modules.setdefault("homeassistant", ha_mock)
sys.modules.setdefault("homeassistant.components", ha_components_mock)
sys.modules.setdefault("homeassistant.components.sensor", ha_components_sensor_mock)
sys.modules.setdefault("homeassistant.helpers", ha_helpers_mock)
sys.modules.setdefault("homeassistant.helpers.config_validation", ha_helpers_cv_mock)
sys.modules.setdefault(
    "homeassistant.helpers.update_coordinator", ha_helpers_update_coordinator_mock
)
sys.modules.setdefault(
    "homeassistant.helpers.device_registry", ha_helpers_device_registry_mock
)
sys.modules.setdefault(
    "homeassistant.helpers.entity_platform", ha_helpers_entity_platform_mock
)
sys.modules.setdefault("homeassistant.config_entries", ha_config_entries_mock)
sys.modules.setdefault("homeassistant.core", ha_core_mock)

workspace_root = pathlib.Path(__file__).resolve().parents[1]
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

coordinator_module = importlib.import_module(
    "custom_components.polleninformation_at.coordinator"
)

PollenDataUpdateCoordinator = coordinator_module.PollenDataUpdateCoordinator
UpdateFailed = coordinator_module.UpdateFailed


class TestPollenDataUpdateCoordinator(unittest.IsolatedAsyncioTestCase):
    """Tests for the PollenDataUpdateCoordinator class."""

    def _entry(
        self,
        data_api_key: str = "data-key",
        options_api_key: str | None = None,
    ) -> MagicMock:
        entry = MagicMock()
        entry.data = {"api_key": data_api_key}
        entry.options = {}
        if options_api_key is not None:
            entry.options["api_key"] = options_api_key
        return entry

    async def test_uses_options_api_key_over_data_api_key(self) -> None:
        """Test that options API key takes precedence over data API key."""
        hass = MagicMock()
        entry = self._entry(data_api_key="data-key", options_api_key="options-key")
        coordinator = PollenDataUpdateCoordinator(hass, entry)

        with patch(
            "custom_components.polleninformation_at.coordinator.PollenApi"
        ) as mock_api_cls:
            api_instance = mock_api_cls.return_value
            api_instance.async_update = AsyncMock()
            api_instance.raw_response = {"contamination": []}

            await coordinator._async_update_data()  # noqa: SLF001

        used_api_key = mock_api_cls.call_args.args[1]
        self.assertEqual(used_api_key, "options-key")  # noqa: PT009

    async def test_returns_raw_response_on_success(self) -> None:
        """Test that the coordinator returns raw API response on success."""
        hass = MagicMock()
        entry = self._entry()
        coordinator = PollenDataUpdateCoordinator(hass, entry)

        with patch(
            "custom_components.polleninformation_at.coordinator.PollenApi"
        ) as mock_api_cls:
            api_instance = mock_api_cls.return_value
            api_instance.async_update = AsyncMock()
            api_instance.raw_response = {"contamination": [{"poll_id": 23}]}

            data = await coordinator._async_update_data()  # noqa: SLF001

        self.assertEqual(data, {"contamination": [{"poll_id": 23}]})  # noqa: PT009

    async def test_wraps_api_error_in_update_failed(self) -> None:
        """Test that API errors are wrapped in UpdateFailed."""
        hass = MagicMock()
        entry = self._entry()
        coordinator = PollenDataUpdateCoordinator(hass, entry)

        with patch(
            "custom_components.polleninformation_at.coordinator.PollenApi"
        ) as mock_api_cls:
            api_instance = mock_api_cls.return_value
            api_instance.async_update = AsyncMock(side_effect=RuntimeError("boom"))
            api_instance.raw_response = None

            with self.assertRaises(UpdateFailed):  # noqa: PT027
                await coordinator._async_update_data()  # noqa: SLF001


if __name__ == "__main__":
    unittest.main()
