# brick-renderer

a tool to render many images or many bricks from the [ldraw part library](https://www.ldraw.org/parts/latest-parts.html) for lego piece classification training material

the images are rendered in blender and [this plugin](https://github.com/TobyLobster/ImportLDraw) to import the pieces

the image_from_3d_gen.py is ran with blender, ie in linux you would execute ```blender -b -P image_from_3d_gen.py```

it will then go through the ldraw parts library, leaving out about 70% of the ~15,000 parts, and rendering the desired number of iteration of each piece, revoling it about and doing some math to maximize it's size on the screen to get various angles as such:

![alt text](https://raw.githubusercontent.com/spencerhhubert/brick-renderer/main/example_pic1.png)
