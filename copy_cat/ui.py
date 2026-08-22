"""
UI and Quick Retrieval Module for Copy Cat.
Provides a sleek, compact, borderless popup window built with Tkinter for quick retrieval
of timestamped paragraphs from memory.txt across macOS, Windows, and Linux.
Features:
- Bottom-left screen positioning.
- Dimension adjustable via parameters and interactive drag-to-resize grip.
- Header drag-to-move support.
- Logo branding loaded from logo.png.
- Live search filtering, metadata preview, and instant copy-to-clipboard on Enter.
"""

import logging
import tkinter as tk
from tkinter import font as tkfont
from typing import List, Dict, Any, Optional

import pyperclip

from copy_cat.config import (
    FONT_FAMILY_PRIMARY,
    FONT_FAMILY_MONO,
    LOGO_PATH,
    POPUP_DEFAULT_WIDTH,
    POPUP_DEFAULT_HEIGHT,
    POPUP_MIN_WIDTH,
    POPUP_MIN_HEIGHT,
    POPUP_MARGIN_LEFT,
    POPUP_MARGIN_BOTTOM,
)
from copy_cat.storage import FileIO

logger = logging.getLogger(__name__)


class ModernPopupUI:
    """
    Sleek, dark-themed popup window for searching, selecting, and copying
    saved keystroke snippets exclusively from memory.txt.
    Always anchors at bottom-left by default, supports dynamic resizing,
    and displays the project logo.
    """

    def __init__(
        self,
        file_io: Optional[FileIO] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ):
        """
        Initialize the popup UI.

        Args:
            file_io: FileIO instance for reading memory.txt snippets.
            width: Custom popup width in pixels (defaults to POPUP_DEFAULT_WIDTH).
            height: Custom popup height in pixels (defaults to POPUP_DEFAULT_HEIGHT).
        """
        self.file_io = file_io or FileIO()
        self.width = width or POPUP_DEFAULT_WIDTH
        self.height = height or POPUP_DEFAULT_HEIGHT
        self.root: Optional[tk.Tk] = None
        self.is_open = False
        self._snippets: List[Dict[str, Any]] = []
        self._filtered_snippets: List[Dict[str, Any]] = []
        self._notification_timer: Optional[str] = None
        self._logo_image: Optional[Any] = None

        # Drag-to-move coordinate tracking
        self._drag_start_x: int = 0
        self._drag_start_y: int = 0

        # Drag-to-resize coordinate tracking
        self._resize_start_x: int = 0
        self._resize_start_y: int = 0
        self._resize_start_w: int = self.width
        self._resize_start_h: int = self.height

    def show(self) -> None:
        """
        Display the popup window at the bottom-left of the active display.
        If already open, brings the existing window to the front.
        """
        if self.is_open and self.root:
            logger.info("Popup is already open. Bringing to front.")
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.focus_force()
            return

        self._create_and_run_window()

    def _load_logo_image(self, size: int = 24) -> Optional[Any]:
        """
        Load and scale logo.png for display in the Tkinter UI header.
        Uses Pillow if available for anti-aliasing; falls back to tk.PhotoImage.

        Args:
            size: Target width and height in pixels.

        Returns:
            PhotoImage instance or None if loading fails.
        """
        if not LOGO_PATH.exists():
            return None

        try:
            from PIL import Image, ImageTk
            img = Image.open(LOGO_PATH)
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            logger.debug("Pillow logo load fallback: %s", e)
            try:
                raw_photo = tk.PhotoImage(file=str(LOGO_PATH))
                sub_x = max(1, raw_photo.width() // size)
                sub_y = max(1, raw_photo.height() // size)
                return raw_photo.subsample(sub_x, sub_y)
            except Exception as e2:
                logger.warning("Could not load logo image: %s", e2)
                return None

    def _create_responsive_button(
        self,
        parent: tk.Widget,
        text: str,
        command: Any,
        default_bg: str = "#27272a",
        default_fg: str = "#a1a1aa",
        hover_bg: str = "#6366f1",
        hover_fg: str = "#ffffff",
        active_bg: str = "#4f46e5",
        font_size: int = 9,
        padx: int = 6,
        pady: int = 2,
    ) -> tk.Label:
        """
        Creates a custom, highly responsive button widget using a Tkinter Label.
        Guarantees 100% surface area hit-testing across macOS, Windows, and Linux.
        Clicking ANYWHERE inside the entire rectangular boundary triggers the command immediately.
        """
        btn = tk.Label(
            parent,
            text=text,
            font=tkfont.Font(family=FONT_FAMILY_PRIMARY, size=font_size, weight="bold"),
            fg=default_fg,
            bg=default_bg,
            padx=padx,
            pady=pady,
            cursor="hand2",
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            justify=tk.CENTER,
        )

        def on_click(event):
            btn.config(bg=active_bg, fg=hover_fg)
            command()
            return "break"

        def on_enter(event):
            btn.config(bg=hover_bg, fg=hover_fg)

        def on_leave(event):
            btn.config(bg=default_bg, fg=default_fg)

        btn.bind("<Button-1>", on_click)
        btn.bind(
            "<ButtonRelease-1>",
            lambda e: btn.config(
                bg=hover_bg if (0 <= e.x <= btn.winfo_width() and 0 <= e.y <= btn.winfo_height()) else default_bg
            ),
        )
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return btn

    def _create_and_run_window(self) -> None:
        """
        Construct, style, and render the Tkinter window.
        Positions the window at the bottom-left of the screen.
        """
        self.is_open = True
        self.root = tk.Tk()
        self.root.title("Copy Cat — Memory Retrieval")

        # Compute screen dimensions and bottom-left coordinate
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        pos_x = POPUP_MARGIN_LEFT
        pos_y = max(0, screen_height - self.height - POPUP_MARGIN_BOTTOM)

        # Set geometry and window properties
        self.root.geometry(f"{self.width}x{self.height}+{pos_x}+{pos_y}")
        self.root.overrideredirect(True)        # Borderless floating window
        self.root.attributes("-topmost", True)  # Always on top

        # Set application icon if supported
        self._logo_image = self._load_logo_image(size=24)
        if self._logo_image:
            try:
                self.root.iconphoto(True, self._logo_image)
            except Exception:
                pass

        # Color Palette - Sleek Modern Dark Theme
        bg_dark = "#18181b"          # Zinc 900
        bg_card = "#27272a"          # Zinc 800
        bg_input = "#3f3f46"         # Zinc 700
        fg_white = "#f4f4f5"         # Zinc 100
        fg_muted = "#a1a1aa"         # Zinc 400
        accent_blue = "#6366f1"      # Indigo 500
        accent_glow = "#818cf8"      # Indigo 400
        accent_green = "#22c55e"     # Emerald 500
        border_color = "#3f3f46"     # Zinc 700 border

        self.root.configure(bg=bg_dark, highlightthickness=1, highlightbackground=border_color)

        # Cross-platform Fonts
        title_font = tkfont.Font(family=FONT_FAMILY_PRIMARY, size=11, weight="bold")
        body_font = tkfont.Font(family=FONT_FAMILY_PRIMARY, size=10)
        mono_font = tkfont.Font(family=FONT_FAMILY_MONO, size=9)
        badge_font = tkfont.Font(family=FONT_FAMILY_PRIMARY, size=8, weight="bold")
        hint_font = tkfont.Font(family=FONT_FAMILY_PRIMARY, size=8)

        # =========================================================================
        # 1. Top Header Bar (Draggable)
        # =========================================================================
        header_frame = tk.Frame(self.root, bg=bg_dark, pady=6, padx=10)
        header_frame.pack(fill=tk.X)

        # Enable dragging the window by the header
        header_frame.bind("<Button-1>", self._start_drag)
        header_frame.bind("<B1-Motion>", self._on_drag)

        # Title Subframe (Logo + Text)
        title_box = tk.Frame(header_frame, bg=bg_dark)
        title_box.pack(side=tk.LEFT)
        title_box.bind("<Button-1>", self._start_drag)
        title_box.bind("<B1-Motion>", self._on_drag)

        if self._logo_image:
            logo_label = tk.Label(title_box, image=self._logo_image, bg=bg_dark)
            logo_label.pack(side=tk.LEFT, padx=(0, 6))
            logo_label.bind("<Button-1>", self._start_drag)
            logo_label.bind("<B1-Motion>", self._on_drag)

        header_title = tk.Label(
            title_box,
            text="Copy Cat",
            font=title_font,
            fg=fg_white,
            bg=bg_dark,
        )
        header_title.pack(side=tk.LEFT)
        header_title.bind("<Button-1>", self._start_drag)
        header_title.bind("<B1-Motion>", self._on_drag)

        # Right subframe: Navigation buttons & status hints
        right_header = tk.Frame(header_frame, bg=bg_dark)
        right_header.pack(side=tk.RIGHT)

        # Close button [✕] in header - responsive full surface area
        close_btn = self._create_responsive_button(
            parent=right_header,
            text="✕",
            command=self.close,
            default_bg=bg_dark,
            default_fg=fg_muted,
            hover_bg="#ef4444",
            hover_fg=fg_white,
            active_bg="#dc2626",
            font_size=10,
            padx=6,
            pady=2,
        )
        close_btn.pack(side=tk.RIGHT, padx=(6, 0))

        # Status / Feedback label with Navigation key beside Enter key
        self.status_label = tk.Label(
            right_header,
            text="[↑/↓] Navigate  •  [Enter] Copy  •  [Esc] Close",
            font=hint_font,
            fg=fg_muted,
            bg=bg_dark,
        )
        self.status_label.pack(side=tk.RIGHT, padx=(4, 0))
        self.status_label.bind("<Button-1>", self._start_drag)
        self.status_label.bind("<B1-Motion>", self._on_drag)

        # Clickable Navigation Up/Down arrow buttons beside status - responsive full surface area
        nav_btn_frame = tk.Frame(right_header, bg=bg_dark)
        nav_btn_frame.pack(side=tk.RIGHT, padx=(0, 4))

        self.btn_up = self._create_responsive_button(
            parent=nav_btn_frame,
            text="▲",
            command=self._on_arrow_up,
            default_bg=bg_card,
            default_fg=fg_muted,
            hover_bg=accent_blue,
            hover_fg=fg_white,
            active_bg="#4f46e5",
            font_size=8,
            padx=5,
            pady=2,
        )
        self.btn_up.pack(side=tk.LEFT, padx=1)

        self.btn_down = self._create_responsive_button(
            parent=nav_btn_frame,
            text="▼",
            command=self._on_arrow_down,
            default_bg=bg_card,
            default_fg=fg_muted,
            hover_bg=accent_blue,
            hover_fg=fg_white,
            active_bg="#4f46e5",
            font_size=8,
            padx=5,
            pady=2,
        )
        self.btn_down.pack(side=tk.LEFT, padx=1)

        # =========================================================================
        # 2. Search Bar
        # =========================================================================
        search_frame = tk.Frame(self.root, bg=bg_dark, padx=10, pady=2)
        search_frame.pack(fill=tk.X)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)

        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=body_font,
            bg=bg_input,
            fg=fg_white,
            insertbackground=accent_glow,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=accent_blue,
            highlightcolor=accent_glow,
        )
        self.search_entry.pack(fill=tk.X, ipady=4, ipadx=6)

        # =========================================================================
        # 3. Split Content Area (Snippets Listbox + Detail Preview)
        # =========================================================================
        content_frame = tk.Frame(self.root, bg=bg_dark, padx=10, pady=6)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left Column: Snippets Listbox
        list_container = tk.Frame(content_frame, bg=bg_card, highlightthickness=1, highlightbackground=border_color)
        list_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))

        self.listbox = tk.Listbox(
            list_container,
            bg=bg_card,
            fg=fg_white,
            selectbackground=accent_blue,
            selectforeground=fg_white,
            font=body_font,
            relief=tk.FLAT,
            highlightthickness=0,
            activestyle="none",
        )
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        # Right Column: Detail Preview Box
        preview_container = tk.Frame(content_frame, bg=bg_card, highlightthickness=1, highlightbackground=border_color)
        preview_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 0))

        self.preview_header = tk.Label(
            preview_container,
            text="Snippet Preview",
            font=badge_font,
            fg=accent_glow,
            bg=bg_card,
            anchor="w",
            padx=6,
            pady=4,
        )
        self.preview_header.pack(fill=tk.X)

        self.preview_text = tk.Text(
            preview_container,
            bg=bg_card,
            fg=fg_white,
            font=mono_font,
            wrap=tk.WORD,
            relief=tk.FLAT,
            highlightthickness=0,
            state=tk.DISABLED,
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 4))

        # =========================================================================
        # 4. Bottom Footer & Resize Grip Bar
        # =========================================================================
        footer_frame = tk.Frame(self.root, bg=bg_dark, padx=10, pady=3)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        footer_hint = tk.Label(
            footer_frame,
            text="[↑/↓] Navigate  •  Drag header to move",
            font=hint_font,
            fg=fg_muted,
            bg=bg_dark,
        )
        footer_hint.pack(side=tk.LEFT)

        # Interactive Resize Handle (⇲) in bottom-right corner
        self.resize_grip = tk.Label(
            footer_frame,
            text="⇲",
            font=tkfont.Font(family=FONT_FAMILY_PRIMARY, size=11),
            fg=fg_muted,
            bg=bg_dark,
            cursor="sizing",
        )
        self.resize_grip.pack(side=tk.RIGHT)
        self.resize_grip.bind("<Button-1>", self._start_resize)
        self.resize_grip.bind("<B1-Motion>", self._on_resize)
        self.resize_grip.bind("<Enter>", lambda e: self.resize_grip.config(fg=accent_glow))
        self.resize_grip.bind("<Leave>", lambda e: self.resize_grip.config(fg=fg_muted))

        # =========================================================================
        # 5. Load Stored Data & Key Bindings
        # =========================================================================
        self._load_snippets()

        # Key Bindings: Global Navigation & Escape Close
        self.root.bind_all("<Escape>", lambda e: self.close())
        self.root.bind_all("<Key-Escape>", lambda e: self.close())

        # Copy on Return anywhere
        self.root.bind("<Return>", lambda e: self._copy_selected())
        self.search_entry.bind("<Return>", lambda e: self._copy_selected())
        self.listbox.bind("<Return>", lambda e: self._copy_selected())
        self.preview_text.bind("<Return>", lambda e: self._copy_selected())

        # Universal Navigation with Up/Down arrow keys
        self.root.bind("<Down>", self._on_arrow_down)
        self.root.bind("<Up>", self._on_arrow_up)
        self.search_entry.bind("<Down>", self._on_arrow_down)
        self.search_entry.bind("<Up>", self._on_arrow_up)
        self.listbox.bind("<Down>", self._on_arrow_down)
        self.listbox.bind("<Up>", self._on_arrow_up)
        self.preview_text.bind("<Down>", self._on_arrow_down)
        self.preview_text.bind("<Up>", self._on_arrow_up)

        # Force focus to search bar on startup
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.focus_force()
        self.search_entry.focus_set()

        # Start Tk event loop
        try:
            self.root.mainloop()
        finally:
            self.is_open = False

    # =========================================================================
    # Drag-to-Move Window Methods
    # =========================================================================

    def _start_drag(self, event) -> None:
        """
        Record initial mouse click coordinates relative to window position.
        """
        if self.root:
            self._drag_start_x = event.x_root - self.root.winfo_x()
            self._drag_start_y = event.y_root - self.root.winfo_y()

    def _on_drag(self, event) -> None:
        """
        Update window position smoothly as header is dragged.
        """
        if self.root:
            new_x = event.x_root - self._drag_start_x
            new_y = event.y_root - self._drag_start_y
            self.root.geometry(f"+{new_x}+{new_y}")

    # =========================================================================
    # Drag-to-Resize Window Methods
    # =========================================================================

    def _start_resize(self, event) -> None:
        """
        Record mouse starting coordinates and initial window dimensions for resizing.
        """
        if self.root:
            self._resize_start_x = event.x_root
            self._resize_start_y = event.y_root
            self._resize_start_w = self.root.winfo_width()
            self._resize_start_h = self.root.winfo_height()

    def _on_resize(self, event) -> None:
        """
        Calculate new dimensions dynamically on mouse drag while respecting minimum size constraints.
        """
        if not self.root:
            return

        delta_x = event.x_root - self._resize_start_x
        delta_y = event.y_root - self._resize_start_y
        new_w = max(POPUP_MIN_WIDTH, self._resize_start_w + delta_x)
        new_h = max(POPUP_MIN_HEIGHT, self._resize_start_h + delta_y)

        curr_x = self.root.winfo_x()
        curr_y = self.root.winfo_y()
        self.root.geometry(f"{new_w}x{new_h}+{curr_x}+{curr_y}")

    # =========================================================================
    # Snippet Data Management & UI Refresh
    # =========================================================================

    def _load_snippets(self) -> None:
        """
        Fetch all snippets strictly from memory.txt and populate the listbox.
        """
        self._snippets = self.file_io.get_all_snippets()
        self._filtered_snippets = list(self._snippets)
        self._update_listbox()

    def _update_listbox(self) -> None:
        """
        Refresh listbox items based on filtered snippets.
        """
        self.listbox.delete(0, tk.END)
        for snippet in self._filtered_snippets:
            preview = snippet.get("preview", "")
            self.listbox.insert(tk.END, f" 📝 {preview}")

        if self._filtered_snippets:
            self.listbox.selection_set(0)
            self._display_snippet_details(self._filtered_snippets[0])
        else:
            self._display_empty_preview()

    def _on_search_changed(self, *args) -> None:
        """
        Filter snippets dynamically as the user types in the search bar.
        """
        query = self.search_var.get().strip().lower()
        if not query:
            self._filtered_snippets = list(self._snippets)
        else:
            self._filtered_snippets = [
                s for s in self._snippets
                if query in s.get("text", "").lower() or query in s.get("preview", "").lower()
            ]
        self._update_listbox()

    def _on_listbox_select(self, event=None) -> None:
        """
        Update the preview box when a listbox row is clicked or highlighted.
        """
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self._filtered_snippets):
                self._display_snippet_details(self._filtered_snippets[index])

    def _display_snippet_details(self, snippet: Dict[str, Any]) -> None:
        """
        Update preview text area contents and header metadata safely.
        """
        text = snippet.get("text", "")
        char_count = snippet.get("char_count", len(snippet.get("content", text)))
        line_count = snippet.get("line_count", len(text.splitlines()) or 1)
        ts = snippet.get("timestamp", "")

        header_str = f"📝 {ts}  •  {char_count} chars" if ts else f"📝 memory.txt  •  {char_count} chars"
        self.preview_header.config(text=header_str)

        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert(tk.END, text)
        self.preview_text.config(state=tk.DISABLED)

    def _display_empty_preview(self) -> None:
        """
        Display placeholder text when memory.txt is empty or no snippets match query.
        """
        self.preview_header.config(text="No Snippets")
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert(tk.END, "No paragraphs found in memory.txt matching your query.\nType to search or clear search to view all.")
        self.preview_text.config(state=tk.DISABLED)

    def _on_arrow_down(self, event=None):
        """
        Navigate down in the listbox regardless of which widget has focus.
        """
        selection = self.listbox.curselection()
        if selection:
            curr = selection[0]
            if curr + 1 < len(self._filtered_snippets):
                self.listbox.selection_clear(curr)
                self.listbox.selection_set(curr + 1)
                self.listbox.see(curr + 1)
                self._display_snippet_details(self._filtered_snippets[curr + 1])
        elif self._filtered_snippets:
            self.listbox.selection_set(0)
            self._display_snippet_details(self._filtered_snippets[0])
        return "break"

    def _on_arrow_up(self, event=None):
        """
        Navigate up in the listbox regardless of which widget has focus.
        """
        selection = self.listbox.curselection()
        if selection:
            curr = selection[0]
            if curr > 0:
                self.listbox.selection_clear(curr)
                self.listbox.selection_set(curr - 1)
                self.listbox.see(curr - 1)
                self._display_snippet_details(self._filtered_snippets[curr - 1])
        elif self._filtered_snippets:
            self.listbox.selection_set(0)
            self._display_snippet_details(self._filtered_snippets[0])
        return "break"

    def _copy_selected(self) -> None:
        """
        Copy selected snippet text (body content without timestamp if available) to clipboard.
        Flashes green confirmation status indicator without closing window.
        """
        selection = self.listbox.curselection()
        if not selection or not self._filtered_snippets:
            return

        index = selection[0]
        snippet = self._filtered_snippets[index]
        # Prefer copying content without timestamp header, or full text if content is empty
        selected_text = snippet.get("content") or snippet.get("text", "")

        logger.info("Copying snippet to system clipboard (%d chars)...", len(selected_text))
        pyperclip.copy(selected_text)

        # Show visual copy confirmation badge on UI
        self._show_copy_notification("✓ Copied to Clipboard!")

    def _show_copy_notification(self, message: str) -> None:
        """
        Display temporary copy feedback in the header status label.
        """
        self.status_label.config(text=message, fg="#22c55e")  # Emerald green

        # Reset back to default hint after 2 seconds
        if self._notification_timer:
            self.root.after_cancel(self._notification_timer)

        def _reset():
            if self.root and self.is_open:
                self.status_label.config(
                    text="[↑/↓] Navigate  •  [Enter] Copy  •  [Esc] Close",
                    fg="#a1a1aa",
                )

        self._notification_timer = self.root.after(2000, _reset)

    def close(self) -> None:
        """
        Destroy the popup window cleanly.
        """
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except Exception:
                pass
            self.root = None
        self.is_open = False


def trigger_popup(
    file_io: Optional[FileIO] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> None:
    """
    Helper function to launch the popup window with optional custom dimensions.

    Args:
        file_io: Optional FileIO storage instance.
        width: Optional custom width.
        height: Optional custom height.
    """
    popup = ModernPopupUI(file_io=file_io, width=width, height=height)
    popup.show()
