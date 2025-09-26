#!/usr/bin/env bash
set -euo pipefail

# Always work relative to the repository root so the script is portable.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
SESSIONS_FILE="$REPO_ROOT/notes/sessions.md"

if [ ! -f "$SESSIONS_FILE" ]; then
  echo "Could not find sessions log at $SESSIONS_FILE" >&2
  exit 1
fi

# Generate timestamp in West Africa Time per logging convention.
timestamp=$(TZ="Africa/Lagos" date '+%Y-%m-%d %H:%M WAT')

# Capture current HEAD SHA and annotate if the working tree is dirty.
fork_sha=$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || true)
status_output=$(git -C "$REPO_ROOT" status --porcelain)
if [ -z "$fork_sha" ]; then
  fork_label="pending"
else
  if [ -n "$status_output" ]; then
    fork_label="$fork_sha (dirty workspace)"
  else
    fork_label="$fork_sha"
  fi
fi

resolve_remote_sha() {
  local remote=$1
  local head_ref
  local sha=""

  if ! git -C "$REPO_ROOT" remote get-url "$remote" >/dev/null 2>&1; then
    return 1
  fi

  head_ref=$(git -C "$REPO_ROOT" symbolic-ref --quiet "refs/remotes/${remote}/HEAD" 2>/dev/null || true)
  if [ -n "$head_ref" ]; then
    sha=$(git -C "$REPO_ROOT" rev-parse "$head_ref" 2>/dev/null || true)
  fi

  if [ -z "$sha" ]; then
    for branch in main master trunk; do
      sha=$(git -C "$REPO_ROOT" rev-parse "${remote}/${branch}" 2>/dev/null || true)
      if [ -n "$sha" ]; then
        break
      fi
    done
  fi

  if [ -n "$sha" ]; then
    printf '%s' "$sha"
    return 0
  fi

  return 1
}

upstream_sha=""
if upstream_sha=$(resolve_remote_sha upstream); then
  :
elif upstream_sha=$(resolve_remote_sha origin); then
  :
else
  upstream_sha="$fork_sha"
fi

if [ -z "$upstream_sha" ]; then
  upstream_label="pending"
else
  upstream_label="$upstream_sha"
fi

entry=$(cat <<EOF_ENTRY
## $timestamp

- Fork commit: $fork_label
- Upstream commit: $upstream_label
- Focus:
- Notes:

EOF_ENTRY
)

first_entry_line=$(grep -n '^## ' "$SESSIONS_FILE" | head -n 1 | cut -d ':' -f 1 || true)
tmp_file=$(mktemp)

# Insert the new entry after the template block while keeping reverse chronology.
if [ -n "$first_entry_line" ]; then
  head -n $(( first_entry_line - 1 )) "$SESSIONS_FILE" > "$tmp_file"
  printf '%s\n' "$entry" >> "$tmp_file"
  printf '\n' >> "$tmp_file"
  tail -n +$(( first_entry_line )) "$SESSIONS_FILE" >> "$tmp_file"
else
  printf '%s\n' "$entry" > "$tmp_file"
fi

mv "$tmp_file" "$SESSIONS_FILE"

echo "Logged session stub for $timestamp"
echo "  Fork commit: $fork_label"
echo "  Upstream commit: $upstream_label"
