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

#================================================================
# CONFIGURATION
#================================================================
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
readonly DEFAULT_ARCH_FILENAME="arch.md"
readonly DEFAULT_AI_BACKEND="cursor-agent"
readonly MAX_PATH_LENGTH=4096
readonly TEMP_DIR_PREFIX="archy"

# Supported AI backends
readonly SUPPORTED_BACKENDS=("cursor-agent" "fabric")

# File extensions to analyze for git changes
readonly CODE_EXTENSIONS=(
    "*.py" "*.ts" "*.js" "*.jsx" "*.tsx" 
    "*.json" "*.yaml" "*.yml"
)

# System directories that should never be accessed (security)
readonly BLOCKED_SYSTEM_DIRS=(
    "/etc" "/sys" "/proc" "/dev" "/boot" "/root"
)

# Pattern template files
readonly CREATE_PATTERN_TEMPLATE="$SCRIPT_DIR/../patterns/create_design_document_pattern.md"
readonly UPDATE_PATTERN_TEMPLATE="$SCRIPT_DIR/../patterns/update_arch_diagram_pattern.md"

#================================================================
# GLOBAL VARIABLES
#================================================================
# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly MAGENTA='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Working directory for temporary files (set in setup_work_directory)
WORK_DIR=""

# Script execution mode and parameters (set in parse_arguments)
FRESH_MODE=false
PROJECT_PATH=""
SUBFOLDER=""
ARCH_FILE_NAME=""
PROJECT_NAME=""

# Derived paths (set in setup_paths)
PROJECT_PATH_ABS=""
ANALYSIS_TARGET_ABS=""
GIT_ROOT=""
ARCH_FILE_PATH=""

# Git information (set in setup_git_context)
DEFAULT_BRANCH=""
PATH_FILTER=""

# Action performed (set during execution)
ACTION_PERFORMED=""

#================================================================
# UTILITY FUNCTIONS
#================================================================

# Print error message and exit with specified code
error_exit() {
    local message="$1"
    local exit_code="${2:-1}"
    
    echo -e "${RED}ERROR:${NC} $message" >&2
    cleanup_and_exit "$exit_code"
}

# Print informational message with consistent formatting
info() {
    local message="$1"
    echo -e "${CYAN}$message${NC}"
}

# Print success message with consistent formatting
success() {
    local message="$1"
    echo -e "${GREEN}$message${NC}"
}

# Print warning message with consistent formatting
warn() {
    local message="$1"
    echo -e "${YELLOW}$message${NC}"
}

#================================================================
# CLEANUP AND SETUP FUNCTIONS
#================================================================

# Clean up temporary directory and exit
cleanup_and_exit() {
    local exit_code="${1:-0}"
    
    if [[ -d "$WORK_DIR" ]]; then
        info "Cleaning up temporary files..."
        rm -rf "$WORK_DIR"
        success "✅ Cleanup complete"
    fi
    
    exit "$exit_code"
}

# Set up secure temporary working directory
setup_work_directory() {
    WORK_DIR=$(mktemp -d -t "${TEMP_DIR_PREFIX}-XXXXXX")
    chmod 700 "$WORK_DIR"  # Only owner can read/write/execute
    
    # Ensure cleanup on script exit, interrupt, or termination
    trap 'cleanup_and_exit $?' EXIT INT TERM
}

#================================================================
# SECURITY VALIDATION FUNCTIONS
#================================================================

# Security check: Prevent path traversal attacks and system directory access
validate_path_security() {
    local path="$1"
    local description="$2"
    
    # Check for directory traversal attempts (e.g., ../../../etc/passwd)
    if [[ "$path" =~ \.\./|\.\.\\ ]] || [[ "$path" =~ /\.\./|/\.\.\\ ]]; then
        error_exit "Path traversal detected in $description: $path"
    fi
    
    # Prevent access to sensitive system directories
    local blocked_path
    for blocked_path in "${BLOCKED_SYSTEM_DIRS[@]}"; do
        if [[ "$path" == "$blocked_path"/* ]]; then
            error_exit "Access to system directory not allowed: $path"
        fi
    done
    
    # Ensure path length is reasonable (prevent buffer overflow attacks)
    if [[ ${#path} -gt $MAX_PATH_LENGTH ]]; then
        error_exit "Path too long (>${MAX_PATH_LENGTH} chars): $path"
    fi
}

# Validate filename contains only safe characters
validate_filename_safety() {
    local filename="$1"
    
    # Only allow alphanumeric characters, dots, underscores, and hyphens
    if [[ ! "$filename" =~ ^[a-zA-Z0-9._-]+$ ]]; then
        error_exit "Invalid characters in filename: $filename"
    fi
}

# Ensure we can write to the specified file location
validate_file_write_permissions() {
    local filepath="$1"
    local dir_path
    dir_path="$(dirname "$filepath")"
    
    # Check if directory is writable
    if [[ ! -w "$dir_path" ]]; then
        error_exit "Cannot write to directory: $dir_path"
    fi
    
    # If file exists, check if it's writable
    if [[ -f "$filepath" && ! -w "$filepath" ]]; then
        error_exit "Cannot overwrite existing file: $filepath"
    fi
    
    # Run security validation on the final path
    validate_path_security "$filepath" "output file"
}

# Validate AI backend is supported
validate_ai_backend() {
    local backend="$1"
    
    local supported_backend
    for supported_backend in "${SUPPORTED_BACKENDS[@]}"; do
        if [[ "$backend" == "$supported_backend" ]]; then
            return 0
        fi
    done
    
    error_exit "Invalid AI backend '$backend'. Supported: ${SUPPORTED_BACKENDS[*]}"
}

#================================================================
# AI BACKEND INTEGRATION FUNCTIONS
#================================================================

# Get the configured AI backend (from environment or default)
get_ai_backend() {
    local backend="${ARCHY_AI_BACKEND:-$DEFAULT_AI_BACKEND}"
    validate_ai_backend "$backend"
    echo "$backend"
}

# Generate content using cursor-agent backend
generate_with_cursor_agent() {
    local prompt_file="$1"
    local output_file="$2"
    local force_flag="${3:-}"
    
    info "Using cursor-agent backend..."
    
    if [[ "$force_flag" == "--force" ]]; then
        cursor-agent -p --force --output-format json "$(cat "$prompt_file")" > "$output_file"
    else
        cursor-agent -p --output-format json "$(cat "$prompt_file")" > "$output_file"
    fi
}

# Generate content using fabric backend
generate_with_fabric() {
    local prompt_file="$1"
    local output_file="$2"
    
    info "Using fabric-ai backend..."
    
    # Call fabric-ai and wrap output in JSON format for consistent processing
    local raw_output
    raw_output=$(echo "$(cat "$prompt_file")" | fabric-ai 2>/dev/null || echo "Error: Failed to call fabric-ai")
    jq -n --arg result "$raw_output" '{"result": $result}' > "$output_file"
}

# Main AI backend abstraction - routes to appropriate backend
invoke_ai_service() {
    local prompt_file="$1"
    local output_file="$2"
    local force_flag="${3:-}"
    local backend
    
    backend=$(get_ai_backend)
    
    case "$backend" in
        "cursor-agent")
            generate_with_cursor_agent "$prompt_file" "$output_file" "$force_flag"
            ;;
        "fabric")
            generate_with_fabric "$prompt_file" "$output_file"
            ;;
        *)
            error_exit "Unknown AI backend '$backend'. This should not happen."
            ;;
    esac
}

# Extract and clean the AI response from JSON output
process_ai_response() {
    local response_file="$1"
    local output_file="$2"
    
    if [[ -s "$response_file" ]]; then
        jq -r '.result // ""' "$response_file" > "$output_file"
    else
        echo "No response from AI backend" > "$output_file"
    fi
}

# Clean up AI response by extracting only the architecture content
clean_architecture_output() {
    local input_file="$1"
    local output_file="$2"
    
    info "Cleaning up output format..."
    
    # Keep only content from "## BUSINESS POSTURE" onwards (removes AI thinking process)
    if grep -q "## BUSINESS POSTURE" "$input_file"; then
        sed -n "/## BUSINESS POSTURE/,\$p" "$input_file" > "$output_file"
    else
        cp "$input_file" "$output_file"
    fi
}

#================================================================
# ARGUMENT PARSING AND SETUP FUNCTIONS  
#================================================================

# Parse command line arguments and set global variables
parse_arguments() {
    # Check for fresh mode flag
    if [[ "${1:-}" == "--fresh" ]]; then
        FRESH_MODE=true
        shift
    fi

    # Set parameter defaults and parse positional arguments
    PROJECT_PATH="${1:-.}"
    SUBFOLDER="${2:-}"
    ARCH_FILE_NAME="${3:-$DEFAULT_ARCH_FILENAME}"
    PROJECT_NAME="${4:-}"
}

# Validate all user inputs for security and correctness
validate_all_inputs() {
    validate_path_security "$PROJECT_PATH" "project path"
    
    if [[ -n "$SUBFOLDER" ]]; then
        validate_path_security "$SUBFOLDER" "subfolder"
    fi
    
    validate_filename_safety "$ARCH_FILE_NAME"
}

# Set up all required paths as absolute paths
setup_paths() {
    # Convert project path to absolute path and verify it exists
    PROJECT_PATH_ABS=$(cd "$PROJECT_PATH" 2>/dev/null && pwd) || {
        error_exit "Project path does not exist: $PROJECT_PATH"
    }

    # Determine analysis target directory (may be subfolder or entire project)
    if [[ -n "$SUBFOLDER" ]]; then
        ANALYSIS_TARGET_ABS="$PROJECT_PATH_ABS/$SUBFOLDER"
        if [[ ! -d "$ANALYSIS_TARGET_ABS" ]]; then
            error_exit "Subfolder does not exist: $SUBFOLDER"
        fi
    else
        ANALYSIS_TARGET_ABS="$PROJECT_PATH_ABS"
    fi

    # Auto-detect project name if not provided
    if [[ -z "$PROJECT_NAME" ]]; then
        PROJECT_NAME=$(basename "$ANALYSIS_TARGET_ABS")
    fi

    # Construct final architecture file path
    ARCH_FILE_PATH="$ANALYSIS_TARGET_ABS/$ARCH_FILE_NAME"
    
    # Validate we can write to the target location
    validate_file_write_permissions "$ARCH_FILE_PATH"
}

# Find git repository and set up git context
setup_git_context() {
    # Search upward from analysis target to find git repository root
    GIT_ROOT="$ANALYSIS_TARGET_ABS"
    while [[ "$GIT_ROOT" != "/" ]]; do
        if [[ -d "$GIT_ROOT/.git" ]]; then
            break
        fi
        GIT_ROOT=$(dirname "$GIT_ROOT")
    done

    if [[ ! -d "$GIT_ROOT/.git" ]]; then
        error_exit "Not a git repository (searched up to root from $ANALYSIS_TARGET_ABS)"
    fi

    # Set up path filter for git operations (if analyzing subfolder)
    if [[ "$ANALYSIS_TARGET_ABS" != "$GIT_ROOT" ]]; then
        # Remove git root prefix to get relative path for git filtering
        PATH_FILTER="${ANALYSIS_TARGET_ABS#$GIT_ROOT/}/"
    else
        PATH_FILTER=""
    fi

    # Detect the default branch (main, master, etc.)
    DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
    
    if ! git show-ref --verify --quiet refs/heads/$DEFAULT_BRANCH; then
        # Try common default branches
        if git show-ref --verify --quiet refs/heads/main; then
            DEFAULT_BRANCH="main"
        elif git show-ref --verify --quiet refs/heads/master; then
            DEFAULT_BRANCH="master"
        else
            # Fallback to current branch
            DEFAULT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
        fi
    fi

    # Change to git root for all git operations
    cd "$GIT_ROOT" || error_exit "Cannot change to git root: $GIT_ROOT"
}

# Display setup information to user
show_analysis_info() {
    info "Analyzing: $ANALYSIS_TARGET_ABS"
    warn "Git root: $GIT_ROOT"
    
    if [[ -n "$PATH_FILTER" ]]; then
        info "Focusing on: ${PATH_FILTER}*"
    fi
}

# Complete initial setup process
setup_environment() {
    setup_work_directory
    parse_arguments "$@"
    validate_all_inputs
    setup_paths
    setup_git_context
    show_analysis_info
    info "Preparing workspace..."
}

#================================================================
# GIT OPERATIONS FUNCTIONS
#================================================================

# Extract git changes for analysis, filtered to relevant file types
extract_git_changes() {
    local changes_file="$WORK_DIR/changes.diff"
    
    warn "Analyzing git changes from ${DEFAULT_BRANCH}...HEAD..."
    
    # Build file extension filters for git diff
    local extension_filters=()
    for ext in "${CODE_EXTENSIONS[@]}"; do
        extension_filters+=("${PATH_FILTER}$ext")
    done
    
    # Generate git diff with both stats and content
    git diff --no-color --stat "$DEFAULT_BRANCH...HEAD" -- "${extension_filters[@]}" > "$changes_file"
    echo "" >> "$changes_file"
    git diff --no-color "$DEFAULT_BRANCH...HEAD" -- "${extension_filters[@]}" >> "$changes_file"
    
    # Verify we found changes
    if [[ ! -s "$changes_file" ]]; then
        error_exit "No changes found in current branch compared to $DEFAULT_BRANCH"
    fi
    
    success "Found git changes to analyze"
    echo "$changes_file"
}

# Create analysis prompt from git changes  
create_change_analysis_prompt() {
    local changes_file="$1"
    local prompt_file="$WORK_DIR/change_analysis_prompt.txt"
    
    {
        echo "Summarize the following git changes for architecture analysis:"
        echo ""
        cat "$changes_file"
    } > "$prompt_file"
    
    echo "$prompt_file"
}

#================================================================
# ARCHITECTURE GENERATION FUNCTIONS  
#================================================================

# Generate fresh architecture document from complete codebase analysis
generate_fresh_architecture() {
    success "Mode: Fresh architecture analysis"
    info "Loading architecture pattern..."
    
    # Prepare pattern template
    local pattern_file="$WORK_DIR/create_pattern.txt"
    cp "$CREATE_PATTERN_TEMPLATE" "$pattern_file"

    # Create project analysis prompt
    local input_file="$WORK_DIR/create_input.md"
    {
        echo "Create a comprehensive architecture design document for:"
        echo ""
        echo "Project Name: $PROJECT_NAME"
        echo "Analysis Target: $ANALYSIS_TARGET_ABS"
        if [[ -n "$SUBFOLDER" ]]; then
            echo "Subfolder Focus: $SUBFOLDER"
        fi
        echo ""
        echo "Analyze the codebase structure and create appropriate C4 diagrams and documentation."
    } > "$input_file"

    # Combine pattern template with input
    local full_prompt="$WORK_DIR/full_prompt.txt"
    {
        cat "$pattern_file"
        echo ""
        cat "$input_file"
    } > "$full_prompt"

    # Generate architecture with AI
    local backend
    backend=$(get_ai_backend)
    echo -e "${MAGENTA}Generating fresh architecture document with $backend...${NC}"
    echo "   This may take a minute, analyzing entire codebase..."
    
    local response_file="$WORK_DIR/ai_response.json"
    invoke_ai_service "$full_prompt" "$response_file"

    # Process and clean the response
    local raw_output="$WORK_DIR/raw_arch.md"
    local cleaned_output="$WORK_DIR/cleaned_arch.md"
    
    info "Processing response..."
    process_ai_response "$response_file" "$raw_output"
    clean_architecture_output "$raw_output" "$cleaned_output"

    # Write final architecture document
    success "Writing fresh architecture document..."
    cp "$cleaned_output" "$ARCH_FILE_PATH"
    
    ACTION_PERFORMED="created"
}
# Update architecture based on git changes (create or update existing)
update_from_git_changes() {
    success "Mode: Change-driven analysis"
    
    # Extract and analyze git changes
    local changes_file
    changes_file=$(extract_git_changes)
    
    local change_prompt
    change_prompt=$(create_change_analysis_prompt "$changes_file")
    
    # Analyze changes with AI to get summary
    local backend
    backend=$(get_ai_backend)
    echo -e "${MAGENTA}Analyzing changes with $backend...${NC}"
    
    local change_response="$WORK_DIR/change_response.json"
    invoke_ai_service "$change_prompt" "$change_response"
    
    local change_summary="$WORK_DIR/change_summary.md"
    info "Processing change analysis..."
    process_ai_response "$change_response" "$change_summary"

    # Determine strategy: update existing or create new architecture
    if [[ -f "$ARCH_FILE_PATH" ]]; then
        update_existing_architecture "$change_summary"
    else
        create_architecture_from_changes "$change_summary"
    fi
}

# Update an existing architecture document with new changes
update_existing_architecture() {
    local change_summary="$1"
    
    echo -e "${BLUE}Found existing architecture file:${NC} $ARCH_FILE_PATH"
    success "Will update existing documentation..."
    
    # Prepare update pattern template
    local pattern_file="$WORK_DIR/update_pattern.txt"
    cp "$UPDATE_PATTERN_TEMPLATE" "$pattern_file"
    
    # Combine existing architecture with change summary
    local combined_input="$WORK_DIR/update_input.md"
    {
        echo "DESIGN DOCUMENT:"
        cat "$ARCH_FILE_PATH"
        echo ""
        echo "CODE CHANGES:"
        cat "$change_summary"
    } > "$combined_input"
    
    # Create full update prompt
    local update_prompt="$WORK_DIR/update_prompt.txt"
    {
        cat "$pattern_file"
        echo ""
        cat "$combined_input"
    } > "$update_prompt"
    
    # Generate updated architecture
    local backend
    backend=$(get_ai_backend)
    echo -e "${MAGENTA}Updating architecture document with $backend...${NC}"
    echo "   This may take a minute, processing changes..."
    
    local response_file="$WORK_DIR/update_response.json"
    invoke_ai_service "$update_prompt" "$response_file" "--force"
    
    # Process and save the updated architecture
    local raw_output="$WORK_DIR/raw_updated_arch.md"
    local cleaned_output="$WORK_DIR/cleaned_updated_arch.md"
    
    process_ai_response "$response_file" "$raw_output"
    clean_architecture_output "$raw_output" "$cleaned_output"
    
    success "Writing updated architecture document..."
    cp "$cleaned_output" "$ARCH_FILE_PATH"
    
    ACTION_PERFORMED="updated"
}

# Create new architecture document from git changes
create_architecture_from_changes() {
    local change_summary="$1"
    
    echo -e "${BLUE}No existing architecture file found${NC}"
    success "Will create new architecture document..."
    
    # Prepare creation pattern template
    local pattern_file="$WORK_DIR/create_from_changes_pattern.txt"
    cp "$CREATE_PATTERN_TEMPLATE" "$pattern_file"
    
    # Create input for new architecture based on changes
    local input_file="$WORK_DIR/create_from_changes_input.md"
    {
        echo "Based on the following code changes, create a comprehensive architecture design document:"
        echo ""
        cat "$change_summary"
        echo ""
        echo "The system is called '$PROJECT_NAME' and processes data."
    } > "$input_file"
    
    # Create full creation prompt
    local create_prompt="$WORK_DIR/create_from_changes_prompt.txt"
    {
        cat "$pattern_file"
        echo ""
        cat "$input_file"
    } > "$create_prompt"
    
    # Generate new architecture
    local backend
    backend=$(get_ai_backend)
    echo -e "${MAGENTA}Creating new architecture document with $backend...${NC}"
    echo "   This may take a minute, analyzing changes..."
    
    local response_file="$WORK_DIR/create_response.json"
    invoke_ai_service "$create_prompt" "$response_file" "--force"
    
    # Process and save the new architecture
    local raw_output="$WORK_DIR/raw_new_arch.md"
    local cleaned_output="$WORK_DIR/cleaned_new_arch.md"
    
    process_ai_response "$response_file" "$raw_output"
    clean_architecture_output "$raw_output" "$cleaned_output"
    
    success "Writing new architecture document..."
    cp "$cleaned_output" "$ARCH_FILE_PATH"
    
    ACTION_PERFORMED="created"
}

#================================================================
# OUTPUT AND REPORTING FUNCTIONS
#================================================================

# Generate final success report with file information
generate_final_report() {
    local file_size
    file_size=$(wc -c < "$ARCH_FILE_PATH" | tr -d ' ')

    # Display success message
    if [[ "$ACTION_PERFORMED" == "updated" ]]; then
        success "SUCCESS: Architecture document updated successfully!"
    else
        success "SUCCESS: Architecture document created successfully!"
    fi
    echo "   File: $ARCH_FILE_PATH ($file_size bytes)"
    echo ""

    # Output structured JSON result for programmatic use
    cat << EOF
{
    "success": true,
    "action": "$ACTION_PERFORMED",
    "project_name": "$PROJECT_NAME",
    "file_path": "$ARCH_FILE_PATH",
    "file_size": $file_size,
    "message": "Architecture document $ACTION_PERFORMED at $ARCH_FILE_PATH",
    "fresh_mode": $FRESH_MODE,
    "changes_processed": $(if [[ "$FRESH_MODE" == true ]]; then echo false; else echo true; fi)
}
EOF
}

#================================================================
# MAIN EXECUTION FUNCTION
#================================================================

# Main orchestration function - coordinates all script operations
main() {
    # Set up environment and validate inputs
    setup_environment "$@"
    
    # Choose execution path based on mode
    if [[ "$FRESH_MODE" == true ]]; then
        generate_fresh_architecture
    else
        update_from_git_changes
    fi
    
    # Generate final report
    generate_final_report
}

#================================================================
# SCRIPT ENTRY POINT
#================================================================

# Execute main function with all provided arguments
main "$@"
