"""
Configuration Module for Copy Cat Application.
Contains all path constants, timing thresholds, and cross-platform settings for
macOS, Windows, and Linux.
"""

import sys
from pathlib import Path

# Base project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data file path (timer.txt is eliminated; memory.txt is self-contained with timestamps)
MEMORY_FILE = BASE_DIR / "memory.txt"

# Flag file indicating whether the UI popup is currently active
UI_ACTIVE_FLAG_FILE = BASE_DIR / ".ui_active"


# Timing and interval configurations (in seconds)
PAUSE_THRESHOLD_SECONDS = 10.0          # Inactivity period that triggers a new timestamped paragraph (10 seconds)
BACKSPACE_TIMEOUT_SECONDS = 5.0         # Maximum continuous typing interval allowed for backspace deletion (5 seconds)
MEMORY_WIPE_INTERVAL_SECONDS = 259200.0 # Interval to completely erase memory.txt (3 days = 72 hours)

# Global Hotkey configuration
HOTKEY_PRESS_COUNT = 3                  # Number of consecutive modifier presses required to open UI
HOTKEY_WINDOW_SECONDS = 1.5             # Time window (seconds) to register consecutive modifier presses

# Platform detection flags
IS_MACOS = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")

# Assets and Branding
LOGO_PATH = BASE_DIR / "logo.png"

# UI Popup Geometry & Positioning (Compact & Space-Optimized)
POPUP_DEFAULT_WIDTH = 460                # Default compact window width in pixels
POPUP_DEFAULT_HEIGHT = 270               # Default compact window height in pixels
POPUP_MIN_WIDTH = 360                    # Minimum allowable window width
POPUP_MIN_HEIGHT = 200                   # Minimum allowable window height
POPUP_MARGIN_LEFT = 16                   # Screen margin from left edge (pixels)
POPUP_MARGIN_BOTTOM = 36                 # Screen margin above bottom edge (pixels)

# Cross-platform font family mappings for Tkinter UI
if IS_MACOS:
    FONT_FAMILY_PRIMARY = "Helvetica"
    FONT_FAMILY_MONO = "Menlo"
elif IS_WINDOWS:
    FONT_FAMILY_PRIMARY = "Segoe UI"
    FONT_FAMILY_MONO = "Consolas"
else:  # Linux / X11 / Wayland
    FONT_FAMILY_PRIMARY = "DejaVu Sans"
    FONT_FAMILY_MONO = "Monospace"

