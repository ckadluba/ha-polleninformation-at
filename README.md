# Home Assistant Polleninformation.at HACS Custom Integration

This [HACS](https://www.hacs.xyz) custom integration enables access to pollen count data from the API of [Österreichischer Polleninformationsdienst (www.polleninformation.at)](https://www.polleninformation.at) in [Home Assistant](https://www.home-assistant.io).

## Disclaimer

This integration is not official software from Österreichischer Polleninformationsdienst, nor am I in any way associated with this organization. I'm just a person with a pollen allergy who wanted to have pollen count data for Austria available in Home Assistant, so I created this integration.

This software is provided under the **Apache License 2.0** and is offered **AS IS**, without warranty of any kind, express or implied.

The authors and contributors accept **NO RESPONSIBILITY** for:
- Data loss or corruption
- API rate limits, failures
- Unexpected behavior or incorrect results

**Important**: Always create backups of your Home Assistant system when using this integration. 

## Installation and Configuration

1. Request an API key from [https://www.polleninformation.at/datenschnittstelle/api-key-anfordern](https://www.polleninformation.at/datenschnittstelle/api-key-anfordern).

1. Search for the "Polleninformation.at" integration in the HACS store in Home Assistant and install it.

1. Under Settings > Devices and Services, select Add Integration, then search for and add the "Polleninformation.at" integration.
   ![Adding the Polleninformation.at integration](images/add_integration.png)

1. A configuration dialog opens where you must enter the API key.
   ![Configuration dialog to enter API key](images/configuration_dialog.png)

1. After that, another dialog for adding the Polleninformation.at device is shown. Select an area for the device and finish the configuration.
   ![Device dialog to select area](images/device_dialog.png)

## Features and Restrictions

* The integration queries the API every six hours. This is a fixed interval and cannot be changed. Since the pollen data does not change that often within a day and to avoid API rate limiting or revocation of API keys, this relaxed interval was chosen.

* The location for which the pollen count is queried is taken from the configured location of the Home Assistant system. There is no possibility to specify a different location.

* A device named "Polleninformation.at" is created when installing the integration. Under this device, there will be a numerical sensor for each of the 13 pollen types covered by the www.polleninformation.at API.
   
  ![alt text](images/device_and_services.png)

  These sensors are numerical sensors representing the current pollen count returned by the API on a scale from 0 to 4.

* These Polleninformation.at integration sensors show the current pollen count. Pollen count predictions are not exposed, although the API offers such data.

## Development

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

Once VS Code is running in the Dev Container, perform the following steps to start Home Assistant with the integration.

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
rate limited or even revoked if you use the API excessively.

### Running isolated unit tests

To run all unit and integration tests (recommended):

```bash
pytest
```

## Acknowledgements and License

The icon for the Polleninformation.at integration (`custom_components/polleninformation_at/brand/icon.png`) was created by [Vignesh Oviyan](https://icon-icons.com/authors/497-vignesh-oviyan) using the [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) license.

Apache License 2.0 - See LICENSE file for details.

This software was created by [Christian Kadluba](https://github.com/ckadluba).