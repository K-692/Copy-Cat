#!/usr/bin/env bash
# ==============================================================================
# Copy Cat — Linux systemd User Service Installer
# Automatically configures, enables, and starts Copy Cat as a systemd user unit.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "$PROJECT_ROOT/venv/bin/python" ]; then
    PYTHON_EXEC="$PROJECT_ROOT/venv/bin/python"
elif [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_EXEC="$PROJECT_ROOT/.venv/bin/python"
else
    PYTHON_EXEC="$(which python3)"
fi

MAIN_SCRIPT="$PROJECT_ROOT/main.py"
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_DEST="$SERVICE_DIR/copycat.service"

echo "🐱 Installing Copy Cat Linux systemd user service..."
echo "  • Project Root: $PROJECT_ROOT"
echo "  • Python Path:  $PYTHON_EXEC"
echo "  • Target:       $SERVICE_DEST"

mkdir -p "$SERVICE_DIR"

cat > "$SERVICE_DEST" <<EOF
[Unit]
Description=Copy Cat Background Keystroke Logger & Retrieval Service
After=graphical-session.target

[Service]
Type=simple
WorkingDirectory=$PROJECT_ROOT
ExecStart=$PYTHON_EXEC $MAIN_SCRIPT
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now copycat.service

echo "✓ Copy Cat service enabled and started!"
echo "  Check status: systemctl --user status copycat.service"
echo "  View logs:    journalctl --user -u copycat.service -f"
echo "  To uninstall: ./scripts/uninstall_linux.sh"
