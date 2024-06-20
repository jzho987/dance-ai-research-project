#!/bin/bash

# Define the directory to loop through
DIRECTORY=./data/music

# Loop through each file in the directory
for FILE in "$DIRECTORY"/*; do
  # Check if it is a file (not a directory)
  if [ -f "$FILE" ]; then
    BASENAME=$(basename "$FILE")
    echo "go run main.go $BASENAME"
    go run main.go $BASENAME
  fi
done