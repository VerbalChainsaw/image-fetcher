# Intelligent Image Curation

Build massive, high-quality image libraries automatically without manual intervention. The intelligent curation system features AI-powered theme generation, quality scoring, automatic categorization, and batch processing.

---

## 🎯 What Is Intelligent Curation?

The curation system allows you to:

✅ **Build Large Libraries Automatically** - Download thousands of images while you sleep
✅ **Quality-First Approach** - Only keep high-quality images
✅ **Smart Theme Generation** - AI generates relevant search themes for categories
✅ **Automatic Organization** - Images sorted by quality and category
✅ **Zero Intervention** - Set it and forget it
✅ **Duplicate Prevention** - Never download the same image twice

---

## 🚀 Quick Start

### Curate a Single Category

```bash
python curator.py nature
```

This will:
1. Generate 15 nature-related themes
2. Download 20 images per theme (300 total)
3. Score each image for quality
4. Organize into excellent/good/acceptable folders
5. Save detailed quality metrics

### Curate Multiple Categories

```bash
python curator.py nature urban abstract lifestyle
```

### Automated Batch Processing

```bash
# Linux/Mac
./curate_library.sh

# Customize categories by editing the script
nano curate_library.sh
```

---

## 📦 Available Categories

The system includes pre-configured theme templates for:

| Category | Themes | Example Themes |
|----------|--------|----------------|
| **nature** | 15 | mountain landscape sunrise, forest path misty morning, ocean waves sunset |
| **urban** | 15 | city skyline night lights, modern architecture, street photography |
| **people** | 15 | business professional, diverse team, family outdoor activity |
| **business** | 15 | startup team collaboration, corporate meeting, office workspace |
| **technology** | 15 | artificial intelligence, data center servers, cybersecurity |
| **lifestyle** | 15 | healthy breakfast, coffee morning, home interior design |
| **abstract** | 15 | geometric pattern colorful, texture background, gradient smooth |
| **seasonal** | 15 | spring flowers blooming, summer beach, autumn leaves falling |

View all themes:
```bash
python curator.py --list-categories
```

---

## 🎨 How It Works

### 1. Theme Generation

The curator uses pre-defined theme templates optimized for each category:

```python
# Example: nature category
themes = [
    'mountain landscape sunrise',
    'forest path misty morning',
    'ocean waves sunset',
    'desert sand dunes',
    'waterfall rainforest',
    ...
]
```

Each theme is crafted to return high-quality, diverse results from image providers.

### 2. Image Download

For each theme, the system:
- Downloads from your selected sources (Pexels, Pixabay, DuckDuckGo)
- Uses duplicate detection to skip already-downloaded images
- Applies retry logic for failed downloads
- Respects API rate limits

### 3. Quality Scoring

Every image is scored on 5 quality metrics:

#### **Resolution Score (25% weight)**
- Scores based on megapixels
- 8MP+ = 100 points
- 4MP = 80 points
- 2MP = 65 points
- 1MP = 50 points

#### **Sharpness Score (25% weight)**
- Edge detection algorithm
- Measures focus and detail
- Identifies blurry images

#### **Brightness Score (15% weight)**
- Analyzes exposure
- Prefers well-lit images
- Avoids over/underexposed photos

#### **Contrast Score (20% weight)**
- Measures tonal range
- Prefers images with good contrast
- Avoids flat, washed-out images

#### **Color Variety Score (15% weight)**
- Analyzes color distribution
- Prefers vibrant, varied colors
- Identifies monochromatic images

**Overall Score** = Weighted average (0-100)

### 4. Automatic Organization

Images are organized by quality tier:

```
curated_collections/
└── nature/
    └── 20250108_143022/
        ├── excellent/          # Score 85-100
        │   ├── mountain_landscape_92_001.jpg
        │   └── mountain_landscape_92_001.json  # Quality metrics
        ├── good/               # Score 70-84
        │   ├── forest_path_78_002.jpg
        │   └── forest_path_78_002.json
        ├── acceptable/         # Score 60-69
        │   ├── ocean_waves_65_003.jpg
        │   └── ocean_waves_65_003.json
        └── curation_report.json
```

Each image includes:
- **Filename**: `theme_score_number.jpg`
- **Quality scores**: Saved as `.json` file
- **Organization**: Sorted into quality folders

### 5. Curation Report

Each session generates a detailed report:

```json
{
  "category": "nature",
  "curation_config": {
    "min_quality_score": 70,
    "images_per_theme": 20,
    "organize_by_quality": true
  },
  "statistics": {
    "themes_processed": 15,
    "images_downloaded": 300,
    "images_rejected": 45,
    "duration_seconds": 425.3
  }
}
```

---

## ⚙️ Configuration

### Command-Line Options

```bash
python curator.py CATEGORIES [OPTIONS]

Options:
  --images-per-theme N    Images per theme (default: 20)
  --min-quality N         Minimum quality score 0-100 (default: 60)
  --output DIR            Output directory (default: curated_collections)
  --sources LIST          Sources: pexels pixabay duckduckgo (default: all)
  --list-categories       Show available categories
```

### Examples

**High-quality nature collection:**
```bash
python curator.py nature --min-quality 85 --images-per-theme 30
```

**Large mixed library:**
```bash
python curator.py nature urban abstract lifestyle \
    --images-per-theme 50 \
    --min-quality 70
```

**Pexels only (highest quality):**
```bash
python curator.py nature --sources pexels --min-quality 80
```

### Custom Configuration

For programmatic use:

```python
from curator import IntelligentCurator
from config import Config

config = Config()
curation_config = {
    'min_quality_score': 75,
    'images_per_theme': 30,
    'target_size': (3840, 2160),  # 4K
    'preferred_sources': ['pexels', 'pixabay'],
    'organize_by_quality': True,
    'auto_cleanup_low_quality': True,  # Delete low-quality images
}

curator = IntelligentCurator(config, curation_config)
curator.curate_category('nature', output_dir=Path('my_library'))
```

---

## 📊 Quality Scoring Details

### Understanding Scores

**Excellent (85-100)**
- Professional quality
- Sharp focus
- Good exposure
- Vibrant colors
- High resolution

**Good (70-84)**
- Above average quality
- Acceptable sharpness
- Decent exposure
- Good composition

**Acceptable (60-69)**
- Usable quality
- Minor issues (slight blur, exposure)
- Lower resolution
- Adequate for most uses

**Rejected (<60)**
- Low quality
- Blurry or out of focus
- Poor exposure
- Very low resolution

### Quality Metrics JSON

Each image's `.json` file contains:

```json
{
  "overall_score": 87.5,
  "resolution_score": 90.0,
  "sharpness_score": 85.0,
  "brightness_score": 88.0,
  "contrast_score": 92.0,
  "color_variety_score": 82.5,
  "notes": [
    "excellent_quality"
  ]
}
```

Use these metrics to:
- Filter images programmatically
- Analyze collection quality
- Train machine learning models
- Create custom organization schemes

---

## 🤖 Automated Batch Processing

### Using the Shell Script

The `curate_library.sh` script runs fully automated curation:

```bash
./curate_library.sh
```

**Default behavior:**
- Processes 5 categories: nature, urban, abstract, lifestyle, technology
- 25 images per theme
- Minimum quality: 70/100
- 10-second pause between categories

**Customize:**

Edit `curate_library.sh`:

```bash
# Configuration
MIN_QUALITY=85              # Raise for higher quality
IMAGES_PER_THEME=50         # More images per theme
OUTPUT_DIR="my_library"     # Custom output

# Categories to curate
CATEGORIES=(
    "nature"
    "urban"
    "people"
    "business"
    "technology"
    "lifestyle"
    "abstract"
    "seasonal"
)
```

### Scheduled Curation (Cron)

Run curation automatically on a schedule:

```bash
# Edit crontab
crontab -e

# Run every night at 2 AM
0 2 * * * cd /path/to/image-fetcher && ./curate_library.sh >> curation.log 2>&1

# Run weekly (Sunday at 3 AM)
0 3 * * 0 cd /path/to/image-fetcher && ./curate_library.sh >> curation.log 2>&1
```

---

## 💡 Use Cases

### 1. Stock Photo Alternative

Build your own royalty-free stock photo library:

```bash
# Comprehensive library
python curator.py nature urban people business lifestyle abstract \
    --images-per-theme 50 \
    --min-quality 80 \
    --sources pexels pixabay
```

Result: ~2,400 high-quality images organized by category and quality.

### 2. AI Training Dataset

Curate datasets for machine learning:

```bash
# High-quality, diverse dataset
python curator.py nature urban people technology \
    --images-per-theme 100 \
    --min-quality 70
```

Use quality scores to filter and balance your dataset.

### 3. Design Assets

Build a design resource library:

```bash
# Backgrounds and textures
python curator.py abstract nature \
    --images-per-theme 40 \
    --min-quality 85
```

### 4. Content Creation

Automatically populate content libraries:

```bash
# Social media content
python curator.py lifestyle people seasonal \
    --images-per-theme 30 \
    --min-quality 75
```

### 5. Video Production

Background footage library:

```bash
# 4K backgrounds
python curator.py nature urban --min-quality 90
```

Use excellent-tier images for high-end production.

---

## 📈 Performance & Scale

### Typical Performance

- **Themes per hour**: ~40-60 (depending on API limits)
- **Images per hour**: ~800-1,200
- **Quality filtering**: <1 second per image
- **Storage**: ~2-5MB per image (1920x1080)

### Large-Scale Curation

**Overnight curation (8 hours):**
```bash
# Configure for maximum output
python curator.py nature urban people business technology lifestyle abstract seasonal \
    --images-per-theme 75 \
    --min-quality 65
```

Expected results:
- 8 categories × 15 themes × 75 images = ~9,000 images
- After quality filtering (~30% rejection): ~6,300 images
- Total storage: ~12-30GB
- Total time: ~6-8 hours

### API Rate Limits

The system automatically handles rate limits:
- 2-second pause between themes
- 10-second pause between categories
- Exponential backoff on failures
- Duplicate detection prevents re-downloads

---

## 🔧 Advanced Features

### Custom Theme Templates

Add your own categories:

```python
# Edit curator.py
THEME_TEMPLATES['mycategory'] = [
    'custom theme 1',
    'custom theme 2',
    'custom theme 3',
    ...
]
```

### Quality-Based Filtering

Process collections programmatically:

```python
from curator import ImageQualityScorer
from pathlib import Path

scorer = ImageQualityScorer()

for img_path in Path('my_collection').glob('*.jpg'):
    scores = scorer.score_image(img_path)

    if scores['overall_score'] >= 85:
        # Use for premium content
        pass
    elif scores['sharpness_score'] < 40:
        # Reject blurry images
        img_path.unlink()
```

### Batch Re-scoring

Re-score existing collections:

```python
from curator import ImageQualityScorer
from pathlib import Path
import json

scorer = ImageQualityScorer()
collection_dir = Path('image_collections/nature_20250108')

for img_path in collection_dir.glob('*.jpg'):
    scores = scorer.score_image(img_path)

    # Save scores
    score_file = img_path.with_suffix('.json')
    with open(score_file, 'w') as f:
        json.dump(scores, f, indent=2)
```

---

## 🎬 Complete Workflow Example

### Goal: Build a 10,000-image library for video production

**Step 1: Configure**

```bash
# Edit curate_library.sh
MIN_QUALITY=80
IMAGES_PER_THEME=100
CATEGORIES=(nature urban lifestyle abstract technology)
```

**Step 2: Run overnight**

```bash
nohup ./curate_library.sh > curation.log 2>&1 &
```

**Step 3: Check progress**

```bash
tail -f curation.log
```

**Step 4: Review results**

```bash
# Count images by quality
find curated_collections/*/excellent -name "*.jpg" | wc -l
find curated_collections/*/good -name "*.jpg" | wc -l
find curated_collections/*/acceptable -name "*.jpg" | wc -l
```

**Step 5: Use in production**

```
curated_collections/
├── nature/excellent/     ← Premium backgrounds
├── urban/excellent/      ← City scenes
├── lifestyle/good/       ← B-roll footage
└── abstract/acceptable/  ← Transitions
```

---

## 🛠️ Troubleshooting

**Q: Curation is too slow**

A: Reduce images per theme or use fewer categories:
```bash
python curator.py nature --images-per-theme 10
```

**Q: Too many low-quality images**

A: Raise minimum quality score:
```bash
python curator.py nature --min-quality 80
```

**Q: Running out of disk space**

A: Enable auto-cleanup and raise quality threshold:
```python
curation_config = {
    'min_quality_score': 75,
    'auto_cleanup_low_quality': True,  # Deletes rejected images
}
```

**Q: Want more control over themes**

A: Edit `THEME_TEMPLATES` in `curator.py` or use interactive mode.

**Q: API rate limits**

A: The system handles this automatically, but you can:
- Use fewer sources: `--sources pexels`
- Increase delays in code
- Configure API keys for higher limits

---

## 📊 Quality Metrics Explained

### Resolution Score
- **What it measures**: Image size in megapixels
- **Why it matters**: Higher resolution = more detail and flexibility
- **Threshold**: 8MP+ for excellent, 2MP minimum

### Sharpness Score
- **What it measures**: Focus and edge definition
- **Why it matters**: Blurry images look unprofessional
- **Algorithm**: Laplacian edge detection variance

### Brightness Score
- **What it measures**: Overall exposure
- **Why it matters**: Well-exposed images are more usable
- **Target**: Middle gray (128/255)

### Contrast Score
- **What it measures**: Tonal range and depth
- **Why it matters**: Good contrast = visual interest
- **Algorithm**: Standard deviation of pixel values

### Color Variety Score
- **What it measures**: Color vibrancy and distribution
- **Why it matters**: Colorful images are more engaging
- **Algorithm**: RGB variance across channels

---

## 🚀 Future Enhancements

Planned features:
- **ML-based quality scoring** - Train on your preferences
- **Content detection** - Identify objects, people, scenery
- **Style classification** - Categorize by artistic style
- **Color palette extraction** - Organize by color scheme
- **Composition analysis** - Rule of thirds, symmetry detection
- **Facial recognition** - Filter/organize images with people
- **Web interface** - Visual curation dashboard
- **Cloud storage integration** - Auto-upload to S3, etc.

---

## 📚 See Also

- [README.md](README.md) - Main documentation
- [DUPLICATE_DETECTION.md](DUPLICATE_DETECTION.md) - Duplicate prevention
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [WEB_INTERFACE.md](WEB_INTERFACE.md) - Web interface
- [CHANGELOG.md](CHANGELOG.md) - Version history

---

**Start building your intelligent image library today! 🎨**
