"""Convert Media Album Art Integration."""

import logging
import asyncio
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN

from .const import (
    DOMAIN,
    CONF_MEDIA_PLAYER,
    CONF_OUTPUT_DIR,
    CONF_OUTPUT_FILENAME,
    CONF_DEFAULT_IMAGE,
    CONF_IMAGE_SIZE,
    ATTR_ENTITY_PICTURE,
    ATTR_MEDIA_ALBUM_NAME,
)
from .image_converter import ImageConverter

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Convert Media Album Art from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Initialize the converter
    converter = ImageConverter(hass, entry.data)
    
    # Initialize the monitor
    monitor = AlbumArtMonitor(hass, entry, converter)
    
    # Store for cleanup
    hass.data[DOMAIN][entry.entry_id] = {
        "converter": converter,
        "monitor": monitor,
    }
    
    # Start monitoring
    await monitor.async_start()
    
    _LOGGER.info("Convert Media Album Art initialized")
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if entry.entry_id in hass.data[DOMAIN]:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        
        # Stop monitoring
        if "monitor" in data:
            await data["monitor"].async_stop()
    
    _LOGGER.info("Convert Media Album Art unloaded")
    
    return True


class AlbumArtMonitor:
    """Monitor media player for album art changes."""

    def __init__(self, hass, config_entry, converter):
        """Initialize the monitor."""
        self.hass = hass
        self.config_entry = config_entry
        self.converter = converter
        
        self.media_player_entity = config_entry.data[CONF_MEDIA_PLAYER]
        self.last_album = None
        self.last_image_url = None
        self._unsub_state_listener = None
        self._processing_lock = asyncio.Lock()
        
        _LOGGER.info("AlbumArtMonitor initialized for %s", self.media_player_entity)

    async def async_start(self):
        """Start monitoring the media player."""
        # Process current state immediately
        await self._process_current_state()
        
        # Set up state change listener
        self._unsub_state_listener = async_track_state_change_event(
            self.hass,
            [self.media_player_entity],
            self._handle_state_change,
        )
        
        _LOGGER.info("Started monitoring %s", self.media_player_entity)

    async def async_stop(self):
        """Stop monitoring."""
        if self._unsub_state_listener:
            self._unsub_state_listener()
            self._unsub_state_listener = None
        
        _LOGGER.info("Stopped monitoring %s", self.media_player_entity)

    async def _process_current_state(self):
        """Process the current state of the media player."""
        state = self.hass.states.get(self.media_player_entity)
        
        if state is None:
            _LOGGER.warning("Media player %s not found", self.media_player_entity)
            return
        
        await self._process_state(state)

    @callback
    async def _handle_state_change(self, event):
        """Handle state change events."""
        new_state = event.data.get("new_state")
        
        if new_state is None:
            return
        
        await self._process_state(new_state)

    async def _process_state(self, state):
        """Process a media player state."""
        # Skip if state is unavailable or unknown
        if state.state in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
            _LOGGER.debug("Media player is %s, skipping", state.state)
            return
        
        # Get album name and image URL
        album_name = state.attributes.get(ATTR_MEDIA_ALBUM_NAME)
        entity_picture = state.attributes.get(ATTR_ENTITY_PICTURE)
        
        # Log current state
        _LOGGER.debug(
            "State update: album=%s, image=%s",
            album_name,
            entity_picture,
        )
        
        # Skip if no album name (not playing music with album art)
        if not album_name:
            _LOGGER.debug("No album name, skipping")
            return
        
        # Skip if no entity picture
        if not entity_picture:
            _LOGGER.warning("Album '%s' has no entity_picture", album_name)
            return
        
        # Check if this is a new album or new image URL
        if (album_name == self.last_album and 
            entity_picture == self.last_image_url):
            _LOGGER.debug("Same album and image, skipping")
            return
        
        # Update tracking
        self.last_album = album_name
        self.last_image_url = entity_picture
        
        _LOGGER.info(
            "New album detected: '%s' with image: %s",
            album_name,
            entity_picture,
        )
        
        # Process the new album art (with lock to prevent concurrent processing)
        async with self._processing_lock:
            await self._convert_album_art(entity_picture, album_name)

    async def _convert_album_art(self, image_url, album_name):
        """Convert and save album art."""
        try:
            _LOGGER.info("Converting album art for '%s'...", album_name)
            
            success = await self.converter.convert_and_save(image_url)
            
            if success:
                _LOGGER.info("Successfully processed album art for '%s'", album_name)
                
                # Fire event for automation/logging
                self.hass.bus.async_fire(
                    f"{DOMAIN}_converted",
                    {
                        "media_player": self.media_player_entity,
                        "album": album_name,
                        "image_url": image_url,
                    },
                )
            else:
                _LOGGER.warning("Failed to process album art for '%s'", album_name)
                
        except Exception as err:
            _LOGGER.error(
                "Unexpected error converting album art for '%s': %s",
                album_name,
                err,
            )
