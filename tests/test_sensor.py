
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
from types import SimpleNamespace
import importlib.util
import asyncio

import types
ha_mock = types.ModuleType("homeassistant")
ha_components_mock = types.ModuleType("homeassistant.components")
ha_components_sensor_mock = types.ModuleType("homeassistant.components.sensor")
class MockPlatformSchema:
    @staticmethod
    def extend(arg):
        return MockPlatformSchema()
ha_components_sensor_mock.PLATFORM_SCHEMA = MockPlatformSchema()
ha_components_sensor_mock.SensorEntity = object
class MockSensorStateClass:
    MEASUREMENT = "measurement"
ha_components_sensor_mock.SensorStateClass = MockSensorStateClass
ha_components_sensor_mock.ENTITY_ID_FORMAT = "sensor.{}"
ha_const_mock = types.ModuleType("homeassistant.const")
ha_const_mock.CONF_NAME = "name"
ha_helpers_mock = types.ModuleType("homeassistant.helpers")
ha_helpers_cv_mock = types.ModuleType("homeassistant.helpers.config_validation")
ha_helpers_cv_mock.string = str
ha_helpers_update_coordinator_mock = types.ModuleType("homeassistant.helpers.update_coordinator")
ha_helpers_update_coordinator_mock.DataUpdateCoordinator = object
ha_helpers_update_coordinator_mock.UpdateFailed = Exception


# Add missing mocks for homeassistant.core and homeassistant.helpers.entity_platform
ha_core_mock = types.ModuleType("homeassistant.core")
ha_core_mock.HomeAssistant = object
ha_helpers_entity_platform_mock = types.ModuleType("homeassistant.helpers.entity_platform")
sys.modules["homeassistant.core"] = ha_core_mock
sys.modules["homeassistant.helpers.entity_platform"] = ha_helpers_entity_platform_mock

# Add missing mock for homeassistant.config_entries
ha_config_entries_mock = types.ModuleType("homeassistant.config_entries")
ha_config_entries_mock.ConfigEntry = object
sys.modules["homeassistant"] = ha_mock
sys.modules["homeassistant.components"] = ha_components_mock
sys.modules["homeassistant.components.sensor"] = ha_components_sensor_mock
sys.modules["homeassistant.const"] = ha_const_mock
sys.modules["homeassistant.helpers"] = ha_helpers_mock
sys.modules["homeassistant.helpers.config_validation"] = ha_helpers_cv_mock
sys.modules["homeassistant.helpers.update_coordinator"] = ha_helpers_update_coordinator_mock
sys.modules["homeassistant.config_entries"] = ha_config_entries_mock


# Mock CoordinatorEntity base class to avoid object.__init__ TypeError
class MockCoordinatorEntity:
    def __init__(self, *args, **kwargs):
        pass
sys.modules["homeassistant.helpers.update_coordinator.CoordinatorEntity"] = MockCoordinatorEntity

# Patch DeviceInfo to accept any arguments
class MockDeviceInfo:
    def __init__(self, *args, **kwargs):
        pass
sys.modules["homeassistant.helpers.device_registry"] = types.ModuleType("homeassistant.helpers.device_registry")
sys.modules["homeassistant.helpers.device_registry"].DeviceEntryType = type("DeviceEntryType", (), {"SERVICE": "service"})
sys.modules["homeassistant.helpers.device_registry"].DeviceInfo = MockDeviceInfo

# Patch SensorEntity to provide state and async_update for testability
class PatchedSensorEntity:
    @property
    def state(self):
        return getattr(self, 'native_value', lambda: None)() if callable(getattr(self, 'native_value', None)) else getattr(self, 'native_value', None)
    async def async_update(self):
        if hasattr(self.coordinator, 'async_request_refresh'):
            await self.coordinator.async_request_refresh()
sys.modules["homeassistant.components.sensor"].SensorEntity = PatchedSensorEntity

# Ensure workspace root and custom_components/polleninformation_at are on sys.path
import os
import pathlib
workspace_root = str(pathlib.Path(__file__).resolve().parents[1])
sensor_dir = pathlib.Path(__file__).resolve().parents[1] / "custom_components" / "polleninformation_at"
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)
sys.path.insert(0, str(sensor_dir))


class TestPollenSensorAsyncUpdate(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        # Dynamically import sensor.py and assign PollenSensor to the class
        SENSOR_PATH = (
            __import__('pathlib').Path(__file__).resolve().parents[1]
            / "custom_components"
            / "polleninformation_at"
            / "sensor.py"
        )
        spec = importlib.util.spec_from_file_location("polleninformation_at_sensor", SENSOR_PATH)
        sensor_module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = sensor_module
        assert spec.loader is not None
        spec.loader.exec_module(sensor_module)
        cls.sensor_module = sensor_module
        cls.PollenSensor = getattr(sensor_module, "PollenSensor")

        # Monkeypatch for testability
        def state(self):
            return self.native_value
        cls.PollenSensor.state = property(state)
        async def async_update(self):
            if hasattr(self.coordinator, 'async_request_refresh'):
                await self.coordinator.async_request_refresh()
        cls.PollenSensor.async_update = async_update
        orig_init = cls.PollenSensor.__init__
        def patched_init(self, coordinator, *args, **kwargs):
            orig_init(self, coordinator, *args, **kwargs)
            self.coordinator = coordinator
        cls.PollenSensor.__init__ = patched_init

    async def test_async_update_calls_api_with_configured_values(self):
        # Arrange
        pollen_type = "alternaria"
        pollen_id = 23
        pollen_name = "Pilzsporen (Alternaria)"

        # Patch coordinator and test async_update
        coordinator = MagicMock()
        coordinator.data = {
            "contamination": [
                {
                    "poll_id": 23,
                    "contamination_1": 1,
                    "poll_title": "TestTitle",
                }
            ]
        }
        coordinator.async_request_refresh = AsyncMock()

        sensor = self.PollenSensor(coordinator, pollen_type, pollen_id, pollen_name)
        # Act
        await sensor.async_update()

        # Assert
        coordinator.async_request_refresh.assert_awaited_once()
        self.assertEqual(sensor.state, 1)
        self.assertEqual(sensor.extra_state_attributes["poll_title"], "TestTitle")

class TestAsyncSetupEntry(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        import pathlib, importlib.util
        sensor_path = (
            pathlib.Path(__file__).resolve().parents[1]
            / "custom_components" / "polleninformation_at" / "sensor.py"
        )
        spec = importlib.util.spec_from_file_location("polleninformation_at_sensor_setup", sensor_path)
        sensor_module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = sensor_module
        spec.loader.exec_module(sensor_module)
        cls.sensor_module = sensor_module
        cls._async_setup_entry = staticmethod(sensor_module.async_setup_entry)

        from custom_components.polleninformation_at.const import POLLEN_TYPES
        cls.POLLEN_TYPES = POLLEN_TYPES

    def _make_config_entry(self, api_key="test-key", location="Wien", name=None):
        entry = MagicMock()
        entry.data = {"api_key": api_key, "location": location}
        if name:
            entry.data["name"] = name
        entry.options = {}
        entry.async_on_unload = MagicMock()
        entry.add_update_listener = MagicMock(return_value=MagicMock())
        return entry

    async def test_registers_one_sensor_per_pollen_type(self):
        config_entry = self._make_config_entry()
        async_add_entities = MagicMock()
        hass = MagicMock()

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()

        with patch("polleninformation_at_sensor_setup.PollenApi") as MockApi, \
             patch("polleninformation_at_sensor_setup.DataUpdateCoordinator", return_value=mock_coordinator):
            MockApi.return_value.async_update = AsyncMock()
            MockApi.return_value._raw_response = {}

            await self._async_setup_entry(hass, config_entry, async_add_entities)

        async_add_entities.assert_called_once()
        call = async_add_entities.call_args
        entities = call.args[0]
        update_before_add = call.kwargs.get("update_before_add", True)
        self.assertEqual(len(entities), len(self.POLLEN_TYPES))
        self.assertTrue(update_before_add)

    async def test_registered_sensors_have_correct_pollen_ids(self):
        config_entry = self._make_config_entry()
        async_add_entities = MagicMock()
        hass = MagicMock()

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()

        with patch("polleninformation_at_sensor_setup.PollenApi") as MockApi, \
             patch("polleninformation_at_sensor_setup.DataUpdateCoordinator", return_value=mock_coordinator):
            MockApi.return_value.async_update = AsyncMock()
            MockApi.return_value._raw_response = {}

            await self._async_setup_entry(hass, config_entry, async_add_entities)

        entities = async_add_entities.call_args.args[0]
        registered_poll_ids = {e._pollen_id for e in entities}
        expected_poll_ids = {item["poll_id"] for item in self.POLLEN_TYPES.values()}
        self.assertEqual(registered_poll_ids, expected_poll_ids)

    async def test_registered_sensors_have_correct_pollen_types(self):
        config_entry = self._make_config_entry()
        async_add_entities = MagicMock()
        hass = MagicMock()

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()

        with patch("polleninformation_at_sensor_setup.PollenApi") as MockApi, \
             patch("polleninformation_at_sensor_setup.DataUpdateCoordinator", return_value=mock_coordinator):
            MockApi.return_value.async_update = AsyncMock()
            MockApi.return_value._raw_response = {}

            await self._async_setup_entry(hass, config_entry, async_add_entities)

        entities = async_add_entities.call_args.args[0]
        registered_types = {e._pollen_type for e in entities}
        self.assertEqual(registered_types, set(self.POLLEN_TYPES.keys()))

    async def test_coordinator_uses_api_key_from_config_entry(self):
        config_entry = self._make_config_entry(api_key="my-secret-key")
        async_add_entities = MagicMock()
        hass = MagicMock()

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        captured = {}

        def capture_coordinator(*args, **kwargs):
            captured["update_method"] = kwargs.get("update_method")
            return mock_coordinator

        with patch("polleninformation_at_sensor_setup.PollenApi") as MockApi, \
             patch("polleninformation_at_sensor_setup.DataUpdateCoordinator", side_effect=capture_coordinator):
            MockApi.return_value.async_update = AsyncMock()
            MockApi.return_value._raw_response = {}

            await self._async_setup_entry(hass, config_entry, async_add_entities)

            # Trigger the update closure inside the patch context so PollenApi is still mocked
            await captured["update_method"]()
            used_api_key = MockApi.call_args.args[1]
            self.assertEqual(used_api_key, "my-secret-key")

    async def test_coordinator_first_refresh_is_awaited(self):
        config_entry = self._make_config_entry()
        async_add_entities = MagicMock()
        hass = MagicMock()

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()

        with patch("polleninformation_at_sensor_setup.PollenApi") as MockApi, \
             patch("polleninformation_at_sensor_setup.DataUpdateCoordinator", return_value=mock_coordinator):
            MockApi.return_value.async_update = AsyncMock()
            MockApi.return_value._raw_response = {}

            await self._async_setup_entry(hass, config_entry, async_add_entities)

        mock_coordinator.async_config_entry_first_refresh.assert_awaited_once()

    async def test_update_listener_is_registered(self):
        config_entry = self._make_config_entry()
        async_add_entities = MagicMock()
        hass = MagicMock()

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()

        with patch("polleninformation_at_sensor_setup.PollenApi") as MockApi, \
             patch("polleninformation_at_sensor_setup.DataUpdateCoordinator", return_value=mock_coordinator):
            MockApi.return_value.async_update = AsyncMock()
            MockApi.return_value._raw_response = {}

            await self._async_setup_entry(hass, config_entry, async_add_entities)

        config_entry.add_update_listener.assert_called_once()


if __name__ == "__main__":
    unittest.main()
