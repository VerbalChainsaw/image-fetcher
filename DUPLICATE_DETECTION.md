# Duplicate Detection

Image Fetcher v2.1 includes intelligent duplicate detection to prevent downloading the same images multiple times across sessions.

## How It Works

The duplicate detection system uses a SQLite database to track all downloaded images. It detects duplicates in two ways:

### 1. URL-Based Detection
- Every image URL is stored in the database
- Before downloading, the system checks if the URL has been seen before
- **Fast**: Prevents unnecessary downloads immediately

### 2. Content-Based Detection (Perceptual Hashing)
- After downloading, the actual image content is hashed
- Detects the same image from different URLs or sources
- **Smart**: Catches duplicates even when sources provide different URLs

## Benefits

✅ **Save Bandwidth** - Don't re-download images you already have
✅ **Save Time** - Skip processing duplicates
✅ **Save Storage** - Avoid storing the same image twice
✅ **Multi-Session** - Works across different download sessions
✅ **Multi-Source** - Detects duplicates from different providers

## Usage

### Command Line

Duplicate detection is **enabled by default**:

```bash
# Duplicates are automatically skipped
python image_fetcher.py "sunset beach" 10
```

To disable duplicate detection:

```bash
# Allow re-downloading images
python image_fetcher.py "sunset beach" 10 --no-duplicates
```

### Interactive Mode

You'll be prompted:

```
Skip duplicate images from previous downloads? [Y/n]:
```

Press Enter for Yes (default) or type 'n' for No.

### Web Interface

In the web interface, you'll see a checkbox:

```
☑ Skip Duplicate Images (Recommended - prevents re-downloading)
```

This is checked by default. Uncheck to allow duplicates.

## Database Location

The duplicate tracking database is stored at:

```
~/.image_fetcher.db  (Unix/Mac)
C:\Users\<username>\.image_fetcher.db  (Windows)
```

## Database Statistics

View your download history and statistics:

```bash
# Show database statistics
python image_fetcher.py --db-stats
```

This displays:
- Total images tracked
- Downloads by source (Pexels, Pixabay, DuckDuckGo)
- Top themes you've downloaded
- Duplicate counts and success rates

Example output:

```
============================================================
Image Database Statistics
============================================================
Total images tracked: 247

Recent downloads by source:
------------------------------------------------------------

PEXELS:
  Theme: sunset beach
    Downloaded: 15, Duplicates: 3, Failed: 2
  Theme: mountain landscape
    Downloaded: 20, Duplicates: 0, Failed: 1

PIXABAY:
  Theme: city skyline
    Downloaded: 12, Duplicates: 5, Failed: 0

DUCKDUCKGO:
  Theme: abstract art
    Downloaded: 8, Duplicates: 2, Failed: 3
============================================================
```

## Output and Reporting

When duplicate detection is enabled, you'll see:

**During Download:**
```
🔍 Duplicate detection: ENABLED (will skip already-downloaded images)

[1/10] Processing image 1 from pexels...
  ✓ Saved: sunset_beach_001.jpg
[2/10] Processing image 2 from pexels...
  ⏭️  Skipped: Duplicate URL (already downloaded)
[3/10] Processing image 3 from pixabay...
  ⏭️  Skipped: Duplicate image (same content from different source)
```

**Final Summary:**
```
============================================================
✅ Successfully saved 7 images
⏭️  Skipped 3 duplicates (already downloaded)
⚠️  Failed to process 0 images
📊 Success rate: 7/10 (70.0%)
⏱️  Total time: 12.3s
📁 Location: /path/to/image_collections/sunset_beach_20250108_143022
============================================================
```

## Metadata Tracking

Each download session records metadata including duplicates:

**metadata.json:**
```json
{
  "theme": "sunset beach",
  "timestamp": "20250108_143022",
  "target_count": 10,
  "actual_count": 7,
  "duplicate_count": 3,
  "failed_count": 0,
  "skip_duplicates": true,
  "duration_seconds": 12.3,
  "images": [...]
}
```

## Database Maintenance

### Clear Old Entries

To keep the database size manageable, you can clear old entries:

```python
from image_db import ImageDatabase

db = ImageDatabase()
deleted = db.clear_old_entries(days=30)  # Keep last 30 days
print(f"Cleared {deleted} old entries")
db.close()
```

### Backup Database

To backup your download history:

```bash
# Unix/Mac
cp ~/.image_fetcher.db ~/.image_fetcher.db.backup

# Windows
copy %USERPROFILE%\.image_fetcher.db %USERPROFILE%\.image_fetcher.db.backup
```

### Reset Database

To start fresh (this will re-download everything):

```bash
# Unix/Mac
rm ~/.image_fetcher.db

# Windows
del %USERPROFILE%\.image_fetcher.db
```

## Use Cases

### 1. Resuming Failed Downloads

If a download session fails partway through, just run it again:

```bash
# First attempt (fails after 5 images)
python image_fetcher.py "nature wallpapers" 20

# Resume - will skip the 5 already downloaded
python image_fetcher.py "nature wallpapers" 20
```

The duplicate detection ensures you don't re-download the same 5 images.

### 2. Building Large Collections Over Time

Download the same theme across multiple sessions:

```bash
# Day 1: Get 10 sunset images
python image_fetcher.py "sunset" 10

# Day 2: Get 10 more (different ones)
python image_fetcher.py "sunset" 10

# Day 3: Get 20 more (all new)
python image_fetcher.py "sunset" 20
```

Each session adds new, unique images to your collection.

### 3. Trying Different Sources

Focus on one source at a time when another is struggling:

```bash
# Try Pexels first
python image_fetcher.py "ocean waves" 15 --sources pexels

# Add more from Pixabay (won't duplicate Pexels images)
python image_fetcher.py "ocean waves" 15 --sources pixabay

# Fill in with DuckDuckGo if needed
python image_fetcher.py "ocean waves" 15 --sources duckduckgo
```

The duplicate detection works across all sources, so you get unique images from each.

### 4. Quality Filtering

Download from multiple sources, keeping only high-quality unique images:

```bash
# Get the best from all sources
python image_fetcher.py "professional photography" 50 --sources all --size 4k
```

The content-based hashing ensures that if Pexels and Pixabay provide the same image, you only get one copy of the highest quality version.

## Technical Details

### Hash Algorithm

- Uses SHA256 for perceptual image hashing
- Images are resized to 8x8 pixels before hashing for consistency
- Detects visually similar images even if slightly different

### Database Schema

**downloaded_images table:**
- `id`: Primary key
- `url`: Image source URL (unique)
- `image_hash`: SHA256 hash of image content
- `source`: Provider (pexels, pixabay, duckduckgo)
- `theme`: Search theme
- `filename`: Saved file path
- `download_date`: Timestamp
- `file_size`: File size in bytes
- `width`, `height`: Image dimensions

**download_stats table:**
- Aggregated statistics per theme and source
- Tracks requested, downloaded, duplicates, failed counts
- Session timestamps

### Performance

- URL checks are nearly instant (indexed database lookup)
- Hash calculation adds ~0.1 seconds per image
- Database size: ~1KB per 10 images tracked
- No impact on download speed or image quality

## Troubleshooting

**Q: Why are NEW images being marked as duplicates?**

A: This shouldn't happen. If it does:
1. Check if you truly haven't downloaded that image before (check metadata.json files)
2. The image might be very similar to a previously downloaded one
3. Try resetting the database (see "Reset Database" above)

**Q: Can I see what's in my database?**

A: Yes, use:
```bash
python image_fetcher.py --db-stats
```

Or access it directly:
```python
from image_db import print_database_stats
print_database_stats()
```

**Q: How much disk space does the database use?**

A: Very little. Expect ~100KB per 1000 images tracked.

**Q: Does this slow down downloads?**

A: Minimal impact:
- URL checking: <0.01 seconds
- Hash calculation: ~0.1 seconds per image
- Overall: Usually faster because duplicates are skipped immediately

**Q: Can I sync the database across machines?**

A: Not automatically, but you can:
1. Copy `~/.image_fetcher.db` to another machine
2. The database will work on any platform (Windows, Mac, Linux)

## API Usage

For programmatic access:

```python
from config import Config
from image_fetcher import ImageFetcher

config = Config()

# Enable duplicate detection (default)
fetcher = ImageFetcher(config, skip_duplicates=True)
fetcher.fetch_and_process("sunset", 10)

# Disable duplicate detection
fetcher = ImageFetcher(config, skip_duplicates=False)
fetcher.fetch_and_process("sunset", 10)  # May get duplicates
```

## Future Enhancements

Planned improvements:
- Web interface to browse database
- Export database to CSV
- Similarity threshold adjustment
- Selective database clearing (by theme, date, source)
- Database synchronization between machines
- Image deduplication tool for existing collections

## See Also

- [README.md](README.md) - Main documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [WEB_INTERFACE.md](WEB_INTERFACE.md) - Web interface guide
- [CHANGELOG.md](CHANGELOG.md) - Version history
