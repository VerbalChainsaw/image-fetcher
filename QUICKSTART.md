# 🚀 Quick Start Guide

Get started with Image Fetcher in 60 seconds!

---

## Option 1: Web Interface (Recommended!) 🌐

**The easiest way - beautiful UI, no command-line needed!**

```bash
# Start the web server
./start_web.sh
# or
python web_app.py
```

Then open your browser to: **http://127.0.0.1:5000**

### What You'll See:
- 🎨 Beautiful purple gradient interface
- 📐 Size preset buttons (4K, FHD, HD, Mobile, etc.)
- 📊 Real-time progress bars
- 🖼️ Image gallery with previews
- 📚 Download history
- ⚙️ Settings panel

---

## Option 2: Command Line (For Power Users) ⌨️

### Basic Usage:
```bash
python image_fetcher.py "sunset beach" 10
```

### With Size Presets:
```bash
python image_fetcher.py "mountains" 15 --size 4k
python image_fetcher.py "cityscape" 20 --size mobile
```

### Choose Sources:
```bash
python image_fetcher.py "ocean" 10 --sources pexels pixabay
```

### Interactive Mode:
```bash
python image_fetcher.py -i
```

---

## Option 3: Desktop GUI 🖥️

```bash
./start_gui.sh
# or
python gui_app.py
```

---

## First Time Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys (Optional but Recommended)
```bash
python image_fetcher.py --setup
```

Get free API keys:
- **Pexels**: https://www.pexels.com/api/
- **Pixabay**: https://pixabay.com/api/docs/

**Note**: Without API keys, only DuckDuckGo source is available.

---

## Testing

Run the test suite to verify everything works:
```bash
python test_suite.py
```

Expected output: `🎉 All tests passed!`

---

## Quick Examples

### For Video Editing (1920x1080):
```bash
python image_fetcher.py "nature backgrounds" 20 --size fhd
```

### For Mobile Wallpapers (1080x1920):
```bash
python image_fetcher.py "abstract art" 15 --size mobile
```

### For 4K Projects:
```bash
python image_fetcher.py "city nightlife" 10 --size 4k
```

### Batch Processing:
Create `themes.txt`:
```
sunset beach, 15
mountain landscape, 20
ocean waves, 10
```

Then run:
```bash
python image_fetcher.py --batch themes.txt
```

---

## Available Size Presets

| Preset | Resolution | Use Case |
|--------|-----------|----------|
| `4k` / `uhd` | 3840×2160 | 4K video, high-res displays |
| `fhd` | 1920×1080 | Full HD video, monitors |
| `hd` | 1280×720 | HD video, smaller screens |
| `mobile` | 1080×1920 | Mobile wallpapers, stories |
| `square` | 1080×1080 | Instagram posts |
| `youtube` | 1920×1080 | YouTube thumbnails |
| `tiktok` | 1080×1920 | TikTok, vertical video |

---

## Output Location

Images are saved to: `image_collections/<theme>_<timestamp>/`

Each collection includes:
- Downloaded images (numbered sequentially)
- `metadata.json` with details about each image

---

## Troubleshooting

### "No module named 'flask'"
```bash
pip install -r requirements.txt
```

### "No images found"
- Try different search terms
- Check your internet connection
- Configure API keys for better results

### Web interface won't start
- Make sure port 5000 is available
- Check that Flask is installed
- Try: `python test_suite.py`

### Progress bars not showing
- Install tqdm: `pip install tqdm`
- They appear automatically in CLI mode

---

## Need Help?

- 📖 **Full Documentation**: See [README.md](README.md)
- 🌐 **Web Interface Guide**: See [WEB_INTERFACE.md](WEB_INTERFACE.md)
- 🐛 **Report Issues**: [GitHub Issues](https://github.com/VerbalChainsaw/image-fetcher/issues)

---

## Pro Tips 💡

1. **Use the web interface** for the best experience
2. **Configure API keys** for higher quality images
3. **Use size presets** instead of typing dimensions
4. **Try batch mode** for multiple themes at once
5. **Check the history** to track your downloads
6. **Preview images** in the web interface before downloading

---

**Enjoy your professional image fetcher! 🎉**
