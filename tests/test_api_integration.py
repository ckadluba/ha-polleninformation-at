import importlib.util
from dotenv import load_dotenv
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


API_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "polleninformation_at"
    / "api.py"
)


def load_pollen_api_class():
    api_spec = importlib.util.spec_from_file_location(
        "polleninformation_at_api_integration",
        API_PATH,
    )
    api_module = importlib.util.module_from_spec(api_spec)
    sys.modules[api_spec.name] = api_module
    assert api_spec.loader is not None
    api_spec.loader.exec_module(api_module)
    return getattr(api_module, "PollenApi", api_module.PollenApi)


class TestPollenApiIntegration(unittest.IsolatedAsyncioTestCase):
    async def test_async_update_fetches_live_data(self):
        # Arrange
        if os.getenv("RUN_POLLEN_API_INTEGRATION_TEST") != "1":
            self.skipTest(
                "Set RUN_POLLEN_API_INTEGRATION_TEST=1 to run the live API integration test."
            )

        pollen_api_class = load_pollen_api_class()

        api_key = os.getenv("POLLENINFORMATION_AT_API_KEY")
        if not api_key:
            self.skipTest(
                "Set POLLENINFORMATION_AT_API_KEY to run the live API integration test."
            )
        latitude = float(os.getenv("POLLEN_API_TEST_LATITUDE", "48.2082"))
        longitude = float(os.getenv("POLLEN_API_TEST_LONGITUDE", "16.3738"))
        poll_id = int(os.getenv("POLLEN_API_TEST_POLL_ID", "23"))
        hass = SimpleNamespace(config=SimpleNamespace(latitude=latitude, longitude=longitude))
        api = pollen_api_class(hass, poll_id, api_key)

        # Act
        await api.async_update()

        # Assert
        self.assertIsInstance(api.state, int | type(None))
        self.assertIsInstance(api.poll_title, str | type(None))
        self.assertTrue(
            api.state is not None or api.poll_title is not None,
            "Live API call returned neither state nor poll_title.",
        )
load_dotenv()
