#!/bin/bash

# Interactive architecture document updater
# Called by: make update-arch

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}Architecture Document Updater${NC}"
echo "================================"
echo ""
echo "This will analyze git changes and update existing arch.md"
echo ""
echo "Path options (supports absolute and relative paths):"
echo "  . or [Enter]              - Current directory (default)"
echo "  ../api                    - Relative: Update API service docs"  
echo "  ../app                    - Relative: Update frontend app docs"
echo "  /full/path/to/service     - Absolute: Any project directory"
echo ""

read -p "Project path: " PROJECT_PATH
PROJECT_PATH=${PROJECT_PATH:-.}

if [ ! -d "$PROJECT_PATH" ]; then
    echo -e "${RED}ERROR: Project path '$PROJECT_PATH' does not exist${NC}"
    exit 1
fi

read -p "Subfolder (optional, press Enter to skip): " SUBFOLDER
read -p "Architecture file name [arch.md]: " ARCH_FILE
ARCH_FILE=${ARCH_FILE:-arch.md}

echo ""
echo -e "${YELLOW}Checking for git changes...${NC}"
echo "   Project: $PROJECT_PATH"
if [ -n "$SUBFOLDER" ]; then echo "   Subfolder: $SUBFOLDER"; fi
echo "   File: $ARCH_FILE"
echo ""

# Find the scripts directory (assuming this script is in cli/ and scripts/ is at same level)
SCRIPT_DIR="$(cd "$(dirname "$0")/../scripts" && pwd)"

if [ -n "$SUBFOLDER" ]; then
    "$SCRIPT_DIR/arch.sh" "$PROJECT_PATH" "$SUBFOLDER" "$ARCH_FILE"
else
    "$SCRIPT_DIR/arch.sh" "$PROJECT_PATH" "" "$ARCH_FILE"
fi
