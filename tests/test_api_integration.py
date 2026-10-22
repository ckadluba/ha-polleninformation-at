import importlib
import importlib.util
import os
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from dotenv import load_dotenv

# Ensure aiohttp is not mocked or None from previous tests
if "aiohttp" in sys.modules:
    del sys.modules["aiohttp"]

import aiohttp

API_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "polleninformation_at"
    / "api.py"
)


def ensure_aiohttp_client_helper() -> None:
    """
    Make sure `homeassistant.helpers.aiohttp_client` can be imported.

    The API module imports the helper at import time. Use the real helper when
    it is available and fall back to a stub otherwise, so the live test also
    runs without a full Home Assistant installation.
    """
    if "homeassistant.helpers.aiohttp_client" in sys.modules:
        return

    try:
        importlib.import_module("homeassistant.helpers.aiohttp_client")
    except ImportError:
        for module_name in [
            name
            for name in sys.modules
            if name == "homeassistant" or name.startswith("homeassistant.")
        ]:
            del sys.modules[module_name]

        stub = ModuleType("homeassistant.helpers.aiohttp_client")
        stub.async_get_clientsession = lambda _hass: None
        sys.modules["homeassistant.helpers.aiohttp_client"] = stub


def load_pollen_api_module():
    """Load the API module so its shared session helper can be patched."""
    ensure_aiohttp_client_helper()

    api_spec = importlib.util.spec_from_file_location(
        "polleninformation_at_api_integration",
        API_PATH,
    )
    if api_spec is None:
        raise ImportError(f"Could not load spec for {API_PATH}")
    api_module = importlib.util.module_from_spec(api_spec)
    if api_spec.name is None:
        raise ImportError(f"api_spec.name is None for {API_PATH}")
    sys.modules[api_spec.name] = api_module
    if api_spec.loader is None:
        raise ImportError(f"api_spec.loader is None for {API_PATH}")
    api_spec.loader.exec_module(api_module)
    return api_module


class TestPollenApiIntegration(unittest.IsolatedAsyncioTestCase):
    async def test_async_update_fetches_live_data(self) -> None:
        # Arrange
        api_key = os.getenv("POLLENINFORMATION_AT_API_KEY")
        if not api_key:
            self.skipTest(
                "Set POLLENINFORMATION_AT_API_KEY to run the live API integration test."
            )

        api_module = load_pollen_api_module()
        pollen_api_class = getattr(api_module, "PollenApi", api_module.PollenApi)

        latitude = float(os.getenv("POLLEN_API_TEST_LATITUDE", "48.2082"))
        longitude = float(os.getenv("POLLEN_API_TEST_LONGITUDE", "16.3738"))
        hass = SimpleNamespace(
            config=SimpleNamespace(
                language="de", latitude=latitude, longitude=longitude
            )
        )
        api = pollen_api_class(hass, api_key)

        # Act
        async with aiohttp.ClientSession() as session:
            with patch.object(
                api_module, "async_get_clientsession", return_value=session
            ):
                await api.async_update()

        # Assert
        self.assertIsInstance(api._raw_response, dict)
        self.assertIn("contamination", api._raw_response)

        # Additional asserts for each pollen_id in POLLEN_TYPES
        from custom_components.polleninformation_at.const import POLLEN_TYPES

        contamination = api._raw_response.get("contamination", {})
        contamination_dict = {
            str(item["poll_id"]): item for item in contamination if "poll_id" in item
        }

        for pollen_key, pollen_info in POLLEN_TYPES.items():
            pollen_id = pollen_info["pollen_id"]
            with self.subTest(pollen_id=pollen_id, pollen_key=pollen_key):
                self.assertIn(
                    str(pollen_id),
                    contamination_dict,
                    f"Poll ID {pollen_id} ({pollen_key}) missing in contamination data",
                )

        # Additional asserts for allergyrisk
        allergyrisk = api._raw_response.get("allergyrisk", {})
        self.assertIn("allergyrisk_1", allergyrisk)


if __name__ == "__main__":
    load_dotenv()
    unittest.main()
