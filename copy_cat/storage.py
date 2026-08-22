"""
Storage Module for Copy Cat Application.
Provides thread-safe and process-safe file operations for memory.txt across
macOS, Windows, and Linux using file locks, [DD-MM-YYYY HH:MM:SS] timestamp headers,
line-bound character erasure, and rolling granular 3-day timestamp pruning.
"""

import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from filelock import FileLock

from copy_cat.config import MEMORY_FILE, MEMORY_WIPE_INTERVAL_SECONDS


class FileIO:
    """
    Thread-safe and process-safe File I/O manager using filelock.
    Handles appending keystroke characters directly to memory.txt with
    [DD-MM-YYYY HH:MM:SS] timestamps, erasing characters on active lines,
    rolling 3-day selective memory pruning, and UI snippet extraction.
    """

    def __init__(
        self,
        memory_path: Path = MEMORY_FILE,
    ):
        """
        Initialize file path and lock object. Ensures memory.txt exists.
        
        Args:
            memory_path: Path to memory.txt storage file.
        """
        self.memory_path = Path(memory_path)

        # File lock for cross-thread and cross-process concurrency safety
        self.memory_lock = FileLock(str(self.memory_path) + ".lock", timeout=10)

        # Ensure storage file is initialized on disk
        self._initialize_files()

    def _initialize_files(self) -> None:
        """
        Create default empty memory file if it doesn't exist.
        """
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.memory_path.exists():
            with self.memory_lock:
                if not self.memory_path.exists():
                    self.memory_path.touch()

    # --- Direct Memory Operations ---

    def read_memory(self) -> str:
        """
        Safely read and return the complete contents of memory.txt.
        
        Returns:
            str: Full text content of memory.txt.
        """
        with self.memory_lock:
            if self.memory_path.exists():
                return self.memory_path.read_text(encoding="utf-8")
            return ""

    def write_memory(self, text: str) -> None:
        """
        Safely overwrite memory.txt with the given text under file lock.
        
        Args:
            text: Content to write into memory.txt.
        """
        with self.memory_lock:
            self.memory_path.write_text(text or "", encoding="utf-8")

    def append_text(self, text: str) -> None:
        """
        Safely append keystroke text directly to memory.txt.
        
        Args:
            text: Character or string to append.
        """
        if not text:
            return
        with self.memory_lock:
            with self.memory_path.open("a", encoding="utf-8") as f:
                f.write(text)

    def append_newline(self) -> None:
        """
        Safely append a single newline character to memory.txt.
        """
        with self.memory_lock:
            with self.memory_path.open("a", encoding="utf-8") as f:
                f.write("\n")

    def append_timestamp_header(self, custom_time: Optional[float] = None) -> str:
        """
        Safely append a [DD-MM-YYYY HH:MM:SS] timestamp header to memory.txt.
        If memory.txt already contains text, inserts double newlines (\\n\\n) before the header.
        
        Args:
            custom_time: Optional epoch timestamp to use instead of current time.
            
        Returns:
            str: The formatted timestamp header string that was appended.
        """
        target_time = custom_time if custom_time is not None else time.time()
        ts_str = time.strftime("[%d-%m-%Y %H:%M:%S]", time.localtime(target_time))
        header_payload = ""

        with self.memory_lock:
            if self.memory_path.exists() and self.memory_path.stat().st_size > 0:
                current_content = self.memory_path.read_text(encoding="utf-8")
                if current_content.endswith("\n\n"):
                    header_payload = f"{ts_str}\n"
                elif current_content.endswith("\n"):
                    header_payload = f"\n{ts_str}\n"
                else:
                    header_payload = f"\n\n{ts_str}\n"
            else:
                header_payload = f"{ts_str}\n"

            with self.memory_path.open("a", encoding="utf-8") as f:
                f.write(header_payload)

        return ts_str

    def erase_last_char_from_line(self) -> bool:
        """
        Safely erase the last character from the active line in memory.txt.
        Will NOT delete newline characters and will NOT erase into timestamp headers [DD-MM-YYYY HH:MM:SS].
        
        Returns:
            bool: True if a character was successfully erased, False if at line start or timestamp header.
        """
        with self.memory_lock:
            if not self.memory_path.exists():
                return False

            content = self.memory_path.read_text(encoding="utf-8")
            if not content:
                return False

            # Do not delete across newlines
            if content.endswith("\n"):
                return False

            # Check if the active line is a timestamp header: [DD-MM-YYYY HH:MM:SS]
            last_line = content.split("\n")[-1]
            if re.match(r"^\[\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}\]$", last_line.strip()):
                # Do not delete timestamp header characters
                return False

            # Remove the last character
            updated_content = content[:-1]
            self.memory_path.write_text(updated_content, encoding="utf-8")
            return True

    def clear_memory(self) -> None:
        """
        Safely truncate memory.txt to completely empty (used for manual wipe).
        """
        with self.memory_lock:
            self.memory_path.write_text("", encoding="utf-8")

    # --- Rolling 3-Day Selective Memory Pruning ---

    def prune_expired_memory(self, max_age_seconds: float = MEMORY_WIPE_INTERVAL_SECONDS) -> int:
        """
        Prune and remove ONLY those content blocks from memory.txt whose timestamp
        is older than max_age_seconds (3 days = 259200s), keeping all other valid contents
        intact until their respective 3-day validity expires.
        
        Args:
            max_age_seconds: Maximum validity duration in seconds (default: 3 days = 259200s).
            
        Returns:
            int: Number of expired blocks removed from memory.txt.
        """
        with self.memory_lock:
            if not self.memory_path.exists() or self.memory_path.stat().st_size == 0:
                return 0

            content = self.memory_path.read_text(encoding="utf-8")
            if not content.strip():
                return 0

            now = time.time()
            pattern = re.compile(r'(\[\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}\])')
            parts = pattern.split(content)

            valid_blocks: List[str] = []
            pruned_count = 0

            # Check if there is non-timestamped initial text
            if parts and not pattern.match(parts[0]):
                initial_text = parts[0].strip()
                if initial_text:
                    mtime = self.memory_path.stat().st_mtime
                    if (now - mtime) < max_age_seconds:
                        valid_blocks.append(initial_text)
                    else:
                        pruned_count += 1
                parts = parts[1:]

            # Iterate through timestamped blocks
            i = 0
            while i < len(parts):
                if pattern.match(parts[i]):
                    ts_header = parts[i]
                    body = parts[i + 1].strip() if (i + 1) < len(parts) else ""
                    
                    # Parse timestamp from header [DD-MM-YYYY HH:MM:SS]
                    is_expired = False
                    try:
                        ts_clean = ts_header.strip("[]")
                        dt = datetime.strptime(ts_clean, "%d-%m-%Y %H:%M:%S")
                        ts_epoch = dt.timestamp()
                        if (now - ts_epoch) >= max_age_seconds:
                            is_expired = True
                    except Exception:
                        is_expired = False

                    if is_expired:
                        pruned_count += 1
                    else:
                        block_text = f"{ts_header}\n{body}" if body else ts_header
                        valid_blocks.append(block_text)
                    i += 2
                else:
                    i += 1

            # Atomically write back remaining valid content if any expired blocks were pruned
            if pruned_count > 0:
                updated_content = "\n\n".join(valid_blocks) if valid_blocks else ""
                self.memory_path.write_text(updated_content, encoding="utf-8")

            return pruned_count

    # --- Snippet Extraction for UI ---

    def get_all_snippets(self) -> List[Dict[str, Any]]:
        """
        Parse memory.txt into structured timestamped paragraph snippets.
        Returns entries ordered from newest to oldest for intuitive UI display.
        
        Returns:
            List[Dict[str, Any]]: List of snippet objects containing 'timestamp', 'content', 'text', 'preview', etc.
        """
        content = self.read_memory()
        if not content or not content.strip():
            return []

        pattern = re.compile(r'(\[\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}\])')
        parts = pattern.split(content)

        snippets: List[Dict[str, Any]] = []

        # Handle non-timestamped initial text if present
        if parts and not pattern.match(parts[0]):
            text = parts[0].strip()
            if text:
                first_line = text.split("\n")[0].strip()
                preview = (first_line[:65] + "...") if len(first_line) > 65 else first_line
                snippets.append({
                    "timestamp": "",
                    "content": text,
                    "text": text,
                    "preview": preview,
                    "char_count": len(text),
                    "line_count": len(text.splitlines()),
                })
            parts = parts[1:]

        # Pair timestamp header matches with following body text
        i = 0
        while i < len(parts):
            if pattern.match(parts[i]):
                ts_header = parts[i]
                body = parts[i + 1].strip() if (i + 1) < len(parts) else ""
                if body:
                    full_text = f"{ts_header}\n{body}"
                    first_line = body.split("\n")[0].strip()
                    preview = f"{ts_header} {(first_line[:50] + '...') if len(first_line) > 50 else first_line}"
                    snippets.append({
                        "timestamp": ts_header,
                        "content": body,
                        "text": full_text,
                        "preview": preview,
                        "char_count": len(body),
                        "line_count": len(body.splitlines()),
                    })
                i += 2
            else:
                i += 1

        # Return latest paragraphs first
        return list(reversed(snippets))
