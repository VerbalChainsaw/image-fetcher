#!/usr/bin/env python3
"""
Image Fetcher - Download and resize images based on a theme
"""

import os
import sys
import argparse
import time
import json
import logging
from pathlib import Path
from datetime import datetime
import requests
from PIL import Image
from io import BytesIO
from config import Config
from image_sources import ImageSourceManager
from image_db import ImageDatabase

# Fix Windows encoding issues
try:
    from utils import setup_windows_encoding, safe_print
    setup_windows_encoding()
except ImportError:
    safe_print = print

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("Note: Install 'tqdm' for progress bars: pip install tqdm")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / '.image_fetcher.log'),
        logging.StreamHandler()
    ]
)

class ImageFetcher:
    def __init__(self, config, output_dir=None, target_size=(1920, 1080), skip_duplicates=True):
        """
        Initialize the Image Fetcher

        Args:
            config: Config object with API keys
            output_dir: Base directory for saving images
            target_size: Target size for resized images (width, height)
            skip_duplicates: Whether to skip previously downloaded images (default: True)
        """
        self.config = config
        self.output_dir = Path(output_dir or config.config.get('output_dir', 'image_collections'))
        self.target_size = target_size
        self.source_manager = ImageSourceManager(config)
        self.skip_duplicates = skip_duplicates
        self.db = ImageDatabase() if skip_duplicates else None

    def search_images(self, theme, max_images=10, sources='all', category=None):
        """
        Search for images using specified sources

        Args:
            theme: Search query/theme
            max_images: Maximum number of images to fetch
            sources: Which sources to use ('all', list, or single source)
            category: Optional category filter

        Returns:
            List of image dictionaries
        """
        return self.source_manager.search(theme, max_images, sources, category)

    def download_image(self, url, timeout=10, max_retries=3):
        """
        Download an image from URL with retry logic

        Args:
            url: Image URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts

        Returns:
            PIL Image object or None if failed
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=timeout, headers=headers)
                response.raise_for_status()

                img = Image.open(BytesIO(response.content))
                return img

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logging.warning(f"  Timeout on attempt {attempt + 1}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"  ✗ Failed after {max_retries} attempts: Timeout")
                    print(f"  ✗ Failed to download: Timeout after {max_retries} attempts")

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logging.warning(f"  Network error on attempt {attempt + 1}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"  ✗ Failed after {max_retries} attempts: {str(e)}")
                    print(f"  ✗ Failed to download: {str(e)[:80]}")

            except Exception as e:
                logging.error(f"  ✗ Unexpected error: {str(e)}")
                print(f"  ✗ Failed to download: {str(e)[:80]}")
                break

        return None

    def resize_and_crop(self, img):
        """
        Resize and crop image to target size while maintaining aspect ratio

        Args:
            img: PIL Image object

        Returns:
            Resized and cropped PIL Image
        """
        # Convert to RGB if needed (handles RGBA, P, etc.)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Calculate aspect ratios
        target_ratio = self.target_size[0] / self.target_size[1]
        img_ratio = img.width / img.height

        # Resize to fill target size (crop will happen if needed)
        if img_ratio > target_ratio:
            # Image is wider than target - fit to height
            new_height = self.target_size[1]
            new_width = int(new_height * img_ratio)
        else:
            # Image is taller than target - fit to width
            new_width = self.target_size[0]
            new_height = int(new_width / img_ratio)

        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Center crop to exact target size
        left = (new_width - self.target_size[0]) // 2
        top = (new_height - self.target_size[1]) // 2
        right = left + self.target_size[0]
        bottom = top + self.target_size[1]

        img = img.crop((left, top, right, bottom))

        return img

    def fetch_and_process(self, theme, num_images=10, sources='all', category=None):
        """
        Main function to fetch, process, and save images

        Args:
            theme: Search theme
            num_images: Number of images to download
            sources: Which sources to use
            category: Optional category filter
        """
        start_time = time.time()

        # Create output directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_theme = "".join(c for c in theme if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_theme = safe_theme.replace(' ', '_')

        theme_dir = self.output_dir / f"{safe_theme}_{timestamp}"
        theme_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n📁 Output directory: {theme_dir}\n")
        logging.info(f"Starting fetch: theme='{theme}', num_images={num_images}, sources={sources}")

        # Search for images
        images = self.search_images(theme, num_images, sources, category)

        if not images:
            print("✗ No images found!")
            logging.warning("No images found for query")
            return

        # Download and process images
        saved_count = 0
        failed_count = 0
        duplicate_count = 0
        metadata = {
            'theme': theme,
            'timestamp': timestamp,
            'target_count': num_images,
            'sources': sources,
            'category': category,
            'target_size': self.target_size,
            'skip_duplicates': self.skip_duplicates,
            'images': []
        }

        safe_print(f"\n⬇️  Downloading and processing images...\n")
        if self.skip_duplicates:
            safe_print(f"🔍 Duplicate detection: ENABLED (will skip already-downloaded images)\n")

        # Use tqdm if available, otherwise regular loop
        image_iterator = tqdm(images, desc="Processing", unit="img", total=num_images) if HAS_TQDM else images

        for i, img_data in enumerate(image_iterator):
            if saved_count >= num_images:
                break

            url = img_data['url']
            source = img_data.get('source', 'unknown')
            photographer = img_data.get('photographer', 'Unknown')

            if not HAS_TQDM:
                print(f"[{saved_count + 1}/{num_images}] Processing image {i + 1} from {source}...")

            # Check for duplicate URL
            if self.skip_duplicates and self.db.is_duplicate_url(url):
                if not HAS_TQDM:
                    print(f"  ⏭️  Skipped: Duplicate URL (already downloaded)")
                logging.info(f"Skipped duplicate URL: {url}")
                duplicate_count += 1
                continue

            # Download image
            img = self.download_image(url)
            if img is None:
                failed_count += 1
                continue

            try:
                # Validate image quality
                if img.width < 800 or img.height < 600:
                    if not HAS_TQDM:
                        print(f"  ⚠ Skipped: Image too small ({img.width}x{img.height})")
                    logging.warning(f"Skipped low-resolution image: {img.width}x{img.height}")
                    failed_count += 1
                    continue

                # Check for duplicate image (same content, different URL)
                if self.skip_duplicates:
                    img_hash = self.db.calculate_image_hash(img)
                    if img_hash and self.db.is_duplicate_hash(img_hash):
                        if not HAS_TQDM:
                            print(f"  ⏭️  Skipped: Duplicate image (same content from different source)")
                        logging.info(f"Skipped duplicate image hash: {img_hash[:16]}...")
                        duplicate_count += 1
                        continue

                # Resize and crop
                img_resized = self.resize_and_crop(img)

                # Save image
                filename = f"{safe_theme}_{saved_count + 1:03d}.jpg"
                filepath = theme_dir / filename
                img_resized.save(filepath, 'JPEG', quality=95)

                # Get file size
                file_size = filepath.stat().st_size

                # Add to database
                if self.skip_duplicates:
                    self.db.add_image(
                        url=url,
                        image_hash=img_hash,
                        source=source,
                        theme=theme,
                        filename=str(filepath),
                        file_size=file_size,
                        width=self.target_size[0],
                        height=self.target_size[1]
                    )

                # Store metadata
                metadata['images'].append({
                    'filename': filename,
                    'source': source,
                    'photographer': photographer,
                    'original_url': url,
                    'title': img_data.get('title', 'Untitled'),
                    'download_time': datetime.now().isoformat()
                })

                if not HAS_TQDM:
                    safe_print(f"  ✓ Saved: {filename}")

                saved_count += 1

            except Exception as e:
                logging.error(f"Error processing image: {e}")
                if not HAS_TQDM:
                    print(f"  ✗ Error processing image: {e}")
                failed_count += 1
                continue

        # Save metadata
        metadata['actual_count'] = saved_count
        metadata['failed_count'] = failed_count
        metadata['duplicate_count'] = duplicate_count
        metadata['duration_seconds'] = round(time.time() - start_time, 2)

        metadata_file = theme_dir / 'metadata.json'
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logging.info(f"Saved metadata to {metadata_file}")
        except Exception as e:
            logging.error(f"Failed to save metadata: {e}")

        # Record session stats in database
        if self.skip_duplicates:
            source_str = sources if isinstance(sources, str) else ','.join(sources)
            self.db.record_session_stats(
                theme=theme,
                source=source_str,
                requested=num_images,
                downloaded=saved_count,
                duplicates=duplicate_count,
                failed=failed_count
            )

        # Summary
        print(f"\n{'='*60}")
        print(f"✅ Successfully saved {saved_count} images")
        if duplicate_count > 0:
            safe_print(f"⏭️  Skipped {duplicate_count} duplicates (already downloaded)")
        if failed_count > 0:
            safe_print(f"⚠️  Failed to process {failed_count} images")
        total_processed = saved_count + failed_count + duplicate_count
        if total_processed > 0:
            safe_print(f"📊 Success rate: {saved_count}/{total_processed} ({100*saved_count/total_processed:.1f}%)")
        safe_print(f"⏱️  Total time: {metadata['duration_seconds']}s")
        print(f"📁 Location: {theme_dir.absolute()}")
        print(f"{'='*60}\n")

        logging.info(f"Completed: {saved_count} saved, {duplicate_count} duplicates, {failed_count} failed, {metadata['duration_seconds']}s")

        return theme_dir


def interactive_mode():
    """Run in interactive mode with prompts"""
    config = Config()

    print("\n" + "="*60)
    print("Image Fetcher - Interactive Mode")
    print("="*60 + "\n")

    # Check if API keys are configured
    available_sources = []
    if config.get_api_key('pexels'):
        available_sources.append('pexels')
    if config.get_api_key('pixabay'):
        available_sources.append('pixabay')
    available_sources.append('duckduckgo')

    print(f"Available sources: {', '.join(available_sources)}")

    if len(available_sources) == 1:
        safe_print("\n💡 Tip: Run with --setup to configure Pexels and Pixabay API keys")
        print("   for better quality and more image sources!\n")

    # Get search theme
    theme = input("Search theme: ").strip()
    if not theme:
        print("✗ Theme required!")
        return

    # Get number of images
    while True:
        try:
            count_str = input("Number of images (default 10): ").strip()
            count = int(count_str) if count_str else 10
            if count > 0:
                break
            print("✗ Must be greater than 0")
        except ValueError:
            print("✗ Please enter a number")

    # Get image sources
    print(f"\nImage sources ({', '.join(available_sources)}):")
    sources_input = input("Use (all/pexels/pixabay/duckduckgo, default all): ").strip().lower()
    sources = sources_input if sources_input else 'all'

    # Get category
    print("\nCategory (optional):")
    print("  Pixabay: nature, backgrounds, science, education, people, etc.")
    print("  Pexels: landscape, portrait, square")
    category = input("Category (press Enter to skip): ").strip() or None

    # Get size
    size_input = input("\nImage size WIDTHxHEIGHT (default 1920x1080): ").strip()
    if size_input:
        try:
            w, h = size_input.lower().split('x')
            size = (int(w), int(h))
        except:
            print("✗ Invalid size format, using default")
            size = (1920, 1080)
    else:
        size = (1920, 1080)

    # Ask about duplicate detection
    skip_dup_input = input("\nSkip duplicate images from previous downloads? [Y/n]: ").strip().lower()
    skip_duplicates = skip_dup_input != 'n'

    print("\n" + "="*60 + "\n")

    # Run fetcher
    fetcher = ImageFetcher(config, target_size=size, skip_duplicates=skip_duplicates)
    fetcher.fetch_and_process(theme, count, sources, category)


def batch_mode(batch_file):
    """Process multiple themes from a file"""
    config = Config()

    if not os.path.exists(batch_file):
        print(f"✗ Batch file not found: {batch_file}")
        sys.exit(1)

    print("\n" + "="*60)
    print(f"Batch Mode - Processing: {batch_file}")
    print("="*60 + "\n")

    with open(batch_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    fetcher = ImageFetcher(config)

    for i, line in enumerate(lines, 1):
        try:
            parts = line.split(',')
            theme = parts[0].strip()

            if not theme:
                print(f"✗ Skipping line {i}: Empty theme")
                continue

            # Parse count with validation
            try:
                count = int(parts[1].strip()) if len(parts) > 1 else 10
                if count <= 0:
                    print(f"✗ Skipping line {i}: Invalid count (must be > 0)")
                    continue
            except (ValueError, IndexError):
                count = 10  # Default if invalid

            print(f"\n[{i}/{len(lines)}] Processing: {theme} ({count} images)")
            print("-" * 60)

            fetcher.fetch_and_process(theme, count)

        except Exception as e:
            print(f"✗ Error processing line {i} ('{line}'): {str(e)}")
            print("  Continuing with next line...")
            continue


def main():
    parser = argparse.ArgumentParser(
        description='Fetch and resize images based on a theme',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python image_fetcher.py "sunset beach" 15
  python image_fetcher.py "mountain landscape" 20 --size 1920x1080
  python image_fetcher.py "riot" 10 --sources pexels pixabay --category nature
  python image_fetcher.py --interactive
  python image_fetcher.py --batch themes.txt
  python image_fetcher.py --setup
        """
    )

    parser.add_argument('theme', type=str, nargs='?', help='Search theme/query for images')
    parser.add_argument('count', type=int, nargs='?', help='Number of images to download')
    parser.add_argument('--size', type=str, metavar='WIDTHxHEIGHT',
                       default='1920x1080', help='Target image size (default: 1920x1080)')
    parser.add_argument('--output', type=str, default='image_collections',
                       help='Output base directory (default: image_collections)')
    parser.add_argument('--sources', type=str, nargs='+',
                       help='Image sources: pexels pixabay duckduckgo (default: all)')
    parser.add_argument('--category', type=str,
                       help='Category filter (varies by source)')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('--batch', '-b', type=str, metavar='FILE',
                       help='Batch process themes from file')
    parser.add_argument('--setup', action='store_true',
                       help='Run API key setup wizard')
    parser.add_argument('--no-duplicates', action='store_true',
                       help='Disable duplicate detection (allows re-downloading same images)')
    parser.add_argument('--db-stats', action='store_true',
                       help='Show database statistics and exit')

    args = parser.parse_args()

    # Database stats mode
    if args.db_stats:
        from image_db import print_database_stats
        print_database_stats()
        return

    # Setup mode
    if args.setup:
        config = Config()
        config.setup_wizard()
        return

    # Interactive mode
    if args.interactive:
        interactive_mode()
        return

    # Batch mode
    if args.batch:
        batch_mode(args.batch)
        return

    # Regular mode - require theme and count
    if not args.theme or not args.count:
        parser.print_help()
        sys.exit(1)

    # Parse size (support both presets and WIDTHxHEIGHT format)
    size = None
    try:
        # Try preset first
        from config import SIZE_PRESETS
        if args.size.lower() in SIZE_PRESETS:
            size = SIZE_PRESETS[args.size.lower()]
            print(f"Using size preset '{args.size}': {size[0]}x{size[1]}")
        else:
            # Try WIDTHxHEIGHT format
            w, h = args.size.lower().split('x')
            size = (int(w), int(h))
    except:
        print(f"✗ Error: Invalid size '{args.size}'")
        print("   Use a preset (4k, fhd, hd, mobile) or WIDTHxHEIGHT (e.g., 1920x1080)")
        print(f"   Available presets: {', '.join(SIZE_PRESETS.keys())}")
        sys.exit(1)

    # Validate inputs
    if args.count <= 0:
        print("✗ Error: Count must be greater than 0")
        sys.exit(1)

    if size[0] <= 0 or size[1] <= 0:
        print("✗ Error: Width and height must be greater than 0")
        sys.exit(1)

    # Prepare sources
    sources = args.sources if args.sources else 'all'

    # Determine skip_duplicates setting (skip by default, unless --no-duplicates flag is set)
    skip_duplicates = not args.no_duplicates

    # Run fetcher
    config = Config()
    fetcher = ImageFetcher(config, output_dir=args.output, target_size=size, skip_duplicates=skip_duplicates)
    fetcher.fetch_and_process(args.theme, args.count, sources, args.category)


if __name__ == "__main__":
    main()
