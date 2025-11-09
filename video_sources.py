"""
Video source providers for the video fetcher application.
Supports multiple video platforms with advanced search and filtering capabilities.
"""

from abc import ABC, abstractmethod
import requests
import time
from typing import List, Dict, Optional


class VideoSource(ABC):
    """Abstract base class for video sources."""

    @abstractmethod
    def search(self, query: str, max_results: int = 10, **kwargs) -> List[Dict]:
        """
        Search for videos based on a query.

        Args:
            query: Search term or theme
            max_results: Maximum number of videos to return
            **kwargs: Additional source-specific parameters

        Returns:
            List of video dictionaries with metadata
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this video source."""
        pass


class PexelsVideoSource(VideoSource):
    """Pexels video API source."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.pexels.com/videos"

    def search(self, query: str, max_results: int = 10, **kwargs) -> List[Dict]:
        """
        Search Pexels for videos.

        Kwargs:
            orientation: 'landscape', 'portrait', or 'square'
            size: 'large', 'medium', or 'small'
            min_width: Minimum video width
            min_height: Minimum video height
            min_duration: Minimum duration in seconds
            max_duration: Maximum duration in seconds
        """
        headers = {"Authorization": self.api_key}

        params = {
            "query": query,
            "per_page": min(max_results, 80),  # Pexels max per page
            "page": 1
        }

        # Add optional filters
        if "orientation" in kwargs:
            params["orientation"] = kwargs["orientation"]
        if "size" in kwargs:
            params["size"] = kwargs["size"]
        if "min_width" in kwargs:
            params["min_width"] = kwargs["min_width"]
        if "min_height" in kwargs:
            params["min_height"] = kwargs["min_height"]
        if "min_duration" in kwargs:
            params["min_duration"] = kwargs["min_duration"]
        if "max_duration" in kwargs:
            params["max_duration"] = kwargs["max_duration"]

        try:
            response = requests.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            videos = []
            for video in data.get("videos", []):
                # Get the highest quality video file
                video_files = video.get("video_files", [])
                if not video_files:
                    continue

                # Sort by quality (width) and get HD version
                video_files.sort(key=lambda x: x.get("width", 0), reverse=True)
                best_quality = video_files[0]

                # Also get a medium quality for faster downloads if needed
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

        except requests.exceptions.RequestException as e:
            print(f"Error fetching from Pexels: {str(e)[:100]}")
            return []

    def get_name(self) -> str:
        return "pexels"


class PixabayVideoSource(VideoSource):
    """Pixabay video API source."""

    CATEGORIES = [
        "backgrounds", "fashion", "nature", "science", "education",
        "feelings", "health", "people", "religion", "places", "animals",
        "industry", "computer", "food", "sports", "transportation",
        "travel", "buildings", "business", "music"
    ]

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://pixabay.com/api/videos/"

    def search(self, query: str, max_results: int = 10, **kwargs) -> List[Dict]:
        """
        Search Pixabay for videos.

        Kwargs:
            category: One of the predefined categories
            min_width: Minimum video width
            min_height: Minimum video height
        """
        params = {
            "key": self.api_key,
            "q": query,
            "video_type": "all",
            "per_page": min(max_results, 200),  # Pixabay max per page
            "safesearch": "true"
        }

        # Add optional filters
        if "category" in kwargs and kwargs["category"] in self.CATEGORIES:
            params["category"] = kwargs["category"]
        if "min_width" in kwargs:
            params["min_width"] = kwargs["min_width"]
        if "min_height" in kwargs:
            params["min_height"] = kwargs["min_height"]

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            videos = []
            for hit in data.get("hits", []):
                # Get available video sizes
                video_files = hit.get("videos", {})

                # Prefer HD quality
                best_url = None
                medium_url = None

                # Priority: large > medium > small
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
                else:
                    continue

                # Get medium quality URL
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

        except requests.exceptions.RequestException as e:
            print(f"Error fetching from Pixabay: {str(e)[:100]}")
            return []

    def get_name(self) -> str:
        return "pixabay"


class VidevoSource(VideoSource):
    """
    Videvo free stock video source.
    Note: This uses web scraping as Videvo doesn't have a public API.
    """

    def __init__(self):
        self.base_url = "https://www.videvo.net"

    def search(self, query: str, max_results: int = 10, **kwargs) -> List[Dict]:
        """
        Search Videvo for videos.
        Uses web scraping to find free stock videos.
        """
        # Note: This is a placeholder implementation
        # A full implementation would require BeautifulSoup or similar
        # For now, return empty to avoid web scraping complexity
        print("Videvo source: Web scraping not yet implemented")
        return []

    def get_name(self) -> str:
        return "videvo"


class VideoSourceManager:
    """Manages multiple video sources and aggregates results."""

    def __init__(self, pexels_key: Optional[str] = None, pixabay_key: Optional[str] = None):
        self.sources = {}

        # Initialize sources with valid API keys
        if pexels_key:
            self.sources["pexels"] = PexelsVideoSource(pexels_key)
        if pixabay_key:
            self.sources["pixabay"] = PixabayVideoSource(pixabay_key)

        # Videvo is free but not fully implemented yet
        # self.sources["videvo"] = VidevoSource()

    def search(
        self,
        query: str,
        max_results: int = 10,
        sources: str = "all",
        **kwargs
    ) -> List[Dict]:
        """
        Search for videos across specified sources.

        Args:
            query: Search term or theme
            max_results: Maximum total number of videos to return
            sources: Comma-separated source names or "all"
            **kwargs: Additional search parameters (filters)

        Returns:
            List of video dictionaries from all requested sources
        """
        # Determine which sources to use
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
            print("No valid video sources available. Please configure API keys.")
            return []

        # Calculate per-source quota
        per_source = max(1, max_results // len(active_sources))

        # Request extra to account for potential filtering/failures
        request_per_source = per_source * 2

        all_videos = []
        for source in active_sources:
            print(f"Searching {source.get_name()}...")
            videos = source.search(query, request_per_source, **kwargs)
            all_videos.extend(videos)
            time.sleep(0.5)  # Small delay to be respectful to APIs

        return all_videos[:max_results]

    def get_available_sources(self) -> List[str]:
        """Return list of available source names."""
        return list(self.sources.keys())

    def get_categories(self, source_name: str) -> List[str]:
        """Get available categories for a specific source."""
        if source_name == "pixabay" and "pixabay" in self.sources:
            return PixabayVideoSource.CATEGORIES
        return []
