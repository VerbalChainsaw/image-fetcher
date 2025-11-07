#!/usr/bin/env python3
"""
Configuration management for Image Fetcher
"""

import os
from pathlib import Path
import json

# Fix Windows encoding issues
try:
    from utils import setup_windows_encoding, safe_print
    setup_windows_encoding()
except ImportError:
    safe_print = print

# Size presets for common use cases
SIZE_PRESETS = {
    '4k': (3840, 2160),
    'uhd': (3840, 2160),
    'fhd': (1920, 1080),
    'hd': (1280, 720),
    'mobile': (1080, 1920),
    'square': (1080, 1080),
    'instagram': (1080, 1080),
    'youtube': (1920, 1080),
    'tiktok': (1080, 1920)
}

class Config:
    """Manage configuration and API keys"""

    def __init__(self):
        self.config_file = Path.home() / '.image_fetcher_config.json'
        self.config = self.load_config()

    @staticmethod
    def get_size_preset(preset_name):
        """Get size from preset name"""
        return SIZE_PRESETS.get(preset_name.lower())

    def load_config(self):
        """Load configuration from file or environment variables"""
        config = {
            'pexels_api_key': '',
            'pixabay_api_key': '',
            'default_source': 'all',  # 'all', 'pexels', 'pixabay', 'duckduckgo'
            'default_size': [1920, 1080],
            'default_category': None,
            'output_dir': 'image_collections',
            'min_resolution': [800, 600],  # Minimum image resolution
            'max_retries': 3,  # Maximum retry attempts for downloads
            'timeout': 10,  # Request timeout in seconds
            'jpeg_quality': 95  # JPEG quality for saved images
        }

        # Try to load from file
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    config.update(saved_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")

        # Override with environment variables if present
        if os.getenv('PEXELS_API_KEY'):
            config['pexels_api_key'] = os.getenv('PEXELS_API_KEY')
        if os.getenv('PIXABAY_API_KEY'):
            config['pixabay_api_key'] = os.getenv('PIXABAY_API_KEY')

        return config

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
            return False

    def set_api_key(self, service, api_key):
        """Set API key for a service"""
        if service.lower() == 'pexels':
            self.config['pexels_api_key'] = api_key
        elif service.lower() == 'pixabay':
            self.config['pixabay_api_key'] = api_key
        else:
            return False
        return self.save_config()

    def get_api_key(self, service):
        """Get API key for a service"""
        return self.config.get(f'{service.lower()}_api_key', '')

    def validate_api_key(self, service, api_key):
        """Validate an API key by making a test request"""
        if not api_key:
            return False

        import requests

        try:
            if service.lower() == 'pexels':
                response = requests.get(
                    'https://api.pexels.com/v1/search?query=test&per_page=1',
                    headers={'Authorization': api_key},
                    timeout=5
                )
                return response.status_code == 200

            elif service.lower() == 'pixabay':
                response = requests.get(
                    'https://pixabay.com/api/',
                    params={'key': api_key, 'q': 'test', 'per_page': 3},
                    timeout=5
                )
                return response.status_code == 200 and 'hits' in response.json()

        except Exception:
            return False

        return False

    def setup_wizard(self):
        """Interactive setup wizard for API keys"""
        print("\n" + "="*60)
        print("Image Fetcher - Configuration Setup")
        print("="*60)
        print("\nEnter your API keys (press Enter to skip):\n")

        print("1. Pexels API Key")
        print("   Get it free at: https://www.pexels.com/api/")
        pexels_key = input("   API Key: ").strip()
        if pexels_key:
            print("   Validating API key...", end=" ")
            if self.validate_api_key('pexels', pexels_key):
                safe_print("✓ Valid!")
                self.config['pexels_api_key'] = pexels_key
            else:
                print("✗ Invalid key - not saved")

        print("\n2. Pixabay API Key")
        print("   Get it free at: https://pixabay.com/api/docs/")
        pixabay_key = input("   API Key: ").strip()
        if pixabay_key:
            print("   Validating API key...", end=" ")
            if self.validate_api_key('pixabay', pixabay_key):
                safe_print("✓ Valid!")
                self.config['pixabay_api_key'] = pixabay_key
            else:
                print("✗ Invalid key - not saved")

        if pexels_key or pixabay_key:
            if self.save_config():
                safe_print(f"\n✓ Configuration saved to: {self.config_file}")
            else:
                print("\n✗ Could not save configuration")

        # Show available size presets
        print("\n3. Available Size Presets:")
        for name, size in SIZE_PRESETS.items():
            print(f"   {name:12s} - {size[0]}x{size[1]}")

        print("\n   Use with: --size 4k or --size fhd")

        print("\nNote: DuckDuckGo doesn't require an API key.")
        print("="*60 + "\n")
