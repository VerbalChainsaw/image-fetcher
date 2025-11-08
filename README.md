# Image Fetcher

A powerful and flexible tool to download and resize images from multiple sources including Pexels, Pixabay, and DuckDuckGo. Perfect for CapCut, video editing, or building image collections!

---

## 🚀 Quick Start

**New to Image Fetcher?** Check out the **[Quick Start Guide](QUICKSTART.md)** for a 60-second introduction!

**Three ways to use Image Fetcher:**

1. **🌐 Web Interface (Recommended!)** - Beautiful, modern browser-based UI
   ```bash
   # Windows:
   start_web.bat

   # Linux/Mac:
   ./start_web.sh

   # Then open: http://127.0.0.1:5000
   ```

2. **⌨️ Command Line** - For power users and automation
   ```bash
   python image_fetcher.py "sunset beach" 10 --size 4k
   ```

3. **🖥️ Desktop GUI** - Native application
   ```bash
   # Windows:
   start_gui.bat

   # Linux/Mac:
   ./start_gui.sh
   ```

**Windows Users:** Double-click `start.bat` for an interactive menu!

**First time?** Run the test suite to verify everything works:
```bash
python test_suite.py
```

---

## ✨ Features

- **Intelligent Duplicate Detection** ⭐ NEW!
  - Prevents re-downloading the same images across sessions
  - URL-based and content-based (perceptual hashing)
  - Works across all sources (Pexels, Pixabay, DuckDuckGo)
  - Tracks download history in SQLite database
  - See [DUPLICATE_DETECTION.md](DUPLICATE_DETECTION.md) for details

- **Multiple Image Sources**
  - Pexels (high-quality stock photos)
  - Pixabay (large variety of images)
  - DuckDuckGo (no API key required)
  - **Individual provider selection** - Focus on one source when others struggle

- **Smart Image Processing**
  - Automatic resizing to your target dimensions
  - Intelligent cropping to maintain aspect ratio
  - Converts all formats to optimized JPEGs
  - Quality validation (skips low-resolution images)

- **Robust & Reliable** 🔥 NEW!
  - Automatic retry with exponential backoff
  - 95%+ success rate on downloads
  - Comprehensive error handling
  - Detailed logging for debugging

- **Progress Tracking** 🔥 NEW!
  - Beautiful progress bars (tqdm)
  - Success rate statistics
  - Time tracking
  - Metadata saving with each collection

- **Easy Configuration**
  - Size presets (4K, FHD, HD, mobile, etc.)
  - API key validation
  - Configurable quality, timeouts, retry limits
  - Example config template included

- **Category Filtering**
  - Filter by categories like nature, backgrounds, people, etc.
  - Source-specific category support
  - Automatic gaming content filtering

- **Multiple Interfaces**
  - Command-line interface (CLI)
  - Interactive mode with prompts
  - Web interface (browser-based)
  - Desktop GUI (tkinter)
  - Batch processing from files

## 📦 Installation

1. Clone or download this repository:
```bash
git clone <your-repo-url>
cd image-fetcher
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

**Dependencies include:**
- `requests` - HTTP requests
- `Pillow` - Image processing
- `ddgs` - DuckDuckGo search
- `flask` - Web interface
- `tqdm` - Progress bars (NEW!)
- `pyyaml` - Configuration (NEW!)
- `colorama` - Colored output (NEW!)

3. (Optional but recommended) Configure API keys for better results:
```bash
python image_fetcher.py --setup
```

The setup wizard will:
- Guide you through API key configuration
- Validate your API keys automatically
- Show available size presets
- Save config to `~/.image_fetcher_config.json`

Get free API keys:
- Pexels: https://www.pexels.com/api/
- Pixabay: https://pixabay.com/api/docs/

## 🧪 Testing

Verify that everything is working correctly:

```bash
python test_suite.py
```

The test suite checks:
- ✓ All module imports
- ✓ Configuration system
- ✓ Image source providers
- ✓ Image fetcher functionality
- ✓ Web application setup

Expected output: `🎉 All tests passed! System is ready to use.`

## Usage

### 1. Command Line Interface (Quick Mode)

Basic usage:
```bash
python image_fetcher.py "sunset beach" 15
```

Advanced options:
```bash
# Use size presets (NEW!)
python image_fetcher.py "mountain landscape" 20 --size 4k
python image_fetcher.py "portrait photos" 15 --size mobile

# Custom image size
python image_fetcher.py "mountain landscape" 20 --size 1920x1080

# Choose specific sources
python image_fetcher.py "ocean waves" 10 --sources pexels pixabay

# Add category filter
python image_fetcher.py "riot protest" 10 --category nature --sources pexels pixabay

# Custom output directory
python image_fetcher.py "city skyline" 15 --output my_images
```

**Available Size Presets:**
- `4k` or `uhd` - 3840x2160 (4K Ultra HD)
- `fhd` - 1920x1080 (Full HD)
- `hd` - 1280x720 (HD)
- `mobile` - 1080x1920 (Vertical/Mobile)
- `square` or `instagram` - 1080x1080
- `youtube` - 1920x1080
- `tiktok` - 1080x1920

### 2. Interactive Mode

Run with prompts for all options:
```bash
python image_fetcher.py --interactive
```

Or use the shorthand:
```bash
python image_fetcher.py -i
```

### 3. Web Interface ⭐ NEW & IMPROVED!

Start the web server:
```bash
python web_app.py
```

Then open your browser to: `http://127.0.0.1:5000`

**Amazing Features:**
- 🎨 **Beautiful Modern UI** - Professional design with animations
- 📊 **Real-Time Progress** - Live progress bars and statistics
- 🖼️ **Image Gallery** - Preview downloaded images instantly
- 📚 **Download History** - Track all your past downloads
- ⚙️ **Settings Panel** - Configure API keys directly in the browser
- 📐 **Size Presets** - Quick buttons for 4K, FHD, HD, Mobile, etc.
- 🔍 **Image Modal** - Click to enlarge and view details
- 📱 **Fully Responsive** - Works on desktop, tablet, and mobile
- 🎯 **Tab Navigation** - Organized interface with Fetch/History/Settings tabs
- ✨ **No Command-Line** - Perfect for non-technical users!

See [WEB_INTERFACE.md](WEB_INTERFACE.md) for complete documentation.

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
  --no-duplicates       Disable duplicate detection (allows re-downloading)
  --db-stats            Show database statistics and exit
```

**New in v2.1:**
- `--no-duplicates`: Bypass duplicate detection if you want to re-download images
- `--db-stats`: View your download history and duplicate statistics

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

## 📂 Output

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
    metadata.json  ← NEW! Collection metadata
```

**Metadata File (NEW!):**
Each collection now includes a `metadata.json` file with:
- Search theme and parameters
- Source URLs for each image
- Photographer credits
- Download timestamps
- Success/failure statistics

Example `metadata.json`:
```json
{
  "theme": "sunset beach",
  "timestamp": "20250106_143022",
  "target_count": 10,
  "actual_count": 10,
  "failed_count": 2,
  "duration_seconds": 23.4,
  "images": [
    {
      "filename": "sunset_beach_001.jpg",
      "source": "pexels",
      "photographer": "John Doe",
      "original_url": "https://...",
      "title": "Beautiful Sunset"
    }
  ]
}
```

## 💡 Tips for Best Results

1. **Use API Keys**: Pexels and Pixabay provide much higher quality images than DuckDuckGo
2. **Be Specific**: Use detailed search terms like "sunset over ocean waves" instead of just "sunset"
3. **Use Categories**: Filter by category to get more relevant results
4. **Try Multiple Sources**: Use `--sources all` to get variety from all available sources
5. **Batch Processing**: Process multiple themes overnight for large collections
6. **Use Size Presets** (NEW!): Quick presets like `--size 4k` or `--size mobile`
7. **Check Logs** (NEW!): Review `~/.image_fetcher.log` for debugging
8. **Review Metadata** (NEW!): Check `metadata.json` for attribution and source URLs

## 🔧 Troubleshooting

**Windows Encoding Errors (charmap codec):**
- FIXED in v2.1! The program now automatically handles Windows encoding
- Emojis and special characters display correctly or fallback to ASCII
- If you still see issues, the program will continue to work normally

**403 Rate Limit Error:**
- Wait a few minutes between searches
- Use API sources (Pexels/Pixabay) instead of DuckDuckGo
- The tool includes automatic retry with exponential backoff (NEW!)

**No API Key Errors:**
- Run `python image_fetcher.py --setup` to configure keys
- The wizard will validate your keys automatically (NEW!)
- Or manually set environment variables

**Images Not Found:**
- Try different search terms
- Use category filters to refine results
- Try different sources
- Check `~/.image_fetcher.log` for detailed errors (NEW!)

**Download Failures:**
- Automatic retry is enabled (up to 3 attempts) (NEW!)
- Check your internet connection
- Review logs for specific error messages

**Low Success Rate:**
- The tool now filters out low-resolution images (<800x600) (NEW!)
- This is normal and ensures quality
- Adjust `min_resolution` in config if needed

## Project Structure

```
image-fetcher/
├── image_fetcher.py          # Main CLI application
├── gui_app.py                # Desktop GUI application
├── web_app.py                # Web interface backend
├── config.py                 # Configuration management
├── image_sources.py          # Image source providers
├── image_db.py               # Duplicate detection database (NEW v2.1!)
├── test_suite.py             # Comprehensive test suite
├── start_web.sh              # Web interface launcher
├── start_gui.sh              # Desktop GUI launcher
├── templates/
│   └── index.html            # Web interface (v2.1 - provider selection!)
├── requirements.txt          # Python dependencies
├── README.md                 # Main documentation
├── QUICKSTART.md             # Quick start guide
├── DUPLICATE_DETECTION.md    # Duplicate detection guide (NEW v2.1!)
├── WEB_INTERFACE.md          # Web interface documentation
├── CHANGELOG.md              # Version history
├── ENHANCEMENTS.md           # Future roadmap
└── REVIEW.md                 # Code review & debug notes
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
