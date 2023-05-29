#render script argument to blender
#use blender -B -P render.py -- <args>
import os
import json
import random
import bpy
import sqlite3 as sql
from mathutils import Vector
from math import pi
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
temp_dir = "tmp"
if not os.path.exists(temp_dir):
    os.mkdir(temp_dir)

if not os.path.exists(os.path.join(temp_dir, "ldrs")):
    os.mkdir(os.path.join(temp_dir, "ldrs"))

class Piece:
    def __init__(self, id:str, ml_id:int, color:str, dat_path:str):
        self.id = id
        self.ml_id = ml_id
        self.dat_path = dat_path
        self.color = random.randint(1,16)
        self.ldr_path = os.path.join(temp_dir, "ldrs", id + ".ldr")

    def makeLDR(self):
        with open(self.ldr_path, "w") as f:
            f.write(f"1 {self.color} 0 0 0 1 0 0 0 1 0 0 0 1 {os.path.basename(self.dat_path)}")

    def __repr__(self):
        return f"Piece(id={self.id},\nml_id={self.ml_id},\ncolor={self.color},\ndat_path={self.dat_path},\nld_path={self.ldr_path})\n\n"

def randomColorCodes(num:int) -> list:
    c.execute("SELECT code FROM colors ORDER BY RANDOM() LIMIT ?", (num,))
    return [i[0] for i in c.fetchall()]

def makePiece(row):
    id = row[0]
    alt_ids = json.loads(row[3])
    dats = filter(lambda x: x in ldraw_kinds, alt_ids)
    dats = list(filter(lambda x: x != "", dats))
    if len(dats) < 1:
        return None
    dats.sort(key=lambda x: len(x))
    #assume the dat we want is the one with the shortest name
    #I any of them would work
    dat_path = os.path.join(ldraw_dir,dats[0]+".dat")
    ml_id = int(c.execute("SELECT ml_id FROM kinds WHERE id = ?",(id,)).fetchone()[0])
    return Piece(id, ml_id, randomColorCodes(1)[0], dat_path)

def whatToRender() -> list:
    c.execute("SELECT * FROM kinds")
    out = []
    for i,row in enumerate(c.fetchall()):
        piece = makePiece(row)
        if piece is not None:
            out.append(piece)
        if i == 5:
            break
    return out

#output is files written to temp_dir
def renderOneIteration(pieces:list, bg_img_path:str, pos:tuple):
    def modeObj():
        if bpy.context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode="OBJECT")
    def deselect():
        bpy.ops.object.select_all(action="DESELECT")
        
    def spawnPiece(piece:Piece, where:tuple):
        kind_id, color, ldr_path = piece.id, piece.color, piece.ldr_path
        
        #messiness here deals with imports of >1 of the same piece kind
        before_import = set(obj.name for obj in bpy.data.objects)
        bpy.ops.import_scene.importldraw(filepath=ldr_path)
        after_import = set(obj.name for obj in bpy.data.objects)
        new_objs = after_import - before_import
        piece = None
        for obj_name in new_objs:
            obj = bpy.data.objects[obj_name]
            if obj_name == "LegoGroundPlane":
                obj.select_set(True)
                bpy.ops.object.delete()
            elif ".ldr" in obj_name:
                continue
            else:
                piece = obj

        init_rot = (random.uniform(0, 2*pi), random.uniform(0, 2*pi), random.uniform(0, 2*pi))
        init_rot = (0,0,0)
        piece.location = where
        piece.rotation_euler = init_rot
        
        #make piece a rigid body for physics sim
        deselect()
        piece.select_set(True)
        print(piece)
        bpy.context.view_layer.objects.active = piece
        bpy.ops.rigidbody.object_add()
        return piece
    
    def hide(obj):
        obj.hide_render = True
        obj.hide_viewport = True
        
    def show(obj):
        obj.hide_render = False
        obj.hide_viewport = False
        
    def setupCam():
        deselect()
        bpy.ops.object.camera_add()
        cam = bpy.context.object
        bpy.context.scene.camera = cam
        cam = bpy.data.scenes["Scene"].camera
        return cam
    
    def moveCam(cam, pos):
        cam_pos = pos[:-3]
        cam_rot = pos[3:]
        cam.rotation_mode = "XYZ"
        cam.location = cam_pos
        looking_at = Vector((0.0, 0.0, 0.0))
        direc = looking_at - cam.location
        cam.rotation_euler = direc.to_track_quat('-Z', 'Y').to_euler()
        #cam specs
        cam.data.lens = 35
        cam.data.sensor_width = 36
        
    def sceneSetup():
        #delete everything in the scene
        modeObj()
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()
        
        #no other lights and pure black background
        bpy.context.scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0
    
    def setImgPlane():
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
        return img_plane
        
    def setContainingWalls():
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

        planes[0].location[1] += range_y
        planes[1].location[1] -= range_y
        planes[2].location[0] += range_x
        planes[3].location[0] -= range_x
        
    def setLight():
        deselect()
        bpy.ops.object.light_add(type="POINT", location=pos[:-3])
        light = bpy.context.object
        light.data.energy = 1000
        looking_at = Vector((0.0, 0.0, 0.0))
        direc = looking_at - Vector(pos[:-3])
        light.rotation_euler = direc.to_track_quat('-Z', 'Y').to_euler()    
        
    cam = sceneSetup()
    img_plane = setImgPlane()
    range_x = img_plane.dimensions[0]/2
    range_y = img_plane.dimensions[1]/2
    setContainingWalls()
    setLight()

    for i,piece in enumerate(pieces):
        init_loc = (random.uniform(-range_x, range_x), random.uniform(-range_y,range_y), 2)
        pieces[i] = spawnPiece(piece, where=init_loc)
    
    #step to end of scene. physics sim needs to step through all frames
    bpy.context.scene.frame_end = 75
    list(map(bpy.context.scene.frame_set, range(1, 75+1)))
    
    cam = setupCam()
    moveCam(cam, pos)
    bpy.context.scene.cycles.samples = 50
    bpy.context.scene.render.resolution_percentage = 50
    for i,piece in enumerate(pieces):
        hide(img_plane)
        list(map(hide, pieces))
        show(piece)
        bpy.context.scene.render.filepath=os.path.join(temp_dir, f"{i}.jpg")
        bpy.ops.render.render(write_still=True)
    
    show(img_plane)
    list(map(show, pieces))
    bpy.context.scene.render.filepath=os.path.join(temp_dir, "final.jpg")
    bpy.ops.render.render(write_still=True)
    return

def numpyMasks(pieces:list):
    return None

pieces = whatToRender()[0:5]
list(map(lambda x: x.makeLDR(), pieces))
print(pieces)
renderOneIteration(pieces, os.path.join(bg_imgs_dir,"bg2.jpg"), pos)
       
def massRender(imgs_per:int):
    kinds = whatToRender()
    bg_imgs = list(map(lambda x: os.path.join(bg_imgs_dir,x), os.listdir(bg_imgs_dir)))
    for kind in kinds:
        for i in range(imgs_per):
            color = randomColorCodes(1)[0]
            bg_img_path = random.choice(bg_imgs)
            #renderOneImg(kind[0], color, kind[1], bg_img_path, pos, kind[2])
