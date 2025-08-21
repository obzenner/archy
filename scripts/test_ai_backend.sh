#!/bin/bash

# test_ai_backend.sh: Simple AI backend test script
# Usage: ./test_ai_backend.sh [message]
# Tests cursor-agent or ollama with a simple prompt

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# AI Backend Configuration
ARCHY_AI_BACKEND="${ARCHY_AI_BACKEND:-cursor-agent}"

# Test message
TEST_MESSAGE="${1:-Hello! Please respond with a brief greeting to confirm you are working correctly.}"

echo -e "${CYAN}🧪 Archy AI Backend Test${NC}"
echo -e "${YELLOW}Backend:${NC} $ARCHY_AI_BACKEND"
echo -e "${YELLOW}Test message:${NC} $TEST_MESSAGE"
echo ""

# Create temp directory in system temp space
TEMP_DIR=$(mktemp -d -t archy-test-XXXXXX)

# Cleanup function
cleanup_temp() {
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
}

# Trap to ensure cleanup even on errors/interrupts
trap cleanup_temp EXIT INT TERM

echo "$TEST_MESSAGE" > "$TEMP_DIR/test_prompt.txt"

# AI Backend abstraction function (copied from arch.sh)
call_ai_backend() {
    local prompt_file="$1"
    local output_file="$2"
    
    case "$ARCHY_AI_BACKEND" in
        "cursor-agent")
            echo -e "${CYAN}Calling cursor-agent...${NC}"
            cursor-agent -p --output-format json "$(cat "$prompt_file")" > "$output_file" 2>/dev/null || {
                echo -e "${RED}❌ cursor-agent failed${NC}"
                return 1
            }
            ;;
        "fabric")
            echo -e "${CYAN}Calling fabric-ai...${NC}"
            local raw_output=$(echo "$(cat "$prompt_file")" | fabric-ai 2>/dev/null || echo "Error: Failed to call fabric-ai")
            # Create JSON structure matching cursor-agent format
            jq -n --arg result "$raw_output" '{"result": $result}' > "$output_file"
            ;;
        *)
            echo -e "${RED}❌ Unknown AI backend '$ARCHY_AI_BACKEND'. Supported: cursor-agent, fabric${NC}"
            return 1
            ;;
    esac
}

# Test the backend
echo -e "${CYAN}Testing AI backend...${NC}"
if call_ai_backend "$TEMP_DIR/test_prompt.txt" "$TEMP_DIR/test_response.json"; then
    echo -e "${GREEN}✅ Backend responded successfully!${NC}"
    echo ""
    echo -e "${BLUE}Response:${NC}"
    echo "----------------------------------------"
    jq -r '.result // "No result found"' "$TEMP_DIR/test_response.json"
    echo "----------------------------------------"
    echo ""
    echo -e "${GREEN}🎉 AI backend test passed!${NC}"
else
    echo -e "${RED}❌ AI backend test failed!${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    case "$ARCHY_AI_BACKEND" in
        "cursor-agent")
            echo "- Make sure cursor-agent is installed and in PATH"
            echo "- Check: command -v cursor-agent"
            echo "- Install from: https://cursor.com/cli"
            ;;
        "fabric")
            echo "- Make sure fabric-ai is installed and in PATH"
            echo "- Install from: https://github.com/danielmiessler/Fabric"
            echo "- Check: command -v fabric-ai"
            echo "- Configure with: fabric-ai --setup"
            ;;
    esac
    exit 1
fi

echo -e "${CYAN}Cleaned up temporary files${NC}"
