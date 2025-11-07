# Image Fetcher for CapCut

A Python tool that searches for images based on a theme, downloads them, resizes them to consistent dimensions, and saves them ready for import into CapCut or any video editing software.

## Features

- Search images using DuckDuckGo (no API key required)
- Download multiple images based on a theme
- Automatically resize and crop to consistent dimensions
- Organize images in timestamped folders
- Perfect for creating video montages in CapCut

## Installation

1. Make sure you have Python 3.7+ installed

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Basic usage:
```bash
python image_fetcher.py "your theme" number_of_images
```

### Examples

Download 15 beach sunset images (default 1920x1080):
```bash
python image_fetcher.py "sunset beach" 15
```

Download 20 mountain images with custom size for vertical video:
```bash
python image_fetcher.py "mountain landscape" 20 --size 1080 1920
```

Download 10 city images to a custom folder:
```bash
python image_fetcher.py "city skyline" 10 --output my_collections
```

### Common CapCut Sizes

- **Standard HD (landscape)**: `--size 1920 1080` (default)
- **Standard HD (portrait)**: `--size 1080 1920`
- **4K (landscape)**: `--size 3840 2160`
- **TikTok/Reels (portrait)**: `--size 1080 1920`
- **YouTube Shorts (portrait)**: `--size 1080 1920`
- **Instagram Square**: `--size 1080 1080`

## Output

Images are saved to:
```
image_collections/
  └── theme_name_YYYYMMDD_HHMMSS/
      ├── theme_name_001.jpg
      ├── theme_name_002.jpg
      └── ...
```

Each run creates a new folder with a timestamp, so your collections never overwrite each other.

## Options

```
python image_fetcher.py [-h] [--size WIDTH HEIGHT] [--output OUTPUT] theme count

Positional arguments:
  theme                 Search theme/query for images
  count                 Number of images to download

Optional arguments:
  -h, --help           Show help message
  --size WIDTH HEIGHT  Target image size (default: 1920 1080)
  --output OUTPUT      Output base directory (default: image_collections)
```

## Tips

- Be specific with your theme for better results (e.g., "tropical beach sunset" instead of just "beach")
- The script downloads extra images and filters out failures, so you should get the number you requested
- All images are automatically cropped from the center to maintain the aspect ratio
- Images are saved as high-quality JPEGs (95% quality)

## Troubleshooting

**No images found:**
- Try a different or more general search term
- Check your internet connection

**Download failures:**
- This is normal - the script downloads more than needed and skips failed downloads
- If many downloads fail, try again later or use a different theme

**Image quality issues:**
- Try more specific search terms
- Results depend on what's available via DuckDuckGo search
