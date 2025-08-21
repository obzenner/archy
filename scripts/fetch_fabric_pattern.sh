#!/bin/bash

# Fetch Fabric pattern from GitHub
# Usage: fetch_fabric_pattern.sh <pattern_name>

set -euo pipefail

PATTERN_NAME="${1:-}"

# Validate input
if [ -z "$PATTERN_NAME" ]; then
    echo '{"error": "pattern_name is required"}' >&2
    exit 1
fi

# Check if curl is available
if ! command -v curl >/dev/null 2>&1; then
    echo '{"error": "curl is required but not installed"}' >&2
    exit 1
fi

# Fabric GitHub repository URL
FABRIC_BASE_URL="https://raw.githubusercontent.com/danielmiessler/Fabric/main/data/patterns"
PATTERN_URL="$FABRIC_BASE_URL/$PATTERN_NAME"

# Try to fetch system.md first (main pattern file)
SYSTEM_CONTENT=""
SYSTEM_URL="$PATTERN_URL/system.md"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$SYSTEM_URL")

if [ "$HTTP_CODE" = "200" ]; then
    SYSTEM_CONTENT=$(curl -s "$SYSTEM_URL")
fi

# Try to fetch user.md (user instructions)
USER_CONTENT=""
USER_URL="$PATTERN_URL/user.md"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$USER_URL")

if [ "$HTTP_CODE" = "200" ]; then
    USER_CONTENT=$(curl -s "$USER_URL")
fi

# Check if we got any content
if [ -z "$SYSTEM_CONTENT" ] && [ -z "$USER_CONTENT" ]; then
    echo '{"error": "pattern not found or unable to fetch"}' >&2
    exit 1
fi

# Output JSON result
cat << EOF
{
    "success": true,
    "pattern_name": "$PATTERN_NAME",
    "system_content": $(echo "$SYSTEM_CONTENT" | jq -Rs .),
    "user_content": $(echo "$USER_CONTENT" | jq -Rs .),
    "system_url": "$SYSTEM_URL",
    "user_url": "$USER_URL"
}
EOF
