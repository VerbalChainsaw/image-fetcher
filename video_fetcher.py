#!/usr/bin/env python3
"""
Video Fetcher - Advanced video scraping and downloading tool
Supports multiple sources, parallel downloads, and comprehensive filtering
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from tqdm import tqdm

from video_config import VideoConfig
from video_sources import VideoSourceManager


class VideoFetcher:
    """
    Advanced video fetcher with multiple sources, parallel downloads,
    and comprehensive filtering capabilities.
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize the video fetcher with configuration."""
        self.config = config or VideoConfig.load_config()

        # Initialize video source manager
        pexels_key = self.config.get("pexels_api_key")
        pixabay_key = self.config.get("pixabay_api_key")

        self.source_manager = VideoSourceManager(
            pexels_key=pexels_key,
            pixabay_key=pixabay_key
        )

        self.output_dir = self.config.get("output_dir", "video_collections")

    def search_videos(
        self,
        theme: str,
        max_videos: int = 10,
        sources: str = "all",
        **filters
    ) -> List[Dict]:
        """
        Search for videos across specified sources with filters.

        Args:
            theme: Search query/theme
            max_videos: Maximum number of videos to find
            sources: Comma-separated source names or "all"
            **filters: Additional search filters (orientation, category, etc.)

        Returns:
            List of video metadata dictionaries
        """
        print(f"\nSearching for '{theme}' videos...")
        print(f"Sources: {sources}")
        print(f"Requested: {max_videos} videos")

        # Apply quality filters from config
        quality = self.config.get("default_quality", "hd")
        quality_params = VideoConfig.get_quality_params(quality)
        filters.update(quality_params)

        # Apply duration filters if configured
        if self.config.get("min_duration"):
            filters["min_duration"] = self.config["min_duration"]
        if self.config.get("max_duration"):
            filters["max_duration"] = self.config["max_duration"]

        # Search across sources
        videos = self.source_manager.search(
            query=theme,
            max_results=max_videos * 2,  # Get extras for filtering
            sources=sources,
            **filters
        )

        print(f"Found {len(videos)} videos from sources")

        # Apply additional filters
        videos = self._apply_filters(videos, filters)

        print(f"After filtering: {len(videos)} videos")

        return videos[:max_videos]

    def _apply_filters(self, videos: List[Dict], filters: Dict) -> List[Dict]:
        """Apply advanced filters to video results."""
        filtered = []

        for video in videos:
            # Check minimum dimensions
            min_width = filters.get("min_width", self.config.get("min_width", 0))
            min_height = filters.get("min_height", self.config.get("min_height", 0))

            if video.get("width", 0) < min_width or video.get("height", 0) < min_height:
                continue

            # Check duration constraints
            duration = video.get("duration", 0)
            min_dur = filters.get("min_duration")
            max_dur = filters.get("max_duration")

            if min_dur and duration < min_dur:
                continue
            if max_dur and duration > max_dur:
                continue

            filtered.append(video)

        return filtered

    def download_video(
        self,
        url: str,
        output_path: Path,
        progress_callback: Optional[Callable] = None
    ) -> bool:
        """
        Download a video from URL to output path with progress tracking.

        Args:
            url: Video download URL
            output_path: Where to save the video
            progress_callback: Optional callback(downloaded_bytes, total_bytes)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check max file size before downloading
            max_size = self.config.get("max_file_size_mb", 100) * 1024 * 1024

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            # Stream download to handle large files
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            # Check file size
            if total_size > max_size:
                print(f"  Skipping {output_path.name}: exceeds max size ({total_size / 1024 / 1024:.1f}MB)")
                return False

            # Download with progress tracking
            downloaded = 0
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total_size)

            return True

        except requests.exceptions.RequestException as e:
            print(f"  Error downloading {output_path.name}: {str(e)[:100]}")
            # Clean up partial download
            if output_path.exists():
                output_path.unlink()
            return False
        except Exception as e:
            print(f"  Unexpected error: {str(e)[:100]}")
            if output_path.exists():
                output_path.unlink()
            return False

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as a filename."""
        # Remove or replace invalid characters
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        # Replace spaces and multiple underscores
        name = re.sub(r'\s+', '_', name)
        name = re.sub(r'_+', '_', name)
        return name.strip('_')

    def fetch_and_process(
        self,
        theme: str,
        num_videos: int = 10,
        sources: str = "all",
        quality: str = "hd",
        progress_callback: Optional[Callable] = None,
        **filters
    ) -> str:
        """
        Fetch and download videos with advanced processing.

        Args:
            theme: Search theme/query
            num_videos: Number of videos to download
            sources: Source selection
            quality: Video quality preference
            progress_callback: Optional callback for progress updates
            **filters: Additional filters

        Returns:
            Path to output directory
        """
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_theme = self._sanitize_filename(theme)
        output_path = Path(self.output_dir) / f"{safe_theme}_{timestamp}"
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\nOutput directory: {output_path}")

        # Update quality in filters
        filters.update(VideoConfig.get_quality_params(quality))

        # Search for videos
        videos = self.search_videos(theme, num_videos, sources, **filters)

        if not videos:
            print("No videos found matching criteria.")
            return str(output_path)

        print(f"\nDownloading {len(videos)} videos...")

        # Parallel download setup
        parallel = self.config.get("parallel_downloads", 3)
        successful = 0
        failed = 0

        # Create metadata file
        metadata_path = output_path / "metadata.txt"
        with open(metadata_path, 'w') as meta:
            meta.write(f"Theme: {theme}\n")
            meta.write(f"Downloaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            meta.write(f"Sources: {sources}\n")
            meta.write(f"Quality: {quality}\n\n")

        def download_task(idx: int, video: Dict) -> tuple:
            """Download a single video."""
            # Prefer medium quality for faster downloads if available
            url = video.get("url_medium", video.get("url"))

            if not url:
                return idx, False, "No URL"

            # Generate filename
            ext = "mp4"  # Most video sources provide MP4
            filename = f"{safe_theme}_{idx+1:03d}.{ext}"
            file_path = output_path / filename

            # Progress bar for this download
            pbar = tqdm(
                total=0,
                unit='B',
                unit_scale=True,
                desc=f"  {filename}",
                leave=False
            )

            def update_progress(downloaded, total):
                if pbar.total != total:
                    pbar.total = total
                pbar.n = downloaded
                pbar.refresh()

            success = self.download_video(url, file_path, update_progress)
            pbar.close()

            # Write metadata
            if success:
                with open(metadata_path, 'a') as meta:
                    meta.write(f"\n{filename}:\n")
                    meta.write(f"  Source: {video.get('source', 'unknown')}\n")
                    meta.write(f"  User: {video.get('user', 'unknown')}\n")
                    meta.write(f"  Dimensions: {video.get('width')}x{video.get('height')}\n")
                    meta.write(f"  Duration: {video.get('duration')}s\n")
                    meta.write(f"  URL: {url}\n")

            return idx, success, filename

        # Execute parallel downloads
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {
                executor.submit(download_task, i, video): i
                for i, video in enumerate(videos)
            }

            # Overall progress bar
            overall_pbar = tqdm(total=len(videos), desc="Overall progress", unit="video")

            for future in as_completed(futures):
                idx, success, info = future.result()
                if success:
                    successful += 1
                else:
                    failed += 1

                overall_pbar.update(1)

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(successful, failed, len(videos))

            overall_pbar.close()

        print(f"\n✓ Download complete!")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Output: {output_path}")

        return str(output_path)


def main():
    """Command-line interface for video fetcher."""
    parser = argparse.ArgumentParser(
        description="Advanced video fetcher with multiple sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick fetch
  %(prog)s "ocean waves" 10

  # Specify sources and quality
  %(prog)s "sunset timelapse" 20 --sources pexels,pixabay --quality hd

  # Advanced filters
  %(prog)s "nature" 15 --orientation landscape --min-duration 10 --max-duration 30

  # Interactive mode
  %(prog)s -i

  # Setup wizard
  %(prog)s --setup
        """
    )

    # Positional arguments
    parser.add_argument("theme", nargs="?", help="Video theme/search query")
    parser.add_argument("count", nargs="?", type=int, help="Number of videos to download")

    # Optional arguments
    parser.add_argument("--sources", default="all", help="Comma-separated sources (all, pexels, pixabay)")
    parser.add_argument("--quality", default="hd", choices=["hd", "medium", "high"],
                        help="Video quality preference")
    parser.add_argument("--orientation", choices=["landscape", "portrait", "square"],
                        help="Video orientation filter")
    parser.add_argument("--category", help="Category filter (for Pixabay)")
    parser.add_argument("--min-duration", type=int, help="Minimum video duration (seconds)")
    parser.add_argument("--max-duration", type=int, help="Maximum video duration (seconds)")
    parser.add_argument("--min-width", type=int, help="Minimum video width")
    parser.add_argument("--min-height", type=int, help="Minimum video height")
    parser.add_argument("--output", help="Output directory")

    # Mode arguments
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="Interactive mode")
    parser.add_argument("--setup", action="store_true",
                        help="Run configuration setup wizard")

    args = parser.parse_args()

    # Setup mode
    if args.setup:
        VideoConfig.setup_wizard()
        return

    # Load config
    config = VideoConfig.load_config()
    fetcher = VideoFetcher(config)

    # Interactive mode
    if args.interactive:
        print("\n=== Video Fetcher - Interactive Mode ===\n")

        theme = input("Enter video theme: ").strip()
        if not theme:
            print("Theme is required.")
            return

        count = input("Number of videos [10]: ").strip()
        count = int(count) if count else 10

        available = fetcher.source_manager.get_available_sources()
        print(f"\nAvailable sources: {', '.join(available)}")
        sources = input("Sources [all]: ").strip() or "all"

        quality = input("Quality (hd/medium/high) [hd]: ").strip() or "hd"

        orientation = input("Orientation (landscape/portrait/square) [any]: ").strip() or None
        category = input("Category [any]: ").strip() or None

        filters = {}
        if orientation:
            filters["orientation"] = orientation
        if category:
            filters["category"] = category

        print("\nStarting download...")
        fetcher.fetch_and_process(theme, count, sources, quality, **filters)

    # Quick mode
    elif args.theme and args.count:
        filters = {}
        if args.orientation:
            filters["orientation"] = args.orientation
        if args.category:
            filters["category"] = args.category
        if args.min_duration:
            filters["min_duration"] = args.min_duration
        if args.max_duration:
            filters["max_duration"] = args.max_duration
        if args.min_width:
            filters["min_width"] = args.min_width
        if args.min_height:
            filters["min_height"] = args.min_height

        if args.output:
            fetcher.output_dir = args.output

        fetcher.fetch_and_process(
            args.theme,
            args.count,
            args.sources,
            args.quality,
            **filters
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
