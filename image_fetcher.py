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
from duckduckgo_search import DDGS

class ImageFetcher:
    def __init__(self, output_dir="image_collections", target_size=(1920, 1080)):
        """
        Initialize the Image Fetcher

        Args:
            output_dir: Base directory for saving images
            target_size: Target size for resized images (width, height)
        """
        self.output_dir = Path(output_dir)
        self.target_size = target_size

    def search_images(self, theme, max_images=10):
        """
        Search for images using DuckDuckGo

        Args:
            theme: Search query/theme
            max_images: Maximum number of images to fetch

        Returns:
            List of image URLs
        """
        print(f"🔍 Searching for '{theme}' images...")

        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(
                    keywords=theme,
                    max_results=max_images * 2  # Get more than needed as some might fail
                ))

            image_urls = [r['image'] for r in results[:max_images * 2]]
            print(f"✓ Found {len(image_urls)} potential images")
            return image_urls

        except Exception as e:
            print(f"✗ Error searching for images: {e}")
            return []

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

    def fetch_and_process(self, theme, num_images=10):
        """
        Main function to fetch, process, and save images

        Args:
            theme: Search theme
            num_images: Number of images to download
        """
        # Create output directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_theme = "".join(c for c in theme if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_theme = safe_theme.replace(' ', '_')

        theme_dir = self.output_dir / f"{safe_theme}_{timestamp}"
        theme_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n📁 Output directory: {theme_dir}\n")

        # Search for images
        image_urls = self.search_images(theme, num_images)

        if not image_urls:
            print("✗ No images found!")
            return

        # Download and process images
        saved_count = 0
        print(f"\n⬇️  Downloading and processing images...\n")

        for i, url in enumerate(image_urls):
            if saved_count >= num_images:
                break

            print(f"[{saved_count + 1}/{num_images}] Processing image {i + 1}...")

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


def main():
    parser = argparse.ArgumentParser(
        description='Fetch and resize images based on a theme',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python image_fetcher.py "sunset beach" 15
  python image_fetcher.py "mountain landscape" 20 --size 1280 720
  python image_fetcher.py "city skyline" 10 --output my_images
        """
    )

    parser.add_argument('theme', type=str, help='Search theme/query for images')
    parser.add_argument('count', type=int, help='Number of images to download')
    parser.add_argument('--size', type=int, nargs=2, metavar=('WIDTH', 'HEIGHT'),
                       default=[1920, 1080], help='Target image size (default: 1920 1080)')
    parser.add_argument('--output', type=str, default='image_collections',
                       help='Output base directory (default: image_collections)')

    args = parser.parse_args()

    # Validate inputs
    if args.count <= 0:
        print("✗ Error: Count must be greater than 0")
        sys.exit(1)

    if args.size[0] <= 0 or args.size[1] <= 0:
        print("✗ Error: Width and height must be greater than 0")
        sys.exit(1)

    # Run fetcher
    fetcher = ImageFetcher(output_dir=args.output, target_size=tuple(args.size))
    fetcher.fetch_and_process(args.theme, args.count)


if __name__ == "__main__":
    main()
