#!/usr/bin/env bash
set -euo pipefail
# CITL_CWD_GUARD_V2
if ! pwd >/dev/null 2>&1; then
  cd "$HOME" 2>/dev/null || cd / 2>/dev/null || true
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

bash "./scripts/linux/setup.sh"

DESK="$HOME/.local/share/applications/ai-training-hub.desktop"
mkdir -p "$HOME/.local/share/applications"

cat > "$DESK" <<DESK_EOF
[Desktop Entry]
Version=1.0
Name=AI Training Hub
Comment=Local training hub launcher
Exec=bash -lc 'cd "$REPO_ROOT" && . .venv/bin/activate && python3 hub_launcher.py'
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Education;Development;
StartupNotify=true
DESK_EOF

update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
echo "Launcher installed: $DESK"
