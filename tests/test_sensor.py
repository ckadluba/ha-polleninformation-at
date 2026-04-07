
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

# Workaround for relative import error: add custom_components/polleninformation_at to sys.path
import os
import pathlib
sensor_dir = pathlib.Path(__file__).resolve().parents[1] / "custom_components" / "polleninformation_at"
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

    async def test_async_update_calls_api_with_configured_values(self):
        # Arrange
        pollen_type = "alternaria"
        pollen_name = "Pilzsporen (Alternaria)"

        # Patch coordinator and test async_update
        coordinator = MagicMock()
        coordinator.data = {
            "contamination": [
                {
                    "poll_id": "alternaria",
                    "contamination_1": 1,
                    "poll_title": "TestTitle",
                }
            ]
        }
        coordinator.async_request_refresh = AsyncMock()

        sensor = self.PollenSensor(coordinator, pollen_type, pollen_name)
        # Act
        await sensor.async_update()

        # Assert
        coordinator.async_request_refresh.assert_awaited_once()
        self.assertEqual(sensor.state, 1)
        self.assertEqual(sensor.extra_state_attributes["poll_title"], "TestTitle")

if __name__ == "__main__":
    unittest.main()
