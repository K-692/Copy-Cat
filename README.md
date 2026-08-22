<div align="center">

<img src="logo.png" alt="Copy Cat Logo" width="180" style="border-radius: 24px; margin-bottom: 12px;" />

# 🐱 Copy Cat

**A lightweight, cross-platform, asynchronous keystroke memory and instant retrieval system — going far beyond traditional clipboard history.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg?style=flat)]()
[![UI](https://img.shields.io/badge/UI-Tkinter%20Dark%20Theme-indigo.svg?style=flat)]()
[![Status](https://img.shields.io/badge/Status-In%20Active%20Daily%20Use-brightgreen.svg?style=flat)]()
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=flat)](LICENSE)

*Silently records keystrokes directly into persistent storage (`memory.txt`), structures timestamped paragraphs with pause detection, handles continuous-typing backspace erasure and mouse interruptions, retains your last 3 days of text even across complete system shutdowns, and provides instant retrieval via a sleek, compact bottom-left floating popup.*

</div>

---

## 📑 Table of Contents

- [💡 Why Copy-Cat?](#-why-copy-cat)
- [🌟 Key Features](#-key-features)
- [📁 Project Architecture](#-project-architecture)
- [🚀 Quick Start & Installation](#-quick-start--installation)
- [🖥️ Usage & CLI Reference](#️-usage--cli-reference)
- [🎨 Modern Bottom-Left Retrieval UI](#-modern-bottom-left-retrieval-ui)
- [⚙️ Background Autostart Setup (Always Run on Login)](#️-background-autostart-setup-always-run-on-login)
  - [🍎 macOS (LaunchAgent)](#-1-macos-launchagent)
  - [🐧 Linux (systemd User Service)](#-2-linux-systemd-user-service)
  - [🪟 Windows (Silent Startup)](#-3-windows-silent-startup)
- [🔒 macOS Permissions Notice](#-macos-permissions-notice)
- [⚙️ Configuration Options](#️-configuration-options)
- [⌨️ Keyboard Shortcuts](#️-keyboard-shortcuts)

---

## 💡 Why Copy-Cat?

> **Has it ever happened to you that you wrote something for a very long time, and then either forgot to save it or lost it completely due to an unexpected system crash, sudden power outage, or accidental tab closure?**
>
> **Copy-Cat solves this problem once and for all by automatically capturing your keystrokes live in the background.**
>
> This allows you to retrieve **at least 70%–100%** of your lost text depending on how you write *(which you will quickly understand and appreciate while using Copy-Cat 😁)*!

### 🚀 Beyond Traditional Clipboard Managers
Standard clipboard managers only remember text **after** you explicitly press `Cmd+C` / `Ctrl+C`. If your browser crashes, an editor freezes, or you accidentally navigate away while typing a long document, email, or message, traditional clipboard tools cannot help you because the text was never copied.

**Copy-Cat works beyond copying:** it passively captures keystrokes as you type across any application, ensuring your thoughts are safeguarded without requiring any manual copy action.

### 💾 Survives System Shutdowns & Reboots (3-Day History Retention)
Everything you type is saved safely and persistently to disk (`memory.txt`). **Even if your system suffers a hard shutdown, crash, or is turned off for hours or days, you can retrieve texts from up to 3 days ago** as soon as you power your machine back on. The automated rolling cleanup continuously manages storage by pruning entries only when they surpass the 3-day (72-hour) mark.

### 👤 In Active Daily Use
> *"Currently, I am actively using Copy-Cat every single day as my primary safeguard. It has repeatedly saved lost drafts, complex prompts, and unsaved code snippets across unexpected application crashes and system reboots!"*

---

## 🌟 Key Features

1. **Direct Timestamped Keystroke Recording (Beyond Clipboard)**:
   - Captures letters, numbers, punctuation, symbols, whitespace, and Enter newlines directly into `memory.txt`.
   - **No Manual Copy Needed**: Works automatically in the background across all applications without needing `Cmd+C` / `Ctrl+C`.
   - **`[DD-MM-YYYY HH:MM:SS]` Timestamps**: Every typing session starts with a formatted timestamp header.
   - **10-Second Pause Gap**: Whenever you pause typing for $> 10$ seconds, a blank line gap and a fresh timestamp header (`\n\n[DD-MM-YYYY HH:MM:SS]\n`) are automatically prepended to the new paragraph.
   - Filters out system shortcut combinations (e.g. `Cmd+C`, `Cmd+V`, `Cmd+Z`, `Ctrl+C`).

2. **Continuous-Typing Backspace Erasure & Interruption Handling**:
   - **Continuous Typing**: When typing continuously, pressing `Backspace` within 5 seconds erases the corresponding characters from the active line in `memory.txt` (never deleting into the timestamp header).
   - **Interruption Detection**: If a mouse click or non-character navigation key occurs before pressing `Backspace`, `memory.txt` writes a newline (`\n`), preserves the previous line, and enters subsequent characters on the new line.

3. **Persistent 3-Day History & Rolling Expiration Pruning**:
   - **Shutdown Resistant**: Persistently stores text on disk so your 3-day history remains intact even if your computer shuts down or crashes.
   - Zero requirement for secondary timer files.
   - Every paragraph block in `memory.txt` is tracked by its timestamp.
   - When 3 days (72 hours) elapse for a specific entry, **only that expired entry is pruned**, preserving newer entries.
   - Startup catch-up check guarantees rolling cleanup even if the system was powered off.

4. **Sleek Bottom-Left Retrieval Popup (`logo.png` Branded)**:
   - **Global Hotkey**: Press `Ctrl` 3 times rapidly on macOS (or `Alt` 3 times on Windows/Linux) within 1.5 seconds.
   - **Bottom-Left Positioning**: Always pops up in the bottom-left corner of the screen by default.
   - **Dimension Adjustable**: Compact default size (`580x380`), resizable on the fly via the bottom-right drag handle (`⇲`), draggable by header, and configurable via CLI or `config.py`.
   - **Instant Copy**: Press `Enter` to copy selected text to the clipboard with green feedback without closing the popup.
   - **Search & Preview**: Live search filter, scrollable listbox, and detailed metadata preview.

---

## 📁 Project Architecture

```
copy_cat/
├── copy_cat/
│   ├── __init__.py            # Package version & metadata
│   ├── config.py              # Cross-platform config, paths, fonts, UI dimensions & margins
│   ├── storage.py             # Process-safe FileIO with timestamps & 3-day pruning
│   ├── listener.py            # Keystroke & mouse listener with 10s pause & backspace logic
│   ├── scheduler.py           # Background maintenance scheduler (3-day rolling wipe)
│   ├── ui.py                  # Tkinter compact bottom-left popup with logo & resize grip
│   └── app.py                 # Application lifecycle coordinator & hotkey subprocess spawner
├── scripts/
│   ├── com.copycat.app.plist  # macOS LaunchAgent template
│   ├── install_mac.sh         # macOS LaunchAgent automated installer
│   ├── uninstall_mac.sh       # macOS LaunchAgent uninstaller
│   ├── copycat.service        # Linux systemd user service unit template
│   ├── install_linux.sh       # Linux systemd user service automated installer
│   ├── uninstall_linux.sh     # Linux systemd user service uninstaller
│   ├── start_windows.vbs      # Windows silent VBS background launcher
│   ├── install_windows.bat    # Windows startup shortcut installer
│   └── uninstall_windows.bat  # Windows startup shortcut uninstaller
├── logo.png                   # High-resolution application logo & branding
├── main.py                    # Application entry point CLI
├── memory.txt                 # Persistent storage for logged text (created on runtime)
├── requirements.txt           # Python dependencies
├── .gitignore                 # Comprehensive Git ignore rules
└── README.md                  # Project documentation
```

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
- Python 3.10 or higher
- macOS, Windows, or Linux

### 2. Clone & Setup Virtual Environment

```bash
# Clone repository
git clone https://github.com/K-692/Copy-Cat.git
cd Copy-Cat

# Create & activate virtual environment (macOS / Linux):
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell / CMD):
python -m venv venv
.\venv\Scripts\activate

# Install dependencies:
pip install -r requirements.txt
```

---

## 🖥️ Usage & CLI Reference

### 1. Run Background Application (Foreground Mode)

Start the keystroke recorder, 3-day scheduler, and global hotkey listener:

```bash
python main.py
```

### 2. Open Retrieval Popup UI Directly

Launch the bottom-left memory retrieval window directly:

```bash
python main.py --popup
```

#### Custom Dimensions:
You can specify custom window dimensions directly via CLI:
```bash
python main.py --popup --width 640 --height 420
```

### 3. Manually Wipe Stored Memory

Erase all recorded entries inside `memory.txt`:

```bash
python main.py --wipe-memory
```

---

## 🎨 Modern Bottom-Left Retrieval UI

The Copy Cat UI is engineered to be unobtrusive, fast, and visually refined:

| Feature | Description |
|---|---|
| **Bottom-Left Anchor** | Pops up at bottom-left (`24px` from left, `48px` above bottom margin) to avoid obstructing main workspaces. |
| **Header Dragging** | Click and drag anywhere on the header bar to move the popup window. |
| **Interactive Resize Grip** | Drag the `⇲` handle in the bottom-right corner to adjust width and height in real-time. |
| **Branded Header** | Displays the crisp `logo.png` icon alongside the application title. |
| **Search & Filter** | Instant live search as you type across all stored timestamped paragraphs. |
| **Quick Copy** | Press `Enter` to copy text to clipboard with instant emerald green feedback badge. |

---

## ⚙️ Background Autostart Setup (Always Run on Login)

### 🍎 1. macOS (LaunchAgent)

#### Automated Setup (Recommended):
Run the automated installer from the repository root:
```bash
./scripts/install_mac.sh
```

#### Manual Setup:
1. Copy the plist file to `~/Library/LaunchAgents`:
   ```bash
   mkdir -p ~/Library/LaunchAgents
   cp scripts/com.copycat.app.plist ~/Library/LaunchAgents/
   ```
2. Replace `{{PYTHON_EXECUTABLE}}`, `{{MAIN_SCRIPT}}`, and `{{WORKING_DIRECTORY}}` inside `~/Library/LaunchAgents/com.copycat.app.plist` with your absolute paths.
3. Load the agent:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.copycat.app.plist
   ```

#### To Uninstall:
```bash
./scripts/uninstall_mac.sh
```

---

### 🐧 2. Linux (systemd User Service)

#### Automated Setup (Recommended):
```bash
./scripts/install_linux.sh
```

#### Manual Setup:
1. Copy unit file:
   ```bash
   mkdir -p ~/.config/systemd/user
   cp scripts/copycat.service ~/.config/systemd/user/
   ```
2. Configure absolute paths inside `~/.config/systemd/user/copycat.service`.
3. Enable and start:
   ```bash
   systemctl --user daemon-reload
   systemctl --user enable --now copycat.service
   ```

#### To Uninstall:
```bash
./scripts/uninstall_linux.sh
```

---

### 🪟 3. Windows (Silent Startup)

#### Automated Setup (Recommended):
Double-click or run:
```cmd
scripts\install_windows.bat
```

#### Manual Setup:
1. Press `Win + R`, type `shell:startup`, and press `Enter`.
2. Create a shortcut pointing to `scripts\start_windows.vbs`.

#### To Uninstall:
Run `scripts\uninstall_windows.bat` or delete the shortcut from `shell:startup`.

---

## 🔒 macOS Permissions Notice

On macOS, keyboard and mouse hooks require **Accessibility** and **Input Monitoring** permissions:

1. Open **System Settings** > **Privacy & Security**.
2. Click **Accessibility** and toggle **ON** your Terminal application or Python binary.
3. Click **Input Monitoring** and ensure the same binary/Terminal is enabled.

---

## ⚙️ Configuration Options

All timing thresholds, geometry settings, and font mappings can be customized in [`copy_cat/config.py`](copy_cat/config.py):

| Constant | Default Value | Description |
|---|---|---|
| `POPUP_DEFAULT_WIDTH` | `460` | Default width of retrieval popup in pixels |
| `POPUP_DEFAULT_HEIGHT` | `270` | Default height of retrieval popup in pixels |
| `POPUP_MIN_WIDTH` | `360` | Minimum allowable width when resizing |
| `POPUP_MIN_HEIGHT` | `200` | Minimum allowable height when resizing |
| `POPUP_MARGIN_LEFT` | `16` | Distance in pixels from screen left edge |
| `POPUP_MARGIN_BOTTOM` | `36` | Distance in pixels from screen bottom edge |
| `PAUSE_THRESHOLD_SECONDS` | `10.0` | Inactivity interval that starts a new timestamped paragraph |
| `BACKSPACE_TIMEOUT_SECONDS` | `5.0` | Maximum continuous typing duration allowed for backspace deletion |
| `MEMORY_WIPE_INTERVAL_SECONDS` | `259200.0` | Rolling expiration lifespan per entry (3 days = 72 hours) |
| `HOTKEY_PRESS_COUNT` | `3` | Rapid modifier presses required to open UI popup |
| `HOTKEY_WINDOW_SECONDS` | `1.5` | Maximum time window to register modifier presses |

---

## ⌨️ Keyboard Shortcuts

| Action | macOS | Windows / Linux |
|---|---|---|
| **Trigger Retrieval Popup** | Press `Ctrl` 3 times in 1.5s | Press `Alt` (or `Ctrl`) 3 times in 1.5s |
| **Navigate Snippets** | `↑` / `↓` Arrow keys | `↑` / `↓` Arrow keys |
| **Search Memory** | Type in search bar | Type in search bar |
| **Copy Selected Paragraph** | `Enter` (keeps popup open) | `Enter` (keeps popup open) |
| **Dismiss / Close Popup** | `Escape` or click `✕` | `Escape` or click `✕` |
| **Move Window** | Click and drag header | Click and drag header |
| **Resize Window** | Drag bottom-right `⇲` handle | Drag bottom-right `⇲` handle |


---

<div align="center">
  <sub>Built with ❤️ for privacy-first, lightning-fast memory retrieval.</sub>
</div>
