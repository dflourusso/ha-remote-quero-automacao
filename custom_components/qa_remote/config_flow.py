import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN


class QAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            qa_entity = user_input["qa_entity"]
            learn_switch = user_input["qa_learn_switch"]

            qa_domain = qa_entity.split(".")[0]
            learn_domain = learn_switch.split(".")[0]

            if qa_domain not in ("text", "input_text"):
                errors["qa_entity"] = "invalid_text_entity"

            if learn_domain not in ("switch", "input_boolean"):
                errors["qa_learn_switch"] = "invalid_switch_entity"

            if not errors:
                return self.async_create_entry(
                    title=user_input["name"],
                    data=user_input,
                )

        schema = vol.Schema({
            vol.Required("name"): str,

            vol.Required("qa_profile"): str,

            # Pode ser text OU input_text
            vol.Required("qa_entity"):
                selector.EntitySelector(),

            # Pode ser switch OU input_boolean
            vol.Required("qa_learn_switch"):
                selector.EntitySelector(),

            # Código aprendido sempre vem de sensor
            vol.Required("qa_code_sensor"):
                selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry):
        return QAOptionsFlow(entry)


# ------------------------------------------------------
# OPTIONS FLOW (edição)
# ------------------------------------------------------

class QAOptionsFlow(config_entries.OptionsFlow):

    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        errors = {}

        if user_input is not None:
            qa_entity = user_input["qa_entity"]
            learn_switch = user_input["qa_learn_switch"]

            qa_domain = qa_entity.split(".")[0]
            learn_domain = learn_switch.split(".")[0]

            if qa_domain not in ("text", "input_text"):
                errors["qa_entity"] = "invalid_text_entity"

            if learn_domain not in ("switch", "input_boolean"):
                errors["qa_learn_switch"] = "invalid_switch_entity"

            if not errors:
                return self.async_create_entry(title="", data=user_input)

        options = {**self.entry.data, **self.entry.options}

        schema = vol.Schema({
            vol.Optional(
                "qa_entity",
                default=options.get("qa_entity"),
            ): selector.EntitySelector(),

            vol.Optional(
                "qa_learn_switch",
                default=options.get("qa_learn_switch"),
            ): selector.EntitySelector(),

            vol.Optional(
                "qa_code_sensor",
                default=options.get("qa_code_sensor"),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
