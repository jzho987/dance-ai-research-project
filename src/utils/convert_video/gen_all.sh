#!/bin/bash

# Define the directory to loop through
DIRECTORY=$1
VIDEODIR=$DIRECTORY-out

# Loop through each file in the directory
for FILE in "$DIRECTORY"/*; do
  # Check if it is a file (not a directory)
  if [ -f "$FILE" ]; then
    BASENAME=$(basename "$FILE")
    RAWNAME="${BASENAME%.*}"
    python main.py --pre --file $FILE --name $RAWNAME --video_dir $VIDEODIR
  fi
done