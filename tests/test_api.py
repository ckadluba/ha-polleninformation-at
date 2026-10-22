"""
Tests for the polleninformation_at API module.

These tests exercise the PollenApi integration's HTTP handling and
logging behavior.
"""

import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch


class StubAioHttpModule:
    """
    A simple aiohttp stub used for testing.

    This stub provides the minimal classes and attributes required by the
    tested module without importing the real aiohttp package.
    """

    class ClientError(Exception):  # noqa: D106
        pass

    class ClientResponseError(ClientError):  # noqa: D106
        def __init__(self, status: int = 0, message: str = "") -> None:
            """
            Initialize a ClientResponseError stub.

            Args:
                status: HTTP status code.
                message: Error message.

            """
            super().__init__(message)
            self.status = status
            self.message = message

    class ClientConnectorError(ClientError):  # noqa: D106
        pass

    class ContentTypeError(ClientResponseError):  # noqa: D106
        pass

    class ClientTimeout:  # noqa: D106
        def __init__(self, total: float | None = None) -> None:
            """
            Initialize a ClientTimeout stub with an optional total timeout.

            Args:
                total: Total timeout value in seconds or None.

            """
            self.total = total

    ClientSession = None


aiohttp_stub = ModuleType("aiohttp")
aiohttp_stub.ClientError = StubAioHttpModule.ClientError  # type: ignore[attr-defined]
aiohttp_stub.ClientResponseError = StubAioHttpModule.ClientResponseError  # type: ignore[attr-defined]
aiohttp_stub.ClientConnectorError = StubAioHttpModule.ClientConnectorError  # type: ignore[attr-defined]
aiohttp_stub.ContentTypeError = StubAioHttpModule.ContentTypeError  # type: ignore[attr-defined]
aiohttp_stub.ClientTimeout = StubAioHttpModule.ClientTimeout  # type: ignore[attr-defined]
aiohttp_stub.ClientSession = StubAioHttpModule.ClientSession  # type: ignore[attr-defined]

aiohttp_client_stub = ModuleType("homeassistant.helpers.aiohttp_client")


def unpatched_get_clientsession(_hass):
    """
    Fail when the shared session helper is used without being patched.

    Args:
        _hass: Home Assistant instance.

    """
    msg = "async_get_clientsession must be patched in tests"
    raise AssertionError(msg)


aiohttp_client_stub.async_get_clientsession = unpatched_get_clientsession  # type: ignore[attr-defined]

API_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "polleninformation_at"
    / "api.py"
)
sys.modules.setdefault("aiohttp", aiohttp_stub)
sys.modules.setdefault("homeassistant.helpers.aiohttp_client", aiohttp_client_stub)
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


class FakeErrorResponse(FakeResponse):
    def raise_for_status(self):
        raise API_MODULE.aiohttp.ClientError("Boom")


class FakeHttpErrorResponse(FakeResponse):
    def __init__(self, status, message):
        super().__init__({})
        self._status = status
        self._message = message

    def raise_for_status(self):
        raise API_MODULE.aiohttp.ClientResponseError(self._status, self._message)


class FakeNetworkErrorResponse(FakeResponse):
    def raise_for_status(self):
        raise API_MODULE.aiohttp.ClientConnectorError("Cannot connect to host")


class FakeInvalidJsonResponse(FakeResponse):
    async def json(self):
        raise ValueError("Expecting value: line 1 column 1 (char 0)")


class FakeContentTypeErrorResponse(FakeResponse):
    def raise_for_status(self):
        raise API_MODULE.aiohttp.ContentTypeError(
            200, "Attempt to decode JSON with unexpected mimetype: text/html"
        )


class FakeTimeoutSession:
    def get(self, url, **kwargs):
        raise TimeoutError


class FakeClientSession:
    def __init__(self, response):
        self._response = response
        self.get = Mock(return_value=response)


class TestPollenApi(unittest.IsolatedAsyncioTestCase):
    def test_init_sets_supported_system_language_or_english_fallback(self):
        for system_language, expected_language in (
            ("de", "de"),
            ("en", "en"),
            ("fr", "en"),
        ):
            with self.subTest(system_language=system_language):
                hass = SimpleNamespace(
                    config=SimpleNamespace(
                        language=system_language, latitude=48.2082, longitude=16.3738
                    )
                )

                api = PollenApi(hass, "test-api-key")

                self.assertEqual(api._lang, expected_language)
                self.assertIn(f"lang={expected_language}", api._url)

    async def test_async_update_sets_state_and_poll_title(self):
        # Arrange
        hass = SimpleNamespace(
            config=SimpleNamespace(language="de", latitude=48.2082, longitude=16.3738)
        )
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
            "polleninformation_at_api.async_get_clientsession",
            return_value=session,
        ):
            api = PollenApi(hass, api_key)
            await api.async_update()

        # Assert
        session.get.assert_called_once()
        self.assertIn(f"apikey={api_key}", session.get.call_args.args[0])
        # The new API only stores the raw response
        self.assertEqual(api._raw_response, payload)

    async def test_async_update_uses_shared_home_assistant_session(self):
        # Arrange
        hass = SimpleNamespace(
            config=SimpleNamespace(language="de", latitude=48.2082, longitude=16.3738)
        )
        payload = {"contamination": []}
        response = FakeResponse(payload)
        session = FakeClientSession(response)
        requested_with = []

        def fake_get_clientsession(requested_hass) -> FakeClientSession:
            requested_with.append(requested_hass)
            return session

        def fail_client_session(*_args, **_kwargs) -> None:
            msg = "A dedicated aiohttp.ClientSession must not be created"
            raise AssertionError(msg)

        api = PollenApi(hass, "test-api-key")

        # Act
        with (
            patch(
                "polleninformation_at_api.async_get_clientsession",
                fake_get_clientsession,
            ),
            patch(
                "polleninformation_at_api.aiohttp.ClientSession",
                fail_client_session,
            ),
        ):
            await api.async_update()

        # Assert
        self.assertEqual(requested_with, [hass])
        session.get.assert_called_once()

    async def test_async_update_uses_lat_lon_from_config(self):
        # Arrange
        hass = SimpleNamespace(
            config=SimpleNamespace(language="de", latitude=47.0, longitude=15.0)
        )
        api_key = "test-key"
        payload = {"contamination": []}
        response = FakeResponse(payload)
        session = FakeClientSession(response)

        # Act
        with patch(
            "polleninformation_at_api.async_get_clientsession", return_value=session
        ):
            api = PollenApi(hass, api_key)
            await api.async_update()

        # Assert
        session.get.assert_called_once()
        url = session.get.call_args.args[0]
        assert "latitude=47.0" in url
        assert "longitude=15.0" in url

    async def test_async_update_uses_api_key_in_url(self):
        # Arrange
        hass = SimpleNamespace(
            config=SimpleNamespace(language="de", latitude=47.0, longitude=15.0)
        )
        api_key = "my-special-key"
        payload = {"contamination": []}
        response = FakeResponse(payload)
        session = FakeClientSession(response)

        # Act
        with patch(
            "polleninformation_at_api.async_get_clientsession", return_value=session
        ):
            api = PollenApi(hass, api_key)
            await api.async_update()

        # Assert
        session.get.assert_called_once()
        url = session.get.call_args.args[0]
        assert f"apikey={api_key}" in url

    async def test_async_update_does_not_log_api_key(self):
        # Arrange
        hass = SimpleNamespace(
            config=SimpleNamespace(language="de", latitude=48.2082, longitude=16.3738)
        )
        api_key = "secret-api-key"
        payload = {"contamination": []}
        response = FakeResponse(payload)
        session = FakeClientSession(response)

        # Act
        with (
            patch(
                "polleninformation_at_api.async_get_clientsession", return_value=session
            ),
            self.assertLogs(API_MODULE.__name__, level="DEBUG") as logs,
        ):
            api = PollenApi(hass, api_key)
            await api.async_update()

        # Assert
        log_text = "\n".join(logs.output)
        self.assertNotIn(api_key, log_text)
        self.assertIn("<REDACTED>", log_text)

    async def test_async_update_uses_actual_url_parameters(self):
        # Arrange
        latitude = 47.0
        longitude = 15.0
        api_key = "my-special-key"
        hass = SimpleNamespace(
            config=SimpleNamespace(
                language="de", latitude=latitude, longitude=longitude
            )
        )
        payload = {"contamination": []}
        response = FakeResponse(payload)
        session = FakeClientSession(response)

        # Act
        with patch(
            "polleninformation_at_api.async_get_clientsession", return_value=session
        ):
            api = PollenApi(hass, api_key)
            await api.async_update()

        # Assert
        session.get.assert_called_once()
        url = session.get.call_args.args[0]
        self.assertIn(f"latitude={latitude}", url)
        self.assertIn(f"longitude={longitude}", url)
        self.assertIn("lang=de", url)
        self.assertIn(f"apikey={api_key}", url)

    async def test_async_update_logs_error_with_redacted_url_and_cause(self):
        # Arrange
        hass = SimpleNamespace(
            config=SimpleNamespace(language="de", latitude=48.2082, longitude=16.3738)
        )
        api_key = "secret-api-key"
        payload = {"contamination": []}
        response = FakeErrorResponse(payload)
        session = FakeClientSession(response)

        # Act / Assert
        with (
            patch(
                "polleninformation_at_api.async_get_clientsession", return_value=session
            ),
            self.assertLogs(API_MODULE.__name__, level="ERROR") as logs,
        ):
            api = PollenApi(hass, api_key)
            with self.assertRaises(RuntimeError) as exc_info:
                await api.async_update()

        self.assertEqual(len(logs.records), 1)
        self.assertIsNotNone(logs.records[0].exc_info)
        self.assertIn("<REDACTED>", logs.output[0])
        self.assertNotIn(api_key, logs.output[0])
        self.assertIsInstance(
            exc_info.exception.__cause__, API_MODULE.aiohttp.ClientError
        )

    async def test_async_update_logs_http_error_with_status_code(self):
        # Arrange
        hass = SimpleNamespace(
            config=SimpleNamespace(language="de", latitude=48.2082, longitude=16.3738)
        )
        api_key = "secret-api-key"
        response = FakeHttpErrorResponse(404, "Not Found")
        session = FakeClientSession(response)

        # Act / Assert
        with (
            patch(
                "polleninformation_at_api.async_get_clientsession", return_value=session
            ),
            self.assertLogs(API_MODULE.__name__, level="ERROR") as logs,
        ):
            api = PollenApi(hass, api_key)
            with self.assertRaises(RuntimeError) as exc_info:
                await api.async_update()

        self.assertEqual(len(logs.records), 1)
        self.assertIn("HTTP error while fetching data from URL", logs.output[0])
        self.assertIn("status 404", logs.output[0])
        self.assertIn("Not Found", logs.output[0])
        self.assertIn("<REDACTED>", logs.output[0])
        self.assertNotIn(api_key, logs.output[0])
        self.assertIsInstance(
            exc_info.exception.__cause__, API_MODULE.aiohttp.ClientResponseError
        )

    async def test_async_update_logs_timeout(self):
        # Arrange
        hass = SimpleNamespace(
            config=SimpleNamespace(language="de", latitude=48.2082, longitude=16.3738)
        )
        api_key = "secret-api-key"
        session = FakeTimeoutSession()

        # Act / Assert
        with (
            patch(
                "polleninformation_at_api.async_get_clientsession", return_value=session
            ),
            self.assertLogs(API_MODULE.__name__, level="ERROR") as logs,
        ):
            api = PollenApi(hass, api_key)
            with self.assertRaises(RuntimeError) as exc_info:
                await api.async_update()

        self.assertEqual(len(logs.records), 1)
        self.assertIn("Timeout while fetching data from URL", logs.output[0])
        self.assertIn("timeout: 10s", logs.output[0])
        self.assertIn("<REDACTED>", logs.output[0])
        self.assertNotIn(api_key, logs.output[0])
        self.assertIsInstance(exc_info.exception.__cause__, TimeoutError)

    async def test_async_update_logs_network_error(self):
        # Arrange
        hass = SimpleNamespace(
            config=SimpleNamespace(language="de", latitude=48.2082, longitude=16.3738)
        )
        api_key = "secret-api-key"
        response = FakeNetworkErrorResponse({})
        session = FakeClientSession(response)

        # Act / Assert
        with (
            patch(
                "polleninformation_at_api.async_get_clientsession", return_value=session
            ),
            self.assertLogs(API_MODULE.__name__, level="ERROR") as logs,
        ):
            api = PollenApi(hass, api_key)
            with self.assertRaises(RuntimeError) as exc_info:
                await api.async_update()

        self.assertEqual(len(logs.records), 1)
        self.assertIn("Error while fetching data from URL", logs.output[0])
        self.assertIn("Cannot connect to host", logs.output[0])
        self.assertIn("<REDACTED>", logs.output[0])
        self.assertNotIn(api_key, logs.output[0])
        self.assertIsInstance(
            exc_info.exception.__cause__, API_MODULE.aiohttp.ClientConnectorError
        )

    async def test_async_update_logs_invalid_response(self):
        # Arrange
        hass = SimpleNamespace(
            config=SimpleNamespace(language="de", latitude=48.2082, longitude=16.3738)
        )
        api_key = "secret-api-key"
        response = FakeInvalidJsonResponse({})
        session = FakeClientSession(response)

        # Act / Assert
        with (
            patch(
                "polleninformation_at_api.async_get_clientsession", return_value=session
            ),
            self.assertLogs(API_MODULE.__name__, level="ERROR") as logs,
        ):
            api = PollenApi(hass, api_key)
            with self.assertRaises(RuntimeError) as exc_info:
                await api.async_update()

        self.assertEqual(len(logs.records), 1)
        self.assertIn("Invalid response from URL", logs.output[0])
        self.assertIn("Expecting value", logs.output[0])
        self.assertIn("<REDACTED>", logs.output[0])
        self.assertNotIn(api_key, logs.output[0])
        self.assertIsInstance(exc_info.exception.__cause__, ValueError)

    async def test_async_update_logs_invalid_content_type(self):
        # Arrange
        hass = SimpleNamespace(
            config=SimpleNamespace(language="de", latitude=48.2082, longitude=16.3738)
        )
        api_key = "secret-api-key"
        response = FakeContentTypeErrorResponse({})
        session = FakeClientSession(response)

        # Act / Assert
        with (
            patch(
                "polleninformation_at_api.async_get_clientsession", return_value=session
            ),
            self.assertLogs(API_MODULE.__name__, level="ERROR") as logs,
        ):
            api = PollenApi(hass, api_key)
            with self.assertRaises(RuntimeError) as exc_info:
                await api.async_update()

        self.assertEqual(len(logs.records), 1)
        self.assertIn("Invalid response content type from URL", logs.output[0])
        self.assertIn("unexpected mimetype", logs.output[0])
        self.assertIn("<REDACTED>", logs.output[0])
        self.assertNotIn(api_key, logs.output[0])
        self.assertIsInstance(
            exc_info.exception.__cause__, API_MODULE.aiohttp.ContentTypeError
        )
