#import bpy
import os
import re
import math
from random import seed
from random import random
from datetime import datetime

def deg_to_radians(deg):
    return (deg / 360) * 2 * math.pi

def random_radian():
    return deg_to_radians(random() * 360)

def timestamp():
    current_moment = datetime.now()
    timestamp = math.floor(datetime.timestamp(current_moment))
    return timestamp

def deselect_all():
    if bpy.context.object.mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

def cut_ext(name):
	return name[:-4];

def cut_path(path):
	return os.path.basename(path);

def name(path):
	return cut_ext(cut_path(path));

def fullname(path):	
	with open(path) as f:
		info = f.readlines()[0];
	f.close();
	return info;

def ignore(path, keep_variations, keep_assemblies):
	if os.path.isdir(path):
		return True;
	ignore_words = ["Electric", "Minifig", "Train", "Constraction",
			"Duplo", "Bracelet", "Figure", "Sticker", "Sheet",
			"Quatro", "Fabuland", "Baseplate", "Scala"];
	if fullname(path).split()[1] in ignore_words:
		return True;
	# ignore "needs work" (~) or symbolic link (=)
	info = fullname(path);
	if info[2]=='=' or info[2]=='~':
		return True;
	part = name(path);
	if re.search("^[stum]", part):
		# ignore sticker, third-party, and unknown
		return True;
	if re.search("[p]", part):
		return True;
	if not keep_variations and re.search("[a-z]$", part):
		return True;
	if not keep_assemblies and re.search("\d{3,5}[cd]\d{2}", part):
		return True;
	if re.search("\d{2}-f\d", part):
		# ignore flexible assemblies
		return True;

def gen_pics(model, iterations, inPath, outPath, res):
    seed()
    #delete everything
    if bpy.context.object.mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    path = os.path.join(inPath, model)
    bpy.ops.import_scene.importldraw(filepath=path)

    deselect_all()
    bpy.data.objects["LegoGroundPlane"].select_set(True)
    bpy.ops.object.delete()

    piece = bpy.data.objects[f"00000_{model}"]
    scene = bpy.data.scenes['Scene']

    dims = piece.dimensions
    dimx, dimy, dimz = dims[0], dims[1], dims[2]

    #camera location
    locx, locy, locz = ((max(dimx, dimy, dimz))+.7), ((max(dimx, dimy, dimz))+.7), (dimz / 2)
    rotx, roty, rotz = deg_to_radians(-90), deg_to_radians(180), deg_to_radians(-45)

    #set camera
    bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=(locx, locy, locz), rotation=(rotx, roty, rotz), scale=(1, 1, 1))
    scene.camera = bpy.context.object
    scene.render.resolution_x = res
    scene.render.resolution_y = res

    #set light
    bpy.ops.object.light_add(type='SUN', radius=1, align='WORLD', location=(locx, locy, locz + 10), scale=(1, 1, 1))

    bpy.ops.mesh.primitive_plane_add(size=50, enter_editmode=False, align='WORLD', location=(-locx, -locy, 0), scale=(1,1,1), rotation=(deg_to_radians(90), 0, deg_to_radians(-45)))

    scene.cycles.device = 'GPU'
    scene.cycles.progressive = 'BRANCHED_PATH'
    scene.cycles.subsurface_samples = 5
    scene.cycles.aa_samples = 64

    def rotate_piece(x, y, z):
        deselect_all()
        piece.select_set(True)
        override=bpy.context.copy()
        override['area']=[a for a in bpy.context.screen.areas if a.type=="VIEW_3D"][0]
        bpy.ops.transform.rotate(override, value=x, orient_axis='X')
        bpy.ops.transform.rotate(override, value=y, orient_axis='Y')
        bpy.ops.transform.rotate(override, value=z, orient_axis='Z')

    for i in range(iterations):
        rotate_piece(random_radian(), random_radian(), random_radian())
        bpy.context.scene.render.filepath = os.path.join(outPath, f"{model[:-4]}_{i}")
        bpy.ops.render.render(write_still = True)

def gen_many_pics(parts_dir, output_dir, quantity, res):
	parts = sorted(os.listdir(model_dir));
	for part in parts:
		# ignore parts that are decorated, unknown, third party, or stickers
		if ignore(cut_ext(part)):
		    continue;
		# setup folders
		part_dir = os.path.join(output_dir, f"{cut_ext(part)}");
		if not os.path.isdir(part_dir):
		    os.mkdir(part_dir);
		# have we done enough renders
		if len(os.listdir(part_dir)) >= (quantity):
		    continue;
		#do it
		gen_pics(part, 32, parts_dir, output_dir, res);

#gen_many_pics("ldraw/parts/", "renders", 32, 128);

remainder = 0;
path = "ldraw/parts/";
parts = sorted(os.listdir(path));
for part in parts:
	if ignore(path+part, False, True):
		continue;
	remainder += 1;
	print(f"{cut_ext(part)} - {fullname(path+part)[:-2]}");

print(f"total: {len(parts)}");
print(f"remainder: {remainder}");
