"""
Main Entry Point for Copy Cat Application.
Run this script to start the background keystroke and mouse listener,
3-day maintenance scheduler, and retrieval hotkey listener.

Usage:
    python main.py                  # Start background app (keystroke recording to memory.txt)
    python main.py --popup          # Open quick retrieval UI popup directly
    python main.py --wipe-memory    # Manually wipe memory.txt
"""

import argparse
import logging
import sys

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("CopyCat")


def main() -> None:
    """
    Parse command line arguments and launch requested Copy Cat subsystem.
    """
    parser = argparse.ArgumentParser(
        description="Copy Cat: Background keystroke logger, direct memory storage & quick retrieval tool."
    )
    parser.add_argument(
        "--popup",
        action="store_true",
        help="Open the memory retrieval popup UI directly.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=None,
        help="Optional custom popup window width in pixels (e.g. 580).",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=None,
        help="Optional custom popup window height in pixels (e.g. 380).",
    )
    parser.add_argument(
        "--wipe-memory",
        action="store_true",
        help="Manually wipe all stored paragraphs from memory.txt.",
    )

    args = parser.parse_args()

    # Subcommand: Manually wipe memory.txt
    if args.wipe_memory:
        from copy_cat.storage import FileIO
        file_io = FileIO()
        file_io.clear_memory()
        logger.info("memory.txt wiped successfully.")
        return

    # Subcommand: Open Quick Retrieval UI popup directly
    if args.popup:
        from copy_cat.ui import trigger_popup
        logger.info("Opening Copy Cat UI popup (width=%s, height=%s)...", args.width, args.height)
        trigger_popup(width=args.width, height=args.height)
        return

    # Default: Start full background application with keystroke listener and 3-day maintenance scheduler
    from copy_cat.app import CopyCatApp
    app = CopyCatApp()
    app.start()


if __name__ == "__main__":
    main()
