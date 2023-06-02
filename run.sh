#!/bin/sh

OS=$(uname)

if [ "$OS" = "Linux" ]; then
    echo "Detected Linux"
    python3 -m pip install --user -r requirements.txt
    site_packages_path=$(python3 -c 'import site; print(site.getusersitepackages())')
    blender -b -P render.py -- $site_packages_path
elif [ "$OS" = "Darwin" ]; then
    echo "Detected Mac OS"
    python3 -m pip install --user -r requirements.txt
    /Applications/Blender.app/Contents/MacOS/Blender -b -P render.py
fi
