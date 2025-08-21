#!/bin/bash

# Interactive CLI setup script
# Called by: make setup-cli

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}Archy CLI Setup${NC}"
echo "=================="
echo ""
echo "This will install 'archy' command globally on your system."
echo ""
echo "Install locations:"
echo "  1) ~/.local/bin/archy        (recommended - user only)"
echo "  2) /usr/local/bin/archy      (system-wide, requires sudo)"
echo "  3) Custom location"
echo ""

read -p "Choose [1], 2, or 3: " CHOICE
CHOICE=${CHOICE:-1}

case "$CHOICE" in
    "1")
        INSTALL_DIR="$HOME/.local/bin"
        echo "Installing to: $INSTALL_DIR"
        ;;
    "2")
        INSTALL_DIR="/usr/local/bin"
        echo "Installing to: $INSTALL_DIR (will prompt for sudo)"
        ;;
    "3")
        read -p "Enter custom path: " INSTALL_DIR
        echo "Installing to: $INSTALL_DIR"
        ;;
    *)
        echo "Invalid choice, using default: ~/.local/bin"
        INSTALL_DIR="$HOME/.local/bin"
        ;;
esac

echo ""
echo -e "${CYAN}Setting up installation...${NC}"

# Get the project root directory (assuming this script is in cli/)
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Setting executable permissions on scripts..."
chmod +x "$PROJECT_DIR/scripts/"*.sh "$PROJECT_DIR/scripts/archy" "$PROJECT_DIR/cli/"*.sh

mkdir -p "$INSTALL_DIR" 2>/dev/null || sudo mkdir -p "$INSTALL_DIR"

if [ "$INSTALL_DIR" = "/usr/local/bin" ]; then
    sudo ln -sf "$PROJECT_DIR/scripts/archy" "$INSTALL_DIR/archy"
else
    ln -sf "$PROJECT_DIR/scripts/archy" "$INSTALL_DIR/archy"
fi

echo -e "${GREEN}archy installed to $INSTALL_DIR/archy${NC}"
echo ""

if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
    echo -e "${YELLOW}Add $INSTALL_DIR to your PATH:${NC}"
    if [ "$INSTALL_DIR" = "$HOME/.local/bin" ]; then
        echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc"
    else
        echo "  echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.zshrc"
    fi
    echo "  source ~/.zshrc"
    echo ""
fi

echo -e "${GREEN}Setup complete! Usage:${NC}"
echo "  archy fresh    - Create fresh architecture doc"
echo "  archy update   - Update from git changes"
echo "  archy          - Default: update mode"
echo "  archy --help   - Show help"
