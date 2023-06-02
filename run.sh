#!/bin/sh

OS=$(uname)

if [ "$OS" = "Linux" ]; then
    echo "Detected Linux"
    python3 -m pip install -r requirements.txt
    export SITE_PACKAGES_PATH=$(python3 -c 'import site; print(site.getusersitepackages())')
    blender -b -P render.py
elif [ "$OS" = "Darwin" ]; then
    echo "Detected Mac OS"
    /Applications/Blender.app/Contents/Resources/2.92/python/bin/python3.7m -m pip install -r requirements.txt
    /Applications/Blender.app/Contents/MacOS/Blender -b -P render.py
fi
