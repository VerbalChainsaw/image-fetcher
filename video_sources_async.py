"""
Async video source providers with advanced features:
- Concurrent API requests
- Circuit breaker pattern
- Intelligent retry with exponential backoff
- Connection pooling
- Rate limiting
"""

import asyncio
import aiohttp
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreaker:
    """Circuit breaker for handling service failures."""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 3

    def __post_init__(self):
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.half_open_calls = 0

    def call_succeeded(self):
        """Record successful call."""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.half_open_calls = 0
            logger.info("Circuit breaker closed - service recovered")

    def call_failed(self):
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning("Circuit breaker opened - service still failing")
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def can_attempt(self) -> bool:
        """Check if call can be attempted."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info("Circuit breaker entering half-open state")
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False

        return False


class AsyncVideoSource(ABC):
    """Abstract base class for async video sources."""

    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.session = session
        self.circuit_breaker = CircuitBreaker()

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 10,
        **kwargs
    ) -> List[Dict]:
        """Search for videos asynchronously."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return source name."""
        pass

    async def retry_with_backoff(
        self,
        coro,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0
    ):
        """
        Retry coroutine with exponential backoff.

        Args:
            coro: Coroutine to retry
            max_retries: Maximum retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay cap
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                if not self.circuit_breaker.can_attempt():
                    raise Exception(f"Circuit breaker open for {self.get_name()}")

                result = await coro
                self.circuit_breaker.call_succeeded()
                return result

            except Exception as e:
                last_exception = e
                self.circuit_breaker.call_failed()

                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = delay * 0.1  # 10% jitter
                    await asyncio.sleep(delay + (hash(str(time.time())) % 100) / 1000 * jitter)
                    logger.warning(f"Retry {attempt + 1}/{max_retries} for {self.get_name()}: {str(e)[:100]}")
                else:
                    logger.error(f"All retries failed for {self.get_name()}: {str(e)[:100]}")

        raise last_exception


class AsyncPexelsVideoSource(AsyncVideoSource):
    """Async Pexels video API source."""

    def __init__(self, api_key: str, session: Optional[aiohttp.ClientSession] = None):
        super().__init__(session)
        self.api_key = api_key
        self.base_url = "https://api.pexels.com/videos"

    async def search(self, query: str, max_results: int = 10, **kwargs) -> List[Dict]:
        """Search Pexels for videos asynchronously."""

        async def _search():
            headers = {"Authorization": self.api_key}
            params = {
                "query": query,
                "per_page": min(max_results, 80),
                "page": 1
            }

            # Add optional filters
            for key in ['orientation', 'size', 'min_width', 'min_height', 'min_duration', 'max_duration']:
                if key in kwargs:
                    params[key] = kwargs[key]

            async with self.session.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                response.raise_for_status()
                data = await response.json()

                videos = []
                for video in data.get("videos", []):
                    video_files = video.get("video_files", [])
                    if not video_files:
                        continue

                    # Sort by quality
                    video_files.sort(key=lambda x: x.get("width", 0), reverse=True)
                    best_quality = video_files[0]

                    # Get medium quality option
                    medium_quality = None
                    for vf in video_files:
                        if 1280 <= vf.get("width", 0) <= 1920:
                            medium_quality = vf
                            break

                    videos.append({
                        "url": best_quality.get("link"),
                        "url_medium": medium_quality.get("link") if medium_quality else best_quality.get("link"),
                        "thumbnail": video.get("image"),
                        "width": best_quality.get("width"),
                        "height": best_quality.get("height"),
                        "duration": video.get("duration"),
                        "source": "pexels",
                        "user": video.get("user", {}).get("name", "Unknown"),
                        "id": video.get("id")
                    })

                return videos[:max_results]

        try:
            return await self.retry_with_backoff(_search())
        except Exception as e:
            logger.error(f"Pexels search failed: {str(e)[:100]}")
            return []

    def get_name(self) -> str:
        return "pexels"


class AsyncPixabayVideoSource(AsyncVideoSource):
    """Async Pixabay video API source."""

    CATEGORIES = [
        "backgrounds", "fashion", "nature", "science", "education",
        "feelings", "health", "people", "religion", "places", "animals",
        "industry", "computer", "food", "sports", "transportation",
        "travel", "buildings", "business", "music"
    ]

    def __init__(self, api_key: str, session: Optional[aiohttp.ClientSession] = None):
        super().__init__(session)
        self.api_key = api_key
        self.base_url = "https://pixabay.com/api/videos/"

    async def search(self, query: str, max_results: int = 10, **kwargs) -> List[Dict]:
        """Search Pixabay for videos asynchronously."""

        async def _search():
            params = {
                "key": self.api_key,
                "q": query,
                "video_type": "all",
                "per_page": min(max_results, 200),
                "safesearch": "true"
            }

            # Add optional filters
            if "category" in kwargs and kwargs["category"] in self.CATEGORIES:
                params["category"] = kwargs["category"]
            for key in ['min_width', 'min_height']:
                if key in kwargs:
                    params[key] = kwargs[key]

            async with self.session.get(
                self.base_url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                response.raise_for_status()
                data = await response.json()

                videos = []
                for hit in data.get("hits", []):
                    video_files = hit.get("videos", {})

                    # Priority: large > medium > small
                    best_url = None
                    medium_url = None
                    best_width = 0
                    best_height = 0

                    if "large" in video_files:
                        best_url = video_files["large"].get("url")
                        best_width = video_files["large"].get("width", 1920)
                        best_height = video_files["large"].get("height", 1080)
                    elif "medium" in video_files:
                        best_url = video_files["medium"].get("url")
                        best_width = video_files["medium"].get("width", 1280)
                        best_height = video_files["medium"].get("height", 720)
                    elif "small" in video_files:
                        best_url = video_files["small"].get("url")
                        best_width = video_files["small"].get("width", 640)
                        best_height = video_files["small"].get("height", 360)

                    if not best_url:
                        continue

                    if "medium" in video_files:
                        medium_url = video_files["medium"].get("url")
                    else:
                        medium_url = best_url

                    videos.append({
                        "url": best_url,
                        "url_medium": medium_url,
                        "thumbnail": hit.get("userImageURL"),
                        "width": best_width,
                        "height": best_height,
                        "duration": hit.get("duration"),
                        "source": "pixabay",
                        "user": hit.get("user", "Unknown"),
                        "id": hit.get("id")
                    })

                return videos[:max_results]

        try:
            return await self.retry_with_backoff(_search())
        except Exception as e:
            logger.error(f"Pixabay search failed: {str(e)[:100]}")
            return []

    def get_name(self) -> str:
        return "pixabay"


class AsyncVideoSourceManager:
    """Manages multiple async video sources with connection pooling."""

    def __init__(
        self,
        pexels_key: Optional[str] = None,
        pixabay_key: Optional[str] = None,
        max_concurrent: int = 10
    ):
        """
        Initialize async source manager.

        Args:
            pexels_key: Pexels API key
            pixabay_key: Pixabay API key
            max_concurrent: Maximum concurrent connections
        """
        self.sources = {}
        self.session = None
        self.max_concurrent = max_concurrent

        # Store keys for lazy initialization
        self.pexels_key = pexels_key
        self.pixabay_key = pixabay_key

    async def __aenter__(self):
        """Async context manager entry."""
        # Create session with connection pooling
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent,
            limit_per_host=5,
            ttl_dns_cache=300
        )

        timeout = aiohttp.ClientTimeout(total=30, connect=10)

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (VideoFetcher/2.0)"}
        )

        # Initialize sources with shared session
        if self.pexels_key:
            self.sources["pexels"] = AsyncPexelsVideoSource(self.pexels_key, self.session)
        if self.pixabay_key:
            self.sources["pixabay"] = AsyncPixabayVideoSource(self.pixabay_key, self.session)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def search(
        self,
        query: str,
        max_results: int = 10,
        sources: str = "all",
        **kwargs
    ) -> List[Dict]:
        """
        Search for videos across sources concurrently.

        Args:
            query: Search term
            max_results: Maximum total results
            sources: Comma-separated source names or "all"
            **kwargs: Additional filters
        """
        # Determine active sources
        if sources == "all":
            active_sources = list(self.sources.values())
        else:
            source_names = [s.strip() for s in sources.split(",")]
            active_sources = [
                self.sources[name]
                for name in source_names
                if name in self.sources
            ]

        if not active_sources:
            logger.warning("No valid video sources available")
            return []

        # Calculate per-source quota
        per_source = max(1, max_results // len(active_sources))
        request_per_source = per_source * 2  # Request extra for filtering

        # Search all sources concurrently
        logger.info(f"Searching {len(active_sources)} sources concurrently...")

        tasks = [
            source.search(query, request_per_source, **kwargs)
            for source in active_sources
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results, filtering out exceptions
        all_videos = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Source {active_sources[i].get_name()} failed: {str(result)[:100]}")
            else:
                all_videos.extend(result)

        logger.info(f"Found {len(all_videos)} total videos from {len(active_sources)} sources")

        return all_videos[:max_results]

    def get_available_sources(self) -> List[str]:
        """Return list of available source names."""
        return list(self.sources.keys())
