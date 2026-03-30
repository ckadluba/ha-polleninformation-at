# Home Assistant Polleninformation.at Integration

TODO: Add description

## Development

Use a local virtual environment for development and live integration tests:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install aiohttp
```

The Home Assistant integration now reads the API key from the integration configuration entry. Configure the key in Home Assistant when setting up the integration, or later via the integration options.

For the live development test, inject the API key via environment variable instead of hardcoding it:

```powershell
$env:RUN_POLLEN_API_INTEGRATION_TEST="1"
$env:POLLENINFORMATION_AT_API_KEY="<your-api-key>"
.\.venv\Scripts\python -m unittest tests.test_api_integration
```

Optional test inputs:

```powershell
$env:POLLEN_API_TEST_LATITUDE="48.2082"
$env:POLLEN_API_TEST_LONGITUDE="16.3738"
$env:POLLEN_API_TEST_POLL_ID="23"
```

Run the isolated unit test with:

```powershell
python -m unittest tests.test_api
```
