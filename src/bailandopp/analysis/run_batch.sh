#!/bin/bash

for FILE in "./inputs"/*; do
  if [ -f "$FILE" ]; then
    SCRIPT="python librosa_visualizer.py  $FILE --out_dir ./outputs"
    echo "$SCRIPT"
    $SCRIPT
  fi
done
