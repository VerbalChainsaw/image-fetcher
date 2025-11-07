#!/usr/bin/env python3
"""
Comprehensive test suite for Image Fetcher
Tests all components to ensure everything works correctly
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules import correctly"""
    print("=" * 60)
    print("Testing Module Imports")
    print("=" * 60)

    try:
        from config import Config, SIZE_PRESETS
        print("✓ config.py imports successfully")
        print(f"  - {len(SIZE_PRESETS)} size presets available")
    except Exception as e:
        print(f"✗ config.py failed: {e}")
        return False

    try:
        from image_sources import (ImageSource, PexelsSource,
                                   PixabaySource, DuckDuckGoSource,
                                   ImageSourceManager)
        print("✓ image_sources.py imports successfully")
    except Exception as e:
        print(f"✗ image_sources.py failed: {e}")
        return False

    try:
        from image_fetcher import ImageFetcher
        print("✓ image_fetcher.py imports successfully")
    except Exception as e:
        print(f"✗ image_fetcher.py failed: {e}")
        return False

    try:
        from flask import Flask
        print("✓ Flask imports successfully")
    except Exception as e:
        print(f"✗ Flask failed: {e}")
        return False

    try:
        import tqdm
        print("✓ tqdm imports successfully")
    except Exception as e:
        print("⚠ tqdm not available (progress bars disabled)")

    return True


def test_config():
    """Test configuration system"""
    print("\n" + "=" * 60)
    print("Testing Configuration")
    print("=" * 60)

    try:
        from config import Config, SIZE_PRESETS

        config = Config()
        print(f"✓ Config initialized with {len(config.config)} settings")

        # Test size presets
        test_preset = Config.get_size_preset('4k')
        assert test_preset == (3840, 2160), "4K preset incorrect"
        print(f"✓ Size presets working (tested '4k': {test_preset})")

        # Test API keys (should be empty if not configured)
        pexels_key = config.get_api_key('pexels')
        pixabay_key = config.get_api_key('pixabay')

        if pexels_key:
            print(f"✓ Pexels API key configured")
        else:
            print("⚠ Pexels API key not configured (using DuckDuckGo only)")

        if pixabay_key:
            print(f"✓ Pixabay API key configured")
        else:
            print("⚠ Pixabay API key not configured (using DuckDuckGo only)")

        return True

    except Exception as e:
        print(f"✗ Config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_image_sources():
    """Test image source providers"""
    print("\n" + "=" * 60)
    print("Testing Image Sources")
    print("=" * 60)

    try:
        from config import Config
        from image_sources import ImageSourceManager

        config = Config()
        manager = ImageSourceManager(config)

        sources = manager.get_available_sources()
        print(f"✓ Available sources: {', '.join(sources)}")

        if 'pexels' not in sources and 'pixabay' not in sources:
            print("⚠ Only DuckDuckGo available (no API keys configured)")
            print("  Run 'python image_fetcher.py --setup' to add API keys")

        return True

    except Exception as e:
        print(f"✗ Image sources test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_image_fetcher():
    """Test ImageFetcher initialization"""
    print("\n" + "=" * 60)
    print("Testing Image Fetcher")
    print("=" * 60)

    try:
        from config import Config
        from image_fetcher import ImageFetcher

        config = Config()

        # Test with default size
        fetcher = ImageFetcher(config)
        print(f"✓ ImageFetcher initialized (default size: {fetcher.target_size})")

        # Test with custom size
        fetcher_4k = ImageFetcher(config, target_size=(3840, 2160))
        print(f"✓ ImageFetcher with custom size: {fetcher_4k.target_size}")

        return True

    except Exception as e:
        print(f"✗ ImageFetcher test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_web_app():
    """Test web application"""
    print("\n" + "=" * 60)
    print("Testing Web Application")
    print("=" * 60)

    try:
        from web_app import app

        print("✓ Web app imports successfully")

        # Check routes
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        print(f"✓ {len(routes)} routes registered:")
        for route in sorted(routes):
            if not route.startswith('/static'):
                print(f"  - {route}")

        return True

    except Exception as e:
        print(f"✗ Web app test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print(" " * 20 + "IMAGE FETCHER TEST SUITE")
    print("=" * 70 + "\n")

    results = {
        'Imports': test_imports(),
        'Configuration': test_config(),
        'Image Sources': test_image_sources(),
        'Image Fetcher': test_image_fetcher(),
        'Web Application': test_web_app()
    }

    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:20s} {status}")

    total = len(results)
    passed = sum(results.values())

    print("\n" + "=" * 70)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
        print("\nQuick Start:")
        print("  - Web Interface: python web_app.py")
        print("  - CLI: python image_fetcher.py 'sunset' 10 --size 4k")
        print("  - Interactive: python image_fetcher.py -i")
    else:
        print("⚠ Some tests failed. Please review errors above.")

    print("=" * 70 + "\n")

    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
