"""
Task Scheduler Module for Copy Cat.
Handles periodic background maintenance for memory.txt, performing rolling
granular pruning of only those blocks older than 3 days while keeping fresh entries.
Completely standalone without timer.txt.
"""

import logging
import threading
from typing import Optional

from copy_cat.config import MEMORY_WIPE_INTERVAL_SECONDS
from copy_cat.storage import FileIO

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Manages periodic background maintenance tasks:
    - Periodically prunes expired blocks (older than 3 days) from memory.txt.
    - Preserves all valid content until their individual 3-day expiration time arrives.
    - Runs catch-up pruning on application startup.
    """

    def __init__(
        self,
        file_io: Optional[FileIO] = None,
        memory_wipe_interval: float = MEMORY_WIPE_INTERVAL_SECONDS,
    ):
        """
        Initialize scheduler with storage manager and memory wipe interval.
        
        Args:
            file_io: Storage manager instance.
            memory_wipe_interval: Interval in seconds after which individual blocks expire (default: 3 days = 259200s).
        """
        self.file_io = file_io or FileIO()
        self.memory_wipe_interval = memory_wipe_interval
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def perform_memory_wipe_if_due(self, force: bool = False) -> bool:
        """
        Perform selective rolling pruning of memory blocks older than 3 days,
        or completely wipe memory if force=True.
        
        Args:
            force: If True, completely clear memory.txt.
            
        Returns:
            bool: True if any expired content was pruned or cleared, False otherwise.
        """
        if force:
            logger.info("Force clearing all contents from memory.txt...")
            self.file_io.clear_memory()
            return True

        pruned = self.file_io.prune_expired_memory(self.memory_wipe_interval)
        if pruned > 0:
            logger.info("Pruned %d expired block(s) (older than 3 days) from memory.txt.", pruned)
            return True
        return False

    def check_startup_tasks(self) -> None:
        """
        Inspect memory.txt timestamps on application startup.
        Removes any expired blocks older than 3 days, keeping remaining valid entries.
        """
        logger.info("Checking startup maintenance on memory.txt...")
        pruned = self.file_io.prune_expired_memory(self.memory_wipe_interval)
        if pruned > 0:
            logger.info("Startup check: Pruned %d expired block(s) older than 3 days.", pruned)
        else:
            logger.info("Startup check: All memory.txt contents are valid (within 3-day window).")

    def _loop(self) -> None:
        """
        Main scheduler loop running in a background daemon thread.
        Checks and prunes expired blocks periodically every 60 seconds.
        """
        logger.info("Maintenance scheduler loop started.")
        while not self._stop_event.is_set():
            if self._stop_event.wait(60.0):
                break

            # Perform selective 3-day expiration pruning
            self.perform_memory_wipe_if_due()

        logger.info("Maintenance scheduler loop terminated.")

    def start(self) -> None:
        """
        Start the background maintenance scheduler thread after running startup checks.
        """
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self.check_startup_tasks()

        self._thread = threading.Thread(target=self._loop, daemon=True, name="CopyCatScheduler")
        self._thread.start()
        logger.info("Background 3-day selective maintenance scheduler started.")

    def stop(self) -> None:
        """
        Signal the scheduler thread to stop and wait for clean termination.
        """
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Background maintenance scheduler stopped.")
