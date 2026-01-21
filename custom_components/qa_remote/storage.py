import json
import os
import logging

from .const import STORAGE_FOLDER

_LOGGER = logging.getLogger(__name__)


class QAStorage:
    def __init__(self, hass, profile):
        self.hass = hass
        self.profile = profile
        self.data = {}

        self._ensure_folder()
        self._load()

    # --------------------------------------------------

    def _path(self):
        return self.hass.config.path(
            STORAGE_FOLDER,
            f"{self.profile}.json"
        )

    # --------------------------------------------------

    def _ensure_folder(self):
        path = self.hass.config.path(STORAGE_FOLDER)

        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

    # --------------------------------------------------

    def _load(self):
        path = self._path()

        if not os.path.exists(path):
            self.data = {"commands": {}}
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception as e:
            _LOGGER.error("Erro lendo QA file: %s", e)
            self.data = {"commands": {}}

    # --------------------------------------------------

    def save(self):
        path = self._path()

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    # --------------------------------------------------

    def get(self, device, command):
        return self.data.get("commands", {}) \
                        .get(device, {}) \
                        .get(command)

    # --------------------------------------------------

    def set(self, device, command, value):
        if "commands" not in self.data:
            self.data["commands"] = {}

        if device not in self.data["commands"]:
            self.data["commands"][device] = {}

        self.data["commands"][device][command] = value
        self.save()

    # --------------------------------------------------

    def devices(self):
        return list(self.data.get("commands", {}).keys())
