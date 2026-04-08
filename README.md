# Home Assistant Polleninformation.at Integration

Custom Home Assistant integration for `polleninformation.at`.






## Development (in the Dev Container)

All development steps and tests are performed inside the Dev Container. This ensures a consistent environment, just like in production.

### Starting VS Code in the Dev Container

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

### Starting Home Assistant with the Integration in the Dev Container

Once VS Code is running in the Dev Comtainer, perform the following steps to start Home Assistant with the integration.

1. In the Run & Debug panel, select the configuration **Home Assistant: Debug current integration**.
2. Start the debugger (F5 or green play button).

Home Assistant will start in debug mode with your integration. Breakpoints in `custom_components/polleninformation_at` will be hit directly.

After starting the debugger (F5), open [http://localhost:8123](http://localhost:8123) in your browser. On first start, create a Home Assistant user and add the "Polleninformation.at" integration via the UI.

The Home Assistant test configuration is located at `.devcontainer/config/configuration.yaml`. The start script automatically links your integration, so code changes are picked up immediately.

### Running integration tests

To run integration tests like `test_async_update_fetches_live_data`:

1. Copy the file `.env.example` to `.env` in the project root:

   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and enter your real API key and (optionally) adjust the test parameters.

   Example:
   ```env
POLLENINFORMATION_AT_API_KEY=your-api-key-here # Comment this line to skip test_async_update_fetches_live_data
   POLLEN_API_TEST_LATITUDE=48.2082
   POLLEN_API_TEST_LONGITUDE=16.3738
   POLLEN_API_TEST_POLLEN_ID=23
   ```

3. Run the test in a terminal inside the Dev Container:

   ```bash
   python -m unittest tests.test_api_integration
   ```

The test will only run and perform a live API call if the variable `POLLENINFORMATION_AT_API_KEY` is 
set in your `.env` file. Be careful not to run the live API test too frequently. Your API key might get 
rate limited or even revoked if you use the Polleninformation.at API ecessively.

### Running isolated unit tests

To run all unit and integration tests (recommended):

```bash
pytest
```
