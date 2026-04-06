import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
from types import SimpleNamespace
import importlib.util
import asyncio

# Dynamically import sensor.py
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
PollenSensor = getattr(sensor_module, "PollenSensor")

class TestPollenSensorAsyncUpdate(unittest.IsolatedAsyncioTestCase):
    async def test_async_update_calls_api_with_configured_values(self):
        # Arrange
        latitude = 48.2
        longitude = 16.37
        api_key = "testkey"
        poll_id = 23
        pollen_type = "alternaria"
        pollen_name = "Pilzsporen (Alternaria)"

        # Mock hass with config
        hass = MagicMock()
        hass.config.latitude = latitude
        hass.config.longitude = longitude

        # Patch PollenApi in the sensor module
        with patch.object(sensor_module, "PollenApi") as MockPollenApi:
            mock_api_instance = MockPollenApi.return_value
            mock_api_instance.async_update = AsyncMock()
            mock_api_instance.state = 1
            mock_api_instance.poll_title = "TestTitle"

            sensor = PollenSensor(hass, poll_id, pollen_type, pollen_name, api_key)
            # Act
            await sensor.async_update()

            # Assert
            MockPollenApi.assert_called_once_with(hass, poll_id, api_key)
            mock_api_instance.async_update.assert_awaited_once()
            self.assertEqual(sensor._state, 1)
            self.assertEqual(sensor._poll_title, "TestTitle")

if __name__ == "__main__":
    unittest.main()
