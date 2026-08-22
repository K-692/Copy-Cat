"""
Keystroke and Mouse Listener Module for Copy Cat.
Hooks keyboard and mouse events across macOS, Windows, and Linux via pynput.
Writes characters directly into memory.txt, prepends [DD-MM-YYYY HH:MM:SS] timestamps
on startup and after 10-second pauses, handles continuous typing 5-second backspace erasure,
manages mouse click / other key interruption behavior, and detects the 3x modifier hotkey trigger.
"""

import collections
import logging
import time
from typing import Callable, Optional
from pynput import keyboard, mouse

from copy_cat.config import (
    PAUSE_THRESHOLD_SECONDS,
    BACKSPACE_TIMEOUT_SECONDS,
    HOTKEY_PRESS_COUNT,
    HOTKEY_WINDOW_SECONDS,
    IS_MACOS,
)
from copy_cat.storage import FileIO

logger = logging.getLogger(__name__)


class KeystrokeListener:
    """
    Background listener that intercepts keyboard and mouse events.
    - Writes characters directly to memory.txt with [DD-MM-YYYY HH:MM:SS] timestamps.
    - Prepends a new timestamp header whenever the typing pause exceeds 10 seconds.
    - Erases letters from active line if typing continuously and Backspace is pressed within 5 seconds.
    - If a mouse click or other non-character key occurs before Backspace, inserts a newline in memory.txt,
      ignores the Backspace deletion, and resets for subsequent typing.
    - Intercepts 3x modifier key presses (Ctrl on macOS, Alt on Win/Linux) to trigger retrieval UI.
    """

    # Modifier keys that define shortcut combinations (Command, Control, Alt/Option)
    SHORTCUT_MODIFIERS = {
        getattr(keyboard.Key, name)
        for name in ("cmd", "cmd_l", "cmd_r", "ctrl", "ctrl_l", "ctrl_r", "alt", "alt_l", "alt_r", "alt_gr")
        if hasattr(keyboard.Key, name)
    }

    def __init__(
        self,
        file_io: Optional[FileIO] = None,
        on_hotkey_trigger: Optional[Callable[[], None]] = None,
        pause_threshold: float = PAUSE_THRESHOLD_SECONDS,
        backspace_timeout: float = BACKSPACE_TIMEOUT_SECONDS,
        hotkey_count: int = HOTKEY_PRESS_COUNT,
        hotkey_window: float = HOTKEY_WINDOW_SECONDS,
    ):
        """
        Initialize the listener with storage and callback hooks.
        """
        self.file_io = file_io or FileIO()
        self.on_hotkey_trigger = on_hotkey_trigger
        self.pause_threshold = pause_threshold
        self.backspace_timeout = backspace_timeout
        self.hotkey_count = hotkey_count
        self.hotkey_window = hotkey_window

        # State tracking for timing, line length, and interruption
        self.last_keystroke_time: float = 0.0
        self.current_line_chars: int = 0
        self.is_interrupted: bool = False

        # Hotkey tracking
        self.modifier_press_times = collections.deque(maxlen=self.hotkey_count)
        self._active_modifiers = set()  # Tracks currently held modifier keys

        # Listeners
        self.keyboard_listener: Optional[keyboard.Listener] = None
        self.mouse_listener: Optional[mouse.Listener] = None
        self._is_running = False

    def _is_modifier_key(self, key: keyboard.Key) -> bool:
        """
        Check if the pressed key matches the platform modifier key for the hotkey.
        macOS: Control key (ctrl / ctrl_l / ctrl_r)
        Windows/Linux: Alt key (alt / alt_l / alt_r / alt_gr) or Control
        """
        if IS_MACOS:
            return key in {
                getattr(keyboard.Key, name)
                for name in ("ctrl", "ctrl_l", "ctrl_r")
                if hasattr(keyboard.Key, name)
            }
        else:
            return key in {
                getattr(keyboard.Key, name)
                for name in ("alt", "alt_l", "alt_r", "alt_gr", "ctrl", "ctrl_l", "ctrl_r")
                if hasattr(keyboard.Key, name)
            }

    def _handle_modifier_press(self) -> None:
        """
        Record timestamp of modifier key press and trigger hotkey callback
        if pressed requisite number of times within the time window.
        """
        now = time.time()
        self.modifier_press_times.append(now)

        if len(self.modifier_press_times) == self.hotkey_count:
            oldest = self.modifier_press_times[0]
            newest = self.modifier_press_times[-1]
            if (newest - oldest) <= self.hotkey_window:
                logger.info("Global hotkey triggered (%d modifier presses in %.2fs)!", self.hotkey_count, newest - oldest)
                self.modifier_press_times.clear()
                if self.on_hotkey_trigger:
                    self.on_hotkey_trigger()

    def _is_valid_character(self, char: str) -> bool:
        """
        Check if a character is strictly a letter, number, symbol, or space.
        Rejects non-printable control characters, tabs, and escape sequences.

        Args:
            char: The character string to validate.

        Returns:
            bool: True if character is a printable letter, number, symbol, or space.
        """
        if not char or len(char) != 1:
            return False

        # Allow standard single space
        if char == " ":
            return True

        # Allow alphanumeric characters (letters and numbers)
        if char.isalnum():
            return True

        # Allow printable symbols and punctuation (ASCII and Unicode symbols)
        if char.isprintable() and not char.isspace():
            return True

        return False

    def _on_mouse_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        """
        Callback executed when a mouse button is pressed or released.
        A mouse click interrupts continuous typing mode.
        """
        # Do not track mouse events if UI popup is currently active
        if self.file_io.is_ui_active():
            return

        if pressed:
            self.is_interrupted = True
            logger.debug("Mouse click registered at (%d, %d). State set to interrupted.", x, y)

    def _on_key_release(self, key: keyboard.Key) -> None:
        """
        Callback executed whenever a key is released.
        Removes released modifier keys from the active modifiers set.
        """
        try:
            if key in self.SHORTCUT_MODIFIERS:
                self._active_modifiers.discard(key)
        except Exception as e:
            logger.error("Error in keystroke listener release handler: %s", e)

    # Explicit navigation and control keys (arrows, home/end, page up/down, tab, etc.)
    NAVIGATION_KEYS = {
        getattr(keyboard.Key, name)
        for name in (
            "up", "down", "left", "right",
            "page_up", "page_down", "home", "end",
            "tab", "insert", "delete"
        )
        if hasattr(keyboard.Key, name)
    }

    def _on_key_press(self, key: keyboard.Key) -> None:
        """
        Callback executed whenever a key is pressed.
        - Checks for shortcut modifiers and multi-press hotkey.
        - Suspends recording completely while UI popup is open.
        - Prepends [DD-MM-YYYY HH:MM:SS] timestamp on first keystroke or > 10s inactivity.
        - Writes characters directly to memory.txt.
        - Handles 5-second continuous typing Backspace character erasure.
        - Handles navigation key / mouse click interruption before Backspace to create a newline.
        """
        try:
            # If UI popup is currently open and active, suspend all keystroke recording
            if self.file_io.is_ui_active():
                return

            now = time.time()

            # 1. Track shortcut modifier keys (Command, Control, Alt)
            if key in self.SHORTCUT_MODIFIERS:
                self._active_modifiers.add(key)
                if self._is_modifier_key(key):
                    self._handle_modifier_press()
                # Modifier press flags session as interrupted
                self.is_interrupted = True
                return

            # 2. Reject key stroke if any shortcut modifier is held (e.g. Cmd+C, Cmd+V, Ctrl+Z, Alt+Tab)
            if self._active_modifiers:
                self.is_interrupted = True
                return

            # 3. Check for Navigation Keys or other special non-character keys (arrows, page up/down, home/end, tab, etc.)
            if key in self.NAVIGATION_KEYS or (
                isinstance(key, keyboard.Key)
                and key not in (keyboard.Key.space, keyboard.Key.enter, keyboard.Key.backspace)
            ):
                self.is_interrupted = True
                logger.debug("Navigation / special key pressed: %s. Interruption flag set.", key)
                return

            # 4. Handle Enter key
            if key == keyboard.Key.enter:
                # If gap > 10 seconds or initial startup, prepend timestamp header
                if self.last_keystroke_time == 0.0 or (now - self.last_keystroke_time) > self.pause_threshold:
                    self.file_io.append_timestamp_header()
                else:
                    self.file_io.append_newline()

                self.last_keystroke_time = now
                self.current_line_chars = 0
                self.is_interrupted = False
                return

            # 5. Handle Backspace key
            if key == keyboard.Key.backspace:
                elapsed = now - self.last_keystroke_time if self.last_keystroke_time > 0 else 999.0

                # Scenario A: Navigation key pressed or mouse clicked before pressing backspace
                # Requirement: In memory.txt, the cursor should go to the newline, ignore backspace deletion
                if self.is_interrupted:
                    logger.debug("Backspace pressed after navigation/interruption -> appending newline in memory.txt.")
                    self.file_io.append_newline()
                    self.is_interrupted = False
                    self.current_line_chars = 0
                    self.last_keystroke_time = now
                    return

                # Scenario B: Continuous typing within 5 seconds without interruption
                # Requirement: Erase character from active line in memory.txt
                if elapsed <= self.backspace_timeout and self.current_line_chars > 0:
                    erased = self.file_io.erase_last_char_from_line()
                    if erased:
                        self.current_line_chars = max(0, self.current_line_chars - 1)
                        logger.debug("Erased 1 character from active line in memory.txt (remaining on line: %d).", self.current_line_chars)
                    self.last_keystroke_time = now
                    return

                # Scenario C: Inactivity gap > 5 seconds or no characters on active line
                return

            # 6. Extract printable character (Letters, Numbers, Symbols, Space)
            char_to_record: Optional[str] = None
            if key == keyboard.Key.space:
                char_to_record = " "
            elif hasattr(key, "char") and key.char is not None:
                if self._is_valid_character(key.char):
                    char_to_record = key.char

            # If not a valid printable character, mark as interrupted and ignore
            if char_to_record is None:
                self.is_interrupted = True
                return

            # 7. Check 10-Second Pause Gap & Initial Startup:
            # Timestamps must come from the first keystroke itself and on > 10s inactivity.
            is_new_timestamp_block = (
                self.last_keystroke_time == 0.0
                or (now - self.last_keystroke_time) > self.pause_threshold
            )

            if is_new_timestamp_block:
                logger.debug("First keystroke or > 10s gap detected. Prepending timestamp header to memory.txt.")
                self.file_io.append_timestamp_header()
                self.current_line_chars = 0

            # 8. Append character directly to memory.txt
            self.file_io.append_text(char_to_record)
            self.current_line_chars += len(char_to_record)
            self.last_keystroke_time = now
            self.is_interrupted = False

        except Exception as e:
            logger.error("Error in keystroke listener handler: %s", e)

    def start(self) -> None:
        """
        Start the keyboard and mouse listeners in background threads.
        """
        if self._is_running:
            return

        self._active_modifiers.clear()
        self.is_interrupted = False
        self.current_line_chars = 0

        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self.keyboard_listener.daemon = True
        self.keyboard_listener.start()

        # Start mouse listener for interruption detection
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
        )
        self.mouse_listener.daemon = True
        self.mouse_listener.start()

        self._is_running = True
        logger.info("Keystroke and mouse listeners started successfully.")

    def stop(self) -> None:
        """
        Stop both keyboard and mouse listeners cleanly.
        """
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None

        self._active_modifiers.clear()
        self._is_running = False
        logger.info("Keystroke and mouse listeners stopped.")
