#!/bin/bash
# Configuration
INSTALL_DIR="$HOME/.local/lib/ibus-lekhika"
COMPONENT_DIR="$HOME/.local/share/ibus/component"
DATA_DIR="$INSTALL_DIR/data"
ICONS_DIR="$HOME/.local/share/ibus-lekhika/icons"
CORE_REPO="https://github.com/khumnath/liblekhika.git"

# Build environment (the "kitchen")
KITCHEN_DIR="./kitchen"
CORE_DIR="$KITCHEN_DIR/liblekhika"

echo "=== IBus Lekhika: Build & Install System ==="

# 1. System Detection & Dependencies
echo "Step 1: Detecting system and checking dependencies..."

# Source OS information
if [ -f /etc/os-release ]; then
    . /etc/os-release
else
    echo "Error: Cannot detect OS distribution (/etc/os-release missing)."
    exit 1
fi

case "$ID" in
    ubuntu|debian|linuxmint|pop)
        DISTRO="debian"
        PKGINSTALL="sudo apt-get install -y"
        PKGUPDATE="sudo apt-get update"
        CHECK_CMD="dpkg -s"
        DEPS="git cmake build-essential pkg-config libicu-dev libsqlite3-dev python3-gi python3-gi-cairo ibus im-config wget"
        ;;
    fedora)
        DISTRO="fedora"
        PKGINSTALL="sudo dnf install -y"
        PKGUPDATE="sudo dnf check-update"
        CHECK_CMD="rpm -q"
        DEPS="git cmake gcc-c++ pkgconf-pkg-config libicu-devel libsqlite3-devel python3-gobject ibus imsettings wget"
        ;;
    arch)
        DISTRO="arch"
        PKGINSTALL="sudo pacman -S --noconfirm"
        PKGUPDATE="sudo pacman -Sy"
        CHECK_CMD="pacman -Qi"
        DEPS="git cmake gcc pkgconf icu sqlite python-gobject ibus wget"
        ;;
    *)
        # Fallback for ID_LIKE
        if [[ "$ID_LIKE" == *"debian"* ]]; then
            DISTRO="debian"
            PKGINSTALL="sudo apt-get install -y"
            PKGUPDATE="sudo apt-get update"
            CHECK_CMD="dpkg -s"
            DEPS="git cmake build-essential pkg-config libicu-dev libsqlite3-dev python3-gi python3-gi-cairo ibus im-config wget"
        else
            echo "Warning: Unsupported distribution ($ID). Proceeding with manual dependency management."
            DISTRO="unknown"
        fi
        ;;
esac

if [ "$DISTRO" != "unknown" ]; then
    MISSING_DEPS=""
    for dep in $DEPS; do
        if ! $CHECK_CMD "$dep" &> /dev/null; then
            MISSING_DEPS="$MISSING_DEPS $dep"
        fi
    done

    if [ -n "$MISSING_DEPS" ]; then
        echo "Detected $ID. Installing missing dependencies: $MISSING_DEPS"
        $PKGUPDATE || true
        $PKGINSTALL $MISSING_DEPS
    else
        echo "All system dependencies are already installed. Skipping installation."
    fi
fi

# 2. Configure Input Method Environment
echo "Step 2: Configuring IBus as the active input method..."
case "$DISTRO" in
    debian)
        if command -v im-config &> /dev/null; then
            im-config -n ibus
        fi
        ;;
    fedora)
        if command -v imsettings-switch &> /dev/null; then
            imsettings-switch -s ibus
        fi
        ;;
    arch)
        echo "Note: Arch Linux requires manual IM environment variables (GTK_IM_MODULE=ibus, etc.) if not already set."
        ;;
esac

# 3. Handle IBus Service
echo "Step 3: Ensuring IBus daemon is running..."
if ! pgrep -x "ibus-daemon" > /dev/null; then
    echo "Starting ibus-daemon..."
    ibus-daemon -drx
else
    echo "IBus daemon is already running."
fi

# 4. Setup Kitchen
echo "Step 4: Setting up build workspace (kitchen)..."
mkdir -p "$KITCHEN_DIR"

# 5. Fetch/Update liblekhika Core in Kitchen
if [ ! -d "$CORE_DIR" ]; then
    echo "Cloning liblekhika core into kitchen..."
    git clone "$CORE_REPO" "$CORE_DIR"
else
    echo "Updating liblekhika core in kitchen..."
    cd "$CORE_DIR" && git pull && cd ../..
fi

# 6. Build liblekhika Core
echo "Step 5: Building liblekhika core..."
mkdir -p "$CORE_DIR/build"
cd "$CORE_DIR/build"
cmake -DCMAKE_BUILD_TYPE=Release ..
make -j$(nproc)
cd ../../..

# 7. Build IBus Wrapper into Kitchen
echo "Step 6: Building IBus wrapper into kitchen..."
make clean BUILD_DIR="$KITCHEN_DIR"
make -j$(nproc) BUILD_DIR="$KITCHEN_DIR" CORE_DIR="$CORE_DIR"

# 8. Create directories
echo "Step 7: Creating installation directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$COMPONENT_DIR"
mkdir -p "$ICONS_DIR"
mkdir -p "$DATA_DIR"
mkdir -p "$HOME/.local/share/lekhika-core"

# 9. Copy Files
echo "Step 8: Deploying binaries and scripts..."
cp src/engine.py "$INSTALL_DIR/"
cp src/setup.py "$INSTALL_DIR/"
cp src/config_manager.py "$INSTALL_DIR/"
cp src/lekhika_wrap.py "$INSTALL_DIR/"
cp "$KITCHEN_DIR/ibus-lekhika.so" "$INSTALL_DIR/"
cp "$CORE_DIR/build/core/liblekhika.so."* "$INSTALL_DIR/" 2>/dev/null || true
cp "$CORE_DIR/build/core/liblekhika.so" "$INSTALL_DIR/"

cp -r data/* "$DATA_DIR/"
cp icons/lekhika.png "$ICONS_DIR/"

# 10. Download dictionary if missing
DICT_FILE="$HOME/.local/share/lekhika-core/lekhikadict.akshardb"
if [ ! -f "$DICT_FILE" ]; then
    echo "Downloading dictionary database..."
    wget -O "$DICT_FILE" https://github.com/khumnath/fcitx5-lekhika/releases/download/dictionary/lekhikadict.akshardb
fi

# 11. Update paths in lekhika.xml
sed "s|/home/computebox/.local/lib/ibus-lekhika/engine.py|$INSTALL_DIR/engine.py|g" src/lekhika.xml > "$COMPONENT_DIR/lekhika.xml"
sed -i "s|/home/computebox/.local/share/ibus-lekhika/icons/lekhika.png|$ICONS_DIR/lekhika.png|g" "$COMPONENT_DIR/lekhika.xml"

# 12. System Integration (Registration)
echo "Step 9: Registering component with IBus system path..."
SYSTEM_XML="/usr/share/ibus/component/lekhika.xml"
LOCAL_XML="$COMPONENT_DIR/lekhika.xml"

if [ ! -f "$SYSTEM_XML" ] || ! diff "$LOCAL_XML" "$SYSTEM_XML" > /dev/null; then
    echo "Updating system-wide IBus component registration (requires sudo)..."
    sudo cp "$LOCAL_XML" "$SYSTEM_XML"
else
    echo "System-wide registration is already up to date."
fi

# 13. Add Lekhika to IBus preload-engines
echo "Step 10: Adding Lekhika to IBus active engines..."
current_engines=$(gsettings get org.freedesktop.ibus.general preload-engines)
if [[ $current_engines != *"'lekhika'"* ]]; then
    if [[ $current_engines == "[]" || $current_engines == "@as []" ]]; then
        new_engines="['lekhika']"
    else
        new_engines="${current_engines%]*}, 'lekhika']"
    fi
    gsettings set org.freedesktop.ibus.general preload-engines "$new_engines"
    echo "Lekhika added to active engines."
else
    echo "Lekhika is already in active engines."
fi

# Finalize
chmod +x "$INSTALL_DIR/engine.py"
chmod +x "$INSTALL_DIR/setup.py"

echo "Step 11: Restarting IBus to load changes..."
ibus restart

echo "=== Installation successful! ==="
echo "Lekhika (Nepali) is now ready to use."
