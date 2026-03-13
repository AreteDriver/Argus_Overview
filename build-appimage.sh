#!/bin/bash
# Argus Overview - AppImage Build Script
# Builds a portable AppImage for Linux distribution

set -e

# Get version from pyproject.toml
VERSION=$(grep 'version = ' pyproject.toml | head -1 | cut -d'"' -f2)

echo "================================================================"
echo "Argus Overview v${VERSION} - AppImage Builder"
echo "================================================================"
echo ""
echo "Building version: $VERSION"
echo ""

# Check build dependencies
echo "Checking build dependencies..."
for cmd in python3 pip wget; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: $cmd is required but not installed."
        exit 1
    fi
done
echo "Build dependencies found"
echo ""

# Check runtime dependencies (warn only)
echo "Checking runtime dependencies..."
for cmd in wmctrl xdotool xrandr; do
    if ! command -v $cmd &> /dev/null; then
        echo "WARNING: $cmd not found. Required at runtime for X11 window management."
    fi
done
echo ""

# Create/activate virtual environment
if [ ! -d "build_venv" ]; then
    echo "Creating build virtual environment..."
    python3 -m venv build_venv
fi
source build_venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null
pip install pyinstaller > /dev/null
echo "✓ Dependencies installed"
echo ""

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist AppDir *.AppImage
echo "✓ Clean complete"
echo ""

# Build with PyInstaller
echo "Building with PyInstaller..."
pyinstaller argus-overview.spec --noconfirm
echo "✓ PyInstaller build complete"
echo ""

# Download appimagetool if not present
if [ ! -f "appimagetool-x86_64.AppImage" ]; then
    echo "Downloading appimagetool..."
    wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x appimagetool-x86_64.AppImage
    echo "✓ appimagetool downloaded"
fi
echo ""

# Create AppDir structure
echo "Creating AppDir structure..."
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps
mkdir -p AppDir/usr/share/icons/hicolor/128x128/apps
mkdir -p AppDir/usr/share/icons/hicolor/64x64/apps

# Copy built application
cp -r dist/Argus-Overview/* AppDir/usr/bin/

# Copy icons
if [ -f "assets/icon.png" ]; then
    cp assets/icon.png AppDir/argus-overview.png
    cp assets/icon.png AppDir/usr/share/icons/hicolor/256x256/apps/argus-overview.png
fi
if [ -f "assets/icon_128.png" ]; then
    cp assets/icon_128.png AppDir/usr/share/icons/hicolor/128x128/apps/argus-overview.png
fi
if [ -f "assets/icon_64.png" ]; then
    cp assets/icon_64.png AppDir/usr/share/icons/hicolor/64x64/apps/argus-overview.png
fi

# Create desktop file
cat > AppDir/argus-overview.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Argus Overview
Comment=Professional Multi-Boxing Tool for EVE Online
Exec=Argus-Overview
Icon=argus-overview
Categories=Utility;Game;
Keywords=eve;online;multibox;preview;argus;overview;
Terminal=false
StartupWMClass=Argus Overview
EOF

cp AppDir/argus-overview.desktop AppDir/usr/share/applications/

# Create AppRun
cat > AppDir/AppRun << 'APPRUN'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/bin:${LD_LIBRARY_PATH}"
export QT_PLUGIN_PATH="${HERE}/usr/bin/PySide6/Qt/plugins"
export QT_QPA_PLATFORM_PLUGIN_PATH="${HERE}/usr/bin/PySide6/Qt/plugins/platforms"
exec "${HERE}/usr/bin/Argus-Overview" "$@"
APPRUN
chmod +x AppDir/AppRun

echo "✓ AppDir structure created"
echo ""

# Build AppImage
echo "Building AppImage..."
# Use APPIMAGE_EXTRACT_AND_RUN to avoid FUSE dependency on build systems
ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 ./appimagetool-x86_64.AppImage AppDir "Argus-Overview-${VERSION}-x86_64.AppImage"
echo ""

# Cleanup
deactivate 2>/dev/null || true

echo "================================================================"
echo "Build Complete!"
echo "================================================================"
echo ""
echo "AppImage created: Argus-Overview-${VERSION}-x86_64.AppImage"
echo ""
echo "To run:"
echo "  chmod +x Argus-Overview-${VERSION}-x86_64.AppImage"
echo "  ./Argus-Overview-${VERSION}-x86_64.AppImage"
echo ""
echo "To distribute:"
echo "  - Upload to GitHub Releases"
echo "  - Share the .AppImage file directly"
echo ""
