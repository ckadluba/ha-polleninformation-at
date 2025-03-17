import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_INTERVAL

class PolleninformationAtConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Polleninformation.at."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PolleninformationAtOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="Polleninformation.at", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_INTERVAL, default=21600): vol.All(vol.Coerce(int), vol.Range(min=1800))
            }),
            description_placeholders={
                "interval_label": "Poll interval (seconds)"
            }
        )

class PolleninformationAtOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Polleninformation.at."""

    def __init__(self, config_entry):
        """Initialize the options flow handler."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_INTERVAL, default=self.config_entry.options.get(CONF_INTERVAL, 21600)): vol.All(vol.Coerce(int), vol.Range(min=1800))
            }),
            description_placeholders={
                "interval_label": "Poll interval (seconds)"
            }
        )