# Convert Media Album Art for Home Assistant

A Home Assistant custom integration that monitors a media player entity and automatically converts album art to BMP format suitable for ESPHome displays.

## Features

- Monitors any media player entity for album art changes
- Automatically downloads and converts album art to BMP format
- Configurable output size and location
- Supports default/fallback images
- Perfect for ESPHome display projects

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/zembrzycki/HACS-integration-convert-media-album-art`
6. Select category "Integration"
7. Click "Add"
8. Find "Convert Media Album Art" in the integrations list
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/convert_media_album_art` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Convert Media Album Art"
4. Configure:
   - **Media Player Entity**: Select your media player
   - **Output Directory**: Where to save the converted image (default: `www`)
   - **Output Filename**: Name of the output file (default: `media_album.bmp`)
   - **Default Image**: Fallback image filename (default: `blank_album.bmp`)
   - **Image Size**: Square dimensions in pixels (default: 200)

## Usage

Once configured, the integration will:
1. Monitor the selected media player for album art changes
2. Download the album art when media is playing
3. Convert it to a square BMP image
4. Save it to the configured location

You can then reference this image in your ESPHome configuration:

```yaml
display:
  - platform: ...
    lambda: |-
      it.image(0, 0, id(album_art));

image:
  - file: "http://YOUR_HA_IP:8123/local/media_album.bmp"
    id: album_art
    resize: 200x200
    type: RGB24
```

## Requirements

- Home Assistant 2024.1.0 or newer
- Pillow >= 10.0.0 (installed automatically)

## License

MIT License - see LICENSE file for details
