"""
Configuration management for the video fetcher application.
Handles API keys, default settings, and user preferences.
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional


class VideoConfig:
    """Configuration manager for video fetcher."""

    CONFIG_FILE = Path.home() / ".video_fetcher_config.json"

    DEFAULT_CONFIG = {
        "pexels_api_key": None,
        "pixabay_api_key": None,
        "default_source": "all",
        "default_quality": "hd",  # hd, medium, or high
        "default_orientation": None,  # landscape, portrait, square, or None
        "default_category": None,
        "output_dir": "video_collections",
        "min_duration": None,  # Minimum video duration in seconds
        "max_duration": None,  # Maximum video duration in seconds
        "min_width": 1280,  # Minimum video width (720p minimum)
        "min_height": 720,
        "max_file_size_mb": 100,  # Maximum file size in MB
        "parallel_downloads": 3,  # Number of simultaneous downloads
        "theme": "dark"  # UI theme: dark or light
    }

    @classmethod
    def load_config(cls) -> Dict:
        """
        Load configuration from file and environment variables.

        Priority:
        1. Environment variables (highest)
        2. Config file
        3. Defaults (lowest)
        """
        config = cls.DEFAULT_CONFIG.copy()

        # Load from file if it exists
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")

        # Override with environment variables
        env_keys = {
            "PEXELS_VIDEO_API_KEY": "pexels_api_key",
            "PIXABAY_VIDEO_API_KEY": "pixabay_api_key",
            "PEXELS_API_KEY": "pexels_api_key",  # Fallback to image API key
            "PIXABAY_API_KEY": "pixabay_api_key"  # Fallback to image API key
        }

        for env_var, config_key in env_keys.items():
            value = os.getenv(env_var)
            if value:
                config[config_key] = value

        return config

    @classmethod
    def save_config(cls, config: Dict) -> None:
        """Save configuration to file."""
        try:
            # Create parent directory if it doesn't exist
            cls.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Save to file
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)

            print(f"Configuration saved to {cls.CONFIG_FILE}")

        except Exception as e:
            print(f"Error saving config: {e}")

    @classmethod
    def set_api_key(cls, service: str, api_key: str) -> None:
        """Set an API key for a specific service and save."""
        config = cls.load_config()
        config[f"{service}_api_key"] = api_key
        cls.save_config(config)

    @classmethod
    def get_api_key(cls, service: str) -> Optional[str]:
        """Get API key for a specific service."""
        config = cls.load_config()
        return config.get(f"{service}_api_key")

    @classmethod
    def setup_wizard(cls) -> None:
        """Interactive setup wizard for configuration."""
        print("\n=== Video Fetcher Configuration Setup ===\n")

        config = cls.load_config()

        # Pexels API Key
        print("Pexels Video API (https://www.pexels.com/api/)")
        current = config.get("pexels_api_key", "")
        if current:
            print(f"Current key: {current[:10]}...{current[-4:]}")
        pexels_key = input("Enter Pexels API key (or press Enter to skip): ").strip()
        if pexels_key:
            config["pexels_api_key"] = pexels_key

        # Pixabay API Key
        print("\nPixabay Video API (https://pixabay.com/api/docs/)")
        current = config.get("pixabay_api_key", "")
        if current:
            print(f"Current key: {current[:10]}...{current[-4:]}")
        pixabay_key = input("Enter Pixabay API key (or press Enter to skip): ").strip()
        if pixabay_key:
            config["pixabay_api_key"] = pixabay_key

        # Default quality
        print("\nDefault video quality:")
        print("  1. HD (1920x1080 or higher)")
        print("  2. Medium (1280x720)")
        print("  3. High (best available)")
        quality_choice = input(f"Enter choice [1-3] (current: {config['default_quality']}): ").strip()
        quality_map = {"1": "hd", "2": "medium", "3": "high"}
        if quality_choice in quality_map:
            config["default_quality"] = quality_map[quality_choice]

        # Output directory
        print(f"\nCurrent output directory: {config['output_dir']}")
        output_dir = input("Enter output directory (or press Enter to keep current): ").strip()
        if output_dir:
            config["output_dir"] = output_dir

        # Min/Max duration
        print("\nVideo duration filters (in seconds):")
        min_dur = input(f"Minimum duration (current: {config['min_duration']} or None): ").strip()
        if min_dur:
            try:
                config["min_duration"] = int(min_dur)
            except ValueError:
                print("Invalid duration, keeping current value")

        max_dur = input(f"Maximum duration (current: {config['max_duration']} or None): ").strip()
        if max_dur:
            try:
                config["max_duration"] = int(max_dur)
            except ValueError:
                print("Invalid duration, keeping current value")

        # Parallel downloads
        parallel = input(f"\nParallel downloads (1-10, current: {config['parallel_downloads']}): ").strip()
        if parallel:
            try:
                p = int(parallel)
                if 1 <= p <= 10:
                    config["parallel_downloads"] = p
                else:
                    print("Must be between 1-10, keeping current value")
            except ValueError:
                print("Invalid number, keeping current value")

        # Theme
        print(f"\nUI Theme (current: {config['theme']})")
        theme = input("Enter 'dark' or 'light': ").strip().lower()
        if theme in ["dark", "light"]:
            config["theme"] = theme

        # Save configuration
        cls.save_config(config)
        print("\n✓ Configuration saved successfully!\n")

    @classmethod
    def get_quality_params(cls, quality: str) -> Dict:
        """
        Get video quality parameters based on quality setting.

        Args:
            quality: 'hd', 'medium', or 'high'

        Returns:
            Dictionary with min_width and min_height
        """
        quality_settings = {
            "hd": {"min_width": 1920, "min_height": 1080},
            "medium": {"min_width": 1280, "min_height": 720},
            "high": {"min_width": 1920, "min_height": 1080}
        }

        return quality_settings.get(quality, quality_settings["hd"])
