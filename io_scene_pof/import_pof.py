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
This script imports Volition POF files to Blender.

Usage:
Run this script from "File->Import" menu and then load the desired POF file.

http://wiki.blender.org/index.php/Scripts/Manual/Import/wavefront_obj
"""


import os
import time
import bpy
import bmesh
import mathutils
from bpy_extras.io_utils import unpack_list, unpack_face_list
from volition import pof


def create_mesh(sobj, use_smooth_groups=False, tex_chunk=None):
    """Takes a submodel and adds a Blender mesh."""
    m = sobj.get_mesh()
    if use_smooth_groups:
        m.calculate_sharp_edges()

    bm = bmesh.new()

    for f in m.face_list:
        bfverts = list()
        for v in f.vert_list:
            bfverts.append(bm.verts.new(v.co))
        bm.faces.new(bfverts)

    me = bpy.data.meshes.new("{}-mesh".format(sobj.name.decode()))
    bm.to_mesh(me)

    me.validate()
    me.update()
    bobj = bpy.data.objects.new("Mesh", me)
    bobj.name = sobj.name.decode()
    if use_smooth_groups:
        bobj.modifiers.new("POF smoothing", "EDGE_SPLIT")
    return bobj


def load(operator, context, filepath,
        use_smooth_groups=False,
        import_center_points=False,
        import_bound_boxes=False,
        import_eye_points=True,
        import_paths=True,
        import_gun_points=True,
        import_mis_points=True,
        import_tgun_points=True,
        import_tmis_points=True,
        import_thrusters=True,
        import_glow_points=True,
        #import_flash_points=True,
        import_special_points=True,
        import_header_data=True,
        import_only_main=False,
        import_detail_levels=True,
        import_detail_boxes=True,
        import_debris=True,
        import_turrets=True,
        import_specials=True,
        import_special_debris=True,
        fore_is_y=True,
        import_shields=True,
        import_textures=True,
        texture_path="../maps/",
        make_materials=False
        ):
    print("\tloading POF file {}...".format(filepath))
    filepath = os.fsencode(filepath)
    cur_time = time.time()
    pof_file = open(filepath, 'rb')
    pof_handler = pof.read_pof(pof_file)
    pof_file.close()
    new_time = time.time()
    print("\ttime to load POF handler {} sec".format(new_time - cur_time))

    # we now have a PolyModel instance containing all the chunks
    # now we check through the kwargs and call the appropriate
    # methods to read the PolyModel

    if pof_handler.pof_ver >= 2116:
        pof_hdr = pof_handler.chunks["HDR2"]
    else:
        pof_hdr = pof_handler.chunks["OHDR"]

    if import_textures:
        txtr_chunk = pof_handler.chunks["TXTR"]
    else:
        txtr_chunk = None

    scene = context.scene

    # We'll start with submodels...

    new_objects = list()

    if import_only_main:
        # import only first detail level and its children

        # get first detail level
        hull_id = pof_hdr.sobj_detail_levels[0]
        hull = pof_handler.submodels[hull_id]
        hull_obj = create_mesh(hull, use_smooth_groups, txtr_chunk)
        new_objects.append(hull_obj)

        # get children
        child_ids = dict()
        for model in pof_handler.submodels.values():
            if model.parent_id == hull_id:
                child_obj = create_mesh(model, use_smooth_groups, txtr_chunk)
                child_obj.parent = hull_obj
                child_obj.location = model.offset
                new_objects.append(child_obj)
                child_ids[model.model_id] = child_obj

        # get second children
        for model in pof_handler.submodels.values():
            if model.parent_id in child_ids:
                child_obj = create_mesh(model, use_smooth_groups, txtr_chunk)
                child_obj.parent = child_ids[model.parent_id]
                x_off = pof_handler.submodels[model.parent_id].offset[0] + model.offset[0]
                y_off = pof_handler.submodels[model.parent_id].offset[1] + model.offset[1]
                z_off = pof_handler.submodels[model.parent_id].offset[2] + model.offset[2]
                child_obj.location = (x_off, y_off, z_off)
##                child_obj.location = model.offset
                new_objects.append(child_obj)

    for obj in new_objects:
        scene.objects.link(obj)

    scene.update()

    return {'FINISHED'}