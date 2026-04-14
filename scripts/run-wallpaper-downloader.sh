#!/bin/bash
# Launcher for Bing Wallpaper Downloader
# Works on Linux, macOS, and Windows (Git Bash/WSL)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check Python availability
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "❌ Error: Python is required but not found"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON -c "import sys; print(sys.version_info.major)")
if [ "$PYTHON_VERSION" -lt 3 ]; then
    echo "❌ Error: Python 3 is required"
    exit 1
fi

echo "🖼️  Starting Bing Wallpaper Downloader..."
$PYTHON "$SCRIPT_DIR/wallpaper_downloader.py"
