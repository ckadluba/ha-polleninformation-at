"""Unit tests for the polleninformation_at sensor integration."""

import importlib.util
import pathlib
import sys
import types
import unittest
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

if TYPE_CHECKING:
    from custom_components.polleninformation_at.sensor import (
        AllergyriskSensor,
        ContaminationSensor,
        PollenSensor,
    )

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
        """Initialize the mock sensor entity description."""
        for key, value in kwargs.items():
            setattr(self, key, value)


class MockCoordinatorEntity:
    """Mock coordinator entity class."""

    def __init__(self, coordinator: object, *_args: object, **_kwargs: object) -> None:
        """Initialize the mock coordinator entity."""
        self.coordinator = coordinator


class MockDataUpdateCoordinator:  # noqa: D101
    def __init__(self, *_args: object, **_kwargs: object) -> None:
        """Initialize the mock data update coordinator."""


class MockDeviceInfo:  # noqa: D101
    def __init__(self, *_args: object, **_kwargs: object) -> None:
        """Initialize the mock device info."""


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

sys.modules["homeassistant"] = ha_mock
sys.modules["homeassistant.components"] = ha_components_mock
sys.modules["homeassistant.components.sensor"] = ha_components_sensor_mock
sys.modules["homeassistant.helpers"] = ha_helpers_mock
sys.modules["homeassistant.helpers.config_validation"] = ha_helpers_cv_mock
sys.modules["homeassistant.helpers.update_coordinator"] = (
    ha_helpers_update_coordinator_mock
)
sys.modules["homeassistant.helpers.device_registry"] = ha_helpers_device_registry_mock
sys.modules["homeassistant.helpers.entity_platform"] = ha_helpers_entity_platform_mock
sys.modules["homeassistant.config_entries"] = ha_config_entries_mock
sys.modules["homeassistant.core"] = ha_core_mock

workspace_root = pathlib.Path(__file__).resolve().parents[1]
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from custom_components.polleninformation_at.const import (  # noqa: E402
    ALLERGYRISK_SERIES_NAME,
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


class TestContaminationSensorLogic(unittest.TestCase):
    """Tests for behavior shared by all contamination sensors."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.sensor_module = load_sensor_module("polleninformation_at_sensor_base")

        class ConcreteContaminationSensor(cls.sensor_module.ContaminationSensor):
            def _get_contamination_entry(self) -> dict | None:
                return self.coordinator.data

        cls.ConcreteContaminationSensor = ConcreteContaminationSensor

    def _make_sensor(
        self,
        data: dict | None,
        contamination_type: str = "test_contamination",
        series_name: str = "test_series",
    ) -> ContaminationSensor:
        coordinator = MagicMock()
        coordinator.data = data
        return self.ConcreteContaminationSensor(
            coordinator, contamination_type, series_name
        )

    def test_get_contamination_entry_is_abstract(self) -> None:
        method = self.sensor_module.ContaminationSensor._get_contamination_entry
        self.assertTrue(method.__isabstractmethod__)

    def test_native_value_uses_configured_series_name(self) -> None:
        sensor = self._make_sensor({"test_series_1": 4})
        self.assertEqual(sensor.native_value, 4)

    def test_native_value_returns_none_for_empty_entry(self) -> None:
        sensor = self._make_sensor({})
        self.assertIsNone(sensor.native_value)

    def test_extra_state_attributes_returns_poll_title(self) -> None:
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


class TestPollenSensorLogic(unittest.IsolatedAsyncioTestCase):
    """Tests for the pollen sensor logic."""

    @classmethod
    def setUpClass(cls) -> None:  # noqa: D102
        cls.sensor_module = load_sensor_module("polleninformation_at_sensor")
        cls.PollenSensor = cls.sensor_module.PollenSensor

        async def async_update(self) -> None:  # noqa: ANN001
            await self.coordinator.async_request_refresh()

        cls.PollenSensor.async_update = async_update

    def _make_sensor(
        self,
        coordinator: object,
        pollen_type: str = "alternaria",
        pollen_id: int = 23,
    ) -> PollenSensor:
        return self.PollenSensor(coordinator, pollen_type, pollen_id)

    def _coordinator_with(self, entries) -> MagicMock:  # noqa: ANN001
        coordinator = MagicMock()
        coordinator.data = {"contamination": entries}
        return coordinator

    async def test_async_update_requests_refresh_from_coordinator(self) -> None:  # noqa: D102
        coordinator = self._coordinator_with(
            [{"poll_id": 23, "contamination_1": 1, "poll_title": "TestTitle"}]
        )
        coordinator.async_request_refresh = AsyncMock()

        sensor = self._make_sensor(coordinator)
        await sensor.async_update()

        coordinator.async_request_refresh.assert_awaited_once()
        self.assertEqual(sensor.state, 1)  # noqa: PT009

    def test_native_value_returns_contamination_level(self) -> None:
        coordinator = self._coordinator_with(
            [{"poll_id": 23, "contamination_1": 5, "poll_title": "Alternaria"}]
        )
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.native_value, 5)

    def test_native_value_returns_none_when_no_data(self) -> None:
        coordinator = MagicMock()
        coordinator.data = None
        sensor = self._make_sensor(coordinator)
        self.assertIsNone(sensor.native_value)

    def test_native_value_returns_none_when_pollen_id_not_found(self) -> None:
        coordinator = self._coordinator_with(
            [{"poll_id": 99, "contamination_1": 3, "poll_title": "Other"}]
        )
        sensor = self._make_sensor(coordinator)
        self.assertIsNone(sensor.native_value)

    def test_native_value_returns_none_when_contamination_missing(self) -> None:
        coordinator = self._coordinator_with(
            [{"poll_id": 23, "poll_title": "Alternaria"}]
        )
        sensor = self._make_sensor(coordinator)
        self.assertIsNone(sensor.native_value)

    def test_native_value_returns_zero(self) -> None:
        coordinator = self._coordinator_with(
            [{"poll_id": 23, "contamination_1": 0, "poll_title": "Alternaria"}]
        )
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.native_value, 0)

    def test_extra_state_attributes_returns_poll_title(self) -> None:
        coordinator = self._coordinator_with(
            [{"poll_id": 23, "contamination_1": 2, "poll_title": "TestTitle"}]
        )
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.extra_state_attributes, {"poll_title": "TestTitle"})

    def test_extra_state_attributes_returns_empty_dict_when_no_data(self) -> None:
        coordinator = MagicMock()
        coordinator.data = None
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.extra_state_attributes, {})

    def test_extra_state_attributes_returns_empty_dict_when_pollen_id_not_found(
        self,
    ) -> None:
        coordinator = self._coordinator_with(
            [{"poll_id": 99, "contamination_1": 1, "poll_title": "Other"}]
        )
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.extra_state_attributes, {})

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

    def test_rumex_sensor_attributes(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(coordinator, pollen_type="rumex", pollen_id=356)
        self.assertEqual(sensor._attr_unique_id, "polleninformation_at_rumex")

    def test_castanea_sensor_attributes(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(
            coordinator,
            pollen_type="castanea",
            pollen_id=326,
        )
        self.assertEqual(sensor._attr_unique_id, "polleninformation_at_castanea")

    def test_plantago_sensor_attributes(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(
            coordinator,
            pollen_type="plantago",
            pollen_id=320,
        )
        self.assertEqual(sensor._attr_unique_id, "polleninformation_at_plantago")

    def test_ailanthus_altissima_sensor_attributes(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(
            coordinator, pollen_type="ailanthus_altissima", pollen_id=1107
        )
        self.assertEqual(
            sensor._attr_unique_id, "polleninformation_at_ailanthus_altissima"
        )

    def test_tilia_sensor_attributes(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(coordinator, pollen_type="tilia", pollen_id=355)
        self.assertEqual(sensor._attr_unique_id, "polleninformation_at_tilia")

    def test_attr_icon(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor._attr_icon, "mdi:flower-pollen")

    def test_attr_state_class(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor._attr_state_class, "measurement")

    def test_attr_native_unit_of_measurement(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor._attr_native_unit_of_measurement, "level")

    def test_attr_has_entity_name(self) -> None:
        coordinator = MagicMock()
        coordinator.data = {}
        sensor = self._make_sensor(coordinator)
        self.assertTrue(sensor._attr_has_entity_name)

    def test_state_equals_native_value(self) -> None:
        coordinator = self._coordinator_with(
            [{"poll_id": 23, "contamination_1": 7, "poll_title": "Alternaria"}]
        )
        sensor = self._make_sensor(coordinator)
        self.assertEqual(sensor.state, sensor.native_value)

    def test_state_is_none_when_no_match(self) -> None:
        coordinator = self._coordinator_with(
            [{"poll_id": 99, "contamination_1": 3, "poll_title": "Other"}]
        )
        sensor = self._make_sensor(coordinator)
        self.assertIsNone(sensor.state)


class TestAllergyriskSensorLogic(unittest.TestCase):
    """Tests for the allergy risk sensor logic."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.sensor_module = load_sensor_module("polleninformation_at_sensor_allergyrisk")
        cls.AllergyriskSensor = cls.sensor_module.AllergyriskSensor

    def _make_sensor(self, data: object) -> AllergyriskSensor:
        coordinator = MagicMock()
        coordinator.data = data
        return self.AllergyriskSensor(coordinator, ALLERGYRISK_TYPE)

    def test_native_value_returns_allergy_risk_level(self) -> None:
        sensor = self._make_sensor(
            {"allergyrisk": {"allergyrisk_1": 3, "poll_title": "Allergierisiko"}}
        )
        self.assertEqual(sensor.native_value, 3)

    def test_native_value_returns_zero(self) -> None:
        sensor = self._make_sensor({"allergyrisk": {"allergyrisk_1": 0}})
        self.assertEqual(sensor.native_value, 0)

    def test_native_value_returns_none_when_no_data(self) -> None:
        sensor = self._make_sensor(None)
        self.assertIsNone(sensor.native_value)

    def test_native_value_returns_none_when_allergy_risk_missing(self) -> None:
        sensor = self._make_sensor({"contamination": []})
        self.assertIsNone(sensor.native_value)

    def test_native_value_returns_none_when_allergy_risk_is_not_dict(self) -> None:
        sensor = self._make_sensor({"allergyrisk": []})
        self.assertIsNone(sensor.native_value)

    def test_native_value_returns_none_when_level_missing(self) -> None:
        sensor = self._make_sensor(
            {"allergyrisk": {"poll_title": "Allergierisiko"}}
        )
        self.assertIsNone(sensor.native_value)

    def test_extra_state_attributes_returns_poll_title(self) -> None:
        sensor = self._make_sensor(
            {"allergyrisk": {"allergyrisk_1": 2, "poll_title": "Allergierisiko"}}
        )
        self.assertEqual(
            sensor.extra_state_attributes, {"poll_title": "Allergierisiko"}
        )

    def test_extra_state_attributes_returns_empty_dict_when_no_data(self) -> None:
        sensor = self._make_sensor(None)
        self.assertEqual(sensor.extra_state_attributes, {})

    def test_initializes_allergy_risk_identity(self) -> None:
        sensor = self._make_sensor({})
        self.assertEqual(sensor.contamination_type, ALLERGYRISK_TYPE)
        self.assertEqual(sensor.series_name, ALLERGYRISK_SERIES_NAME)
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

    async def test_registered_pollensensors_have_correct_contamination_types(
        self,
    ) -> None:
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
        registered_types = {
            entity.contamination_type for entity in pollensensor_entities
        }
        self.assertEqual(registered_types, set(self.POLLEN_TYPES.keys()))

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

    async def test_registered_allergyrisk_sensor_has_correct_contamination_types(
        self,
    ) -> None:
        config_entry = self._make_config_entry()
        async_add_entities = MagicMock()
        hass = MagicMock()
        hass.data = {self.DOMAIN: {config_entry.entry_id: MagicMock()}}

        await self.async_setup_entry(hass, config_entry, async_add_entities)

        entities = async_add_entities.call_args.args[0]
        allergyrisksensor_entities = [
            entity
            for entity in entities
            if isinstance(entity, self.sensor_module.AllergyriskSensor)
        ]
        self.assertEqual(
            allergyrisksensor_entities[0].contamination_type, ALLERGYRISK_TYPE
        )


if __name__ == "__main__":
    unittest.main()
