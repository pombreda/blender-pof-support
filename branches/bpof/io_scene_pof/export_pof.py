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
from bpy_extras.io_utils import unpack_list, unpack_face_list
from volition import pof


def create_mesh(bm, use_smooth_groups, fore_is_y):
    """Takes a Blender mesh and returns a Volition mesh."""
    vert_list = list()
    for v in bm.vertices:
        vert_list.append(pof.Vertex(v.co))

    edge_list = list()
    for e in bm.edges:
        e_sharp = e.use_edge_sharp
        e_verta = vert_list[e.vertices[0]]
        e_vertb = vert_list[e.vertices[1]]
        edge_list.append(pof.Edge([e_verta, e_vertb], e_sharp))

    face_list = list()
    for f in bm.polygons:
        # user must make sure mesh is triangulated
        f_verta = vert_list[f.vertices[0]]
        f_vertb = vert_list[f.vertices[1]]
        f_vertc = vert_list[f.vertices[2]]
        edgea = pof.Edge([f_verta, f_vertb])
        edgeb = pof.Edge([f_vertb, f_vertc])
        edgec = pof.Edge([f_vertc, f_verta])
        face_list.append(pof.Face([edgea, edgeb, edgec], vert_idx=f.vertices,
                        textured=True, color=f.material_index))

    return pof.Mesh(vert_list, edge_list, face_list)