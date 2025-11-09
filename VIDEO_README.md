# 🎬 Video Fetcher - Advanced Multi-Source Video Scraper

A powerful, feature-rich video scraping tool that downloads high-quality videos from multiple sources with advanced filtering, parallel downloads, and a beautiful dark mode web interface.

## ✨ Features

### Core Capabilities
- **Multiple Video Sources**: Pexels, Pixabay (easily extensible)
- **Advanced Search & Filtering**: Quality, orientation, duration, category filters
- **Parallel Downloads**: Download multiple videos simultaneously for faster processing
- **Smart Quality Selection**: Automatic HD/Medium/High quality selection
- **Progress Tracking**: Real-time progress bars and statistics
- **Error Handling**: Robust retry logic and graceful error recovery
- **Metadata Export**: Saves video information for each download

### User Interfaces
- **Web Interface**: Modern, responsive UI with dark/light theme toggle
- **Command Line**: Full-featured CLI with interactive and batch modes
- **RESTful API**: Complete API for integration into other tools

### Web Interface Features
- 🌙 **Dark Mode**: Beautiful dark theme with light mode option
- 📊 **Real-time Progress**: Live download statistics and progress bars
- 🎯 **Advanced Filters**: Category, orientation, duration, quality filters
- ⚙️ **Settings Management**: Easy API key configuration
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile

## 🚀 Quick Start

### Installation

1. **Clone or navigate to the repository**:
```bash
cd image-fetcher
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure API keys** (optional but recommended):
```bash
python video_fetcher.py --setup
```

Or set environment variables:
```bash
export PEXELS_API_KEY="your_pexels_key"
export PIXABAY_API_KEY="your_pixabay_key"
```

### Getting API Keys

**Pexels** (Free):
- Visit: https://www.pexels.com/api/
- Sign up for a free account
- Get your API key instantly

**Pixabay** (Free):
- Visit: https://pixabay.com/api/docs/
- Sign up for a free account
- Get your API key

## 💻 Usage

### Web Interface (Recommended)

Start the web server:
```bash
python video_web_app.py
```

Then open your browser to: http://127.0.0.1:5001

The web interface provides:
- Interactive search form
- Real-time progress tracking
- Advanced filter options
- Dark/light theme toggle
- Settings management

### Command Line Interface

**Quick mode** - Download videos with one command:
```bash
python video_fetcher.py "ocean waves" 10
```

**With quality and sources**:
```bash
python video_fetcher.py "sunset timelapse" 20 --sources pexels,pixabay --quality hd
```

**Advanced filters**:
```bash
python video_fetcher.py "nature" 15 \
    --orientation landscape \
    --min-duration 10 \
    --max-duration 30 \
    --quality hd
```

**Interactive mode** - Guided prompts:
```bash
python video_fetcher.py -i
```

**Setup wizard**:
```bash
python video_fetcher.py --setup
```

## 🎯 Advanced Features

### Search Filters

**Quality Options**:
- `hd`: 1920x1080 or higher (Full HD)
- `medium`: 1280x720 (HD)
- `high`: Best available quality

**Orientation**:
- `landscape`: Horizontal videos
- `portrait`: Vertical videos (mobile-friendly)
- `square`: 1:1 ratio videos

**Duration Filters**:
- `--min-duration`: Minimum video length in seconds
- `--max-duration`: Maximum video length in seconds

**Categories** (Pixabay only):
- backgrounds, fashion, nature, science, education
- feelings, health, people, religion, places
- animals, industry, computer, food, sports
- transportation, travel, buildings, business, music

### Parallel Downloads

Configure simultaneous downloads in config:
```bash
python video_fetcher.py --setup
# Set parallel_downloads (1-10)
```

Or in `~/.video_fetcher_config.json`:
```json
{
  "parallel_downloads": 3
}
```

### Output Structure

Videos are saved to organized directories:
```
video_collections/
└── ocean_waves_20250109_143022/
    ├── ocean_waves_001.mp4
    ├── ocean_waves_002.mp4
    ├── ocean_waves_003.mp4
    └── metadata.txt
```

The `metadata.txt` file contains information about each video:
```
Theme: ocean waves
Downloaded: 2025-01-09 14:30:22
Sources: all
Quality: hd

ocean_waves_001.mp4:
  Source: pexels
  User: John Doe
  Dimensions: 1920x1080
  Duration: 15s
  URL: https://...
```

## 📡 API Reference

### Start a Fetch Job

```bash
POST /api/fetch
Content-Type: application/json

{
  "theme": "ocean waves",
  "count": 10,
  "sources": "all",
  "quality": "hd",
  "orientation": "landscape",
  "category": "nature",
  "min_duration": 5,
  "max_duration": 30
}
```

Response:
```json
{
  "job_id": 1
}
```

### Check Job Status

```bash
GET /api/status/<job_id>
```

Response:
```json
{
  "id": 1,
  "status": "running",
  "progress": "Downloaded 5/10 videos (0 failed)",
  "current": 5,
  "total": 10,
  "successful": 5,
  "failed": 0,
  "result_dir": "/path/to/videos"
}
```

### Update Configuration

```bash
POST /api/setup
Content-Type: application/json

{
  "pexels_key": "your_key",
  "pixabay_key": "your_key",
  "theme": "dark"
}
```

### Get Configuration

```bash
GET /api/config
```

## ⚙️ Configuration

Configuration is stored in `~/.video_fetcher_config.json`:

```json
{
  "pexels_api_key": "your_pexels_key",
  "pixabay_api_key": "your_pixabay_key",
  "default_source": "all",
  "default_quality": "hd",
  "default_orientation": null,
  "default_category": null,
  "output_dir": "video_collections",
  "min_duration": null,
  "max_duration": null,
  "min_width": 1280,
  "min_height": 720,
  "max_file_size_mb": 100,
  "parallel_downloads": 3,
  "theme": "dark"
}
```

### Configuration Priority

1. **Environment variables** (highest priority)
   - `PEXELS_VIDEO_API_KEY` or `PEXELS_API_KEY`
   - `PIXABAY_VIDEO_API_KEY` or `PIXABAY_API_KEY`

2. **Configuration file** (`~/.video_fetcher_config.json`)

3. **Default values** (lowest priority)

## 🎨 Web Interface Customization

### Theme Toggle

The web interface supports dark and light themes. Click the moon/sun icon in the top-right corner to toggle.

Theme preference is saved automatically and persists across sessions.

### Custom Port

Run the web server on a custom port:
```bash
python video_web_app.py --port 8080
```

Access on network:
```bash
python video_web_app.py --host 0.0.0.0 --port 5001
```

## 🔧 Advanced CLI Options

```
usage: video_fetcher.py [-h] [--sources SOURCES] [--quality {hd,medium,high}]
                        [--orientation {landscape,portrait,square}]
                        [--category CATEGORY] [--min-duration MIN_DURATION]
                        [--max-duration MAX_DURATION] [--min-width MIN_WIDTH]
                        [--min-height MIN_HEIGHT] [--output OUTPUT]
                        [-i] [--setup]
                        [theme] [count]

Advanced video fetcher with multiple sources

positional arguments:
  theme                 Video theme/search query
  count                 Number of videos to download

options:
  -h, --help            show this help message and exit
  --sources SOURCES     Comma-separated sources (all, pexels, pixabay)
  --quality {hd,medium,high}
                        Video quality preference
  --orientation {landscape,portrait,square}
                        Video orientation filter
  --category CATEGORY   Category filter (for Pixabay)
  --min-duration MIN_DURATION
                        Minimum video duration (seconds)
  --max-duration MAX_DURATION
                        Maximum video duration (seconds)
  --min-width MIN_WIDTH
                        Minimum video width
  --min-height MIN_HEIGHT
                        Minimum video height
  --output OUTPUT       Output directory
  -i, --interactive     Interactive mode
  --setup              Run configuration setup wizard
```

## 📊 Examples

### Example 1: Nature Videos for Social Media
```bash
python video_fetcher.py "mountain sunset" 20 \
    --quality hd \
    --orientation portrait \
    --min-duration 5 \
    --max-duration 15
```

### Example 2: Background Videos for Website
```bash
python video_fetcher.py "abstract motion" 10 \
    --category backgrounds \
    --orientation landscape \
    --quality high \
    --min-duration 10
```

### Example 3: Quick Timelapse Collection
```bash
python video_fetcher.py "city timelapse" 15 \
    --sources pexels \
    --quality hd \
    --orientation landscape
```

## 🐛 Troubleshooting

### No videos found
- Check your API keys are configured correctly
- Try different search terms
- Verify you have internet connection
- Check API rate limits haven't been exceeded

### Downloads are slow
- Increase `parallel_downloads` in configuration (max 10)
- Try using `medium` quality instead of `hd`
- Check your internet connection speed

### Videos are too large
- Lower the `max_file_size_mb` in configuration
- Use `medium` quality instead of `hd`
- Set `max_duration` to limit video length

### API key errors
- Verify keys are valid and active
- Check you haven't exceeded rate limits
- Ensure keys are for the correct service

## 📝 Notes

- **API Rate Limits**: Free tier API keys have rate limits. Be respectful!
- **File Sizes**: HD videos can be large (10-100MB each). Plan storage accordingly.
- **Quality vs Speed**: Higher quality = larger files = slower downloads
- **Sources**: More sources = more variety but slower searches

## 🤝 Contributing

To add new video sources:

1. Create a new class in `video_sources.py` inheriting from `VideoSource`
2. Implement `search()` and `get_name()` methods
3. Add the source to `VideoSourceManager.__init__()`
4. Update documentation

Example:
```python
class NewVideoSource(VideoSource):
    def search(self, query, max_results=10, **kwargs):
        # Implementation here
        return videos

    def get_name(self):
        return "newsource"
```

## 📄 License

This project builds on the image-fetcher codebase and follows the same license terms.

## 🙏 Credits

Video sources:
- **Pexels**: https://www.pexels.com/
- **Pixabay**: https://pixabay.com/

Built with:
- Flask (Web framework)
- Requests (HTTP library)
- tqdm (Progress bars)

## 📞 Support

For issues, questions, or feature requests, please check:
1. This README for common solutions
2. Configuration file for settings
3. API documentation for the sources you're using

---

**Happy video collecting!** 🎬✨
