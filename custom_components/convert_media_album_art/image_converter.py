"""Image conversion logic for Convert Media Album Art."""

import logging
import os
import io
import aiohttp
from PIL import Image
from pathlib import Path
from homeassistant.helpers.network import get_url, NoURLAvailableError

_LOGGER = logging.getLogger(__name__)


class ImageConverter:
    """Handle image downloading and conversion for ESPHome displays."""

    def __init__(self, hass, config):
        """Initialize the image converter."""
        self.hass = hass
        self.output_dir = config.get("output_dir", "www")
        self.output_filename = config.get("output_filename", "esp_album_art.bmp")
        self.default_image = config.get("default_image", "blank_album.bmp")
        self.image_size = config.get("image_size", 200)

        # Construct full paths
        self.config_dir = Path(hass.config.path())
        self.output_path = self.config_dir / self.output_dir / self.output_filename
        self.default_path = self.config_dir / self.output_dir / self.default_image

        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        _LOGGER.info(
            "ImageConverter initialized: output=%s, default=%s, size=%dx%d",
            self.output_path,
            self.default_path,
            self.image_size,
            self.image_size,
        )

    def _get_base_url(self):
        """Get the base URL for Home Assistant.

        Uses HA's own URL resolver instead of guessing a port, so this
        keeps working no matter what port the frontend/API is bound to.
        """
        try:
            return get_url(self.hass, allow_cloud=False)
        except NoURLAvailableError:
            _LOGGER.warning(
                "No internal or external URL configured in Home Assistant; "
                "falling back to localhost"
            )
            port = getattr(self.hass.config.api, "port", 8123)
            return f"http://localhost:{port}"

    async def download_image(self, url):
        """Download image from URL."""
        try:
            # Handle relative URLs by prepending base URL
            if url.startswith("/"):
                base_url = self._get_base_url()
                url = f"{base_url}{url}"

            _LOGGER.info("Downloading image from: %s", url)

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to download image: HTTP %s", response.status)
                        return None

                    image_data = await response.read()

                    if not image_data:
                        _LOGGER.error("Downloaded image is empty")
                        return None

                    _LOGGER.info("Successfully downloaded %d bytes", len(image_data))
                    return image_data

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error downloading image: %s", err)
            return None
        except Exception as err:
            _LOGGER.error("Unexpected error downloading image: %s", err)
            return None

    def convert_to_bmp(self, image_data):
        """Convert image data to 24-bit BMP suitable for ESPHome."""
        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_data))

            _LOGGER.debug(
                "Original image: mode=%s, size=%s",
                image.mode,
                image.size,
            )

            # Convert to RGB (remove alpha channel, handle all formats)
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Resize to target size (forcing aspect ratio)
            target_size = (self.image_size, self.image_size)
            image = image.resize(target_size, Image.Resampling.LANCZOS)

            # Save as 24-bit BMP (BMP3 format)
            output_buffer = io.BytesIO()
            image.save(
                output_buffer,
                format="BMP",
                bits=8,  # 8 bits per channel = 24-bit color
            )

            _LOGGER.debug(
                "Converted image: size=%s, output_bytes=%d",
                image.size,
                output_buffer.tell(),
            )

            return output_buffer.getvalue()

        except Exception as err:
            _LOGGER.error("Error converting image: %s", err)
            return None

    async def convert_and_save(self, image_url):
        """Download, convert, and save album art."""
        try:
            # Download the image
            image_data = await self.download_image(image_url)
            if not image_data:
                _LOGGER.warning("Failed to download image, using default")
                return await self.use_default_image()

            # Convert to BMP
            bmp_data = self.convert_to_bmp(image_data)
            if not bmp_data:
                _LOGGER.warning("Failed to convert image, using default")
                return await self.use_default_image()

            # Save to output file
            await self.hass.async_add_executor_job(
                self._write_file,
                self.output_path,
                bmp_data,
            )

            _LOGGER.info(
                "Successfully converted and saved album art to %s",
                self.output_path,
            )
            return True

        except Exception as err:
            _LOGGER.error("Unexpected error in convert_and_save: %s", err)
            return await self.use_default_image()

    async def use_default_image(self):
        """Copy default image to output location."""
        try:
            if not self.default_path.exists():
                _LOGGER.error(
                    "Default image not found at %s - creating blank image",
                    self.default_path,
                )
                await self._create_blank_image()
                return False

            # Copy default to output
            await self.hass.async_add_executor_job(
                self._copy_file,
                self.default_path,
                self.output_path,
            )

            _LOGGER.info("Used default image: %s", self.default_path)
            return True

        except Exception as err:
            _LOGGER.error("Error using default image: %s", err)
            # Last resort: create a blank image
            await self._create_blank_image()
            return False

    async def _create_blank_image(self):
        """Create a blank black image as ultimate fallback."""
        try:
            # Create blank RGB image
            blank = Image.new("RGB", (self.image_size, self.image_size), (0, 0, 0))

            # Save as BMP
            output_buffer = io.BytesIO()
            blank.save(output_buffer, format="BMP", bits=8)

            await self.hass.async_add_executor_job(
                self._write_file,
                self.output_path,
                output_buffer.getvalue(),
            )

            _LOGGER.info("Created blank fallback image")

        except Exception as err:
            _LOGGER.error("Failed to create blank image: %s", err)

    def _write_file(self, path, data):
        """Write data to file (sync operation for executor)."""
        with open(path, "wb") as f:
            f.write(data)

    def _copy_file(self, src, dst):
        """Copy file (sync operation for executor)."""
        import shutil
        shutil.copy2(src, dst)
