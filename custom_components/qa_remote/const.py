DOMAIN = "qa_remote"
STORAGE_FOLDER = "qa_ir"

CONF_MQTT_TOPIC = "qa_mqtt_topic"
CONF_SEND_DELAY = "qa_send_delay"

# ~2s matches measured Zosung publish→LED latency on typical meshes.
DEFAULT_SEND_DELAY = 2.0
