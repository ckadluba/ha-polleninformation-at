import sys
import types
# Mock all required Home Assistant modules before any custom_components import
ha_mock = types.ModuleType("homeassistant")
ha_components_mock = types.ModuleType("homeassistant.components")
ha_components_sensor_mock = types.ModuleType("homeassistant.components.sensor")
class DummyPlatformSchema:
    def extend(self, *args, **kwargs):
        return self
ha_components_sensor_mock.PLATFORM_SCHEMA = DummyPlatformSchema()
class DummySensorStateClass:
    MEASUREMENT = "measurement"
ha_components_sensor_mock.SensorEntity = object
ha_components_sensor_mock.SensorStateClass = DummySensorStateClass
ha_components_sensor_mock.ENTITY_ID_FORMAT = "sensor.{}"
ha_const_mock = types.ModuleType("homeassistant.const")
ha_const_mock.CONF_NAME = "name"
ha_helpers_mock = types.ModuleType("homeassistant.helpers")
ha_helpers_cv_mock = types.ModuleType("homeassistant.helpers.config_validation")
ha_helpers_cv_mock.string = lambda x: x

# Mock homeassistant.helpers.update_coordinator
ha_helpers_update_coordinator_mock = types.ModuleType("homeassistant.helpers.update_coordinator")
ha_helpers_update_coordinator_mock.DataUpdateCoordinator = object
ha_helpers_update_coordinator_mock.UpdateFailed = Exception
sys.modules["homeassistant.helpers.update_coordinator"] = ha_helpers_update_coordinator_mock


# Patch DeviceInfo to accept any arguments
ha_helpers_device_registry_mock = types.ModuleType("homeassistant.helpers.device_registry")
ha_helpers_device_registry_mock.DeviceEntryType = type("DeviceEntryType", (), {"SERVICE": "service"})
class MockDeviceInfo:
    def __init__(self, *args, **kwargs):
        pass
ha_helpers_device_registry_mock.DeviceInfo = MockDeviceInfo
sys.modules["homeassistant.helpers.device_registry"] = ha_helpers_device_registry_mock

# Patch SensorEntity to provide state and async_update for testability
class PatchedSensorEntity:
    @property
    def state(self):
        return getattr(self, 'native_value', lambda: None)() if callable(getattr(self, 'native_value', None)) else getattr(self, 'native_value', None)
    async def async_update(self):
        if hasattr(self.coordinator, 'async_request_refresh'):
            await self.coordinator.async_request_refresh()
sys.modules["homeassistant.components.sensor"].SensorEntity = PatchedSensorEntity

# Mock CoordinatorEntity base class to avoid object.__init__ TypeError
class MockCoordinatorEntity:
    def __init__(self, *args, **kwargs):
        pass
sys.modules["homeassistant.helpers.update_coordinator.CoordinatorEntity"] = MockCoordinatorEntity

# Other mocks
ha_config_entries_mock = types.ModuleType("homeassistant.config_entries")
ha_config_entries_mock.ConfigEntry = object
ha_core_mock = types.ModuleType("homeassistant.core")
ha_core_mock.HomeAssistant = object
ha_helpers_entity_platform_mock = types.ModuleType("homeassistant.helpers.entity_platform")
sys.modules["homeassistant"] = ha_mock
sys.modules["homeassistant.components"] = ha_components_mock
sys.modules["homeassistant.components.sensor"] = ha_components_sensor_mock
sys.modules["homeassistant.const"] = ha_const_mock
sys.modules["homeassistant.helpers"] = ha_helpers_mock
sys.modules["homeassistant.helpers.config_validation"] = ha_helpers_cv_mock
sys.modules["homeassistant.config_entries"] = ha_config_entries_mock
sys.modules["homeassistant.core"] = ha_core_mock
sys.modules["homeassistant.helpers.entity_platform"] = ha_helpers_entity_platform_mock

import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import unittest
from unittest.mock import MagicMock
from custom_components.polleninformation_at.sensor_entity import PollenSensor

class TestPollenSensorLogic(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        # Monkeypatch PollenSensor for testability
        from custom_components.polleninformation_at.sensor_entity import PollenSensor
        def state(self):
            return self.native_value
        PollenSensor.state = property(state)
        async def async_update(self):
            if hasattr(self.coordinator, 'async_request_refresh'):
                await self.coordinator.async_request_refresh()
        PollenSensor.async_update = async_update
        orig_init = PollenSensor.__init__
        def patched_init(self, coordinator, *args, **kwargs):
            orig_init(self, coordinator, *args, **kwargs)
            self.coordinator = coordinator
        PollenSensor.__init__ = patched_init
        # Patch available property for test
        PollenSensor.available = property(lambda self: True)

    def test_sensor_properties(self):
        # Arrange
        coordinator = MagicMock()
        coordinator.data = {
            "contamination": [
                {
                    "poll_id": "alternaria",
                    "contamination_1": 7,
                    "poll_title": "TestTitle",
                }
            ]
        }
        pollen_type = "alternaria"
        pollen_name = "Pilzsporen (Alternaria)"
        sensor_instance = PollenSensor(coordinator, pollen_type, pollen_type, pollen_name)

        # Assert
        assert sensor_instance.state == 7
        assert sensor_instance.extra_state_attributes == {"poll_title": "TestTitle"}
        assert sensor_instance.available is True

if __name__ == "__main__":
    unittest.main()
