#!/bin/bash

# Interactive Fabric pattern fetcher
# Called by: make fetch-pattern

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}Fabric Pattern Fetcher${NC}"
echo "========================="
echo ""
echo "Fetches Fabric AI patterns from GitHub for custom prompts"
echo ""
echo "Popular patterns:"
echo "  create_design_document          - C4 architecture docs"
echo "  update_architecture_diagram     - Update existing docs" 
echo "  analyze_code_structure          - Code analysis"
echo "  create_summary                  - Project summaries"
echo ""

read -p "Pattern name: " PATTERN_NAME

if [ -z "$PATTERN_NAME" ]; then
    echo -e "${RED}ERROR: Pattern name is required${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Fetching pattern: $PATTERN_NAME${NC}"

# Find the scripts directory (assuming this script is in cli/ and scripts/ is at same level)
SCRIPT_DIR="$(cd "$(dirname "$0")/../scripts" && pwd)"

"$SCRIPT_DIR/fetch_fabric_pattern.sh" "$PATTERN_NAME"
