# CLAUDE.md - AI Assistant Guide for Image Fetcher

## Project Overview

**Image Fetcher** is a Python-based tool for downloading and processing images from multiple sources (Pexels, Pixabay, DuckDuckGo). It provides multiple interfaces (CLI, web, GUI) for flexible usage across different user preferences and environments.

**Primary Use Case**: Download themed image collections for video editing (especially CapCut), presentations, or any project requiring curated image sets.

**Key Features**:
- Multi-source image aggregation (Pexels, Pixabay, DuckDuckGo)
- Automatic image resizing and cropping to target dimensions
- Category-based filtering
- Multiple user interfaces (CLI, web, desktop GUI)
- Batch processing capabilities
- API key management

## Architecture

### High-Level Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   CLI    │  │   Web    │  │   GUI    │  │  Batch   │   │
│  │ (main)   │  │ (Flask)  │  │(tkinter) │  │  Mode    │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                         │
        ┌────────────────▼────────────────┐
        │      ImageFetcher (Core)        │
        │  - search_images()              │
        │  - download_image()             │
        │  - resize_and_crop()            │
        │  - fetch_and_process()          │
        └────────────┬────────────────────┘
                     │
        ┌────────────▼────────────────┐
        │   ImageSourceManager        │
        │   - Aggregates sources      │
        │   - Distributes requests    │
        └────────────┬────────────────┘
                     │
        ┌────────────┴────────────────┐
        │                             │
   ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐
   │ Pexels   │  │ Pixabay  │  │DuckDuck  │
   │ Source   │  │ Source   │  │Go Source │
   └──────────┘  └──────────┘  └──────────┘
```

### Core Components

1. **image_fetcher.py** - Main application logic
   - `ImageFetcher` class: Core image fetching and processing
   - CLI argument parsing and mode handling
   - Interactive and batch mode implementations

2. **image_sources.py** - Image source providers
   - `ImageSource` base class
   - `PexelsSource`, `PixabaySource`, `DuckDuckGoSource` implementations
   - `ImageSourceManager`: Aggregates and manages sources

3. **config.py** - Configuration management
   - `Config` class: API key storage and retrieval
   - Environment variable and file-based configuration
   - Setup wizard for user configuration

4. **web_app.py** - Flask web interface
   - REST API endpoints
   - Background job processing with threads
   - Job status tracking

5. **gui_app.py** - Desktop GUI
   - Tkinter-based UI
   - Threading for non-blocking operations
   - API key setup dialog

6. **templates/index.html** - Web interface frontend
   - Modern, responsive design
   - Asynchronous job status polling
   - Form validation

## File Organization

```
image-fetcher/
├── image_fetcher.py      # Main CLI application (entry point)
├── config.py             # Configuration and API key management
├── image_sources.py      # Image source providers and manager
├── web_app.py            # Flask web server
├── gui_app.py            # Tkinter desktop GUI
├── templates/
│   └── index.html        # Web interface HTML/CSS/JS
├── requirements.txt      # Python dependencies
├── README.md            # User documentation
└── CLAUDE.md           # This file (AI assistant guide)

# Runtime directories (created automatically):
├── image_collections/   # Default output directory
│   └── <theme>_<timestamp>/
│       └── <theme>_001.jpg, ...
└── ~/.image_fetcher_config.json  # User config file (in home dir)
```

## Code Conventions

### Python Style
- **PEP 8 compliance**: Follow standard Python style guidelines
- **Docstrings**: All public classes and methods have docstrings
- **Type hints**: Not currently used, but welcome in new code
- **Error handling**: Try-except blocks with user-friendly error messages
- **Emoji usage**: Used in CLI output for visual clarity (✓, ✗, 📁, 🔍, etc.)

### Naming Conventions
- **Classes**: PascalCase (e.g., `ImageFetcher`, `PexelsSource`)
- **Functions/Methods**: snake_case (e.g., `fetch_and_process`, `search_images`)
- **Constants**: Not strictly enforced, but use UPPER_CASE for true constants
- **Private methods**: Prefix with underscore (e.g., `_internal_method`)

### File Naming
- **Python modules**: snake_case (e.g., `image_sources.py`)
- **Output files**: `<theme>_<number>.jpg` (e.g., `sunset_beach_001.jpg`)
- **Directories**: `<theme>_<timestamp>` (e.g., `sunset_beach_20250106_143022`)

## Key Technical Patterns

### 1. Plugin Architecture for Image Sources
Each source implements the `ImageSource` base class:
```python
class ImageSource:
    def search(self, query, max_results=10, category=None):
        raise NotImplementedError
```

**When adding new sources**:
1. Create new class inheriting from `ImageSource`
2. Implement `search()` method returning list of dicts with keys: `url`, `thumbnail`, `source`, `photographer`
3. Register in `ImageSourceManager.__init__()`

### 2. Configuration Priority
Configuration is loaded in this order (later overrides earlier):
1. Default values in code
2. `~/.image_fetcher_config.json` file
3. Environment variables (`PEXELS_API_KEY`, `PIXABAY_API_KEY`)

### 3. Image Processing Pipeline
1. **Search** → Get image URLs from sources
2. **Download** → Fetch raw images (with retries)
3. **Process** → Convert to RGB, resize with aspect ratio preservation
4. **Crop** → Center-crop to exact target dimensions
5. **Save** → Save as JPEG with 95% quality

### 4. Threading Model
- **Web app**: Background threads for long-running fetch operations
- **GUI app**: Threading to prevent UI blocking
- **CLI**: Synchronous execution (no threading needed)

## Development Workflows

### Adding a New Image Source

1. **Create source class** in `image_sources.py`:
```python
class NewSource(ImageSource):
    def __init__(self, api_key=None):
        self.api_key = api_key

    def search(self, query, max_results=10, category=None):
        # Implement API call
        # Return list of dicts with: url, thumbnail, source, photographer
        pass
```

2. **Register in ImageSourceManager**:
```python
def __init__(self, config):
    # ... existing sources ...
    new_key = config.get_api_key('newsource')
    if new_key:
        self.sources['newsource'] = NewSource(new_key)
```

3. **Update config.py** if API key needed:
```python
def load_config(self):
    config = {
        # ... existing keys ...
        'newsource_api_key': '',
    }
```

4. **Update CLI arguments** in `image_fetcher.py`:
```python
parser.add_argument('--sources', type=str, nargs='+',
                   help='Image sources: pexels pixabay duckduckgo newsource')
```

5. **Update documentation** in README.md

### Adding CLI Features

1. Add argument to `argparse` in `main()` function
2. Parse and validate argument
3. Pass to `ImageFetcher` methods
4. Update help text and examples
5. Update README.md with usage examples

### Modifying Image Processing

The resize/crop logic is in `ImageFetcher.resize_and_crop()`:
- Always converts to RGB (handles RGBA, grayscale, etc.)
- Maintains aspect ratio during resize
- Center-crops to exact dimensions
- Uses LANCZOS resampling for quality

**To modify**:
1. Edit `resize_and_crop()` method in `image_fetcher.py`
2. Consider adding optional parameters (quality, resampling method)
3. Test with various input formats and sizes

### Web Interface Changes

**Backend** (web_app.py):
- Add new route with `@app.route()` decorator
- Follow REST conventions (`/api/...` for API endpoints)
- Use `jsonify()` for JSON responses
- Thread long operations with `threading.Thread`

**Frontend** (templates/index.html):
- Modern CSS with gradients and transitions
- Vanilla JavaScript (no frameworks)
- Async/await for API calls
- Poll-based status updates

## Testing Considerations

### Manual Testing Checklist
- [ ] CLI mode with various arguments
- [ ] Interactive mode with all options
- [ ] Batch mode with sample file
- [ ] Web interface on different browsers
- [ ] GUI on target platforms (Windows, Mac, Linux)
- [ ] API key setup wizard
- [ ] Error handling (network failures, invalid inputs)
- [ ] Rate limiting with DuckDuckGo
- [ ] Various image formats (JPEG, PNG, WebP, etc.)
- [ ] Edge cases (1 image, 100 images, invalid themes)

### Common Test Scenarios
```bash
# Basic functionality
python image_fetcher.py "sunset" 5

# All sources
python image_fetcher.py "mountain" 10 --sources pexels pixabay duckduckgo

# Category filtering
python image_fetcher.py "riot" 10 --category nature --sources pexels pixabay

# Custom size
python image_fetcher.py "ocean" 10 --size 1920x1080

# Interactive mode
python image_fetcher.py -i

# Batch mode
echo "sunset,5\nmountain,10" > test_themes.txt
python image_fetcher.py -b test_themes.txt

# Web interface
python web_app.py

# GUI
python gui_app.py
```

## Common Development Tasks

### Task: Add support for new image dimension presets

1. Add constant in `image_fetcher.py`:
```python
PRESETS = {
    'hd': (1920, 1080),
    '4k': (3840, 2160),
    'mobile': (1080, 1920),
    'square': (1080, 1080)
}
```

2. Update CLI argument parsing:
```python
parser.add_argument('--preset', choices=list(PRESETS.keys()))
```

3. Apply preset in main():
```python
if args.preset:
    size = PRESETS[args.preset]
```

### Task: Add progress callback for GUI updates

1. Modify `ImageFetcher.fetch_and_process()` to accept callback:
```python
def fetch_and_process(self, theme, num_images=10, sources='all',
                     category=None, progress_callback=None):
    # ...
    if progress_callback:
        progress_callback(f"Downloading {saved_count}/{num_images}")
```

2. Update callers to pass callback function

### Task: Implement image deduplication

1. Add hash function (use PIL's Image.tobytes() and hashlib)
2. Track hashes in `fetch_and_process()`
3. Skip duplicates before saving
4. Optionally add `--allow-duplicates` flag

## Important Gotchas and Edge Cases

### Rate Limiting
- **DuckDuckGo**: Has aggressive rate limiting; 1-second delay between requests
- **Pexels**: 200 requests/hour (free tier)
- **Pixabay**: 5000 requests/hour (free tier)

**Solution**: Built-in delays in source implementations. Consider exponential backoff for failures.

### Image Format Handling
- Some sources return WebP, PNG, or RGBA images
- Always convert to RGB before saving as JPEG
- Handle transparency by converting to white background or specified color

### Category Filtering Differences
- **Pixabay**: Fixed category list (nature, backgrounds, etc.)
- **Pexels**: Uses orientation (landscape, portrait, square)
- **DuckDuckGo**: No native category support; uses negative keywords

**Convention**: Document category differences in help text and README

### File Naming Safety
- Theme names may contain special characters
- Sanitize with: `"".join(c for c in theme if c.isalnum() or c in (' ', '-', '_'))`
- Replace spaces with underscores for filesystem compatibility

### Threading and Job Management
- Web app uses global `jobs` dict (not production-ready)
- For production: Use database, Redis, or Celery
- GUI uses daemon threads (automatically exit with main program)

### API Key Security
- Never commit API keys to git
- Store in `~/.image_fetcher_config.json` (user home directory)
- Support environment variables for CI/CD
- `.gitignore` should include `*config.json`

## Git Workflow

### Branch Strategy
- **Main branch**: Stable, production-ready code
- **Feature branches**: `feature/description` or `claude/session-id`
- **Bug fixes**: `fix/description`

### Commit Messages
Follow conventional commits style:
- `feat: Add new image source support`
- `fix: Handle RGBA to RGB conversion correctly`
- `docs: Update README with batch mode examples`
- `refactor: Extract image processing into separate method`

### Before Committing
1. Test affected functionality
2. Check for hardcoded API keys or secrets
3. Update README.md if user-facing changes
4. Update this CLAUDE.md if architecture changes

## API Documentation

### ImageFetcher Class

**Constructor**:
```python
ImageFetcher(config, output_dir=None, target_size=(1920, 1080))
```

**Key Methods**:
- `search_images(theme, max_images, sources, category)` → List[dict]
- `download_image(url, timeout)` → PIL.Image | None
- `resize_and_crop(img)` → PIL.Image
- `fetch_and_process(theme, num_images, sources, category)` → Path

### Config Class

**Methods**:
- `load_config()` → dict
- `save_config()` → bool
- `get_api_key(service)` → str
- `set_api_key(service, api_key)` → bool
- `setup_wizard()` → None (interactive)

### ImageSourceManager

**Methods**:
- `search(query, max_results, sources, category)` → List[dict]
- `get_available_sources()` → List[str]

**Image dict format**:
```python
{
    'url': str,           # Full-resolution image URL
    'thumbnail': str,     # Thumbnail URL
    'source': str,        # 'pexels' | 'pixabay' | 'duckduckgo'
    'photographer': str   # Photographer name or 'Unknown'
}
```

## Environment Variables

- `PEXELS_API_KEY`: Pexels API key (overrides config file)
- `PIXABAY_API_KEY`: Pixabay API key (overrides config file)

## Dependencies

**Core**:
- `Pillow` (>= 10.0.0): Image processing
- `requests` (>= 2.31.0): HTTP client
- `ddgs` (>= 1.0.0): DuckDuckGo image search

**Web Interface**:
- `flask` (>= 3.0.0): Web framework

**GUI**:
- `tkinter`: Built-in Python GUI library (no pip install needed)

## Performance Considerations

### Bottlenecks
1. **Network I/O**: Downloading images (largest bottleneck)
2. **Image processing**: Resize/crop operations
3. **Disk I/O**: Saving files

### Optimization Strategies
- **Parallel downloads**: Consider `concurrent.futures.ThreadPoolExecutor`
- **Caching**: Cache search results (avoid re-searching same theme)
- **Lazy loading**: For GUI, load thumbnails before full images
- **Connection pooling**: Reuse HTTP connections with `requests.Session()`

### Memory Management
- Process images one at a time (current implementation)
- Don't load all images into memory before processing
- Consider streaming large downloads

## Security Considerations

### API Key Handling
- Store in user home directory (`~/.image_fetcher_config.json`)
- File should have restrictive permissions (0600 on Unix)
- Never log API keys
- Validate API key format before saving

### User Input Validation
- Sanitize theme names for filesystem
- Validate count (1-100 range enforced in web app)
- Validate image dimensions (positive integers)
- Escape HTML in web interface (Flask auto-escapes with Jinja2)

### Network Security
- Use HTTPS for all API calls
- Set reasonable timeouts (10 seconds default)
- Handle SSL certificate validation errors gracefully
- User-Agent header to identify application

## Future Enhancement Ideas

### High Priority
- [ ] Add automated testing (pytest)
- [ ] Support custom output filename patterns
- [ ] Add image metadata preservation (EXIF)
- [ ] Implement proper logging (Python logging module)

### Medium Priority
- [ ] Add more image sources (Unsplash, Flickr)
- [ ] Support video thumbnail extraction
- [ ] Add image filters (B&W, sepia, etc.)
- [ ] Export collection metadata (JSON manifest)

### Low Priority
- [ ] Database for search history and favorites
- [ ] User accounts in web interface
- [ ] Scheduled/automated fetching
- [ ] Integration with cloud storage (S3, Drive)

## AI Assistant Guidelines

### When Making Changes

1. **Understand context**: Read related code before modifying
2. **Maintain consistency**: Follow existing patterns and style
3. **Test thoroughly**: Manually test all affected interfaces
4. **Update documentation**: Keep README.md and CLAUDE.md in sync
5. **Consider all interfaces**: Changes may affect CLI, web, and GUI

### Best Practices

- **Preserve backwards compatibility**: Don't break existing CLI arguments
- **Fail gracefully**: Always provide helpful error messages
- **User-friendly output**: Use emojis and formatting in CLI
- **Cross-platform**: Test paths work on Windows, Mac, Linux
- **Resource cleanup**: Close files, sessions, and threads properly

### Common Mistakes to Avoid

- Hardcoding file paths (use Path, expanduser)
- Breaking API key configuration (test with and without keys)
- Forgetting to update all interfaces when changing core logic
- Not handling network failures (always use timeouts and try-except)
- Ignoring rate limits (especially DuckDuckGo)

### When Uncertain

- Check git history: `git log --oneline`
- Look at recent commits for patterns
- Test in interactive mode first
- Ask user for clarification on requirements
- Propose changes before implementing

## Quick Reference Commands

```bash
# Run CLI
python image_fetcher.py "theme" 10

# Interactive mode
python image_fetcher.py -i

# Setup wizard
python image_fetcher.py --setup

# Batch processing
python image_fetcher.py -b themes.txt

# Web interface
python web_app.py

# Desktop GUI
python gui_app.py

# Install dependencies
pip install -r requirements.txt

# View git history
git log --oneline --graph --all

# Check current status
git status
```

## Support and Resources

### External Documentation
- [Pexels API Docs](https://www.pexels.com/api/documentation/)
- [Pixabay API Docs](https://pixabay.com/api/docs/)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [Flask Documentation](https://flask.palletsprojects.com/)

### Project Resources
- **User Documentation**: See README.md
- **Issue Tracking**: GitHub Issues (if applicable)
- **Git Repository**: Current working directory

---

**Last Updated**: 2025-01-15
**Version**: 1.0
**Maintainer**: Repository owner

This document should be updated whenever significant architectural changes are made to the codebase.
