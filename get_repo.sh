#!/bin/bash

OUTPUT=repo-analysis.txt

echo "===================================================" > $OUTPUT
echo "Repository: $(basename $(pwd))" >> $OUTPUT
echo "Generated: $(date)" >> $OUTPUT
echo "===================================================" >> $OUTPUT

echo -e "\n\n=== DIRECTORY STRUCTURE ===\n" >> $OUTPUT
find . \
  -path "./.git" -prune -o \
  -path "./target" -prune -o \
  -path "./node_modules" -prune -o \
  -path "./.venv" -prune -o \
  -print >> $OUTPUT

echo -e "\n\n=== FILE CONTENTS ===\n" >> $OUTPUT

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
     -name "*.txt" \
  \) \
  ! -path "*/.git/*" \
  ! -path "*/target/*" \
  ! -path "*/node_modules/*" \
  ! -path "*/.venv/*" \
| sort | while read file
do
    echo -e "\n\n===================================================" >> $OUTPUT
    echo "FILE: $file" >> $OUTPUT
    echo "===================================================" >> $OUTPUT
    cat "$file" >> $OUTPUT
done

echo "Created $OUTPUT"