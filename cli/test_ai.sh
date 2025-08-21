#!/bin/bash

# AI backend testing script
# Called by: make test-ai

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}Testing AI Backend${NC}"
echo "====================="
echo ""

BACKEND=${ARCHY_AI_BACKEND:-cursor-agent}
echo "Testing backend: $BACKEND"
echo ""

# Find the scripts directory (assuming this script is in cli/ and scripts/ is at same level)
SCRIPT_DIR="$(cd "$(dirname "$0")/../scripts" && pwd)"

"$SCRIPT_DIR/test_ai_backend.sh"

echo ""
echo -e "${BLUE}You can also test different backends:${NC}"
echo "   archy test -t fabric          # Test fabric"  
echo "   archy test -t cursor-agent    # Test cursor-agent"
echo "   archy test -t fabric \"Custom message\"   # Test with custom message"
