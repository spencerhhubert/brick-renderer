#render script argument to blender
#use blender -B -P render.py -- <args>
import os
import json
import bpy
import sqlite3 as sql

piece_db_path = "../nexus/databases/pieces.db"
ldraw_dir = "ldraw/parts/"
ldraw_kinds = list(map(lambda x: x[:-4],os.listdir(ldraw_dir)))
out_dir = "renders/"

def whatToRender(db_path:str) -> list:
    db = sql.connect(piece_db_path)
    c = db.cursor()
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

def randomColorCodes(num:int, db_path:str) -> list:
    db = sql.connect(db_path)
    c = db.cursor()
    c.execute("SELECT code FROM colors ORDER BY RANDOM() LIMIT ?", (num,))
    return [i[0] for i in c.fetchall()]

def render(kind_id:str, color:str, dat_path:str, bg_img_path:str, pos:tuple, out_path:str):
    return None
