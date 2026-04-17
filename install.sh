#!/bin/bash
# IBus Lekhika: Remote Installer Script
# This script clones the repository and executes the full build/install process.

REPO_URL="https://github.com/khumnath/ibus-lekhika.git"
INSTALL_DIR="ibus-lekhika-setup"

echo "=== IBus Lekhika: Remote Setup Utility ==="

# 1. Check for Git
if ! command -v git &> /dev/null; then
    echo "Error: Git is not installed. Please install git first."
    exit 1
fi

# 2. Clone the repository
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing setup directory..."
    cd "$INSTALL_DIR" && git pull && cd ..
else
    echo "Cloning repository from $REPO_URL..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# 3. Execute the Build and Install script
echo "Launching the build and installation process..."
cd "$INSTALL_DIR"
chmod +x build-and-install.sh
./build-and-install.sh

echo ""
echo "Remote installation process finished."
