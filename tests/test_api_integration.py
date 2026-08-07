"""
Integration tests for the polleninformation_at API.

Requires POLLENINFORMATION_AT_API_KEY in the environment to run the live
API integration test.
"""

import importlib
import importlib.util
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv

from custom_components.polleninformation_at.const import POLLEN_TYPES

load_dotenv()

# Ensure aiohttp is not mocked or None from previous tests
if "aiohttp" in sys.modules:
    del sys.modules["aiohttp"]

API_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "polleninformation_at"
    / "api.py"
)


def load_pollen_api_class():  # noqa: ANN201
    """
    Load and return the PollenApi class from the local api.py file.

    This dynamically imports the api module from the custom_components
    package path defined by API_PATH and returns the PollenApi attribute.
    Raises ImportError on failure to load the module or required attributes.
    """
    api_spec = importlib.util.spec_from_file_location(
        "polleninformation_at_api_integration",
        API_PATH,
    )
    if api_spec is None:
        msg = f"Could not load spec for {API_PATH}"
        raise ImportError(msg)
    api_module = importlib.util.module_from_spec(api_spec)
    if api_spec.name is None:
        msg = f"api_spec.name is None for {API_PATH}"
        raise ImportError(msg)
    sys.modules[api_spec.name] = api_module
    if api_spec.loader is None:
        msg = f"api_spec.loader is None for {API_PATH}"
        raise ImportError(msg)
    api_spec.loader.exec_module(api_module)
    return getattr(api_module, "PollenApi", api_module.PollenApi)


class TestPollenApiIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for the PollenApi integration."""

    async def test_async_update_fetches_live_data(self) -> None:
        """Test that async_update fetches live data from the pollen API."""
        # Arrange
        api_key = os.getenv("POLLENINFORMATION_AT_API_KEY")
        if not api_key:
            self.skipTest(
                "Set POLLENINFORMATION_AT_API_KEY to run the live API integration test."
            )

        pollen_api_class = load_pollen_api_class()

        latitude = float(os.getenv("POLLEN_API_TEST_LATITUDE", "48.2082"))
        longitude = float(os.getenv("POLLEN_API_TEST_LONGITUDE", "16.3738"))
        hass = SimpleNamespace(
            config=SimpleNamespace(latitude=latitude, longitude=longitude)
        )
        api = pollen_api_class(hass, api_key)

        # Act
        await api.async_update()

        # Assert
        self.assertIsInstance(api._raw_response, dict)  # noqa: PT009, SLF001
        self.assertIn("contamination", api._raw_response)  # noqa: PT009, SLF001

        # Additional asserts for each pollen_id in POLLEN_TYPES
        contamination = api._raw_response.get("contamination", {})  # noqa: SLF001
        contamination_dict = {
            str(item["poll_id"]): item for item in contamination if "poll_id" in item
        }

        for pollen_key, pollen_info in POLLEN_TYPES.items():
            pollen_id = pollen_info["pollen_id"]
            with self.subTest(pollen_id=pollen_id, pollen_key=pollen_key):
                self.assertIn(  # noqa: PT009
                    str(pollen_id),
                    contamination_dict,
                    f"Poll ID {pollen_id} ({pollen_key}) missing in contamination data",
                )


if __name__ == "__main__":
    load_dotenv()
    unittest.main()
