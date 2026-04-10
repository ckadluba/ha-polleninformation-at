import unittest
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
import importlib.util
from unittest.mock import Mock, patch


class StubAioHttpModule:
    class ClientError(Exception):
        pass

    class ClientTimeout:
        def __init__(self, total=None):
            self.total = total

    ClientSession = None


aiohttp_stub = ModuleType("aiohttp")
setattr(aiohttp_stub, "ClientError", StubAioHttpModule.ClientError)
setattr(aiohttp_stub, "ClientTimeout", StubAioHttpModule.ClientTimeout)
setattr(aiohttp_stub, "ClientSession", StubAioHttpModule.ClientSession)


API_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "polleninformation_at"
    / "api.py"
)
sys.modules.setdefault("aiohttp", aiohttp_stub)
API_SPEC = importlib.util.spec_from_file_location("polleninformation_at_api", API_PATH)
assert API_SPEC is not None
API_MODULE = importlib.util.module_from_spec(API_SPEC)
sys.modules[API_SPEC.name] = API_MODULE
assert API_SPEC.loader is not None
API_SPEC.loader.exec_module(API_MODULE)
PollenApi = getattr(API_MODULE, "PollenAPI", API_MODULE.PollenApi)


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    def raise_for_status(self):
        return None

    async def json(self):
        return self._payload


class FakeClientSession:
    def __init__(self, response):
        self._response = response
        self.get = Mock(return_value=response)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None


class TestPollenApi(unittest.IsolatedAsyncioTestCase):
    async def test_async_update_sets_state_and_poll_title(self):
        # Arrange
        hass = SimpleNamespace(config=SimpleNamespace(latitude=48.2082, longitude=16.3738))
        api_key = "test-api-key"
        payload = {
            "contamination": [
                {
                    "pollen_id": 23,
                    "contamination_1": 3,
                    "poll_title": "Pilzsporen (Alternaria)",
                }
            ]
        }
        response = FakeResponse(payload)
        session = FakeClientSession(response)

        # Act
        with patch(
            "polleninformation_at_api.aiohttp.ClientSession",
            return_value=session,
        ):
            api = PollenApi(hass, api_key)
            await api.async_update()

        # Assert
        session.get.assert_called_once()
        self.assertIn(f"apikey={api_key}", session.get.call_args.args[0])
        # The new API only stores the raw response
        self.assertEqual(api._raw_response, payload)

    async def test_async_update_uses_lat_lon_from_config(self):
        # Arrange
        hass = SimpleNamespace(config=SimpleNamespace(latitude=47.0, longitude=15.0))
        api_key = "test-key"
        payload = {"contamination": []}
        response = FakeResponse(payload)
        session = FakeClientSession(response)

        # Act
        with patch("polleninformation_at_api.aiohttp.ClientSession", return_value=session):
            api = PollenApi(hass, api_key)
            await api.async_update()

        # Assert
        session.get.assert_called_once()
        url = session.get.call_args.args[0]
        assert "latitude=47.0" in url
        assert "longitude=15.0" in url

    async def test_async_update_uses_api_key_in_url(self):
        # Arrange
        hass = SimpleNamespace(config=SimpleNamespace(latitude=47.0, longitude=15.0))
        api_key = "my-special-key"
        payload = {"contamination": []}
        response = FakeResponse(payload)
        session = FakeClientSession(response)

        # Act
        with patch("polleninformation_at_api.aiohttp.ClientSession", return_value=session):
            api = PollenApi(hass, api_key)
            await api.async_update()

        # Assert
        session.get.assert_called_once()
        url = session.get.call_args.args[0]
        assert f"apikey={api_key}" in url
