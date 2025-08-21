#!/bin/bash

# CLI uninstaller script
# Called by: make uninstall-cli

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}Removing archy CLI installation...${NC}"
echo ""

REMOVED=false

for location in "$HOME/.local/bin/archy" "/usr/local/bin/archy" "/usr/bin/archy"; do
    if [ -L "$location" ] || [ -f "$location" ]; then
        echo -e "${BLUE}Found: $location${NC}"
        if [ "$location" = "/usr/local/bin/archy" ] || [ "$location" = "/usr/bin/archy" ]; then
            echo "   Removing system installation (may need sudo)..."
            sudo rm -f "$location" && echo -e "${GREEN}Removed: $location${NC}" || echo -e "${RED}Failed to remove: $location${NC}"
        else
            rm -f "$location" && echo -e "${GREEN}Removed: $location${NC}" || echo -e "${RED}Failed to remove: $location${NC}"
        fi
        REMOVED=true
    fi
done

if [ "$REMOVED" = "false" ]; then
    echo -e "${BLUE}No archy installations found in common locations:${NC}"
    echo "   - ~/.local/bin/archy"
    echo "   - /usr/local/bin/archy"
    echo "   - /usr/bin/archy"
    echo ""
    echo -e "${YELLOW}If installed elsewhere, remove manually:${NC}"
    echo "   which archy  # Find location"
    echo "   rm \$(which archy)  # Remove it"
else
    echo ""
    echo -e "${GREEN}Archy CLI uninstall complete!${NC}"
fi
