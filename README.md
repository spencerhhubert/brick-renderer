# brick-renderer

a tool to render pics of lego pieces from the [ldraw part library](https://www.ldraw.org/parts/latest-parts.html) to train a classifcation model

the images are rendered in blender with [this plugin](https://github.com/TobyLobster/ImportLDraw) to import the pieces

`render.py` is ran as an argument to blender like `blender -b -P render.py` on linux and `/Applications/Blender.app/Contents/MacOS/Blender -b -P render.py` on mac os
