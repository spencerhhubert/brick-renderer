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
pos = (0,5,5,0,0,0) #x,y,z,pitch,yaw,roll floor where piece lies relative to camera

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

def renderOneImg(pieces:list, bg_img_path:str, pos:tuple, out_path:str):
    
    def modeObj():
        if bpy.context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode="OBJECT")
    def deselect():
        bpy.ops.object.select_all(action="DESELECT")
        
    def makePiece(piece:tuple, where:tuple):
        kind_id, color, dat_path = piece
        
        #messiness here deals with imports of >1 of the same piece kind
        before_import = set(obj.name for obj in bpy.data.objects)
        bpy.ops.import_scene.importldraw(filepath=dat_path)
        after_import = set(obj.name for obj in bpy.data.objects)
        new_objs = after_import - before_import
        piece = None
        for obj_name in new_objs:
            obj = bpy.data.objects[obj_name]
            if obj_name == "LegoGroundPlane":
                obj.select_set(True)
                bpy.ops.object.delete()
            else:
                piece = obj

        init_rot = (random.uniform(0, 2*pi), random.uniform(0, 2*pi), random.uniform(0, 2*pi))
        init_rot = (0,0,0)
        print("where", where)
        piece.location = where
        piece.rotation_euler = init_rot
        
        #make piece a rigid body for physics sim
        deselect()
        piece.select_set(True)
        bpy.context.view_layer.objects.active = piece
        bpy.ops.rigidbody.object_add()

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
    
    range_x = img_plane.dimensions[0]/2
    range_y = img_plane.dimensions[1]/2
    planes[0].location[1] += range_y
    planes[1].location[1] -= range_y
    planes[2].location[0] += range_x
    planes[3].location[0] -= range_x

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

    for piece in pieces:
        init_loc = (random.uniform(-range_x, range_x), random.uniform(-range_y,range_y), 2)
        makePiece(piece, where=init_loc)
        
    #print(f"Initial position: {piece.location}")
    #physics sim needs to set through every frame no matter what
    #this loop avoids using regular playback in favor of just getting
    #to the last frame asap
    bpy.context.scene.frame_end = 75
    list(map(bpy.context.scene.frame_set, range(1, 75+1)))
    #print(f"Final position: {piece.matrix_world.translation}")
    
    return

ids = ["3001", "3002", "3003", "3004", "3005"]
pieces = [("3001", "0", os.path.join(ldraw_dir,"3001.dat")), ("3005", "0", os.path.join(ldraw_dir,"3005.dat"))]
pieces = [(id, "0", os.path.join(ldraw_dir, f"{id}.dat")) for id in ids]

renderOneImg(pieces, os.path.join(bg_imgs_dir,"bg2.jpg"), pos, out_dir)
       
def massRender(imgs_per:int):
    kinds = whatToRender()
    bg_imgs = list(map(lambda x: os.path.join(bg_imgs_dir,x), os.listdir(bg_imgs_dir)))
    for kind in kinds:
        for i in range(imgs_per):
            color = randomColorCodes(1)[0]
            bg_img_path = random.choice(bg_imgs)
            #renderOneImg(kind[0], color, kind[1], bg_img_path, pos, kind[2])
