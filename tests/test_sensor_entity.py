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
ha_components_sensor_mock.SensorEntity = PatchedSensorEntity

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
        PollenSensor.state = property(lambda self: self.native_value)
        orig_init = PollenSensor.__init__
        def patched_init(self, coordinator, *args, **kwargs):
            orig_init(self, coordinator, *args, **kwargs)
            self.coordinator = coordinator
        PollenSensor.__init__ = patched_init

    def _make_sensor(self, coordinator, pollen_type="alternaria", pollen_id=23, pollen_name="Pilzsporen (Alternaria)"):
        return PollenSensor(coordinator, pollen_type, pollen_id, pollen_name)

    def _coordinator_with(self, entries):
        coordinator = MagicMock()
        coordinator.data = {"contamination": entries}
        return coordinator

    # --- native_value ---

    def test_native_value_returns_contamination_level(self):
        coordinator = self._coordinator_with([{"poll_id": 23, "contamination_1": 5, "poll_title": "Alternaria"}])
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.native_value, 5)

    def test_native_value_returns_none_when_no_data(self):
        coordinator = MagicMock()
        coordinator.data = None
        sensor = self._make_sensor(coordinator)
        self.assertIsNone(sensor.native_value)

    def test_native_value_returns_none_when_poll_id_not_found(self):
        coordinator = self._coordinator_with([{"poll_id": 99, "contamination_1": 3, "poll_title": "Other"}])
        sensor = self._make_sensor(coordinator)
        self.assertIsNone(sensor.native_value)

    def test_native_value_returns_none_when_contamination_missing(self):
        coordinator = self._coordinator_with([{"poll_id": 23, "poll_title": "Alternaria"}])
        sensor = self._make_sensor(coordinator)
        self.assertIsNone(sensor.native_value)

    def test_native_value_returns_zero(self):
        coordinator = self._coordinator_with([{"poll_id": 23, "contamination_1": 0, "poll_title": "Alternaria"}])
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.native_value, 0)

    # --- extra_state_attributes ---

    def test_extra_state_attributes_returns_poll_title(self):
        coordinator = self._coordinator_with([{"poll_id": 23, "contamination_1": 2, "poll_title": "TestTitle"}])
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.extra_state_attributes, {"poll_title": "TestTitle"})

    def test_extra_state_attributes_returns_empty_dict_when_no_data(self):
        coordinator = MagicMock()
        coordinator.data = None
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.extra_state_attributes, {})

    def test_extra_state_attributes_returns_empty_dict_when_poll_id_not_found(self):
        coordinator = self._coordinator_with([{"poll_id": 99, "contamination_1": 1, "poll_title": "Other"}])
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.extra_state_attributes, {})

    # --- static attributes ---

    def test_attr_name(self):
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(coordinator, pollen_name="Roggen (Secale)")
        self.assertEqual(sensor._attr_name, "Roggen (Secale)")

    def test_attr_unique_id(self):
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(coordinator, pollen_type="secale")
        self.assertEqual(sensor._attr_unique_id, "polleninformation_at_secale")

    def test_attr_icon(self):
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor._attr_icon, "mdi:flower-pollen")

    def test_attr_state_class(self):
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor._attr_state_class, "measurement")

    def test_attr_native_unit_of_measurement(self):
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor._attr_native_unit_of_measurement, "level")

    def test_attr_has_entity_name(self):
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(coordinator)
        self.assertTrue(sensor._attr_has_entity_name)

    # --- state (via monkeypatched property) ---

    def test_state_equals_native_value(self):
        coordinator = self._coordinator_with([{"poll_id": 23, "contamination_1": 7, "poll_title": "Alternaria"}])
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.state, sensor.native_value)

    def test_state_is_none_when_no_match(self):
        coordinator = self._coordinator_with([{"poll_id": 99, "contamination_1": 3, "poll_title": "Other"}])
        sensor = self._make_sensor(coordinator)
        self.assertIsNone(sensor.state)

if __name__ == "__main__":
    unittest.main()
