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
import mathutils
from volition import pof


def create_mesh(sobj, use_smooth_groups=False, fore_is_y=True, tex_chunk=None):
    """Takes a submodel and adds a Blender mesh."""
    m = sobj.get_mesh()
    if use_smooth_groups:
        m.calculate_sharp_edges()

    bm = bpy.data.meshes.new(sobj.name.decode())

    vert_list = m.get_vert_list()
    bm.vertices.add(len(vert_list))
    bm.vertices.foreach_set("co", vert_list)

    edge_list, edge_sharps = m.get_edge_list()
    bm.edges.add(len(edge_list))
    bm.edges.foreach_set("vertices", edge_list)
    if use_smooth_groups:
        bm.edges.foreach_set("use_edge_sharp", edge_sharps)

    face_list = m.get_face_list()
    bm.polygons.add(len(face_list))
    bm.polygons.foreach_set("vertices", face_list)

    if use_smooth_groups:
        bm.show_edge_sharp = True
        for f in bm.polygons:
            f.use_smooth = True

    ## TODO add support for textures, axis flipping

    bm.validate()
    bm.update()
    bobj = bpy.data.objects.new("Mesh", bm)
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

    scene = context.scene

    # We'll start with submodels...

    new_objects = list()

    if import_only_main:
        # import only first detail level and its children

        # get first detail level
        hull_id = pof_hdr.sobj_detail_levels[0]
        hull = pof_handler.submodels[hull_id]
        if import_textures:
            hull_obj = create_mesh(hull, use_smooth_groups, fore_is_y, pof_handler.chunks["TXTR"])
        else:
            hull_obj = create_mesh(hull, use_smooth_groups, fore_is_y)
        new_objects.append(hull_obj)

    for obj in new_objects:
        scene.objects.link(obj)

    scene.update()

    return {'FINISHED'}