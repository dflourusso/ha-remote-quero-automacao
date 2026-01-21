import logging
import asyncio

from homeassistant.components.remote import RemoteEntity
from homeassistant.helpers.event import async_track_state_change_event

from .storage import QAStorage

_LOGGER = logging.getLogger(__name__)


class QARemote(RemoteEntity):

    def __init__(self, hass, config):
        self.hass = hass

        self._name = config.get("name")
        self._profile = config.get("qa_profile")

        self._send_entity = config.get("qa_entity")          # text
        self._learn_switch = config.get("qa_learn_switch")  # switch
        self._code_sensor = config.get("qa_code_sensor")    # sensor

        self._attr_name = self._name
        self._attr_unique_id = f"qa_remote_{self._profile}"

        self.storage = QAStorage(hass, self._profile)

    # --------------------------------------------------
    # SEND COMMAND
    # --------------------------------------------------

    async def async_send_command(self, command, **kwargs):

        device = kwargs.get("device")

        if not device:
            _LOGGER.error("send_command sem device")
            return

        if isinstance(command, list):
            command = command[0]

        ir = self.storage.get(device, command)

        if not ir:
            _LOGGER.error(
                "QA: comando '%s' não existe para device '%s'",
                command,
                device,
            )
            return

        _LOGGER.info("[QA] %s → %s", device, command)

        await self.hass.services.async_call(
            "text",
            "set_value",
            {
                "entity_id": self._send_entity,
                "value": ir,
            },
            blocking=True,
        )

    # --------------------------------------------------
    # LEARN COMMAND (REAL)
    # --------------------------------------------------

    async def async_learn_command(self, **kwargs):

        device = kwargs.get("device")
        command = kwargs.get("command")

        if isinstance(command, list):
            command = command[0]

        if not device or not command:
            _LOGGER.error("learn_command requer device e command")
            return

        _LOGGER.info(
            "[QA] Iniciando aprendizado: %s → %s",
            device,
            command,
        )

        learned_event = asyncio.Event()
        learned_value = {"code": None}

        # ------------------------------
        # CALLBACK SENSOR
        # ------------------------------

        async def _sensor_changed(event):
            new = event.data.get("new_state")
            if not new or not new.state:
                return

            learned_value["code"] = new.state
            learned_event.set()

        # Escuta o sensor
        unsub = async_track_state_change_event(
            self.hass,
            [self._code_sensor],
            _sensor_changed,
        )

        try:
            # 1) Ligar modo learn
            await self.hass.services.async_call(
                "switch",
                "turn_on",
                {"entity_id": self._learn_switch},
                blocking=True,
            )

            # 2) Esperar código (timeout 20s)
            try:
                await asyncio.wait_for(learned_event.wait(), timeout=20)
            except asyncio.TimeoutError:
                _LOGGER.error("[QA] Timeout no aprendizado IR")
                return

            code = learned_value["code"]

            if not code:
                _LOGGER.error("[QA] Código aprendido vazio")
                return

            # 3) Salvar
            self.storage.set(device, command, code)

            _LOGGER.info(
                "[QA] Aprendido com sucesso: %s → %s",
                device,
                command,
            )

        finally:
            # 4) Cleanup
            unsub()

            await self.hass.services.async_call(
                "switch",
                "turn_off",
                {"entity_id": self._learn_switch},
                blocking=True,
            )
