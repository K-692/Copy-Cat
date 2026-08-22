#!/usr/bin/env bash
# ==============================================================================
# Copy Cat — macOS LaunchAgent Uninstaller
# Stops and removes the Copy Cat background LaunchAgent.
# ==============================================================================

set -e

PLIST_DEST="$HOME/Library/LaunchAgents/com.copycat.app.plist"

echo "🐱 Uninstalling Copy Cat macOS LaunchAgent..."

if [ -f "$PLIST_DEST" ]; then
    echo "  • Unloading LaunchAgent service..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
    echo "  • Removing plist configuration..."
    rm -f "$PLIST_DEST"
    echo "✓ Copy Cat LaunchAgent uninstalled successfully."
else
    echo "• No installed LaunchAgent plist found at $PLIST_DEST."
fi
