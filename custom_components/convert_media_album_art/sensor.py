"""Sensor platform for Convert Media Album Art.

Exposes a single sensor per config entry whose state is the
fully-resolved, ready-to-fetch URL for the converted album art image
(e.g. "http://ha.7p.net/local/media_album.bmp"). Point ESPHome (or
anything else) at this entity instead of hardcoding a host/port in your
device YAML - when the URL changes (new port, new host, moved behind a
proxy) you only ever update it in one place.
"""

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.network import NoURLAvailableError, get_url

from .const import (
    CONF_DEFAULT_IMAGE,
    CONF_ESPHOME_BASE_URL,
    CONF_IMAGE_SIZE,
    CONF_MEDIA_PLAYER,
    CONF_OUTPUT_DIR,
    CONF_OUTPUT_FILENAME,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OUTPUT_FILENAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform for a config entry."""
    async_add_entities([AlbumArtUrlSensor(hass, entry)])


class AlbumArtUrlSensor(SensorEntity):
    """The fully-resolved URL an ESPHome device (or anything else) should
    use to fetch the converted album art image.
    """

    _attr_has_entity_name = True
    _attr_name = "ESPHome image URL"
    _attr_icon = "mdi:link-variant"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    # Config-derived value; cheap to recompute, so plain polling (default
    # ~30s scan interval) is enough - no need for push/coordinator wiring.
    _attr_should_poll = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hass = hass
        # Keep the actual ConfigEntry reference (not a data snapshot) so
        # this always reflects the latest saved options without a reload.
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_esphome_url"

        media_player = entry.data.get(CONF_MEDIA_PLAYER, "")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Album Art for {media_player}" if media_player else "Convert Media Album Art",
            manufacturer="Convert Media Album Art",
        )

    @property
    def native_value(self) -> str | None:
        """Return the fully-resolved URL to the converted image."""
        data = self._entry.data

        base_url = (data.get(CONF_ESPHOME_BASE_URL) or "").strip().rstrip("/")

        if not base_url:
            # Blank = fall back to whatever HA is configured with for
            # itself (Settings > System > Network). Fine for the common
            # case where ESPHome devices and HA share the same network.
            try:
                base_url = get_url(self.hass, allow_cloud=False).rstrip("/")
            except NoURLAvailableError:
                _LOGGER.warning(
                    "No ESPHome base URL configured for '%s' and no HA "
                    "internal/external URL is available either - set one "
                    "explicitly in the integration options",
                    self.entity_id,
                )
                return None

        output_dir = data.get(CONF_OUTPUT_DIR, DEFAULT_OUTPUT_DIR)
        output_filename = data.get(CONF_OUTPUT_FILENAME, DEFAULT_OUTPUT_FILENAME)

        if output_dir != "www":
            # HA only auto-serves the "www" folder under /local/. Anything
            # else needs a manually registered static path, which this
            # sensor doesn't know about - flag it rather than silently
            # returning a URL that 404s.
            _LOGGER.warning(
                "output_dir is '%s' instead of 'www' - Home Assistant only "
                "serves the 'www' folder under /local/, so this computed "
                "URL is likely wrong for '%s'",
                output_dir,
                self.entity_id,
            )

        return f"{base_url}/local/{output_filename}"
