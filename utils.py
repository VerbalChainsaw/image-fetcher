#!/usr/bin/env python3
"""
Utility functions for Image Fetcher
"""

import sys
import os


def setup_windows_encoding():
    """
    Fix Windows console encoding issues to support UTF-8 and emojis.
    Call this at the start of scripts that print Unicode characters.
    """
    if sys.platform == 'win32':
        try:
            # Try to set UTF-8 encoding for stdout and stderr
            import io
            if sys.stdout.encoding != 'utf-8':
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            if sys.stderr.encoding != 'utf-8':
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

            # Try to enable VT100 processing on Windows 10+
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except:
                pass
        except Exception:
            pass


def safe_print(*args, **kwargs):
    """
    Print with fallback for encoding errors.
    Replaces emojis with ASCII alternatives on Windows if needed.
    """
    emoji_replacements = {
        '✨': '*',
        '🎨': '[Design]',
        '📊': '[Stats]',
        '🖼️': '[Image]',
        '📚': '[Docs]',
        '⚙️': '[Config]',
        '📐': '[Size]',
        '🔍': '[Search]',
        '📱': '[Mobile]',
        '🎯': '[Target]',
        '✓': 'OK',
        '✅': '[OK]',
        '⬇️': 'v',
        '⚠️': '!',
        '💡': 'Tip:',
        '🔧': '[Tool]',
        '🚀': '>',
        '⏱️': '[Time]',
    }

    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: replace emojis with ASCII
        new_args = []
        for arg in args:
            if isinstance(arg, str):
                for emoji, replacement in emoji_replacements.items():
                    arg = arg.replace(emoji, replacement)
            new_args.append(arg)
        print(*new_args, **kwargs)


# Initialize encoding on import for Windows
setup_windows_encoding()
