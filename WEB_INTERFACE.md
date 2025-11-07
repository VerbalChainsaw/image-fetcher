# 🌐 Web Interface Guide

## Overview

The Image Fetcher Web Interface is a **professional, modern web application** that makes image fetching easy and beautiful. No command-line knowledge required!

---

## 🚀 Quick Start

1. **Start the server:**
   ```bash
   python web_app.py
   ```

2. **Open your browser:**
   Navigate to `http://127.0.0.1:5000`

3. **Start fetching images!**
   - Enter a search theme
   - Select size preset (4K, FHD, HD, etc.)
   - Click "Fetch Images"
   - Watch real-time progress
   - Preview your images instantly!

---

## ✨ Features

### 1. **Beautiful Modern UI**
- Professional gradient design
- Smooth animations and transitions
- Clean, intuitive interface
- Responsive layout for all devices

### 2. **Fetch Images Tab** 📥

The main interface for downloading images:

- **Search Theme**: Enter what you're looking for
  - Examples: "sunset beach", "mountain landscape", "city skyline"
  - Be specific for better results

- **Image Sources**: Choose your preferred source
  - All Available Sources (recommended)
  - Pexels (High Quality)
  - Pixabay (Large Variety)
  - DuckDuckGo (No API Key)

- **Number of Images**: 1-100 images per download

- **Category Filter** (Optional):
  - Pixabay: nature, backgrounds, science, people, animals, etc.
  - Pexels: landscape, portrait, square

- **Size Presets**: Quick buttons for common sizes
  - 4K UHD (3840×2160)
  - Full HD (1920×1080)
  - HD (1280×720)
  - Mobile (1080×1920)
  - Square (1080×1080)
  - YouTube (1920×1080)

- **Custom Size**: Set exact width and height in pixels

### 3. **Real-Time Progress Tracking** 📊

Watch your download progress live:

- **Progress Bar**: Visual representation of completion
- **Percentage**: Exact progress percentage
- **Status Message**: Current operation (Searching, Downloading, etc.)
- **Statistics**:
  - Completed count
  - Failed count
  - Success rate

### 4. **Image Gallery Preview** 🖼️

After download completes:

- **Thumbnail Grid**: See all your images at a glance
- **Hover Effects**: Smooth zoom and overlay
- **Image Details**: View photographer, source, and title
- **Click to Enlarge**: Full-screen modal view
- **Download All**: Export your entire collection

### 5. **Download History** 📚

Track all your past downloads:

- **Theme**: What you searched for
- **Timestamp**: When it was downloaded
- **Image Count**: How many images
- **Sources**: Which sources were used
- **Size**: Resolution of images
- **Success Rate**: How many succeeded
- **Refresh Button**: Update the list

### 6. **Settings Panel** ⚙️

Configure your application:

- **API Keys**:
  - Add Pexels API key
  - Add Pixabay API key
  - Keys are validated and saved
  - Links to get free API keys

- **About Section**:
  - Version information
  - Feature list
  - GitHub repository link

---

## 🎨 Design Highlights

### Color Scheme
- **Primary**: Purple gradient (#667eea → #764ba2)
- **Success**: Green (#4caf50)
- **Warning**: Orange (#ff9800)
- **Error**: Red (#f44336)
- **Info**: Blue (#2196f3)

### Animations
- Tab switching fade-in
- Button hover effects
- Progress bar transitions
- Gallery item zoom
- Modal fade-in/out

### Typography
- Modern sans-serif fonts
- Clear hierarchy
- Readable sizes
- Proper contrast

---

## 📱 Responsive Design

The interface adapts to all screen sizes:

- **Desktop** (1200px+): Full layout with side-by-side controls
- **Tablet** (768px-1200px): Adjusted grid layout
- **Mobile** (<768px): Stacked layout, touch-friendly

---

## 🔌 API Endpoints

The web interface uses these backend endpoints:

### `POST /api/fetch`
Start a new image fetch job
```json
{
  "theme": "sunset beach",
  "count": 10,
  "sources": "all",
  "category": "nature",
  "width": 1920,
  "height": 1080
}
```

### `GET /api/status/:job_id`
Get status of a running job
```json
{
  "status": "running",
  "progress": "Downloading image 5/10...",
  "percent": 50,
  "stats": {
    "completed": 5,
    "failed": 1,
    "rate": "83%"
  }
}
```

### `GET /api/results/:job_id`
Get results of a completed job
```json
{
  "images": [
    {
      "path": "/images/sunset_beach_20251107/image_001.jpg",
      "title": "Beautiful Sunset",
      "photographer": "John Doe",
      "source": "pexels"
    }
  ],
  "metadata": {...}
}
```

### `GET /api/history`
Get download history
```json
{
  "history": [
    {
      "theme": "sunset beach",
      "timestamp": "20251107_143022",
      "count": 10,
      "sources": "all",
      "size": "1920x1080",
      "success_rate": "10/12"
    }
  ]
}
```

### `POST /api/setup`
Save API keys
```json
{
  "pexels_key": "your-key-here",
  "pixabay_key": "your-key-here"
}
```

---

## 💡 Tips for Best Experience

1. **Configure API Keys First**
   - Go to Settings tab
   - Add your Pexels and Pixabay keys
   - Get much better quality images

2. **Use Size Presets**
   - Click preset buttons for quick sizing
   - Custom sizes also supported

3. **Monitor Progress**
   - Watch real-time statistics
   - See exactly what's happening

4. **Browse History**
   - Check past downloads
   - Track your collections

5. **Preview Before Download**
   - Use the gallery to see results
   - Click images to enlarge

---

## 🐛 Troubleshooting

### Server Won't Start

```bash
# Make sure dependencies are installed
pip install -r requirements.txt

# Check if port 5000 is available
lsof -i :5000  # On Linux/Mac
netstat -ano | findstr :5000  # On Windows
```

### API Keys Not Saving

- Check file permissions on `~/.image_fetcher_config.json`
- Make sure you're not entering the placeholder (••••)
- Refresh the page after saving

### Images Not Loading

- Check that `image_collections/` directory exists
- Verify images were actually downloaded
- Check browser console for errors

### Progress Not Updating

- Ensure JavaScript is enabled
- Check browser console for errors
- Try refreshing the page

---

## 🎯 Keyboard Shortcuts

- **Tab**: Navigate between form fields
- **Enter**: Submit form (when in form)
- **Esc**: Close modal (when viewing image)
- **Click outside modal**: Close modal

---

## 🔒 Security Notes

- **Local Only**: Default configuration runs on localhost (127.0.0.1)
- **No Auth**: No authentication by default (for local use)
- **API Keys**: Stored securely in config file
- **HTTPS**: Not configured by default (local development)

### Running on Network

To allow access from other devices on your network:

```python
# In web_app.py, change:
run_web_app(host='0.0.0.0', port=5000)
```

⚠️ **Warning**: Only do this on trusted networks!

---

## 🚀 Advanced Usage

### Custom Port

```python
# Edit web_app.py
run_web_app(host='127.0.0.1', port=8080, debug=False)
```

### Production Deployment

For production, use a proper WSGI server:

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

### Adding Authentication

Consider adding Flask-Login or similar for multi-user scenarios.

---

## 📊 Browser Compatibility

Tested and working on:

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Opera 76+

Requires:
- JavaScript enabled
- Modern CSS support (CSS Grid, Flexbox)
- Fetch API support

---

## 🎨 Customization

### Changing Colors

Edit the CSS variables in `templates/index.html`:

```css
:root {
    --primary: #667eea;  /* Main color */
    --secondary: #764ba2;  /* Accent color */
    --success: #4caf50;  /* Success messages */
    /* ... etc */
}
```

### Adding Features

The codebase is modular and easy to extend:

1. **Frontend**: Edit `templates/index.html`
2. **Backend**: Edit `web_app.py`
3. **Core Logic**: Edit `image_fetcher.py`

---

## 📝 Future Enhancements

Planned features for future versions:

- [ ] User accounts and authentication
- [ ] Saved search presets
- [ ] Bulk download of multiple themes
- [ ] Export to ZIP
- [ ] Share collections via link
- [ ] Image editing (crop, filter)
- [ ] Favorites/bookmark images
- [ ] Search within downloaded images
- [ ] Dark mode toggle
- [ ] Multi-language support

---

## 🤝 Contributing

Want to improve the web interface?

1. Fork the repository
2. Make your changes
3. Test thoroughly
4. Submit a pull request

Areas we'd love help with:
- UI/UX improvements
- New features
- Bug fixes
- Documentation
- Translations

---

## 📄 License

Same as the main project - open source and free to use!

---

## 💬 Support

Having issues? Found a bug? Have a suggestion?

- 🐛 **Report bugs**: [GitHub Issues](https://github.com/VerbalChainsaw/image-fetcher/issues)
- 💡 **Suggest features**: [GitHub Discussions](https://github.com/VerbalChainsaw/image-fetcher/discussions)
- 📧 **Contact**: See repository for contact information

---

## 🎉 Credits

Built with:
- **Python** - Backend logic
- **Flask** - Web framework
- **HTML/CSS/JavaScript** - Frontend
- **Modern Web Standards** - Responsive design

---

**Enjoy your beautiful new web interface!** 🎨✨
