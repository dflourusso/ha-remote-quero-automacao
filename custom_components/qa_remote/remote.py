import logging
import asyncio

from homeassistant.components.remote import RemoteEntity
from homeassistant.helpers.event import async_track_state_change_event

from .storage import QAStorage

_LOGGER = logging.getLogger(__name__)


class QARemote(RemoteEntity):
    """QA IR Remote."""

    def __init__(self, hass, config):
        self.hass = hass

        self._name = config["name"]
        self._profile = config["qa_profile"]

        # Entidades expostas pelo hub QA
        self._send_entity = config["qa_entity"]          # input_text (debug) ou text (final)
        self._learn_switch = config["qa_learn_switch"]   # input_boolean (debug) ou switch
        self._code_sensor = config["qa_code_sensor"]     # sensor com IR aprendido

        self._attr_name = self._name
        self._attr_unique_id = f"qa_remote_{self._profile}"
        self._attr_icon = "mdi:infrared"

        self.storage = QAStorage(hass, self._profile)

    # --------------------------------------------------
    # LIFECYCLE
    # --------------------------------------------------

    async def async_added_to_hass(self):
        """Carrega os códigos IR fora do event loop."""
        await self.storage.async_load()

    # --------------------------------------------------
    # SEND COMMAND
    # --------------------------------------------------

    async def async_send_command(self, command, **kwargs):
        device = kwargs.get("device")

        if not device:
            _LOGGER.error("QA send_command sem device")
            return

        # Aceita string ou lista, mas envia um por vez
        if isinstance(command, list):
            command = command[0]

        ir = self.storage.get(device, command)

        if not ir:
            _LOGGER.error(
                "QA: comando '%s' não encontrado para '%s'",
                command,
                device,
            )
            return

        domain = self._send_entity.split(".")[0]

        _LOGGER.info("[QA] Enviando IR: %s → %s", device, command)

        await self.hass.services.async_call(
            domain,
            "set_value",
            {
                "entity_id": self._send_entity,
                "value": ir,
            },
            blocking=True,
        )

    # --------------------------------------------------
    # LEARN COMMAND
    # --------------------------------------------------

    async def async_learn_command(self, **kwargs):
        device = kwargs.get("device")
        command = kwargs.get("command")

        if not device or not command:
            _LOGGER.error("QA learn_command requer device e command")
            return

        # Aprende apenas um comando
        if isinstance(command, list):
            command = command[0]

        _LOGGER.info("[QA] Aprendendo IR: %s → %s", device, command)

        learned_event = asyncio.Event()
        learned_code = {"value": None}

        async def _sensor_changed(event):
            new = event.data.get("new_state")
            if not new or not new.state:
                return

            learned_code["value"] = new.state
            learned_event.set()

        unsub = async_track_state_change_event(
            self.hass,
            [self._code_sensor],
            _sensor_changed,
        )

        try:
            # Liga modo aprendizado
            learn_domain = self._learn_switch.split(".")[0]

            await self.hass.services.async_call(
                learn_domain,
                "turn_on",
                {"entity_id": self._learn_switch},
                blocking=True,
            )

            try:
                # ⏱️ Timeout aumentado para 60s
                await asyncio.wait_for(learned_event.wait(), timeout=60)
            except asyncio.TimeoutError:
                _LOGGER.error("[QA] Timeout ao aprender IR")
                return

            code = learned_code["value"]

            if not code:
                _LOGGER.error("[QA] Código IR vazio")
                return

            await self.storage.set(device, command, code)

            _LOGGER.info(
                "[QA] IR aprendido com sucesso: %s → %s",
                device,
                command,
            )

        finally:
            unsub()

            # Desliga modo aprendizado
            learn_domain = self._learn_switch.split(".")[0]

            await self.hass.services.async_call(
                learn_domain,
                "turn_off",
                {"entity_id": self._learn_switch},
                blocking=True,
            )


# ------------------------------------------------------
# SETUP ENTRY
# ------------------------------------------------------

async def async_setup_entry(hass, entry, async_add_entities):
    config = {**entry.data, **entry.options}

    async_add_entities([
        QARemote(hass, config)
    ])
