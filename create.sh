#!/usr/bin/env bash

set -euo pipefail

OUTPUT="repo-analysis.txt"
TEMP_OUTPUT="${OUTPUT}.tmp"

cleanup() {
    rm -f "$TEMP_OUTPUT"
}

trap cleanup EXIT

# Start with a clean temporary output file.
: > "$TEMP_OUTPUT"

{
    echo "==================================================="
    echo "Repository: $(basename "$PWD")"
    echo "Generated: $(date -Iseconds)"
    echo "==================================================="

    echo
    echo
    echo "=== DIRECTORY STRUCTURE ==="
    echo

    find . \
        -path "./.git" -prune -o \
        -path "./target" -prune -o \
        -path "./node_modules" -prune -o \
        -path "./.venv" -prune -o \
        -path "./venv" -prune -o \
        -path "./__pycache__" -prune -o \
        -path "./.pytest_cache" -prune -o \
        -path "./dist" -prune -o \
        -path "./build" -prune -o \
        -name "$OUTPUT" -prune -o \
        -name "$TEMP_OUTPUT" -prune -o \
        -print

    echo
    echo
    echo "=== FILE CONTENTS ==="
} >> "$TEMP_OUTPUT"

find . -type f \
    \( \
        -name "*.md" -o \
        -name "*.yaml" -o \
        -name "*.yml" -o \
        -name "*.json" -o \
        -name "*.toml" -o \
        -name "*.xml" -o \
        -name "*.properties" -o \
        -name "*.py" -o \
        -name "*.java" -o \
        -name "*.js" -o \
        -name "*.jsx" -o \
        -name "*.ts" -o \
        -name "*.tsx" -o \
        -name "*.html" -o \
        -name "*.css" -o \
        -name "*.sql" -o \
        -name "*.sh" -o \
        -name "*.txt" \
    \) \
    ! -path "*/.git/*" \
    ! -path "*/target/*" \
    ! -path "*/node_modules/*" \
    ! -path "*/.venv/*" \
    ! -path "*/venv/*" \
    ! -path "*/__pycache__/*" \
    ! -path "*/.pytest_cache/*" \
    ! -path "*/dist/*" \
    ! -path "*/build/*" \
    ! -name "$OUTPUT" \
    ! -name "$TEMP_OUTPUT" \
    ! -name "*.min.js" \
    ! -name "*.map" \
    ! -name "package-lock.json" \
    ! -name "poetry.lock" \
    -print0 |
    sort -z |
    while IFS= read -r -d '' file
    do
        {
            echo
            echo
            echo "==================================================="
            echo "FILE: $file"
            echo "==================================================="

            if grep -Iq . "$file"; then
                cat "$file"
            else
                echo "[Skipped: file appears to be binary]"
            fi
        } >> "$TEMP_OUTPUT"
    done

# Move only after the complete export succeeds.
mv "$TEMP_OUTPUT" "$OUTPUT"

# Disable the cleanup trap because the temporary file has been moved.
trap - EXIT

FILE_COUNT=$(
    grep -c "^FILE: " "$OUTPUT" || true
)

FILE_SIZE=$(
    du -h "$OUTPUT" | cut -f1
)

echo
echo "Repository export completed successfully."
echo "Output: $OUTPUT"
echo "Files included: $FILE_COUNT"
echo "Output size: $FILE_SIZE"