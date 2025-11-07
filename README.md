# Image Fetcher

A powerful and flexible tool to download and resize images from multiple sources including Pexels, Pixabay, and DuckDuckGo. Perfect for CapCut, video editing, or building image collections!

## Features

- **Multiple Image Sources**
  - Pexels (high-quality stock photos)
  - Pixabay (large variety of images)
  - DuckDuckGo (no API key required)

- **Smart Image Processing**
  - Automatic resizing to your target dimensions
  - Intelligent cropping to maintain aspect ratio
  - Converts all formats to optimized JPEGs

- **Category Filtering**
  - Filter by categories like nature, backgrounds, people, etc.
  - Source-specific category support

- **Multiple Interfaces**
  - Command-line interface (CLI)
  - Interactive mode with prompts
  - Web interface (browser-based)
  - Desktop GUI (tkinter)
  - Batch processing from files

## Installation

1. Clone or download this repository:
```bash
git clone <your-repo-url>
cd image-fetcher
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional but recommended) Configure API keys for better results:
```bash
python image_fetcher.py --setup
```

Get free API keys:
- Pexels: https://www.pexels.com/api/
- Pixabay: https://pixabay.com/api/docs/

## Usage

### 1. Command Line Interface (Quick Mode)

Basic usage:
```bash
python image_fetcher.py "sunset beach" 15
```

Advanced options:
```bash
# Specify image size
python image_fetcher.py "mountain landscape" 20 --size 1920x1080

# Choose specific sources
python image_fetcher.py "ocean waves" 10 --sources pexels pixabay

# Add category filter
python image_fetcher.py "riot protest" 10 --category nature --sources pexels pixabay

# Custom output directory
python image_fetcher.py "city skyline" 15 --output my_images
```

### 2. Interactive Mode

Run with prompts for all options:
```bash
python image_fetcher.py --interactive
```

Or use the shorthand:
```bash
python image_fetcher.py -i
```

### 3. Web Interface

Start the web server:
```bash
python web_app.py
```

Then open your browser to: `http://127.0.0.1:5000`

Features:
- User-friendly interface
- Real-time progress updates
- No command-line needed
- Perfect for non-technical users

### 4. Desktop GUI

Launch the desktop application:
```bash
python gui_app.py
```

Features:
- Native desktop application
- Easy API key configuration
- Real-time status updates
- Cross-platform (Windows, Mac, Linux)

### 5. Batch Processing

Create a text file with themes (one per line):

**themes.txt:**
```
sunset beach, 15
mountain landscape, 20
city skyline, 10
ocean waves
```

Run batch mode:
```bash
python image_fetcher.py --batch themes.txt
```

Or use the shorthand:
```bash
python image_fetcher.py -b themes.txt
```

## Examples

### Avoiding Gaming Images

When searching for topics like "riot" that might return gaming images (League of Legends Riot Games), use category filters:

```bash
# Use Pexels/Pixabay with category to get real photos
python image_fetcher.py "riot" 10 --sources pexels pixabay --category nature

# Or use interactive mode to specify filters
python image_fetcher.py -i
```

DuckDuckGo automatically excludes common gaming keywords like "game", "gaming", "league", "valorant", etc.

### Different Use Cases

**For video backgrounds (1920x1080):**
```bash
python image_fetcher.py "abstract backgrounds" 20 --category backgrounds
```

**For mobile wallpapers (1080x1920):**
```bash
python image_fetcher.py "nature scenes" 15 --size 1080x1920
```

**For thumbnails (1280x720):**
```bash
python image_fetcher.py "tech gadgets" 10 --size 1280x720
```

## Available Categories

### Pixabay Categories
- backgrounds
- fashion
- nature
- science
- education
- feelings
- health
- people
- religion
- places
- animals
- industry
- computer
- food
- sports
- transportation
- travel
- buildings
- business
- music

### Pexels Orientations
- landscape
- portrait
- square

## Command-Line Options

```
positional arguments:
  theme                 Search theme/query for images
  count                 Number of images to download

options:
  -h, --help            Show help message
  --size WIDTHxHEIGHT   Target image size (default: 1920x1080)
  --output DIR          Output directory (default: image_collections)
  --sources [...]       Image sources: pexels pixabay duckduckgo (default: all)
  --category CAT        Category filter (varies by source)
  --interactive, -i     Run in interactive mode
  --batch FILE, -b      Batch process themes from file
  --setup               Run API key setup wizard
```

## Configuration

API keys are stored in `~/.image_fetcher_config.json` or can be set via environment variables:

```bash
export PEXELS_API_KEY="your-pexels-key"
export PIXABAY_API_KEY="your-pixabay-key"
```

Run the setup wizard anytime:
```bash
python image_fetcher.py --setup
```

## Output

Images are saved to `image_collections/` (or your custom directory) in folders named:
```
<theme>_<timestamp>/
```

For example:
```
image_collections/
  sunset_beach_20250106_143022/
    sunset_beach_001.jpg
    sunset_beach_002.jpg
    ...
```

## Tips for Best Results

1. **Use API Keys**: Pexels and Pixabay provide much higher quality images than DuckDuckGo
2. **Be Specific**: Use detailed search terms like "sunset over ocean waves" instead of just "sunset"
3. **Use Categories**: Filter by category to get more relevant results
4. **Try Multiple Sources**: Use `--sources all` to get variety from all available sources
5. **Batch Processing**: Process multiple themes overnight for large collections

## Troubleshooting

**403 Rate Limit Error:**
- Wait a few minutes between searches
- Use API sources (Pexels/Pixabay) instead of DuckDuckGo
- The tool already includes rate limiting delays

**No API Key Errors:**
- Run `python image_fetcher.py --setup` to configure keys
- Or manually set environment variables

**Images Not Found:**
- Try different search terms
- Use category filters to refine results
- Try different sources

## Project Structure

```
image-fetcher/
├── image_fetcher.py      # Main CLI application
├── gui_app.py            # Desktop GUI application
├── web_app.py            # Web interface
├── config.py             # Configuration management
├── image_sources.py      # Image source providers
├── templates/
│   └── index.html        # Web interface template
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## License

This project is open source and available for personal and commercial use.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## Credits

- Uses Pexels API for high-quality stock photos
- Uses Pixabay API for diverse image content
- Uses DDGS (DuckDuckGo Search) for no-API-key searches
- Built with Python, Flask, and tkinter
