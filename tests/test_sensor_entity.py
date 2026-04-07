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
ha_helpers_update_coordinator_mock = types.ModuleType("homeassistant.helpers.update_coordinator")
ha_helpers_update_coordinator_mock.DataUpdateCoordinator = object
ha_helpers_update_coordinator_mock.UpdateFailed = Exception
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
sys.modules["homeassistant.helpers.update_coordinator"] = ha_helpers_update_coordinator_mock
sys.modules["homeassistant.config_entries"] = ha_config_entries_mock
sys.modules["homeassistant.core"] = ha_core_mock
sys.modules["homeassistant.helpers.entity_platform"] = ha_helpers_entity_platform_mock

import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import unittest
from unittest.mock import MagicMock
from custom_components.polleninformation_at.sensor_entity import PollenSensor

class TestPollenSensorLogic(unittest.IsolatedAsyncioTestCase):
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
        sensor_instance = PollenSensor(coordinator, pollen_type, pollen_name)

        # Assert
        assert sensor_instance.state == 7
        assert sensor_instance.extra_state_attributes == {"poll_title": "TestTitle"}
        assert sensor_instance.available is True

if __name__ == "__main__":
    unittest.main()
