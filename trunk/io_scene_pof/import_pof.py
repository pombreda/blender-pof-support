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

http://code.google.com/p/blender-pof-support/wiki/ImportScript
"""


import os
import time
import bpy
import bmesh
import mathutils
from bpy_extras.io_utils import unpack_list, unpack_face_list
from volition import pof


def create_mesh(sobj, use_smooth_groups, fore_is_y, import_textures):
    """Takes a submodel and adds a Blender mesh."""
    m = sobj.get_mesh()
    if use_smooth_groups:
        m.calculate_sharp_edges()

    bm = bmesh.new()

    for f in m.face_list:
        bfverts = list()
        for v in f.vert_list:
            x = v.co[0]
            y = v.co[1]
            z = v.co[2]
            if fore_is_y:
                co = (x, z, y)
            else:
                co = (x, y, z)
            bfverts.append(bm.verts.new(co))
        bface = bm.faces.new(bfverts)
##        if import_textures:
##            bface.material_index = f.color

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
        #import_special_debris=True,
        fore_is_y=True,
        import_shields=True,
        import_textures=True,
        texture_path="../maps/",
        texture_format=".dds",
        pretty_materials=False
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

    cur_time = time.time()

    # Textures first

        # we'll do this by making a material for every texture
        # if we're importing pretty textures, we'll make a
        # Blender texture each for shine, normal, glow, etc.

        # we'll keep the materials in a list and link every material
        # to every submodel object.  That way, we can assign
        # material indices that are the same as the POF texture indices

    if not os.path.isdir(texture_path):
        print("Given texture path is not a valid directory.")
        import_textures = False

    if import_textures:
        txtr_chunk = pof_handler.chunks["TXTR"]
        # go through txtr_chunk, make Blender images for each
        # if pretty_textures: get shine, normal, glow, etc., too
        missing_textures = 0
        bmats = list()
        bimgs = list()
        if pretty_materials:
            shine_imgs = list()
            normal_imgs = list()
            glow_imgs = list()
        for tex in txtr_chunk.textures:
            tex_name = tex.decode()
            tex_path = os.path.join(texture_path, tex_name + texture_format)
            if os.path.isfile(tex_path):
                bimgs.append(bpy.data.images.load(tex_path))
            else:
                print("Missing texture {}".format(tex_name))
                missing_textures += 1
            if pretty_materials:
                shine_name = tex_name + "-shine" + texture_format
                norm_name = tex_name + "-normal" + texture_format
                glow_name = tex_name + "-glow" + texture_format
                shine_path = os.path.join(texture_path, shine_name)
                norm_path = os.path.join(texture_path, norm_name)
                glow_path = os.path.join(texture_path, glow_name)
                if os.path.isfile(shine_path):
                    shine_imgs.append(bpy.data.images.load(shine_path))
                else:
                    missing_textures += 1
                if os.path.isfile(norm_path):
                    normal_imgs.append(bpy.data.images.load(norm_path))
                else:
                    missing_textures += 1
                if os.path.isfile(glow_path):
                    glow_imgs.append(bpy.data.images.load(glow_path))
                else:
                    missing_textures += 1
        print("Total missing textures: {}".format(missing_textures))

    # Now submodels

    new_objects = dict()    # dict instead of list so
                            # we can ref by POF model id

    if import_only_main:
        # import only first detail level and its children

        # get first detail level
        hull_id = pof_hdr.sobj_detail_levels[0]
        hull = pof_handler.submodels[hull_id]
        hull_obj = create_mesh(hull, use_smooth_groups, fore_is_y, import_textures)
        new_objects[hull_id] = hull_obj

        # get children
        child_ids = dict()
        for model in pof_handler.submodels.values():
            if model.parent_id == hull_id:
                child_obj = create_mesh(model, use_smooth_groups, fore_is_y, import_textures)
                child_obj.parent = hull_obj
                if fore_is_y:
                    off_x = model.offset[0]
                    off_y = model.offset[1]
                    off_z = model.offset[2]
                    child_obj.location = (off_x, off_z, off_y)
                else:
                    child_obj.location = model.offset
                new_objects[model.model_id] = child_obj

        # get second children
        for model in pof_handler.submodels.values():
            if model.parent_id in child_ids:
                child_obj = create_mesh(model, use_smooth_groups, fore_is_y, import_textures)
                child_obj.parent = new_objects[model.parent_id]
                x_off = pof_handler.submodels[model.parent_id].offset[0] + model.offset[0]
                y_off = pof_handler.submodels[model.parent_id].offset[1] + model.offset[1]
                z_off = pof_handler.submodels[model.parent_id].offset[2] + model.offset[2]
                if fore_is_y:
                    child_obj.location = (x_off, z_off, y_off)
                else:
                    child_obj.location = (x_off, y_off, z_off)
                new_objects[model.model_id] = child_obj

    else:
        layer_count = 0
        debris_layer = None
        main_detail = None

        if import_detail_levels:
            for i in pof_hdr.sobj_detail_levels:
                model = pof_handler.submodels[i]
                this_obj = create_mesh(model, use_smooth_groups, fore_is_y, import_textures)
                # put LODs on sep layers from each other
                this_obj.layers[0] = False
                this_obj.layers[layer_count] = True
                layer_count += 1
                new_objects[model.model_id] = this_obj
            main_detail = new_objects[0]

        if import_debris:
            for i in pof_hdr.sobj_debris:
                model = pof_handler.submodels[i]
                this_obj = create_mesh(model, use_smooth_groups, fore_is_y, import_textures)
                # put debris on sep layer from LODs, but same as each other
                this_obj.layers[0] = False
                this_obj.layers[layer_count] = True
                new_objects[model.model_id] = this_obj
                debris_layer = layer_count
            layer_count += 1

        if import_turrets:
            if "TGUN" in pof_handler.chunks:
                tchunk = pof_handler.chunks["TGUN"]
                for i in range(len(tchunk.base_sobj)):
                    model = pof_handler.submodels[tchunk.base_sobj[i]]
                    this_obj = create_mesh(model, use_smooth_groups, fore_is_y, import_textures)
                    if main_detail is not None:
                        this_obj.parent = main_detail
                    off_x = model.offset[0]
                    off_y = model.offset[1]
                    off_z = model.offset[2]
                    if fore_is_y:
                        this_obj.location = (off_x, off_z, off_y)
                    else:
                        this_obj.location = (off_x, off_y, off_z)

                    if tchunk.barrel_sobj[i] > -1:
                        bar_model = pof_handler.submodels[tchunk.barrel_sobj[i]]
                        barrel_obj = create_mesh(bar_model, use_smooth_groups, fore_is_y, import_textures)
                        barrel_obj.parent = this_obj
                        off_x += model.offset[0]
                        off_y += model.offset[1]
                        off_z += model.offset[2]
                        if fore_is_y:
                            barrel_obj.location = (off_x, off_z, off_y)
                        else:
                            barrel_obj.location = (off_x, off_y, off_z)
                        new_objects[bar_model.model_id] = barrel_obj
                    new_objects[model.model_id] = this_obj

            if "TMIS" in pof_handler.chunks:
                tchunk = pof_handler.chunks["TMIS"]
                for i in range(len(tchunk.base_sobj)):
                    model = pof_handler.submodels[tchunk.base_sobj[i]]
                    this_obj = create_mesh(model, use_smooth_groups, fore_is_y, import_textures)
                    if main_detail is not None:
                        this_obj.parent = main_detail
                    off_x = model.offset[0]
                    off_y = model.offset[1]
                    off_z = model.offset[2]
                    if fore_is_y:
                        this_obj.location = (off_x, off_z, off_y)
                    else:
                        this_obj.location = (off_x, off_y, off_z)

                    if tchunk.barrel_sobj[i] > -1:
                        bar_model = pof_handler.submodels[tchunk.barrel_sobj[i]]
                        barrel_obj = create_mesh(bar_model, use_smooth_groups, fore_is_y, import_textures)
                        barrel_obj.parent = this_obj
                        off_x += model.offset[0]
                        off_y += model.offset[1]
                        off_z += model.offset[2]
                        if fore_is_y:
                            barrel_obj.location = (off_x, off_z, off_y)
                        else:
                            barrel_obj.location = (off_x, off_y, off_z)
                        new_objects[bar_model.model_id] = barrel_obj
                    new_objects[model.model_id] = this_obj

        if import_specials:
            for model in pof_handler.submodels.values():
                if b"subsystem" in model.properties:
                    this_obj = create_mesh(model, use_smooth_groups, fore_is_y, import_textures)
                    this_obj.parent = new_objects[model.parent_id]
                    new_objects[model.model_id] = this_object

    if import_shields and "SHLD" in pof_handler.chunks:
        model = pof_handler.chunks["SHLD"]
        this_obj = create_mesh(model, False, fore_is_y, None)
        this_obj.draw_type = "WIRE"
        new_objects["shield"] = this_obj

    # done

    for obj in new_objects.values():
        scene.objects.link(obj)

    scene.update()
    new_time = time.time()
    print("\ttime to add objects {}".format(new_time - cur_time))

    return {'FINISHED'}