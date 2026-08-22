#!/usr/bin/env bash
# ==============================================================================
# Copy Cat — macOS LaunchAgent Installer
# Automatically configures and registers Copy Cat to run silently on login.
# ==============================================================================

set -e

# Resolve project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Detect python interpreter inside virtual environment
if [ -f "$PROJECT_ROOT/venv/bin/python" ]; then
    PYTHON_EXEC="$PROJECT_ROOT/venv/bin/python"
elif [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_EXEC="$PROJECT_ROOT/.venv/bin/python"
else
    PYTHON_EXEC="$(which python3)"
fi

MAIN_SCRIPT="$PROJECT_ROOT/main.py"
PLIST_DEST="$HOME/Library/LaunchAgents/com.copycat.app.plist"

echo "🐱 Installing Copy Cat macOS LaunchAgent..."
echo "  • Project Root: $PROJECT_ROOT"
echo "  • Python Path:  $PYTHON_EXEC"
echo "  • Main Script:  $MAIN_SCRIPT"
echo "  • Plist Target: $PLIST_DEST"

# Ensure LaunchAgents directory exists
mkdir -p "$HOME/Library/LaunchAgents"

# Unload previous service if currently registered
if launchctl list | grep -q "com.copycat.app"; then
    echo "  • Unloading existing service..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

# Generate configured plist file
cat > "$PLIST_DEST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.copycat.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_EXEC</string>
        <string>$MAIN_SCRIPT</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_ROOT</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/copycat.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/copycat.stderr.log</string>
</dict>
</plist>
EOF

# Load and start the background service
launchctl load "$PLIST_DEST"

echo "✓ Copy Cat LaunchAgent installed and loaded successfully!"
echo "  To view logs: tail -f /tmp/copycat.stdout.log"
echo "  To uninstall: ./scripts/uninstall_mac.sh"
echo ""
echo "=============================================================================="
echo "⚠️  IMPORTANT: macOS Accessibility & Input Monitoring Permission Required"
echo "=============================================================================="
echo "macOS requires explicit permission for background keystroke listeners."
echo ""
echo "Please ensure the Python binary is enabled in System Settings:"
echo "  1. Open System Settings > Privacy & Security > Accessibility"
echo "  2. Toggle ON 'Python' (or add '$PYTHON_EXEC')"
echo "  3. Open System Settings > Privacy & Security > Input Monitoring"
echo "  4. Toggle ON 'Python' (or add '$PYTHON_EXEC')"
echo ""
echo "Opening Accessibility Settings now..."
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility" 2>/dev/null || true
echo "=============================================================================="
