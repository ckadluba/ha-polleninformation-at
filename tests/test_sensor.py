"""Unit tests for the polleninformation_at sensor integration."""

import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import MagicMock

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


class MockSensorStateClass:
    """Mock sensor state class constants."""

    MEASUREMENT = "measurement"


class MockSensorEntity:
    """Mock sensor entity class."""

    @property
    def state(self) -> object:
        """Return the current state of the sensor entity."""
        native_value = getattr(self, "native_value", None)
        return native_value() if callable(native_value) else native_value


class MockSensorEntityDescription:
    """Mock sensor entity description class."""

    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003, ARG002
        for key, value in kwargs.items():
            setattr(self, key, value)


class MockCoordinatorEntity:
    """Mock coordinator entity class."""

    def __init__(self, coordinator: object, *_args: object, **_kwargs: object) -> None:
        self.coordinator = coordinator


class MockDataUpdateCoordinator:  # noqa: D101
    def __init__(self, *_args: object, **_kwargs: object) -> None:
        pass


class MockDeviceInfo:  # noqa: D101
    def __init__(self, *_args: object, **_kwargs: object) -> None:
        pass


ha_components_sensor_mock.SensorEntity = MockSensorEntity  # type: ignore[attr-defined]
ha_components_sensor_mock.SensorEntityDescription = (  # type: ignore[attr-defined]
    MockSensorEntityDescription
)
ha_components_sensor_mock.SensorStateClass = MockSensorStateClass  # type: ignore[attr-defined]
ha_helpers_cv_mock.config_entry_only_config_schema = lambda domain: None  # type: ignore[attr-defined]  # noqa: ARG005
ha_helpers_update_coordinator_mock.DataUpdateCoordinator = MockDataUpdateCoordinator  # type: ignore[attr-defined]
ha_helpers_update_coordinator_mock.CoordinatorEntity = MockCoordinatorEntity  # type: ignore[attr-defined]
ha_helpers_update_coordinator_mock.UpdateFailed = Exception  # type: ignore[attr-defined]
ha_helpers_device_registry_mock.DeviceEntryType = type(  # type: ignore[attr-defined]
    "DeviceEntryType",
    (),
    {"SERVICE": "service"},
)
ha_helpers_device_registry_mock.DeviceInfo = MockDeviceInfo  # type: ignore[attr-defined]
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

from custom_components.polleninformation_at.const import (  # noqa: E402
    ALLERGYRISK_TYPE,
)


def load_sensor_module(module_name: str) -> types.ModuleType:  # noqa: ANN201, D103
    sensor_path = (
        workspace_root / "custom_components" / "polleninformation_at" / "sensor.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, sensor_path)
    assert spec is not None  # noqa: S101
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None  # noqa: S101
    spec.loader.exec_module(module)
    return module


class TestCoordinatorSensorLogic(unittest.TestCase):
    """Tests for behavior shared by all coordinator-backed sensors."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.sensor_module = load_sensor_module("polleninformation_at_sensor_base")

        class DummyExtractor:
            def __init__(self, payload):
                self.payload = payload

            def get_native_value(self):
                return self.payload.get("test_series_1") if self.payload else None

            def get_extra_state_attributes(self):
                return (
                    {"poll_title": self.payload.get("poll_title")}
                    if self.payload
                    else {}
                )

        class ConcreteCoordinatorSensor(cls.sensor_module.CoordinatorSensor):
            pass

        cls.DummyExtractor = DummyExtractor
        cls.ConcreteCoordinatorSensor = ConcreteCoordinatorSensor

    def _make_sensor(
        self, data: dict | None, contamination_type: str = "custom_type"
    ) -> object:
        coordinator = MagicMock()
        coordinator.data = data
        return self.ConcreteCoordinatorSensor(
            coordinator,
            self.DummyExtractor(data or {}),
            contamination_type,
        )

    def test_native_value_uses_data_extractor(self) -> None:
        sensor = self._make_sensor({"test_series_1": 4})
        self.assertEqual(sensor.native_value, 4)

    def test_native_value_returns_none_for_empty_entry(self) -> None:
        sensor = self._make_sensor({})
        self.assertIsNone(sensor.native_value)

    def test_extra_state_attributes_uses_data_extractor(self) -> None:
        sensor = self._make_sensor({"poll_title": "Test contamination"})
        self.assertEqual(
            sensor.extra_state_attributes, {"poll_title": "Test contamination"}
        )

    def test_initializes_common_entity_attributes(self) -> None:
        sensor = self._make_sensor(None, contamination_type="custom_type")

        self.assertEqual(sensor._attr_unique_id, "polleninformation_at_custom_type")
        self.assertEqual(sensor.entity_id, "sensor.polleninformation_at_custom_type")
        self.assertEqual(sensor._attr_icon, "mdi:flower-pollen")
        self.assertEqual(sensor._attr_state_class, "measurement")
        self.assertEqual(sensor._attr_native_unit_of_measurement, "level")
        self.assertTrue(sensor._attr_has_entity_name)


class TestPollenDataExtractorLogic(unittest.TestCase):
    """Tests for the pollen data extraction logic."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.sensor_module = load_sensor_module("polleninformation_at_data_extractor")
        cls.PollenDataExtractor = cls.sensor_module.PollenDataExtractor

    def test_native_value_returns_matching_pollen_level(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {
            "contamination": [
                {"poll_id": 23, "contamination_1": 4, "poll_title": "Alternaria"}
            ]
        }
        extractor = self.PollenDataExtractor(coordinator, 23)
        self.assertEqual(extractor.get_native_value(), 4)

    def test_native_value_returns_none_when_no_matching_pollen(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {"contamination": [{"poll_id": 99, "contamination_1": 4}]}
        extractor = self.PollenDataExtractor(coordinator, 23)
        self.assertIsNone(extractor.get_native_value())

    def test_native_value_returns_none_without_response(self) -> None:
        coordinator = MagicMock()
        coordinator.data = None
        extractor = self.PollenDataExtractor(coordinator, 23)
        self.assertIsNone(extractor.get_native_value())

    def test_extra_state_attributes_is_empty(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {"contamination": [{"poll_id": 23, "contamination_1": 5}]}
        extractor = self.PollenDataExtractor(coordinator, 23)
        self.assertEqual(extractor.get_extra_state_attributes(), {})


class TestAllergyriskDataExtractorLogic(unittest.TestCase):
    """Tests for allergyrisk extraction logic."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.sensor_module = load_sensor_module(
            "polleninformation_at_allergyrisk_extractor"
        )
        cls.AllergyriskDataExtractor = cls.sensor_module.AllergyriskDataExtractor

    def test_native_value_returns_allergy_risk_level(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {
            "allergyrisk": {"allergyrisk_1": 3, "poll_title": "Allergierisiko"}
        }
        extractor = self.AllergyriskDataExtractor(coordinator)
        self.assertEqual(extractor.get_native_value(), 3)

    def test_native_value_returns_none_when_allergyrisk_is_missing(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {"contamination": []}
        extractor = self.AllergyriskDataExtractor(coordinator)
        self.assertIsNone(extractor.get_native_value())

    def test_native_value_returns_none_when_response_is_missing(self) -> None:
        coordinator = MagicMock()
        coordinator.data = None
        extractor = self.AllergyriskDataExtractor(coordinator)
        self.assertIsNone(extractor.get_native_value())

    def test_extra_state_attributes_is_empty(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {"allergyrisk": {"allergyrisk_1": 2}}
        extractor = self.AllergyriskDataExtractor(coordinator)
        self.assertEqual(extractor.get_extra_state_attributes(), {})


class TestPollenSensorLogic(unittest.TestCase):
    """Tests for the pollen sensor logic."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.sensor_module = load_sensor_module("polleninformation_at_sensor")
        cls.PollenSensor = cls.sensor_module.PollenSensor

    def _make_sensor(
        self, coordinator: object, pollen_type: str = "alternaria", pollen_id: int = 23
    ):
        return self.PollenSensor(coordinator, pollen_type, pollen_id)

    def test_native_value_returns_contamination_level(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {
            "contamination": [
                {"poll_id": 23, "contamination_1": 5, "poll_title": "Alternaria"}
            ]
        }
        sensor = self._make_sensor(coordinator)
        self.assertIsInstance(
            sensor.data_extractor, self.sensor_module.PollenDataExtractor
        )
        self.assertEqual(sensor.native_value, 5)
        self.assertEqual(sensor.state, 5)

    def test_native_value_returns_none_when_pollen_id_not_found(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {
            "contamination": [
                {"poll_id": 99, "contamination_1": 3, "poll_title": "Other"}
            ]
        }
        sensor = self._make_sensor(coordinator)
        self.assertIsNone(sensor.native_value)

    def test_attr_unique_id(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(coordinator, pollen_type="secale")
        self.assertEqual(sensor._attr_unique_id, "polleninformation_at_secale")

    def test_entity_id_follows_stable_integration_pattern(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(coordinator, pollen_type="betula")
        self.assertEqual(sensor.entity_id, "sensor.polleninformation_at_betula")

    def test_attr_icon(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor._attr_icon, "mdi:flower-pollen")


class TestAllergyriskSensorLogic(unittest.TestCase):
    """Tests for the allergy risk sensor logic."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.sensor_module = load_sensor_module(
            "polleninformation_at_sensor_allergyrisk"
        )
        cls.AllergyriskSensor = cls.sensor_module.AllergyriskSensor

    def _make_sensor(self, data: object) -> object:
        coordinator = MagicMock()
        coordinator.data = data
        return self.AllergyriskSensor(coordinator)

    def test_native_value_returns_allergy_risk_level(self) -> None:
        sensor = self._make_sensor(
            {"allergyrisk": {"allergyrisk_1": 3, "poll_title": "Allergierisiko"}}
        )
        self.assertEqual(sensor.native_value, 3)

    def test_native_value_returns_none_when_no_data(self) -> None:
        sensor = self._make_sensor(None)
        self.assertIsNone(sensor.native_value)

    def test_initializes_allergy_risk_identity(self) -> None:
        sensor = self._make_sensor({})
        self.assertEqual(sensor.name_suffix, ALLERGYRISK_TYPE)
        self.assertEqual(sensor._attr_unique_id, "polleninformation_at_allergyrisk")
        self.assertEqual(sensor.entity_id, "sensor.polleninformation_at_allergyrisk")


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

    async def test_registers_one_pollensensor_per_pollen_type(self) -> None:
        config_entry = self._make_config_entry()
        async_add_entities = MagicMock()
        hass = MagicMock()
        hass.data = {self.DOMAIN: {config_entry.entry_id: MagicMock()}}

        await self.async_setup_entry(hass, config_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args.args[0]
        pollensensor_entities = [
            entity
            for entity in entities
            if isinstance(entity, self.sensor_module.PollenSensor)
        ]
        self.assertEqual(len(pollensensor_entities), len(self.POLLEN_TYPES))

    async def test_registered_pollensensors_have_correct_pollen_ids(self) -> None:
        config_entry = self._make_config_entry()
        async_add_entities = MagicMock()
        hass = MagicMock()
        hass.data = {self.DOMAIN: {config_entry.entry_id: MagicMock()}}

        await self.async_setup_entry(hass, config_entry, async_add_entities)

        entities = async_add_entities.call_args.args[0]
        pollensensor_entities = [
            entity
            for entity in entities
            if isinstance(entity, self.sensor_module.PollenSensor)
        ]
        registered_pollen_ids = {entity._pollen_id for entity in pollensensor_entities}  # noqa: SLF001
        expected_pollen_ids = {item["pollen_id"] for item in self.POLLEN_TYPES.values()}
        self.assertEqual(registered_pollen_ids, expected_pollen_ids)

    async def test_registers_one_allergyrisk_sensor(self) -> None:
        config_entry = self._make_config_entry()
        async_add_entities = MagicMock()
        hass = MagicMock()
        hass.data = {self.DOMAIN: {config_entry.entry_id: MagicMock()}}

        await self.async_setup_entry(hass, config_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args.args[0]
        allergyrisksensor_entities = [
            entity
            for entity in entities
            if isinstance(entity, self.sensor_module.AllergyriskSensor)
        ]
        self.assertEqual(len(allergyrisksensor_entities), 1)


if __name__ == "__main__":
    unittest.main()
