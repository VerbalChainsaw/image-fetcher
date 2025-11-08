"""
Image Database - Tracks downloaded images to prevent duplicates

This module provides a SQLite-based database to track all downloaded images
across sessions. It stores both URLs and image hashes to detect duplicates
even when the same image comes from different sources or URLs.
"""

import sqlite3
import hashlib
import os
import logging
from datetime import datetime
from pathlib import Path
from PIL import Image


class ImageDatabase:
    """Manages a database of downloaded images to prevent duplicates"""

    def __init__(self, db_path=None):
        """
        Initialize the image database

        Args:
            db_path: Path to SQLite database file. If None, uses ~/.image_fetcher.db
        """
        if db_path is None:
            db_path = os.path.expanduser('~/.image_fetcher.db')

        self.db_path = db_path
        self.conn = None
        self._init_database()

    def _init_database(self):
        """Initialize database connection and create tables if needed"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row

            # Create tables
            cursor = self.conn.cursor()

            # Table for downloaded images
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS downloaded_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    image_hash TEXT NOT NULL,
                    source TEXT NOT NULL,
                    theme TEXT,
                    filename TEXT,
                    download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_size INTEGER,
                    width INTEGER,
                    height INTEGER,
                    UNIQUE(url)
                )
            ''')

            # Index on hash for fast duplicate detection
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_image_hash
                ON downloaded_images(image_hash)
            ''')

            # Index on source for filtering
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_source
                ON downloaded_images(source)
            ''')

            # Table for download statistics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS download_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    theme TEXT NOT NULL,
                    source TEXT NOT NULL,
                    requested_count INTEGER,
                    downloaded_count INTEGER,
                    duplicate_count INTEGER,
                    failed_count INTEGER,
                    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            self.conn.commit()
            logging.info(f"Image database initialized at {self.db_path}")

        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")
            raise

    def calculate_image_hash(self, image_data):
        """
        Calculate perceptual hash of image data

        Args:
            image_data: PIL Image object or bytes

        Returns:
            str: SHA256 hash of image
        """
        try:
            if isinstance(image_data, Image.Image):
                # Convert PIL Image to bytes for hashing
                # Resize to small size for perceptual hashing
                img_small = image_data.resize((8, 8), Image.Resampling.LANCZOS)
                img_bytes = img_small.tobytes()
            else:
                img_bytes = image_data

            return hashlib.sha256(img_bytes).hexdigest()
        except Exception as e:
            logging.error(f"Error calculating image hash: {e}")
            return None

    def is_duplicate_url(self, url):
        """
        Check if a URL has already been downloaded

        Args:
            url: Image URL to check

        Returns:
            bool: True if URL exists in database
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM downloaded_images WHERE url = ?', (url,))
            result = cursor.fetchone()
            return result is not None
        except Exception as e:
            logging.error(f"Error checking duplicate URL: {e}")
            return False

    def is_duplicate_hash(self, image_hash):
        """
        Check if an image hash already exists (same image, different URL)

        Args:
            image_hash: Image hash to check

        Returns:
            bool: True if hash exists in database
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM downloaded_images WHERE image_hash = ?', (image_hash,))
            result = cursor.fetchone()
            return result is not None
        except Exception as e:
            logging.error(f"Error checking duplicate hash: {e}")
            return False

    def add_image(self, url, image_hash, source, theme=None, filename=None,
                  file_size=None, width=None, height=None):
        """
        Add a downloaded image to the database

        Args:
            url: Image source URL
            image_hash: Calculated image hash
            source: Source provider (pexels, pixabay, duckduckgo)
            theme: Search theme/query
            filename: Saved filename
            file_size: File size in bytes
            width: Image width
            height: Image height
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO downloaded_images
                (url, image_hash, source, theme, filename, file_size, width, height)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (url, image_hash, source, theme, filename, file_size, width, height))
            self.conn.commit()
            logging.debug(f"Added image to database: {filename} from {source}")
        except Exception as e:
            logging.error(f"Error adding image to database: {e}")

    def record_session_stats(self, theme, source, requested, downloaded, duplicates, failed):
        """
        Record statistics for a download session

        Args:
            theme: Search theme
            source: Source provider
            requested: Number of images requested
            downloaded: Number successfully downloaded
            duplicates: Number of duplicates skipped
            failed: Number of failed downloads
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO download_stats
                (theme, source, requested_count, downloaded_count, duplicate_count, failed_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (theme, source, requested, downloaded, duplicates, failed))
            self.conn.commit()
        except Exception as e:
            logging.error(f"Error recording session stats: {e}")

    def get_stats_by_theme(self, theme):
        """
        Get download statistics for a specific theme

        Args:
            theme: Search theme

        Returns:
            list: List of statistics rows
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT source,
                       SUM(requested_count) as total_requested,
                       SUM(downloaded_count) as total_downloaded,
                       SUM(duplicate_count) as total_duplicates,
                       SUM(failed_count) as total_failed
                FROM download_stats
                WHERE theme = ?
                GROUP BY source
            ''', (theme,))
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting stats by theme: {e}")
            return []

    def get_stats_by_source(self, source):
        """
        Get download statistics for a specific source

        Args:
            source: Source provider

        Returns:
            list: List of statistics rows
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT theme,
                       SUM(requested_count) as total_requested,
                       SUM(downloaded_count) as total_downloaded,
                       SUM(duplicate_count) as total_duplicates,
                       SUM(failed_count) as total_failed,
                       MAX(session_date) as last_download
                FROM download_stats
                WHERE source = ?
                GROUP BY theme
                ORDER BY last_download DESC
                LIMIT 20
            ''', (source,))
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting stats by source: {e}")
            return []

    def get_duplicate_count(self, theme=None, source=None):
        """
        Get count of duplicates for a theme/source

        Args:
            theme: Optional theme filter
            source: Optional source filter

        Returns:
            int: Number of duplicates
        """
        try:
            cursor = self.conn.cursor()

            if theme and source:
                cursor.execute('''
                    SELECT COUNT(*) FROM downloaded_images
                    WHERE theme = ? AND source = ?
                ''', (theme, source))
            elif theme:
                cursor.execute('''
                    SELECT COUNT(*) FROM downloaded_images
                    WHERE theme = ?
                ''', (theme,))
            elif source:
                cursor.execute('''
                    SELECT COUNT(*) FROM downloaded_images
                    WHERE source = ?
                ''', (source,))
            else:
                cursor.execute('SELECT COUNT(*) FROM downloaded_images')

            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logging.error(f"Error getting duplicate count: {e}")
            return 0

    def clear_old_entries(self, days=30):
        """
        Clear database entries older than specified days

        Args:
            days: Number of days to keep (default: 30)

        Returns:
            int: Number of entries deleted
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                DELETE FROM downloaded_images
                WHERE download_date < datetime('now', ? || ' days')
            ''', (f'-{days}',))
            deleted = cursor.rowcount
            self.conn.commit()
            logging.info(f"Cleared {deleted} entries older than {days} days")
            return deleted
        except Exception as e:
            logging.error(f"Error clearing old entries: {e}")
            return 0

    def get_total_images(self):
        """Get total number of tracked images"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM downloaded_images')
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logging.error(f"Error getting total images: {e}")
            return 0

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logging.debug("Database connection closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def print_database_stats():
    """Print statistics about the image database"""
    try:
        with ImageDatabase() as db:
            total = db.get_total_images()
            print(f"\n{'='*60}")
            print(f"Image Database Statistics")
            print(f"{'='*60}")
            print(f"Total images tracked: {total}")
            print(f"Database location: {db.db_path}")

            if total > 0:
                print(f"\n{'Recent downloads by source:'}")
                print(f"{'-'*60}")

                for source in ['pexels', 'pixabay', 'duckduckgo']:
                    stats = db.get_stats_by_source(source)
                    if stats:
                        print(f"\n{source.upper()}:")
                        for row in stats[:5]:  # Top 5 themes
                            print(f"  Theme: {row['theme']}")
                            print(f"    Downloaded: {row['total_downloaded']}, "
                                  f"Duplicates: {row['total_duplicates']}, "
                                  f"Failed: {row['total_failed']}")

            print(f"\n{'='*60}\n")
    except Exception as e:
        print(f"Error printing stats: {e}")


if __name__ == '__main__':
    # Run stats when executed directly
    print_database_stats()
