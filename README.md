# Home Assistant Polleninformation.at Integration

Custom Home Assistant integration for `polleninformation.at`.



## Development

For classic development and live tests outside the container:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install aiohttp
```


The Home Assistant integration reads the API key from the integration configuration. For live tests, you can set the key via environment variable:

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

### Debugging the integration in VS Code (with Dev Container)

To debug this integration using VS Code, Dev Containers, and WSL:

1. Open a WSL terminal (e.g., Ubuntu on Windows).
2. Change to your project directory:
	```bash
	cd /path/to/ha-polleninformation-at
	```
3. Start VS Code in WSL:
	```bash
	code .
	```
4. If prompted, reopen the project in the Dev Container ("Reopen in Container").
5. Wait until the Dev Container is fully started.
6. In VS Code, select the Python interpreter inside the container (e.g., /usr/local/bin/python3) if not already selected.
7. In the VS Code Run & Debug panel, choose the configuration **Home Assistant: Debug current integration**.
8. Start the debugger (F5 or green play button).

This will start Home Assistant in debug mode with your integration. Breakpoints in `custom_components/polleninformation_at` will be hit directly.

After starting the debugger (F5), open your browser and go to [http://localhost:8123](http://localhost:8123).
On the first start, you need to create a Home Assistant user account. Then add the "Polleninformation.at" integration via the Home Assistant UI.

The Home Assistant test configuration is located at `.devcontainer/config/configuration.yaml`. The start script links your checked-out integration from `custom_components/polleninformation_at` into that config directory, so code changes are picked up immediately.
