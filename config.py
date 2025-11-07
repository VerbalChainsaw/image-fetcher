#!/usr/bin/env python3
"""
Configuration management for Image Fetcher
"""

import os
from pathlib import Path
import json

class Config:
    """Manage configuration and API keys"""

    def __init__(self):
        self.config_file = Path.home() / '.image_fetcher_config.json'
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from file or environment variables"""
        config = {
            'pexels_api_key': '',
            'pixabay_api_key': '',
            'default_source': 'all',  # 'all', 'pexels', 'pixabay', 'duckduckgo'
            'default_size': [1920, 1080],
            'default_category': None,
            'output_dir': 'image_collections'
        }

        # Try to load from file
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    config.update(saved_config)
            except Exception:
                pass

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
            self.config['pexels_api_key'] = pexels_key

        print("\n2. Pixabay API Key")
        print("   Get it free at: https://pixabay.com/api/docs/")
        pixabay_key = input("   API Key: ").strip()
        if pixabay_key:
            self.config['pixabay_api_key'] = pixabay_key

        if pexels_key or pixabay_key:
            if self.save_config():
                print(f"\n✓ Configuration saved to: {self.config_file}")
            else:
                print("\n✗ Could not save configuration")

        print("\nNote: DuckDuckGo doesn't require an API key.")
        print("="*60 + "\n")
