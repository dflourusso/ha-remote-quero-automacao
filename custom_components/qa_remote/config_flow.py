import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import DOMAIN


class QAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(self, user_input=None):

        if user_input is not None:
            return self.async_create_entry(
                title=user_input["name"],
                data=user_input,
            )

        schema = vol.Schema({

            vol.Required("name"): str,

            vol.Required("qa_profile"): str,

            vol.Required("qa_entity"):
                selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="text")
                ),

            vol.Required("qa_learn_switch"):
              selector.EntitySelector(
                  selector.EntitySelectorConfig(domain="switch")
              ),

          vol.Required("qa_code_sensor"):
              selector.EntitySelector(
                  selector.EntitySelectorConfig(domain="sensor")
              ),

        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )
