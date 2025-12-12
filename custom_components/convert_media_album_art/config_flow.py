"""Config flow for Convert Media Album Art."""

import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_MEDIA_PLAYER,
    CONF_OUTPUT_DIR,
    CONF_OUTPUT_FILENAME,
    CONF_DEFAULT_IMAGE,
    CONF_IMAGE_SIZE,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OUTPUT_FILENAME,
    DEFAULT_IMAGE_SIZE,
    DEFAULT_DEFAULT_IMAGE,
)

_LOGGER = logging.getLogger(__name__)


class ConvertMediaAlbumArtConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Convert Media Album Art."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate media player entity exists
            media_player = user_input[CONF_MEDIA_PLAYER]
            
            if not self.hass.states.get(media_player):
                errors["base"] = "invalid_media_player"
            else:
                # Create the entry
                return self.async_create_entry(
                    title=f"Album Art for {media_player}",
                    data=user_input,
                )

        # Build the schema
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_MEDIA_PLAYER,
                    default="media_player.kitchen",
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="media_player",
                    ),
                ),
                vol.Optional(
                    CONF_OUTPUT_DIR,
                    default=DEFAULT_OUTPUT_DIR,
                ): str,
                vol.Optional(
                    CONF_OUTPUT_FILENAME,
                    default=DEFAULT_OUTPUT_FILENAME,
                ): str,
                vol.Optional(
                    CONF_DEFAULT_IMAGE,
                    default=DEFAULT_DEFAULT_IMAGE,
                ): str,
                vol.Optional(
                    CONF_IMAGE_SIZE,
                    default=DEFAULT_IMAGE_SIZE,
                ): vol.All(vol.Coerce(int), vol.Range(min=50, max=1000)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return ConvertMediaAlbumArtOptionsFlow()


class ConvertMediaAlbumArtOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Convert Media Album Art."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Update the config entry data with new options
            # Use hass from the handler
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input},
            )
            return self.async_create_entry(title="", data={})

        # Get current values from config entry data
        current_data = self.config_entry.data

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_MEDIA_PLAYER,
                    default=current_data.get(CONF_MEDIA_PLAYER, "media_player.kitchen"),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="media_player",
                    ),
                ),
                vol.Optional(
                    CONF_OUTPUT_DIR,
                    default=current_data.get(CONF_OUTPUT_DIR, DEFAULT_OUTPUT_DIR),
                ): str,
                vol.Optional(
                    CONF_OUTPUT_FILENAME,
                    default=current_data.get(CONF_OUTPUT_FILENAME, DEFAULT_OUTPUT_FILENAME),
                ): str,
                vol.Optional(
                    CONF_DEFAULT_IMAGE,
                    default=current_data.get(CONF_DEFAULT_IMAGE, DEFAULT_DEFAULT_IMAGE),
                ): str,
                vol.Optional(
                    CONF_IMAGE_SIZE,
                    default=current_data.get(CONF_IMAGE_SIZE, DEFAULT_IMAGE_SIZE),
                ): vol.All(vol.Coerce(int), vol.Range(min=50, max=1000)),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
