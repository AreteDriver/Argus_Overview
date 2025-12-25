#!/bin/bash
# EVE Overview Pro v2.1 Ultimate Edition - Installation Script

set -e

echo "================================================================"
echo "EVE Overview Pro v2.1 Ultimate Edition"
echo "Installation Script"
echo "================================================================"
echo ""

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Error: This application is designed for Linux only."
    exit 1
fi

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "Error: Python 3.8 or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi
echo "✓ Python $PYTHON_VERSION found"

# Check for system dependencies
echo ""
echo "Checking system dependencies..."

MISSING_DEPS=()

for cmd in wmctrl xdotool convert import xwd; do
    if ! command -v $cmd &> /dev/null; then
        MISSING_DEPS+=($cmd)
    else
        echo "✓ $cmd found"
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo ""
    echo "Missing system dependencies: ${MISSING_DEPS[@]}"
    echo ""
    echo "Please install them using your package manager:"
    echo ""
    
    if [ -f /etc/debian_version ]; then
        echo "  sudo apt-get install wmctrl xdotool imagemagick x11-apps"
    elif [ -f /etc/redhat-release ]; then
        echo "  sudo dnf install wmctrl xdotool ImageMagick xorg-x11-apps"
    elif [ -f /etc/arch-release ]; then
        echo "  sudo pacman -S wmctrl xdotool imagemagick xorg-xwd"
    else
        echo "  Install: wmctrl, xdotool, ImageMagick, x11-apps"
    fi
    echo ""
    
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create installation directory
INSTALL_DIR="$HOME/eve-overview-pro"
echo ""
echo "Creating installation directory: $INSTALL_DIR"

if [ -d "$INSTALL_DIR" ]; then
    echo "Installation directory already exists."
    read -p "Replace it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
    else
        echo "Installation cancelled."
        exit 0
    fi
fi

mkdir -p "$INSTALL_DIR"
echo "✓ Installation directory created"

# Copy files
echo "Copying files..."
cp -r src "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"
cp README.md "$INSTALL_DIR/"
echo "✓ Files copied"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
cd "$INSTALL_DIR"
python3 -m venv venv
echo "✓ Virtual environment created"

# Activate and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Create launcher script
echo ""
echo "Creating launcher script..."
cat > "$INSTALL_DIR/run.sh" << 'RUNNER'
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
source venv/bin/activate
python src/main.py "$@"
RUNNER

chmod +x "$INSTALL_DIR/run.sh"
echo "✓ Launcher script created"

# Create desktop entry
echo "Creating desktop entry..."
mkdir -p ~/.local/share/applications

cat > ~/.local/share/applications/eve-overview-pro.desktop << DESKTOP
[Desktop Entry]
Version=2.1
Type=Application
Name=EVE Overview Pro
Comment=Multi-window preview tool for EVE Online
Exec=$INSTALL_DIR/run.sh
Icon=utilities-system-monitor
Terminal=false
Categories=Utility;Game;
Keywords=eve;online;multibox;preview;
DESKTOP

echo "✓ Desktop entry created"

# Create config directory
echo "Creating configuration directory..."
mkdir -p ~/.config/eve-overview-pro/profiles
mkdir -p ~/.config/eve-overview-pro/layouts
echo "✓ Configuration directory created"

echo ""
echo "================================================================"
echo "Installation Complete!"
echo "================================================================"
echo ""
echo "EVE Overview Pro v2.1 has been installed to:"
echo "  $INSTALL_DIR"
echo ""
echo "To run EVE Overview Pro:"
echo "  $INSTALL_DIR/run.sh"
echo ""
echo "Or find it in your applications menu!"
echo ""
echo "Quick Start:"
echo "  1. Launch EVE clients"
echo "  2. Run EVE Overview Pro"
echo "  3. Go to Characters & Teams tab"
echo "  4. Add your characters and create teams"
echo "  5. Use Layouts tab to save window arrangements"
echo "  6. Use Settings Sync tab to copy settings between characters"
echo ""
echo "Fly safe, capsuleer! o7"
echo ""
