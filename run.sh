#!/bin/sh

OS=$(uname)

if [ "$OS" = "Linux" ]; then
    echo "Detected Linux"
    blender -b -P render.py
elif [ "$OS" = "Darwin" ]; then
    echo "Detected Mac OS"
    /Applications/Blender.app/Contents/MacOS/Blender -b -P render.py
fi

