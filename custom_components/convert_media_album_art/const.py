"""Constants for Convert Media Album Art."""

DOMAIN = "convert_media_album_art"
CONF_MEDIA_PLAYER = "media_player"
CONF_OUTPUT_DIR = "output_dir"
CONF_OUTPUT_FILENAME = "output_filename"
CONF_DEFAULT_IMAGE = "default_image"
CONF_IMAGE_SIZE = "image_size"
# Base URL that ESPHome devices should use to fetch the converted image
# (e.g. "http://10.10.10.9" or "http://ha.example.com"). Leave blank to
# auto-detect using Home Assistant's own configured internal/external URL.
CONF_ESPHOME_BASE_URL = "esphome_base_url"

DEFAULT_OUTPUT_DIR = "www"
DEFAULT_OUTPUT_FILENAME = "media_album.bmp"
DEFAULT_IMAGE_SIZE = 200
DEFAULT_DEFAULT_IMAGE = "blank_album.bmp"
DEFAULT_ESPHOME_BASE_URL = ""

ATTR_ENTITY_PICTURE = "entity_picture"
ATTR_MEDIA_ALBUM_NAME = "media_album_name"
