# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""
This script exports Volition POF files from Blender.

Usage:
Run this script from "File->Export" menu and then save the desired POF file.

http://code.google.com/p/blender-pof-support/wiki/ExportScript
"""


import os
import time
import bpy
import bmesh
import mathutils
from collections import OrderedDict
from bpy_extras.io_utils import unpack_list, unpack_face_list
from . import pof


def create_mesh(bm, fore_is_y):
    """Takes a Blender mesh and returns a Volition mesh."""
    verts = list()
    vnorms = OrderedDict()
    for v in bm.vertices:
        co = tuple(v.co)
        if co not in verts:
            verts.append(co)
            vnorms[co] = list()
        vnorms[co].append(tuple(v.normal))

    # creating the face list might be slow, have to do a lot of index()'ing
    faces = list()
    fvnorms = list()
    centers = list()
    tex_ids = list()
    fnorms = list()
    for f in bm.polygons:
        this_face = list()
        these_norms = list()
        for v in f.vertices:
            this_coord = tuple(bm.vertices[v].co)
            this_norm = tuple(bm.vertices[v].normal)
            this_vert = verts.index(this_coord)
            this_face.append(this_vert)
            these_norms.append(vnorms[this_coord].index(this_norm))
        faces.append(this_face)
        fvnorms.append(these_norms)
        centers.append(tuple(f.center))
        tex_ids.append(f.material_index)
        fnorms.append(tuple(f.normal))

    m = pof.Mesh()
    m.verts = verts
    m.vnorms = list(vnorms.values())
    m.faces = faces
    m.fvnorms = fvnorms
    m.centers = centers
    m.tex_ids = tex_ids
    m.fnorms = fnorms

    if fore_is_y:
        m.flip_yz()

    return m