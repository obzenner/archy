#!/bin/bash

# Universal architecture document generator
# Usage: arch.sh [--fresh] [project_path] [subfolder] [arch_file_name] [project_name]
# 
# Modes:
#   Default: Update architecture based on git changes (change-driven)
#   --fresh: Create fresh architecture from full codebase analysis
#
# If no project_path provided, defaults to current directory (.)

set -euo pipefail

# Create temp directory in system temp space with secure permissions
TEMP_DIR=$(mktemp -d -t archy-XXXXXX)
chmod 700 "$TEMP_DIR"  # Only owner can read/write/execute

# Trap to ensure cleanup even on errors/interrupts
cleanup_tmp() {
    if [ -d "$TEMP_DIR" ]; then
        echo -e "${CYAN}Cleaning up temporary files...${NC}"
        rm -rf "$TEMP_DIR"
        echo -e "${GREEN}✅ Cleanup complete${NC}"
    fi
}
trap cleanup_tmp EXIT INT TERM

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory early, before we change working directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Security Functions
validate_path() {
    local path="$1"
    local description="$2"
    
    # Check for directory traversal attempts
    if [[ "$path" =~ \.\./|\.\.\\ ]] || [[ "$path" =~ /\.\./|/\.\.\\ ]]; then
        echo -e "${RED}ERROR:${NC} Path traversal detected in $description: $path" >&2
        exit 1
    fi
    
    # Prevent access to sensitive system directories
    case "$path" in
        /etc/*|/sys/*|/proc/*|/dev/*|/boot/*|/root/*)
            echo -e "${RED}ERROR:${NC} Access to system directory not allowed: $path" >&2
            exit 1
            ;;
    esac
    
    # Ensure path is reasonable length (prevent buffer issues)
    if [[ ${#path} -gt 4096 ]]; then
        echo -e "${RED}ERROR:${NC} Path too long: $path" >&2
        exit 1
    fi
}

validate_filename() {
    local filename="$1"
    # Only allow safe filename characters
    if [[ ! "$filename" =~ ^[a-zA-Z0-9._-]+$ ]]; then
        echo -e "${RED}ERROR:${NC} Invalid characters in filename: $filename" >&2
        exit 1
    fi
}

validate_file_write() {
    local filepath="$1"
    local dir_path
    dir_path="$(dirname "$filepath")"
    
    # Check if directory is writable
    if [[ ! -w "$dir_path" ]]; then
        echo -e "${RED}ERROR:${NC} Cannot write to directory: $dir_path" >&2
        exit 1
    fi
    
    # If file exists, check if it's writable
    if [[ -f "$filepath" && ! -w "$filepath" ]]; then
        echo -e "${RED}ERROR:${NC} Cannot overwrite existing file: $filepath" >&2
        exit 1
    fi
    
    # Validate final path
    validate_path "$filepath" "output file"
}

# AI Backend Configuration with validation
ARCHY_AI_BACKEND="${ARCHY_AI_BACKEND:-cursor-agent}"
case "$ARCHY_AI_BACKEND" in
    "cursor-agent"|"fabric") ;;
    *)
        echo -e "${RED}ERROR:${NC} Invalid AI backend '$ARCHY_AI_BACKEND'. Supported: cursor-agent, fabric" >&2
        exit 1
        ;;
esac

# AI Backend abstraction function
call_ai_backend() {
    local prompt_file="$1"
    local output_file="$2"
    local force_flag="${3:-}"
    
    case "$ARCHY_AI_BACKEND" in
        "cursor-agent")
            echo -e "${CYAN}Using cursor-agent backend...${NC}"
            if [ "$force_flag" = "--force" ]; then
                cursor-agent -p --force --output-format json "$(cat "$prompt_file")" > "$output_file"
            else
                cursor-agent -p --output-format json "$(cat "$prompt_file")" > "$output_file"
            fi
            ;;
        "fabric")
            echo -e "${CYAN}Using fabric-ai backend...${NC}"
            local raw_output=$(echo "$(cat "$prompt_file")" | fabric-ai 2>/dev/null || echo "Error: Failed to call fabric-ai")
            jq -n --arg result "$raw_output" '{"result": $result}' > "$output_file"
            ;;
        *)
            echo -e "${RED}ERROR: Unknown AI backend '$ARCHY_AI_BACKEND'. Supported: cursor-agent, fabric${NC}"
            exit 1
            ;;
    esac
}

# Parse arguments
FRESH_MODE=false
if [[ "${1:-}" == "--fresh" ]]; then
    FRESH_MODE=true
    shift
fi

PROJECT_PATH="${1:-.}"
SUBFOLDER="${2:-}"
ARCH_FILE_NAME="${3:-arch.md}"
PROJECT_NAME="${4:-}"

# Security validations
validate_path "$PROJECT_PATH" "project path"
if [ -n "$SUBFOLDER" ]; then
    validate_path "$SUBFOLDER" "subfolder"
fi
validate_filename "$ARCH_FILE_NAME"

# Normalize project path to absolute early
PROJECT_PATH_ABS=$(cd "$PROJECT_PATH" 2>/dev/null && pwd) || {
    echo '{"error": "project_path does not exist"}' >&2
    exit 1
}

# Determine analysis target (absolute path)
if [ -n "$SUBFOLDER" ]; then
    ANALYSIS_TARGET_ABS="$PROJECT_PATH_ABS/$SUBFOLDER"
    if [ ! -d "$ANALYSIS_TARGET_ABS" ]; then
        echo '{"error": "subfolder does not exist"}' >&2
        exit 1
    fi
else
    ANALYSIS_TARGET_ABS="$PROJECT_PATH_ABS"
fi

# Find git repository root (search upward from analysis target)
GIT_ROOT="$ANALYSIS_TARGET_ABS"
while [ "$GIT_ROOT" != "/" ]; do
    if [ -d "$GIT_ROOT/.git" ]; then
        break
    fi
    GIT_ROOT=$(dirname "$GIT_ROOT")
done

if [ ! -d "$GIT_ROOT/.git" ]; then
    echo '{"error": "not a git repository (searched up to root)"}' >&2
    exit 1
fi

# Auto-detect project name if not provided
if [ -z "$PROJECT_NAME" ]; then
    PROJECT_NAME=$(basename "$ANALYSIS_TARGET_ABS")
fi

echo -e "${CYAN}Analyzing:${NC} $ANALYSIS_TARGET_ABS"
echo -e "${YELLOW}Git root:${NC} $GIT_ROOT"

# Change to git root for all git operations
cd "$GIT_ROOT"

# Preparing workspace
echo -e "${CYAN}Preparing workspace...${NC}"

# Construct architecture file path (always absolute)
ARCH_FILE="$ANALYSIS_TARGET_ABS/$ARCH_FILE_NAME"

if [ "$FRESH_MODE" = true ]; then
    echo -e "${GREEN}Mode:${NC} Fresh architecture analysis"
    echo -e "${CYAN}Loading architecture pattern...${NC}"
    
    # Fresh mode - analyze entire codebase like create_arch.sh
    PATTERN_FILE="$SCRIPT_DIR/../patterns/create_design_document_pattern.md"
    cp "$PATTERN_FILE" $TEMP_DIR/create_pattern.txt

    # Create input for new architecture document
    echo -e "${CYAN}Preparing full codebase analysis prompt...${NC}"
    {
        echo "Create a comprehensive architecture design document for:"
        echo ""
        echo "Project Name: $PROJECT_NAME"
        echo "Analysis Target: $ANALYSIS_TARGET_ABS"
        if [ -n "$SUBFOLDER" ]; then
            echo "Subfolder Focus: $SUBFOLDER"
        fi
        echo ""
        echo "Analyze the codebase structure and create appropriate C4 diagrams and documentation."
    } > $TEMP_DIR/create_input.md

    # Create full prompt
    {
        cat $TEMP_DIR/create_pattern.txt
        echo ""
        cat $TEMP_DIR/create_input.md
    } > $TEMP_DIR/full_prompt.txt

    # Create new architecture with AI backend
    echo -e "${MAGENTA}Generating fresh architecture document with ${ARCHY_AI_BACKEND}...${NC}"
    echo "   This may take a minute, analyzing entire codebase..."
    call_ai_backend $TEMP_DIR/full_prompt.txt $TEMP_DIR/cursor_response.json

    # Extract the result field from AI backend JSON response
    echo -e "${CYAN}Processing response...${NC}"
    if [ -s $TEMP_DIR/cursor_response.json ]; then
        jq -r '.result // ""' $TEMP_DIR/cursor_response.json > $TEMP_DIR/new_arch.md
    else
        echo "No response from AI backend" > $TEMP_DIR/new_arch.md
    fi

    # Clean up cursor thinking process - keep only from "## BUSINESS POSTURE" onwards
    echo -e "${CYAN}Cleaning up output format...${NC}"
    if grep -q "## BUSINESS POSTURE" $TEMP_DIR/new_arch.md; then
        sed -n "/## BUSINESS POSTURE/,\$p" $TEMP_DIR/new_arch.md > $TEMP_DIR/cleaned_arch.md
        mv $TEMP_DIR/cleaned_arch.md $TEMP_DIR/new_arch.md
    fi

    # Write the architecture document to the target location
    echo -e "${GREEN}Writing fresh architecture document...${NC}"
    validate_file_write "$ARCH_FILE"
    cp $TEMP_DIR/new_arch.md "$ARCH_FILE"

    ACTION="created"
    
else
    echo -e "${GREEN}Mode:${NC} Change-driven analysis"
    
    # Default mode - git change analysis
    
    # Calculate relative path for git filtering (using bash instead of Python)
    if [ "$ANALYSIS_TARGET_ABS" != "$GIT_ROOT" ]; then
        # Remove git root prefix to get relative path
        PATH_FILTER="${ANALYSIS_TARGET_ABS#$GIT_ROOT/}/"
    else
        PATH_FILTER=""
    fi

    # Detect default branch (main, master, etc.)
    DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
    if ! git show-ref --verify --quiet refs/heads/$DEFAULT_BRANCH; then
        # Try common default branches
        if git show-ref --verify --quiet refs/heads/main; then
            DEFAULT_BRANCH="main"
        elif git show-ref --verify --quiet refs/heads/master; then
            DEFAULT_BRANCH="master"
        else
            # Fallback to current branch or main
            DEFAULT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
        fi
    fi
    
    # Get git diff for code files only, filtered to project directory if specified
    echo -e "${YELLOW}Analyzing git changes from ${DEFAULT_BRANCH}...HEAD...${NC}"
    if [ -n "$PATH_FILTER" ]; then
        echo "   Focusing on: ${PATH_FILTER}*"
    fi
    git diff --no-color --stat $DEFAULT_BRANCH...HEAD -- "${PATH_FILTER}*.py" "${PATH_FILTER}*.ts" "${PATH_FILTER}*.js" "${PATH_FILTER}*.jsx" "${PATH_FILTER}*.tsx" "${PATH_FILTER}*.json" "${PATH_FILTER}*.yaml" "${PATH_FILTER}*.yml" > $TEMP_DIR/changes.diff
    echo "" >> $TEMP_DIR/changes.diff
    git diff --no-color $DEFAULT_BRANCH...HEAD -- "${PATH_FILTER}*.py" "${PATH_FILTER}*.ts" "${PATH_FILTER}*.js" "${PATH_FILTER}*.jsx" "${PATH_FILTER}*.tsx" "${PATH_FILTER}*.json" "${PATH_FILTER}*.yaml" "${PATH_FILTER}*.yml" >> $TEMP_DIR/changes.diff

    # Check if changes exist
    if [ ! -s $TEMP_DIR/changes.diff ]; then
        echo -e "${RED}ERROR:${NC} No changes found in current branch compared to $DEFAULT_BRANCH"
        echo "{\"error\": \"No changes found in current branch compared to $DEFAULT_BRANCH\"}"
        exit 1
    fi
    echo -e "${GREEN}Found git changes to analyze${NC}"

    # Create full prompt for git diff analysis
    echo -e "${CYAN}Preparing git diff analysis...${NC}"
    {
        echo "Summarize the following git changes for architecture analysis:"
        echo ""
        cat $TEMP_DIR/changes.diff
    } > $TEMP_DIR/full_prompt1.txt

    # Analyze changes with AI backend
    echo -e "${MAGENTA}Analyzing changes with ${ARCHY_AI_BACKEND}...${NC}"
    call_ai_backend $TEMP_DIR/full_prompt1.txt $TEMP_DIR/cursor_response.json

    # Extract the result field from AI backend JSON response
    echo -e "${CYAN}Processing change analysis...${NC}"
    if [ -s $TEMP_DIR/cursor_response.json ]; then
        jq -r '.result // ""' $TEMP_DIR/cursor_response.json > $TEMP_DIR/change_summary.md
    else
        echo "No response from AI backend" > $TEMP_DIR/change_summary.md
    fi

    # Check if architecture file exists to determine which pattern to use  
    if [ -f "$ARCH_FILE" ]; then
        echo -e "${BLUE}Found existing architecture file:${NC} $ARCH_FILE"
        echo -e "${GREEN}Will update existing documentation...${NC}"
        ACTION="updated"
        
        # Update existing architecture - use custom pattern if available
        CUSTOM_PATTERN="$SCRIPT_DIR/../patterns/update_arch_diagram_pattern.md"
        if [ -f "$CUSTOM_PATTERN" ]; then
            cp "$CUSTOM_PATTERN" $TEMP_DIR/arch_diagram_prompt.txt
        else
            echo '{"error": "Pattern file not found"}' >&2
            exit 1
        fi
        
        # Prepare combined architecture input for updating
        {
            echo "DESIGN DOCUMENT:"
            cat "$ARCH_FILE"
            echo ""
            echo "CODE CHANGES:"
            cat $TEMP_DIR/change_summary.md
        } > $TEMP_DIR/arch_input.md
        
    else
        echo -e "${BLUE}No existing architecture file found${NC}"
        echo -e "${GREEN}Will create new architecture document...${NC}"
        ACTION="created"
        
        # Create new architecture
        echo -e "${CYAN}Loading creation pattern...${NC}"
        PATTERN_FILE="$SCRIPT_DIR/../patterns/create_design_document_pattern.md"
        cp "$PATTERN_FILE" $TEMP_DIR/arch_diagram_prompt.txt
        
        # Prepare input for creating new architecture document
        {
            echo "Based on the following code changes, create a comprehensive architecture design document:"
            echo ""
            cat $TEMP_DIR/change_summary.md
            echo ""
            echo "The system is called '$PROJECT_NAME' and processes data."
        } > $TEMP_DIR/arch_input.md
    fi

    # Create full prompt for architecture update/creation
    {
        cat $TEMP_DIR/arch_diagram_prompt.txt
        echo ""
        cat $TEMP_DIR/arch_input.md
    } > $TEMP_DIR/full_prompt2.txt
    
    if [ "$ACTION" = "updated" ]; then
        echo -e "${MAGENTA}Updating architecture document with ${ARCHY_AI_BACKEND}...${NC}"
        echo "   This may take a minute, processing changes..."
    else
        echo -e "${MAGENTA}Creating new architecture document with ${ARCHY_AI_BACKEND}...${NC}"
        echo "   This may take a minute, analyzing changes..."
    fi
    
    call_ai_backend $TEMP_DIR/full_prompt2.txt $TEMP_DIR/cursor_arch_response.json "--force"
    
    # Extract the result field from AI backend JSON response
    if [ -s $TEMP_DIR/cursor_arch_response.json ]; then
        jq -r '.result // ""' $TEMP_DIR/cursor_arch_response.json > $TEMP_DIR/proposed_arch.md
    else
        if [ "$ACTION" = "updated" ]; then
            echo "No response from AI backend for architecture update" > $TEMP_DIR/proposed_arch.md
        else
            echo "No response from AI backend for architecture creation" > $TEMP_DIR/proposed_arch.md
        fi
    fi
    
    # Clean up cursor thinking process - keep only from "## BUSINESS POSTURE" onwards
    echo -e "${CYAN}Cleaning up output format...${NC}"
    if grep -q "## BUSINESS POSTURE" $TEMP_DIR/proposed_arch.md; then
        sed -n "/## BUSINESS POSTURE/,\$p" $TEMP_DIR/proposed_arch.md > $TEMP_DIR/cleaned_arch.md
        mv $TEMP_DIR/cleaned_arch.md $TEMP_DIR/proposed_arch.md
    fi
    
    # Write the architecture document to the target location
    if [ "$ACTION" = "updated" ]; then
        echo -e "${GREEN}Writing updated architecture document...${NC}"
    else
        echo -e "${GREEN}Writing new architecture document...${NC}"
    fi
    validate_file_write "$ARCH_FILE"
    cp $TEMP_DIR/proposed_arch.md "$ARCH_FILE"
fi

# Get file size for reporting
FILE_SIZE=$(wc -c < "$ARCH_FILE" | tr -d ' ')

if [ "$ACTION" = "updated" ]; then
    echo -e "${GREEN}SUCCESS:${NC} Architecture document updated successfully!"
else
    echo -e "${GREEN}SUCCESS:${NC} Architecture document created successfully!"
fi
echo "   File: $ARCH_FILE ($FILE_SIZE bytes)"
echo ""

# Output concise JSON result (no massive content fields!)
cat << EOF
{
    "success": true,
    "action": "$ACTION",
    "project_name": "$PROJECT_NAME",
    "file_path": "$ARCH_FILE",
    "file_size": $FILE_SIZE,
    "message": "Architecture document $ACTION at $ARCH_FILE",
    "fresh_mode": $FRESH_MODE,
    "changes_processed": $(if [ "$FRESH_MODE" = true ]; then echo false; else echo true; fi)
}
EOF
