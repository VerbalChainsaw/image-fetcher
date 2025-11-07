#!/usr/bin/env python3
"""
Image source providers for fetching images from various APIs
"""

import time
import requests
from ddgs import DDGS

class ImageSource:
    """Base class for image sources"""

    def search(self, query, max_results=10, category=None):
        """Search for images. Must be implemented by subclasses."""
        raise NotImplementedError


class PexelsSource(ImageSource):
    """Pexels API image source"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.pexels.com/v1"

    def search(self, query, max_results=10, category=None):
        """Search Pexels for images"""
        if not self.api_key:
            return []

        try:
            headers = {'Authorization': self.api_key}
            params = {
                'query': query,
                'per_page': min(max_results, 80),  # Pexels max is 80
                'orientation': category if category in ['landscape', 'portrait', 'square'] else None
            }

            response = requests.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            images = []

            for photo in data.get('photos', []):
                images.append({
                    'url': photo['src']['original'],
                    'thumbnail': photo['src']['medium'],
                    'source': 'pexels',
                    'photographer': photo.get('photographer', 'Unknown'),
                    'title': photo.get('alt', 'Untitled'),
                    'id': photo.get('id', '')
                })

            return images[:max_results]

        except Exception as e:
            import logging
            logging.error(f"Pexels error: {str(e)}")
            print(f"  Pexels error: {str(e)[:80]}...")
            return []


class PixabaySource(ImageSource):
    """Pixabay API image source"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://pixabay.com/api/"

    def search(self, query, max_results=10, category=None):
        """Search Pixabay for images"""
        if not self.api_key:
            return []

        try:
            params = {
                'key': self.api_key,
                'q': query,
                'per_page': min(max_results, 200),  # Pixabay max is 200
                'image_type': 'photo',  # Filter out illustrations and vector graphics
                'safesearch': 'true'
            }

            # Add category if specified
            valid_categories = ['backgrounds', 'fashion', 'nature', 'science',
                              'education', 'feelings', 'health', 'people',
                              'religion', 'places', 'animals', 'industry',
                              'computer', 'food', 'sports', 'transportation',
                              'travel', 'buildings', 'business', 'music']

            if category and category.lower() in valid_categories:
                params['category'] = category.lower()

            response = requests.get(
                self.base_url,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            images = []

            for hit in data.get('hits', []):
                images.append({
                    'url': hit['largeImageURL'],
                    'thumbnail': hit['previewURL'],
                    'source': 'pixabay',
                    'photographer': hit.get('user', 'Unknown'),
                    'title': hit.get('tags', 'Untitled'),
                    'id': hit.get('id', '')
                })

            return images[:max_results]

        except Exception as e:
            import logging
            logging.error(f"Pixabay error: {str(e)}")
            print(f"  Pixabay error: {str(e)[:80]}...")
            return []


class DuckDuckGoSource(ImageSource):
    """DuckDuckGo image source (no API key required)"""

    def search(self, query, max_results=10, category=None):
        """Search DuckDuckGo for images"""
        try:
            # Add a delay to avoid rate limiting
            time.sleep(1)

            # Build search query with optional category and negative keywords
            search_query = query

            # Add negative keywords to filter out gaming content (common issue with search results)
            negative_keywords = ['game', 'gaming', 'video game', 'league', 'valorant', 'fortnite']
            search_query = f"{query} -{' -'.join(negative_keywords)}"

            # Add category to query if specified
            if category:
                search_query = f"{search_query} {category}"

            with DDGS() as ddgs:
                results = list(ddgs.images(
                    keywords=search_query,
                    max_results=max_results * 2  # Fetch extra in case some fail to download
                ))

            images = []
            for r in results[:max_results * 2]:
                images.append({
                    'url': r['image'],
                    'thumbnail': r.get('thumbnail', r['image']),
                    'source': 'duckduckgo',
                    'photographer': 'Unknown',
                    'title': r.get('title', 'Unknown')
                })

            return images[:max_results * 2]

        except Exception as e:
            # Log full error for debugging
            import logging
            logging.error(f"DuckDuckGo error: {str(e)}")
            print(f"  DuckDuckGo error: {str(e)[:80]}...")
            return []


class ImageSourceManager:
    """Manage multiple image sources and aggregate results"""

    def __init__(self, config):
        self.sources = {}

        # Initialize available sources
        pexels_key = config.get_api_key('pexels')
        if pexels_key:
            self.sources['pexels'] = PexelsSource(pexels_key)

        pixabay_key = config.get_api_key('pixabay')
        if pixabay_key:
            self.sources['pixabay'] = PixabaySource(pixabay_key)

        # DuckDuckGo always available
        self.sources['duckduckgo'] = DuckDuckGoSource()

    def search(self, query, max_results=10, sources='all', category=None):
        """
        Search for images across specified sources

        Args:
            query: Search query
            max_results: Total number of images to return
            sources: 'all', list of source names, or single source name
            category: Optional category filter

        Returns:
            List of image dictionaries
        """
        if sources == 'all':
            active_sources = list(self.sources.keys())
        elif isinstance(sources, list):
            active_sources = [s for s in sources if s in self.sources]
        elif sources in self.sources:
            active_sources = [sources]
        else:
            active_sources = ['duckduckgo']  # fallback

        if not active_sources:
            print("✗ No valid image sources available!")
            return []

        print(f"🔍 Searching {', '.join(active_sources)} for '{query}' images...")

        all_images = []
        per_source = max(1, max_results // len(active_sources))

        for source_name in active_sources:
            source = self.sources[source_name]
            print(f"  → {source_name.capitalize()}...")
            images = source.search(query, per_source * 2, category)
            all_images.extend(images)

        print(f"✓ Found {len(all_images)} potential images")
        return all_images[:max_results * 2]  # Return extra in case some fail to download

    def get_available_sources(self):
        """Get list of available source names"""
        return list(self.sources.keys())
