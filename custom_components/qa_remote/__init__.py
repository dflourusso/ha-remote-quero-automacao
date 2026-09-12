from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_setup(hass: HomeAssistant, config: dict):
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_forward_entry_setups(entry, ["remote"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    return await hass.config_entries.async_forward_entry_unload(entry, "remote")


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate config entry from switch-based to button-based learning."""
    if entry.version > 2:
        return False

    if entry.version < 2:
        data = {**entry.data}
        options = {**entry.options}

        if "qa_learn_switch" in data and "qa_learn_button" not in data:
            data["qa_learn_button"] = data.pop("qa_learn_switch")
        elif "qa_learn_switch" in data:
            data.pop("qa_learn_switch")

        if "qa_learn_switch" in options and "qa_learn_button" not in options:
            options["qa_learn_button"] = options.pop("qa_learn_switch")
        elif "qa_learn_switch" in options:
            options.pop("qa_learn_switch")

        hass.config_entries.async_update_entry(
            entry,
            data=data,
            options=options,
            version=2,
        )

    return True
