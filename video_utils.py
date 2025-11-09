"""
Video utility functions for advanced operations.

Features:
- Thumbnail generation with FFmpeg
- Video compression
- Format conversion
- Metadata extraction
- Batch processing
"""

import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import hashlib


logger = logging.getLogger(__name__)


@dataclass
class VideoInfo:
    """Video file information."""
    path: Path
    duration: float
    width: int
    height: int
    fps: float
    bitrate: int
    codec: str
    size_bytes: int
    format: str


class VideoThumbnailGenerator:
    """Generate video thumbnails using FFmpeg."""

    def __init__(self):
        self.has_ffmpeg = self._check_ffmpeg()

    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                check=True,
                timeout=5
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("FFmpeg not available - thumbnail generation disabled")
            return False

    def generate_thumbnail(
        self,
        video_path: Path,
        output_path: Path,
        timestamp: float = 0.0,
        width: int = 320,
        height: int = 180
    ) -> bool:
        """
        Generate a thumbnail from video at specified timestamp.

        Args:
            video_path: Path to video file
            output_path: Path to save thumbnail
            timestamp: Time in seconds to capture (0.0 for first frame)
            width: Thumbnail width
            height: Thumbnail height

        Returns:
            True if successful
        """
        if not self.has_ffmpeg:
            return False

        try:
            # Create output directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # FFmpeg command
            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),
                '-i', str(video_path),
                '-vframes', '1',
                '-vf', f'scale={width}:{height}',
                '-y',  # Overwrite output
                str(output_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30,
                check=True
            )

            logger.info(f"Generated thumbnail: {output_path.name}")
            return True

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout generating thumbnail for {video_path.name}")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate thumbnail: {e.stderr.decode()[:200]}")
            return False
        except Exception as e:
            logger.error(f"Error generating thumbnail: {str(e)[:100]}")
            return False

    def generate_multiple_thumbnails(
        self,
        video_path: Path,
        output_dir: Path,
        count: int = 5,
        width: int = 320,
        height: int = 180
    ) -> List[Path]:
        """
        Generate multiple thumbnails at intervals throughout the video.

        Args:
            video_path: Path to video file
            output_dir: Directory to save thumbnails
            count: Number of thumbnails to generate
            width: Thumbnail width
            height: Thumbnail height

        Returns:
            List of generated thumbnail paths
        """
        if not self.has_ffmpeg:
            return []

        # Get video duration
        info = self.get_video_info(video_path)
        if not info:
            return []

        duration = info.duration
        if duration <= 0:
            return []

        # Calculate timestamps
        interval = duration / (count + 1)
        timestamps = [interval * (i + 1) for i in range(count)]

        # Generate thumbnails
        thumbnails = []
        for i, timestamp in enumerate(timestamps):
            output_path = output_dir / f"{video_path.stem}_thumb_{i+1}.jpg"

            if self.generate_thumbnail(video_path, output_path, timestamp, width, height):
                thumbnails.append(output_path)

        logger.info(f"Generated {len(thumbnails)}/{count} thumbnails")
        return thumbnails

    def generate_sprite_sheet(
        self,
        video_path: Path,
        output_path: Path,
        tiles_x: int = 5,
        tiles_y: int = 5,
        tile_width: int = 160,
        tile_height: int = 90
    ) -> bool:
        """
        Generate a sprite sheet (grid of thumbnails) from video.

        Args:
            video_path: Path to video file
            output_path: Path to save sprite sheet
            tiles_x: Number of tiles horizontally
            tiles_y: Number of tiles vertically
            tile_width: Width of each tile
            tile_height: Height of each tile

        Returns:
            True if successful
        """
        if not self.has_ffmpeg:
            return False

        try:
            total_tiles = tiles_x * tiles_y

            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-vf', f'fps=1/{total_tiles},scale={tile_width}:{tile_height},tile={tiles_x}x{tiles_y}',
                '-frames:v', '1',
                '-y',
                str(output_path)
            ]

            subprocess.run(cmd, capture_output=True, timeout=60, check=True)

            logger.info(f"Generated sprite sheet: {output_path.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate sprite sheet: {str(e)[:100]}")
            return False

    def get_video_info(self, video_path: Path) -> Optional[VideoInfo]:
        """
        Extract detailed video information using FFprobe.

        Args:
            video_path: Path to video file

        Returns:
            VideoInfo object or None
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(video_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )

            data = json.loads(result.stdout)

            # Find video stream
            video_stream = next(
                (s for s in data.get('streams', []) if s['codec_type'] == 'video'),
                None
            )

            if not video_stream:
                return None

            format_info = data.get('format', {})

            # Parse frame rate
            fps = 0.0
            if 'r_frame_rate' in video_stream:
                fps_str = video_stream['r_frame_rate']
                if '/' in fps_str:
                    num, den = map(int, fps_str.split('/'))
                    fps = num / den if den > 0 else 0.0

            return VideoInfo(
                path=video_path,
                duration=float(format_info.get('duration', 0)),
                width=video_stream.get('width', 0),
                height=video_stream.get('height', 0),
                fps=fps,
                bitrate=int(format_info.get('bit_rate', 0)),
                codec=video_stream.get('codec_name', 'unknown'),
                size_bytes=int(format_info.get('size', 0)),
                format=format_info.get('format_name', 'unknown')
            )

        except Exception as e:
            logger.error(f"Failed to get video info: {str(e)[:100]}")
            return None


class VideoBatchProcessor:
    """Batch process videos with various operations."""

    def __init__(self):
        self.thumbnail_gen = VideoThumbnailGenerator()

    def process_directory(
        self,
        directory: Path,
        generate_thumbnails: bool = True,
        thumbnail_dir: Optional[Path] = None
    ) -> Dict[str, any]:
        """
        Process all videos in a directory.

        Args:
            directory: Directory containing videos
            generate_thumbnails: Whether to generate thumbnails
            thumbnail_dir: Custom thumbnail directory

        Returns:
            Processing results
        """
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return {"error": "Directory not found"}

        # Find all video files
        video_extensions = {'.mp4', '.webm', '.avi', '.mov', '.mkv', '.flv'}
        video_files = [
            f for f in directory.rglob('*')
            if f.suffix.lower() in video_extensions
        ]

        logger.info(f"Found {len(video_files)} video files")

        results = {
            "total_files": len(video_files),
            "processed": 0,
            "failed": 0,
            "thumbnails_generated": 0,
            "files": []
        }

        thumb_dir = thumbnail_dir or directory / "thumbnails"
        thumb_dir.mkdir(exist_ok=True)

        for video_file in video_files:
            try:
                # Get video info
                info = self.thumbnail_gen.get_video_info(video_file)

                file_result = {
                    "path": str(video_file),
                    "name": video_file.name,
                    "info": None,
                    "thumbnail": None
                }

                if info:
                    file_result["info"] = {
                        "duration": info.duration,
                        "resolution": f"{info.width}x{info.height}",
                        "fps": info.fps,
                        "codec": info.codec,
                        "size_mb": info.size_bytes / 1024 / 1024
                    }

                # Generate thumbnail
                if generate_thumbnails and self.thumbnail_gen.has_ffmpeg:
                    thumb_path = thumb_dir / f"{video_file.stem}.jpg"

                    if self.thumbnail_gen.generate_thumbnail(
                        video_file,
                        thumb_path,
                        timestamp=info.duration / 2 if info else 0.0
                    ):
                        file_result["thumbnail"] = str(thumb_path)
                        results["thumbnails_generated"] += 1

                results["files"].append(file_result)
                results["processed"] += 1

            except Exception as e:
                logger.error(f"Error processing {video_file.name}: {str(e)[:100]}")
                results["failed"] += 1

        logger.info(f"Batch processing complete: {results['processed']}/{results['total_files']} files")
        return results

    def generate_catalog(
        self,
        directory: Path,
        output_file: Path
    ) -> bool:
        """
        Generate a video catalog (JSON file with all video info).

        Args:
            directory: Directory to catalog
            output_file: Output JSON file

        Returns:
            True if successful
        """
        results = self.process_directory(directory, generate_thumbnails=False)

        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)

            logger.info(f"Catalog saved to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save catalog: {str(e)}")
            return False


class VideoHasher:
    """Generate hashes for videos for deduplication."""

    @staticmethod
    def hash_file(file_path: Path, chunk_size: int = 8192) -> str:
        """Generate SHA256 hash of entire file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def hash_partial(file_path: Path, size_mb: int = 1) -> str:
        """
        Generate hash of first N megabytes for faster comparison.

        Useful for quick duplicate detection on large files.
        """
        sha256 = hashlib.sha256()
        bytes_to_read = size_mb * 1024 * 1024

        with open(file_path, 'rb') as f:
            data = f.read(bytes_to_read)
            sha256.update(data)

        return sha256.hexdigest()

    @staticmethod
    def find_duplicates(directory: Path) -> Dict[str, List[Path]]:
        """
        Find duplicate videos in directory by hash.

        Returns:
            Dictionary mapping hash to list of duplicate files
        """
        hashes = {}
        video_extensions = {'.mp4', '.webm', '.avi', '.mov', '.mkv'}

        video_files = [
            f for f in directory.rglob('*')
            if f.suffix.lower() in video_extensions
        ]

        logger.info(f"Scanning {len(video_files)} files for duplicates...")

        for video_file in video_files:
            try:
                # Use partial hash for speed
                file_hash = VideoHasher.hash_partial(video_file)

                if file_hash not in hashes:
                    hashes[file_hash] = []

                hashes[file_hash].append(video_file)

            except Exception as e:
                logger.error(f"Error hashing {video_file.name}: {str(e)[:100]}")

        # Filter to only duplicates
        duplicates = {h: files for h, files in hashes.items() if len(files) > 1}

        logger.info(f"Found {len(duplicates)} sets of duplicates")
        return duplicates
