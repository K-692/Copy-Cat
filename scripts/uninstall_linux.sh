#!/usr/bin/env bash
# ==============================================================================
# Copy Cat — Linux systemd User Service Uninstaller
# Stops, disables, and removes the Copy Cat systemd user service unit.
# ==============================================================================

set -e

SERVICE_DEST="$HOME/.config/systemd/user/copycat.service"

echo "🐱 Uninstalling Copy Cat Linux systemd user service..."

if [ -f "$SERVICE_DEST" ]; then
    echo "  • Stopping and disabling service..."
    systemctl --user stop copycat.service 2>/dev/null || true
    systemctl --user disable copycat.service 2>/dev/null || true
    echo "  • Removing service unit file..."
    rm -f "$SERVICE_DEST"
    systemctl --user daemon-reload
    echo "✓ Copy Cat service uninstalled successfully."
else
    echo "• No installed service unit found at $SERVICE_DEST."
fi
