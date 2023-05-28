#render script argument to blender
#use blender -B -P render.py -- <args>
import os
import json
import random
import bpy
import sqlite3 as sql
from mathutils import Vector
#install to blender python instance
#/Applications/Blender.app/Contents/Resources/2.92/python/bin/python3.7m -m pip install pillow
from PIL import Image

piece_db_path = "../nexus/databases/pieces.db"
db = sql.connect(piece_db_path)
c = db.cursor()
ldraw_dir = "ldraw/parts/"
ldraw_kinds = list(map(lambda x: x[:-4],os.listdir(ldraw_dir)))
out_dir = "renders/"
bg_imgs_dir = "bg_imgs/"
px_per_mm = 10 #for bg img
pos = (0,10,10,0,0,0) #x,y,z,pitch,yaw,roll floor where piece lies relative to camera

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
    
    #import background image and scale by cm per pixel
    deselect()
    bpy.ops.import_image.to_plane(files=[{"name":os.path.basename(bg_img_path)}],
                                    directory=os.path.dirname(bg_img_path), align_axis='Z+',
                                    relative=False)
    img_plane = bpy.context.active_object
    img_plane.select_set(True)
    bpy.context.view_layer.objects.active = img_plane
    bpy.ops.rigidbody.object_add()
    img_plane.rigid_body.type = "PASSIVE"
    deselect()
    
    #scale img according to size of piece
    img = Image.open(bg_img_path)
    img_w, img_h = img.size
    mm_per_bu = 1000 #blender units
    new_w = img_w / px_per_mm / mm_per_bu
    new_h = img_h / px_per_mm / mm_per_bu
    img_plane.scale.x = new_w/2
    img_plane.scale.y = new_h/2
    img_plane.scale *= 25 #the bricks are 25x too big but physics is wrong if you scale them down 
    
    planes = []
    for i in range(4):
        deselect()
        bpy.ops.mesh.primitive_plane_add(location=(0, 0, 0))
        plane = bpy.context.object
        dim = max(img_plane.dimensions[0], img_plane.dimensions[1])
        plane.scale = (dim,10,1)
        plane.select_set(True)
        bpy.ops.rigidbody.object_add()
        plane.rigid_body.type = "PASSIVE"
        plane.rigid_body.collision_shape = "MESH"
        #make invisible in render
        plane.hide_render = True
        plane.hide_viewport = True
        planes.append(plane)
        
    planes[0].rotation_euler = (pi/2,0,0)
    planes[1].rotation_euler = (pi/2,0,0)
    planes[2].rotation_euler = (pi/2,0,pi/2)
    planes[3].rotation_euler = (pi/2,0,pi/2)
    
    planes[0].location[1] += img_plane.dimensions[1]/2
    planes[1].location[1] -= img_plane.dimensions[1]/2
    planes[2].location[0] += img_plane.dimensions[0]/2
    planes[3].location[0] -= img_plane.dimensions[0]/2

    #set up camera
    cam_pos = pos[:-3]
    cam_rot = pos[3:]
    deselect()
    bpy.ops.object.camera_add(location=cam_pos)
    cam = bpy.context.object
    cam.rotation_mode = "XYZ"
    looking_at = Vector((0.0, 0.0, 0.0))
    direc = looking_at - cam.location
    cam.rotation_euler = direc.to_track_quat('-Z', 'Y').to_euler()
    
    #cam specs
    cam.data.lens = 35
    cam.data.sensor_width = 36
    
    #lights
    deselect()
    bpy.ops.object.light_add(type="POINT", location=cam_pos)
    light = bpy.context.object
    light.data.energy = 1000
    looking_at = Vector((0.0, 0.0, 0.0))
    direc = looking_at - cam.location
    light.rotation_euler = direc.to_track_quat('-Z', 'Y').to_euler()

    #import lego piece
    bpy.ops.import_scene.importldraw(filepath=dat_path)

    modeObj()
    deselect()
    bpy.data.objects["LegoGroundPlane"].select_set(True)
    bpy.ops.object.delete()
    
    piece = bpy.data.objects[f"00000_{os.path.basename(dat_path)}"]

    #set random initial state for piece
    init_loc = (random.uniform(-1, 1), random.uniform(-1,1), 5)
    init_rot = (random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1))
    piece.location = init_loc
    piece.rotation_euler = init_rot
    
    #make piece a rigid body for physics sim
    deselect()
    piece.select_set(True)
    bpy.context.view_layer.objects.active = piece
    bpy.ops.rigidbody.object_add()
        
    print(f"Initial position: {piece.location}")
    #physics sim needs to set through every frame no matter what
    #this loop avoids using regular playback in favor of just getting
    #to the last frame asap
    bpy.context.scene.frame_end = 75
    list(map(bpy.context.scene.frame_set, range(1, 75+1)))
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

renderOne("3001", "0", os.path.join(ldraw_dir,"3001.dat"),
        os.path.join(bg_imgs_dir,"bg1.jpg"), pos, out_dir)

