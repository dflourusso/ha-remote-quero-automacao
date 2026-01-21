import json
import os
import logging

from .const import STORAGE_FOLDER

_LOGGER = logging.getLogger(__name__)


class QAStorage:
    def __init__(self, hass, profile):
        self.hass = hass
        self.profile = profile
        self.data = {"commands": {}}

        # ⚠️ NÃO faz I/O aqui
        self._ensure_folder()

    # --------------------------------------------------
    # PATHS
    # --------------------------------------------------

    def _path(self):
        return self.hass.config.path(
            STORAGE_FOLDER,
            f"{self.profile}.json"
        )

    # --------------------------------------------------
    # FOLDER
    # --------------------------------------------------

    def _ensure_folder(self):
        path = self.hass.config.path(STORAGE_FOLDER)
        os.makedirs(path, exist_ok=True)

    # --------------------------------------------------
    # LOAD (ASYNC SAFE)
    # --------------------------------------------------

    async def async_load(self):
        """Carrega o arquivo fora do event loop."""
        await self.hass.async_add_executor_job(self._load)

    def _load(self):
        path = self._path()

        if not os.path.exists(path):
            self.data = {"commands": {}}
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception as e:
            _LOGGER.error("Erro lendo QA file %s: %s", path, e)
            self.data = {"commands": {}}

    # --------------------------------------------------
    # SAVE (ASYNC SAFE)
    # --------------------------------------------------

    async def async_save(self):
        """Salva o arquivo fora do event loop."""
        await self.hass.async_add_executor_job(self._save)

    def _save(self):
        path = self._path()

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            _LOGGER.error("Erro salvando QA file %s: %s", path, e)

    # --------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------

    def get(self, device, command):
        return (
            self.data
            .get("commands", {})
            .get(device, {})
            .get(command)
        )

    async def set(self, device, command, value):
        if "commands" not in self.data:
            self.data["commands"] = {}

        if device not in self.data["commands"]:
            self.data["commands"][device] = {}

        self.data["commands"][device][command] = value
        await self.async_save()

    def devices(self):
        return list(self.data.get("commands", {}).keys())
