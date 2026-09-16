import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_MQTT_TOPIC, CONF_SEND_DELAY, DEFAULT_SEND_DELAY, DOMAIN


def _send_delay_selector():
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0.5,
            max=10,
            step=0.1,
            unit_of_measurement="s",
            mode=selector.NumberSelectorMode.BOX,
        )
    )


class QAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

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

            vol.Required("qa_learn_button"):
                selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="button")
                ),

            vol.Required("qa_code_sensor"):
                selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),

            vol.Optional(
                CONF_SEND_DELAY,
                default=DEFAULT_SEND_DELAY,
            ): _send_delay_selector(),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry):
        return QAOptionsFlow(entry)


class QAOptionsFlow(config_entries.OptionsFlow):

    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            saved_topic = (
                self.entry.options.get(CONF_MQTT_TOPIC)
                or self.entry.data.get(CONF_MQTT_TOPIC)
                or ""
            ).strip()
            if saved_topic:
                user_input[CONF_MQTT_TOPIC] = saved_topic
            return self.async_create_entry(
                title="",
                data=user_input,
            )

        options = {**self.entry.data, **self.entry.options}

        schema = vol.Schema({
            vol.Optional(
                "qa_entity",
                default=options.get("qa_entity"),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="text")
            ),

            vol.Optional(
                "qa_learn_button",
                default=options.get("qa_learn_button"),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="button")
            ),

            vol.Optional(
                "qa_code_sensor",
                default=options.get("qa_code_sensor"),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),

            vol.Optional(
                CONF_SEND_DELAY,
                default=options.get(CONF_SEND_DELAY, DEFAULT_SEND_DELAY),
            ): _send_delay_selector(),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
