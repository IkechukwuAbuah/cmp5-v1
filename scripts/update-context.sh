#!/usr/bin/env bash
set -euo pipefail

# Context Update Script for CMP5 v1 EFL Agent Assistant
# Updates agent context with current progress and task completion status

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
SESSIONS_FILE="$REPO_ROOT/notes/sessions.md"
STATUS_FILE="$REPO_ROOT/logs/status_line.json"

# Generate timestamp in West Africa Time per logging convention.
CURRENT_TIMESTAMP=$(TZ="Africa/Lagos" date '+%Y-%m-%d %H:%M WAT')

# Capture current HEAD SHA and annotate if the working tree is dirty.
FORK_SHA=$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || true)
STATUS_OUTPUT=$(git -C "$REPO_ROOT" status --porcelain)
if [ -z "$FORK_SHA" ]; then
  FORK_LABEL="pending"
else
  if [ -n "$STATUS_OUTPUT" ]; then
    FORK_LABEL="$FORK_SHA (dirty workspace)"
  else
    FORK_LABEL="$FORK_SHA"
  fi
fi

# Get current task status summary
COMPLETED_TASKS=$(grep -c "✅" "$REPO_ROOT/specs/001-efl-agent-assistant-prototype-track-trace-vo/tasks.md" || true)
REMAINING_TASKS=$(grep -c "⚠️ NOT IMPLEMENTED" "$REPO_ROOT/specs/001-efl-agent-assistant-prototype-track-trace-vo/tasks.md" || true)
TOTAL_CURRENT_TASKS=$((COMPLETED_TASKS + REMAINING_TASKS))

# Calculate progress percentage
if [ "$TOTAL_CURRENT_TASKS" -gt 0 ]; then
  PROGRESS_PERCENTAGE=$(echo "scale=2; ($COMPLETED_TASKS * 100) / $TOTAL_CURRENT_TASKS" | bc)
else
  PROGRESS_PERCENTAGE="0"
fi

echo "=== CMP5 v1 Context Update ==="
echo "Timestamp: $CURRENT_TIMESTAMP"
echo "Feature: 001-efl-agent-assistant-prototype-track-trace-vo"
echo "Tasks Completed: $COMPLETED_TASKS"
echo "Tasks Remaining: $REMAINING_TASKS"
echo "Current Phase: Phase 3.6.2 (Localisation) - COMPLETED"
echo "Next Phase: Phase 3.7 (Polish)"
echo "Progress: $PROGRESS_PERCENTAGE%"
echo ""

# Update sessions.md if it exists
if [ -f "$SESSIONS_FILE" ]; then
  # Check if this exact timestamp already exists
  if ! grep -q "## $CURRENT_TIMESTAMP" "$SESSIONS_FILE" ; then
    # Insert the new entry at the top
    TMP_FILE=$(mktemp)
    echo "## $CURRENT_TIMESTAMP" > "$TMP_FILE"
    echo "" >> "$TMP_FILE"
    echo "- Fork commit: $FORK_LABEL" >> "$TMP_FILE"
    UPSTREAM_SHA=$(git -C "$REPO_ROOT" rev-parse origin/main 2>/dev/null || echo "unknown")
    echo "- Upstream commit: $UPSTREAM_SHA" >> "$TMP_FILE"
    echo "- Focus: Complete Phase 3.7: Polish tasks (T063-T072)" >> "$TMP_FILE"
    echo "- Notes: Context update - Localisation phase completed, moving to polish phase. $COMPLETED_TASKS/$TOTAL_CURRENT_TASKS tasks done ($PROGRESS_PERCENTAGE%)." >> "$TMP_FILE"
    echo "" >> "$TMP_FILE"

    # Add the rest of the existing file
    cat "$SESSIONS_FILE" >> "$TMP_FILE"
    mv "$TMP_FILE" "$SESSIONS_FILE"
    echo "✓ Updated sessions.md"
  else
    echo "✓ Session already exists in sessions.md"
  fi
else
  echo "⚠ Sessions file not found at $SESSIONS_FILE"
fi

# Update status_line.json if it exists and is valid JSON
if [ -f "$STATUS_FILE" ]; then
  if command -v jq >/dev/null 2>&1 && jq empty "$STATUS_FILE" 2>/dev/null; then
    # Create backup
    cp "$STATUS_FILE" "$STATUS_FILE.backup"

    # Create a simple JSON update
    cat > "$STATUS_FILE.tmp" << EOF
{
  "last_updated": "$CURRENT_TIMESTAMP",
  "current_feature": "001-efl-agent-assistant-prototype-track-trace-vo",
  "current_phase": "Phase 3.6.2 (Localisation) - COMPLETED",
  "next_phase": "Phase 3.7 (Polish)",
  "tasks_completed": $COMPLETED_TASKS,
  "tasks_remaining": $REMAINING_TASKS,
  "progress_percentage": $PROGRESS_PERCENTAGE
}
EOF

    # If the original file is valid JSON, merge them
    if jq empty "$STATUS_FILE" 2>/dev/null; then
      # Merge the new data with existing data
      jq -s '.[0] + .[1]' "$STATUS_FILE" "$STATUS_FILE.tmp" > "$STATUS_FILE.final" && mv "$STATUS_FILE.final" "$STATUS_FILE"
    else
      # Just use the new data
      mv "$STATUS_FILE.tmp" "$STATUS_FILE"
    fi
    echo "✓ Updated status_line.json"
  else
    echo "⚠ jq not available or status file is not valid JSON, skipping status_line.json update"
  fi
else
  echo "⚠ Status file not found at $STATUS_FILE"
fi

echo ""
echo "=== Context Update Complete ==="
echo "Current Status:"
echo "- Feature: 001-efl-agent-assistant-prototype-track-trace-vo"
echo "- Phase: Phase 3.6.2 (Localisation) - COMPLETED"
echo "- Progress: $COMPLETED_TASKS/$TOTAL_CURRENT_TASKS tasks completed ($PROGRESS_PERCENTAGE%)"
echo "- Ready for: Phase 3.7 (Polish) tasks T063-T072"
echo ""
echo "Next recommended actions:"
echo "1. Complete remaining unit tests (T063, T065)"
echo "2. Implement performance tests (T067, T068)"
echo "3. Update API documentation (T069)"
echo "4. Run manual testing scenarios (T072)"
