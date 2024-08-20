#!/bin/bash

# Define the directory to loop through
MOTION_DIR=$1
MUSICPATH=$2
CKPT_PATH=$3

for MOTION in "$MOTION_DIR"/*; 
do
  if [ -f "$MOTION" ]; 
  then
    BASENAME=$(basename "$MOTION")
    RAWNAME="${BASENAME%.*}"
    MBASENAME=$(basename "$MUSICPATH")
    MRAWNAME="${MBASENAME%.*}"
    echo "python main.py --motion inputs/$BASENAME --music $MUSICPATH --save_dir ./video/$RAWNAME-$MRAWNAME --weights $CKPT_PATH"
    python main.py --motion inputs/$BASENAME --music $MUSICPATH --save_dir ./video/$RAWNAME-$MRAWNAME --weights $CKPT_PATH
  fi
done