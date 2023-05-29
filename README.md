# brick-renderer

a tool to render pics of lego pieces from the [ldraw part library](https://www.ldraw.org/parts/latest-parts.html) to train a classifcation model

the images are rendered in blender with [this plugin](https://github.com/TobyLobster/ImportLDraw) to import the pieces

![example rendered pic of ldraw pieces](https://raw.githubusercontent.com/spencerhhubert/brick-renderer/main/assets/example01.jpg)

## run
`chmod +x run.sh`

`./run.sh`

## todo
- lego logo on studs
- many of the pieces in the db are too big. need filter to remove those when building the db
    - I think the BL api contains dimensions
- output np array and pics in training-ready format
