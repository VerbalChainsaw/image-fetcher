"""
Advanced database layer for video fetcher.
Provides download history, deduplication, analytics, and queue management.
"""

import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager
import threading


class VideoDatabase:
    """Thread-safe SQLite database for video management."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database with schema creation."""
        if db_path is None:
            db_path = str(Path.home() / ".video_fetcher.db")

        self.db_path = db_path
        self.local = threading.local()
        self._init_database()

    @contextmanager
    def get_connection(self):
        """Thread-safe database connection context manager."""
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.local.conn.row_factory = sqlite3.Row

        try:
            yield self.local.conn
        except Exception as e:
            self.local.conn.rollback()
            raise e

    def _init_database(self):
        """Create database schema if not exists."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Downloads table - complete download history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT,
                    source TEXT NOT NULL,
                    theme TEXT NOT NULL,
                    url TEXT NOT NULL,
                    url_hash TEXT UNIQUE NOT NULL,
                    file_path TEXT,
                    file_hash TEXT,
                    file_size INTEGER,
                    width INTEGER,
                    height INTEGER,
                    duration REAL,
                    quality TEXT,
                    orientation TEXT,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    download_speed REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    metadata TEXT
                )
            """)

            # Download chunks table - for resume capability
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    download_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    start_byte INTEGER NOT NULL,
                    end_byte INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (download_id) REFERENCES downloads(id),
                    UNIQUE(download_id, chunk_index)
                )
            """)

            # Queue table - prioritized download queue
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    theme TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    sources TEXT NOT NULL,
                    quality TEXT NOT NULL,
                    filters TEXT,
                    priority INTEGER DEFAULT 0,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    progress INTEGER DEFAULT 0,
                    error_message TEXT
                )
            """)

            # Search history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    source TEXT,
                    results_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Statistics table - aggregated stats
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL UNIQUE,
                    total_downloads INTEGER DEFAULT 0,
                    successful_downloads INTEGER DEFAULT 0,
                    failed_downloads INTEGER DEFAULT 0,
                    total_size_bytes INTEGER DEFAULT 0,
                    total_duration_seconds REAL DEFAULT 0,
                    avg_download_speed REAL DEFAULT 0
                )
            """)

            # Rate limiting table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL UNIQUE,
                    requests_count INTEGER DEFAULT 0,
                    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_request TIMESTAMP
                )
            """)

            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_downloads_url_hash
                ON downloads(url_hash)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_downloads_file_hash
                ON downloads(file_hash)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_downloads_theme
                ON downloads(theme)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_downloads_status
                ON downloads(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_downloads_created_at
                ON downloads(created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_queue_status
                ON download_queue(status, priority DESC)
            """)

            conn.commit()

    @staticmethod
    def hash_url(url: str) -> str:
        """Generate consistent hash for URL."""
        return hashlib.sha256(url.encode()).hexdigest()

    @staticmethod
    def hash_file(file_path: Path, chunk_size: int = 8192) -> str:
        """Generate SHA256 hash of file for deduplication."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()

    def is_duplicate_url(self, url: str) -> bool:
        """Check if URL has been downloaded before."""
        url_hash = self.hash_url(url)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM downloads WHERE url_hash = ? AND status = 'completed'",
                (url_hash,)
            )
            return cursor.fetchone()[0] > 0

    def is_duplicate_file(self, file_hash: str) -> bool:
        """Check if file hash exists (content duplicate)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM downloads WHERE file_hash = ?",
                (file_hash,)
            )
            return cursor.fetchone()[0] > 0

    def add_download(
        self,
        source: str,
        theme: str,
        url: str,
        metadata: Optional[Dict] = None
    ) -> int:
        """Add new download record. Returns download ID."""
        url_hash = self.hash_url(url)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO downloads
                (source, theme, url, url_hash, status, metadata, video_id, width, height, duration, quality)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source,
                theme,
                url,
                url_hash,
                'pending',
                json.dumps(metadata) if metadata else None,
                metadata.get('id') if metadata else None,
                metadata.get('width') if metadata else None,
                metadata.get('height') if metadata else None,
                metadata.get('duration') if metadata else None,
                metadata.get('quality') if metadata else None
            ))
            conn.commit()
            return cursor.lastrowid

    def update_download(
        self,
        download_id: int,
        status: Optional[str] = None,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        error_message: Optional[str] = None,
        download_speed: Optional[float] = None
    ):
        """Update download record."""
        updates = []
        params = []

        if status:
            updates.append("status = ?")
            params.append(status)
            if status == 'completed':
                updates.append("completed_at = CURRENT_TIMESTAMP")

        if file_path:
            updates.append("file_path = ?")
            params.append(file_path)

        if file_size is not None:
            updates.append("file_size = ?")
            params.append(file_size)

        if error_message:
            updates.append("error_message = ?")
            params.append(error_message)

        if download_speed is not None:
            updates.append("download_speed = ?")
            params.append(download_speed)

        if not updates:
            return

        params.append(download_id)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE downloads SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()

    def set_file_hash(self, download_id: int, file_hash: str):
        """Set file hash after download completion."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE downloads SET file_hash = ? WHERE id = ?",
                (file_hash, download_id)
            )
            conn.commit()

    def get_download_stats(self, days: int = 30) -> Dict:
        """Get download statistics for the last N days."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Overall stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'completed' THEN file_size ELSE 0 END) as total_size,
                    AVG(CASE WHEN status = 'completed' THEN download_speed ELSE NULL END) as avg_speed,
                    SUM(CASE WHEN status = 'completed' THEN duration ELSE 0 END) as total_duration
                FROM downloads
                WHERE created_at >= datetime('now', ?)
            """, (f'-{days} days',))

            row = cursor.fetchone()

            # Per-source stats
            cursor.execute("""
                SELECT
                    source,
                    COUNT(*) as count,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful
                FROM downloads
                WHERE created_at >= datetime('now', ?)
                GROUP BY source
            """, (f'-{days} days',))

            sources = {row['source']: dict(row) for row in cursor.fetchall()}

            # Daily breakdown
            cursor.execute("""
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status = 'completed' THEN file_size ELSE 0 END) as size
                FROM downloads
                WHERE created_at >= datetime('now', ?)
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """, (f'-{days} days',))

            daily = [dict(row) for row in cursor.fetchall()]

            return {
                'total_downloads': row['total'] or 0,
                'successful': row['successful'] or 0,
                'failed': row['failed'] or 0,
                'total_size_bytes': row['total_size'] or 0,
                'avg_speed_mbps': (row['avg_speed'] or 0) / 1024 / 1024 if row['avg_speed'] else 0,
                'total_duration_hours': (row['total_duration'] or 0) / 3600,
                'sources': sources,
                'daily': daily
            }

    def add_search_history(self, query: str, source: str, results_count: int):
        """Record search query for autocomplete/suggestions."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO search_history (query, source, results_count)
                VALUES (?, ?, ?)
            """, (query, source, results_count))
            conn.commit()

    def get_search_suggestions(self, prefix: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on history."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT query, COUNT(*) as frequency
                FROM search_history
                WHERE query LIKE ? || '%'
                GROUP BY query
                ORDER BY frequency DESC, created_at DESC
                LIMIT ?
            """, (prefix, limit))

            return [row['query'] for row in cursor.fetchall()]

    def get_popular_themes(self, limit: int = 20) -> List[Tuple[str, int]]:
        """Get most popular search themes."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT theme, COUNT(*) as count
                FROM downloads
                WHERE status = 'completed'
                GROUP BY theme
                ORDER BY count DESC
                LIMIT ?
            """, (limit,))

            return [(row['theme'], row['count']) for row in cursor.fetchall()]

    def check_rate_limit(self, source: str, max_requests: int, window_seconds: int) -> bool:
        """Check if source has exceeded rate limit. Returns True if allowed."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get or create rate limit record
            cursor.execute("""
                INSERT OR IGNORE INTO rate_limits (source, requests_count)
                VALUES (?, 0)
            """, (source,))

            # Check current window
            cursor.execute("""
                SELECT requests_count,
                       (julianday('now') - julianday(window_start)) * 86400 as elapsed
                FROM rate_limits
                WHERE source = ?
            """, (source,))

            row = cursor.fetchone()

            # Reset window if expired
            if row['elapsed'] > window_seconds:
                cursor.execute("""
                    UPDATE rate_limits
                    SET requests_count = 1,
                        window_start = CURRENT_TIMESTAMP,
                        last_request = CURRENT_TIMESTAMP
                    WHERE source = ?
                """, (source,))
                conn.commit()
                return True

            # Check limit
            if row['requests_count'] >= max_requests:
                return False

            # Increment counter
            cursor.execute("""
                UPDATE rate_limits
                SET requests_count = requests_count + 1,
                    last_request = CURRENT_TIMESTAMP
                WHERE source = ?
            """, (source,))
            conn.commit()
            return True

    def get_recent_downloads(self, limit: int = 50) -> List[Dict]:
        """Get recent download records."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT *
                FROM downloads
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def cleanup_old_records(self, days: int = 90):
        """Clean up old failed downloads and search history."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Remove old failed downloads
            cursor.execute("""
                DELETE FROM downloads
                WHERE status = 'failed'
                AND created_at < datetime('now', ?)
            """, (f'-{days} days',))

            # Remove old search history
            cursor.execute("""
                DELETE FROM search_history
                WHERE created_at < datetime('now', ?)
            """, (f'-{days * 2} days',))

            conn.commit()

    def vacuum(self):
        """Optimize database (reclaim space, rebuild indexes)."""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
            conn.execute("ANALYZE")
