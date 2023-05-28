#render script argument to blender
#use blender -B -P render.py -- <args>
import os
import json
import bpy
import sqlite3 as sql
import random

piece_db_path = "../nexus/databases/pieces.db"
db = sql.connect(piece_db_path)
c = db.cursor()
ldraw_dir = "ldraw/parts/"
ldraw_kinds = list(map(lambda x: x[:-4],os.listdir(ldraw_dir)))
out_dir = "renders/"
bg_imgs_dir = "bg_imgs/"
pos = (0,0,0,0,0,0) #x,y,z,pitch,yaw,roll floor where piece lies relative to camera

def whatToRender() -> list:
    outs = []
    c.execute("SELECT * FROM kinds")
    for i,row in enumerate(c.fetchall()):
        id = row[0]
        alt_ids = json.loads(row[3])
        dats = list(filter(lambda x: x in ldraw_kinds, alt_ids))
        if len(dats) < 1:
            continue
        dats.sort(key=lambda x: len(x))
        #assume the dat we want is the one with the shortest name
        #I any of them would work
        dat_path = os.path.join(ldraw_dir,dats[0]+".dat")
        outs.append((id, dat_path, os.path.join(out_dir, id)))
    return outs

def randomColorCodes(num:int) -> list:
    c.execute("SELECT code FROM colors ORDER BY RANDOM() LIMIT ?", (num,))
    return [i[0] for i in c.fetchall()]

def renderOne(kind_id:str, color:str, dat_path:str, bg_img_path:str, pos:tuple, out_path:str):
    def modeObj():
        if bpy.context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode="OBJECT")
    def deselect():
        bpy.ops.object.select_all(action="DESELECT")

    #delete everything in the scene
    modeObj()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    bpy.ops.import_scene.importldraw(filepath=dat_path)

    modeObj()
    deselect()
    bpy.data.objects["LegoGroundPlane"].select_set(True)
    bpy.ops.object.delete()
    
    piece = bpy.data.objects[f"00000_{os.path.basename(dat_path)}"]
    
    init_loc = (0, 0, 5)
    random.seed()
    init_rot = (random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1))
    piece.location = init_loc
    piece.rotation_euler = init_rot
    
    deselect()
    piece.select_set(True)
    bpy.context.view_layer.objects.active = piece
    bpy.ops.rigidbody.object_add()
    
    #make ground
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    ground = bpy.context.object
    deselect()
    ground.select_set(True)
    bpy.context.view_layer.objects.active = ground
    bpy.ops.rigidbody.object_add()
    ground.rigid_body.type = "PASSIVE"
    
    print(f"Initial position: {piece.location}")
    #physics sim needs to set through every frame no matter what
    #this loop avoids using regular playback in favor of just getting
    #to the last frame asap
    for frame in range(1, 75+1):
        bpy.context.scene.frame_set(frame)
    print(f"Final position: {piece.matrix_world.translation}")
    return

def massRender(imgs_per:int):
    kinds = whatToRender()
    bg_imgs = list(map(lambda x: os.path.join(bg_imgs_dir,x), os.listdir(bg_imgs_dir)))
    for kind in kinds:
        for i in range(imgs_per):
            color = randomColorCodes(1)[0]
            bg_img_path = random.choice(bg_imgs)
            renderOne(kind[0], color, kind[1], bg_img_path, pos, kind[2])


renderOne("3005", "0", os.path.join(ldraw_dir,"3005.dat"), os.path.join(bg_imgs_dir,"bg1.jpg"), pos, out_dir)
