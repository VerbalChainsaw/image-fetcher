#!/usr/bin/env python3
"""
Image Fetcher - Download and resize images based on a theme
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import requests
from PIL import Image
from io import BytesIO
from config import Config
from image_sources import ImageSourceManager

class ImageFetcher:
    def __init__(self, config, output_dir=None, target_size=(1920, 1080)):
        """
        Initialize the Image Fetcher

        Args:
            config: Config object with API keys
            output_dir: Base directory for saving images
            target_size: Target size for resized images (width, height)
        """
        self.config = config
        self.output_dir = Path(output_dir or config.config.get('output_dir', 'image_collections'))
        self.target_size = target_size
        self.source_manager = ImageSourceManager(config)

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

    def download_image(self, url, timeout=10):
        """
        Download an image from URL

        Args:
            url: Image URL
            timeout: Request timeout in seconds

        Returns:
            PIL Image object or None if failed
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()

            img = Image.open(BytesIO(response.content))
            return img

        except Exception as e:
            print(f"  ✗ Failed to download: {str(e)[:50]}")
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
        # Create output directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_theme = "".join(c for c in theme if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_theme = safe_theme.replace(' ', '_')

        theme_dir = self.output_dir / f"{safe_theme}_{timestamp}"
        theme_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n📁 Output directory: {theme_dir}\n")

        # Search for images
        images = self.search_images(theme, num_images, sources, category)

        if not images:
            print("✗ No images found!")
            return

        # Download and process images
        saved_count = 0
        print(f"\n⬇️  Downloading and processing images...\n")

        for i, img_data in enumerate(images):
            if saved_count >= num_images:
                break

            url = img_data['url']
            source = img_data.get('source', 'unknown')

            print(f"[{saved_count + 1}/{num_images}] Processing image {i + 1} from {source}...")

            # Download image
            img = self.download_image(url)
            if img is None:
                continue

            try:
                # Resize and crop
                img = self.resize_and_crop(img)

                # Save image
                filename = f"{safe_theme}_{saved_count + 1:03d}.jpg"
                filepath = theme_dir / filename
                img.save(filepath, 'JPEG', quality=95)

                print(f"  ✓ Saved: {filename}")
                saved_count += 1

            except Exception as e:
                print(f"  ✗ Error processing image: {e}")
                continue

        print(f"\n{'='*60}")
        print(f"✅ Successfully saved {saved_count} images to:")
        print(f"   {theme_dir.absolute()}")
        print(f"{'='*60}\n")

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
        print("\n💡 Tip: Run with --setup to configure Pexels and Pixabay API keys")
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

    print("\n" + "="*60 + "\n")

    # Run fetcher
    fetcher = ImageFetcher(config, target_size=size)
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
        parts = line.split(',')
        theme = parts[0].strip()
        count = int(parts[1].strip()) if len(parts) > 1 else 10

        print(f"\n[{i}/{len(lines)}] Processing: {theme} ({count} images)")
        print("-" * 60)

        fetcher.fetch_and_process(theme, count)


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

    args = parser.parse_args()

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

    # Parse size
    try:
        w, h = args.size.lower().split('x')
        size = (int(w), int(h))
    except:
        print("✗ Error: Invalid size format. Use WIDTHxHEIGHT (e.g., 1920x1080)")
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

    # Run fetcher
    config = Config()
    fetcher = ImageFetcher(config, output_dir=args.output, target_size=size)
    fetcher.fetch_and_process(args.theme, args.count, sources, args.category)


if __name__ == "__main__":
    main()
