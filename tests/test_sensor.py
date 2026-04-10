import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import AsyncMock, MagicMock


ha_mock = types.ModuleType("homeassistant")
ha_components_mock = types.ModuleType("homeassistant.components")
ha_components_sensor_mock = types.ModuleType("homeassistant.components.sensor")
ha_helpers_mock = types.ModuleType("homeassistant.helpers")
ha_helpers_cv_mock = types.ModuleType("homeassistant.helpers.config_validation")
ha_helpers_update_coordinator_mock = types.ModuleType("homeassistant.helpers.update_coordinator")
ha_helpers_device_registry_mock = types.ModuleType("homeassistant.helpers.device_registry")
ha_helpers_entity_platform_mock = types.ModuleType("homeassistant.helpers.entity_platform")
ha_config_entries_mock = types.ModuleType("homeassistant.config_entries")
ha_core_mock = types.ModuleType("homeassistant.core")


class MockSensorStateClass:
    MEASUREMENT = "measurement"


class MockSensorEntity:
    @property
    def state(self):
        native_value = getattr(self, "native_value", None)
        return native_value() if callable(native_value) else native_value


class MockCoordinatorEntity:
    def __init__(self, coordinator, *args, **kwargs):
        self.coordinator = coordinator


class MockDataUpdateCoordinator:
    def __init__(self, *args, **kwargs):
        pass


class MockDeviceInfo:
    def __init__(self, *args, **kwargs):
        pass


ha_components_sensor_mock.SensorEntity = MockSensorEntity
ha_components_sensor_mock.SensorStateClass = MockSensorStateClass
ha_helpers_cv_mock.config_entry_only_config_schema = lambda domain: None
ha_helpers_update_coordinator_mock.DataUpdateCoordinator = MockDataUpdateCoordinator
ha_helpers_update_coordinator_mock.CoordinatorEntity = MockCoordinatorEntity
ha_helpers_update_coordinator_mock.UpdateFailed = Exception
ha_helpers_device_registry_mock.DeviceEntryType = type(
    "DeviceEntryType",
    (),
    {"SERVICE": "service"},
)
ha_helpers_device_registry_mock.DeviceInfo = MockDeviceInfo
ha_helpers_entity_platform_mock.AddEntitiesCallback = object
ha_config_entries_mock.ConfigEntry = object
ha_core_mock.HomeAssistant = object

sys.modules["homeassistant"] = ha_mock
sys.modules["homeassistant.components"] = ha_components_mock
sys.modules["homeassistant.components.sensor"] = ha_components_sensor_mock
sys.modules["homeassistant.helpers"] = ha_helpers_mock
sys.modules["homeassistant.helpers.config_validation"] = ha_helpers_cv_mock
sys.modules["homeassistant.helpers.update_coordinator"] = ha_helpers_update_coordinator_mock
sys.modules["homeassistant.helpers.device_registry"] = ha_helpers_device_registry_mock
sys.modules["homeassistant.helpers.entity_platform"] = ha_helpers_entity_platform_mock
sys.modules["homeassistant.config_entries"] = ha_config_entries_mock
sys.modules["homeassistant.core"] = ha_core_mock

workspace_root = pathlib.Path(__file__).resolve().parents[1]
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))


def load_sensor_module(module_name: str):
    sensor_path = workspace_root / "custom_components" / "polleninformation_at" / "sensor.py"
    spec = importlib.util.spec_from_file_location(module_name, sensor_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestPollenSensorLogic(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.sensor_module = load_sensor_module("polleninformation_at_sensor")
        cls.PollenSensor = cls.sensor_module.PollenSensor

        async def async_update(self):
            await self.coordinator.async_request_refresh()

        cls.PollenSensor.async_update = async_update

    def _make_sensor(
        self,
        coordinator,
        pollen_type="alternaria",
        pollen_id=23,
        pollen_name="Pilzsporen (Alternaria)",
    ):
        return self.PollenSensor(coordinator, pollen_type, pollen_id, pollen_name)

    def _coordinator_with(self, entries):
        coordinator = MagicMock()
        coordinator.data = {"contamination": entries}
        return coordinator

    async def test_async_update_requests_refresh_from_coordinator(self):
        coordinator = self._coordinator_with(
            [{"poll_id": 23, "contamination_1": 1, "poll_title": "TestTitle"}]
        )
        coordinator.async_request_refresh = AsyncMock()

        sensor = self._make_sensor(coordinator)
        await sensor.async_update()

        coordinator.async_request_refresh.assert_awaited_once()
        self.assertEqual(sensor.state, 1)

    def test_native_value_returns_contamination_level(self):
        coordinator = self._coordinator_with(
            [{"poll_id": 23, "contamination_1": 5, "poll_title": "Alternaria"}]
        )
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.native_value, 5)

    def test_native_value_returns_none_when_no_data(self):
        coordinator = MagicMock()
        coordinator.data = None
        sensor = self._make_sensor(coordinator)
        self.assertIsNone(sensor.native_value)

    def test_native_value_returns_none_when_pollen_id_not_found(self):
        coordinator = self._coordinator_with(
            [{"poll_id": 99, "contamination_1": 3, "poll_title": "Other"}]
        )
        sensor = self._make_sensor(coordinator)
        self.assertIsNone(sensor.native_value)

    def test_native_value_returns_none_when_contamination_missing(self):
        coordinator = self._coordinator_with([{"poll_id": 23, "poll_title": "Alternaria"}])
        sensor = self._make_sensor(coordinator)
        self.assertIsNone(sensor.native_value)

    def test_native_value_returns_zero(self):
        coordinator = self._coordinator_with(
            [{"poll_id": 23, "contamination_1": 0, "poll_title": "Alternaria"}]
        )
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.native_value, 0)

    def test_extra_state_attributes_returns_poll_title(self):
        coordinator = self._coordinator_with(
            [{"poll_id": 23, "contamination_1": 2, "poll_title": "TestTitle"}]
        )
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.extra_state_attributes, {"poll_title": "TestTitle"})

    def test_extra_state_attributes_returns_empty_dict_when_no_data(self):
        coordinator = MagicMock()
        coordinator.data = None
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.extra_state_attributes, {})

    def test_extra_state_attributes_returns_empty_dict_when_pollen_id_not_found(self):
        coordinator = self._coordinator_with(
            [{"poll_id": 99, "contamination_1": 1, "poll_title": "Other"}]
        )
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.extra_state_attributes, {})

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

    def test_state_equals_native_value(self):
        coordinator = self._coordinator_with(
            [{"poll_id": 23, "contamination_1": 7, "poll_title": "Alternaria"}]
        )
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.state, sensor.native_value)

    def test_state_is_none_when_no_match(self):
        coordinator = self._coordinator_with(
            [{"poll_id": 99, "contamination_1": 3, "poll_title": "Other"}]
        )
        sensor = self._make_sensor(coordinator)
        self.assertIsNone(sensor.state)


class TestAsyncSetupEntry(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.sensor_module = load_sensor_module("polleninformation_at_sensor_setup")
        cls.async_setup_entry = staticmethod(cls.sensor_module.async_setup_entry)

        from custom_components.polleninformation_at.const import DOMAIN, POLLEN_TYPES

        cls.DOMAIN = DOMAIN
        cls.POLLEN_TYPES = POLLEN_TYPES

    def _make_config_entry(self):
        entry = MagicMock()
        entry.entry_id = "test-entry-id"
        return entry

    async def test_registers_one_sensor_per_pollen_type(self):
        config_entry = self._make_config_entry()
        async_add_entities = MagicMock()
        hass = MagicMock()
        hass.data = {self.DOMAIN: {config_entry.entry_id: MagicMock()}}

        await self.async_setup_entry(hass, config_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args.args[0]
        self.assertEqual(len(entities), len(self.POLLEN_TYPES))

    async def test_registered_sensors_have_correct_pollen_ids(self):
        config_entry = self._make_config_entry()
        async_add_entities = MagicMock()
        hass = MagicMock()
        hass.data = {self.DOMAIN: {config_entry.entry_id: MagicMock()}}

        await self.async_setup_entry(hass, config_entry, async_add_entities)

        entities = async_add_entities.call_args.args[0]
        registered_pollen_ids = {entity._pollen_id for entity in entities}
        expected_pollen_ids = {item["pollen_id"] for item in self.POLLEN_TYPES.values()}
        self.assertEqual(registered_pollen_ids, expected_pollen_ids)

    async def test_registered_sensors_have_correct_pollen_types(self):
        config_entry = self._make_config_entry()
        async_add_entities = MagicMock()
        hass = MagicMock()
        hass.data = {self.DOMAIN: {config_entry.entry_id: MagicMock()}}

        await self.async_setup_entry(hass, config_entry, async_add_entities)

        entities = async_add_entities.call_args.args[0]
        registered_types = {entity._pollen_type for entity in entities}
        self.assertEqual(registered_types, set(self.POLLEN_TYPES.keys()))


if __name__ == "__main__":
    unittest.main()
