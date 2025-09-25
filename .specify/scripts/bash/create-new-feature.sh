#!/bin/bash

# Create new feature branch and spec file from natural language description
# Usage: ./create-new-feature.sh --json "Feature description"

set -e

# Check if --json flag is provided
if [[ "$1" == "--json" ]]; then
    JSON_OUTPUT=true
    FEATURE_DESC="$2"
else
    JSON_OUTPUT=false
    FEATURE_DESC="$1"
fi

if [[ -z "$FEATURE_DESC" ]]; then
    echo "Error: Feature description is required" >&2
    exit 1
fi

# Generate branch name from feature description
# Convert to lowercase, replace spaces with hyphens, remove special characters
BRANCH_NAME=$(echo "$FEATURE_DESC" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9 -]//g' | sed 's/ /-/g' | cut -c1-50)

# Ensure branch name is not empty and add feature prefix
if [[ -z "$BRANCH_NAME" ]]; then
    BRANCH_NAME="feature-spec"
fi
BRANCH_NAME="feature/$(date +%Y%m%d)-${BRANCH_NAME}"

# Generate spec file path
SPEC_DIR="specs"
SPEC_FILE="${SPEC_DIR}/$(date +%Y%m%d)-$(echo "$BRANCH_NAME" | sed 's|feature/||' | sed 's/[^a-z0-9-]//g').md"

# Create specs directory if it doesn't exist
mkdir -p "$SPEC_DIR"

# Check if we're in a git repository
if git rev-parse --git-dir > /dev/null 2>&1; then
    # Create and checkout new branch
    git checkout -b "$BRANCH_NAME"

    # Initialize spec file
    touch "$SPEC_FILE"
    git add "$SPEC_FILE"
else
    echo "Warning: Not in a git repository, skipping branch creation" >&2
fi

# Output JSON if requested
if [[ "$JSON_OUTPUT" == "true" ]]; then
    cat << EOF
{
    "BRANCH_NAME": "$BRANCH_NAME",
    "SPEC_FILE": "$SPEC_FILE",
    "FEATURE_DESC": "$FEATURE_DESC"
}
EOF
fi

echo "Created feature branch: $BRANCH_NAME" >&2
echo "Spec file: $SPEC_FILE" >&2