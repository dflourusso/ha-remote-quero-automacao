import asyncio
import json
import logging

from homeassistant.components.remote import RemoteEntity
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_MQTT_TOPIC, CONF_SEND_DELAY, DEFAULT_SEND_DELAY
from .storage import QAStorage

_LOGGER = logging.getLogger(__name__)

_INVALID_STATES = {"", "unknown", "unavailable", "none", "null"}


def _extract_command_topic(payload):
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
    if not isinstance(payload, dict):
        return None
    topic = payload.get("command_topic")
    if isinstance(topic, str) and topic.strip():
        return topic.strip()
    return None


def _topics_from_set_topic(set_topic):
    topic = set_topic.rstrip("/")
    if topic.endswith("/set"):
        return topic, topic[: -len("/set")]
    return f"{topic}/set", topic


def _valid_ir_code(value):
    if not isinstance(value, str):
        return False
    return value.strip().lower() not in _INVALID_STATES


class QARemote(RemoteEntity):
    """QA IR Remote."""

    def __init__(self, hass, config):
        self.hass = hass

        self._name = config["name"]
        self._profile = config["qa_profile"]

        # Entidades expostas pelo hub QA
        self._send_entity = config["qa_entity"]
        self._learn_button = config["qa_learn_button"]
        self._code_sensor = config["qa_code_sensor"]
        self._mqtt_topic_override = (config.get(CONF_MQTT_TOPIC) or "").strip() or None
        try:
            self._send_delay = float(config.get(CONF_SEND_DELAY, DEFAULT_SEND_DELAY))
        except (TypeError, ValueError):
            self._send_delay = DEFAULT_SEND_DELAY

        self._attr_name = self._name
        self._attr_unique_id = f"qa_remote_{self._profile}"
        self._attr_icon = "mdi:infrared"

        self._send_lock = asyncio.Lock()
        self.storage = QAStorage(hass, self._profile)

    async def async_added_to_hass(self):
        """Carrega os códigos IR fora do event loop."""
        await self.storage.async_load()

    def _mqtt_topics(self):
        """Return (set_topic, state_topic) or (None, None)."""
        override = self._mqtt_topic_override
        if override:
            set_topic, state_topic = _topics_from_set_topic(override)
            _LOGGER.debug("[QA] MQTT topic from saved override: %s", set_topic)
            return set_topic, state_topic

        command_topic = self._discovery_command_topic()
        if not command_topic:
            return None, None

        set_topic, state_topic = _topics_from_set_topic(command_topic)
        _LOGGER.debug("[QA] MQTT topic from discovery: %s", set_topic)
        return set_topic, state_topic

    def _discovery_command_topic(self):
        """command_topic from the text entity's MQTT discovery (includes z2m instance prefix)."""
        if not self._mqtt_ready():
            return None

        try:
            from homeassistant.components.mqtt import debug_info
        except ImportError:
            return None

        ent = er.async_get(self.hass).async_get(self._send_entity)
        device_id = ent.device_id if ent else None

        if device_id:
            try:
                info = debug_info.info_for_device(self.hass, device_id)
            except Exception as err:
                _LOGGER.debug("[QA] MQTT discovery lookup failed: %s", err)
                _LOGGER.debug("[QA] MQTT discovery lookup failed: %s", err)
                info = None

            if info:
                for entity_info in info.get("entities") or []:
                    if entity_info.get("entity_id") != self._send_entity:
                        continue
                    topic = _extract_command_topic(
                        (entity_info.get("discovery_data") or {}).get("payload")
                    )
                    if topic:
                        return topic

                for entity_info in info.get("entities") or []:
                    topic = _extract_command_topic(
                        (entity_info.get("discovery_data") or {}).get("payload")
                    )
                    if topic and topic.rstrip("/").endswith("/set"):
                        return topic

        return self._command_topic_from_entity_debug()

    def _command_topic_from_entity_debug(self):
        mqtt_data = self.hass.data.get("mqtt")
        try:
            from homeassistant.components.mqtt.models import DATA_MQTT

            mqtt_data = self.hass.data.get(DATA_MQTT, mqtt_data)
        except ImportError:
            pass

        if mqtt_data is None:
            return None

        entities = getattr(mqtt_data, "debug_info_entities", None)
        if entities is None and isinstance(mqtt_data, dict):
            entities = mqtt_data.get("debug_info_entities")
        if not entities:
            return None

        entity_info = entities.get(self._send_entity)
        if not entity_info:
            return None

        discovery = entity_info.get("discovery_data") or {}
        payload = discovery.get("payload")
        if payload in (None, ""):
            try:
                from homeassistant.components.mqtt.const import ATTR_DISCOVERY_PAYLOAD

                payload = discovery.get(ATTR_DISCOVERY_PAYLOAD)
            except ImportError:
                payload = None

        return _extract_command_topic(payload) or _extract_command_topic(discovery)

    def _mqtt_ready(self):
        return "mqtt" in self.hass.config.components and self.hass.services.has_service(
            "mqtt", "publish"
        )

    async def _publish_ir(self, ir):
        set_topic, _ = self._mqtt_topics()

        if self._mqtt_ready() and set_topic:
            _LOGGER.debug("[QA] MQTT publish %s", set_topic)
            await self.hass.services.async_call(
                "mqtt",
                "publish",
                {
                    "topic": set_topic,
                    "payload": json.dumps({"ir_code_to_send": ir}),
                    "qos": 0,
                    "retain": False,
                },
                blocking=True,
            )
            return True

        domain = self._send_entity.split(".")[0]
        _LOGGER.warning(
            "[QA] MQTT indisponível ou topic não detectado; usando %s.set_value",
            domain,
        )
        await self.hass.services.async_call(
            domain,
            "set_value",
            {
                "entity_id": self._send_entity,
                "value": ir,
            },
            blocking=True,
        )
        return False

    def _inter_send_delay(self, kwargs):
        delay = self._send_delay
        raw = kwargs.get("delay_secs")
        if raw is None:
            return delay
        try:
            return max(delay, float(raw))
        except (TypeError, ValueError):
            return delay

    async def async_send_command(self, command, **kwargs):
        device = kwargs.get("device")

        if not device:
            _LOGGER.error("QA send_command sem device")
            return

        if isinstance(command, str):
            commands = [command]
        else:
            commands = list(command)

        if not commands:
            return

        try:
            repeats = int(kwargs.get("num_repeats", 1) or 1)
        except (TypeError, ValueError):
            repeats = 1
        repeats = max(1, repeats)

        delay = self._inter_send_delay(kwargs)

        async with self._send_lock:
            for _ in range(repeats):
                for cmd in commands:
                    ir = self.storage.get(device, cmd)

                    if not ir or not _valid_ir_code(ir):
                        _LOGGER.error(
                            "QA: comando '%s' não encontrado para '%s'",
                            cmd,
                            device,
                        )
                        continue

                    _LOGGER.info("[QA] Enviando IR: %s → %s", device, cmd)
                    await self._publish_ir(ir)
                    if delay > 0:
                        await asyncio.sleep(delay)

    async def async_learn_command(self, **kwargs):
        device = kwargs.get("device")
        command = kwargs.get("command")

        if not device or not command:
            _LOGGER.error("QA learn_command requer device e command")
            return

        if isinstance(command, list):
            command = command[0]

        _LOGGER.info("[QA] Aprendendo IR: %s → %s", device, command)

        any_event = asyncio.Event()
        mqtt_event = asyncio.Event()
        learned = {"mqtt": None, "sensor": None}
        previous = {"code": None, "ts": None}
        armed = False

        def _timings_ts(payload):
            timings = payload.get("learned_ir_timings") if isinstance(payload, dict) else None
            if isinstance(timings, dict):
                return timings.get("timestamp")
            return None

        def _accept_mqtt_payload(payload):
            if not isinstance(payload, dict):
                return

            code = payload.get("learned_ir_code")
            ts = _timings_ts(payload)

            if not armed:
                previous["code"] = code if _valid_ir_code(code) else None
                previous["ts"] = ts
                return

            if not _valid_ir_code(code):
                return

            if code != previous["code"] or (ts and ts != previous["ts"]):
                learned["mqtt"] = code
                mqtt_event.set()
                any_event.set()

        async def _sensor_changed(event):
            new = event.data.get("new_state")
            if not new or not _valid_ir_code(new.state):
                return

            if not armed:
                previous["code"] = previous["code"] or new.state
                return

            learned["sensor"] = new.state
            any_event.set()

        async def _mqtt_message(msg):
            raw = msg.payload
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            try:
                payload = json.loads(raw)
            except (TypeError, ValueError, json.JSONDecodeError):
                return
            _accept_mqtt_payload(payload)

        unsub_sensor = async_track_state_change_event(
            self.hass,
            [self._code_sensor],
            _sensor_changed,
        )
        unsub_mqtt = None

        try:
            _, state_topic = self._mqtt_topics()
            if self._mqtt_ready() and state_topic:
                from homeassistant.components.mqtt import async_subscribe

                unsub_mqtt = await async_subscribe(self.hass, state_topic, _mqtt_message)
                # Drain the retained Z2M state so we don't treat it as a new code.
                await asyncio.sleep(0.3)

            armed = True

            await self.hass.services.async_call(
                "button",
                "press",
                {"entity_id": self._learn_button},
                blocking=True,
            )

            try:
                await asyncio.wait_for(any_event.wait(), timeout=60)
            except asyncio.TimeoutError:
                _LOGGER.error("[QA] Timeout ao aprender IR")
                return

            # Sensor state is capped at 255 chars; wait briefly for the full MQTT payload.
            if not mqtt_event.is_set() and unsub_mqtt:
                try:
                    await asyncio.wait_for(mqtt_event.wait(), timeout=0.8)
                except asyncio.TimeoutError:
                    pass

            code = learned["mqtt"] or learned["sensor"]

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
            unsub_sensor()
            if unsub_mqtt:
                unsub_mqtt()


async def async_setup_entry(hass, entry, async_add_entities):
    config = {**entry.data, **entry.options}

    async_add_entities([
        QARemote(hass, config)
    ])
