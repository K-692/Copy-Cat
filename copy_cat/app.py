"""
Main Application Coordinator for Copy Cat.
Integrates storage, keystroke and mouse listener, 3-day maintenance scheduler, and UI popup.
Fully compatible with macOS, Windows, and Linux.
"""

import logging
import signal
import subprocess
import sys
import threading
import time
from typing import Optional

from copy_cat.config import BASE_DIR, IS_MACOS
from copy_cat.listener import KeystrokeListener
from copy_cat.scheduler import TaskScheduler
from copy_cat.storage import FileIO

logger = logging.getLogger(__name__)


class CopyCatApp:
    """
    Core Application Coordinator.
    Manages background keystroke listener, periodic 3-day memory maintenance, and UI popup subprocesses.
    """

    def __init__(self):
        """
        Initialize the Copy Cat application with storage, listener, and scheduler.
        """
        self.file_io = FileIO()
        self.scheduler = TaskScheduler(file_io=self.file_io)
        self.listener = KeystrokeListener(
            file_io=self.file_io,
            on_hotkey_trigger=self._on_hotkey_pressed,
        )
        self._popup_proc: Optional[subprocess.Popen] = None
        self._is_running = False

    def _on_hotkey_pressed(self) -> None:
        """
        Invoked by KeystrokeListener when the modifier key is pressed 3 times.
        Spawns the UI retrieval popup as an isolated subprocess so that Tkinter / Cocoa
        runs safely on its own main thread without causing threading crashes.
        Suspends background keystroke listening while the UI popup is active.
        """
        logger.info("HotKey detected! Spawning Quick Retrieval popup subprocess...")
        try:
            # Prevent opening multiple overlapping popup windows if one is already active
            if self._popup_proc is not None and self._popup_proc.poll() is None:
                logger.info("Popup is already open on screen.")
                return

            self.file_io.set_ui_active(True)
            cmd = [sys.executable, str(BASE_DIR / "main.py"), "--popup"]
            self._popup_proc = subprocess.Popen(
                cmd,
                cwd=str(BASE_DIR),
            )
            logger.info("Spawned popup process (PID: %d)", self._popup_proc.pid)

            # Spawn a thread to monitor when popup exits and reset UI active flag
            def _watch_popup(proc: subprocess.Popen):
                try:
                    proc.wait()
                except Exception:
                    pass
                finally:
                    self.file_io.set_ui_active(False)
                    logger.info("Popup process closed. Background listener resumed.")

            threading.Thread(target=_watch_popup, args=(self._popup_proc,), daemon=True).start()

        except Exception as e:
            self.file_io.set_ui_active(False)
            logger.error("Failed to spawn popup UI subprocess: %s", e)

    def start(self) -> None:
        """
        Start the background listener and scheduler.
        Enters a blocking wait loop until interrupted.
        """
        logger.info("=" * 60)
        logger.info("🐱 Starting Copy Cat Application")
        logger.info("• Modifier Hotkey: Press %s 3 times rapidly (within 1.5s)", "Ctrl" if IS_MACOS else "Alt")
        logger.info("• Direct Storage: Keystrokes written directly to memory.txt")
        logger.info("• Timestamps: Prepends [DD-MM-YYYY HH:MM:SS] on start and > 10s pauses")
        logger.info("• Backspace Erasure: Continuous typing within 5s erases active line characters")
        logger.info("• Interrupt Handling: Mouse click/other keys before backspace creates newline")
        logger.info("• Memory Maintenance: Complete wipe every 3 days (self-contained)")
        logger.info("=" * 60)

        self._is_running = True

        # Register signal handlers for clean exit
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        # Start background components
        self.listener.start()
        self.scheduler.start()

        # Keep main thread alive
        try:
            while self._is_running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            logger.info("Received KeyboardInterrupt.")
        finally:
            self.stop()

    def stop(self) -> None:
        """
        Stop all running services cleanly.
        """
        if not self._is_running:
            return

        logger.info("Stopping Copy Cat application...")
        self._is_running = False
        if self._popup_proc is not None and self._popup_proc.poll() is None:
            try:
                self._popup_proc.terminate()
            except Exception:
                pass
        self.listener.stop()
        self.scheduler.stop()
        logger.info("Copy Cat stopped cleanly.")

    def _handle_signal(self, signum, frame):
        """
        Signal handler for SIGINT/SIGTERM.
        """
        logger.info("Caught signal %s. Shutting down...", signum)
        self.stop()
        sys.exit(0)
