#!/bin/bash

# Define the directory to loop through
MOTION_DIR=$1
MUSIC_DIR=$2
CKPT_PATH=$3

for MOTION in "$MOTION_DIR"/*; 
do
  if [ -f "$MOTION" ]; 
  then
    BASENAME=$(basename "$MOTION")
    RAWNAME="${BASENAME%.*}"
    for MUSIC in "$MUSIC_DIR"/*; 
    do
      if [ -f "$MUSIC" ]; 
      then
        MUSIC_BASE=$(basename "$MUSIC")
        MUSIC_NAME="${MUSIC_BASE%.*}"
        python main.py --motion inputs/$BASENAME --music ./wav/$MUSIC_BASE --save_dir ./video/$RAWNAME-$MUSIC_NAME --weights $CKPT_PATH
      fi
    done
  fi
done