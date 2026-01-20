#!/bin/bash
# Argus Overview - Portable Tarball Build Script
# Creates a self-contained tarball that runs directly after extraction
#
# Output: dist/argus-overview-VERSION-portable-linux-x86_64.tar.gz
#
# User experience:
#   tar xf argus-overview-X.X.X-portable-linux-x86_64.tar.gz
#   cd argus-overview-X.X.X
#   ./run.sh

set -e

echo "================================================================"
echo "Argus Overview - Portable Tarball Builder"
echo "================================================================"
echo ""

# Get version from pyproject.toml
VERSION=$(grep 'version = ' pyproject.toml | head -1 | cut -d'"' -f2)
echo "Building version: $VERSION"

# Configuration
BUILD_NAME="argus-overview-${VERSION}"
BUILD_DIR="dist/${BUILD_NAME}"
TARBALL="dist/${BUILD_NAME}-portable-linux-x86_64.tar.gz"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python version: $PYTHON_VERSION"

# Clean previous build
echo ""
echo "Cleaning previous build..."
rm -rf "$BUILD_DIR"
rm -f "$TARBALL"
mkdir -p "$BUILD_DIR"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv "$BUILD_DIR/venv"
source "$BUILD_DIR/venv/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip wheel > /dev/null
pip install -r requirements.txt > /dev/null
echo "Dependencies installed"

# Deactivate venv
deactivate

# Copy source files
echo "Copying source files..."
cp -r src "$BUILD_DIR/"
cp -r assets "$BUILD_DIR/" 2>/dev/null || mkdir -p "$BUILD_DIR/assets"
cp requirements.txt "$BUILD_DIR/"
cp LICENSE "$BUILD_DIR/"

# Create run.sh launcher
echo "Creating launcher..."
cat > "$BUILD_DIR/run.sh" << 'LAUNCHER'
#!/bin/bash
# Argus Overview - Portable Launcher
# Run this script to start Argus Overview

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check system dependencies
check_deps() {
    local missing=()
    for cmd in wmctrl xdotool import; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        echo "Missing system dependencies: ${missing[*]}"
        echo ""
        echo "Install them with:"
        if [ -f /etc/debian_version ]; then
            echo "  sudo apt-get install wmctrl xdotool imagemagick"
        elif [ -f /etc/redhat-release ]; then
            echo "  sudo dnf install wmctrl xdotool ImageMagick"
        elif [ -f /etc/arch-release ]; then
            echo "  sudo pacman -S wmctrl xdotool imagemagick"
        else
            echo "  wmctrl xdotool imagemagick (via your package manager)"
        fi
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Check dependencies on first run
if [ ! -f "$SCRIPT_DIR/.deps_checked" ]; then
    check_deps
    touch "$SCRIPT_DIR/.deps_checked"
fi

# Activate venv and run
source "$SCRIPT_DIR/venv/bin/activate"
PYTHONPATH="$SCRIPT_DIR/src" exec python "$SCRIPT_DIR/src/main.py" "$@"
LAUNCHER

chmod +x "$BUILD_DIR/run.sh"

# Create README
cat > "$BUILD_DIR/README.txt" << README
Argus Overview v${VERSION} - Portable Edition
============================================

QUICK START
-----------
1. Extract this archive anywhere
2. Run: ./run.sh

SYSTEM REQUIREMENTS
-------------------
- Linux x86_64
- Python ${PYTHON_VERSION}+ (included in venv)
- System tools: wmctrl, xdotool, imagemagick

Install system tools:
  Ubuntu/Debian: sudo apt-get install wmctrl xdotool imagemagick
  Fedora/RHEL:   sudo dnf install wmctrl xdotool ImageMagick
  Arch Linux:    sudo pacman -S wmctrl xdotool imagemagick

CONFIGURATION
-------------
Config files are stored in: ~/.config/argus-overview/

For full documentation, see:
https://github.com/AreteDriver/Argus_Overview

Fly safe! o7
README

# Create desktop file template (optional install)
cat > "$BUILD_DIR/install-desktop.sh" << 'DESKTOP_INSTALL'
#!/bin/bash
# Optional: Install desktop entry for application menu integration

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

mkdir -p ~/.local/share/applications
mkdir -p ~/.local/share/icons/hicolor/256x256/apps

# Copy icon
if [ -f "$SCRIPT_DIR/assets/icon.png" ]; then
    cp "$SCRIPT_DIR/assets/icon.png" ~/.local/share/icons/hicolor/256x256/apps/argus-overview.png
    ICON_NAME="argus-overview"
else
    ICON_NAME="utilities-system-monitor"
fi

# Create desktop entry
cat > ~/.local/share/applications/argus-overview.desktop << EOF
[Desktop Entry]
Type=Application
Name=Argus Overview
Comment=Professional Multi-Boxing Tool for EVE Online
Exec=$SCRIPT_DIR/run.sh
Icon=$ICON_NAME
Terminal=false
Categories=Utility;Game;
Keywords=eve;online;multibox;preview;
StartupWMClass=Argus Overview
EOF

# Update caches
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor/ 2>/dev/null || true
update-desktop-database ~/.local/share/applications 2>/dev/null || true

echo "Desktop entry installed!"
echo "Argus Overview should now appear in your applications menu."
DESKTOP_INSTALL

chmod +x "$BUILD_DIR/install-desktop.sh"

# Create tarball
echo ""
echo "Creating tarball..."
cd dist
tar czf "${BUILD_NAME}-portable-linux-x86_64.tar.gz" "$BUILD_NAME"
cd ..

# Calculate size
TARBALL_SIZE=$(du -h "$TARBALL" | cut -f1)

echo ""
echo "================================================================"
echo "Build Complete!"
echo "================================================================"
echo ""
echo "Output: $TARBALL"
echo "Size:   $TARBALL_SIZE"
echo ""
echo "To use:"
echo "  tar xf ${BUILD_NAME}-portable-linux-x86_64.tar.gz"
echo "  cd ${BUILD_NAME}"
echo "  ./run.sh"
echo ""
