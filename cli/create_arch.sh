#!/bin/bash

# Interactive architecture document creator
# Called by: make create-arch

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}Architecture Document Creator${NC}"
echo "================================="
echo ""
echo "Path options (supports absolute and relative paths):"
echo "  . or [Enter]              - Current directory (default)"
echo "  ../api                    - Relative: API service directory"
echo "  ../app                    - Relative: Frontend app directory"
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
read -p "Project name (optional, press Enter for auto-detect): " PROJECT_NAME

echo ""
echo -e "${GREEN}Creating architecture document...${NC}"
echo "   Project: $PROJECT_PATH"
if [ -n "$SUBFOLDER" ]; then echo "   Subfolder: $SUBFOLDER"; fi
echo "   Output: $ARCH_FILE"
if [ -n "$PROJECT_NAME" ]; then echo "   Name: $PROJECT_NAME"; fi
echo ""

# Find the scripts directory (assuming this script is in cli/ and scripts/ is at same level)
SCRIPT_DIR="$(cd "$(dirname "$0")/../scripts" && pwd)"

if [ -n "$SUBFOLDER" ] && [ -n "$PROJECT_NAME" ]; then
    "$SCRIPT_DIR/arch.sh" --fresh "$PROJECT_PATH" "$SUBFOLDER" "$ARCH_FILE" "$PROJECT_NAME"
elif [ -n "$SUBFOLDER" ]; then
    "$SCRIPT_DIR/arch.sh" --fresh "$PROJECT_PATH" "$SUBFOLDER" "$ARCH_FILE"
elif [ -n "$PROJECT_NAME" ]; then
    "$SCRIPT_DIR/arch.sh" --fresh "$PROJECT_PATH" "" "$ARCH_FILE" "$PROJECT_NAME"
else
    "$SCRIPT_DIR/arch.sh" --fresh "$PROJECT_PATH" "" "$ARCH_FILE"
fi
