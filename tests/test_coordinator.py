import importlib.util
import importlib
import pathlib
import sys
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

ha_mock = types.ModuleType("homeassistant")
ha_helpers_mock = types.ModuleType("homeassistant.helpers")
ha_helpers_cv_mock = types.ModuleType("homeassistant.helpers.config_validation")
ha_helpers_update_coordinator_mock = types.ModuleType("homeassistant.helpers.update_coordinator")
ha_config_entries_mock = types.ModuleType("homeassistant.config_entries")
ha_core_mock = types.ModuleType("homeassistant.core")


class MockDataUpdateCoordinator:
    def __init__(self, hass, logger, name, update_interval):
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval


class MockUpdateFailed(Exception):
    pass


setattr(ha_helpers_cv_mock, "config_entry_only_config_schema", lambda domain: None)
setattr(ha_helpers_update_coordinator_mock, "DataUpdateCoordinator", MockDataUpdateCoordinator)
setattr(ha_helpers_update_coordinator_mock, "UpdateFailed", MockUpdateFailed)
setattr(ha_config_entries_mock, "ConfigEntry", object)
setattr(ha_core_mock, "HomeAssistant", object)

sys.modules["homeassistant"] = ha_mock
sys.modules["homeassistant.helpers"] = ha_helpers_mock
sys.modules["homeassistant.helpers.config_validation"] = ha_helpers_cv_mock
sys.modules["homeassistant.helpers.update_coordinator"] = ha_helpers_update_coordinator_mock
sys.modules["homeassistant.config_entries"] = ha_config_entries_mock
sys.modules["homeassistant.core"] = ha_core_mock

workspace_root = pathlib.Path(__file__).resolve().parents[1]
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

coordinator_module = importlib.import_module(
    "custom_components.polleninformation_at.coordinator"
)

PollenDataUpdateCoordinator = coordinator_module.PollenDataUpdateCoordinator
UpdateFailed = coordinator_module.UpdateFailed


class TestPollenDataUpdateCoordinator(unittest.IsolatedAsyncioTestCase):
    def _entry(self, data_api_key="data-key", options_api_key=None):
        entry = MagicMock()
        entry.data = {"api_key": data_api_key}
        entry.options = {}
        if options_api_key is not None:
            entry.options["api_key"] = options_api_key
        return entry

    async def test_uses_options_api_key_over_data_api_key(self):
        hass = MagicMock()
        entry = self._entry(data_api_key="data-key", options_api_key="options-key")
        coordinator = PollenDataUpdateCoordinator(hass, entry)

        with patch("custom_components.polleninformation_at.coordinator.PollenApi") as mock_api_cls:
            api_instance = mock_api_cls.return_value
            api_instance.async_update = AsyncMock()
            api_instance.raw_response = {"contamination": []}

            await coordinator._async_update_data()

        used_api_key = mock_api_cls.call_args.args[1]
        self.assertEqual(used_api_key, "options-key")

    async def test_returns_raw_response_on_success(self):
        hass = MagicMock()
        entry = self._entry()
        coordinator = PollenDataUpdateCoordinator(hass, entry)

        with patch("custom_components.polleninformation_at.coordinator.PollenApi") as mock_api_cls:
            api_instance = mock_api_cls.return_value
            api_instance.async_update = AsyncMock()
            api_instance.raw_response = {"contamination": [{"poll_id": 23}]}

            data = await coordinator._async_update_data()

        self.assertEqual(data, {"contamination": [{"poll_id": 23}]})

    async def test_wraps_api_error_in_update_failed(self):
        hass = MagicMock()
        entry = self._entry()
        coordinator = PollenDataUpdateCoordinator(hass, entry)

        with patch("custom_components.polleninformation_at.coordinator.PollenApi") as mock_api_cls:
            api_instance = mock_api_cls.return_value
            api_instance.async_update = AsyncMock(side_effect=RuntimeError("boom"))
            api_instance.raw_response = None

            with self.assertRaises(UpdateFailed):
                await coordinator._async_update_data()


if __name__ == "__main__":
    unittest.main()
