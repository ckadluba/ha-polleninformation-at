import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, INTEGRATION_NAME, DEFAULT_INTERVAL, MIN_INTERVAL, CONF_INTERVAL

class PolleninformationAtConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION=1
    CONNECTION_CLASS=config_entries.CONN_CLASS_CLOUD_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PolleninformationAtOptionsFlowHandler()

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title=INTEGRATION_NAME, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_INTERVAL, default=DEFAULT_INTERVAL): 
                    vol.All(vol.Coerce(int), vol.Range(min=MIN_INTERVAL))
            })
        )

class PolleninformationAtOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self):
        """Initialize options flow."""
        self._conf_app_id: str | None=None

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title=INTEGRATION_NAME, data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_INTERVAL, default=self.config_entry.options.get(CONF_INTERVAL, DEFAULT_INTERVAL)): 
                    vol.All(vol.Coerce(int), vol.Range(min=MIN_INTERVAL)) 
            })
        )